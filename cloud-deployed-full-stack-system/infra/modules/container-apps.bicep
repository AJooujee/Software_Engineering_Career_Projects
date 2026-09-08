param location string
param managedEnvironmentName string
param backendAppName string
param frontendAppName string
param migrationJobName string
param backendImage string
param frontendImage string
param postgresServerFqdn string
param postgresDatabaseName string
param postgresAdministratorLogin string

@secure()
param postgresAdministratorPassword string

@secure()
param jwtSecretKey string

param logAnalyticsCustomerId string

@secure()
param logAnalyticsSharedKey string

param tags object

var databaseUrl = 'postgresql+psycopg://${postgresAdministratorLogin}:${postgresAdministratorPassword}@${postgresServerFqdn}:5432/${postgresDatabaseName}?sslmode=require'
var backendEnvironment = [
  {
    name: 'APP_ENV'
    value: 'production'
  }
  {
    name: 'DATABASE_URL'
    secretRef: 'database-url'
  }
  {
    name: 'JWT_SECRET_KEY'
    secretRef: 'jwt-secret-key'
  }
  {
    name: 'JWT_ALGORITHM'
    value: 'HS256'
  }
  {
    name: 'ACCESS_TOKEN_EXPIRE_MINUTES'
    value: '30'
  }
  {
    name: 'JWT_ISSUER'
    value: 'cloud-operations-api'
  }
  {
    name: 'JWT_AUDIENCE'
    value: 'cloud-operations-client'
  }
]
var applicationSecrets = [
  {
    name: 'database-url'
    value: databaseUrl
  }
  {
    name: 'jwt-secret-key'
    value: jwtSecretKey
  }
]

resource managedEnvironment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: managedEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    publicNetworkAccess: 'Enabled'
  }
}

resource backendApp 'Microsoft.App/containerApps@2025-07-01' = {
  name: backendAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        allowInsecure: false
        external: false
        targetPort: 8000
        transport: 'http'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: applicationSecrets
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          env: backendEnvironment
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 20
              timeoutSeconds: 5
              failureThreshold: 3
              successThreshold: 1
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health/ready'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 6
              successThreshold: 1
            }
          ]
          resources: {
            cpu: any('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
      terminationGracePeriodSeconds: 30
    }
  }
}

resource frontendApp 'Microsoft.App/containerApps@2025-07-01' = {
  name: frontendAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        allowInsecure: false
        external: true
        targetPort: 8080
        transport: 'http'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          env: [
            {
              name: 'BACKEND_UPSTREAM'
              value: backendAppName
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 8080
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 20
              timeoutSeconds: 5
              failureThreshold: 3
              successThreshold: 1
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 8080
                scheme: 'HTTP'
              }
              initialDelaySeconds: 3
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 6
              successThreshold: 1
            }
          ]
          resources: {
            cpu: any('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
      terminationGracePeriodSeconds: 30
    }
  }
  dependsOn: [
    backendApp
  ]
}

resource migrationJob 'Microsoft.App/jobs@2025-07-01' = {
  name: migrationJobName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: managedEnvironment.id
    configuration: {
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
      replicaRetryLimit: 1
      replicaTimeout: 600
      secrets: applicationSecrets
      triggerType: 'Manual'
    }
    template: {
      containers: [
        {
          name: 'migration'
          image: backendImage
          command: [
            'python'
          ]
          args: [
            '-m'
            'alembic'
            'upgrade'
            'head'
          ]
          env: backendEnvironment
          resources: {
            cpu: any('0.25')
            memory: '0.5Gi'
          }
        }
      ]
    }
  }
}

output frontendFqdn string = frontendApp.properties.configuration.ingress.fqdn
output frontendAppName string = frontendApp.name
output backendAppName string = backendApp.name
output migrationJobName string = migrationJob.name
