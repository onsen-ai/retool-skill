<GlobalFunctions>
  <RESTQuery
    id="fetchUsers"
    enableTransformer={true}
    query="https://api.example.com/users"
    resourceName="REST-WithoutResource"
    transformer="// Transform API response — adjust to your API shape
return data"
  />
  <RESTQuery
    id="updateUser"
    body='{"email":"{{ editEmail.value }}"}'
    bodyType="raw"
    headers={'[{"key":"Content-Type","value":"application/json"}]'}
    query="https://api.example.com/users/{{ usersTable.selectedRow.id }}"
    resourceName="REST-WithoutResource"
    runWhenModelUpdates={false}
    type="PATCH"
  >
    <Event
      id="c7d8e9f0"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="fetchUsers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="a1b2c3d5"
      event="success"
      method="selectRow"
      params={{ ordered: [["key", "{{ usersTable.selectedRow.id }}"]] }}
      pluginId="usersTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </RESTQuery>
  <RESTQuery
    id="activateUser"
    body='{"status":"active"}'
    bodyType="raw"
    headers={'[{"key":"Content-Type","value":"application/json"}]'}
    query="https://api.example.com/users/{{ usersTable.selectedRow.id }}"
    resourceName="REST-WithoutResource"
    runWhenModelUpdates={false}
    type="PATCH"
  >
    <Event
      id="d6e7f8a9"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="fetchUsers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="b0c1d2e3"
      event="success"
      method="selectRow"
      params={{ ordered: [["key", "{{ usersTable.selectedRow.id }}"]] }}
      pluginId="usersTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </RESTQuery>
  <RESTQuery
    id="deactivateUser"
    body='{"status":"inactive"}'
    bodyType="raw"
    headers={'[{"key":"Content-Type","value":"application/json"}]'}
    query="https://api.example.com/users/{{ usersTable.selectedRow.id }}"
    requireConfirmation={true}
    confirmationMessage="Deactivate **{{ usersTable.selectedRow.name }}**?"
    resourceName="REST-WithoutResource"
    runWhenModelUpdates={false}
    type="PATCH"
  >
    <Event
      id="f4a5b6c7"
      event="success"
      method="trigger"
      params={{ ordered: [] }}
      pluginId="fetchUsers"
      type="datasource"
      waitMs="0"
      waitType="debounce"
    />
    <Event
      id="d8e9f0a1"
      event="success"
      method="selectRow"
      params={{ ordered: [["key", "{{ usersTable.selectedRow.id }}"]] }}
      pluginId="usersTable"
      type="widget"
      waitMs="100"
      waitType="debounce"
    />
  </RESTQuery>
  <JavascriptQuery
    id="applyFilters"
    query={include("./lib/applyFilters.js", "string")}
  />
</GlobalFunctions>
