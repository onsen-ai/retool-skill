---
name: retool-app-builder
description: >
  Build, edit, and improve Retool apps using ToolScript (RSX format).
  Use this skill whenever the user mentions retool, toolscript, RSX,
  internal tool, admin panel, data management app, CRUD app, or wants
  to create any Retool application — whether from scratch, modifying
  an existing one, or improving it with production patterns.
  Also triggers for: retool import, retool zip, retool table, retool
  modal, retool form, retool filter, retool dashboard, retool chat,
  build internal app, admin dashboard, data editor.
---

# Retool App Builder

Build importable Retool apps using ToolScript/RSX — Retool's markup language for source-controlled apps.

## A. Orientation

This skill creates importable Retool apps. Each app is a directory containing RSX markup files, position layout JSON, and metadata — zipped for Retool import.

**Reference files** (paths relative to this skill):
- `references/TOOLSCRIPT-CHEATSHEET.md` — **READ FIRST.** Condensed rules for component nesting, positioning, IDs, queries, events.
- `references/TOOLSCRIPT-SPEC.md` — Full 2500-line spec. Use for deep lookups when the cheatsheet isn't enough.
- `assets/examples/` — 6 importable template apps (Minimal, CRUD Table, Master-Detail, Search Filter, AI Chat, Advanced CRUD).

**Scripts** in `scripts/` handle validation, scaffolding, and position math — use them instead of manual RSX editing whenever possible.

**Output contract:** ALWAYS produce a named directory with all required files (`main.rsx`, `functions.rsx`, `metadata.json`, `.positions.json`) AND a zip via `zip_app.sh`.

## B. Scripts Reference

| Script | Purpose | When to use |
|--------|---------|-------------|
| `validate_app.py <dir>` | Validate against all import rules | **ALWAYS** before zipping. Catches import-breaking errors. |
| `scaffold_app.py "Name" --template <type>` | Create app from template. Types: `minimal`, `crud`, `master-detail`, `search-filter`, `chat`, `advanced-crud` | Start here for **NEW** apps. |
| `list_components.py <dir>` | Show component tree | Start here for **EDIT/IMPROVE**. Understand the app without reading RSX. |
| `add_component.py <dir> --type T --id I ...` | Add component + update positions | Add components with correct layout math. |
| `add_query.py <dir> --type T --id I ...` | Add query with event chains | Add queries with proper attributes and events. |
| `extract_component.py <dir> --component ID` | Move subtree to src/ file | When main.rsx gets too large. |
| `fix_positions.py <dir>` | Recalculate vertical layout | Fix layout after adding/removing components. |
| `zip_app.sh <dir>` | Zip for Retool import (runs validate) | Final step — produces the importable zip. |

**Principle:** Prefer scripts over manual RSX editing. Scripts handle position math, ID generation, and file consistency automatically. Only edit RSX directly for complex customizations scripts can't handle (custom attribute values, conditional logic, complex nesting).

## C. Task Identification

Determine the mode based on what the user asks:

- **NEW** — "build me a retool app for..." → `scaffold_app.py` with closest template → customize → validate → zip
- **EDIT** — "add X to my retool app" / "change Y in this app" → `list_components.py` first → targeted changes → validate → zip
- **IMPROVE** — "make this app production-ready" / "review my app" → `list_components.py` → audit → apply changes → validate → zip

## D. Template Selection Matrix

For NEW apps, pick the closest template:

| User needs... | Template | Patterns included |
|---|---|---|
| Simple display, read-only data | `minimal` | Text, basic layout |
| Table + create/edit/delete modals | `crud` | Modal, ModalFrame, Form, SQL CRUD, State, event chains |
| Table + side panel editing | `master-detail` | SplitPaneFrame, Container+Tabs+View, dynamic width |
| Filtered data, search bar | `search-filter` | setFilterStack, DateRange, JavascriptQuery |
| AI/chat interface | `chat` | Chat component, RESTQuery, JavascriptQuery |
| Complex: bulk ops, filters, detail pane | `advanced-crud` | Everything above combined |
| Dashboard with stats | `minimal` | Manually add Statistic, KeyValue components |

Read the template example files from `assets/examples/<name>/` before customizing — understand what you're starting from.

## E. NEW App Workflow

1. **Read** `references/TOOLSCRIPT-CHEATSHEET.md` for rules
2. **Scaffold:**
   ```bash
   python scripts/scaffold_app.py "App Name" --template <type> --output-dir <path>
   ```
3. **Read ALL generated files** to understand the starting point
4. **Read the closest example** from `assets/examples/` for pattern reference
5. **Customize:** modify query SQL, component labels/attributes, column definitions, form fields
6. **Add new components:**
   ```bash
   python scripts/add_component.py <dir> --type TextInput --id searchInput --parent-frame '$main' --after pageTitle --attrs 'label="" placeholder="Search..."' --width 6
   ```
7. **Add new queries:**
   ```bash
   python scripts/add_query.py <dir> --type SELECT --id selectItems --table items --sql-file
   ```
8. **Extract if main.rsx is large:**
   ```bash
   python scripts/extract_component.py <dir> --component editModal
   ```
9. **Fix positions if needed:**
   ```bash
   python scripts/fix_positions.py <dir>
   ```
10. **Validate:**
    ```bash
    python scripts/validate_app.py <dir>
    ```
    Fix ALL failures before proceeding.
11. **Zip:**
    ```bash
    bash scripts/zip_app.sh <dir>
    ```

## F. EDIT Workflow

1. **Understand the app:**
   ```bash
   python scripts/list_components.py <dir>
   ```
