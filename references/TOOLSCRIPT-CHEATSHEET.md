# ToolScript Cheatsheet

Condensed reference for generating importable Retool apps. For full details, see `TOOLSCRIPT-SPEC.md`.

---

## 1. Directory Structure

```
app-name/
├── .positions.json       # Component layout (REQUIRED)
├── metadata.json         # App metadata (REQUIRED)
├── main.rsx              # Entry point — <App> root (REQUIRED)
├── functions.rsx         # <GlobalFunctions> — queries, state (REQUIRED)
├── lib/                  # Extracted SQL/JS/CSS files
│   ├── queryName.sql
│   └── scriptName.js
└── src/                  # Extracted RSX components
    └── componentName.rsx
```

---

## 2. RSX Syntax

```jsx
<Component
  id="uniqueId"
  stringAttr="value"
  boolAttr={true}
  nullAttr={null}
  numberAttr={375}
  exprAttr="{{ widget.value }}"
  arrayAttr={[]}
  objectAttr={{ mode: "index", indexType: "display", index: 0 }}
  includeAttr={include("./lib/file.sql", "string")}
>
  <ChildComponent />
</Component>
```

- **String:** `attr="value"` — plain text or `{{ expression }}`
- **Boolean:** `attr={true}` or `attr={false}` — NOT `"true"`
- **Expression:** `attr="{{ widget.value }}"` — double curly braces
- **Include:** `attr={include("./lib/file.ext", "string")}` — external file
- **Comments:** Use `_comment="text"` attribute — **NEVER `<!-- -->`** (breaks import)

---

## 3. Nesting Rules

| Parent | Valid Direct Children |
|--------|---------------------|
| `<App>` | `Include`, `Frame`, `SplitPaneFrame`, `DrawerFrame`, `ModalFrame`, `AppStyles`, `DocumentTitle`, `UrlFragments` |
| `<Frame>` | Any visible component, `Include`, `Modal` |
| `<Container>` | `Header`, `View` (**must have ≥1 View**) |
| `<View>` | Any visible component |
| `<Form>` | `Header`, `Body`, `Footer` (**must have all three**), `Event` |
| `<Header>` / `<Body>` / `<Footer>` | Any visible component |
| `<Modal>` | `Form`, or any visible component |
| `<ModalFrame>` | `Header`, `Body` (**must be child of App, NOT Frame**) |
| `<DrawerFrame>` | `Header`, `Body` (**must be child of App, NOT Frame**) |
| `<SplitPaneFrame>` | `Form`, or any visible component (**must be child of App, NOT Frame**) |
| `<Table>` | `Column` (**must have ≥1**), `Action`, `ToolbarButton`, `Event`, `Include` |
| `<Select>` / `<Multiselect>` | `Option`, `Event` |
| `<Button>` / `<Action>` / `<ToolbarButton>` | `Event` |
| `<GlobalFunctions>` | `Folder`, `SqlQueryUnified`, `RESTQuery`, `JavascriptQuery`, `SqlTransformQuery`, `State`, `Function` |

**Leaf nodes** (no children): `Column`, `Option`, `Property`, `Event`, `Include`, `Text`, `TextInput`, `TextArea`, `Image`, `Date`, `Slider`, `Switch`, `Checkbox`, `NumberInput`, `Statistic`, `Divider`, `Spacer`, `State`, `Chat`.

**Button-like** (leaf except `Event` children): `Button`, `Select`, `Multiselect`, `DateRange`, `FileButton`.

---

## 4. ID Generation

| Type | Pattern | Regex | Generator |
|------|---------|-------|-----------|
| Component | camelCase/PascalCase | `^[a-zA-Z_]\w*$` | Human-chosen, descriptive |
| Frame | `$` + name | `^\$\w+$` | Fixed: `$main`, `$header` |
| Column | 5-hex | `^[0-9a-f]{5}$` | `secrets.token_hex(3)[:5]` |
| View | 5-hex | `^[0-9a-f]{5}$` | `secrets.token_hex(3)[:5]` |
| Option | 5-hex | `^[0-9a-f]{5}$` | `secrets.token_hex(3)[:5]` |
| Action | 5-hex | `^[0-9a-f]{5}$` | `secrets.token_hex(3)[:5]` |
| Event | 8-hex | `^[0-9a-f]{8}$` | `secrets.token_hex(4)` |
| ToolbarButton | 2-4 hex | `^[0-9a-f]{2,4}$` | `secrets.token_hex(1)` |
| pageUuid | UUID v4 | Standard | `uuid.uuid4()` |

