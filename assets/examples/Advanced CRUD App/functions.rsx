<GlobalFunctions>
  <State id="isBulkUpdate" value="{{ false }}" />
  <State id="bulkUpdateData" value="{{ [] }}" />

  <SqlQueryUnified
    id="selectMembers"
    query={include("./lib/selectMembers.sql", "string")}
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    transformer="return data"
    warningCodes={[]}
  />

  <SqlTransformQuery
    id="selectDepartments"
    query="SELECT DISTINCT department AS label, department AS value FROM {{ selectMembers.data }} ORDER BY department"
    resourceName="SQL Transforms"
    transformer="return data"
  />

  <SqlQueryUnified
    id="updateMember"
    actionType="UPDATE_BY"
    changesetIsObject={true}
    changesetObject="{{ { ...DetailForm.data } }}"
    editorMode="gui"
    filterBy={'[{"key":"id","value":"{{ membersTable.selectedRow.id }}","operation":"="}]'}
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.team_members"
  >
    <Event
      id="aa11bb22"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectMembers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="cc33dd44"
      event="success"
      method="selectRow"
      params={{ ordered: [["key", "{{ membersTable.selectedRow.id }}"]] }}
      pluginId="membersTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </SqlQueryUnified>

  <SqlQueryUnified
    id="bulkUpdateMembers"
    actionType="BULK_UPDATE_BY_KEY"
    bulkUpdatePrimaryKey="id"
    editorMode="gui"
    records="{{ bulkUpdateData.value }}"
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.team_members"
  >
    <Event
      id="ee55ff66"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectMembers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="11223344"
      event="success"
      method="setValue"
      params={{ ordered: [["value", false]] }}
      pluginId="isBulkUpdate"
      type="state"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="55667788"
      event="success"
      method="hide"
      params={{}}
      pluginId="confirmBulkUpdate"
      type="widget"
      waitMs="0"
      waitType="debounce"
    />
  </SqlQueryUnified>

  <SqlQueryUnified
    id="deleteMember"
    actionType="DELETE_BY"
    editorMode="gui"
    filterBy={'[{"key":"id","value":"{{ membersTable.selectedRow.id }}","operation":"="}]'}
    requireConfirmation={true}
    confirmationMessage="Are you sure you want to remove **{{ membersTable.selectedRow.name }}** from the team?"
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.team_members"
  >
    <Event
      id="99aabb00"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectMembers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="ccddee11"
      event="success"
      method="clearSelection"
      params={{}}
      pluginId="membersTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </SqlQueryUnified>

  <SqlQueryUnified
    id="saveTableChanges"
    actionType="BULK_UPSERT_BY_KEY"
    bulkUpdatePrimaryKey="id"
    editorMode="gui"
    records="{{ membersTable.changesetArray }}"
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.team_members"
  >
    <Event
      id="22334455"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectMembers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
  </SqlQueryUnified>

  <JavascriptQuery
    id="applyFilters"
    query={include("./lib/applyFilters.js", "string")}
    resourceDisplayName="JavascriptQuery"
    runWhenModelUpdates={false}
  />

  <JavascriptQuery
    id="setBulkUpdateData"
    query={include("./lib/setBulkUpdateData.js", "string")}
    resourceDisplayName="JavascriptQuery"
    runWhenModelUpdates={false}
  />
</GlobalFunctions>
