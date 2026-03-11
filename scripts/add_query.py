#!/usr/bin/env python3
"""Add a query definition to a Retool ToolScript app's functions.rsx.

Supports SELECT, INSERT, UPDATE_BY, DELETE_BY, BULK_UPDATE_BY_KEY,
BULK_UPSERT_BY_KEY, javascript, and sql-transform query types.
Uses regex-based parsing (RSX is NOT valid XML).
"""

import argparse
import json
import os
import re
import secrets
import sys


def gen_event_id():
    """Generate an 8-character hex event ID."""
    return secrets.token_hex(4)


def parse_event_action(action_str):
    """Parse an event action string into (pluginId, method, type, params).

    Examples:
        "selectProducts.trigger()" -> ("selectProducts", "trigger", "datasource", ...)
        "editModal.hide()"         -> ("editModal", "hide", "widget", ...)
        "isBulkUpdate.setValue(false)" -> ("isBulkUpdate", "setValue", "state", ...)
    """
    # Match: pluginId.method(args)
    m = re.match(r"(\w+)\.(\w+)\((.*)\)$", action_str.strip())
    if not m:
        print(
            f"Warning: Could not parse event action: {action_str}",
            file=sys.stderr,
        )
        return None

    plugin_id = m.group(1)
    method = m.group(2)
    args_str = m.group(3).strip()

    # Determine type
    datasource_methods = {"trigger"}
    state_methods = {"setValue", "setIn", "reset"}
    # widget methods: hide, show, close, selectRow, clearSelection, clearValue, etc.

    if method in datasource_methods:
        event_type = "datasource"
    elif method in state_methods:
        event_type = "state"
    else:
        event_type = "widget"

    # Build params
    if method == "trigger":
        params = "{{ ordered: [] }}"
    elif method == "setValue" and args_str:
        # Parse the value
        params = f'{{ ordered: [["value", {args_str}]] }}'
    elif method == "selectRow":
        params = "{{ ordered: [] }}"
    else:
        params = "{{}}"

    return (plugin_id, method, event_type, params)


def build_event_xml(action_str, indent="    "):
    """Build an Event RSX element from an action string."""
    parsed = parse_event_action(action_str)
    if parsed is None:
        return ""

    plugin_id, method, event_type, params = parsed
    eid = gen_event_id()

    wait_ms = "0"
    # For widget methods that need a slight delay
    if method in ("selectRow", "clearSelection"):
        wait_ms = "100"

    lines = [
        f"{indent}<Event",
        f'{indent}  id="{eid}"',
        f'{indent}  event="success"',
        f'{indent}  method="{method}"',
        f"{indent}  params={params}",
        f'{indent}  pluginId="{plugin_id}"',
        f'{indent}  type="{event_type}"',
        f'{indent}  waitMs="{wait_ms}"',
        f'{indent}  waitType="debounce"',
        f"{indent}/>",
    ]
    return "\n".join(lines)