2. **Read specific files** that need changes
3. **Make targeted modifications** using scripts where possible:
   - Adding components → `add_component.py`
   - Adding queries → `add_query.py`
   - Extracting to src/ → `extract_component.py`
4. **For complex changes** (modifying existing attributes, rewiring events), edit RSX directly
5. **Fix positions:**
   ```bash
   python scripts/fix_positions.py <dir>
   ```
6. **Validate:**
   ```bash
   python scripts/validate_app.py <dir>
   ```
7. **Zip:**
   ```bash
   bash scripts/zip_app.sh <dir>
   ```

## G. IMPROVE Workflow + Audit Checklist

1. **Understand the app:**
   ```bash
   python scripts/list_components.py <dir>
   ```
2. **Read functions.rsx** fully to understand query patterns
3. **Audit against checklist:**
   - [ ] Destructive queries (DELETE) have `requireConfirmation={true}`?
   - [ ] Mutation queries have success events that refresh data?
   - [ ] After update: does it re-select the updated row (`selectRow`)?
   - [ ] After delete: does it clear selection (`clearSelection`)?
   - [ ] Forms have `loading="{{ query.isFetching }}"` and `disableSubmit="{{ query.isFetching }}"`?
   - [ ] Could dropdown options use SqlTransformQuery instead of separate queries?
   - [ ] Could filtering use client-side `setFilterStack()` instead of SQL WHERE?
   - [ ] Are State variables used for UI mode flags (bulk update, editing state)?
   - [ ] Does the app have proper event chains (mutate → refresh → UI update)?
   - [ ] Are ModalFrame/SplitPaneFrame/DrawerFrame children of App (not Frame)?
4. **Present findings** and proposed changes to user
5. **Apply approved improvements**
6. **Validate + zip**

## H. Manual Editing Reference

For when scripts aren't sufficient — the critical rules to follow:

### Nesting
- ModalFrame/SplitPaneFrame/DrawerFrame must be children of `<App>` (not `<Frame>`)
- Form requires `<Header>` + `<Body>` + `<Footer>` (all three; use `showHeader={false}` to hide)
- Container requires at least one `<View>` direct child (not inside Body)
- Table requires at least one `<Column>` child

### Positioning
- Every visible component needs a `.positions.json` entry
- View is transparent — no position entry ever
- `col + width <= 12`
- Children inside a View use `container: parentContainerId` + `subcontainer: viewId`
- Header/footer items use `rowGroup: "header"` or `rowGroup: "footer"`
- ModalFrame children use `subcontainer: modalId`

### IDs
- All IDs globally unique across all .rsx files
- Columns/Views/Options/Actions: 5-char hex `[0-9a-f]{5}`
- Events: 8-char hex `[0-9a-f]{8}`

### Syntax
- No `<!-- comments -->` — use `_comment="text"` attribute
- Boolean: `{true}` not `"true"`
- Expressions: `{{ widget.value }}`
- Include: `{include("./lib/file.sql", "string")}`

For deeper reference: read `references/TOOLSCRIPT-CHEATSHEET.md` or the full spec.

## I. Quick Templates

### main.rsx skeleton
```jsx
<App>
  <Include src="./functions.rsx" />
  <Frame id="$main" type="main" padding="8px 12px" paddingType="normal" sticky={false}
    isHiddenOnDesktop={false} isHiddenOnMobile={false}>
    <Text id="pageTitle" value="### App Title" verticalAlign="center" marginType="normal" />
  </Frame>
</App>
```

### functions.rsx skeleton
```jsx
<GlobalFunctions>
</GlobalFunctions>
```

### metadata.json template
```json
{
  "toolscriptVersion": "1.0.0",
  "version": "43.0.9",
  "pageUuid": "00000000-0000-0000-0000-000000000001",
  "appTemplate": {
    "appMaxWidth": "100%",
    "appThemeId": -1,
    "experimentalFeatures": { "object": { "sourceControlTemplateDehydration": false } },
    "notificationsSettings": { "object": { "globalQueryShowFailureToast": true, "globalQueryShowSuccessToast": true, "globalQueryToastDuration": 4.5 } },
    "version": "3.338.0"
  }
}
```

### .positions.json minimal
```json
{
  "pageTitle": { "row": 0, "height": 0.6, "width": 12 }
}
```

### Event template
```jsx
<Event id="hex8char" event="success" method="trigger"
  params={{ ordered: [] }} pluginId="queryId" type="datasource"
  waitMs="0" waitType="debounce" />
```

### SELECT query one-liner
```jsx
<SqlQueryUnified id="selectItems" query={include("./lib/selectItems.sql", "string")}
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" transformer="return data" warningCodes={[]} />
```

### INSERT one-liner
```jsx
<SqlQueryUnified id="insertItem" actionType="INSERT" changesetIsObject={true}
  changesetObject="{{ { ...CreateForm.data } }}" editorMode="gui"
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items">
  <Event id="hex8" event="success" method="trigger" pluginId="selectItems" type="datasource" waitMs="0" waitType="debounce" />
</SqlQueryUnified>
```

### UPDATE_BY one-liner
```jsx
<SqlQueryUnified id="updateItem" actionType="UPDATE_BY" changesetIsObject={true}
  changesetObject="{{ { ...EditForm.data } }}" editorMode="gui"
  filterBy={'[{"key":"id","value":"{{ table.selectedRow.id }}","operation":"="}]'}
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items" />
```

### DELETE_BY one-liner
```jsx
<SqlQueryUnified id="deleteItem" actionType="DELETE_BY" editorMode="gui"
  filterBy={'[{"key":"id","value":"{{ table.selectedRow.id }}","operation":"="}]'}
  requireConfirmation={true} confirmationMessage="Delete **{{ table.selectedRow.name }}**?"
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items" />
```
