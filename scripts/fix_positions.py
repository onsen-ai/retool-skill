#!/usr/bin/env python3
"""
fix_positions.py — Recalculates vertical layout positions to eliminate gaps and overlaps.

Usage:
    python fix_positions.py <app-dir>                          # fix all containers
    python fix_positions.py <app-dir> --container '$main'      # fix specific container

Reads .positions.json, recomputes row values so components stack without gaps,
preserves col offsets, widths, heights, rowGroup entries, and container/subcontainer refs.
"""

import argparse
import json
import os
import sys


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
    """Guess a default height from the component id if the type can be inferred."""
    # Simple heuristic: check if the id contains a known type name (case-insensitive)
    lower = component_id.lower()
    for type_name, h in DEFAULT_HEIGHTS.items():
        if type_name.lower() in lower:
            return h
    return 1.0  # safe fallback


# ---------------------------------------------------------------------------
# Scope key: groups components by (container, subcontainer) or top-level
# ---------------------------------------------------------------------------

def scope_key(entry):
    """Return a hashable key representing the positioning scope of a component."""
    container = entry.get("container")
    subcontainer = entry.get("subcontainer")
    return (container or "", subcontainer or "")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def fix_positions(app_dir, target_container=None):
    app_dir = os.path.abspath(app_dir)
    pos_file = os.path.join(app_dir, ".positions.json")

    if not os.path.isfile(pos_file):
        print(f"Error: {pos_file} not found")
        sys.exit(1)

    with open(pos_file, "r", encoding="utf-8") as f:
        positions = json.load(f)

    # Group components by scope
    scopes = {}
    for comp_id, entry in positions.items():
        key = scope_key(entry)
        scopes.setdefault(key, []).append((comp_id, entry))

    changes = []

    for key, components in scopes.items():
        container_name = key[0] or key[1] or "$main"

        # If the user specified a container filter, skip non-matching scopes
        if target_container is not None:
            if container_name != target_container:
                continue

        # Separate rowGroup (header/footer) from body components
        body_components = []
        for comp_id, entry in components:
            if "rowGroup" in entry:
                continue  # leave header/footer entries unchanged
            body_components.append((comp_id, entry))

        if not body_components:
            continue

        # Sort by current row (default 0), then by col for stability
        body_components.sort(key=lambda x: (x[1].get("row", 0), x[1].get("col", 0)))

        # Group components that share the same row value (same visual row)
        row_groups = []
        current_row_val = None
        current_group = []
        for comp_id, entry in body_components:
            r = entry.get("row", 0)
            if current_row_val is None or r != current_row_val:
                if current_group:
                    row_groups.append(current_group)
                current_group = [(comp_id, entry)]
                current_row_val = r
            else:
                current_group.append((comp_id, entry))
        if current_group:
            row_groups.append(current_group)

        # Recalculate rows: each visual row starts where the previous one ended
        next_row = 0
        for group in row_groups:
            # All components in the group get the same row value
            max_height = 0
            for comp_id, entry in group:
                h = entry.get("height", 0)
                if h == 0:
                    h = get_default_height(comp_id)
                    entry["height"] = h
                max_height = max(max_height, h)

            for comp_id, entry in group:
                old_row = entry.get("row", 0)
                if old_row != next_row:
                    changes.append(
                        f"  {comp_id}: row {old_row} -> {next_row} (scope: {container_name})"
                    )
                entry["row"] = next_row

                # Warn if col + width > 12
                col = entry.get("col", 0)
                width = entry.get("width", 12)
                if col + width > 12:
                    print(
                        f"Warning: {comp_id} col({col}) + width({width}) = {col + width} > 12"
                    )

            next_row = round(next_row + max_height, 4)

    # Write back
    with open(pos_file, "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=2)
        f.write("\n")

    # Summary
    if changes:
        print(f"Updated {pos_file}")
        print(f"{len(changes)} position change(s):")
        for c in changes:
            print(c)
    else:
        print("No changes needed — all positions are already correct.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Recalculate vertical layout positions in .positions.json"
    )
    parser.add_argument("app_dir", help="Path to the Retool app directory")
    parser.add_argument(
        "--container",
        default=None,
        help="Fix only a specific container (e.g. '$main')",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.app_dir):
        print(f"Error: {args.app_dir} is not a directory")
        sys.exit(1)

    fix_positions(args.app_dir, args.container)


if __name__ == "__main__":
    main()
