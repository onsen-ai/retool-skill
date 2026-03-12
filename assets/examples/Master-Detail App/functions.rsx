<GlobalFunctions>
<State id="detailTab" value="{{ 'details' }}" />
  <SqlQueryUnified
    id="selectCustomers"
    query={include("./lib/selectCustomers.sql", "string")}
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    warningCodes={[]}
  />
  <SqlQueryUnified
    id="updateCustomer"
    actionType="UPDATE_BY"
    changesetIsObject={true}
    changesetObject="{{ { ...DetailForm.data } }}"
    editorMode="gui"
    filterBy={'[{"key":"id","value":"{{ customersTable.selectedRow.id }}","operation":"="}]'}
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.customers"
  >
    <Event
      id="cc33dd44"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectCustomers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
  </SqlQueryUnified>
</GlobalFunctions>
