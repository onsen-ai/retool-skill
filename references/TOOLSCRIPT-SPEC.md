# Retool Toolscript Specification

> Reverse-engineered from 10 reference apps. Cross-referenced with official Retool docs.
> Includes generative layer (Sections 18–19) with ID rules, nesting constraints, positioning recipes, and 5 importable example apps.
> Generated: 2026-03-11 | Toolscript Version: 1.0.0 | Retool Platform: 3.179.0–3.338.0

---

## 1. Format Overview

**Toolscript** is Retool's JSX-like markup language for serializing apps in source control. It uses the `.rsx` (Retool Scripting XML) file extension and replaced the deprecated YAML format (removed Q2 2025).

### Key Characteristics
- XML/JSX-like syntax with self-closing tags, boolean/expression attributes, and nesting
- Component ordering reflects canvas position: top-to-bottom, then left-to-right
- Omits default values to produce cleaner diffs
- Attributes starting with `_` are internal/editor metadata (not user-editable)
- Available since Retool 3.6.0 (Cloud and Self-hosted Edge 3.33+)

### Versioning
Three version numbers coexist:
- **`toolscriptVersion`**: Always `"1.0.0"` across all observed apps
- **`version`**: App snapshot version, always `"43.0.9"` in all observed apps
- **`appTemplate.version`**: Retool platform version (e.g., `"3.179.0"` to `"3.338.0"`)

### IDE Support
Set language mode to "JavaScript (JSX)" in VS Code for `.rsx` files.

---

## 2. Directory & File Structure

### Directory Layout
```
app-name/
├── .positions.json          # Single-file positions (older format)
├── .positions/              # Per-page positions (newer format)
│   ├── .global_positions.json
│   ├── .pageName.positions.json
│   ├── .global_mobile_positions.json
│   └── .pageName.mobilePositions.json
├── .defaults.json           # Component defaults at serialization (auto-generated)
├── metadata.json            # App version, settings, experimental features
├── main.rsx                 # Entry point — <App> root with Includes
├── functions.rsx            # <GlobalFunctions> — all queries, state, functions
├── header.rsx               # <Frame id="$header"> — nav bar / header
├── lib/                     # Extracted code files
│   ├── queryName.sql        # SQL queries
│   ├── functionName.js      # JavaScript query/function bodies
│   ├── $appStyles.css       # Global CSS
│   ├── params.json          # Workflow parameters
│   └── script.query         # Query files (rare)
└── src/                     # Extracted RSX components
    ├── containerName.rsx    # Containers, drawers, modals
    └── expandedRow.rsx      # Table expanded row templates
```

### Fixed File Names
- `main.rsx` — always the entry point
- `functions.rsx` — always contains `<GlobalFunctions>`
- `metadata.json` — always contains app metadata

### File Naming Conventions
- `src/` files: named after the root component `id` (e.g., `splitPaneFrame1.rsx`)
- `lib/` SQL files: named after the query `id` (e.g., `selectUsers.sql`)
- `lib/` JS files: named after the query/function `id` (e.g., `onTemplateChange.js`)
- `lib/$appStyles.css`: always prefixed with `$`

---

## 3. RSX Syntax

### Tags & Attributes
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
  orderedAttr={{ ordered: [{ key: "value" }] }}
  mapAttr={{ map: { key: "value" } }}
  includeAttr={include("./lib/file.sql", "string")}
>
  <ChildComponent />
</Component>
```

### Template Expressions (`{{ }}`)
Used in string attribute values for dynamic data binding:
```jsx
value="{{ widgetId.value }}"                              // Component value
data="{{ queryName.data }}"                               // Query results
disabled="{{ query.isFetching }}"                         // Query state
hidden="{{ retoolContext.environment === 'production' }}" // Environment check
caption="{{ currentSourceRow.fieldName }}"                // Table row context
label="{{ item.name }}"                                   // Iterator variable
text="{{ self.value ? 'On' : 'Off' }}"                   // Self-reference
```

### Built-in Context Variables
| Variable | Context | Description |
|----------|---------|-------------|
| `self` | Any component | Self-reference (`self.value`, `self.values[0]`, `self.viewKeys[0]`, `self.currentViewKey`) |
| `currentSourceRow` | Table Column | Current row data (source, pre-sort) |
| `currentRow` | TableLegacy | Current row data |
| `item` | Column/Select/ListViewBeta | Current cell value or iterator item |
| `i` | ListViewBeta/Action | Current iteration index |
| `ri` | Nested ListViewBeta | Row index array (`ri[0]` = parent list index) |
| `retoolContext` | Global | Environment, pages, currentPage |
| `current_user` | Global | email, fullName, profilePhotoUrl |
| `localStorage` | Global | Persisted local storage values |

### Built-in Utility Functions
| Function | Description |
|----------|-------------|
| `formatDataAsArray(data)` | Normalize query data to row array |
| `formatDataAsObject(data)` | Normalize query data to object |
| `utils.exportData(data, filename, format)` | Export data to file |
| `utils.playSound(dataUri)` | Play audio |
| `utils.copyToClipboard(text)` | Copy to clipboard |
| `numbro(value).format(options)` | Number formatting |
| `_` (lodash) | Full lodash library |
| `moment()` | Moment.js (implied) |

### `include()` Directive
Loads external file content as a string attribute value:
```jsx
query={include("./lib/selectUsers.sql", "string")}
funcBody={include("./lib/compute.js", "string")}
css={include("./lib/$appStyles.css", "string")}
workflowParams={include("../lib/params.json", "string")}
```
- Always two arguments: relative path + `"string"`
- Path is relative to the file containing the include
- `../lib/` used from screen-level queries (one directory deeper)

### `style` Attribute Patterns
Three serialization formats observed (all valid):
```jsx
// 1. Ordered array (preserves key order, most common)
style={{ ordered: [{ background: "canvas" }, { border: "transparent" }] }}

// 2. Map wrapper
style={{ map: { background: "#fafafa" } }}

// 3. Flat object (on Table, Text)
style={{ border: "rgb(204,204,204)", borderRadius: "8px", accent: "rgb(70,166,124)" }}
```

### `_disclosedFields` Pattern
Controls which style fields are visible in the Retool editor:
```jsx
_disclosedFields={{ array: ["primary-surface", "accent-background"] }}
_disclosedFields={["color"]}
```

### `_comment` Attribute
Annotation/metadata attribute for adding developer comments to any component:
```jsx
_comment="This container holds the main search interface"
```

---

## 4. Top-Level Elements

### `<App>`
Root element of `main.rsx`. No attributes. Children: `Include`, `AppStyles`, `DocumentTitle`, `UrlFragments`, `Frame`.

### `<AppStyles>`
Global CSS injection.
```jsx
<AppStyles id="$appStyles" css={include("./lib/$appStyles.css", "string")} />
```
**Apps:** Image Lab, Iris Atlas v2, Experience Studio

### `<DocumentTitle>`
Browser tab title.
```jsx
<DocumentTitle id="$customDocumentTitle" value="Iris Atlas" />
```
**Apps:** Iris Atlas v2

### `<UrlFragments>`
URL hash parameter binding for deep linking.
```jsx
<UrlFragments
  id="$urlFragments"
  value={{ ordered: [
    { map: { key: "category", pageLoadValueOverride: "{{ ... }}" } },
    { map: { key: "template", pageLoadValueOverride: "{{ ... }}" } }
  ] }}
/>
```
**Apps:** Prompt Studio

### `<Include>`
File inclusion directive.
```jsx
<Include src="./functions.rsx" />
<Include src="./header.rsx" />
<Include src="./src/componentName.rsx" />
```

### `<Frame>`
Top-level page section. Two special IDs:
- `$header` — sticky header bar (type `"header"`)
- `$main` — main content area (type `"main"`)
- `$main2`, `$main3` — additional main frames for multi-page apps

```jsx
<Frame
  id="$header"
  type="header"
  sticky={true}
  padding="8px 12px"
  isHiddenOnDesktop={false}
  isHiddenOnMobile={true}
>
  <Module id="onsenNavBar1" name="Onsen :: NavBar" pageUuid="uuid" margin="0" />
</Frame>
```

| Attribute | Type | Values |
|-----------|------|--------|
| `id` | string | `"$header"`, `"$main"`, `"$main2"` |
| `type` | string | `"header"`, `"main"` |
| `sticky` | bool/null | `true`, `null` |
| `padding` | string | `"8px 12px"`, `"0"` |
| `paddingType` | string | `"normal"`, `"none"` |
| `enableFullBleed` | bool/null | `true`, `false`, `null` |
| `isHiddenOnDesktop` | bool | |
| `isHiddenOnMobile` | bool | |
| `style` | object | ordered array |
| `_disclosedFields` | object | |

### `<GlobalFunctions>`
Root element of `functions.rsx`. No attributes. Contains all queries, state, and functions.
```jsx
<GlobalFunctions>
  <Folder id="queries">
    <SqlQueryUnified ... />
  </Folder>
  <State id="myState" value="{{ [] }}" />
  <Function id="compute" funcBody={include("./lib/compute.js", "string")} runBehavior="debounced" />
</GlobalFunctions>
```

### `<Folder>`
Organizes queries/state/functions within `<GlobalFunctions>` or `<Screen>`.
```jsx
<Folder id="crud">
  <SqlQueryUnified ... />
  <JavascriptQuery ... />