**All IDs must be globally unique** across all .rsx files in the app.

---

## 5. Positioning

### Grid System
- **12-column grid**: `width` = 1–12, `col` = 0–11
- **Constraint**: `col + width <= 12`
- **Row units**: fractional, 0.2 increments. `row: 0` = top.

### Standard Sizes

| Component | Height | Width |
|-----------|--------|-------|
| Text/title | 0.6 | 12 |
| TextInput/Select/Button/DateRange/Date | 1.0 | 6–12 |
| TextArea | 1.0 | 12 |
| Table | 13.2 | 12 |
| Chat | 17.4 | 12 |
| Divider | 0.2 | 12 |
| Form/Container | 0.2 | 12 |

### Vertical Layout
```
Component 1: row=0,    height=0.6  (title)
Component 2: row=0.6,  height=1.0  (input)
Component 3: row=1.6,  height=1.0  (input)
Component 4: row=2.6,  height=13.2 (table)
```

### Horizontal Layout (same row)
```json
"leftInput":  { "row": 0.6, "col": 0, "height": 1, "width": 6 },
"rightInput": { "row": 0.6, "col": 6, "height": 1, "width": 6 }
```

### Filter Bar (4-across)
```json
"search":   { "row": 0.6, "col": 0, "height": 1, "width": 4 },
"category": { "row": 0.6, "col": 4, "height": 1, "width": 2 },
"status":   { "row": 0.6, "col": 6, "height": 1, "width": 2 },
"dateRange":{ "row": 0.6, "col": 8, "height": 1, "width": 2 },
"resetBtn": { "row": 0.6, "col": 10, "height": 1, "width": 2 }
```

### Container/Form Internals
```json
"formField": { "container": "MyForm", "row": 0, "height": 1, "width": 12 }
```

### Header/Footer (rowGroup)
```json
"title":  { "container": "MyForm", "rowGroup": "header", "height": 0.6, "width": 12 },
"saveBtn":{ "container": "MyForm", "rowGroup": "footer", "col": 6, "height": 1, "width": 6 }
```

### SplitPaneFrame/DrawerFrame Children
```json
"form": { "subcontainer": "detailPane", "height": 0.2, "width": 12 }
```

### View Transparency Rule
**NEVER** create a position entry for a `<View>`. Children of a View use:
```json
"DetailForm": { "container": "detailContainer", "subcontainer": "detailsView", "height": 0.2, "width": 12 }
```

### ModalFrame Children
```json
"modalTitle": { "subcontainer": "editModal", "rowGroup": "header", "height": 0.6, "width": 12 },
"modalForm":  { "subcontainer": "editModal", "height": 0.2, "width": 12 }
```

---

## 6. Critical Import Failures

These 9 rules cause "Failed import" errors if violated:

1. **ModalFrame/SplitPaneFrame/DrawerFrame must be under `<App>`**, not `<Frame>`
2. **Form requires Header + Body + Footer** (all three — use `showHeader={false}` to hide)
3. **Container requires ≥1 View** child (direct, not inside Body)
4. **View is transparent** in .positions.json — no position entry ever
5. **No XML comments** `<!-- -->` in any .rsx file (use `_comment` attribute)
6. **Every visible component needs a position entry** in .positions.json
7. **col + width ≤ 12** for every position entry
8. **4 required files**: main.rsx, functions.rsx, metadata.json, .positions.json
9. **All IDs globally unique**; hex formats must be exact (5-char/8-char)

---

## 7. Component Quick Reference

