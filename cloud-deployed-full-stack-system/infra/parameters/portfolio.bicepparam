using '../main.bicep'

param location = 'eastus'
param environmentName = 'portfolio'
param backendImage = readEnvironmentVariable('PHASE9_BACKEND_IMAGE')
param frontendImage = readEnvironmentVariable('PHASE9_FRONTEND_IMAGE')
param postgresAdministratorLogin = 'cloudopsadmin'
param postgresAdministratorPassword = readEnvironmentVariable('PHASE9_POSTGRES_ADMIN_PASSWORD')
param jwtSecretKey = readEnvironmentVariable('PHASE9_JWT_SECRET_KEY')
param additionalTags = {
  costCenter: 'portfolio'
  owner: 'aj'
}