</Folder>
```

---

## 5. Layout & Container Components

### `<Container>`
Multi-view container with optional header/footer. Acts as stack layout or tabbed container.

| Attribute | Type | Example | Notes |
|-----------|------|---------|-------|
| `id` | string | `"AppContainer"` | |
| `_direction` | string | `"vertical"` | Stack direction |
| `_gap` | string/number | `"0px"`, `"10px"`, `0` | Gap between children |
| `_type` | string | `"stack"` | Layout type |
| `_align` | string | `"center"` | Cross-axis alignment |
| `_justify` | string | `"center"`, `"space-between"`, `"end"` | Main-axis alignment |
| `_flexWrap` | bool | | Enable wrapping |
| `currentViewKey` | string/expr | `"{{ self.viewKeys[0] }}"` | Active view |
| `enableFullBleed` | bool | `true` | Full width |
| `heightType` | string | `"fixed"`, `"fill"` | |
| `hoistFetching` | bool | `true` | |
| `loading` | string | `"{{ query.isFetching }}"` | |
| `margin` | string | `"0"` | |
| `overflowType` | string | `"hidden"`, `"pagination"` | |
| `padding` | string | `"12px"`, `"0"` | |
| `paddingType` | string | `"normal"`, `"none"` | |
| `showBody` | bool/string | `true`, `"{{ toggle.value }}"` | |
| `showBorder` | bool | | |
| `showFooter` | bool | | |
| `showHeader` | bool/string | | |
| `showHeaderBorder` | bool/string | | |
| `style` | object | ordered/map/flat | |
| `styleContext` | object | `{{ map: { borderRadius: "8px" } }}` | |
| `transition` | string | `"slide"` | View transition |
| `footerPadding` | string | `"4px 12px"` | |
| `footerPaddingType` | string | `"normal"`, `"none"` | |
| `headerPadding` | string | `"4px 12px"` | |
| `headerPaddingType` | string | `"normal"`, `"none"` | |

**Children:** `<Header>`, `<Body>`, `<Footer>`, `<View>`

**Apps:** All 9 apps

### `<Header>` / `<Body>` / `<Footer>`
Structural slots within Container, Form, DrawerFrame, ModalFrame. No own attributes.

### `<View>`
Tab/view pane within a Container.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | `"a8c58"` (hex) |
| `viewKey` | string | `"Messages"`, `"View 1"` |
| `label` | string | `"Preview"` |
| `icon` | string | `"bold/..."` |
| `iconPosition` | string | `"left"` |
| `disabled` | bool/expr | |
| `hidden` | bool/expr | |

### `<SplitPaneFrame>`
Resizable side panel.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | `"splitPaneFrame1"` |
| `_resizeHandleEnabled` | bool | `true` |
| `enableFullBleed` | bool | |
| `position` | string | `"right"` |
| `width` | string | `"500px"`, `"50%"`, `"{{ expr }}"` |
| `hidden` | string/bool | |
| `isHiddenOnMobile` | bool | |
| `padding` | string | |
| `showFooterBorder` | bool | |
| `showHeaderBorder` | bool | |

**Apps:** AI Guide Studio, Prompt Studio, Iris Atlas v2, Experience Studio

### `<DrawerFrame>`
Slide-out drawer panel.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | `"SuperpowersDrawer"` |
| `hidden` | bool | `true` (initially hidden) |
| `hideOnEscape` | bool | `true` |
| `overlayInteraction` | bool | `true` |
| `showOverlay` | bool | `true` |
| `width` | string | `"medium"`, `"large"`, `"1200px"` |
| `enableFullBleed` | bool | |
| `showFooter` | bool | |
| `showHeader` | bool | |
| `isHiddenOnMobile` | bool | |
| `padding` | string | |

**Apps:** AI Guide Studio, Prompt Studio, Experience Studio

### `<ModalFrame>`
Modal dialog overlay (top-level, included via `<Include>`).

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `hidden` | bool | `true` |
| `hideOnEscape` | bool | |
| `overlayInteraction` | bool | |
| `showOverlay` | bool | |
| `size` | string | `"medium"`, `"large"`, `"fullScreen"` |
| `enableFullBleed` | bool | |
| `showFooter` | bool | |
| `showHeader` | bool | |
| `showHeaderBorder` | bool | |
| `isHiddenOnMobile` | bool | |
| `padding` | string | `"0"`, `"8px 12px"` |

**Apps:** Iris AI Images, Prompt Studio, Iris Atlas v2, Experience Studio

### `<Modal>`
Inline modal with trigger button (sits in component tree, not top-level).

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | `"modal1"` |
| `buttonText` | string | `"Add AI persona"` |
| `closeOnOutsideClick` | bool | `true` |
| `hidden` | string | `"true"` |
| `modalHeightType` | string | `"auto"` |
| `modalWidth` | string | `"350"`, `"800px"` |
| `events` | array | `{[]}` |

**Apps:** AI Guide Studio, Katalog, Prompt Studio

### `<Form>`
Data entry form with validation and submit handling.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `disableSubmit` | expr | `"{{ query.isFetching }}"` |
| `disabled` | expr | |
| `initialData` | expr | `"{{ table.selectedSourceRow }}"` |
| `loading` | expr | |
| `requireValidation` | bool | |
| `resetAfterSubmit` | bool | |
| `scroll` | bool | |
| `hoistFetching` | bool | |
| `showBody`/`showFooter`/`showHeader` | bool | |
| `showBorder` | bool | |
| `hidden` | expr | |
| `style` | object | |

**Children:** `<Header>`, `<Body>`, `<Footer>`, `<Event>`

### `<ListViewBeta>`
Repeating list/grid layout.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `_primaryKeys` | expr | `"{{ i }}"` |
| `data` | expr | `"{{ query.data }}"` |
| `heightType` | string | `"auto"`, `"fill"` |
| `itemWidth` | string | `"200px"` |
| `layoutType` | string | `"grid"` |
| `numColumns` | number/string | `3` |
| `enableInstanceValues` | bool | |
| `margin` | string | |
| `padding` | string | |
| `hidden` | string | |

**Magic variables:** `item` (current item), `i` (index), `ri` (nested indices array)

**Apps:** Image Lab, Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio

### `<ListView>`
Older list view (non-Beta).

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `instances` | expr | |
| `rowKeys` | expr | |
| `showBorder` | bool | |
| `showDropShadow` | bool | |
| `formDataKey` | string | |
| `hidden` | expr | |

**Apps:** Prompt Studio

### `<TabbedContainer>` → see `<Container>` with `<Tabs>`
Tabbed layout is achieved via `<Container>` + `<Tabs navigateContainer={true} targetContainerId="...">`.

---

## 6. Data Display Components

### `<Table>`
Full-featured data table (modern version).

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `data` | expr | `"{{ query.data }}"` |
| `cellSelection` | string | `"none"` |
| `clearChangesetOnSave` | bool | |
| `defaultSelectedRow` | object | `{{ mode: "index"/"none", indexType: "display"/"data", index: 0 }}` |
| `defaultSort` | array | `{[{ object: { columnId: "id", direction: "desc" } }]}` |
| `dynamicRowHeights` | bool | |
| `emptyMessage` | string | |
| `enableExpandableRows` | bool | |
| `enableSaveActions` | bool | |
| `heightType` | string | `"auto"`, `"fill"` |
| `primaryKeyColumnId` | string | |
| `rowBackgroundColor` | expr | |
| `rowHeight` | string | `"small"`, `"medium"`, `"large"` |
| `rowSelection` | string | `"none"`, `"single"`, `"multiple"` |
| `searchMode` | string | `"caseInsensitive"`, `"caseSensitive"` |
| `searchTerm` | expr | |
| `showBorder` | bool | |
| `showColumnBorders` | bool | |
| `showFooter` | bool | |
| `showHeader` | bool | |
| `toolbarPosition` | string | `"bottom"` |
| `templatePageSize` | number | `20` |
| `actionsOverflowPosition` | number | |
| `autoColumnWidth` | bool | |
| `alwaysShowRowSelectionCheckboxes` | bool | |
| `persistRowSelection` | bool | |
| `includeRowInChangesetArray` | bool | |
| `overflowType` | string | `"pagination"` |
| `groupByColumns` | object | |
| `groupedColumnConfig` | object | `{{ expandByDefault: false, size: 88.75 }}` |
| `margin` | string | |
| `style` | object | |
| `changesetArray` | expr | Array of pending row changes |
| `cursorCache` | object | Cached cursor state |
| `selectedDataIndexes` | array | Indexes of selected rows (data-order) |
| `selectedRowKeys` | array | Primary keys of selected rows |
| `selectedRows` | array | Full row objects of selected rows |
| `selectedSourceRows` | array | Source (pre-sort) row objects of selected rows |
| `sortArray` | array | Current sort state |
| `newRows` | array | Rows added via addRow |
| `expandedRowDataIndexes` | array | Indexes of expanded rows |
| `deprecatedLabels` | object | Legacy label map |
| `dynamicColumnSource` | expr | Dynamic column generation source |

**Children:** `<Column>`, `<Action>`, `<ToolbarButton>`, `<Event>`, `<Include>` (for ExpandedRow)

**Apps:** All except Katalog (which uses TableLegacy)

### `<Column>`
Table column definition.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | hex (e.g., `"334b4"`) |
| `key` | string | Data field key |
| `label` | string | Display label |
| `format` | string | See format list below |
| `formatOptions` | object | Format-specific options |
| `alignment` | string | `"left"`, `"right"`, `"center"` |
| `position` | string | `"center"` |
| `size` | number | Pixel width |
| `editable` | bool/string | |
| `editableInNewRows` | string | `"true"` |
| `editableOptions` | object | `{{ showStepper: true }}`, `{{ spellCheck: false }}`, `{{ allowCustomValue: true }}` |
| `hidden` | string | `"true"`, `"false"` |
| `caption` | expr | Subtitle text |
| `cellTooltip` | expr | |
| `cellTooltipMode` | string | `"overflow"`, `"custom"` |
| `valueOverride` | expr | Override displayed value |
| `backgroundColor` | expr | |
| `textColor` | expr | |
| `tooltip` | string | Header tooltip |
| `placeholder` | string | |
| `referenceId` | string | |
| `groupAggregationMode` | string | `"none"`, `"sum"`, `"average"` |
| `summaryAggregationMode` | string | `"none"` |
| `optionList` | object | For tag/select columns |
| `statusIndicatorOptions` | object | |

**Column `format` values:** `string`, `multilineString`, `decimal`, `percent`, `boolean`, `datetime`, `date`, `tag`, `tags`, `json`, `html`, `markdown`, `progress`

### `<Action>`
Table row action button.
```jsx
<Action id="4a6c3" icon="bold/interface-delete-bin-5-alternate" label="Delete" disabled="{{ i == 0 }}">
  <Event event="clickAction" method="trigger" type="datasource" pluginId="deleteQuery" ... />
</Action>
```

### `<ToolbarButton>`
Table toolbar button.
```jsx
<ToolbarButton id="1a" icon="bold/interface-text-formatting-filter-2" label="Filter" type="filter" />
<ToolbarButton id="3c" icon="bold/interface-download-button-2" label="Download" type="custom">
  <Event event="clickToolbar" method="exportData" type="widget" pluginId="tableName" ... />
</ToolbarButton>
```
**Types:** `"filter"`, `"custom"`, `"addRow"`

### `<ExpandedRow>`
Template for table expandable rows. Included via `<Include>` inside `<Table>`.
```jsx
<ExpandedRow id="TemplatesTableExpandedRow">
  <Table data="{{ currentSourceRow.messages }}" ... />
