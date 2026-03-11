<GlobalFunctions>
  <JavascriptQuery
    id="sendMessage"
    query={include("./lib/sendMessage.js", "string")}
    resourceName="JavascriptQuery"
    _additionalScope={{ array: ["message"] }}
  />
  <RESTQuery
    id="sendToAI"
    body='{"model":"gpt-4o","messages":[{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":"{{ message }}"}]}'
    bodyType="raw"
    headers={'[{"key":"Content-Type","value":"application/json"}]'}
    query="chat/completions"
    resourceDisplayName="your-openai-resource"
    resourceName="REPLACE_WITH_RESOURCE_UUID"
    resourceTypeOverride=""
    type="POST"
    queryTimeout="60000"
    _additionalScope={{ array: ["message"] }}
  />
</GlobalFunctions>