def build_sql_query(args):
    """Build a SqlQueryUnified element."""
    indent = "  "
    child_indent = "    "
    lines = []

    # Determine query attribute
    if args.sql_file:
        query_attr = '{include("./lib/' + args.id + '.sql", "string")}'
    elif args.sql:
        query_attr = args.sql
    else:
        query_attr = f"SELECT * FROM {args.table}" if args.table else "SELECT 1"

    action_type = args.type.upper()

    lines.append(f"{indent}<SqlQueryUnified")
    lines.append(f'{indent}  id="{args.id}"')

    # Attributes in alphabetical order (after id)
    attrs = []

    if action_type in ("INSERT", "UPDATE_BY", "DELETE_BY", "BULK_UPDATE_BY_KEY", "BULK_UPSERT_BY_KEY"):
        attrs.append(('actionType', f'"{action_type}"'))

    if action_type in ("BULK_UPDATE_BY_KEY", "BULK_UPSERT_BY_KEY"):
        pk = args.bulk_primary_key or "id"
        attrs.append(('bulkUpdatePrimaryKey', f'"{pk}"'))

    if action_type in ("INSERT", "UPDATE_BY"):
        attrs.append(('changesetIsObject', '{true}'))
        if args.form:
            attrs.append(('changesetObject', '"{{ { ...' + args.form + '.data } }}"'))

    if action_type in ("DELETE_BY",) and args.confirm:
        attrs.append(('confirmationMessage', f'"{args.confirm}"'))

    if action_type in ("INSERT", "UPDATE_BY", "DELETE_BY", "BULK_UPDATE_BY_KEY", "BULK_UPSERT_BY_KEY"):
        attrs.append(('editorMode', '"gui"'))

    if action_type in ("UPDATE_BY", "DELETE_BY"):
        if args.filter_key and args.filter_ref:
            filter_val = (
                """{'[{"key":\""""
                + args.filter_key
                + """","value":"{{ """
                + args.filter_ref
                + """ }}","operation":"="}]'}"""
            )
            attrs.append(('filterBy', filter_val))

    if action_type == "SELECT":
        # Quote the query value
        if args.sql_file:
            attrs.append(('query', query_attr))
        else:
            attrs.append(('query', f'"{query_attr}"'))
        attrs.append(('resourceDisplayName', f'"{args.resource_name}"'))
        attrs.append(('resourceName', '"REPLACE_WITH_RESOURCE_UUID"'))
        attrs.append(('resourceTypeOverride', '""'))
        attrs.append(('transformer', '"return data"'))
        attrs.append(('warningCodes', '{[]}'))
    else:
        if action_type in ("BULK_UPDATE_BY_KEY", "BULK_UPSERT_BY_KEY"):
            records_ref = args.records_ref or "[]"
            attrs.append(('records', f'"{{{{ {records_ref} }}}}"'))

        if action_type in ("DELETE_BY",) and args.confirm:
            attrs.append(('requireConfirmation', '{true}'))

        attrs.append(('resourceDisplayName', f'"{args.resource_name}"'))
        attrs.append(('resourceName', '"REPLACE_WITH_RESOURCE_UUID"'))
        attrs.append(('resourceTypeOverride', '""'))
        attrs.append(('runWhenModelUpdates', '{false}'))
        if args.table:
            attrs.append(('tableName', f'"{args.table}"'))

    # Sort and emit attributes
    attrs.sort(key=lambda x: x[0])
    for key, val in attrs:
        lines.append(f"{indent}  {key}={val}")

    # Events
    events = []
    if args.on_success:
        for action in args.on_success.split(","):
            action = action.strip()
            if action:
                ev = build_event_xml(action, indent=child_indent)
                if ev:
                    events.append(ev)

    if events:
        lines.append(f"{indent}>")
        for ev in events:
            lines.append(ev)
        lines.append(f"{indent}</SqlQueryUnified>")
    else:
        lines.append(f"{indent}/>")

    return "\n".join(lines)


def build_js_query(args):
    """Build a JavascriptQuery element."""
    indent = "  "

    if args.js_file:
        query_attr = '{include("./lib/' + args.id + '.js", "string")}'
    elif args.js_body:
        query_attr = f'"{args.js_body}"'
    else:
        query_attr = '""'

    lines = [
        f"{indent}<JavascriptQuery",
        f'{indent}  id="{args.id}"',
        f"{indent}  query={query_attr}",
        f'{indent}  resourceDisplayName="JavascriptQuery"',
        f"{indent}  runWhenModelUpdates={{false}}",
    ]

    events = []
    if args.on_success:
        for action in args.on_success.split(","):
            action = action.strip()
            if action:
                ev = build_event_xml(action, indent="    ")
                if ev:
                    events.append(ev)

    if events:
        lines.append(f"{indent}>")
        for ev in events:
            lines.append(ev)
        lines.append(f"{indent}</JavascriptQuery>")
    else:
        lines.append(f"{indent}/>")

    return "\n".join(lines)


