#!/usr/bin/env python3
"""Parse a Retool app directory and output a structured component tree.

Usage:
    python list_components.py <app-dir>                  # tree format (default)
    python list_components.py <app-dir> --format json    # machine-readable
    python list_components.py <app-dir> --format table   # tabular
"""

import re
import json
import os
import sys
import argparse

# ---------------------------------------------------------------------------
# RSX tokenizer (NOT XML — RSX has {true}, {{ expr }}, events={[{...}]}, etc.)
#
# A regex approach can't handle RSX's arbitrary brace nesting without
# catastrophic backtracking — real files contain events={[{ordered:[...]}]}
# prop values 6+ levels deep. Instead, we use a hand-rolled scanner: a simple
# regex finds tag-name starts, then a character loop consumes the attribute
# region while tracking string/brace state.
# ---------------------------------------------------------------------------

_TAG_START_RE = re.compile(r'<(/?)([A-Z][A-Za-z0-9_-]*|[a-z][A-Za-z0-9_]*)')


def _skip_quoted(s, i):
    """s[i] is a quote char. Return index just past the matching closing quote."""
    q = s[i]
    n = len(s)
    j = i + 1
    while j < n and s[j] != q:
        if s[j] == '\\' and j + 1 < n:
            j += 2
        else:
            j += 1
    return j + 1  # past closing quote (or past end if unterminated)


def _skip_braced(s, i):
    """s[i] is '{'. Return index just past the matching '}'."""
    n = len(s)
    depth = 1
    j = i + 1
    while j < n and depth > 0:
        c = s[j]
        if c == '"' or c == "'":
            j = _skip_quoted(s, j)
        elif c == '{':
            depth += 1
            j += 1
        elif c == '}':
            depth -= 1
            j += 1
        else:
            j += 1
    return j


def iter_tags(text):
    """Yield (is_close, tag, attrs_str, is_self_closing) for every tag.

    attrs_str excludes the trailing '/' on self-closing tags (matches the
    groups the old regex produced).
    """
    n = len(text)
    i = 0
    while i < n:
        m = _TAG_START_RE.search(text, i)
        if not m:
            return
        is_close = bool(m.group(1))
        tag = m.group(2)
        j = m.end()
        attrs_start = j
        found = False
        while j < n:
            c = text[j]
            if c == '>':
                attrs_str = text[attrs_start:j]
                stripped = attrs_str.rstrip()
                is_self_closing = stripped.endswith('/')
                if is_self_closing:
                    cut = attrs_str.rfind('/')
                    attrs_str = attrs_str[:cut]
                yield (is_close, tag, attrs_str, is_self_closing)
                i = j + 1
                found = True
                break
            if c == '"' or c == "'":
                j = _skip_quoted(text, j)
            elif c == '{':
                j = _skip_braced(text, j)
            else:
                j += 1
        if not found:
            return


def extract_attr(attrs_str, attr_name):
    """Extract a single attribute value from an attribute string.

    Returns: string value (for "..." / '...' / {...}), True for bare attrs,
    or None if not found.
    """
    target_len = len(attr_name)
    n = len(attrs_str)
    i = 0
    while i < n:
        c = attrs_str[i]
        # Skip past quoted strings and braced exprs so we don't match attr
        # names that appear inside an earlier attribute's value.
        if c == '"' or c == "'":
            i = _skip_quoted(attrs_str, i)
            continue
        if c == '{':
            i = _skip_braced(attrs_str, i)
            continue
        if c.isalpha() or c == '_':
            name_start = i
            while i < n and (attrs_str[i].isalnum() or attrs_str[i] in '_-'):
                i += 1
            name = attrs_str[name_start:i]
            # Skip whitespace between name and '='
            k = i
            while k < n and attrs_str[k].isspace():
                k += 1
            if k < n and attrs_str[k] == '=':
                k += 1
                while k < n and attrs_str[k].isspace():
                    k += 1
                if k >= n:
                    if name == attr_name:
                        return True
                    continue
                vc = attrs_str[k]
                if vc == '"' or vc == "'":
                    end = _skip_quoted(attrs_str, k)
                    if name == attr_name:
                        return attrs_str[k + 1:end - 1]
                    i = end
                    continue
                if vc == '{':
                    end = _skip_braced(attrs_str, k)
                    if name == attr_name:
                        return attrs_str[k + 1:end - 1]
                    i = end
                    continue
                # Unquoted value — skip one token
                end = k
                while end < n and not attrs_str[end].isspace():
                    end += 1
                if name == attr_name:
                    return attrs_str[k:end]
                i = end
                continue
            else:
                # Bare attribute (no '=')
                if name == attr_name:
                    return True
                continue
        i += 1
    return None


