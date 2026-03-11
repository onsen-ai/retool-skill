#!/usr/bin/env python3
"""
scaffold_app.py - Create a new Retool app directory from a template.

Usage:
    python scaffold_app.py "Expense Manager" --template crud --output-dir /tmp/test-apps
    python scaffold_app.py "Team Dashboard" --template advanced-crud --output-dir /tmp/test-apps

Templates: minimal, crud, master-detail, search-filter, chat, advanced-crud
"""

import os
import sys
import argparse
import shutil
import uuid
import secrets
import json
import re
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, '..', 'assets', 'examples')

TEMPLATE_MAP = {
    'minimal': 'Minimal App',
    'crud': 'CRUD Table App',
    'master-detail': 'Master-Detail App',
    'search-filter': 'Search Filter App',
    'chat': 'AI Chat App',
    'advanced-crud': 'Advanced CRUD App',
}

# Regex patterns for the different ID types found in .rsx files
# Column IDs: id="c01a1" (5-char hex, starts with 'c')
# Event IDs: id="aa11bb22" (8-char hex)
# Option IDs: id="a1b2c" (5-char hex, no 'c' prefix pattern)
# View IDs: id="detailsView" — these are NOT hex, leave alone
# Action IDs: id="a01a1" (5-char hex, starts with 'a')
# ToolbarButton IDs: id="tb01" (2-char hex after 'tb')
# Various option IDs like "t1a2b", "s1a2b", "f1a2b", "r1a1a", "ds1a1" etc.

# We identify hex IDs by scanning all id="..." attributes in .rsx files
# and classifying them by length and pattern.

# IDs we should NOT regenerate (they are semantic component IDs, not hex):
SEMANTIC_ID_PATTERN = re.compile(
    r'^(\$main|pageTitle|searchInput|chatBox|resetBtn|'
    r'[a-zA-Z]{2,}[A-Z][a-zA-Z]*|'  # camelCase names like productsTable, createModal
    r'[a-zA-Z]+View|'                 # view IDs like detailsView, activityView
    r'[a-zA-Z]+Pane|'                 # pane IDs like detailPane
    r'[a-zA-Z]+Form|'                 # form IDs like DetailForm
    r'[a-zA-Z]+Container)$'          # container IDs like detailContainer
)


def is_hex_id(id_val):
    """Determine if an id value is a hex-based ID that should be regenerated."""
    # Skip $main and other framework IDs
    if id_val.startswith('$'):
        return False

    # Check if it's a toolbar button ID (tb + 2 hex chars)
    if re.match(r'^tb[0-9a-f]{2}$', id_val):
        return True

    # Check if it's a pure hex ID (column, event, option, action patterns)
    # These are strings composed of hex chars [0-9a-f] only
    if re.match(r'^[0-9a-f]+$', id_val, re.IGNORECASE):
        return True

    # Check for IDs like "ds1a1", "r1a1a", "s1a2b", "t1a2b" etc.
    # These are short alphanumeric IDs with hex-like patterns
    if re.match(r'^[a-z]{1,2}[0-9a-f]+$', id_val) and len(id_val) <= 5:
        return True

    return False


def classify_hex_id(id_val):
    """Classify a hex ID to determine the generation strategy."""
    # Toolbar button: tb + 2 hex chars
    if re.match(r'^tb[0-9a-f]{2}$', id_val):
        return 'toolbar'

    # 8-char hex: events
    if re.match(r'^[0-9a-f]{8}$', id_val):
        return 'event'

    # 5-char patterns: columns (c...), actions (a...), options, etc.
    # All 5-char hex-like IDs
    if len(id_val) == 5:
        return 'short'

    # Anything else that passed is_hex_id
    return 'short'


def generate_new_id(id_type):
    """Generate a new unique ID based on type."""
    if id_type == 'toolbar':
        return 'tb' + secrets.token_hex(1)
    elif id_type == 'event':
        return secrets.token_hex(4)
    else:  # short (columns, options, actions)
        return secrets.token_hex(3)[:5]