def build_sql_transform_query(args):
    """Build a SqlTransformQuery element."""
    indent = "  "

    if args.sql_file:
        query_attr = '{include("./lib/' + args.id + '.sql", "string")}'
    elif args.sql:
        query_attr = f'"{args.sql}"'
    else:
        query_attr = '"SELECT 1"'

    lines = [
        f"{indent}<SqlTransformQuery",
        f'{indent}  id="{args.id}"',
        f"{indent}  query={query_attr}",
        f'{indent}  resourceName="SQL Transforms"',
        f'{indent}  transformer="return data"',
    ]

    events = []
    if args.on_success:
        for action in args.on_success.split(","):
            action = action.strip()
            if action:
                ev = build_event_xml(action, indent="    ")
                if ev:
                    events.append(ev)

    if events:
        lines.append(f"{indent}>")
        for ev in events:
            lines.append(ev)
        lines.append(f"{indent}</SqlTransformQuery>")
    else:
        lines.append(f"{indent}/>")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Add a query to a Retool ToolScript app"
    )
    parser.add_argument("app_dir", help="Path to app directory")
    parser.add_argument(
        "--type",
        required=True,
        help="Query type: SELECT, INSERT, UPDATE_BY, DELETE_BY, "
        "BULK_UPDATE_BY_KEY, BULK_UPSERT_BY_KEY, javascript, sql-transform",
    )
    parser.add_argument("--id", required=True, help="Query ID")
    parser.add_argument("--table", help="Database table name")
    parser.add_argument("--form", help="Form ID for changeset binding")
    parser.add_argument("--filter-key", help="Column for filterBy")
    parser.add_argument("--filter-ref", help="Expression for filter value")
    parser.add_argument(
        "--on-success", help="Comma-separated success event chain"
    )
    parser.add_argument("--confirm", help="Confirmation message")
    parser.add_argument("--sql", help="Inline SQL")
    parser.add_argument(
        "--sql-file", action="store_true", help="Create lib/<id>.sql"
    )
    parser.add_argument("--js-body", help="Inline JS for javascript queries")
    parser.add_argument(
        "--js-file", action="store_true", help="Create lib/<id>.js"
    )
    parser.add_argument(
        "--resource-name",
        default="your-database",
        help="Resource display name",
    )
    parser.add_argument(
        "--bulk-primary-key", help="Primary key for bulk operations"
    )
    parser.add_argument(
        "--records-ref", help="Expression for bulk records"
    )

    args = parser.parse_args()

    app_dir = os.path.abspath(args.app_dir)
    functions_path = os.path.join(app_dir, "functions.rsx")
    if not os.path.isfile(functions_path):
        print(
            f"Error: functions.rsx not found: {functions_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(functions_path, "r") as f:
        content = f.read()

    # Determine query type and build XML
    qtype = args.type.lower().replace("_", "").replace("-", "")
    if qtype == "javascript":
        query_xml = build_js_query(args)
    elif qtype == "sqltransform":
        query_xml = build_sql_transform_query(args)
    else:
        # SQL query types
        query_xml = build_sql_query(args)

    # Create lib/ files if requested
    lib_dir = os.path.join(app_dir, "lib")
    if args.sql_file and args.sql:
        os.makedirs(lib_dir, exist_ok=True)
        sql_path = os.path.join(lib_dir, f"{args.id}.sql")
        with open(sql_path, "w") as f:
            f.write(args.sql)
            if not args.sql.endswith("\n"):
                f.write("\n")
        print(f"Created {sql_path}")

    if args.js_file and args.js_body:
        os.makedirs(lib_dir, exist_ok=True)
        js_path = os.path.join(lib_dir, f"{args.id}.js")
        with open(js_path, "w") as f:
            f.write(args.js_body)
            if not args.js_body.endswith("\n"):
                f.write("\n")
        print(f"Created {js_path}")

    # Insert before </GlobalFunctions>
    close_tag = "</GlobalFunctions>"
    insert_pos = content.rfind(close_tag)
    if insert_pos < 0:
        print(
            "Error: </GlobalFunctions> not found in functions.rsx",
            file=sys.stderr,
        )
        sys.exit(1)

    # Add blank line before new query if there's content before it
    prefix = content[:insert_pos].rstrip()
    if prefix.endswith("<GlobalFunctions>"):
        # Empty GlobalFunctions - just add newline
        new_content = prefix + "\n" + query_xml + "\n" + close_tag + "\n"
    else:
        new_content = prefix + "\n\n" + query_xml + "\n" + close_tag + "\n"

    # Write atomically
    tmp_path = functions_path + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(new_content)
    os.replace(tmp_path, functions_path)

    print(f"Added {args.type} query '{args.id}' to {functions_path}")


if __name__ == "__main__":
    main()