</ExpandedRow>
```
**Apps:** Prompt Catalog, Iris Atlas v2

### `<TableLegacy>`
Legacy table component with column-config map attributes instead of child `<Column>` elements.

Key differences from `<Table>`:
- Column definitions via map attributes: `_columns`, `columnHeaderNames`, `columnFormats`, `columnEditable`, `columnAlignment`, etc.
- Row actions via `actionButtons` array attribute
- Events via `events` array attribute (not child elements)
- `serverPaginated`, `totalRowCount` for server-side pagination
- `rowColor` instead of `rowBackgroundColor`
- `defaultSelectedRow` is a string (`"none"`) not an object

**Column format values (TableLegacy):** `NumberDataCell`, `PercentDataCell`, `CheckboxDataCell`, `HtmlDataCell`, `SingleTagDataCell`, `DateDataCell`, `DateTimeDataCell`, `TextDataCell`, `JsonDataCell`, `button`, `default`

**TableLegacy attributes:**

| Attribute | Category | Type | Description |
|-----------|----------|------|-------------|
| `_columnSummaryTypes` | Column config | object | Summary type per column |
| `_columnSummaryValues` | Column config | object | Summary value per column |
| `_columnVisibility` | Column config | object | Visibility toggle per column |
| `_compatibilityMode` | Column config | bool | Legacy compatibility flag |
| `columnColors` | Column config | object | Color map per column |
| `columnFrozenAlignments` | Column config | object | Frozen column alignment per column |
| `columnMappers` | Column config | object | Value mapper per column |
| `columnMappersRenderAsHTML` | Column config | object | Render mapper output as HTML per column |
| `columnTypeProperties` | Column config | object | Type-specific properties per column |
| `columnTypeSpecificExtras` | Column config | object | Extra type-specific config per column |
| `columnWidths` | Column config | object | Pixel width per column |
| `actionButtonPosition` | Behavior | string | Position of action buttons |
| `actionButtonSelectsRow` | Behavior | bool | Whether clicking action selects the row |
| `allowMultiRowSelect` | Behavior | bool | Enable multi-row selection |
| `customButtonName` | Behavior | string | Label for custom action button |
| `defaultSortByColumn` | Behavior | string | Default sort column key |
| `disableSorting` | Behavior | bool | Disable column sorting |
| `doubleClickToEdit` | Behavior | bool | Require double-click to enter edit mode |
| `downloadRawData` | Behavior | bool | Download raw (untransformed) data |
| `freezeActionButtonColumns` | Behavior | bool | Freeze action button columns |
| `saveChangesDisabled` | Behavior | bool | Disable save-changes button |
| `showBoxShadow` | Behavior | bool | Show drop shadow |
| `showClearSelection` | Behavior | bool | Show clear-selection button |
| `showFilterButton` | Behavior | bool | Show filter button in toolbar |
| `sortByRawValue` | Behavior | bool | Sort by raw value instead of display value |

**Apps:** Katalog

### `<KeyValue>`
Key-value pair display.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `data` | expr | |
| `editIcon` | string | |
| `enableSaveActions` | bool | |
| `groupLayout` | string | `"singleColumn"` |
| `itemLabelPosition` | string | |
| `labelWrap` | bool | |
| `minColumnWidth` | string | `"300"` |

**Children:** `<Property>`

**Apps:** Chat Insights

### `<Property>`
Field within `<KeyValue>`.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | Data field key (doubles as key) |
| `editable` | string | `"false"` |
| `format` | string | `"datetime"`, `"boolean"`, `"string"`, `"markdown"`, `"html"`, `"decimal"`, `"tags"`, `"json"`, `"multilineString"` |
| `formatOptions` | object | |
| `hidden` | string | |
| `label` | string | |
| `valueOverride` | expr | |
| `editableOptions` | object | |

### `<JSONExplorer>`
Interactive JSON tree viewer.
```jsx
<JSONExplorer id="jsonExplorer1" value="{{ JSON.parse(data) }}" expandNodes="{{ ... }}" />
```
**Apps:** Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio

### `<Statistic>`
Metric display with trend indicators.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `value` | expr | |
| `label` | string | |
| `labelCaption` | string | |
| `icon` | string | |
| `currency` | string | `"USD"` |
| `decimalPlaces` | string | `"1"` |
| `suffix` | string | `"K"`, `"M"` |
| `showSeparators` | bool | |
| `positiveTrend` | expr | |
| `secondaryValue` | expr | |
| `secondaryFormattingStyle` | string | `"percent"` |
| `secondarySignDisplay` | string | `"trendArrows"` |
| `secondaryCurrency` | string | Currency code for secondary value |
| `secondaryDecimalPlaces` | string | Decimal places for secondary value |
| `secondaryEnableTrend` | bool | Show trend indicator on secondary value |
| `secondaryPositiveTrend` | expr | Positive trend condition for secondary value |
| `secondaryShowSeparators` | bool | Show thousand separators on secondary value |
| `href` | expr | Link URL for the statistic |

**Apps:** Katalog

### `<ProgressBar>`
Progress indicator.
```jsx
<ProgressBar id="pb1" label="Classified" labelPosition="top" value="{{ expr }}" />
```
**Apps:** Katalog

### `<ProgressCircle>`
Circular progress/loading indicator.
```jsx
<ProgressCircle id="pc1" horizontalAlign="center" indeterminate="{{ !isDone }}" value="{{ progress }}" />
```
**Apps:** Iris Atlas v2

### `<Tags>`
Tag/pill display.

| Attribute | Type |
|-----------|------|
| `id` | string |
| `value` | expr |
| `colors` | expr |
| `hashColors` | bool |
| `allowWrap` | bool |
| `style` | object |

**Apps:** Prompt Studio, Experience Studio

### `<TagsWidget2>`
Alternative tag display widget.
```jsx
<TagsWidget2 id="tw2" allowWrap={true} colorByIndex="#DEDEDE" data="{{ expr }}" hidden="{{ ... }}" />
```
**Apps:** Prompt Studio, Iris Atlas v2

---

## 7. Input Components

### `<TextInput>`
| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `formDataKey` | string | Form field binding |
| `label` | string | |
| `labelPosition` | string | `"top"` |
| `placeholder` | string | |
| `required` | bool | |
| `readOnly` | string | `"true"` |
| `showClear` | bool | |
| `value` | expr | |
| `iconBefore` | string | |
| `disabled` | expr | |
| `hidden` | expr | |

### `<TextArea>`
| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `autoResize` | bool | `true` |
| `formDataKey` | string | |
| `label` | string | |
| `labelPosition` | string | `"top"` |
| `minLines` | number/string | `2` |
| `maxLines` | string | `"7"`, `"8"` |
| `placeholder` | string | |
| `required` | bool | |
| `disabled` | expr | |
| `hidden` | expr | |
| `loading` | expr | |
| `readOnly` | string | |
| `value` | expr | |
| `inputTooltip` | string | |
| `maxLength` | expr | |
| `style` | object | `{{ fontSize: "10px", fontFamily: "Jetbrains Mono NL" }}` |

### `<Select>`
Dropdown select.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `itemMode` | string | `"static"` (uses `<Option>` children) or `"mapped"` (uses `data`/`labels`/`values`) |
| `data` | expr | Data source for mapped mode |
| `labels` | expr | `"{{ item.name }}"` |
| `values` | expr | `"{{ item.id }}"` |
| `value` | expr | Selected value |
| `label` | string | |
| `labelPosition` | string | `"top"` |
| `placeholder` | string | |
| `emptyMessage` | string | `"No options"` |
| `searchMode` | string | `"caseInsensitive"`, `"disabled"` |
| `showClear` | bool | |
| `showSelectionIndicator` | bool | |
| `allowCustomValue` | bool | |
| `allowDeselect` | bool | |
| `overlayMaxHeight` | number | `375` |
| `overlayMinWidth` | string | |
| `captionByIndex` | expr | |
| `iconByIndex` | expr | |
| `colorByIndex` | expr | |
| `fallbackTextByIndex` | expr | |
| `tooltipByIndex` | expr | |
| `tooltipText` | string | |
| `formDataKey` | string | |
| `required` | bool | |
| `hidden` | expr | |
| `disabled` | expr | |
| `maintainSpaceWhenHidden` | bool | |
| `disabledByIndex` | expr | Disable specific options by index |
| `hiddenByIndex` | expr | Hide specific options by index |
| `_colorByIndex` | expr | Internal color override per option |
| `_fallbackTextByIndex` | expr | Internal fallback text per option |
| `_imageByIndex` | expr | Internal image override per option |

**Children:** `<Option>`, `<Event>`

### `<Multiselect>`
Multi-value select. Same attributes as Select plus:
| Attribute | Type | Example |
|-----------|------|---------|
| `wrapTags` | bool | `true` |
| `automaticItemColors` | bool | |
| `disabledByIndex` | expr | Disable specific options by index |
| `hiddenByIndex` | expr | Hide specific options by index |
| `_colorByIndex` | expr | Internal color override per option |
| `_fallbackTextByIndex` | expr | Internal fallback text per option |
| `_imageByIndex` | expr | Internal image override per option |

### `<Option>`
Static option for Select, Multiselect, Tabs, SegmentedControl, Navigation, DropdownButton.
```jsx
<Option id="5675d" value="Option 1" label="Display Label" caption="Subtitle" icon="bold/..." disabled={false} hidden={false} />
```
Special attributes in Navigation context: `itemType` (`"custom"`, `"app"`), `key`, `parentKey` (for nested menus).

### `<Cascader>`
Hierarchical/cascading select.
```jsx
<Cascader
  id="cascader1"
  structure="{{ formatDataAsArray(data).map(v => [v.category, v.name]) }}"
  value="{{ [] }}"
  formDataKey="template"
  label="Template"
  placeholder="Select"
  required={true}
  events={[...]}
/>
```
**Apps:** Experience Studio

### `<Checkbox>`
```jsx
<Checkbox id="cb1" label="Enable" disabled="{{ expr }}" hidden="{{ expr }}" />
```

### `<RadioGroup>`
```jsx
<RadioGroup id="rg1" itemMode="static" groupLayout="singleColumn" label="Type" value="{{ self.values[0] }}">
  <Option id="opt1" value="a" label="Alpha" />
</RadioGroup>
```

### `<SegmentedControl>`
```jsx
<SegmentedControl id="sc1" itemMode="static" paddingType="spacious" value="{{ self.values[0] }}">
  <Option id="opt1" value="tab1" label="Tab 1" />
</SegmentedControl>
```

### `<Switch>`
```jsx
<Switch id="sw1" label="Enable" formDataKey="is_active" value="false" labelAlign="right" labelPosition="left" />
```

### `<NumberInput>`
| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `allowNull` | bool | |
| `currency` | string | `"USD"` (default, even non-monetary) |
| `decimalPlaces` | string | `"0"` |
| `inputValue` | number | |
| `label` | string | |
| `min`/`max` | string | |
| `placeholder` | string | |
| `showClear` | bool | |
| `showSeparators` | bool | |
| `showStepper` | bool | |
| `textAfter` | string | `"messages"`, `"words"` (unit suffix) |
| `tooltipText` | string | |
| `value` | expr | |
| `preventScroll` | bool | |
| `formDataKey` | string | |

**Apps:** Prompt Studio, Experience Studio

### `<Slider>`
```jsx
<Slider id="sl1" label="Count" labelPosition="top" min="1" max="30" step={1} value="6" />
```
**Apps:** Image Lab, Prompt Studio, Experience Studio

### `<Date>`
Single date picker.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `dateFormat` | string | `"d MMM yyyy"`, `"MMM d, yyyy"` |
| `datePlaceholder` | string/expr | `"{{ self.dateFormat.toUpperCase() }}"` |
| `formDataKey` | string | Form field binding |
| `iconBefore` | string | `"bold/interface-calendar"` |
| `label` | string | |
| `labelPosition` | string | `"top"` |
| `showClear` | bool | |
| `value` | expr | |
| `disabled` | expr | |
| `hidden` | expr | |
| `required` | bool | |

```jsx
<Date id="StartDate" dateFormat="d MMM yyyy" datePlaceholder="{{ self.dateFormat.toUpperCase() }}"
  formDataKey="start_date" iconBefore="bold/interface-calendar" label="Start date"
  labelPosition="top" showClear={true} />
```
**Apps:** iHeadcount

### `<DateRange>`
Date range picker with start and end values.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `dateFormat` | string | `"MMM d, yyyy"` |
| `startPlaceholder` | string | `"Start date"` |
| `endPlaceholder` | string | `"End date"` |
| `textBetween` | string | `"-"` |
| `iconBefore` | string | `"bold/interface-calendar-remove"` |
| `label` | string | |
| `labelPosition` | string | `"top"` |
| `showClear` | bool | |
| `value` | object | `{{ ordered: [{ start: "" }, { end: "" }] }}` |
| `disabled` | expr | |
| `hidden` | expr | |

**Value access:** `widget.value?.start`, `widget.value?.end`

**Children:** `<Event>` (e.g., on `"change"`)

```jsx
<DateRange id="StartDateFilter" dateFormat="MMM d, yyyy" startPlaceholder="Start date"
  endPlaceholder="End date" iconBefore="bold/interface-calendar-remove" label="Start Date"
  labelPosition="top" showClear={true} textBetween="-"
  value={{ ordered: [{ start: "" }, { end: "" }] }}>
  <Event id="19845c7d" event="change" method="trigger" pluginId="applyFilter"
    type="datasource" waitMs="0" waitType="debounce" />
</DateRange>
```
**Apps:** iHeadcount

### `<FileButton>`
File upload button.
```jsx
<FileButton id="fb1" _isUpgraded={true} text="Upload" iconBefore="bold/interface-upload-button-2"
  styleVariant="outline" maxCount={20} maxSize="250mb" disabled="{{ ... }}">
  <Event event="parse" method="trigger" type="datasource" pluginId="processUpload" ... />
</FileButton>
```
**Apps:** Prompt Studio, Experience Studio

### `<JSONEditor>`
JSON editor with inline events.
```jsx
<JSONEditor id="je1" value="{{ data }}" hidden="{{ expr }}"
  events={[{ ordered: [
    { event: "change" }, { type: "script" }, { method: "run" },
    { pluginId: "" }, { targetId: null },
    { params: { ordered: [{ src: "..." }] } },
    { waitType: "debounce" }, { waitMs: "200" }, { id: "..." }
  ]}]}
/>
```
**Apps:** Prompt Studio, Experience Studio

### `<Listbox>`
Selection list.
```jsx
<Listbox id="lb1" data="{{ query.data }}" labels="{{ item.name }}" values="{{ item.id }}"
  value="{{ ... }}" emptyMessage="No items" label="Select" labelPosition="top" />
```
**Apps:** Experience Studio

### `<Tabs>`
Tab navigation, can drive Container view switching.
```jsx
<Tabs id="tabs1" itemMode="static" navigateContainer={true} targetContainerId="container1"
  value="{{ self.values[0] }}" styleVariant="lineBottom">
  <Option id="opt1" value="Tab 1" />
</Tabs>
```

---

## 8. Action Components

### `<Button>`
| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `text` | string/expr | |
| `iconBefore` | string | `"bold/interface-edit-pencil"` |
| `submit` | bool | `true` (form submit) |
| `submitTargetId` | string | Form id |
| `styleVariant` | string | `"outline"`, `"solid"`, `"danger"` |
| `disabled` | expr | |
| `loading` | expr | |
| `loaderPosition` | string | `"replace"` |
| `horizontalAlign` | string | `"right"`, `"center"` |
| `heightType` | string | `"auto"`, `"fill"` |
| `ariaLabel` | string | `"Close"` |
| `allowWrap` | bool | |
| `margin` | string | |
| `tooltipText` | string | |
| `style` | object | |

**Children:** `<Event>` (one or more)

### `<ButtonGroup2>`
Button group container.
```jsx
<ButtonGroup2 id="bg1" alignment="right" overflowPosition={1}>
  <ButtonGroup2-Button id="btn1" text="Action" icon="bold/..." styleVariant="outline">
    <Event ... />
  </ButtonGroup2-Button>
</ButtonGroup2>
```
**Apps:** Prompt Studio, Experience Studio

### `<DropdownButton>`
Button with dropdown menu.
```jsx
<DropdownButton id="dd1" text="More" icon="bold/interface-arrows-button-down"
  itemMode="static" styleVariant="outline" overlayMaxHeight={375}>
  <Option id="opt1" label="Action 1" value="a1">
    <Event event="click" ... />
  </Option>
