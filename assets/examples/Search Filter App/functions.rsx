<GlobalFunctions>
<SqlQueryUnified
    id="selectProducts"
    query={include("./lib/selectProducts.sql", "string")}
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    warningCodes={[]}
  />
  <SqlQueryUnified
    id="selectCategories"
    query="SELECT id, name FROM public.categories ORDER BY name"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    warningCodes={[]}
  />
  <JavascriptQuery
    id="applyFilters"
    query={include("./lib/applyFilters.js", "string")}
  />
</GlobalFunctions>
