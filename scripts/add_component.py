#!/usr/bin/env python3
"""Add a component to an existing Retool ToolScript app.

Updates both the .rsx file and .positions.json atomically.
Uses regex-based parsing (RSX is NOT valid XML).
"""

import argparse
import json
import os
import re
import sys

# Default heights by component type
DEFAULT_HEIGHTS = {
    "Text": 0.6,
    "TextInput": 1.0,
    "Select": 1.0,
    "Multiselect": 1.0,
    "DateRange": 1.0,
    "Date": 1.0,
    "Button": 1.0,
    "Switch": 1.0,
    "Checkbox": 1.0,
    "TextArea": 1.0,
    "Table": 13.2,
    "Chat": 17.4,
    "Form": 0.2,
    "Container": 0.2,
    "Divider": 0.2,
}

# Structural components that should NOT get marginType="normal"
STRUCTURAL_TYPES = {
    "Frame", "Form", "Container", "Header", "Body", "Footer", "View",
}


def parse_attrs(attrs_str):
    """Parse RSX attribute string into list of (key, raw_value) tuples.

    Handles:
      label=""              -> ("label", '""')
      placeholder="Search"  -> ("placeholder", '"Search..."')
      showClear={true}      -> ("showClear", '{true}')
      iconBefore="bold/x"   -> ("iconBefore", '"bold/x"')
    """
    if not attrs_str or not attrs_str.strip():
        return []

    attrs = []
    s = attrs_str.strip()
    i = 0
    while i < len(s):
        # skip whitespace
        while i < len(s) and s[i] in (" ", "\t", "\n"):
            i += 1
        if i >= len(s):
            break

        # read key
        key_start = i
        while i < len(s) and s[i] not in ("=", " ", "\t"):
            i += 1
        key = s[key_start:i]
        if not key:
            break

        # skip '='
        if i < len(s) and s[i] == "=":
            i += 1
        else:
            # boolean shorthand: just the key name means {true}
            attrs.append((key, "{true}"))
            continue

        # read value
        if i >= len(s):
            break

        if s[i] == '"':
            # quoted string value
            j = i + 1
            while j < len(s) and s[j] != '"':
                if s[j] == "\\":
                    j += 1
                j += 1
            val = s[i : j + 1]
            i = j + 1
        elif s[i] == "{":
            # JSX expression - find matching closing brace
            depth = 0
            j = i
            while j < len(s):
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                elif s[j] == '"':
                    j += 1
                    while j < len(s) and s[j] != '"':
                        if s[j] == "\\":
                            j += 1
                        j += 1
                elif s[j] == "'":
                    j += 1
                    while j < len(s) and s[j] != "'":
                        if s[j] == "\\":
                            j += 1
                        j += 1
                j += 1
            val = s[i : j + 1]
            i = j + 1
        else:
            # unquoted value (shouldn't normally happen in RSX)
            j = i
            while j < len(s) and s[j] not in (" ", "\t"):
                j += 1
            val = s[i:j]
            i = j

        attrs.append((key, val))

    return attrs


def build_component_xml(comp_type, comp_id, attrs, children, indent="    "):
    """Build RSX component string."""
    lines = []
    lines.append(f"{indent}<{comp_type}")
    lines.append(f'{indent}  id="{comp_id}"')

    # Add parsed attributes in alphabetical order
    parsed = parse_attrs(attrs) if attrs else []
    # Check if marginType is already specified
    has_margin = any(k == "marginType" for k, _ in parsed)
    # Add marginType if not structural and not already specified
    if not has_margin and comp_type not in STRUCTURAL_TYPES:
        parsed.append(("marginType", '"normal"'))
    # Sort attributes alphabetically (id already placed first)
    parsed.sort(key=lambda x: x[0])
    for key, val in parsed:
        lines.append(f"{indent}  {key}={val}")

    if children:
        lines.append(f"{indent}>")
        # indent children
        for child_line in children.strip().split("\n"):
            lines.append(f"{indent}  {child_line}")
        lines.append(f"{indent}</{comp_type}>")
    else:
        lines.append(f"{indent}/>")

    return "\n".join(lines)


