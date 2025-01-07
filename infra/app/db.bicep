metadata description = 'Creates an Azure Cosmos DB for NoSQL account with a database.'

param suffix string
param location string = resourceGroup().location
param tags object = {}
param logAnalyticsWorkspaceId string

resource account 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: 'cosmos-${suffix}'
  kind: 'GlobalDocumentDB'
  location: location
  tags: tags
  properties: {
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    apiProperties: {}
    capabilities: [{ name: 'EnableServerless' }]
    minimalTlsVersion: 'Tls12'
  }
}

var databaseName = 'calldb'
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2022-05-15' = {
  name: databaseName
  parent: account
  properties: {
    resource: { id: databaseName }
  }
}

var containerName = 'utterances'
resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2022-05-15' = {
  name: containerName
  parent: database
  properties: {
    resource: {
      id: containerName
      partitionKey: { paths: ['/PartitionKey'] }
    }
    options: {}
  }
}

resource diagnosticLogs 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: account.name
  scope: account
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'DataPlaneRequests'
        enabled: true
      }
      {
        category: 'MongoRequests'
        enabled: true
      }
      {
        category: 'CassandraRequests'
        enabled: true
      }
      {
        category: 'GremlinRequests'
        enabled: true
      }
      {
        category: 'TableApiRequests'
        enabled: true
      }
      {
        category: 'PartitionKeyStatistics'
        enabled: true
      }
      {
        category: 'QueryRuntimeStatistics'
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

output name string = account.name
output endpoint string = account.properties.documentEndpoint
output databaseName string = database.name
output containerName string = container.name
