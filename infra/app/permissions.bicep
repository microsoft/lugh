param userPrincipalId string
param apiPrincipalId string
param cosmosAccountName string

var roleIds = [
  // Azure AI Developer
  '64702f94-c441-49e6-a78b-ef80e0188fee'
  // todo: add any more permissions here...
]

module userRoles '../core/security/role.bicep' = [
  for roleId in roleIds: {
    name: 'user-${roleId}'
    params: {
      principalId: userPrincipalId
      principalType: 'User'
      roleDefinitionId: roleId
    }
  }
]

module apiRoles '../core/security/role.bicep' = [
  for roleId in roleIds: {
    name: 'api-${roleId}'
    params: {
      principalId: apiPrincipalId
      principalType: 'ServicePrincipal'
      roleDefinitionId: roleId
    }
  }
]

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosAccountName
}

resource roleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2022-08-15' = {
  parent: cosmos
  name: guid(subscription().id, cosmos.id, cosmos.name, 'sql-role')
  properties: {
    assignableScopes: [
      cosmos.id
    ]
    permissions: [
      {
        dataActions: [
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
        ]
        notDataActions: []
      }
    ]
    roleName: 'Reader Writer'
    type: 'CustomRole'
  }
}

module apiRole '../core/database/cosmos/sql/cosmos-sql-role-assign.bicep' = {
  name: 'api-role'
  params: {
    accountName: cosmosAccountName
    roleDefinitionId: roleDefinition.id
    principalId: apiPrincipalId
  }
}

resource userRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2022-05-15' = {
  parent: cosmos
  name: guid(roleDefinition.id, userPrincipalId, cosmos.id)
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: roleDefinition.id
    scope: cosmos.id
  }
}
