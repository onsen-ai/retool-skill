#!/usr/bin/env python3
"""
Unit tests for scripts/fix_positions.py.

Stdlib-only (unittest). Run with:

    python -m unittest scripts.tests.test_fix_positions

or from the scripts/ dir:

    python -m unittest tests.test_fix_positions

Each test builds a small in-memory .positions.json, runs the CLI via main(argv),
and asserts on the on-disk file afterwards. A shared temp app dir is used to
avoid touching the real examples.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

# Make scripts/ importable whether the test is run from scripts/ or the repo root
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(HERE)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import fix_positions  # noqa: E402


def _write_positions(app_dir, data):
    path = os.path.join(app_dir, ".positions.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def _read_positions(app_dir):
    with open(os.path.join(app_dir, ".positions.json"), encoding="utf-8") as f:
        return json.load(f)


@contextlib.contextmanager
def _capture():
    out, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class FixPositionsTests(unittest.TestCase):
    def setUp(self):
        self.app_dir = tempfile.mkdtemp(prefix="fixpos-test-")

    def tearDown(self):
        shutil.rmtree(self.app_dir, ignore_errors=True)

    # ---------------------------------------------------------------
    # Change 1 — dry-run default / --apply
    # ---------------------------------------------------------------

    def test_dry_run_does_not_write(self):
        """Without --apply, an overlapping scope is reported but not written."""
        data = {
            # Overlap: comp2's row (0.5) is inside comp1's vertical span (0 + 1 = 1.0)
            "comp1": {"container": "ScopeA", "row": 0, "height": 1, "width": 12},
            "comp2": {"container": "ScopeA", "row": 0.5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)
        before = _read_positions(self.app_dir)

        with _capture() as (out, _err):
            fix_positions.main([self.app_dir])
        output = out.getvalue()

        self.assertIn("Dry run", output)
        self.assertIn("ScopeA", output)
        self.assertEqual(_read_positions(self.app_dir), before)

    def test_apply_writes(self):
        """With --apply, the same scope is rewritten on disk."""
        data = {
            "comp1": {"container": "ScopeA", "row": 0, "height": 1, "width": 12},
            "comp2": {"container": "ScopeA", "row": 0.5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main([self.app_dir, "--apply"])
        after = _read_positions(self.app_dir)

        # comp1 stays at row 0; comp2 is no longer overlapping.
        self.assertEqual(after["comp1"]["row"], 0)
        self.assertEqual(after["comp2"]["row"], 1)

    # ---------------------------------------------------------------
    # Change 2 — skip already-valid scopes
    # ---------------------------------------------------------------

    def test_valid_scope_is_skipped(self):
        """Authored 5-row gap (no overlaps) is preserved, even with --apply."""
        data = {
            "head": {"container": "ScopeA", "row": 0, "height": 1, "width": 12},
            "body": {"container": "ScopeA", "row": 6, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture() as (out, _):
            fix_positions.main([self.app_dir, "--apply"])

        after = _read_positions(self.app_dir)
        self.assertEqual(after["head"]["row"], 0)
        self.assertEqual(after["body"]["row"], 6)  # unchanged
        self.assertIn("No changes needed", out.getvalue())

    def test_side_by_side_components_are_not_overlapping(self):
        """Same row, different cols with non-overlapping widths → valid scope."""
        data = {
            "left":  {"container": "ScopeA", "row": 0, "col": 0, "height": 1, "width": 6},
            "right": {"container": "ScopeA", "row": 0, "col": 6, "height": 1, "width": 6},
        }
        _write_positions(self.app_dir, data)

        with _capture() as (out, _):
            fix_positions.main([self.app_dir, "--apply"])

        after = _read_positions(self.app_dir)
        self.assertEqual(after, data)
        self.assertIn("No changes needed", out.getvalue())

    def test_overlapping_scope_fixed(self):
        """Two genuinely overlapping components are fixed; other scopes untouched."""
        data = {
            "a": {"container": "ScopeA", "row": 0, "height": 2, "width": 12},
            "b": {"container": "ScopeA", "row": 1, "height": 2, "width": 12},
            # Different scope — untouched.
            "c": {"container": "ScopeB", "row": 5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main([self.app_dir, "--apply"])
        after = _read_positions(self.app_dir)

        self.assertEqual(after["a"]["row"], 0)
        self.assertEqual(after["b"]["row"], 2)  # moved to just below a
        self.assertEqual(after["c"]["row"], 5)  # unchanged

    def test_zero_height_alone_does_not_force_rewrite(self):
        """height: 0 is common for stack-layout Form/Container entries — it alone
        shouldn't invalidate a scope. The entry is left as-is (width/col/row)."""
        data = {
            "SomeForm": {"container": "ScopeA", "row": 0, "height": 0, "width": 12},
        }
        _write_positions(self.app_dir, data)
        before = _read_positions(self.app_dir)

        with _capture() as (out, _):
            fix_positions.main([self.app_dir, "--apply"])

        self.assertEqual(_read_positions(self.app_dir), before)
        self.assertIn("No changes needed", out.getvalue())

    def test_zero_height_is_used_for_overlap_detection(self):
        """When a scope has an overlap, zero-height entries use their type-inferred
        default during the overlap check (so stack-layout components don't silently
        mask overlaps)."""
        data = {
            # Button default height = 1.0 → at row 0, spans 0-1.0
            "ButtonA": {"container": "ScopeA", "row": 0, "height": 0, "width": 12},
            # Overlaps into ButtonA's inferred span
            "ButtonB": {"container": "ScopeA", "row": 0.5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main([self.app_dir, "--apply"])
        after = _read_positions(self.app_dir)

        # Scope was rewritten → both entries got packed; height inferred during rewrite.
        self.assertEqual(after["ButtonA"]["height"], 1.0)
        self.assertEqual(after["ButtonA"]["row"], 0)
        self.assertEqual(after["ButtonB"]["row"], 1)

    # ---------------------------------------------------------------
    # Change 3 — --shift-from / --by
    # ---------------------------------------------------------------

    def test_shift_from_basic(self):
        """--shift-from N --by M moves rows >= N, leaves rows < N alone."""
        data = {
            "a": {"container": "ScopeA", "row": 0, "height": 1, "width": 12},
            "b": {"container": "ScopeA", "row": 2, "height": 1, "width": 12},
            "c": {"container": "ScopeA", "row": 3, "height": 1, "width": 12},
            "d": {"container": "ScopeA", "row": 5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main(
                [self.app_dir, "--scope", "ScopeA", "--shift-from", "3", "--by", "2", "--apply"]
            )
        after = _read_positions(self.app_dir)

        self.assertEqual(after["a"]["row"], 0)
        self.assertEqual(after["b"]["row"], 2)  # below cutoff — unchanged
        self.assertEqual(after["c"]["row"], 5)  # 3 + 2
        self.assertEqual(after["d"]["row"], 7)  # 5 + 2

    def test_shift_from_preserves_other_scopes(self):
        """Shift in ScopeA does not affect ScopeB."""
        data = {
            "a": {"container": "ScopeA", "row": 5, "height": 1, "width": 12},
            "b": {"container": "ScopeB", "row": 5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main(
                [self.app_dir, "--scope", "ScopeA", "--shift-from", "0", "--by", "3", "--apply"]
            )
        after = _read_positions(self.app_dir)

        self.assertEqual(after["a"]["row"], 8)
        self.assertEqual(after["b"]["row"], 5)  # untouched

    def test_shift_from_matches_subcontainer(self):
        """--scope matches either container or subcontainer."""
        data = {
            "a": {"container": "Outer", "subcontainer": "Inner", "row": 5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main(
                [self.app_dir, "--scope", "Inner", "--shift-from", "0", "--by", "3", "--apply"]
            )

        self.assertEqual(_read_positions(self.app_dir)["a"]["row"], 8)

    def test_shift_from_requires_by_and_scope(self):
        """--shift-from alone exits with error."""
        data = {"a": {"container": "ScopeA", "row": 5, "height": 1, "width": 12}}
        _write_positions(self.app_dir, data)

        with _capture():
            with self.assertRaises(SystemExit):
                fix_positions.main([self.app_dir, "--shift-from", "3"])

    def test_shift_from_dry_run(self):
        """--shift-from without --apply prints diff, writes nothing."""
        data = {
            "a": {"container": "ScopeA", "row": 5, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)
        before = _read_positions(self.app_dir)

        with _capture() as (out, _):
            fix_positions.main(
                [self.app_dir, "--scope", "ScopeA", "--shift-from", "0", "--by", "3"]
            )
        output = out.getvalue()

        self.assertIn("Dry run", output)
        self.assertEqual(_read_positions(self.app_dir), before)

    # ---------------------------------------------------------------
    # Backward compat
    # ---------------------------------------------------------------

    def test_container_alias_still_works(self):
        """--container is accepted with a deprecation notice on stderr."""
        data = {
            "a": {"container": "ScopeA", "row": 0, "height": 2, "width": 12},
            "b": {"container": "ScopeA", "row": 1, "height": 2, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture() as (_out, err):
            fix_positions.main([self.app_dir, "--container", "ScopeA", "--apply"])
        stderr = err.getvalue()

        self.assertIn("deprecated", stderr.lower())
        after = _read_positions(self.app_dir)
        self.assertEqual(after["b"]["row"], 2)  # scope was fixed via the alias

    # ---------------------------------------------------------------
    # Regression guard — the incident this plan was written to fix
    # ---------------------------------------------------------------

    def test_no_cross_scope_rewrites_when_only_one_scope_broken(self):
        """A real bug from production: an overlap in one scope should NOT cause
        the script to rewrite other valid scopes."""
        data = {
            # ScopeA has an overlap
            "a1": {"container": "ScopeA", "row": 0, "height": 2, "width": 12},
            "a2": {"container": "ScopeA", "row": 1, "height": 2, "width": 12},
            # ScopeB is a valid scope with deliberate spacing
            "b1": {"container": "ScopeB", "row": 0, "height": 1, "width": 12},
            "b2": {"container": "ScopeB", "row": 5, "height": 1, "width": 12},
            # ScopeC is a valid tight-packed scope
            "c1": {"container": "ScopeC", "row": 0, "height": 1, "width": 12},
            "c2": {"container": "ScopeC", "row": 1, "height": 1, "width": 12},
        }
        _write_positions(self.app_dir, data)

        with _capture():
            fix_positions.main([self.app_dir, "--apply"])
        after = _read_positions(self.app_dir)

        # ScopeA was fixed
        self.assertEqual(after["a2"]["row"], 2)
        # ScopeB's authored spacing preserved
        self.assertEqual(after["b2"]["row"], 5)
        # ScopeC unchanged
        self.assertEqual(after["c1"]["row"], 0)
        self.assertEqual(after["c2"]["row"], 1)


if __name__ == "__main__":
    unittest.main()