### Layout
```jsx
<Frame id="$main" type="main" padding="8px 12px" paddingType="normal" sticky={false} isHiddenOnDesktop={false} isHiddenOnMobile={false}>
<Container id="myContainer" enableFullBleed={true} padding="12px" showBody={true} showHeader={true}>
  <Header>...</Header>
  <View id="a1b2c" viewKey="tab1" label="Tab 1">...</View>
</Container>
<Form id="MyForm" requireValidation={true} resetAfterSubmit={true} showBody={true} showHeader={true} showFooter={true} padding="12px">
  <Header><Text id="title" value="#### Title" /></Header>
  <Body>...inputs...</Body>
  <Footer><Button id="btn" submit={true} submitTargetId="MyForm" text="Save" /></Footer>
  <Event id="hex8" event="submit" method="trigger" pluginId="queryId" type="datasource" waitMs="0" waitType="debounce" />
</Form>
<Modal id="myModal" buttonText="Open" closeOnOutsideClick={true} events={[]} modalHeightType="auto">
<ModalFrame id="myModalFrame" hidden={true} hideOnEscape={true} overlayInteraction={true} showOverlay={true} size="medium">
<SplitPaneFrame id="myPane" position="right" width="400px" hidden="{{ !table.selectedRow.id }}" _resizeHandleEnabled={true} enableFullBleed={true}>
<Tabs id="tabs" itemMode="static" navigateContainer={true} targetContainerId="containerId" value="{{ self.values[0] }}">
  <Option id="hex5" value="tab1" label="Tab 1" />
</Tabs>
```

### Data Display
```jsx
<Text id="title" value="### Heading\n{{ dynamic }}" verticalAlign="center" marginType="normal" />
<Table id="tbl" data="{{ query.data }}" primaryKeyColumnId="hex5" defaultSelectedRow={{ mode: "index", indexType: "display", index: 0 }} rowSelection="single" showBorder={true} showFooter={true} showHeader={true} templatePageSize={20}>
  <Column id="hex5" key="field" label="Label" format="string" alignment="left" position="center" size={200} />
  <Action id="hex5" icon="bold/interface-edit-pencil" label="Edit"><Event .../></Action>
  <ToolbarButton id="hex2" icon="bold/interface-text-formatting-filter-2" label="Filter" type="filter" />
</Table>
```

### Inputs
```jsx
<TextInput id="input" formDataKey="name" label="Name" labelPosition="top" placeholder="Enter..." required={true} showClear={true} marginType="normal" />
<TextArea id="area" formDataKey="desc" label="Description" labelPosition="top" autoResize={true} minLines={2} marginType="normal" />
<Select id="sel" itemMode="static" label="Category" labelPosition="top" showClear={true} showSelectionIndicator={true} marginType="normal">
  <Option id="hex5" value="opt1" label="Option 1" />
</Select>
<Select id="sel2" itemMode="mapped" data="{{ query.data }}" labels="{{ item.name }}" values="{{ item.id }}" label="Category" labelPosition="top" showClear={true} />
<DateRange id="dr" label="Date" labelPosition="top" showClear={true} marginType="normal">
  <Event id="hex8" event="change" method="trigger" pluginId="applyFilters" type="datasource" waitMs="0" waitType="debounce" />
</DateRange>
<Date id="dt" formDataKey="date" label="Date" labelPosition="top" dateFormat="d MMM yyyy" />
<Chat id="chat" queryTargetId="sendMessage" assistantName="AI" showHeader={true} showTimestamp={true} placeholder="Ask..." />
```

### Actions
```jsx
<Button id="btn" text="Save" submit={true} submitTargetId="FormId" marginType="normal" />
<Button id="btn" text="Cancel" styleVariant="outline" marginType="normal">
  <Event id="hex8" event="click" method="hide" params={{}} pluginId="modalId" type="widget" waitMs="0" waitType="debounce" />
</Button>
```

---

## 8. Query Patterns

### SELECT (raw SQL)
```jsx
<SqlQueryUnified id="selectItems"
  query={include("./lib/selectItems.sql", "string")}
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" transformer="return data" warningCodes={[]} />
```

