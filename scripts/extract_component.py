#!/usr/bin/env python3
"""
extract_component.py — Moves a component subtree from an .rsx file into src/<name>.rsx,
replacing it with an <Include> tag.

Usage:
    python extract_component.py <app-dir> --component <component-id>

Example:
    python extract_component.py ./my-app --component editModal
"""

import argparse
import os
import re
import sys


# ---------------------------------------------------------------------------
# RSX block finder (regex-based — RSX is NOT valid XML)
# ---------------------------------------------------------------------------

def find_component_block(content, component_id):
    """Find start and end positions of a component block by its id.

    Returns (start, end, tag_name) or None if not found.
    """
    # Match the opening tag that contains id="<component_id>"
    pattern = re.compile(
        rf'(\s*)<([A-Z]\w*)\b([^>]*\bid="{re.escape(component_id)}"[^>]*?)(/?)>',
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return None

    tag_name = match.group(2)
    is_self_closing = match.group(4) == "/"
    start = match.start()

    if is_self_closing:
        return start, match.end(), tag_name

    # Walk forward, tracking nesting depth to find the correct closing tag.
    depth = 1
    pos = match.end()
    # Open pattern: <TagName ...> but NOT self-closing (no / before >)
    open_pattern = re.compile(rf"<{re.escape(tag_name)}\b[^>]*(?<!/)>")
    close_pattern = re.compile(rf"</{re.escape(tag_name)}>")

    while depth > 0 and pos < len(content):
        next_open = open_pattern.search(content, pos)
        next_close = close_pattern.search(content, pos)

        if next_close is None:
            break

        if next_open and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return start, next_close.end(), tag_name
            pos = next_close.end()

    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FRAME_TYPES = {"ModalFrame", "SplitPaneFrame", "DrawerFrame"}


def rsx_files_in_order(app_dir):
    """Yield (filepath, is_main) for main.rsx first, then src/*.rsx."""
    main = os.path.join(app_dir, "main.rsx")
    if os.path.isfile(main):
        yield main, True
    src_dir = os.path.join(app_dir, "src")
    if os.path.isdir(src_dir):
        for fname in sorted(os.listdir(src_dir)):
            if fname.endswith(".rsx"):
                yield os.path.join(src_dir, fname), False


def detect_indent(content, position):
    """Return the whitespace at the start of the line containing *position*."""
    line_start = content.rfind("\n", 0, position)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1  # skip the newline itself
    indent = ""
    for ch in content[line_start:]:
        if ch in (" ", "\t"):
            indent += ch
        else:
            break
    return indent


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def extract_component(app_dir, component_id):
    app_dir = os.path.abspath(app_dir)
    src_dir = os.path.join(app_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    dest_file = os.path.join(src_dir, f"{component_id}.rsx")
    if os.path.isfile(dest_file):
        print(f"Error: {dest_file} already exists. Remove it first if you want to re-extract.")
        sys.exit(1)

    # 1. Find the component in one of the .rsx files
    found_file = None
    found_is_main = False
    block_info = None

    for filepath, is_main in rsx_files_in_order(app_dir):
        content = open(filepath, "r", encoding="utf-8").read()
        result = find_component_block(content, component_id)
        if result is not None:
            found_file = filepath
            found_is_main = is_main
            block_info = result
            break

    if block_info is None:
        print(f"Error: Component '{component_id}' not found in any .rsx file under {app_dir}")
        sys.exit(1)

    start, end, tag_name = block_info
    content = open(found_file, "r", encoding="utf-8").read()
    subtree = content[start:end]

    # Strip leading blank lines but preserve the tag's own indentation reset to zero
    subtree = subtree.lstrip("\n")
    # Determine the common indent so we can de-indent the extracted block
    lines = subtree.split("\n")
    if lines:
        # Use the indent of the first line as the baseline
        first_indent = len(lines[0]) - len(lines[0].lstrip())
        if first_indent > 0:
            dedented = []
            for line in lines:
                if line.strip() == "":
                    dedented.append("")
                elif line[:first_indent].strip() == "":
                    dedented.append(line[first_indent:])
                else:
                    dedented.append(line)
            subtree = "\n".join(dedented)

    # Ensure subtree ends with a single newline
    subtree = subtree.rstrip("\n") + "\n"

    # 2. Write the extracted subtree to src/<component_id>.rsx
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write(subtree)
    print(f"Wrote: {dest_file}")

    # 3. Build the Include tag
    if found_is_main:
        include_path = f"./src/{component_id}.rsx"
    else:
        # Source is already inside src/ — use relative path from src/
        include_path = f"./{component_id}.rsx"

    # 4. Replace the subtree in the source file
    # For ModalFrame / SplitPaneFrame / DrawerFrame that are direct children of <App>,
    # place the Include as a direct child of App (top-level).
    # Otherwise, replace in-place.

    before = content[:start]
    after = content[end:]

    is_top_level_frame = tag_name in FRAME_TYPES

    if is_top_level_frame and found_is_main:
        # Remove the subtree (and surrounding whitespace/newline)
        # Then place the Include before </App>
        # Clean up: strip trailing whitespace AND newline from before, then rejoin
        new_content = before.rstrip() + "\n" + after.lstrip("\n")
        # Insert <Include .../> on its own line before closing </App>
        close_app_pattern = re.compile(r"^(</App>)", re.MULTILINE)
        m = close_app_pattern.search(new_content)
        if m:
            indent = "  "  # top-level child of App
            include_line = f'{indent}<Include src="{include_path}" />\n'
            insert_pos = m.start()
            new_content = new_content[:insert_pos] + include_line + new_content[insert_pos:]
        else:
            print("Warning: Could not find </App> tag; inserting Include at removal site.")
            indent = detect_indent(content, start)
            include_tag = f'{indent}<Include src="{include_path}" />'
            new_content = before + include_tag + "\n" + after
    else:
        # Replace in-place
        indent = detect_indent(content, start)
        include_tag = f'{indent}<Include src="{include_path}" />'
        # Preserve newline after the block
        new_content = before + include_tag + "\n" + after.lstrip("\n")

    with open(found_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated: {found_file}")
    print(f"Replaced '{component_id}' ({tag_name}) with <Include src=\"{include_path}\" />")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract a component subtree from an .rsx file into src/<name>.rsx"
    )
    parser.add_argument("app_dir", help="Path to the Retool app directory")
    parser.add_argument(
        "--component", required=True, help="The component id to extract"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.app_dir):
        print(f"Error: {args.app_dir} is not a directory")
        sys.exit(1)

    extract_component(args.app_dir, args.component)


if __name__ == "__main__":
    main()