</DropdownButton>
```
Supports `targetId` on events to link handlers to specific Options.

**Apps:** Image Lab, Iris AI Images, Katalog, Experience Studio

### `<Link>`
```jsx
<Link id="link1" text="{{ expr }}" horizontalAlign="center" showUnderline="hover"/"never"
  iconBefore="bold/..." style={{ ordered: [{ hoverText: "..." }] }}>
  <Event event="click" ... />
</Link>
```
**Apps:** Prompt Studio, Iris Atlas v2

### `<ToggleButton>`
Toggle with icon switching.
```jsx
<ToggleButton id="tb1" text="{{ self.value ? 'Hide' : 'Show' }}"
  iconForFalse="bold/..." iconForTrue="bold/..." iconPosition="replace"
  styleVariant="outline" value="{{ expr }}">
  <Event event="change" ... />
</ToggleButton>
```
**Apps:** Iris Atlas v2

---

## 9. Presentation Components

### `<Text>`
Markdown-enabled text display.
```jsx
<Text id="title" value="### Page Title\n{{ dynamicContent }}"
  verticalAlign="center" horizontalAlign="center" disableMarkdown={false}
  heightType="fixed"/"fill" style={{ ordered: [{ color: "rgb(23,61,36)" }] }} />
```
Supports markdown (`#`, `##`, `**bold**`, etc.) and inline HTML (`<pre>`, `<div>`, `<span>`).

### `<Image>`
```jsx
<Image id="img1" src="{{ url }}" altText="{{ desc }}" fit="contain"
  aspectRatio="1" heightType="fixed" horizontalAlign="center"
  retoolFileObject="{{ fileButton.value }}" tooltipText="{{ ... }}"
  style={{ ordered: [{ borderColor: "#cccccc" }] }} />
```

### `<Avatar>`
```jsx
<Avatar id="av1" fallback="AB" label="{{ name }}" labelCaption="{{ email }}"
  imageSize={32} src="{{ profileUrl }}" style={{ ordered: [{ background: "primary" }] }} />
```
**Apps:** Katalog, Iris Atlas v2

### `<Divider>`
Labeled or plain horizontal divider.
```jsx
<Divider id="div1" text="Section" textSize="h6" horizontalAlign="left"
  style={{ ordered: [{ fontSize: "h6Font" }, { fontWeight: "700" }] }} />
```

### `<Spacer>`
Empty vertical space.
```jsx
<Spacer id="spacer1" marginType="normal" />
```

### `<Video>`
```jsx
<Video id="vid1" src="{{ url }}" hidden="{{ expr }}" playbackRate={1} volume={0.5} />
```
**Apps:** Prompt Studio

### `<Navigation>`
Page navigation bar.
```jsx
<Navigation id="nav1" itemMode="static" altText="Navigation">
  <Option id="opt1" key="home" label="Home" icon="bold/..." itemType="custom">
    <Event event="click" method="setCurrentView" type="widget" ... />
  </Option>
  <Option id="opt2" key="admin" label="Admin" icon="bold/..." parentKey="home" itemType="app" />
</Navigation>
```
`parentKey` creates nested/sub-menu items.

**Apps:** Katalog, Iris Atlas v2

### `<Chat>`
AI chat interface widget.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | `"AtlasChatBox"` |
| `queryTargetId` | string | JavascriptQuery id for message processing |
| `assistantName` | string | `"Atlas AI"` |
| `_sessionStorageId` | string | UUID for session persistence |
| `showAvatar` | bool | |
| `showEmptyState` | bool | |
| `showHeader` | bool | |
| `showTimestamp` | bool | |
| `placeholder` | string | |
| `emptyTitle`/`emptyDescription` | string | |
| `avatarSrc`/`avatarFallback`/`avatarImageSize` | expr/string/number | |
| `_actionIds`/`_actionLabel`/`_actionIcon`/`_actionType`/`_actionHidden`/`_actionDisabled` | object/array | Per-action config maps |
| `_headerButtonIds`/`_headerButtonLabel`/`_headerButtonIcon`/`_headerButtonType`/`_headerButtonHidden` | object/array | Header button config |
| `_defaultUsername` | expr | |

**Apps:** Iris Atlas v2

---

## 10. Query & Data System

### `<SqlQueryUnified>`
Primary database query component. Supports raw SQL and GUI modes.

**Common attributes (all modes):**
| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | Query name |
| `resourceDisplayName` | string | `"onsen-db (apps)"` |
| `resourceName` | string | Resource UUID |
| `errorTransformer` | string | `"return data.error"` |
| `transformer` | string | `"return data"`, `"return formatDataAsArray(data)"` |
| `enableTransformer` | bool | |
| `isMultiplayerEdited` | bool | |
| `runWhenModelUpdates` | bool | `false` for mutations |
| `showSuccessToaster` | bool | |
| `notificationDuration` | number | `4.5` |
| `queryTimeout` | string | Milliseconds |
| `warningCodes` | array | `{[]}` |
| `workflowActionType` | null | |
| `workflowBlockPluginId` | null | |
| `workflowBlockUuid` | null | |
| `workflowRunId` | null | |
| `_additionalScope` | array | Variable names for `additionalScope` |
| `queryDisabled` | expr | `"{{ condition }}"` |
| `requireConfirmation` | bool | |
| `confirmationMessage` | string | Markdown-formatted |
| `successMessage` | string | |
| `resourceTypeOverride` | string | `""` — override toggle for resource type (also on RESTQuery, OpenAPIQuery) |

**Raw SQL mode (SELECT):**
```jsx
<SqlQueryUnified id="selectUsers"
  query={include("./lib/selectUsers.sql", "string")}
  resourceDisplayName="db-name" resourceName="uuid" ... />
```

**GUI mode — available `actionType` values:**
| actionType | Description | Key Attributes |
|------------|-------------|----------------|
| *(omitted)* | Raw SQL SELECT | `query` (include or inline) |
| `"INSERT"` | Insert row | `tableName`, `changeset`/`changesetObject`, `editorMode="gui"` |
| `"UPDATE_BY"` | Update by filter | `tableName`, `changeset`/`changesetObject`, `filterBy`, `editorMode="gui"` |
| `"DELETE_BY"` | Delete by filter | `tableName`, `filterBy`, `editorMode="gui"` |
| `"BULK_UPDATE_BY_KEY"` | Bulk update | `tableName`, `bulkUpdatePrimaryKey`, `records`, `editorMode="gui"` |
| `"BULK_UPSERT_BY_KEY"` | Bulk upsert | `tableName`, `bulkUpdatePrimaryKey`, `records`, `editorMode="gui"` |
| `"UPDATE_OR_INSERT_BY"` | Upsert single | `tableName`, `changeset`, `filterBy`, `editorMode="gui"` |

**Changeset formats:**
```jsx
// Array format (JSON string)
changeset={'[{"key":"name","value":"{{ widget.value }}"}]'}

// Object format
changesetIsObject={true}
changesetObject="{{ { ...form.data } }}"
```

**FilterBy format:**
```jsx
filterBy={'[{"key":"id","value":"{{ table.selectedRow.id }}","operation":"="}]'}
```

**Children:** `<Event>` (typically on `"success"`)

### `<RESTQuery>`
HTTP API calls.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `query` | string | URL path: `"chat/completions"`, `"responses"`, `"images/generations"` |
| `type` | string | `"POST"` (HTTP method) |
| `body` | string | JSON body (raw or key-value) |
| `bodyType` | string | `"raw"` (string), `"json"` (key-value array) |
| `headers` | string | `'[{"key":"Content-Type","value":"application/json"}]'` |
| `queryTimeout` | string | `"60000"` to `"600000"` |
| `enableTransformer` | bool | |
| `transformer` | string | |
| `_additionalScope` | array | |
| `version` | number | `1` |
| `confirmationMessage` | string | |
| `queryFailureConditions` | string | JSON array |

### `<JavascriptQuery>`
Client-side JavaScript execution.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `query` | include/string | `{include("./lib/script.js", "string")}` |
| `resourceName` | string | Always `"JavascriptQuery"` |
| `runWhenPageLoads` | bool | |
| `runWhenPageLoadsDelay` | string | `"3000"` ms |
| `updateSetValueDynamically` | bool | |
| `queryFailureConditions` | string | JSON array |
| `successMessage` | string | |
| `_additionalScope` | array | |

### `<OpenAPIQuery>`
OpenAPI/Swagger-generated API calls.

| Attribute | Type | Example |
|-----------|------|---------|
| `id` | string | |
| `method` | string | `"post"` |
| `operationId` | string | `"createChatCompletion"` |
| `path` | string | `"/chat/completions"` |
| `parameters` | string | JSON with `{{ }}` |
| `requestBody` | string | JSON with `{{ }}` |
| `requestBodyDynamicStates` | string | JSON feature flags |
| `requestBodyMetadata` | string | |
| `parameterDynamicStates` | string | |
| `parameterMetadata` | string | |
| `resourceDisplayName` | string | |
| `resourceName` | string | UUID |
| `server` | string | `"default_server_url"` |
| `serverVariables` | string | JSON |
| `importedQueryInputs` | object | `{{ map: { variable0: "{{ expr }}" } }}` |
| `playgroundQueryUuid` | string | UUID linking to API playground query |
| `serverVariablesDynamicStates` | string | JSON dynamic states for server variables |

**Apps:** Prompt Studio, Experience Studio

### `<S3Query>`
AWS S3 operations.

| actionType | Description |
|------------|-------------|
| *(omitted)* | List objects |
| `"getSignedUrl"` | Get signed URL |
| `"upload"` | Upload file |
| `"copy"` | Copy object |

| Attribute | Type |
|-----------|------|
| `bucketName` | string (supports `{{ }}`) |
| `prefix` | string |
| `signedOperationName` | string |
| `signedOperationOptions` | string |
| `uploadData`/`uploadFileName`/`uploadFileType` | string |
| `useRawUploadFileType` | bool |
| `copySource`/`fileKey` | string |
| `queryDisabled` | expr |
| `queryFailureConditions` | string |

**Apps:** Experience Studio

### `<SqlTransformQuery>`
In-browser SQL over already-fetched data (no remote DB).
```jsx
<SqlTransformQuery id="getAllDashboards"
  query={include("../lib/getAllDashboards.sql", "string")}
  resourceName="SQL Transforms" />
```
**Apps:** Iris Atlas v2

### `<WorkflowRun>`
Trigger a Retool Workflow.
```jsx
<WorkflowRun id="triggerAiDashboard"
  resourceName="WorkflowRun"
  workflowId="uuid"
  workflowParams={include("../lib/params.json", "string")}
  workflowRunExecutionType="async">
  <Event event="success" ... />
</WorkflowRun>
```
**Apps:** Iris Atlas v2

### `<Function>`
Reactive computed value (auto-reruns when dependencies change).
```jsx
<Function id="selectedChat"
  funcBody={include("./lib/selectedChat.js", "string")}
  runBehavior="debounced" />
```
Distinct from `<JavascriptQuery>`: uses `funcBody` (not `query`), has `runBehavior`, no transformer/error handling. Always reactive — not triggered manually.

### `<State>`
Reactive state variable.
```jsx
<State id="images" value="{{ [] }}"
  _persistedValueGetter={null} _persistedValueSetter={null}
  persistedValueKey="" persistValue={false} />
```

### `<Module>`
Embedded reusable module (shared across apps).
```jsx
<Module id="onsenNavBar1" name="Onsen :: NavBar" pageUuid="uuid" margin="0" />
```

---

## 11. lib/ File Patterns

### SQL Patterns
```sql
-- Simple SELECT
SELECT * FROM schema.table ORDER BY column

-- Parameterized WHERE
WHERE user_id = {{ UserSelect.value }}
  AND status = {{ StatusSelect.value }}

-- Optional filter (show all when null)
WHERE (column = {{ widget.value }} OR {{ widget.value === null }})

-- Array membership
WHERE id = ANY({{ arrayVariable }})

-- ILIKE search
AND name ILIKE '%' || {{ searchInput.value }} || '%'

-- CTE
WITH aggregated AS (
  SELECT id, COUNT(1) AS cnt FROM table GROUP BY 1
)
SELECT * FROM main_table LEFT JOIN aggregated USING (id)

-- Stored procedure call
CALL schema.procedure(_param := {{ value }})

-- Server-side pagination
OFFSET {{ table.paginationOffset }} LIMIT {{ table.pageSize }}

-- Dynamic ORDER BY
ORDER BY CASE WHEN {{ expr }} THEN column END ASC

-- Vector similarity search (pgvector)
WHERE embedding <#> (({{ embedding }})::FLOAT[])::VECTOR < -0.5

-- Retool subquery as table reference
FROM {{ getDocs.data }} AS docs
```