def extract_all_attrs(attrs_str):
    """Parse an attribute string into a dict. Handles arbitrary brace nesting."""
    attrs = {}
    n = len(attrs_str)
    i = 0
    while i < n:
        c = attrs_str[i]
        if c.isspace() or c == ',':
            i += 1
            continue
        if c == '"' or c == "'":
            # Stray value without a name — skip it.
            i = _skip_quoted(attrs_str, i)
            continue
        if c == '{':
            i = _skip_braced(attrs_str, i)
            continue
        if not (c.isalpha() or c == '_'):
            i += 1
            continue
        name_start = i
        while i < n and (attrs_str[i].isalnum() or attrs_str[i] in '_-'):
            i += 1
        name = attrs_str[name_start:i]
        # Whitespace before '='
        while i < n and attrs_str[i].isspace():
            i += 1
        if i >= n or attrs_str[i] != '=':
            attrs[name] = True
            continue
        i += 1  # past '='
        while i < n and attrs_str[i].isspace():
            i += 1
        if i >= n:
            attrs[name] = True
            break
        vc = attrs_str[i]
        if vc == '"' or vc == "'":
            end = _skip_quoted(attrs_str, i)
            attrs[name] = attrs_str[i + 1:end - 1]
            i = end
        elif vc == '{':
            end = _skip_braced(attrs_str, i)
            attrs[name] = attrs_str[i + 1:end - 1]
            i = end
        else:
            end = i
            while end < n and not attrs_str[end].isspace():
                end += 1
            attrs[name] = attrs_str[i:end]
            i = end
    return attrs


# ---------------------------------------------------------------------------
# Node representation
# ---------------------------------------------------------------------------

class Node:
    __slots__ = ('tag', 'id', 'attrs', 'children', 'events', 'parent',
                 'section', 'src_file')

    def __init__(self, tag, node_id, attrs, src_file=None):
        self.tag = tag
        self.id = node_id
        self.attrs = attrs          # dict of all attributes
        self.children = []          # list[Node]
        self.events = []            # list[dict] — summarised Event info
        self.parent = None
        self.section = None         # 'header' | 'body' | 'footer' | None
        self.src_file = src_file    # e.g. "src/editModal.rsx"

    def add_child(self, child):
        child.parent = self
        self.children.append(child)


# Tags that are structural wrappers, not real components
SECTION_TAGS = {'Header', 'Body', 'Footer'}
SKIP_TAGS = {'Event', 'Option', 'Include'}
CONTAINER_TAGS = {'App', 'GlobalFunctions'}


# ---------------------------------------------------------------------------
# Parse RSX text into a tree of Nodes
# ---------------------------------------------------------------------------

def parse_rsx(text, app_dir, src_annotation=None):
    """Parse RSX text and return a list of top-level Nodes."""
    nodes = []
    stack = []          # list of (Node | section_marker)
    section_stack = []  # tracks current Header/Body/Footer context

    for is_close, tag, attrs_str, is_self_closing in iter_tags(text):
        if tag == 'Include' and not is_close:
            src = extract_attr(attrs_str, 'src')
            if src and isinstance(src, str):
                inc_path = os.path.normpath(os.path.join(app_dir, src))
                if os.path.isfile(inc_path):
                    # Determine annotation (relative to app dir)
                    rel = os.path.relpath(inc_path, app_dir)
                    inc_text = _read_file(inc_path)
                    inc_nodes = parse_rsx(inc_text, app_dir, src_annotation=rel)
                    parent = stack[-1] if stack else None
                    for n in inc_nodes:
                        if src_annotation is None and rel != 'functions.rsx':
                            n.src_file = rel
                        if parent:
                            _apply_section(n, section_stack)
                            parent.add_child(n)
                        else:
                            nodes.append(n)
            continue

        if tag == 'Event':
            if not is_close and stack:
                ev = _parse_event(attrs_str)
                stack[-1].events.append(ev)
            continue

        if tag == 'Option':
            # Count options on parent
            continue

        if tag in SECTION_TAGS:
            if is_close:
                if section_stack:
                    section_stack.pop()
            elif not is_self_closing:
                section_stack.append(tag.lower())
            continue

        if tag == 'View':
            # View is a container section inside Container
            if is_close:
                if stack and stack[-1].tag == 'View':
                    stack.pop()
            elif not is_self_closing:
                all_attrs = extract_all_attrs(attrs_str)
                node_id = all_attrs.get('id', '')
                node = Node('View', node_id, all_attrs, src_file=src_annotation)
                parent = stack[-1] if stack else None
                if parent:
                    _apply_section(node, section_stack)
                    parent.add_child(node)
                else:
                    nodes.append(node)
                stack.append(node)
            continue

        if is_close:
            if stack and stack[-1].tag == tag:
                stack.pop()
            continue

        all_attrs = extract_all_attrs(attrs_str)
        node_id = all_attrs.get('id', '')
        node = Node(tag, node_id, all_attrs, src_file=src_annotation)

        parent = stack[-1] if stack else None
        if parent and tag not in CONTAINER_TAGS:
            _apply_section(node, section_stack)
            parent.add_child(node)
        else:
            if src_annotation and not node.src_file:
                node.src_file = src_annotation
            nodes.append(node)

        if not is_self_closing:
            stack.append(node)

    return nodes