def find_component_end(rsx_content, component_id):
    """Find the end position of a component block by its id.

    Returns the index right after the component's closing tag or self-closing />.
    """
    # Find the opening tag that contains id="component_id"
    # Pattern: <TagName ... id="component_id" ... /> or <TagName ... id="component_id" ...>...</TagName>
    id_pattern = re.compile(
        r'<(\w+)\s[^>]*?id="' + re.escape(component_id) + r'"',
        re.DOTALL,
    )
    match = id_pattern.search(rsx_content)
    if not match:
        return None, None

    tag_name = match.group(1)
    start_pos = match.start()

    # Now find if this is self-closing or has children
    # Scan forward from match to find either /> or >
    pos = match.end()
    while pos < len(rsx_content):
        if rsx_content[pos : pos + 2] == "/>":
            return start_pos, pos + 2
        elif rsx_content[pos] == ">":
            # Has children - find matching closing tag
            # Need to handle nested tags of same name
            depth = 1
            pos += 1
            open_pat = re.compile(r"<" + re.escape(tag_name) + r"[\s/>]")
            close_pat = re.compile(r"</" + re.escape(tag_name) + r"\s*>")
            while pos < len(rsx_content) and depth > 0:
                next_open = open_pat.search(rsx_content, pos)
                next_close = close_pat.search(rsx_content, pos)
                if next_close is None:
                    break
                if next_open and next_open.start() < next_close.start():
                    # Check if it's self-closing
                    tag_end = rsx_content.find(">", next_open.end())
                    if tag_end >= 0 and rsx_content[tag_end - 1] == "/":
                        # Self-closing, don't change depth
                        pos = tag_end + 1
                    else:
                        depth += 1
                        pos = next_open.end()
                else:
                    depth -= 1
                    if depth == 0:
                        return start_pos, next_close.end()
                    pos = next_close.end()
            return start_pos, pos
        pos += 1

    return start_pos, None


def find_component_before(rsx_content, component_id):
    """Find the start position of a component block by its id."""
    id_pattern = re.compile(
        r'<(\w+)\s[^>]*?id="' + re.escape(component_id) + r'"',
        re.DOTALL,
    )
    match = id_pattern.search(rsx_content)
    if not match:
        return None
    return match.start()


