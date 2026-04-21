#!/usr/bin/env python3
"""
fix_positions.py — Recalculate vertical layout positions in .positions.json.

Safe-by-default: dry-run unless --apply is passed. Scopes that are already valid
(no overlaps, no zero-height entries) are left untouched so intentional authored
spacing is preserved.

Modes
-----
    # Dry-run (default). Prints the planned diff and exits without writing.
    python fix_positions.py <app-dir>

    # Apply the same diff.
    python fix_positions.py <app-dir> --apply

    # Restrict to a single scope (container or subcontainer).
    python fix_positions.py <app-dir> --scope EditInteractionForm --apply

    # Additive shift: move rows at or below --shift-from by --by, nothing else.
    # No gap-collapsing. Requires --scope.
    python fix_positions.py <app-dir> --scope EditInteractionForm \\
        --shift-from 10.2 --by 3.2 --apply

Notes
-----
- `--container` is accepted as an alias for `--scope` with a deprecation warning
  on stderr.
- `rowGroup: "header"` / `"footer"` entries are never touched (they have their
  own layout semantics).
- Col+width > 12 still produces a warning, as before.
"""

import argparse
import json
import os
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# Standard fallback heights (used when height is missing or 0)
# ---------------------------------------------------------------------------

DEFAULT_HEIGHTS = {
    "Text": 0.6,
    "TextInput": 1.0,
    "Select": 1.0,
    "DateRange": 1.0,
    "Button": 1.0,
    "TextArea": 1.0,
    "Table": 13.2,
    "Chat": 17.4,
    "Form": 0.2,
    "Container": 0.2,
}


def get_default_height(component_id):
    """Guess a default height from the component id if the type can be inferred.

    Returns 1.0 as the fallback.
    """
    lower = component_id.lower()
    for type_name, h in DEFAULT_HEIGHTS.items():
        if type_name.lower() in lower:
            return h
    return 1.0


# ---------------------------------------------------------------------------
# Scope helpers
# ---------------------------------------------------------------------------

def scope_key(entry):
    """Hashable key grouping components by their positioning scope."""
    return (entry.get("container") or "", entry.get("subcontainer") or "")


def scope_matches(entry, scope):
    """Whether `entry` belongs to the given scope name.

    A scope name matches either the container or subcontainer field.
    """
    if not scope:
        return True
    return entry.get("container") == scope or entry.get("subcontainer") == scope


# ---------------------------------------------------------------------------
# Validity check (Change 2): skip scopes that don't need fixing
# ---------------------------------------------------------------------------

def _cols_overlap(a, b):
    ca, wa = a.get("col", 0), a.get("width", 12)
    cb, wb = b.get("col", 0), b.get("width", 12)
    return ca < cb + wb and cb < ca + wa


# Precision tolerance for row math. Positions in .positions.json are floats with
# common round-off (e.g. 2.2 + 0.6 = 2.8000000000000003); treat sub-EPS differences
# as "touching, not overlapping." Matches the file's `round(..., 4)` convention.
_EPS = 1e-6


def scope_is_valid(body_components):
    """Return True if no two body components genuinely overlap.

    Body components = the list after header/footer rowGroup entries are filtered
    out. An "overlap" requires both row-range AND col-range intersection — pure
    side-by-side components at the same row (different cols) are NOT overlaps.

    Zero-height entries (common for stack-layout Forms and Containers) use the
    type-inferred default from the id only for the overlap check; their stored
    `height` is not changed by this function.
    """
    sorted_entries = sorted(
        body_components,
        key=lambda x: (x[1].get("row", 0), x[1].get("col", 0)),
    )
    for i in range(len(sorted_entries)):
        aid, a = sorted_entries[i]
        ra = a.get("row", 0)
        ha = a.get("height", 0) or get_default_height(aid)
        a_bottom = ra + ha
        for j in range(i + 1, len(sorted_entries)):
            _, b = sorted_entries[j]
            rb = b.get("row", 0)
            if rb + _EPS >= a_bottom:
                # All subsequent entries start at or below a's bottom → no overlap.
                break
            if _cols_overlap(a, b):
                return False
    return True


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_positions(app_dir):
    pos_file = os.path.join(os.path.abspath(app_dir), ".positions.json")
    if not os.path.isfile(pos_file):
        print(f"Error: {pos_file} not found", file=sys.stderr)
        sys.exit(1)
    with open(pos_file, "r", encoding="utf-8") as f:
        return pos_file, json.load(f)