def _apply_section(node, section_stack):
    if section_stack:
        node.section = section_stack[-1]


def _parse_event(attrs_str):
    """Extract useful info from an Event tag."""
    return {
        'event': extract_attr(attrs_str, 'event'),
        'method': extract_attr(attrs_str, 'method'),
        'pluginId': extract_attr(attrs_str, 'pluginId'),
        'type': extract_attr(attrs_str, 'type'),
        'params': extract_attr(attrs_str, 'params'),
    }


def _read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Count helpers
# ---------------------------------------------------------------------------

def _count_options(text_around_tag, tag_id):
    """Count <Option .../> children within a component in raw RSX."""
    return 0  # We'll count from re-scanning


def count_options_in_attrs(rsx_text, component_id):
    """Count Option tags that are children of a specific component."""
    count = 0
    depth = 0
    inside = False
    for is_close, tag, attrs_str, is_self_closing in iter_tags(rsx_text):
        if not is_close and not inside:
            cid = extract_attr(attrs_str, 'id')
            if cid == component_id:
                if is_self_closing:
                    return 0
                inside = True
                depth = 1
                continue

        if inside:
            if is_close:
                depth -= 1
                if depth <= 0:
                    break
            elif not is_self_closing:
                depth += 1
                if tag == 'Option':
                    count += 1
            else:
                if tag == 'Option':
                    count += 1

    return count


# ---------------------------------------------------------------------------
# Build full app tree
# ---------------------------------------------------------------------------

def build_app_tree(app_dir):
    """Parse all RSX files and return the root App node."""
    main_rsx = os.path.join(app_dir, 'main.rsx')
    if not os.path.isfile(main_rsx):
        print(f"Error: {main_rsx} not found", file=sys.stderr)
        sys.exit(1)

    text = _read_file(main_rsx)
    top_nodes = parse_rsx(text, app_dir)

    # Also read raw text for option counting
    all_rsx_text = _gather_all_rsx(app_dir)

    # Load positions
    positions = {}
    pos_path = os.path.join(app_dir, '.positions.json')
    if os.path.isfile(pos_path):
        with open(pos_path, 'r', encoding='utf-8') as f:
            positions = json.load(f)

    # Build a single root
    root = Node('App', '', {})
    for n in top_nodes:
        if n.tag == 'App':
            # Merge children from App wrapper
            for child in n.children:
                root.add_child(child)
            root.events = n.events
        elif n.tag == 'GlobalFunctions':
            root.add_child(n)
        else:
            root.add_child(n)

    return root, all_rsx_text, positions


def _gather_all_rsx(app_dir):
    """Read and concatenate all .rsx files for option counting."""
    parts = []
    for dirpath, _, filenames in os.walk(app_dir):
        for fn in sorted(filenames):
            if fn.endswith('.rsx'):
                parts.append(_read_file(os.path.join(dirpath, fn)))
    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Tree format rendering
# ---------------------------------------------------------------------------

def render_tree(root, all_rsx_text, positions):
    lines = []
    lines.append('App')
    _render_children(root, '', True, lines, all_rsx_text, positions)
    return '\n'.join(lines)


