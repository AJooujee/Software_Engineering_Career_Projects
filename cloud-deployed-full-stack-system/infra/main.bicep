targetScope = 'resourceGroup'

@description('Azure region selected by the Phase 9 capability preflight.')
@allowed([
  'eastus'
])
param location string = 'eastus'

@description('Short environment label used in Azure resource names and tags.')
@minLength(2)
@maxLength(12)
param environmentName string = 'portfolio'

@description('Immutable GHCR backend image reference, preferably a commit-SHA tag.')
param backendImage string

@description('Immutable GHCR frontend image reference, preferably a commit-SHA tag.')
param frontendImage string

@description('PostgreSQL administrator login. This is not the application administrator email.')
@minLength(3)
@maxLength(63)
param postgresAdministratorLogin string = 'cloudopsadmin'

@description('URL-safe PostgreSQL administrator password supplied only at deployment time.')
@secure()
@minLength(16)
param postgresAdministratorPassword string

@description('JWT signing secret supplied only at deployment time.')
@secure()
@minLength(32)
param jwtSecretKey string

@description('Optional tags merged with the Phase 9 baseline tags.')
param additionalTags object = {}

var deploymentToken = toLower(uniqueString(subscription().subscriptionId, resourceGroup().id, environmentName))
var namePrefix = 'cloudops-${environmentName}'
var commonTags = union({
  application: 'cloud-operations'
  environment: environmentName
  managedBy: 'bicep'
  phase: '9'
}, additionalTags)

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-${deploymentToken}'
  params: {
    location: location
    workspaceName: 'log-${namePrefix}-${deploymentToken}'
    tags: commonTags
  }
}

module database 'modules/database.bicep' = {
  name: 'database-${deploymentToken}'
  params: {
    location: location
    serverName: 'pg-${namePrefix}-${deploymentToken}'
    databaseName: 'cloud_operations'
    administratorLogin: postgresAdministratorLogin
    administratorPassword: postgresAdministratorPassword
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    tags: commonTags
  }
}

module platform 'modules/container-apps.bicep' = {
  name: 'container-apps-${deploymentToken}'
  params: {
    location: location
    managedEnvironmentName: 'cae-${namePrefix}-${deploymentToken}'
    backendAppName: 'backend-${deploymentToken}'
    frontendAppName: 'frontend-${deploymentToken}'
    migrationJobName: 'migration-${deploymentToken}'
    backendImage: backendImage
    frontendImage: frontendImage
    postgresServerFqdn: database.outputs.serverFqdn
    postgresDatabaseName: database.outputs.databaseName
    postgresAdministratorLogin: postgresAdministratorLogin
    postgresAdministratorPassword: postgresAdministratorPassword
    jwtSecretKey: jwtSecretKey
    logAnalyticsCustomerId: monitoring.outputs.customerId
    logAnalyticsSharedKey: monitoring.outputs.sharedKey
    tags: commonTags
  }
}

output location string = location
output frontendUrl string = 'https://${platform.outputs.frontendFqdn}'
output frontendAppName string = platform.outputs.frontendAppName
output backendAppName string = platform.outputs.backendAppName
output migrationJobName string = platform.outputs.migrationJobName
output postgresServerName string = database.outputs.serverName
output logAnalyticsWorkspaceName string = monitoring.outputs.workspaceName
output databaseNetworkMode string = 'Public endpoint with TLS and Azure-service firewall rule; cost-first portfolio profile.'
