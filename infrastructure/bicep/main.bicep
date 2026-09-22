@description('Location for all resources')
param location string = 'eastus'

@description('Unique suffix for globally unique resource names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('Name prefix for all resources')
param prefix string = 'ai-security'

@description('Azure Container Registry name (must be globally unique, alphanumeric only)')
param acrName string = 'acr${take(replace(uniqueSuffix, '-', ''), 12)}'

@description('Container App name for the Foundry runtime service')
param containerAppName string = 'ca-ai-security-runtime'

@description('Foundry runtime bearer token (stored as Container App secret)')
@secure()
param foundryRuntimeToken string = ''

// -----------------------------------------------
// Log Analytics Workspace (SOC Telemetry)
// -----------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-${prefix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// -----------------------------------------------
// Application Insights (Agent Tracing)
// -----------------------------------------------
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// -----------------------------------------------
// Key Vault (Secrets)
// -----------------------------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-sec-${take(uniqueSuffix, 10)}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
  }
}

// -----------------------------------------------
// Storage Account (SoT artifacts)
// -----------------------------------------------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'staisec${take(uniqueSuffix, 10)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource sotContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'source-of-truth'
  properties: {
    publicAccess: 'None'
  }
}

resource schemasContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'schemas'
  properties: {
    publicAccess: 'None'
  }
}

// -----------------------------------------------
// Azure OpenAI Service
// -----------------------------------------------
resource openAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: 'aoai-${prefix}-${uniqueSuffix}'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'aoai-${prefix}-${uniqueSuffix}'
    publicNetworkAccess: 'Enabled'
  }
}

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAI
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
  }
}

// -----------------------------------------------
// AI Foundry Hub
// -----------------------------------------------
resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' = {
  name: 'hub-${prefix}'
  location: location
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'AI Security Platform Hub'
    description: 'Hub for AI Security Agent Platform on Azure AI Foundry'
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    hbiWorkspace: false
    publicNetworkAccess: 'Enabled'
  }
}

// -----------------------------------------------
// AI Foundry Project
// -----------------------------------------------
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' = {
  name: 'project-security-agents'
  location: location
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Security Agents Project'
    description: 'Contains AI Security Engineer, Red Team, and Runtime SOC agents'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
}

// -----------------------------------------------
// Azure Container Registry (ACR)
// -----------------------------------------------
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

// -----------------------------------------------
// Container Apps Environment
// -----------------------------------------------
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-ai-security'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// -----------------------------------------------
// Container App (Foundry Runtime Service)
// -----------------------------------------------
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: 'system'
        }
      ]
      secrets: foundryRuntimeToken != '' ? [
        {
          name: 'foundry-runtime-token'
          value: foundryRuntimeToken
        }
      ] : []
    }
    template: {
      containers: [
        {
          name: containerAppName
          // Image will be updated by CD pipeline after first ACR push
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAI.properties.endpoint
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              value: 'gpt-4o'
            }
            {
              name: 'FOUNDRY_USE_AZURE_AD'
              value: 'true'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT'
              value: storageAccount.name
            }
            {
              name: 'AZURE_RESOURCE_GROUP'
              value: resourceGroup().name
            }
            {
              name: 'AZURE_AI_PROJECT'
              value: aiProject.name
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            {
              name: 'FOUNDRY_SOC_EXECUTE'
              value: 'false'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Grant Container App identity AcrPull role on the registry
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, containerApp.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------
// Outputs
// -----------------------------------------------
output resourceGroupName string = resourceGroup().name
output aiHubName string = aiHub.name
output aiProjectName string = aiProject.name
output openAIEndpoint string = openAI.properties.endpoint
output openAIName string = openAI.name
output storageAccountName string = storageAccount.name
output keyVaultName string = keyVault.name
output logAnalyticsWorkspaceId string = logAnalytics.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output acrLoginServer string = acr.properties.loginServer
output acrName string = acr.name
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output containerAppName string = containerApp.name