def write_positions(pos_file, positions):
    with open(pos_file, "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_changes(changes, apply_):
    if not changes:
        print("No changes needed.")
        return
    by_scope = defaultdict(list)
    for ch in changes:
        by_scope[ch["scope"]].append(ch)

    total = sum(len(v) for v in by_scope.values())
    print(f"{total} position change(s) across {len(by_scope)} scope(s):")
    for scope, items in sorted(by_scope.items()):
        print(f"\n  [{scope}]  ({len(items)} change{'s' if len(items) != 1 else ''})")
        for ch in items:
            print(f"    {ch['id']}: row {ch['old']} → {ch['new']}")

    if not apply_:
        print("\nDry run — no changes written.")
        print("Re-run with --apply to persist.")


def _warn_col_width(positions):
    """Existing warning preserved: any component where col + width > 12."""
    for cid, entry in positions.items():
        col = entry.get("col", 0)
        width = entry.get("width", 12)
        if col + width > 12:
            print(
                f"Warning: {cid} col({col}) + width({width}) = {col + width} > 12",
                file=sys.stderr,
            )


# ---------------------------------------------------------------------------
# Mode A: additive --shift-from / --by (Change 3)
# ---------------------------------------------------------------------------

def shift_scope(positions, scope, cutoff, delta):
    """Shift rows >= cutoff in `scope` by `delta`. Returns list of change records."""
    changes = []
    for cid, entry in positions.items():
        if not scope_matches(entry, scope):
            continue
        row = entry.get("row")
        if not isinstance(row, (int, float)):
            continue
        if row >= cutoff:
            new_row = round(row + delta, 4)
            if new_row != row:
                changes.append({"id": cid, "old": row, "new": new_row, "scope": scope})
                entry["row"] = new_row
    return changes


# ---------------------------------------------------------------------------
# Mode B: collapse-gaps (existing behavior, gated by scope_is_valid)
# ---------------------------------------------------------------------------

def collapse_gaps(positions, target_scope=None):
    """Pack each scope's body components so rows start at 0 with no gaps.

    Scopes whose current layout is already valid (no overlaps, no zero-height
    entries) are left untouched. Header/footer rowGroup entries are never moved.

    Returns a list of change records.
    """
    scopes = defaultdict(list)
    for cid, entry in positions.items():
        scopes[scope_key(entry)].append((cid, entry))

    changes = []

    for key, components in scopes.items():
        container_name = key[0] or key[1] or "$main"

        if target_scope is not None:
            # Match either container or subcontainer (preserves old behavior).
            if key[0] != target_scope and key[1] != target_scope:
                continue

        body_components = [(cid, e) for cid, e in components if "rowGroup" not in e]
        if not body_components:
            continue

        # Skip if already valid — preserves authored spacing.
        if scope_is_valid(body_components):
            continue

        body_components.sort(key=lambda x: (x[1].get("row", 0), x[1].get("col", 0)))

        # Group components that share a row value (same visual row).
        row_groups = []
        current_row_val = None
        current_group = []
        for cid, entry in body_components:
            r = entry.get("row", 0)
            if current_row_val is None or r != current_row_val:
                if current_group:
                    row_groups.append(current_group)
                current_group = [(cid, entry)]
                current_row_val = r
            else:
                current_group.append((cid, entry))
        if current_group:
            row_groups.append(current_group)

        # Recompute rows, packing tight. Record both row changes and inferred-height
        # fixes so that a scope with only zero-height entries still writes on --apply.
        next_row = 0
        for group in row_groups:
            max_height = 0
            for cid, entry in group:
                old_height = entry.get("height", 0)
                h = old_height
                if h == 0:
                    h = get_default_height(cid)
                    entry["height"] = h
                    changes.append(
                        {
                            "id": cid,
                            "old": f"height={old_height}",
                            "new": f"height={h}",
                            "scope": container_name,
                        }
                    )
                max_height = max(max_height, h)

            for cid, entry in group:
                old_row = entry.get("row", 0)
                if old_row != next_row:
                    changes.append(
                        {"id": cid, "old": old_row, "new": next_row, "scope": container_name}
                    )
                    entry["row"] = next_row

            next_row = round(next_row + max_height, 4)

    return changes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Recalculate vertical layout positions in .positions.json (dry-run by default)"
    )
    parser.add_argument("app_dir", help="Path to the Retool app directory")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes. Without this flag, only the planned diff is printed.",
    )
    parser.add_argument(
        "--scope",
        default=None,
        help="Container or subcontainer name to operate on (e.g. 'EditInteractionForm').",
    )
    parser.add_argument(
        "--container",
        dest="container",
        default=None,
        help="Deprecated alias for --scope. Prefer --scope.",
    )
    parser.add_argument(
        "--shift-from",
        dest="shift_from",
        type=float,
        default=None,
        help="Row cutoff. Entries in --scope with row >= this value are shifted.",
    )
    parser.add_argument(
        "--by",
        dest="by",
        type=float,
        default=None,
        help="Row delta. Required when --shift-from is set.",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.app_dir):
        print(f"Error: {args.app_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Unify --container and --scope with a one-line deprecation warning.
    if args.container is not None:
        print(
            "Warning: --container is deprecated; use --scope instead.",
            file=sys.stderr,
        )
        if args.scope is None:
            args.scope = args.container

    # --shift-from mode has stricter requirements.
    if args.shift_from is not None:
        if args.by is None or args.scope is None:
            parser.error("--shift-from requires --by and --scope")

    pos_file, positions = load_positions(args.app_dir)

    if args.shift_from is not None:
        changes = shift_scope(positions, args.scope, args.shift_from, args.by)
    else:
        changes = collapse_gaps(positions, target_scope=args.scope)

    _warn_col_width(positions)
    _print_changes(changes, args.apply)

    if args.apply and changes:
        write_positions(pos_file, positions)
        print(f"\nWrote {pos_file}")


if __name__ == "__main__":
    main()
