param suffix string
param location string = resourceGroup().location
param tags object = {}
param openaiName string
param chatDeploymentName string
param chatVersion string // todo: how to get this programmatically from the deployment?
param cosmosAccountName string
param cosmosDbName string
param comsosContainerName string
param appServicePlanId string
param applicationInsightsName string
param logAnalyticsWorkspaceId string
param allowedOrigins array = []

resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openaiName
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosAccountName
}

resource appService 'Microsoft.Web/sites@2022-03-01' = {
  name: 'app-${suffix}'
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlanId
    siteConfig: {
      linuxFxVersion: 'python|3.11'
      alwaysOn: true
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'
      appCommandLine: ''
      numberOfWorkers: null
      minimumElasticInstanceCount: null
      use32BitWorkerProcess: false
      functionAppScaleLimit: null
      healthCheckPath: ''
      cors: {
        allowedOrigins: union(['https://portal.azure.com', 'https://ms.portal.azure.com'], allowedOrigins)
      }
    }
    clientAffinityEnabled: false
    httpsOnly: true
    virtualNetworkSubnetId: null
  }

  identity: { type: 'SystemAssigned' }

  resource basicPublishingCredentialsPoliciesFtp 'basicPublishingCredentialsPolicies' = {
    name: 'ftp'
    properties: {
      allow: false
    }
  }

  resource basicPublishingCredentialsPoliciesScm 'basicPublishingCredentialsPolicies' = {
    name: 'scm'
    properties: {
      allow: false
    }
  }
}

// Updates to the single Microsoft.sites/web/config resources that need to be performed sequentially
// sites/web/config 'appsettings'
resource configAppSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  name: 'appsettings'
  parent: appService
  properties: union(
    { AZURE_OPENAI_BASE_URL: openAi.properties.endpoint },
    { AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: chatDeploymentName },
    { AZURE_OPENAI_API_VERSION: chatVersion },
    { AZURE_COSMOSDB_ENDPOINT: cosmos.properties.documentEndpoint },
    { AZURE_COSMOSDB_DATABASE: cosmosDbName },
    { AZURE_COSMOSDB_CONTAINER: comsosContainerName },
    {
      SCM_DO_BUILD_DURING_DEPLOYMENT: string(true)
      ENABLE_ORYX_BUILD: string(true)
    },
    { PYTHON_ENABLE_GUNICORN_MULTIWORKERS: 'true' },
    { APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString },
    { APPINSIGHTS_INSTRUMENTATIONKEY: applicationInsights.properties.InstrumentationKey },
    { ApplicationInsightsAgent_EXTENSION_VERSION: '~2' }
  )
}

// sites/web/config 'logs'
resource configLogs 'Microsoft.Web/sites/config@2022-03-01' = {
  name: 'logs'
  parent: appService
  properties: {
    applicationLogs: { fileSystem: { level: 'Verbose' } }
    detailedErrorMessages: { enabled: true }
    failedRequestsTracing: { enabled: true }
    httpLogs: { fileSystem: { enabled: true, retentionInDays: 1, retentionInMb: 35 } }
  }
  dependsOn: [configAppSettings]
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = if (!empty(applicationInsightsName)) {
  name: applicationInsightsName
}

///////////////////////////////////////////////////

resource appServiceDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: appService.name
  scope: appService
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
      }
      {
        category: 'AppServiceAppLogs'
        enabled: true
      }
      {
        category: 'AppServiceAuditLogs'
        enabled: true
      }
      {
        category: 'AppServiceIPSecAuditLogs'
        enabled: true
      }
      {
        category: 'AppServicePlatformLogs'
        enabled: true
      }
      {
        category: 'AppServiceAuthenticationLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output name string = appService.name
output url string = 'https://${appService.properties.defaultHostName}'
output identity string = appService.identity.principalId
