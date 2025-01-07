targetScope = 'subscription'

// The main bicep module to provision Azure resources.
// For a more complete walkthrough to understand how this file works with azd,
// see https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/make-azd-compatible?pivots=azd-create

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Emit sensitive logs (viz. prompts and completions) to the OpenTelemetry collector. Defaults to false.')
param emitSensitiveLogs bool = false

// Optional parameters to override the default azd resource naming conventions.
// Add the following to main.parameters.json to provide values:
// "resourceGroupName": {
//      "value": "myGroupName"
// }
param resourceGroupName string = ''

var abbrs = loadJsonContent('./abbreviations.json')

// tags that should be applied to all resources.
var tags = {
  // Tag all resources with the environment name.
  'azd-env-name': environmentName
}

// Generate a unique token to be used in naming resources.
// Remove linter suppression after using.
#disable-next-line no-unused-vars
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Name of the service defined in azure.yaml
// A tag named azd-service-name with this value should be applied to the service host resource, such as:
//   Microsoft.Web/sites for appservice, function
// Example usage:
//   tags: union(tags, { 'azd-service-name': apiServiceName })
#disable-next-line no-unused-vars
var apiServiceName = 'python-api'

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Add resources to be provisioned below.
// A full example that leverages azd bicep modules can be seen in the todo-python-mongo template:
// https://github.com/Azure-Samples/todo-python-mongo/tree/main/infra

module monitoring 'app/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    suffix: resourceToken
    location: location
    tags: tags
  }
}

module openAi 'app/ai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    suffix: resourceToken
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module db 'app/db.bicep' = {
  name: 'db'
  scope: rg
  params: {
    suffix: resourceToken
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: rg
  params: {
    // Add parameters to the module here.
    // The module will be able to access these parameters as if they were defined in the module.
    // Example:
    //   name: 'appserviceplan'
    //   location: location
    //   tags: tags
    name: '${abbrs.webServerFarms}${environmentName}'
    sku: {
      name: 'B1'
    }
  }
}

module api 'app/api.bicep' = {
  name: 'api'
  scope: rg
  params: {
    // Add parameters to the module here.
    // The module will be able to access these parameters as if they were defined in the module.
    // Example:
    //   name: 'api'
    //   location: location
    //   tags: tags
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    suffix: resourceToken
    location: location
    tags: {
      'azd-service-name': apiServiceName
    }
    appServicePlanId: appServicePlan.outputs.id
    openaiName: openAi.outputs.name
    chatDeploymentName: openAi.outputs.chatDeployment
    chatVersion: openAi.outputs.chatDeploymentVersion
    cosmosAccountName: db.outputs.name
    cosmosDbName: db.outputs.databaseName
    comsosContainerName: db.outputs.containerName
  }
}

module permissions 'app/permissions.bicep' = {
  name: 'permissions'
  scope: rg
  params: {
    apiPrincipalId: api.outputs.identity
    userPrincipalId: principalId
    cosmosAccountName: db.outputs.name
  }
}

// Add outputs from the deployment here, if needed.
//
// This allows the outputs to be referenced by other bicep deployments in the deployment pipeline,
// or by the local machine as a way to reference created resources in Azure for local development.
// Secrets should not be added here.
//
// Outputs are automatically saved in the local azd environment .env file.
// To see these outputs, run `azd env get-values`,  or `azd env get-values --output json` for json output.
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId

// app insights
output AZURE_APP_INSIGHTS_INSTRUMENTATION_KEY string = monitoring.outputs.applicationInsightsInstrumentationKey
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString

// open ai
output AZURE_OPENAI_BASE_URL string = openAi.outputs.endpoint
output AZURE_OPENAI_CHAT_DEPLOYMENT_NAME string = openAi.outputs.chatDeployment
output AZURE_OPENAI_API_VERSION string = openAi.outputs.chatDeploymentVersion

// cosmos
output AZURE_COSMOSDB_ENDPOINT string = db.outputs.endpoint
output AZURE_COSMOSDB_DATABASE string = db.outputs.databaseName
output AZURE_COSMOSDB_CONTAINER string = db.outputs.containerName


output USER_PRINCIPAL_ID string = principalId
output SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE bool = emitSensitiveLogs