def main():
    parser = argparse.ArgumentParser(
        description="Add a component to a Retool ToolScript app"
    )
    parser.add_argument("app_dir", help="Path to app directory")
    parser.add_argument("--type", required=True, help="Component tag name")
    parser.add_argument("--id", required=True, help="Component ID")
    parser.add_argument(
        "--parent-frame", default="$main", help="Parent frame/container ID"
    )
    parser.add_argument("--after", help="ID of sibling to insert after")
    parser.add_argument("--before", help="ID of sibling to insert before")
    parser.add_argument("--attrs", default="", help="RSX attributes string")
    parser.add_argument(
        "--width", type=int, default=12, help="Column width (1-12)"
    )
    parser.add_argument(
        "--height", type=float, default=None, help="Row height"
    )
    parser.add_argument("--col", type=int, default=None, help="Column offset")
    parser.add_argument(
        "--same-row",
        action="store_true",
        help="Place on same row as --after component",
    )
    parser.add_argument(
        "--container", help="Container ID for position entry"
    )
    parser.add_argument(
        "--subcontainer", help="Subcontainer ID for position entry"
    )
    parser.add_argument(
        "--row-group",
        choices=["header", "footer"],
        help="Row group for form header/footer",
    )
    parser.add_argument(
        "--file", default="main.rsx", help="Which .rsx file to modify"
    )
    parser.add_argument("--children", default="", help="Inline RSX children")

    args = parser.parse_args()

    app_dir = os.path.abspath(args.app_dir)
    rsx_path = os.path.join(app_dir, args.file)
    if not os.path.isfile(rsx_path):
        # Check in src/ subdirectory
        rsx_path_alt = os.path.join(app_dir, "src", args.file)
        if os.path.isfile(rsx_path_alt):
            rsx_path = rsx_path_alt
        else:
            print(f"Error: RSX file not found: {rsx_path}", file=sys.stderr)
            sys.exit(1)

    positions_path = os.path.join(app_dir, ".positions.json")
    if not os.path.isfile(positions_path):
        print(
            f"Error: Positions file not found: {positions_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read files
    with open(rsx_path, "r") as f:
        rsx_content = f.read()
    with open(positions_path, "r") as f:
        positions = json.load(f)

    # Determine height
    comp_height = args.height
    if comp_height is None:
        comp_height = DEFAULT_HEIGHTS.get(args.type, 1.0)

    # Build component XML
    component_xml = build_component_xml(
        args.type, args.id, args.attrs, args.children
    )

    # Insert into RSX
    if args.after:
        _, end_pos = find_component_end(rsx_content, args.after)
        if end_pos is None:
            print(
                f'Error: Could not find component with id="{args.after}" in {rsx_path}',
                file=sys.stderr,
            )
            sys.exit(1)
        # Insert after the component, preserving newline
        rsx_content = (
            rsx_content[:end_pos] + "\n" + component_xml + rsx_content[end_pos:]
        )
    elif args.before:
        start_pos = find_component_before(rsx_content, args.before)
        if start_pos is None:
            print(
                f'Error: Could not find component with id="{args.before}" in {rsx_path}',
                file=sys.stderr,
            )
            sys.exit(1)
        # Insert before the component
        rsx_content = (
            rsx_content[:start_pos] + component_xml + "\n" + rsx_content[start_pos:]
        )
    else:
        # Insert before the closing tag of the parent frame
        parent_id = args.parent_frame
        # Find closing tag of parent
        _, parent_end = find_component_end(rsx_content, parent_id)
        if parent_end is None:
            # Try finding </Frame> as fallback
            close_match = re.search(r"</Frame>", rsx_content)
            if close_match:
                insert_pos = close_match.start()
            else:
                print(
                    f"Error: Could not find parent frame '{parent_id}'",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            # Find the closing tag within the parent
            close_tag = f"</Frame>"
            # We need to insert before the closing tag of the frame
            # Find </Frame> that ends at parent_end
            close_match = rsx_content.rfind(close_tag, 0, parent_end)
            if close_match >= 0:
                insert_pos = close_match
            else:
                insert_pos = parent_end
        rsx_content = (
            rsx_content[:insert_pos]
            + component_xml
            + "\n"
            + rsx_content[insert_pos:]
        )

    # Calculate position entry
    pos_entry = {}

    if args.container:
        pos_entry["container"] = args.container
    if args.subcontainer:
        pos_entry["subcontainer"] = args.subcontainer
    if args.row_group:
        pos_entry["rowGroup"] = args.row_group

    # Calculate row position
    if args.after and args.after in positions:
        after_pos = positions[args.after]
        if args.same_row:
            # Same row as --after
            after_row = after_pos.get("row", 0)
            pos_entry["row"] = after_row
        else:
            after_row = after_pos.get("row", 0)
            after_height = after_pos.get("height", 1.0)
            pos_entry["row"] = after_row + after_height
    elif args.before and args.before in positions:
        before_pos = positions[args.before]
        before_row = before_pos.get("row", 0)
        # Place at the same row as --before (before component will shift down)
        pos_entry["row"] = before_row
    # If no after/before, row defaults to 0 (omitted from JSON for row=0 in
    # some examples, but we include it for clarity)

    if args.col is not None and args.col > 0:
        pos_entry["col"] = args.col

    pos_entry["height"] = comp_height
    pos_entry["width"] = args.width

    # Add to positions
    positions[args.id] = pos_entry

    # Write files atomically (write to temp then rename)
    # Write RSX
    tmp_rsx = rsx_path + ".tmp"
    with open(tmp_rsx, "w") as f:
        f.write(rsx_content)
    os.replace(tmp_rsx, rsx_path)

    # Write positions
    tmp_pos = positions_path + ".tmp"
    with open(tmp_pos, "w") as f:
        json.dump(positions, f, indent=2)
        f.write("\n")
    os.replace(tmp_pos, positions_path)

    print(f"Added <{args.type} id=\"{args.id}\" /> to {rsx_path}")
    print(f"Updated {positions_path}")


if __name__ == "__main__":
    main()