### JavaScript Patterns
```javascript
// Query triggering with additionalScope
await query.trigger({ additionalScope: { paramName: value } })

// Sequential execution
await query1.trigger();
await query2.trigger();

// Parallel execution
await Promise.all([q1.trigger(), q2.trigger(), q3.trigger()])

// State management
state.setValue(newValue)
component.setCurrentView('viewKey')
table.selectRow({ mode: "index", indexType: "data", index: 0 })
table.clearSelection()
modal.close()

// Retool helpers in JS context
const data = {{ formatDataAsArray(queryName.data) }};
const user = {{ current_user.email }};

// Lodash (always available)
_.merge({}, original, changes)
_.keyBy(array, 'field')
_.cloneDeep(object)

// Table changeset merge
const changes = table.changesetObject;
const merged = _.merge(data, changes);
state.setValue(merged);

// Table filter API
table.setFilterStack({ filters: [{ columnId: "col", operator: "isNotEmpty" }] });
table.resetFilterStack();
```

### CSS Patterns
```css
/* Target specific component instance by ID with --0 suffix */
#ComponentId--0 {
  font-family: monospace;
  font-size: 0.65rem;
}

/* Hide Retool chrome elements */
div[data-testid="Navigation::FloatingPresentationNav"] { display: none; }
div._3bEXZ.ant-dropdown-trigger.retool-dropdown { display: none; }
```

### include() Integration
| File Type | Attribute | Example |
|-----------|-----------|---------|
| `.sql` | `query` | `query={include("./lib/select.sql", "string")}` |
| `.js` | `query` | `query={include("./lib/script.js", "string")}` |
| `.js` | `funcBody` | `funcBody={include("./lib/compute.js", "string")}` |
| `.css` | `css` | `css={include("./lib/$appStyles.css", "string")}` |
| `.json` | `workflowParams` | `workflowParams={include("../lib/params.json", "string")}` |
| `.query` | `query` | `query={include("./lib/script.query", "string")}` |

---

## 12. Event System

### `<Event>` Element
```jsx
<Event
  id="hex8chars"
  event="click"
  method="trigger"
  params={{ ordered: [] }}
  pluginId="targetId"
  type="datasource"
  waitMs="0"
  waitType="debounce"
  enabled="{{ condition }}"  // optional, conditional execution
  targetId="optionId"        // optional, for DropdownButton option targeting
/>
```

### Event Types (`event` attribute)

| Event | Context | Description |
|-------|---------|-------------|
| `click` | Button, Link, Option, Container | Standard click |
| `change` | Select, Multiselect, Switch, TextInput, ToggleButton, JSONEditor | Value changed |
| `submit` | Form | Form submitted |
| `success` | Any query | Query completed successfully |
| `failure` | JavascriptQuery | Query failed |
| `save` | Table | Table save button clicked |
| `selectRow` | Table | Row selection changed |
| `clickAction` | Table Action, Chat action | Row action clicked |
| `clickToolbar` | ToolbarButton | Toolbar button clicked |
| `clickHeader` | Chat header button | Chat header button clicked |
| `clickCell` | Table Column | Cell clicked |
| `changeCell` | Table Column | Cell value changed |
| `pageChange` | TableLegacy | Page changed (server pagination) |
| `saveChanges` | TableLegacy | Save button clicked |
| `rowSelectChange` | TableLegacy | Row selection changed |
| `parse` | FileButton | File parsed after upload |
| `show` | Container/DrawerFrame | Component shown |
| `fullscreen` | DynamicWidget | Custom component fullscreen toggle |
| `copy` | DynamicWidget | Custom component copy action |

### Methods (`method` attribute)

| Method | Type | Description | Params |
|--------|------|-------------|--------|
| `trigger` | `datasource` | Fire a query | `{{ ordered: [] }}` or with `additionalScope` |
| `reset` | `datasource` | Reset query state | `{}` |
| `run` | `script` | Execute inline JS | `{ ordered: [{ src: "code" }] }` or `{ map: { src: "code" } }` |
| `setValue` | `widget`/`state` | Set value | `{ map: { value: "..." } }` or `{ ordered: [{ value: "..." }] }` |
| `show` | `widget` | Show component | `{}` |
| `hide` | `widget` | Hide component | `{}` |
| `setHidden` | `widget` | Set hidden state | `{ ordered: [{ hidden: true }] }` or `{ map: { hidden: true } }` |
| `setCurrentView` | `widget` | Switch container view | `{ ordered: [{ viewKey: "..." }] }` or `{ map: { viewKey: "..." } }` |
| `setShowBody` | `widget` | Toggle body visibility | `{ map: { showBody: "{{ self.value }}" } }` |
| `close` | `widget` | Close modal | `{}` |
| `open` | `widget` | Open modal | `{}` |
| `clear` | `widget` | Clear form | `{}` |
| `refresh` | `widget` | Refresh table | `{}` |
| `selectRow` | `widget` | Select table row | `{ map: { options: { mode, indexType, index, key } } }` |
| `clearSelection` | `widget` | Clear table selection | `{}` |
| `exportData` | `widget` | Export table data | `{}` |
| `clearHistory` | `widget` | Clear chat history | `{}` |
| `clearValue` | `widget` | Clear widget value | `{}` |
| `openApp` | `util` | Navigate to app | `{ ordered: [{ uuid }, { options: { ordered: [{ hashParams }, { newTab }] } }] }` |
| `openPage` | `util` | Navigate to page | |
| `openUrl` | `util` | Open URL | `{ map: { url: "..." } }` |
| `copyToClipboard` | `util` | Copy text | `{ map: { value: "..." } }` or `{ ordered: [{ value: "..." }] }` |
| `showNotification` | `util` | Show toast | |

### Target Types (`type` attribute)

| Type | pluginId | Description |
|------|----------|-------------|
| `datasource` | Query id | Targets a query |
| `widget` | Component id | Targets a UI component |
| `state` | State id | Targets a State variable |
| `script` | `""` (empty) | Runs inline JavaScript |
| `util` | `""` (empty) | Built-in utility function |

### Inline Events (alternative syntax)
Used on `JSONEditor`, `Cascader`, `TableLegacy`, and `DynamicWidget_*`:
```jsx
events={[{
  ordered: [
    { event: "change" }, { type: "datasource" }, { method: "trigger" },
    { pluginId: "queryId" }, { targetId: null },
    { params: { ordered: [] } },
    { waitType: "debounce" }, { waitMs: "500" }, { id: "hexId" }
  ]
}]}
```

### Debounce Timing (`waitMs`)
| Value | Use Case |
|-------|----------|
| `"0"` | Immediate (most common) |
| `"200"` | Text input debounce |
| `"500"` | JSONEditor change |
| `"1000"` | Heavy computation |

---

## 13. Positioning System

### `.positions.json` Schema
Maps component `id` to position object:

```json
{
  "componentId": {
    "type": "stack",
    "container": "parentContainerId",
    "subcontainer": "viewHexId",
    "rowGroup": "header",
    "row": 0.6,
    "col": 4,
    "height": 1,
    "width": 12,
    "stackPosition": {
      "object": {
        "ordinal": 0,
        "widthType": "fixed",
        "width": 485.67,
        "height": 40
      }
    }
  }
}
```

### Position Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `type` | string | `"stack"` or omitted (grid) |
| `container` | string | Parent component id |
| `subcontainer` | string | View id (hex) or named section (`"header"`) |
| `rowGroup` | string | `"header"` or `"footer"` — places in container section |
| `row` | float | Vertical position (0.2 increments) |
| `col` | int | Column offset (0–11 in 12-column grid) |
| `height` | float | Row height (fractional grid units) |
| `width` | int | Column span (1–12) |
| `stackPosition.object.ordinal` | float | Sort order (can be negative: `-13.5`) |
| `stackPosition.object.widthType` | string | `"fixed"`, `"fill"`, `"auto"` |
| `stackPosition.object.width` | float | Pixel width (`0` = auto) |
| `stackPosition.object.height` | float | Pixel height (`0` = auto) |

### Multi-Page Positions
Newer apps use per-page position files in `.positions/` directory:
```
.positions/.global_positions.json
.positions/.pageName.positions.json
.positions/.global_mobile_positions.json
.positions/.pageName.mobilePositions.json
```

---

## 14. Template Expression Syntax

### Expression Contexts
| Context | Available Variables |
|---------|-------------------|
| Component attribute | `{{ }}` with any variable |
| Table Column | `currentSourceRow`, `item`, `i` |
| TableLegacy Column | `currentRow`, `currentColumn`, `self` |
| ListViewBeta child | `item`, `i`, `ri` (nested) |
| Select/Multiselect label | `item` |
| Form initialData | Query data, selected rows |
| SQL query (in `{{ }}`) | Widget values, query data, `localStorage`, `current_user` |
| JS query (in `{{ }}`) | Same as SQL + `retoolContext`, `formatDataAsArray`, lodash |

### Common Patterns
```jsx
// Conditional rendering
"{{ condition ? 'yes' : 'no' }}"

// Object-as-switch dispatch
"{{ { key1: value1, key2: value2 }[selector] }}"

// Lodash operations
"{{ _.find(data, { id: selectedId }) }}"
"{{ _.startCase(item) }}"
"{{ _.omit(obj, ['field1', 'field2']) }}"

// Template literal
"{{ `${firstName} ${lastName}` }}"

// numbro formatting
"{{ numbro(value).format({ thousandSeparated: true }) }}"
"{{ numbro(value).formatCurrency({ mantissa: 4 }) }}"

// JSON operations
"{{ JSON.stringify(obj, null, 2) }}"
"{{ JSON.parse(stringValue) }}"

// Array operations
"{{ items.filter(x => x.active).map(x => x.name) }}"
```

---

## 15. Module System

### `<Module>`
Embeds a reusable module by `pageUuid` reference:
```jsx
<Module id="onsenNavBar1" name="Onsen :: NavBar" pageUuid="219fc286-..." margin="0" />
```

### `<DynamicWidget_*>` (Custom Component Collections)
External custom component libraries registered in `metadata.json`:
```jsx
<DynamicWidget_MermaidViewer_MermaidViewer
  id="mermaid1"
  collectionUuid="460e5b84-..."
  mermaidCode="{{ expr }}"
  Arrows="Curved"
  defaultZoomLevel="0.9"
  heightType="fill"
  events={[...]}
/>
```
Tag naming: `DynamicWidget_{CollectionName}_{WidgetName}`

Metadata registration:
```json
{
  "customComponentCollections": [{
    "name": "CodeViewer",
    "collectionUuid": "ff3c49fe-...",
    "revisionUuid": "..."
  }]
}
```

**Apps:** Iris Atlas v2

---

## 16. Multi-Page Apps

### `<Screen>` Element
Each page is a `<Screen>` in a separate `.rsx` file, included from `main.rsx`.

```jsx
<Screen
  id="chat"
  title="Data Warehouse"
  browserTitle="Atlas Chat"
  urlSlug="chat"
  uuid="screen-uuid"
  _order={2}
  _customShortcuts={[]}
  _hashParams={[]}
  _searchParams={[]}
>
  <Folder id="queries">...</Folder>
  <Frame id="$main3" type="main" ...>...</Frame>
</Screen>
```

### Metadata for Multi-Page
```json
{
  "appTemplate": {
    "rootScreen": "dwh",
    "pageCodeFolders": {
      "dwh": { "object": { "queryGroup": { "array": ["query1", "query2"] } } },
      "mb": { "object": { ... } }
    }
  }
}
```

### Navigation Between Pages
```jsx
<Navigation id="pageNav" data="{{ retoolContext.pages }}" labels="{{ item.name }}"
  highlightByIndex="{{ retoolContext.currentPage?.handle === item.handle }}">
  <Event event="click" method="openPage" type="util" ... />
</Navigation>
```

**Apps:** Iris Atlas v2

---

## 17. Version Differences

### Table vs TableLegacy
| Feature | Table (modern) | TableLegacy |
|---------|---------------|-------------|
| Column definition | Child `<Column>` elements | Map attributes (`_columns`, `columnFormats`, etc.) |
| Events | Child `<Event>` elements | `events` array attribute |
| Selected row | Object: `{ mode, indexType, index }` | String: `"none"` |
| Row styling | `rowBackgroundColor` | `rowColor` |
| Server pagination | Not observed | `serverPaginated`, `totalRowCount` |
| Format names | `"string"`, `"decimal"`, `"tag"` | `"TextDataCell"`, `"NumberDataCell"`, `"SingleTagDataCell"` |