def find_all_hex_ids_in_rsx(app_dir):
    """Scan all .rsx files and extract hex IDs from id="..." attributes."""
    hex_ids = set()
    rsx_files = glob.glob(os.path.join(app_dir, '**', '*.rsx'), recursive=True)

    for filepath in rsx_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Find all id="..." attributes
        for match in re.finditer(r'\bid="([^"]+)"', content):
            id_val = match.group(1)
            if is_hex_id(id_val):
                hex_ids.add(id_val)

    return hex_ids


def find_hex_ids_in_positions(app_dir):
    """Find hex IDs referenced in .positions.json files."""
    # .positions.json doesn't usually contain hex IDs as keys --
    # the keys are semantic component IDs. But some references like
    # groupByColumnId, primaryKeyColumnId in .rsx files reference column IDs.
    # We handle those through the rsx replacement.
    pass


def build_id_mapping(hex_ids):
    """Create old_id -> new_id mapping, ensuring no collisions."""
    mapping = {}
    used_ids = set()

    for old_id in hex_ids:
        id_type = classify_hex_id(old_id)
        # Generate unique new ID
        attempts = 0
        while True:
            new_id = generate_new_id(id_type)
            if new_id not in used_ids and new_id not in hex_ids:
                break
            attempts += 1
            if attempts > 100:
                raise RuntimeError(f"Could not generate unique ID after 100 attempts for {old_id}")
        mapping[old_id] = new_id
        used_ids.add(new_id)

    return mapping


def replace_ids_in_file(filepath, id_mapping):
    """Replace all old hex IDs with new ones in a file, using exact matching."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Sort by length descending to avoid partial replacements
    for old_id, new_id in sorted(id_mapping.items(), key=lambda x: len(x[0]), reverse=True):
        # For .rsx files: replace id="old_id" attributes
        content = content.replace(f'id="{old_id}"', f'id="{new_id}"')

        # Replace references like primaryKeyColumnId="old_id"
        content = content.replace(f'ColumnId="{old_id}"', f'ColumnId="{new_id}"')

        # Replace groupByColumnId="old_id"
        # (already handled by the ColumnId pattern above)

        # Replace pluginId references only if the old_id is used as a pluginId
        # (pluginIds are semantic names, not hex IDs, so we skip this)

        # Replace submitTargetId references (these are semantic, skip)

        # Replace targetContainerId references (these are semantic, skip)

    return content != original, content


def replace_ids_in_positions(filepath, id_mapping):
    """Replace hex IDs in .positions.json files.

    The keys in .positions.json are semantic component IDs, not hex IDs.
    However, we still check for any hex ID references in values.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Replace any hex IDs found in the JSON content
    for old_id, new_id in sorted(id_mapping.items(), key=lambda x: len(x[0]), reverse=True):
        # Use word-boundary matching to avoid partial replacements
        content = re.sub(r'(?<=["\s:])' + re.escape(old_id) + r'(?=["\s,}])', new_id, content)

    return content != original, content


