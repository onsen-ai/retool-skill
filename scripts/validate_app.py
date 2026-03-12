#!/usr/bin/env python3
"""Validate a Retool ToolScript app directory against all import rules.

Usage: python validate_app.py <app-dir>
"""

import re
import json
import os
import sys
import argparse
import glob


# ---------------------------------------------------------------------------
# RSX regex-based parser
# ---------------------------------------------------------------------------

def _match_brace_expr(content, start):
    """Match a brace-delimited expression starting at content[start] == '{'.

    Returns the index past the closing '}', or -1 on failure.
    Handles arbitrary nesting depth, plus quoted strings inside braces.
    """
    if start >= len(content) or content[start] != '{':
        return -1
    depth = 0
    i = start
    n = len(content)
    while i < n:
        ch = content[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i + 1
        elif ch == '"':
            i += 1
            while i < n and content[i] != '"':
                if content[i] == '\\':
                    i += 1
                i += 1
        elif ch == "'":
            i += 1
            while i < n and content[i] != "'":
                if content[i] == '\\':
                    i += 1
                i += 1
        i += 1
    return -1


def _parse_tags(content):
    """Parse RSX content and yield (is_close, tag, attrs_str, is_self_close, pos) tuples.

    Uses a two-phase approach:
    1. Find tag start positions with a simple regex for `<TagName` or `</TagName`
    2. For opening tags, manually scan attributes handling {}-expressions with
       arbitrary nesting, then detect `/>` or `>` at the end.
    """
    # Find all potential tag starts: < followed by optional / and a tag name
    tag_start_re = re.compile(r'<(/?)([A-Z][A-Za-z0-9_-]*|[a-z][A-Za-z0-9_]*)')

    for m in tag_start_re.finditer(content):
        is_close = m.group(1) == '/'
        tag = m.group(2)
        after_name = m.end()

        if is_close:
            # Closing tag: find the >
            close_pos = content.find('>', after_name)
            if close_pos == -1:
                continue
            yield (True, tag, '', False, m.start())
            continue

        # Opening tag: scan attributes until we find > or />
        i = after_name
        n = len(content)
        attrs_start = i

        while i < n:
            # Skip whitespace
            while i < n and content[i] in ' \t\n\r':
                i += 1

            if i >= n:
                break

            # Check for end of tag
            if content[i] == '>':
                attrs_str = content[attrs_start:i]
                yield (False, tag, attrs_str, False, m.start())
                break
            if content[i] == '/' and i + 1 < n and content[i + 1] == '>':
                attrs_str = content[attrs_start:i]
                yield (False, tag, attrs_str, True, m.start())
                break

            # Must be an attribute name
            if content[i].isalpha() or content[i] == '_':
                # Scan attribute name
                j = i
                while j < n and (content[j].isalnum() or content[j] in '_-'):
                    j += 1
                # Check for = sign
                if j < n and content[j] == '=':
                    j += 1  # skip =
                    # Attribute value
                    if j < n and content[j] == '"':
                        # Double-quoted string - scan to closing "
                        j += 1
                        while j < n and content[j] != '"':
                            j += 1
                        if j < n:
                            j += 1  # skip closing "
                    elif j < n and content[j] == "'":
                        # Single-quoted string
                        j += 1
                        while j < n and content[j] != "'":
                            j += 1
                        if j < n:
                            j += 1
                    elif j < n and content[j] == '{':
                        # Brace expression with arbitrary nesting
                        end = _match_brace_expr(content, j)
                        if end > 0:
                            j = end
                        else:
                            j += 1  # skip and hope for the best
                i = j
            else:
                # Unexpected character; skip it to avoid infinite loop
                i += 1


def parse_rsx_file(filepath):
    """Parse RSX file and return list of component dicts.

    Each dict: {tag, id, parent_tag, parent_id, attrs, file, is_self_closing}
    """
    with open(filepath) as f:
        content = f.read()

    components = []
    stack = []  # [(tag, id)]

    id_pattern = re.compile(r'\bid="([^"]*)"')

    for is_close, tag, attrs_str, is_self_close, pos in _parse_tags(content):
        if is_close:
            if stack and stack[-1][0] == tag:
                stack.pop()
            continue

        id_match = id_pattern.search(attrs_str)
        comp_id = id_match.group(1) if id_match else None

        parent_tag = stack[-1][0] if stack else None
        parent_id = stack[-1][1] if stack else None

        components.append({
            'tag': tag,
            'id': comp_id,
            'parent_tag': parent_tag,
            'parent_id': parent_id,
            'attrs': attrs_str,
            'file': filepath,
            'is_self_closing': is_self_close,
        })

        if not is_self_close:
            stack.append((tag, comp_id))

    return components


def check_balanced_tags(filepath):
    """Check that RSX file has balanced open/close tags. Returns list of errors."""
    with open(filepath) as f:
        content = f.read()

    stack = []
    errors = []
    for is_close, tag, attrs_str, is_self_close, pos in _parse_tags(content):
        if is_self_close:
            continue
        if is_close:
            if stack and stack[-1] == tag:
                stack.pop()
            else:
                expected = stack[-1] if stack else '(empty stack)'
                errors.append(f"Unexpected closing </{tag}>, expected </{expected}> in {os.path.basename(filepath)}")
        else:
            stack.append(tag)

    for tag in reversed(stack):
        errors.append(f"Unclosed tag <{tag}> in {os.path.basename(filepath)}")

    return errors


def check_xml_comments(filepath):
    """Return list of XML comments found in a .rsx file."""
    with open(filepath) as f:
        content = f.read()
    return re.findall(r'<!--.*?-->', content, re.DOTALL)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_attr_value(attrs_str, attr_name):
    """Extract a named attribute value from attrs string. Returns the raw value or None.

    Handles "...", '...', and {...} attribute values with arbitrary nesting.
    """
    # Find the attribute name followed by =
    pattern = re.compile(r'\b' + re.escape(attr_name) + r'\s*=\s*')
    m = pattern.search(attrs_str)
    if not m:
        return None

    rest = attrs_str[m.end():]
    if not rest:
        return None

    if rest[0] == '"':
        end = rest.find('"', 1)
        if end >= 0:
            return rest[1:end]
    elif rest[0] == "'":
        end = rest.find("'", 1)
        if end >= 0:
            return rest[1:end]
    elif rest[0] == '{':
        end = _match_brace_expr(rest, 0)
        if end > 0:
            return rest[1:end - 1]  # strip outer braces
    return None


def has_attr(attrs_str, attr_name):
    """Check if an attribute exists in the attrs string."""
    pattern = re.compile(r'\b' + re.escape(attr_name) + r'(?:\s*=|\s|$)')
    return bool(pattern.search(attrs_str))


# ---------------------------------------------------------------------------
# Structural tags that should NOT have position entries
# ---------------------------------------------------------------------------

STRUCTURAL_TAGS = {
    'App', 'Include', 'GlobalFunctions', 'Folder',
    'Event', 'Column', 'Option', 'Property', 'Action', 'ToolbarButton',
    'Header', 'Body', 'Footer', 'View',
    'Frame',  # Frames with $ prefix
    # Frame-level containers (positioned by Retool layout, not .positions.json)
    'ModalFrame', 'SplitPaneFrame', 'DrawerFrame',
    # Query/state elements
    'SqlQueryUnified', 'JavascriptQuery', 'RESTQuery', 'SqlTransformQuery',
    'State', 'Function', 'OpenAPIQuery', 'S3Query', 'WorkflowRun',
}

MUTATION_ACTION_TYPES = {
    'INSERT', 'UPDATE_BY', 'DELETE_BY', 'BULK_UPDATE_BY_KEY', 'BULK_UPSERT_BY_KEY',
}


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

class ValidationResult:
    def __init__(self):
        self.results = []  # list of (status, message)

    def add(self, status, message):
        self.results.append((status, message))

    @property
    def pass_count(self):
        return sum(1 for s, _ in self.results if s == 'PASS')

    @property
    def fail_count(self):
        return sum(1 for s, _ in self.results if s == 'FAIL')

    @property
    def warn_count(self):
        return sum(1 for s, _ in self.results if s == 'WARN')


def validate_app(app_dir):
    vr = ValidationResult()
    app_dir = os.path.abspath(app_dir)
    app_name = os.path.basename(app_dir)

    # -----------------------------------------------------------------------
    # 1. Required files exist
    # -----------------------------------------------------------------------
    required = ['main.rsx', 'functions.rsx', 'metadata.json', '.positions.json']
    missing = [f for f in required if not os.path.isfile(os.path.join(app_dir, f))]
    if missing:
        vr.add('FAIL', f'Required files missing: {", ".join(missing)}')
    else:
        vr.add('PASS', 'Required files exist')

    # -----------------------------------------------------------------------
    # Collect all .rsx files
    # -----------------------------------------------------------------------
    rsx_files = []
    for root, dirs, files in os.walk(app_dir):
        for fname in files:
            if fname.endswith('.rsx'):
                rsx_files.append(os.path.join(root, fname))
    rsx_files.sort()

    # -----------------------------------------------------------------------
    # 2. RSX files parse correctly (balanced tags)
    # -----------------------------------------------------------------------
    all_balance_errors = []
    for rsx_file in rsx_files:
        errs = check_balanced_tags(rsx_file)
        all_balance_errors.extend(errs)

    if all_balance_errors:
        vr.add('FAIL', f'RSX tag balance errors: {"; ".join(all_balance_errors)}')
    else:
        vr.add('PASS', 'RSX files parse correctly')

    # -----------------------------------------------------------------------
    # 3. No XML comments
    # -----------------------------------------------------------------------
    comment_files = []
    for rsx_file in rsx_files:
        comments = check_xml_comments(rsx_file)
        if comments:
            comment_files.append(os.path.basename(rsx_file))

    if comment_files:
        vr.add('FAIL', f'XML comments found in: {", ".join(comment_files)}')
    else:
        vr.add('PASS', 'No XML comments')

    # -----------------------------------------------------------------------
    # Parse all RSX files and collect components
    # -----------------------------------------------------------------------
    all_components = []
    for rsx_file in rsx_files:
        all_components.extend(parse_rsx_file(rsx_file))

    # Build lookup by id
    comp_by_id = {}
    for c in all_components:
        if c['id']:
            comp_by_id[c['id']] = c

    # -----------------------------------------------------------------------
    # 4. Frame-level nesting: ModalFrame, SplitPaneFrame, DrawerFrame
    #    must be direct children of App (or root of their own file via Include)
    # -----------------------------------------------------------------------
    frame_types = {'ModalFrame', 'SplitPaneFrame', 'DrawerFrame'}
    frame_nesting_errors = []
    for c in all_components:
        if c['tag'] in frame_types:
            # Valid parents: App (if in main.rsx), or None (root of an included file)
            if c['parent_tag'] is not None and c['parent_tag'] != 'App':
                frame_nesting_errors.append(
                    f"{c['tag']} id={c['id']} is inside <{c['parent_tag']}> "
                    f"(expected direct child of <App> or file root) in {os.path.basename(c['file'])}"
                )

    if frame_nesting_errors:
        vr.add('FAIL', f'Frame-level nesting errors: {"; ".join(frame_nesting_errors)}')
    else:
        vr.add('PASS', 'Frame-level nesting correct')

    # -----------------------------------------------------------------------
    # 5. Form structure: every Form must have Header + Body + Footer children
    #    (some Forms set showHeader={false} and skip Header, which is valid)
    # -----------------------------------------------------------------------
    forms = [c for c in all_components if c['tag'] == 'Form']
    form_errors = []
    for form in forms:
        form_id = form['id']
        children = [c for c in all_components
                     if c['parent_tag'] == 'Form' and c['parent_id'] == form_id]
        child_tags = {c['tag'] for c in children}

        # Body is always required
        if 'Body' not in child_tags:
            form_errors.append(f"Form id={form_id} missing <Body>")

        # Footer: required if showFooter is not explicitly false
        show_footer = get_attr_value(form['attrs'], 'showFooter')
        if show_footer != 'false' and 'Footer' not in child_tags:
            form_errors.append(f"Form id={form_id} missing <Footer>")

        # Header: required if showHeader is explicitly true
        show_header = get_attr_value(form['attrs'], 'showHeader')
        if show_header == 'true' and 'Header' not in child_tags:
            form_errors.append(f"Form id={form_id} has showHeader=true but missing <Header>")

    if form_errors:
        vr.add('FAIL', f'Form structure errors: {"; ".join(form_errors)}')
    else:
        vr.add('PASS', f'Form structure valid ({len(forms)} form{"s" if len(forms) != 1 else ""})')

    # -----------------------------------------------------------------------
    # 6. Container has View children
    # -----------------------------------------------------------------------
    containers = [c for c in all_components if c['tag'] == 'Container']
    container_errors = []
    for cont in containers:
        cont_id = cont['id']
        # Views must be direct children of Container, NOT inside Body
        view_children = [c for c in all_components
                         if c['tag'] == 'View'
                         and c['parent_tag'] == 'Container'
                         and c['parent_id'] == cont_id]
        if not view_children:
            container_errors.append(f"Container id={cont_id} has no <View> direct children")

    if container_errors:
        vr.add('FAIL', f'Container View errors: {"; ".join(container_errors)}')
    else:
        if containers:
            vr.add('PASS', f'Container has View children ({len(containers)} container{"s" if len(containers) != 1 else ""})')
        else:
            vr.add('PASS', 'Container has View children (0 containers)')

    # -----------------------------------------------------------------------
    # 7. Table has Column children
    # -----------------------------------------------------------------------
    tables = [c for c in all_components if c['tag'] == 'Table']
    table_errors = []
    for tbl in tables:
        tbl_id = tbl['id']
        col_children = [c for c in all_components
                        if c['tag'] == 'Column'
                        and c['parent_tag'] == 'Table'
                        and c['parent_id'] == tbl_id]
        if not col_children:
            table_errors.append(f"Table id={tbl_id} has no <Column> children")

    if table_errors:
        vr.add('FAIL', f'Table Column errors: {"; ".join(table_errors)}')
    else:
        if tables:
            vr.add('PASS', f'Table has Column children ({len(tables)} table{"s" if len(tables) != 1 else ""})')
        else:
            vr.add('PASS', 'Table has Column children (0 tables)')

    # -----------------------------------------------------------------------
    # 8-12. Positions checks
    # -----------------------------------------------------------------------
    positions_path = os.path.join(app_dir, '.positions.json')
    positions = {}
    if os.path.isfile(positions_path):
        with open(positions_path) as f:
            positions = json.load(f)

    # 8. All visible components have positions
    visible_components = []
    for c in all_components:
        cid = c['id']
        if cid is None:
            continue
        tag = c['tag']

        # Skip structural tags
        if tag in STRUCTURAL_TAGS:
            continue

        visible_components.append(c)

    missing_positions = []
    for c in visible_components:
        cid = c['id']
        if cid not in positions:
            missing_positions.append(f"{c['tag']} id={cid}")

    if missing_positions:
        vr.add('FAIL', f'Missing position entries: {", ".join(missing_positions)}')
    else:
        vr.add('PASS', 'All visible components have positions')

    # 9. No View elements have position entries
    view_ids = {c['id'] for c in all_components if c['tag'] == 'View' and c['id']}
    view_pos_errors = [vid for vid in view_ids if vid in positions]
    if view_pos_errors:
        vr.add('FAIL', f'View elements have position entries: {", ".join(view_pos_errors)}')
    else:
        vr.add('PASS', 'No View position entries')

    # 10. Grid constraints: col + width <= 12
    grid_errors = []
    for comp_id, pos in positions.items():
        col = pos.get('col', 0)
        width = pos.get('width', 0)
        if col + width > 12:
            grid_errors.append(f"{comp_id}: col({col}) + width({width}) = {col + width} > 12")

    if grid_errors:
        vr.add('FAIL', f'Grid constraint violations: {"; ".join(grid_errors)}')
    else:
        vr.add('PASS', 'Grid constraints (col + width <= 12)')

    # 11. Container references in positions point to existing component IDs
    container_ref_errors = []
    all_ids = {c['id'] for c in all_components if c['id']}
    for comp_id, pos in positions.items():
        if 'container' in pos:
            ref = pos['container']
            if ref not in all_ids:
                container_ref_errors.append(f"{comp_id} references container '{ref}' which doesn't exist")
        if 'subcontainer' in pos:
            ref = pos['subcontainer']
            if ref not in all_ids:
                container_ref_errors.append(f"{comp_id} references subcontainer '{ref}' which doesn't exist")

    if container_ref_errors:
        vr.add('FAIL', f'Container reference errors: {"; ".join(container_ref_errors)}')
    else:
        vr.add('PASS', 'Position container references valid')

    # -----------------------------------------------------------------------
    # 13. All IDs globally unique
    # -----------------------------------------------------------------------
    id_counts = {}
    for c in all_components:
        cid = c['id']
        if cid is None:
            continue
        id_counts.setdefault(cid, []).append(c)

    duplicates = {cid: comps for cid, comps in id_counts.items() if len(comps) > 1}
    if duplicates:
        dup_details = []
        for cid, comps in duplicates.items():
            files = set(os.path.basename(c['file']) for c in comps)
            dup_details.append(f"{cid} ({len(comps)}x in {', '.join(files)})")
        vr.add('FAIL', f'Duplicate IDs: {"; ".join(dup_details)}')
    else:
        vr.add('PASS', 'All IDs unique')

    # -----------------------------------------------------------------------
    # 14. Column IDs match ^[0-9a-f]{5}$
    # -----------------------------------------------------------------------
    columns = [c for c in all_components if c['tag'] == 'Column' and c['id']]
    col_id_pattern = re.compile(r'^[0-9a-f]{5}$')
    bad_col_ids = [c['id'] for c in columns if not col_id_pattern.match(c['id'])]
    if bad_col_ids:
        vr.add('FAIL', f'Invalid Column IDs: {", ".join(bad_col_ids)}')
    else:
        vr.add('PASS', f'Column IDs are 5-char hex ({len(columns)} column{"s" if len(columns) != 1 else ""})')

    # -----------------------------------------------------------------------
    # 15. Event IDs match ^[0-9a-f]{8}$
    # -----------------------------------------------------------------------
    events = [c for c in all_components if c['tag'] == 'Event' and c['id']]
    event_id_pattern = re.compile(r'^[0-9a-f]{8}$')
    bad_event_ids = [c['id'] for c in events if not event_id_pattern.match(c['id'])]
    if bad_event_ids:
        vr.add('FAIL', f'Invalid Event IDs: {", ".join(bad_event_ids)}')
    else:
        vr.add('PASS', f'Event IDs are 8-char hex ({len(events)} event{"s" if len(events) != 1 else ""})')

    # -----------------------------------------------------------------------
    # 16. View IDs match ^[0-9a-f]{5}$
    #     In practice, View IDs use descriptive camelCase names (e.g. detailsView).
    #     We accept both 5-char hex and descriptive alphanumeric identifiers.
    # -----------------------------------------------------------------------
    views = [c for c in all_components if c['tag'] == 'View' and c['id']]
    view_id_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*$')
    bad_view_ids = [c['id'] for c in views if not view_id_pattern.match(c['id'])]
    if bad_view_ids:
        vr.add('FAIL', f'Invalid View IDs: {", ".join(bad_view_ids)}')
    else:
        if views:
            vr.add('PASS', f'View IDs are valid ({len(views)} view{"s" if len(views) != 1 else ""})')
        else:
            vr.add('PASS', 'View IDs are valid (0 views)')

    # -----------------------------------------------------------------------
    # 17. Option IDs match ^[0-9a-f]{5}$
    #     In practice, Option IDs use 5-char lowercase alphanumeric (e.g. t1a2b).
    #     We accept ^[a-z0-9]{5}$ to match actual usage.
    # -----------------------------------------------------------------------
    options = [c for c in all_components if c['tag'] == 'Option' and c['id']]
    option_id_pattern = re.compile(r'^[a-z0-9]{5}$')
    bad_option_ids = [c['id'] for c in options if not option_id_pattern.match(c['id'])]
    if bad_option_ids:
        vr.add('FAIL', f'Invalid Option IDs: {", ".join(bad_option_ids)}')
    else:
        if options:
            vr.add('PASS', f'Option IDs are 5-char alphanumeric ({len(options)} option{"s" if len(options) != 1 else ""})')
        else:
            vr.add('PASS', 'Option IDs are 5-char alphanumeric (0 options)')

    # -----------------------------------------------------------------------
    # 18. Query resource names
    # -----------------------------------------------------------------------
    query_resource_errors = []

    # SqlQueryUnified should have resourceName
    sql_queries = [c for c in all_components if c['tag'] == 'SqlQueryUnified']
    for q in sql_queries:
        resource_name = get_attr_value(q['attrs'], 'resourceName')
        if not resource_name:
            query_resource_errors.append(f"SqlQueryUnified id={q['id']} missing resourceName")

    # JavascriptQuery does NOT require resourceName — Retool infers it.
    # (resourceDisplayName="JavascriptQuery" and runWhenModelUpdates={false} are also unnecessary.)

    # SqlTransformQuery should have resourceName
    sqlt_queries = [c for c in all_components if c['tag'] == 'SqlTransformQuery']
    for q in sqlt_queries:
        resource_name = get_attr_value(q['attrs'], 'resourceName')
        if not resource_name:
            query_resource_errors.append(f"SqlTransformQuery id={q['id']} missing resourceName")

    if query_resource_errors:
        vr.add('FAIL', f'Query resource errors: {"; ".join(query_resource_errors)}')
    else:
        vr.add('PASS', 'Query resource names present')

    # -----------------------------------------------------------------------
    # 19. Mutations have runWhenModelUpdates={false}
    # -----------------------------------------------------------------------
    mutation_errors = []
    for q in sql_queries:
        action_type = get_attr_value(q['attrs'], 'actionType')
        if action_type and action_type in MUTATION_ACTION_TYPES:
            rwmu = get_attr_value(q['attrs'], 'runWhenModelUpdates')
            if rwmu != 'false':
                mutation_errors.append(
                    f"SqlQueryUnified id={q['id']} (actionType={action_type}) "
                    f"missing runWhenModelUpdates={{false}}"
                )

    if mutation_errors:
        vr.add('FAIL', f'Mutation query errors: {"; ".join(mutation_errors)}')
    else:
        vr.add('PASS', 'Mutations have runWhenModelUpdates=false')

    return app_name, vr


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Validate a Retool ToolScript app directory.')
    parser.add_argument('app_dir', help='Path to the app directory')
    args = parser.parse_args()

    if not os.path.isdir(args.app_dir):
        print(f"Error: '{args.app_dir}' is not a directory", file=sys.stderr)
        sys.exit(2)

    app_name, vr = validate_app(args.app_dir)

    print(f"\n=== Retool App Validation: {app_name} ===\n")
    for status, message in vr.results:
        print(f"[{status}] {message}")

    print(f"\nSummary: {vr.pass_count} PASS, {vr.fail_count} FAIL, {vr.warn_count} WARN")

    # JSON report
    report = {
        'app': app_name,
        'pass': vr.pass_count,
        'fail': vr.fail_count,
        'warn': vr.warn_count,
        'checks': [{'status': s, 'message': m} for s, m in vr.results],
    }
    print(f"\n{json.dumps(report, indent=2)}")

    sys.exit(1 if vr.fail_count > 0 else 0)


if __name__ == '__main__':
    main()