### `.positions.json` vs `.positions/` Directory
| Feature | Single file (older) | Directory (newer) |
|---------|-------------------|-------------------|
| Format | `.positions.json` at root | `.positions/` directory with per-page files |
| Mobile | Combined | Separate `.mobilePositions.json` files |
| Global | Combined | Separate `.global_positions.json` |
| Apps | All 9 reference apps | Iris Atlas v2 (multi-page) |

### Platform Version Differences
| Feature | Older (3.179–3.244) | Newer (3.286–3.338) |
|---------|--------------------|--------------------|
| `workflowBlockUuid` | Present | Replaced by `workflowBlockPluginId` |
| `paddingType` on Frame | Absent | `"normal"` |
| `version` on RESTQuery | Absent | `{1}` |
| `Folder` in GlobalFunctions | Optional | Common |
| `_disclosedFields` | Absent | Common |

---

## 17b. metadata.json Full Schema Reference

```json
{
  "toolscriptVersion": "1.0.0",
  "version": "43.0.9",
  "pageUuid": "uuid",
  "appTemplate": {
    "appMaxWidth": "100%" | "1280px" | "1560px",
    "appThemeId": -1 | 133,
    "appThemeName": "Efficy",
    "version": "3.327.0",
    "rootScreen": "dwh",
    "shortlink": false,
    "responsiveLayoutDisabled": true,
    "preloadedAppJavaScript": "window.fn = ...",
    "preloadedAppJSLinks": { "array": ["https://cdn.jsdelivr.net/..."] },
    "experimentalFeatures": {
      "object": { "sourceControlTemplateDehydration": false }
    },
    "notificationsSettings": {
      "object": {
        "globalQueryShowFailureToast": true,
        "globalQueryShowSuccessToast": true,
        "globalQueryToastDuration": 4.5
      }
    },
    "pageCodeFolders": { ... },
    "customComponentCollections": [{ "name": "...", "collectionUuid": "...", "revisionUuid": "..." }]
  }
}
```

---

## 18. App Generation Guide

This section provides the rules needed to **generate** a complete, importable Retool app from scratch.

### 18.1 ID Generation Rules

Every ID in a Retool app follows one of these patterns. When generating an app, use these rules to produce valid, non-colliding IDs.

| ID Type | Pattern | Regex | Example | Assignment |
|---------|---------|-------|---------|------------|
| **Frame** | `$` + name | `^\$[a-zA-Z_]\w*$` | `$main`, `$header` | Fixed: always `$main`, `$header` |
| **Component (semantic)** | PascalCase or camelCase | `^[a-zA-Z_]\w*$` | `CreateUserForm`, `dataTable` | Human-chosen, descriptive of purpose |
| **Component (numbered)** | typeName + number | `^[a-z_]\w*\d+$` | `textInput1`, `button2` | Auto-incremented per component type |
| **Column** | 5-char hex | `^[0-9a-f]{5}$` | `334b4`, `a7300` | Random. Generate with: `Math.random().toString(16).slice(2,7)` |
| **Event** | 8-char hex | `^[0-9a-f]{8}$` | `037f213c`, `fe9d6d21` | Random. Generate with: `Math.random().toString(16).slice(2,10)` |
| **View** | 5-char hex | `^[0-9a-f]{5}$` | `ae9ca`, `00f4b` | Random (same pattern as Column) |
| **Option** | 5-char hex | `^[0-9a-f]{5}$` | `5675d`, `ed132` | Random (same pattern as Column) |
| **Action** | 5-char hex | `^[0-9a-f]{5}$` | `4a6c3` | Random (same pattern as Column) |
| **ToolbarButton** | Short hex | `^[0-9a-f]{2,4}$` | `1a`, `3c` | Short random hex |
| **Query/Function** | snake_case or camelCase | `^[a-z_]\w*$` | `select_users`, `deleteMessage` | Human-chosen: snake_case for SQL, camelCase for JS |
| **pageUuid** | UUID v4 | Standard UUID | `9f851920-3b94-...` | Generated by Retool; use placeholder `00000000-0000-0000-0000-000000000001` |

**ID uniqueness rule:** All component IDs must be unique across the entire app (all RSX files combined). Column, Event, Option, View, and Action IDs must be unique within their parent component.

**Naming convention for components:**
- Major structural components: PascalCase (`CreateUserForm`, `SuperpowersDrawer`, `EditProductForm`)
- Generic/repeated components: camelCase + number (`textInput1`, `button2`, `divider1`)
- Page titles and key UI elements: descriptive camelCase (`pageTitle`, `dataTable`, `searchInput`)

### 18.2 Nesting Rules

**Parent-child constraint matrix.** Only the listed children are valid direct children of each parent.

| Parent | Valid Direct Children |
|--------|---------------------|
| `<App>` | `<Include>`, `<Frame>`, `<SplitPaneFrame>`, `<DrawerFrame>`, `<ModalFrame>`, `<AppStyles>`, `<DocumentTitle>`, `<UrlFragments>` |
| `<Frame>` | Any visible component, `<Include>`, `<Modal>` |
| `<Container>` | `<Header>`, `<View>` |
| `<View>` | Any visible component |
| `<Form>` | `<Header>`, `<Body>`, `<Footer>`, `<Event>` |
| `<Header>` | Any visible component (in Form: typically `<Text>` title; in Container: typically `<Tabs>`) |
| `<Body>` | Any visible component |
| `<Footer>` | Any visible component (typically `<Button>` elements) |
| `<Modal>` | `<Form>`, or any visible component |
| `<ModalFrame>` | `<Header>`, `<Body>` (**must be child of `<App>`, not `<Frame>`**) |
| `<DrawerFrame>` | `<Header>`, `<Body>` (**must be child of `<App>`, not `<Frame>`**) |
| `<SplitPaneFrame>` | `<Form>`, or any visible component (**must be child of `<App>`, not `<Frame>`**) |
| `<Table>` | `<Column>`, `<Action>`, `<ToolbarButton>`, `<Event>`, `<Include>` (for ExpandedRow) |
| `<ExpandedRow>` | Any visible component |
| `<ListViewBeta>` | Any visible component (rendered per item) |
| `<KeyValue>` | `<Property>` |
| `<Select>` / `<Multiselect>` | `<Option>`, `<Event>` |
| `<Tabs>` | `<Option>` |
| `<Button>` | `<Event>` |
| `<Action>` | `<Event>` |
| `<ToolbarButton>` | `<Event>` |
| `<DropdownButton>` | `<Option>` (which can contain `<Event>`) |
| `<ButtonGroup2>` | `<ButtonGroup2-Button>` (which can contain `<Event>`) |
| `<GlobalFunctions>` | `<Folder>`, `<SqlQueryUnified>`, `<RESTQuery>`, `<JavascriptQuery>`, `<OpenAPIQuery>`, `<S3Query>`, `<SqlTransformQuery>`, `<WorkflowRun>`, `<Function>`, `<State>` |
| `<Folder>` | Same as `<GlobalFunctions>` children |
| `<Screen>` | `<Folder>`, `<Frame>`, query/state elements |

**Leaf nodes** (never have children): `<Column>`, `<Option>`, `<Property>`, `<Event>`, `<Include>`, `<Module>`, `<Divider>`, `<Spacer>`, `<Text>`, `<TextInput>`, `<TextArea>`, `<Image>`, `<Avatar>`, `<Date>`, `<Slider>`, `<Switch>`, `<Checkbox>`, `<NumberInput>`, `<Statistic>`, `<ProgressBar>`, `<ProgressCircle>`, `<JSONExplorer>`, `<Video>`, `<State>`, `<Chat>`.

**Note:** `<Button>`, `<Select>`, `<Multiselect>`, `<DateRange>`, `<FileButton>` are leaf-like but can contain `<Event>` children.

**Required structural patterns:**
1. `<Form>` **must** have `<Header>` + `<Body>` + `<Footer>` (all three, set `showHeader`/`showFooter` to hide visually)
2. `<Container>` **must** have at least one `<View>` child
3. `<Table>` **must** have at least one `<Column>` child
4. `<ModalFrame>` / `<DrawerFrame>` should have `<Header>` and/or `<Body>`

### 18.3 Positioning Recipes

Every visible component **must** have an entry in `.positions.json`. Components without position entries will not render.

#### Grid System
- **12-column grid**: `width` ranges from 1 to 12; `col` ranges from 0 to 11
- **Row units**: fractional, in ~0.2 increments. `row: 0` is the top.
- **Constraint**: `col + width <= 12` (components must fit within the grid)

#### Standard Component Sizes

| Component Type | Typical Height | Typical Width | Notes |
|----------------|---------------|---------------|-------|
| Title/Text | 0.6 | 12 | Use for page headings |
| TextInput | 1.0 | 6–12 | Label + field |
| TextArea | 1.0–2.0 | 12 | Larger for multi-line |
| Select/Multiselect | 1.0 | 3–6 | In filter bars: 2–3 |
| Button | 1.0 | 2–4 | In forms/footers |
| Table | 13.2 | 12 | Standard data table |
| Chat | 17.4 | 12 | Full-height chat |
| Divider | 0.2 | 12 | Visual separator |
| Image | 3.0–13.2 | 4–12 | Varies by use |

#### Vertical Layout Recipe
Place components top-to-bottom by incrementing `row` by the previous component's `height`:
```
Component 1: row=0,    height=0.6  (title)
Component 2: row=0.6,  height=1.0  (input)
Component 3: row=1.6,  height=1.0  (input)
Component 4: row=2.6,  height=13.2 (table)
```

#### Horizontal Layout Recipe (Side-by-Side)
Split the 12-column grid:
```json
"leftInput":  { "row": 0.6, "col": 0, "height": 1, "width": 6 },
"rightInput": { "row": 0.6, "col": 6, "height": 1, "width": 6 }
```

#### Filter Bar Recipe (4-column layout)
```json
"searchInput":    { "row": 0.6, "col": 0, "height": 1, "width": 5 },
"categoryFilter": { "row": 0.6, "col": 5, "height": 1, "width": 3 },
"statusFilter":   { "row": 0.6, "col": 8, "height": 1, "width": 2 },
"resetBtn":       { "row": 0.6, "col": 10, "height": 1, "width": 2 }
```

#### Container/Form Internal Positioning
Components inside containers use `container` or `subcontainer` to scope their coordinates:
```json
"fieldName": {
  "container": "MyForm",
  "row": 0,
  "height": 1,
  "width": 12
}
```

#### Header/Footer Positioning (rowGroup)
Components in form/container headers and footers use `rowGroup` instead of `row`:
```json
"formTitle": {
  "container": "MyForm",
  "rowGroup": "header",
  "height": 0.6,
  "width": 12
},
"saveButton": {
  "container": "MyForm",
  "rowGroup": "footer",
  "col": 6,
  "height": 1,
  "width": 6
}
```

#### SplitPaneFrame / DrawerFrame Children
Use `subcontainer` with the frame's `id`:
```json
"editForm": {
  "subcontainer": "splitPaneFrame1",
  "height": 0.2,
  "width": 12
}
```

#### Container View Children
`<View>` elements are **transparent** in `.positions.json` — they do NOT get their own position entries. Instead, components inside a View reference both the parent Container (via `container`) and the View (via `subcontainer`):
```json
"DetailForm": {
  "container": "detailContainer",
  "subcontainer": "detailsView",
  "height": 0.2,
  "width": 12
},
"activityText": {
  "container": "detailContainer",
  "subcontainer": "activityView",
  "height": 2,
  "width": 12
}
```
**Important:** Never create a position entry for a `<View>` itself — this will cause a "Could not match plugin subtype View" import error.

#### ModalFrame Children
Components in the Header use `rowGroup: "header"` + `subcontainer`; components in the Body use `subcontainer`:
```json
"modalTitle": {
  "rowGroup": "header",
  "subcontainer": "editModal",
  "height": 0.6,
  "width": 12
},
"modalForm": {
  "subcontainer": "editModal",
  "height": 0.2,
  "width": 12
}
```

#### Stack Positioning (Optional)
Stack positioning adds pixel-level control. It is **optional** — many apps work without it. When present:
```json
"component": {
  "type": "stack",
  "row": 0,
  "height": 1,
  "width": 12,
  "stackPosition": {
    "object": {
      "ordinal": 0,
      "widthType": "fixed",
      "width": 485.67,
      "height": 40
    }
  }
}
```
- `ordinal`: Sort order (lower = earlier; can be negative: `-4.5`)
- `widthType`: `"fixed"` (pixel width), `"fill"` (expand to fill), `"auto"` (content-sized)