### INSERT
```jsx
<SqlQueryUnified id="insertItem" actionType="INSERT"
  changesetIsObject={true} changesetObject="{{ { ...CreateForm.data } }}"
  editorMode="gui" resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items">
  <Event id="hex8" event="success" method="trigger" pluginId="selectItems" type="datasource" waitMs="0" waitType="debounce" />
  <Event id="hex8" event="success" method="close" params={{}} pluginId="createModal" type="widget" waitMs="0" waitType="debounce" />
</SqlQueryUnified>
```

### UPDATE_BY
```jsx
<SqlQueryUnified id="updateItem" actionType="UPDATE_BY"
  changesetIsObject={true} changesetObject="{{ { ...EditForm.data } }}"
  editorMode="gui" filterBy={'[{"key":"id","value":"{{ table.selectedRow.id }}","operation":"="}]'}
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items">
  <Event id="hex8" event="success" method="trigger" pluginId="selectItems" type="datasource" waitMs="0" waitType="debounce" />
  <Event id="hex8" event="success" method="selectRow" params={{ ordered: [["key", "{{ table.selectedRow.id }}"]] }} pluginId="table" type="widget" waitMs="100" waitType="debounce" />
</SqlQueryUnified>
```

### DELETE_BY
```jsx
<SqlQueryUnified id="deleteItem" actionType="DELETE_BY"
  editorMode="gui" filterBy={'[{"key":"id","value":"{{ table.selectedRow.id }}","operation":"="}]'}
  requireConfirmation={true} confirmationMessage="Delete **{{ table.selectedRow.name }}**?"
  resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items">
  <Event id="hex8" event="success" method="trigger" pluginId="selectItems" type="datasource" waitMs="0" waitType="debounce" />
  <Event id="hex8" event="success" method="clearSelection" params={{}} pluginId="table" type="widget" waitMs="100" waitType="debounce" />
</SqlQueryUnified>
```

### BULK_UPDATE_BY_KEY / BULK_UPSERT_BY_KEY
```jsx
<SqlQueryUnified id="bulkUpdate" actionType="BULK_UPDATE_BY_KEY"
  bulkUpdatePrimaryKey="id" records="{{ stateVar.value }}"
  editorMode="gui" resourceDisplayName="your-database" resourceName="REPLACE_WITH_RESOURCE_UUID"
  resourceTypeOverride="" runWhenModelUpdates={false} tableName="public.items">
  <Event ... />
</SqlQueryUnified>
```

### JavascriptQuery
```jsx
<JavascriptQuery id="applyFilters"
  query={include("./lib/applyFilters.js", "string")}
  resourceDisplayName="JavascriptQuery" runWhenModelUpdates={false} />
```

### RESTQuery
```jsx
<RESTQuery id="sendToAI"
  body='{"model":"gpt-4o","messages":[...]}'
  bodyType="raw" headers={'[{"key":"Content-Type","value":"application/json"}]'}
  query="chat/completions" type="POST" queryTimeout="60000"
  resourceDisplayName="your-api" resourceName="REPLACE_WITH_RESOURCE_UUID" resourceTypeOverride=""
  _additionalScope={{ array: ["message"] }} />
```

### SqlTransformQuery
```jsx
<SqlTransformQuery id="selectOptions"
  query="SELECT DISTINCT col AS label, col AS value FROM {{ mainQuery.data }} ORDER BY col"
  resourceName="SQL Transforms" transformer="return data" />
```

### State
```jsx
<State id="myFlag" value="{{ false }}" />
<State id="myList" value="{{ [] }}" />
```

---

## 9. Event Patterns

### Event Template
```jsx
<Event id="hex8char" event="eventName" method="methodName"
  params={{ ordered: [] }} pluginId="targetId" type="targetType"
  waitMs="0" waitType="debounce" />
```

### Common Events

