<GlobalFunctions>
  <State id="editingRowId" value="{{ null }}" />
  <SqlQueryUnified
    id="selectProducts"
    query={include("./lib/selectProducts.sql", "string")}
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    transformer="return data"
    warningCodes={[]}
  />
  <SqlQueryUnified
    id="insertProduct"
    actionType="INSERT"
    changesetIsObject={true}
    changesetObject="{{ { ...CreateProductForm.data } }}"
    editorMode="gui"
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.products"
  >
    <Event
      id="77aa88bb"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectProducts"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="99cc00dd"
      event="success"
      method="close"
      params={{}}
      pluginId="createModal"
      type="widget"
      waitMs="0"
      waitType="debounce"
    />
  </SqlQueryUnified>
  <SqlQueryUnified
    id="updateProduct"
    actionType="UPDATE_BY"
    changesetIsObject={true}
    changesetObject="{{ { ...EditProductForm.data } }}"
    editorMode="gui"
    filterBy={'[{"key":"id","value":"{{ productsTable.selectedRow.id }}","operation":"="}]'}
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.products"
  >
    <Event
      id="aabb1122"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectProducts"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="ccdd3344"
      event="success"
      method="hide"
      params={{}}
      pluginId="editModal"
      type="widget"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="eeff7788"
      event="success"
      method="selectRow"
      params={{ ordered: [["key", "{{ productsTable.selectedRow.id }}"]] }}
      pluginId="productsTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </SqlQueryUnified>
  <SqlQueryUnified
    id="deleteProduct"
    actionType="DELETE_BY"
    editorMode="gui"
    filterBy={'[{"key":"id","value":"{{ productsTable.selectedRow.id }}","operation":"="}]'}
    requireConfirmation={true}
    confirmationMessage="Are you sure you want to delete **{{ productsTable.selectedRow.name }}**?"
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    runWhenModelUpdates={false}
    tableName="public.products"
  >
    <Event
      id="eeff5566"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="selectProducts"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="aabb9900"
      event="success"
      method="clearSelection"
      params={{}}
      pluginId="productsTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </SqlQueryUnified>
</GlobalFunctions>