**Tip for generation:** Omit `stackPosition` and `type: "stack"` unless you need pixel-precise layouts. The grid-based row/col/width/height system is sufficient for most apps and is simpler to generate correctly.

### 18.4 metadata.json Template

Every app needs a `metadata.json`. Use this template and replace the placeholder UUID:

```json
{
  "toolscriptVersion": "1.0.0",
  "version": "43.0.9",
  "pageUuid": "REPLACE_WITH_UUID",
  "appTemplate": {
    "appMaxWidth": "100%",
    "appThemeId": -1,
    "experimentalFeatures": {
      "object": {
        "sourceControlTemplateDehydration": false
      }
    },
    "notificationsSettings": {
      "object": {
        "globalQueryShowFailureToast": true,
        "globalQueryShowSuccessToast": true,
        "globalQueryToastDuration": 4.5
      }
    },
    "version": "3.338.0"
  }
}
```

**Notes:**
- `pageUuid`: Use any valid UUID v4. Retool reassigns a new UUID on import, so the placeholder is fine.
- `toolscriptVersion` and `version`: Always `"1.0.0"` and `"43.0.9"` respectively.
- `appTemplate.version`: Use `"3.338.0"` (or the latest observed platform version).
- `appThemeId`: `-1` for default theme. Use a positive integer for custom themes (must exist in the target Retool instance).

**Optional fields** (add as needed):
- `appThemeName`: `"ThemeName"` — custom theme name
- `rootScreen`: `"pageName"` — for multi-page apps
- `pageCodeFolders`: `{ ... }` — registry of all queries, state, and component IDs (used in both single-page and multi-page apps)
- `shortlink`: `false` — enable/disable short URL
- `responsiveLayoutDisabled`: `true` — disable responsive layout
- `preloadedAppJavaScript`: `"window.fn = ..."` — global JS
- `preloadedAppJSLinks`: `{ "array": ["https://..."] }` — external JS libraries
- `customComponentCollections`: `[{ "name": "...", "collectionUuid": "...", "revisionUuid": "..." }]` — custom components

### 18.5 Resource References

Queries reference database/API resources via two attributes:
- `resourceDisplayName` — human-readable name shown in Retool UI (e.g., `"my-postgres"`)
- `resourceName` — UUID of the resource in the Retool instance (e.g., `"312ca604-eb15-40e9-bb14-0064eadb954d"`)

**When generating apps:**
1. Use a descriptive `resourceDisplayName` (e.g., `"your-database"`, `"openai-api"`)
2. Set `resourceName` to `"REPLACE_WITH_RESOURCE_UUID"`
3. After importing the app into Retool, the user must update each query to point to an actual resource

**Special resource names (no UUID needed):**
- `"JavascriptQuery"` — for `<JavascriptQuery>` (client-side JS, no remote resource)
- `"SQL Transforms"` — for `<SqlTransformQuery>` (in-browser SQL)
- `"WorkflowRun"` — for `<WorkflowRun>` (Retool Workflows)

### 18.6 Import/Export

Retool imports and exports apps as **zip archives** of the directory structure.

**To create an importable app:**
1. Create the directory structure (see Section 2):
   ```
   My App/
   ├── .positions.json
   ├── metadata.json
   ├── main.rsx
   ├── functions.rsx
   ├── src/           (optional, for extracted components)
   │   └── component.rsx
   └── lib/           (optional, for extracted code)
       ├── query.sql
       └── script.js
   ```
2. Zip the directory:
   ```bash
   zip -r "My App.zip" "My App/"
   ```
3. In Retool: **Create new** > **From file/ZIP** > upload the zip

**Minimum required files:** `main.rsx`, `functions.rsx`, `metadata.json`, `.positions.json`

**Minimum valid `main.rsx`:**
```jsx
<App>
  <Include src="./functions.rsx" />
  <Frame id="$main" type="main" padding="8px 12px" paddingType="normal" sticky={false}
    isHiddenOnDesktop={false} isHiddenOnMobile={false}>
    <!-- components here -->
  </Frame>
</App>
```

**Minimum valid `functions.rsx`:**
```jsx
<GlobalFunctions>
</GlobalFunctions>
```

### 18.7 State Management Patterns

Use `<State>` to hold UI mode flags, collected data for modals, static option lists, and cached computed values. Declare State variables inside `<GlobalFunctions>`.

**When to use `<State>`:**
- **UI mode flags:** `<State id="isBulkUpdate" value="{{ false }}" />` — toggles form between single-edit and bulk-update modes
- **Collected data for modals:** `<State id="bulkUpdateData" value="{{ [] }}" />` — stores the rows to be bulk-updated, displayed in a confirmation modal
- **Static option lists:** `<State id="colleagueTypes" value="{{ ['Full-Time', 'Part-Time', 'Contractor'] }}" />` — avoids hardcoding in multiple places
- **Cached computed values:** `<State id="activeCount" value="{{ 0 }}" />` — updated by a JavascriptQuery after data loads

**Setting State values:**
- From an `<Event>`: `method="setValue"` with `params={{ ordered: [["value", "newValue"]] }}`
- From JavaScript: `state.setValue("stateId", newValue)` inside a `<JavascriptQuery>`

**Example — toggle bulk mode:**
```jsx
<State id="isBulkUpdate" value="{{ false }}" />

<!-- Button toggles it on -->
<Button id="bulkUpdateBtn" text="Bulk Update">
  <Event id="ab12cd34" event="click" method="setValue"
    params={{ ordered: [["value", true]] }}
    pluginId="isBulkUpdate" type="state" waitMs="0" waitType="debounce" />
</Button>
```

### 18.8 Client-Side Filtering with setFilterStack()

When data is already loaded in a Table, use `setFilterStack()` for instant, client-side filtering instead of re-querying the database.

**When to use:**
- Dataset is small enough to load fully (hundreds to low thousands of rows)
- Many filter combinations — avoids complex SQL WHERE clauses
- Instant UX — no loading spinners

**Contrast with SQL-level filtering:** The Search Filter App pattern (Section 19.4) shows SQL-level `WHERE` clause filtering, which is better for large datasets that shouldn't be loaded entirely. Both approaches are valid — choose based on dataset size.

**Pattern:** A `<JavascriptQuery>` collects all filter widget values, builds a filter stack object, and calls `table.setFilterStack(stack)`.

**Filter object structure:**
```js
{
  filters: [
    { columnId: "c02b2", operator: "includes", value: searchInput.value },
    { columnId: "c04d4", operator: "=", value: statusFilter.value },
    { columnId: "c06f6", operator: ">=", value: dateRange.value.start }
  ],
  operator: "and"  // or "or"
}
```

**Available operators:** `=`, `!=`, `>=`, `<=`, `>`, `<`, `isOneOf`, `includes`, `doesNotInclude`, `isEmpty`, `isNotEmpty`, `isTrue`, `isFalse`

**Wiring:** Each filter widget triggers the `applyFilters` query on change:
```jsx
<TextInput id="searchInput" ...>
  <Event id="ab12cd34" event="change" method="trigger"
    params={{ ordered: [] }} pluginId="applyFilters"
    type="datasource" waitMs="300" waitType="debounce" />
</TextInput>
```

**Reset pattern:** Call `table.resetFilterStack()` to clear all client-side filters.

### 18.9 SqlTransformQuery as Derived Lookups

Use `<SqlTransformQuery>` to derive dropdown options, counts, or summaries from an already-loaded main query — no extra database round-trips.

**Pattern:** One main query loads all data. `SqlTransformQuery` components run in-browser SQL against that data to produce derived views.

**Example — department options derived from team data:**
```jsx
<SqlTransformQuery
  id="selectDepartments"
  query="SELECT DISTINCT department AS label, department AS value FROM {{ selectMembers.data }} ORDER BY department"
  resourceName="SQL Transforms"
  transformer="return data"
/>
```

**Key attributes:**
- `resourceName="SQL Transforms"` — built-in resource, no configuration needed
- References main query data via `{{ mainQuery.data }}` in the SQL

**Benefits:**
- Single source of truth: dropdown options always match loaded data
- No extra DB queries: reduces load and latency
- Always in sync: when main query refreshes, derived queries auto-update

**Common derived lookups:**
- Distinct values for filter dropdowns: `SELECT DISTINCT column FROM {{ query.data }}`
- Grouped counts for summaries: `SELECT department, COUNT(*) as count FROM {{ query.data }} GROUP BY department`
- Filtered subsets: `SELECT * FROM {{ query.data }} WHERE status = 'active'`

### 18.10 Bulk Operations Pattern

Use `BULK_UPDATE_BY_KEY` and `BULK_UPSERT_BY_KEY` action types to update multiple rows in a single query.

**`BULK_UPDATE_BY_KEY`:** Updates multiple rows by primary key.
```jsx
<SqlQueryUnified
  id="bulkUpdateMembers"
  actionType="BULK_UPDATE_BY_KEY"
  bulkUpdatePrimaryKey="id"
  records="{{ bulkUpdateData.value }}"
  editorMode="gui"
  resourceName="REPLACE_WITH_RESOURCE_UUID"
  runWhenModelUpdates={false}
  tableName="public.team_members"
/>
```

**`BULK_UPSERT_BY_KEY`:** Inserts or updates. Useful for:
- Saving inline table edits: `records="{{ membersTable.changesetArray }}"`
- Adding a new row: `records="{{ [{ name: 'New', department: 'Eng' }] }}"`
- Duplicating a row: `records="{{ [{ ...membersTable.selectedRow, id: undefined }] }}"`

**Confirmation flow for bulk operations:**
1. **Collect:** A `<JavascriptQuery>` gathers the affected rows into a `<State>` variable
2. **Preview:** A `<ModalFrame>` shows a confirmation dialog with count, affected members (via `<Tags>`), and field summary
3. **Confirm:** User clicks confirm → triggers the bulk query → on success: refresh data + close modal
4. **Safety:** Disable the confirm button if count exceeds a limit or no fields are selected:
   ```jsx
   disabled="{{ bulkUpdateData.value.length > 50 || !selectedFields.value.length }}"
   ```

**Event chain on bulk update success:**
```jsx
<Event id="..." event="success" method="trigger" pluginId="selectMembers" type="datasource" />
<Event id="..." event="success" method="setValue" params={{ ordered: [["value", false]] }}
  pluginId="isBulkUpdate" type="state" />
<Event id="..." event="success" method="hide" pluginId="confirmBulkUpdate" type="widget" />
```

---

## 19. App Pattern Recipes

Complete, importable example apps are provided in the `examples/` directory. Each demonstrates a common Retool app pattern.

### 19.1 Minimal App
**Directory:** `examples/Minimal App/`
**Pattern:** Simplest valid Retool app — one `<Text>` component.
**Files:** `main.rsx`, `functions.rsx`, `metadata.json`, `.positions.json`
**Use as:** Skeleton starter for any new app.

**Structure:**
```
<App> → <Frame $main> → <Text>
```

### 19.2 CRUD Table App
**Directory:** `examples/CRUD Table App/`
**Pattern:** Data table with create modal and edit modal, backed by SQL queries (SELECT, INSERT, UPDATE, DELETE).
**Files:** `main.rsx`, `functions.rsx`, `metadata.json`, `.positions.json`, `src/editModal.rsx`, `lib/selectProducts.sql`

**Structure:**
```
<App>
  → <Frame $main>
      → <Text> (page title)
      → <Modal> → <Form> (create)
      → <Table> (data display + row actions)
  → <ModalFrame> (edit — direct child of App, via Include)
      → <Form>
  → <GlobalFunctions>
      → State editingRowId (tracks which row is being edited)
      → selectProducts (SELECT)
      → insertProduct (INSERT, on form submit)
      → updateProduct (UPDATE_BY → refresh → re-select row → hide modal)
      → deleteProduct (DELETE_BY → refresh → clear selection)
```

**Key patterns demonstrated:**
- Modal with embedded Form for record creation
- ModalFrame (top-level) for editing, triggered by table row action
- Form submission → query trigger → table refresh chain via `<Event>` elements
- `requireConfirmation` on destructive queries
- `initialData` binding form fields to selected table row
- `resourceName="REPLACE_WITH_RESOURCE_UUID"` placeholder pattern
- **State variable** for tracking editing context (Section 18.7)
- **Re-select row after update** via `selectRow` event (preserves UX continuity)
- **Clear selection after delete** via `clearSelection` event

