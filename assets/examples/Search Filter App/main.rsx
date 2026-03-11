<App>
  <Include src="./functions.rsx" />
  <Frame
    id="$main"
    isHiddenOnDesktop={false}
    isHiddenOnMobile={false}
    padding="8px 12px"
    paddingType="normal"
    sticky={false}
    type="main"
  >
    <Text
      id="pageTitle"
      marginType="normal"
      value="### Product Catalog"
      verticalAlign="center"
    />
    <TextInput
      id="searchInput"
      iconBefore="bold/interface-search"
      label=""
      marginType="normal"
      placeholder="Search by name..."
      showClear={true}
    >
      <Event
        id="ab12cd34"
        event="change"
        method="trigger"
        params={{ ordered: [] }}
        pluginId="applyFilters"
        type="datasource"
        waitMs="300"
        waitType="debounce"
      />
    </TextInput>
    <Select
      id="categoryFilter"
      data="{{ selectCategories.data }}"
      emptyMessage="All categories"
      itemMode="mapped"
      label="Category"
      labelPosition="top"
      labels="{{ item.name }}"
      marginType="normal"
      placeholder="All categories"
      showClear={true}
      showSelectionIndicator={true}
      values="{{ item.id }}"
    >
      <Event
        id="cd34ef56"
        event="change"
        method="trigger"
        params={{ ordered: [] }}
        pluginId="applyFilters"
        type="datasource"
        waitMs="0"
        waitType="debounce"
      />
    </Select>
    <Select
      id="statusFilter"
      emptyMessage="All statuses"
      itemMode="static"
      label="Status"
      labelPosition="top"
      marginType="normal"
      placeholder="All statuses"
      showClear={true}
      showSelectionIndicator={true}
    >
      <Option id="f1a2b" value="active" label="Active" />
      <Option id="f3c4d" value="draft" label="Draft" />
      <Option id="f5e6f" value="archived" label="Archived" />
      <Event
        id="ef56ab78"
        event="change"
        method="trigger"
        params={{ ordered: [] }}
        pluginId="applyFilters"
        type="datasource"
        waitMs="0"
        waitType="debounce"
      />
    </Select>
    <DateRange
      id="dateRangeFilter"
      label="Updated"
      labelPosition="top"
      marginType="normal"
      showClear={true}
    >
      <Event
        id="ab78cd90"
        event="change"
        method="trigger"
        params={{ ordered: [] }}
        pluginId="applyFilters"
        type="datasource"
        waitMs="0"
        waitType="debounce"
      />
    </DateRange>
    <Button
      id="resetBtn"
      marginType="normal"
      styleVariant="outline"
      text="Reset"
    >
      <Event
        id="aa11bb22"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="searchInput"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="cc33dd44"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="categoryFilter"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="ee55ff66"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="statusFilter"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="11223344"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="dateRangeFilter"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="55667788"
        event="click"
        method="trigger"
        params={{ ordered: [] }}
        pluginId="applyFilters"
        type="datasource"
        waitMs="100"
        waitType="debounce"
      />
    </Button>
    <Table
      id="resultsTable"
      cellSelection="none"
      data="{{ selectProducts.data }}"
      defaultSelectedRow={{ mode: "none", indexType: "display", index: 0 }}
      heightType="auto"
      primaryKeyColumnId="c01a1"
      rowHeight="medium"
      searchMode="caseInsensitive"
      showBorder={true}
      showFooter={true}
      showHeader={true}
      templatePageSize={20}
    >
      <Column
        id="c01a1"
        alignment="left"
        editable={false}
        format="string"
        key="id"
        label="ID"
        position="center"
        size={60}
      />
      <Column
        id="c02b2"
        alignment="left"
        format="string"
        key="name"
        label="Name"
        position="center"
        size={200}
      />
      <Column
        id="c03c3"
        alignment="left"
        format="tag"
        formatOptions={{ automaticColors: true }}
        key="category_name"
        label="Category"
        position="center"
        size={120}
      />
      <Column
        id="c04d4"
        alignment="left"
        format="tag"
        formatOptions={{ automaticColors: true }}
        key="status"
        label="Status"
        position="center"
        size={100}
      />
      <Column
        id="c05e5"
        alignment="right"
        format="decimal"
        formatOptions={{ showSeparators: true, notation: "standard" }}
        key="price"
        label="Price"
        position="center"
        size={100}
      />
      <Column
        id="c06f6"
        alignment="left"
        format="datetime"
        key="updated_at"
        label="Updated"
        position="center"
        size={140}
      />
      <ToolbarButton id="tb01" icon="bold/interface-text-formatting-filter-2" label="Filter" type="filter" />
    </Table>
  </Frame>
</App>