def replace_ids_in_js(filepath, id_mapping):
    """Replace column ID references in .js files (e.g., columnId: "c02b2")."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    for old_id, new_id in sorted(id_mapping.items(), key=lambda x: len(x[0]), reverse=True):
        # Replace columnId: "old_id" patterns
        content = content.replace(f'"{old_id}"', f'"{new_id}"')

    return content != original, content


def update_page_title(app_dir, app_name):
    """Update the page title Text component to include the app name."""
    rsx_files = glob.glob(os.path.join(app_dir, '**', '*.rsx'), recursive=True)

    for filepath in rsx_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match the pageTitle Text component's value attribute
        # Patterns: value="### Products", value="### Hello, Retool!\nThis is..."
        # Replace the heading text with the app name
        new_content = re.sub(
            r'(id="pageTitle"[^>]*\n\s*(?:[^>]*\n\s*)*value=")###\s+[^"]*(")',
            rf'\g<1>### {app_name}\2',
            content
        )

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

    return False


def update_metadata(app_dir):
    """Generate a new pageUuid in metadata.json."""
    metadata_path = os.path.join(app_dir, 'metadata.json')
    if not os.path.exists(metadata_path):
        return False

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    old_uuid = metadata.get('pageUuid', '')
    new_uuid = str(uuid.uuid4())
    metadata['pageUuid'] = new_uuid

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        f.write('\n')

    return old_uuid, new_uuid


def scaffold_app(app_name, template, output_dir):
    """Main scaffolding function."""
    # Resolve template directory
    if template not in TEMPLATE_MAP:
        print(f"Error: Unknown template '{template}'.")
        print(f"Available templates: {', '.join(sorted(TEMPLATE_MAP.keys()))}")
        sys.exit(1)

    template_dir_name = TEMPLATE_MAP[template]
    template_dir = os.path.normpath(os.path.join(ASSETS_DIR, template_dir_name))

    if not os.path.isdir(template_dir):
        print(f"Error: Template directory not found: {template_dir}")
        sys.exit(1)

    # Create output directory
    app_dir = os.path.join(output_dir, app_name)
    if os.path.exists(app_dir):
        print(f"Error: Output directory already exists: {app_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Copy template
    shutil.copytree(template_dir, app_dir)
    print(f"Copied template '{template}' ({template_dir_name}) to {app_dir}")

    # Step 2: Update metadata with new pageUuid
    uuid_result = update_metadata(app_dir)
    if uuid_result:
        old_uuid, new_uuid = uuid_result
        print(f"Updated pageUuid: {old_uuid} -> {new_uuid}")

    # Step 3: Find all hex IDs and build mapping
    hex_ids = find_all_hex_ids_in_rsx(app_dir)
    if hex_ids:
        id_mapping = build_id_mapping(hex_ids)
        print(f"Regenerating {len(id_mapping)} hex IDs:")
        for old_id, new_id in sorted(id_mapping.items()):
            print(f"  {old_id} -> {new_id}")

        # Step 3a: Replace IDs in all .rsx files
        rsx_files = glob.glob(os.path.join(app_dir, '**', '*.rsx'), recursive=True)
        for filepath in rsx_files:
            changed, content = replace_ids_in_file(filepath, id_mapping)
            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Updated IDs in {os.path.relpath(filepath, app_dir)}")

        # Step 3b: Replace IDs in .positions.json
        positions_files = glob.glob(os.path.join(app_dir, '**', '.positions.json'), recursive=True)
        for filepath in positions_files:
            changed, content = replace_ids_in_positions(filepath, id_mapping)
            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Updated IDs in {os.path.relpath(filepath, app_dir)}")

        # Step 3c: Replace column ID references in .js files
        js_files = glob.glob(os.path.join(app_dir, '**', '*.js'), recursive=True)
        for filepath in js_files:
            changed, content = replace_ids_in_js(filepath, id_mapping)
            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Updated IDs in {os.path.relpath(filepath, app_dir)}")
    else:
        id_mapping = {}
        print("No hex IDs found to regenerate.")

    # Step 4: Update page title
    title_updated = update_page_title(app_dir, app_name)
    if title_updated:
        print(f"Updated page title to '### {app_name}'")
    else:
        print("Warning: Could not find pageTitle component to update.")

    # Summary
    all_files = []
    for root, dirs, files in os.walk(app_dir):
        for f in files:
            all_files.append(os.path.relpath(os.path.join(root, f), app_dir))

    print(f"\nScaffolded app '{app_name}' with {len(all_files)} files:")
    for f in sorted(all_files):
        print(f"  {f}")

    return app_dir, id_mapping


def main():
    parser = argparse.ArgumentParser(
        description='Create a new Retool app directory from a template.'
    )
    parser.add_argument(
        'app_name',
        help='Name for the new app (e.g., "Expense Manager")'
    )
    parser.add_argument(
        '--template', '-t',
        required=True,
        choices=sorted(TEMPLATE_MAP.keys()),
        help='Template to use'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='.',
        help='Output directory (default: current directory)'
    )

    args = parser.parse_args()
    scaffold_app(args.app_name, args.template, args.output_dir)


if __name__ == '__main__':
    main()