def _render_children(node, prefix, is_root, lines, all_rsx_text, positions):
    children = node.children
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        if is_root:
            connector = '\u2514\u2500\u2500 ' if is_last else '\u251c\u2500\u2500 '
            new_prefix = '    ' if is_last else '\u2502   '
        else:
            connector = '\u2514\u2500\u2500 ' if is_last else '\u251c\u2500\u2500 '
            new_prefix = prefix + ('    ' if is_last else '\u2502   ')

        label = _format_node(child, all_rsx_text, positions)
        section_prefix = ''
        if child.section and child.section in ('header', 'footer'):
            section_prefix = f'[{child.section}] '

        line = f'{prefix}{connector}{section_prefix}{label}'
        lines.append(line)
        _render_children(child, new_prefix, False, lines, all_rsx_text, positions)


def _format_node(node, all_rsx_text, positions):
    """Format a single node for tree display."""
    tag = node.tag
    nid = node.id
    parts = [tag]
    if nid:
        parts.append(nid)

    # Source annotation
    src_note = ''
    if node.src_file and node.src_file != 'functions.rsx':
        src_note = f' ({node.src_file})'

    # --- Type-specific formatting ---

    if tag == 'Text':
        val = node.attrs.get('value', '')
        if isinstance(val, str) and val:
            display = val.replace('\n', ' ')
            if len(display) > 30:
                display = display[:30] + '...'
            parts.append(f'"{display}"')

    elif tag in ('TextInput', 'TextArea', 'NumberInput', 'Date', 'DateRange',
                 'Checkbox', 'Switch', 'Radio', 'Rating', 'FileInput',
                 'RichTextEditor'):
        extras = _input_extras(node)
        if extras:
            parts.append(f'({extras})')

    elif tag in ('Select', 'Multiselect'):
        extras_list = []
        fdk = node.attrs.get('formDataKey')
        if fdk and isinstance(fdk, str):
            extras_list.append(f'formDataKey={fdk}')
        req = node.attrs.get('required')
        if req and req is not False and str(req) != 'false':
            extras_list.append('required')
        opt_count = count_options_in_attrs(all_rsx_text, nid)
        if opt_count:
            extras_list.append(f'{opt_count} options')
        if extras_list:
            parts.append(f'({", ".join(extras_list)})')

    elif tag == 'Table':
        cols, actions, toolbars = _count_table_children(node)
        summary = []
        if cols:
            summary.append(f'{cols} columns')
        if actions:
            summary.append(f'{actions} actions')
        if toolbars:
            summary.append(f'{toolbars} toolbar')
        if summary:
            parts.append(f'({", ".join(summary)})')

    elif tag == 'Column':
        label = node.attrs.get('label', '')
        key = node.attrs.get('key', '')
        if label:
            parts.append(f'"{label}"')
        if key:
            parts.append(f'(key={key})')

    elif tag == 'Action':
        label = node.attrs.get('label', '')
        if label:
            parts.append(f'"{label}"')
        target = _action_target(node)
        if target:
            parts.append(f'\u2192 {target}')

    elif tag == 'ToolbarButton':
        label = node.attrs.get('label', '')
        tb_type = node.attrs.get('type', '')
        if label:
            parts.append(f'"{label}"')
        if tb_type:
            parts.append(f'({tb_type})')

    elif tag == 'Button':
        submit = node.attrs.get('submit')
        text_val = node.attrs.get('text', '')
        if text_val and isinstance(text_val, str):
            display = text_val
            if len(display) > 30:
                display = display[:27] + '...'
            parts.append(f'"{display}"')
        extras = []
        if submit and submit is not False and str(submit) != 'false':
            extras.append('submit')
        target = _button_event_summary(node)
        if target:
            extras.append(f'\u2192 {target}')
        if extras:
            parts.append(f'({", ".join(extras)})')

    elif tag == 'Form':
        submit_target = _form_submit_target(node)
        if submit_target:
            parts.append(f'\u2192 {submit_target}')

    elif tag == 'State':
        val = node.attrs.get('value', '')
        if isinstance(val, str):
            # Strip {{ }} wrapper
            val = val.strip()
            if val.startswith('{{') and val.endswith('}}'):
                val = val[2:-2].strip()
            parts.append(f'= {val}')

    elif tag in ('SqlQueryUnified', 'SqlTransformQuery', 'JavascriptQuery',
                 'RESTQuery', 'GraphQLQuery'):
        extras = _query_extras(node)
        if extras:
            parts.append(extras)

    elif tag == 'Chat':
        target = node.attrs.get('queryTargetId', '')
        if target:
            parts.append(f'(query={target})')

    elif tag in ('Modal', 'ModalFrame'):
        pass  # Just show tag + id

    elif tag == 'SplitPaneFrame':
        pos = node.attrs.get('position', '')
        if pos and isinstance(pos, str):
            parts.append(f'({pos})')

    elif tag == 'Tabs':
        opt_count = count_options_in_attrs(all_rsx_text, nid)
        if opt_count:
            parts.append(f'({opt_count} tabs)')

    elif tag == 'Container':
        pass

    elif tag == 'View':
        label = node.attrs.get('label', '')
        view_key = node.attrs.get('viewKey', '')
        if label:
            parts.append(f'"{label}"')
        if view_key:
            parts.append(f'(viewKey={view_key})')

    elif tag == 'Tags':
        pass

    elif tag == 'GlobalFunctions':
        pass  # Just the tag name

    if src_note:
        parts.append(src_note)

    return ' '.join(parts)