| Trigger | event | method | type | pluginId | Notes |
|---------|-------|--------|------|----------|-------|
| Button click → trigger query | `click` | `trigger` | `datasource` | queryId | |
| Form submit → trigger query | `submit` | `trigger` | `datasource` | queryId | |
| Input change → trigger query | `change` | `trigger` | `datasource` | queryId | `waitMs="300"` for text |
| Query success → refresh data | `success` | `trigger` | `datasource` | selectQueryId | |
| Query success → hide modal | `success` | `hide` | `widget` | modalId | |
| Query success → show widget | `success` | `show` | `widget` | widgetId | |
| Query success → re-select row | `success` | `selectRow` | `widget` | tableId | `waitMs="100"` |
| Query success → clear selection | `success` | `clearSelection` | `widget` | tableId | `waitMs="100"` |
| Query success → set state | `success` | `setValue` | `state` | stateId | `params={{ ordered: [["value", X]] }}` |
| Button click → close modal | `click` | `close` | `widget` | modalId | `params={{}}` |
| Button click → hide widget | `click` | `hide` | `widget` | widgetId | `params={{}}` |
| Button click → clear widget | `click` | `clearValue` | `widget` | widgetId | `params={{}}` |
| Button click → clear form | `click` | `clear` | `widget` | formId | |
| Button click → run inline JS | `click` | `run` | `script` | `""` | `params={{ map: { src: "code" } }}` |
| Table action → run inline JS | `clickAction` | `run` | `script` | `""` | `params={{ map: { src: "code" } }}` |
| Table save → trigger query | `save` | `trigger` | `datasource` | saveQueryId | |

---

## 10. State & Filtering

### State Management
```jsx
<!-- Declare in GlobalFunctions -->
<State id="editingRowId" value="{{ null }}" />
<State id="isBulkUpdate" value="{{ false }}" />

<!-- Set via Event -->
<Event id="hex8" event="click" method="setValue"
  params={{ ordered: [["value", true]] }} pluginId="isBulkUpdate" type="state" waitMs="0" waitType="debounce" />
```

### Client-Side Filtering (setFilterStack)
```javascript
// lib/applyFilters.js
const filters = [];

if (searchInput.value) {
  filters.push({ columnId: "c02b2", operator: "includes", value: searchInput.value });
}
if (statusFilter.value) {
  filters.push({ columnId: "c04d4", operator: "=", value: statusFilter.value });
}
if (dateRange.value.start) {
  filters.push({ columnId: "c06f6", operator: ">=", value: dateRange.value.start });
}

const stack = filters.length > 0
  ? { filters, operator: "and" }
  : { filters: [], operator: "and" };

resultsTable.setFilterStack(stack);
```

**Filter operators:** `=`, `!=`, `>=`, `<=`, `>`, `<`, `isOneOf`, `includes`, `doesNotInclude`, `isEmpty`, `isNotEmpty`, `isTrue`, `isFalse`

### SqlTransformQuery (Derived Lookups)
```jsx
<SqlTransformQuery id="selectDepartments"
  query="SELECT DISTINCT department AS label, department AS value FROM {{ selectMembers.data }} ORDER BY department"
  resourceName="SQL Transforms" transformer="return data" />
```

---

## 11. Spec Section Index

| Section | Lines | Topic |
|---------|-------|-------|
| 1 | 1–28 | Format Overview |
| 2 | 30–68 | Directory & File Structure |
| 3 | 70–166 | RSX Syntax |
| 4 | 168–261 | Top-Level Elements |
| 5 | 264–452 | Layout & Container Components |
| 6 | 454–717 | Data Display Components |
| 7 | 718–985 | Input Components |
| 8 | 986–1056 | Action Components |
| 9 | 1057–1137 | Presentation Components |
| 10 | 1140–1335 | Query & Data System |
| 11 | 1336–1438 | lib/ File Patterns |
| 12 | 1441–1542 | Event System |
| 13 | 1544–1598 | Positioning System |
| 14 | 1600–1642 | Template Expressions |
| 17b | 1760–1792 | metadata.json Full Schema |
| 18 | 1795–2249 | App Generation Guide |
| 19 | 2250–2426 | App Pattern Recipes |
| A | 2427–2510 | Component Tag Reference |
| B | 2513–2541 | Icon Naming Convention |
