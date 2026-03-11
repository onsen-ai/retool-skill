<App>
  <Include src="./functions.rsx" />
  <Include src="./src/detailPane.rsx" />
  <Include src="./src/confirmBulkUpdate.rsx" />
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
      value="### Team Members"
      verticalAlign="center"
    />
    <TextInput
      id="searchInput"
      iconBefore="bold/interface-search"
      label=""
      marginType="normal"
      placeholder="Search by name or email..."
      showClear={true}
    >
      <Event
        id="a1b2c3d4"
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
      id="departmentFilter"
      data="{{ selectDepartments.data }}"
      emptyMessage="All departments"
      itemMode="mapped"
      label="Department"
      labelPosition="top"
      labels="{{ item.label }}"
      marginType="normal"
      placeholder="All departments"
      showClear={true}
      showSelectionIndicator={true}
      values="{{ item.value }}"
    >
      <Event
        id="e5f6a7b8"
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
      <Option id="s1a1a" value="active" label="Active" />
      <Option id="s2b2b" value="on_leave" label="On Leave" />
      <Option id="s3c3c" value="offboarded" label="Offboarded" />
      <Event
        id="c9d0e1f2"
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
      label="Joined"
      labelPosition="top"
      marginType="normal"
      showClear={true}
    >
      <Event
        id="a3b4c5d6"
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
        id="e7f8a9b0"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="searchInput"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="c1d2e3f4"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="departmentFilter"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="a5b6c7d8"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="statusFilter"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="e9f0a1b2"
        event="click"
        method="clearValue"
        params={{}}
        pluginId="dateRangeFilter"
        type="widget"
        waitMs="0"
        waitType="debounce"
      />
      <Event
        id="c3d4e5f6"
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
      id="membersTable"
      cellSelection="none"
      changesetArray={[]}
      clearChangesetOnSave={true}
      data="{{ selectMembers.data }}"
      defaultSelectedRow={{ mode: "index", indexType: "display", index: 0 }}
      enableSaveActions={true}
      groupByColumnId="c04d4"
      heightType="auto"
      primaryKeyColumnId="c01a1"
      rowHeight="medium"
      rowSelection="single"
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
        size={180}
      />
      <Column
        id="c03c3"
        alignment="left"
        format="string"
        key="email"
        label="Email"
        position="center"
        size={220}
      />
      <Column
        id="c04d4"
        alignment="left"
        format="tag"
        formatOptions={{ automaticColors: true }}
        key="department"
        label="Department"
        position="center"
        size={130}
      />
      <Column
        id="c05e5"
        alignment="left"
        editable={true}
        format="tag"
        formatOptions={{ automaticColors: true }}
        key="status"
        label="Status"
        position="center"
        size={100}
      />
      <Column
        id="c06f6"
        alignment="left"
        format="date"
        key="joined_date"
        label="Joined"
        position="center"
        size={120}
      />
      <Column
        id="c07a7"
        alignment="left"
        editable={true}
        format="string"
        key="role"
        label="Role"
        position="center"
        size={150}
      />
      <Action id="a01a1" icon="bold/interface-edit-pencil" label="Edit">
        <Event
          id="a7b8c9d0"
          event="clickAction"
          method="show"
          params={{}}
          pluginId="detailPane"
          type="widget"
          waitMs="0"
          waitType="debounce"
        />
      </Action>
      <Action id="a02b2" icon="bold/interface-delete-bin-5-alternate" label="Delete">
        <Event
          id="e1f2a3b4"
          event="clickAction"
          method="trigger"
          params={{ ordered: [] }}
          pluginId="deleteMember"
          type="datasource"
          waitMs="0"
          waitType="debounce"
        />
      </Action>
      <ToolbarButton id="tb01" icon="bold/interface-text-formatting-filter-2" label="Filter" type="filter" />
      <ToolbarButton id="tb02" icon="bold/interface-download-button-2" label="Download" type="download" />
      <ToolbarButton id="tb03" icon="bold/interface-arrows-synchronize" label="Bulk Update" type="custom">
        <Event
          id="c5d6e7f8"
          event="click"
          method="trigger"
          params={{ ordered: [] }}
          pluginId="setBulkUpdateData"
          type="datasource"
          waitMs="0"
          waitType="debounce"
        />
      </ToolbarButton>
      <Event
        id="a9b0c1d2"
        event="save"
        method="trigger"
        params={{ ordered: [] }}
        pluginId="saveTableChanges"
        type="datasource"
        waitMs="0"
        waitType="debounce"
      />
    </Table>
  </Frame>
</App>