### 19.3 Master-Detail App
**Directory:** `examples/Master-Detail App/`
**Pattern:** Table with a tabbed side panel (`<SplitPaneFrame>`) that shows and edits the selected row's details, with a second "Activity" tab.

**Structure:**
```
<App>
  → <Frame $main>
      → <Text> (page title)
      → <Table> (master list)
  → <SplitPaneFrame position="right" width="{{ dynamic per tab }}">
      → <Container>
          → <Header> → <Text> + <Tabs> + <Button close>
          → <Body>
              → <View "details"> → <Form> (detail editor)
              → <View "activity"> → <Text> (activity placeholder)
  → <GlobalFunctions>
      → State detailTab (tracks active tab)
```

**Key patterns demonstrated:**
- `<SplitPaneFrame>` with `position="right"` and **dynamic width per tab** (Section 18.7)
- Panel hidden when no row selected: `hidden="{{ !table.selectedRow.id }}"`
- **Tabbed Container** inside SplitPaneFrame with `<Tabs navigateContainer={true}>`
- **Close button** in header with `detailPane.hide()` event
- Form `initialData` bound to `table.selectedSourceRow`
- **State variable** for tab tracking
- Positioning: SplitPaneFrame children use `subcontainer`, Views use `container` nesting

### 19.4 Search Filter App
**Directory:** `examples/Search Filter App/`
**Pattern:** Client-side filtering via `setFilterStack()` with text search, dropdowns, and date range — all filters applied instantly without re-querying the database.

**Structure:**
```
<App>
  → <Frame $main>
      → <Text> (page title)
      → <TextInput> (search box with icon)
      → <Select> × 2 (category + status filters)
      → <DateRange> (date range filter)
      → <Button> (reset all filters)
      → <Table> (client-side filtered results)
  → <GlobalFunctions>
      → selectProducts (simple unfiltered SELECT — loads all data)
      → selectCategories (dropdown data source)
      → applyFilters (JavascriptQuery — builds filter stack from widget values)
```

**Key patterns demonstrated:**
- **Client-side `setFilterStack()` pattern** (Section 18.8) — replaces SQL WHERE filtering
- Each filter widget triggers `applyFilters` query on change via `<Event>`
- Filter bar layout: multiple components on the same row using `col` offsets
- `<DateRange>` component for date-based filtering
- Reset button clearing all widgets + triggering `applyFilters` to reset filter stack
- `showClear={true}` on inputs for user convenience
- Debounced text search (300ms) for performance

### 19.5 AI Chat App
**Directory:** `examples/AI Chat App/`
**Pattern:** Chat interface powered by an AI API (OpenAI-compatible).

**Structure:**
```
<App>
  → <Frame $main>
      → <Text> (page title)
      → <Chat queryTargetId="sendMessage">
  → <GlobalFunctions>
      → sendMessage (JavascriptQuery — orchestrates the chat flow)
      → sendToAI (RESTQuery — calls the AI API)
```

**Key patterns demonstrated:**
- `<Chat>` component with `queryTargetId` pointing to a JavascriptQuery
- Chat component automatically passes the user's message to the target query
- JavascriptQuery orchestrating an API call via `await query.trigger()`
- RESTQuery with `bodyType="raw"` for JSON payloads
- `_additionalScope` for passing variables between queries

### 19.6 Advanced CRUD App
**Directory:** `examples/Advanced CRUD App/`
**Pattern:** Team member management app demonstrating all iHeadcount production patterns — the capstone example combining State management, client-side filtering, SqlTransformQuery, bulk operations, tabbed detail pane, and inline editing.

**Structure:**
```
<App>
  → <Frame $main>
      → <Text> (page title)
      → <TextInput> (search)
      → <Select> (department — data from SqlTransformQuery)
      → <Select> (status — static options)
      → <DateRange> (joined date filter)
      → <Button> (reset)
      → <Table> (grouped by department, editable status/role, inline save)
          → ToolbarButtons: Filter, Download, Bulk Update
          → Actions: Edit (shows detail pane), Delete (with confirmation)
  → <SplitPaneFrame> (tabbed detail pane with dynamic width)
      → <Container> → <Header> + <Tabs> + close <Button>
      → <View "details"> → <Form> (full member editor)
      → <View "activity"> → <Text> (placeholder)
  → <ModalFrame> (bulk update confirmation)
      → <Header> → warning title + close button
      → <Body> → warning Text + Tags (affected members) + field summary
      → <Footer> → cancel + confirm (disabled if count > 50)
  → <GlobalFunctions>
      → State: isBulkUpdate, bulkUpdateData
      → selectMembers (main SELECT)
      → selectDepartments (SqlTransformQuery — derived from selectMembers)
      → updateMember (UPDATE_BY → refresh → re-select row)
      → bulkUpdateMembers (BULK_UPDATE_BY_KEY → refresh → reset state → hide modal)
      → deleteMember (DELETE_BY → refresh → clear selection)
      → saveTableChanges (BULK_UPSERT_BY_KEY — inline edits)
      → applyFilters (JavascriptQuery — setFilterStack)
      → setBulkUpdateData (JavascriptQuery — collect rows for bulk op)
```

**Key patterns demonstrated (Sections 18.7–18.10):**
- **State management** (18.7): `isBulkUpdate` flag, `bulkUpdateData` array for modal preview
- **Client-side filtering** (18.8): `setFilterStack()` with debounced search, category, status, and date range filters
- **SqlTransformQuery** (18.9): `selectDepartments` derives dropdown options from `selectMembers` data — no extra DB query
- **Bulk operations** (18.10): `BULK_UPDATE_BY_KEY` with confirmation modal, `BULK_UPSERT_BY_KEY` for inline table saves
- **Tabbed detail pane**: `<SplitPaneFrame>` with `<Container>` → `<Tabs>` → `<View>`, dynamic width per tab
- **Grouped table**: `groupByColumnId` for department-based grouping
- **Event chains**: update → refresh → re-select row; delete → refresh → clear selection; bulk update → refresh → reset state → hide modal
- **Safety patterns**: `requireConfirmation` on delete, `disabled` on bulk confirm button with count guard

---

## Appendix A: Complete Component Tag Reference

| Tag | Category | Source Apps |
|-----|----------|------------|
| `Action` | Table child | All with Table |
| `App` | Root | All |
| `AppStyles` | Top-level | Image Lab, Iris Atlas v2, Experience Studio |
| `Avatar` | Presentation | Katalog, Iris Atlas v2 |
| `Body` | Structural slot | All |
| `Button` | Action | All |
| `ButtonGroup2` | Action | Prompt Studio, Experience Studio |
| `ButtonGroup2-Button` | Action | Prompt Studio, Experience Studio |
| `Cascader` | Input | Experience Studio, iHeadcount |
| `Chat` | Presentation | Iris Atlas v2 |
| `Checkbox` | Input | Prompt Studio, Iris Atlas v2 |
| `Column` | Table child | All with Table |
| `Container` | Layout | All |
| `Date` | Input | iHeadcount |
| `DateRange` | Input | iHeadcount |
| `Divider` | Presentation | All |
| `DocumentTitle` | Top-level | Iris Atlas v2 |
| `DrawerFrame` | Layout | AI Guide Studio, Prompt Studio, Experience Studio |
| `DropdownButton` | Action | Image Lab, Iris AI Images, Katalog, Experience Studio |
| `DynamicWidget_*` | Custom | Iris Atlas v2 |
| `Event` | Event system | All |
| `ExpandedRow` | Table child | Prompt Catalog, Iris Atlas v2 |
| `FileButton` | Input | Prompt Studio, Experience Studio |
| `Folder` | Organizational | All |
| `Footer` | Structural slot | All |
| `Form` | Layout | AI Guide Studio, Katalog, Prompt Studio, Experience Studio, iHeadcount |
| `Frame` | Top-level | All |
| `Function` | Data | Image Lab, Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio, iHeadcount |
| `GlobalFunctions` | Root | All |
| `Header` | Structural slot | All |
| `Image` | Presentation | Image Lab, Prompt Studio, Experience Studio |
| `Include` | Top-level | All |
| `JSONEditor` | Input | Prompt Studio, Experience Studio |
| `JSONExplorer` | Display | Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio |
| `JavascriptQuery` | Data | All |
| `KeyValue` | Display | Chat Insights, iHeadcount |
| `Link` | Action | Prompt Studio, Iris Atlas v2 |
| `Listbox` | Input | Experience Studio |
| `ListView` | Layout | Prompt Studio |
| `ListViewBeta` | Layout | Image Lab, Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio, iHeadcount |
| `Modal` | Layout | AI Guide Studio, Katalog, Prompt Studio |
| `ModalFrame` | Layout | Iris AI Images, Prompt Studio, Iris Atlas v2, Experience Studio, iHeadcount |
| `Module` | Module | AI Guide Studio, Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio |
| `Multiselect` | Input | AI Guide Studio, Prompt Catalog, Prompt Studio, Iris Atlas v2, Experience Studio |
| `Navigation` | Presentation | Katalog, Iris Atlas v2 |
| `NumberInput` | Input | Prompt Studio, Experience Studio |
| `OpenAPIQuery` | Data | Prompt Studio, Experience Studio |
| `Option` | Input child | All |
| `ProgressBar` | Display | Katalog |
| `ProgressCircle` | Display | Iris Atlas v2 |
| `Property` | Display child | Chat Insights, iHeadcount |
| `RESTQuery` | Data | Image Lab, Iris AI Images, Prompt Studio, Iris Atlas v2, Experience Studio |
| `RadioGroup` | Input | Prompt Studio, Experience Studio |
| `S3Query` | Data | Experience Studio |
| `Screen` | Multi-page | Iris Atlas v2 |
| `SegmentedControl` | Input | Prompt Studio, Experience Studio |
| `Select` | Input | All |
| `Slider` | Input | Image Lab, Prompt Studio, Experience Studio |
| `Spacer` | Presentation | AI Guide Studio, Prompt Studio, Iris Atlas v2, Experience Studio |
| `SplitPaneFrame` | Layout | AI Guide Studio, Prompt Studio, Iris Atlas v2, Experience Studio, iHeadcount |
| `SqlQueryUnified` | Data | All |
| `SqlTransformQuery` | Data | Iris Atlas v2, iHeadcount |
| `State` | Data | Image Lab, Iris AI Images, Chat Insights, Prompt Studio, Iris Atlas v2, Experience Studio, iHeadcount |
| `Statistic` | Display | Katalog |
| `Switch` | Input | Image Lab, Prompt Studio, Katalog, Experience Studio, iHeadcount |
| `Table` | Display | All except Katalog |
| `TableLegacy` | Display | Katalog |
| `Tabs` | Input | Chat Insights, Prompt Studio, Katalog, Iris Atlas v2, Experience Studio |
| `Tags` | Display | Prompt Studio, Experience Studio, iHeadcount |
| `TagsWidget2` | Display | Prompt Studio, Iris Atlas v2 |
| `Text` | Presentation | All |
| `TextArea` | Input | All |
| `TextInput` | Input | All |
| `ToggleButton` | Action | Iris Atlas v2 |
| `ToolbarButton` | Table child | Chat Insights, Prompt Catalog, Iris Atlas v2, Experience Studio, iHeadcount |
| `UrlFragments` | Top-level | Prompt Studio |
| `Video` | Presentation | Prompt Studio |
| `View` | Layout child | All with Container |
| `WorkflowRun` | Data | Iris Atlas v2 |

---

## Appendix B: Icon Naming Convention

All icons use a path format: `"bold/category-name"` or `"line/category-name"`

Common prefixes:
- `bold/interface-` — UI actions (delete, edit, arrows, add, setting)
- `bold/image-` — Image-related (picture, flash)
- `bold/mail-` — Communication (chat)
- `bold/programming-` — Development (web, text)
- `bold/computer-` — Devices (voice-mail, connection)
- `bold/travel-` — Navigation (map, compass)
- `bold/phone-` — Phone (telephone)
- `line/interface-` — Line-weight variant of interface icons

Examples:
```
bold/interface-delete-bin-5-alternate
bold/interface-edit-pencil
bold/interface-arrows-synchronize
bold/interface-add-1
bold/interface-search
bold/interface-download-button-2
bold/interface-upload-button-2
bold/interface-arrows-button-down
bold/interface-validation-check
bold/image-picture-landscape-2
bold/interface-edit-magic-wand
line/interface-edit-pencil
```