def _input_extras(node):
    extras = []
    fdk = node.attrs.get('formDataKey')
    if fdk and isinstance(fdk, str):
        extras.append(f'formDataKey={fdk}')
    req = node.attrs.get('required')
    if req and req is not False and str(req) != 'false':
        extras.append('required')
    return ', '.join(extras)


def _count_table_children(node):
    cols = 0
    actions = 0
    toolbars = 0
    for c in node.children:
        if c.tag == 'Column':
            cols += 1
        elif c.tag == 'Action':
            actions += 1
        elif c.tag == 'ToolbarButton':
            toolbars += 1
    return cols, actions, toolbars


def _action_target(node):
    """Extract action target from Event children."""
    targets = []
    for ev in node.events:
        t = _event_target_str(ev)
        if t:
            targets.append(t)
    return ', '.join(targets) if targets else ''


def _button_event_summary(node):
    targets = []
    for ev in node.events:
        t = _event_target_str(ev)
        if t:
            targets.append(t)
    return ', '.join(targets) if targets else ''


def _form_submit_target(node):
    for ev in node.events:
        if ev.get('event') == 'submit':
            return _event_target_str(ev)
    return ''


def _query_extras(node):
    """Format query node: [actionType, flags] -> success chain."""
    parts_inner = []
    action_type = node.attrs.get('actionType', '')
    if action_type and isinstance(action_type, str):
        parts_inner.append(action_type)
    else:
        # Detect from query attribute
        query_val = node.attrs.get('query', '')
        if isinstance(query_val, str):
            q_upper = query_val.upper().strip()
            if q_upper.startswith('SELECT'):
                parts_inner.append('SELECT')
            elif q_upper.startswith('INSERT'):
                parts_inner.append('INSERT')
            elif q_upper.startswith('UPDATE'):
                parts_inner.append('UPDATE')
            elif q_upper.startswith('DELETE'):
                parts_inner.append('DELETE')
            elif 'include(' in query_val:
                # Can't determine from include, skip
                pass

    req_confirm = node.attrs.get('requireConfirmation')
    if req_confirm and req_confirm is not False and str(req_confirm) != 'false':
        parts_inner.append('requireConfirmation')

    bracket = f'[{", ".join(parts_inner)}]' if parts_inner else ''

    # Success event chain
    success_targets = []
    for ev in node.events:
        if ev.get('event') == 'success':
            t = _event_target_str(ev)
            if t:
                success_targets.append(t)

    chain = ', '.join(success_targets) if success_targets else ''

    result_parts = []
    if bracket:
        result_parts.append(bracket)
    if chain:
        result_parts.append(f'\u2192 {chain}')
    return ' '.join(result_parts)


def _event_target_str(ev):
    """Build a short target string from an Event dict."""
    plugin_id = ev.get('pluginId', '') or ''
    method = ev.get('method', '') or ''
    ev_type = ev.get('type', '') or ''
    params = ev.get('params', '') or ''

    if ev_type == 'script':
        # Extract from params map src
        if isinstance(params, str) and 'src' in params:
            # Try both quoted key and unquoted key forms
            m = re.search(r'(?:"src"|src)\s*:\s*"([^"]*)"', params)
            if m:
                return m.group(1)
        return f'{plugin_id}.{method}()' if plugin_id else method

    if plugin_id and method:
        return f'{plugin_id}.{method}()'
    if plugin_id:
        return f'{plugin_id}.trigger()'
    return method or ''


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def render_json(root, all_rsx_text, positions):
    return json.dumps(_node_to_dict(root, all_rsx_text, positions), indent=2)


