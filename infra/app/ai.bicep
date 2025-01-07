param suffix string
param location string = resourceGroup().location
param tags object = {}
param logAnalyticsWorkspaceId string

var name = 'openai-${suffix}'
var chatDeploymentName = 'chat'
var chatDeploymentVersion = '2024-02-15-preview' // todo: how can we get this from bicep?
var embeddingDeploymentName = 'embedding'

resource account 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: false
  }
  sku: {
    name: 'S0'
  }
}

resource chat 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: account
  name: chatDeploymentName
  properties: {
    model: {
      name: 'gpt-4o'
      format: 'OpenAI'
      version: '2024-05-13' // need to figure this out better
    }
    raiPolicyName: null
  }
  sku: {
    name: 'Standard'
    capacity: 20
  }
}

resource diagnosticLogs 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: account.name
  scope: account
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'Audit'
        enabled: true
      }
      {
        category: 'RequestResponse'
        enabled: true
      }
      {
        category: 'Trace'
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

output chatDeployment string = chatDeploymentName
output chatDeploymentVersion string = chatDeploymentVersion
output embeddingDeployment string = embeddingDeploymentName
output endpoint string = '${account.properties.endpoint}openai/'
output name string = account.name
output version string = chatDeploymentVersion
