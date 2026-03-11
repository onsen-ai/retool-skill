<GlobalFunctions>
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
    id="selectCategories"
    query="SELECT id, name FROM public.categories ORDER BY name"
    resourceDisplayName="your-database"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    transformer="return data"
    warningCodes={[]}
  />
  <JavascriptQuery
    id="applyFilters"
    query={include("./lib/applyFilters.js", "string")}
    resourceDisplayName="JavascriptQuery"
    runWhenModelUpdates={false}
  />
</GlobalFunctions>