def _node_to_dict(node, all_rsx_text, positions):
    d = {
        'type': node.tag,
    }
    if node.id:
        d['id'] = node.id
    if node.section:
        d['section'] = node.section
    if node.src_file:
        d['src'] = node.src_file
    if node.attrs:
        d['attrs'] = {k: v for k, v in node.attrs.items() if k != 'id'}

    if node.events:
        d['events'] = [
            {k: v for k, v in ev.items() if v is not None}
            for ev in node.events
        ]

    # Position data
    if node.id and node.id in positions:
        d['position'] = positions[node.id]

    # Option count for select-type
    if node.tag in ('Select', 'Multiselect', 'Tabs'):
        opt_count = count_options_in_attrs(all_rsx_text, node.id)
        if opt_count:
            d['optionCount'] = opt_count

    # Table child counts
    if node.tag == 'Table':
        cols, actions, toolbars = _count_table_children(node)
        d['columnCount'] = cols
        d['actionCount'] = actions
        if toolbars:
            d['toolbarButtonCount'] = toolbars

    if node.children:
        d['children'] = [
            _node_to_dict(c, all_rsx_text, positions)
            for c in node.children
        ]

    return d


# ---------------------------------------------------------------------------
# Table format
# ---------------------------------------------------------------------------

def render_table(root, all_rsx_text, positions):
    rows = []
    rows.append(f'{"TYPE":<20}{"ID":<25}{"PARENT":<20}KEY ATTRS')
    rows.append('-' * 90)
    _table_rows(root, '', rows, all_rsx_text)
    return '\n'.join(rows)


def _table_rows(node, parent_id, rows, all_rsx_text):
    for child in node.children:
        key_attrs = _key_attrs_summary(child, all_rsx_text)
        row = f'{child.tag:<20}{child.id:<25}{parent_id:<20}{key_attrs}'
        rows.append(row)
        _table_rows(child, child.id or child.tag, rows, all_rsx_text)


def _key_attrs_summary(node, all_rsx_text):
    """One-line summary of key attributes for table output."""
    parts = []
    tag = node.tag
    if tag == 'Text':
        val = node.attrs.get('value', '')
        if isinstance(val, str) and val:
            display = val.replace('\n', ' ')
            if len(display) > 40:
                display = display[:37] + '...'
            parts.append(f'value="{display}"')
    elif tag in ('TextInput', 'TextArea', 'Select', 'Multiselect', 'NumberInput',
                 'Date', 'DateRange', 'Checkbox', 'Switch'):
        fdk = node.attrs.get('formDataKey')
        if fdk:
            parts.append(f'formDataKey={fdk}')
        req = node.attrs.get('required')
        if req and str(req) != 'false':
            parts.append('required')
    elif tag == 'Column':
        label = node.attrs.get('label', '')
        key = node.attrs.get('key', '')
        if label:
            parts.append(f'label="{label}"')
        if key:
            parts.append(f'key={key}')
    elif tag in ('SqlQueryUnified', 'SqlTransformQuery', 'JavascriptQuery', 'RESTQuery'):
        at = node.attrs.get('actionType', '')
        if at:
            parts.append(f'actionType={at}')
    elif tag == 'State':
        val = node.attrs.get('value', '')
        if isinstance(val, str):
            parts.append(f'value={val}')
    elif tag == 'Button':
        text_val = node.attrs.get('text', '')
        submit = node.attrs.get('submit')
        if text_val:
            parts.append(f'text="{text_val}"')
        if submit and str(submit) != 'false':
            parts.append('submit')

    if node.src_file:
        parts.append(f'src={node.src_file}')

    return ', '.join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Parse a Retool app directory and output a component tree.'
    )
    parser.add_argument('app_dir', help='Path to the Retool app directory')
    parser.add_argument(
        '--format', '-f',
        choices=['tree', 'json', 'table'],
        default='tree',
        help='Output format (default: tree)'
    )
    args = parser.parse_args()

    app_dir = os.path.abspath(args.app_dir)
    if not os.path.isdir(app_dir):
        print(f"Error: {app_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    root, all_rsx_text, positions = build_app_tree(app_dir)

    if args.format == 'tree':
        print(render_tree(root, all_rsx_text, positions))
    elif args.format == 'json':
        print(render_json(root, all_rsx_text, positions))
    elif args.format == 'table':
        print(render_table(root, all_rsx_text, positions))


if __name__ == '__main__':
    main()
