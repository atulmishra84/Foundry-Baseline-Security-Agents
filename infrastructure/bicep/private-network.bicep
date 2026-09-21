@description('Region (must match existing Foundry resources)')
param location string = 'eastus'

@description('Existing storage account name')
param storageAccountName string

@description('Existing Key Vault name')
param keyVaultName string

@description('Existing Azure OpenAI account name')
param openAiAccountName string

@description('VNet address space')
param vnetPrefix string = '10.60.0.0/16'

var peSubnetPrefix = '10.60.1.0/24'
var reservedCaePrefix = '10.60.2.0/23'

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: 'vnet-ai-security'
  location: location
  properties: {
    addressSpace: { addressPrefixes: [vnetPrefix] }
    subnets: [
      {
        name: 'snet-private-endpoints'
        properties: {
          addressPrefix: peSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'snet-container-apps'
        properties: {
          addressPrefix: reservedCaePrefix
          delegations: [
            {
              name: 'cae'
              properties: { serviceName: 'Microsoft.App/environments' }
            }
          ]
        }
      }
    ]
  }
}

resource blobZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.core.windows.net'
  location: 'global'
}

resource vaultZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.vaultcore.azure.net'
  location: 'global'
}

resource openaiZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.openai.azure.com'
  location: 'global'
}

resource blobLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: blobZone
  name: 'link-vnet-ai-security'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}

resource vaultLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: vaultZone
  name: 'link-vnet-ai-security'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}

resource openaiLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: openaiZone
  name: 'link-vnet-ai-security'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource openAi 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' existing = {
  name: openAiAccountName
}

resource peStorage 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-staiseclfje77wuun-blob'
  location: location
  properties: {
    subnet: { id: '${vnet.id}/subnets/snet-private-endpoints' }
    privateLinkServiceConnections: [
      {
        name: 'pe-storage-blob'
        properties: {
          privateLinkServiceId: storage.id
          groupIds: ['blob']
        }
      }
    ]
  }
}

resource peVault 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-kv-sec-vault'
  location: location
  properties: {
    subnet: { id: '${vnet.id}/subnets/snet-private-endpoints' }
    privateLinkServiceConnections: [
      {
        name: 'pe-kv'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: ['vault']
        }
      }
    ]
  }
}

resource peOpenAi 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-aoai-account'
  location: location
  properties: {
    subnet: { id: '${vnet.id}/subnets/snet-private-endpoints' }
    privateLinkServiceConnections: [
      {
        name: 'pe-aoai'
        properties: {
          privateLinkServiceId: openAi.id
          groupIds: ['account']
        }
      }
    ]
  }
}

resource peStorageDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: peStorage
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      { name: 'blob', properties: { privateDnsZoneId: blobZone.id } }
    ]
  }
}

resource peVaultDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: peVault
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      { name: 'vault', properties: { privateDnsZoneId: vaultZone.id } }
    ]
  }
}

resource peOpenAiDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: peOpenAi
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      { name: 'openai', properties: { privateDnsZoneId: openaiZone.id } }
    ]
  }
}

output vnetId string = vnet.id
output privateEndpointSubnetId string = '${vnet.id}/subnets/snet-private-endpoints'
output containerAppsSubnetId string = '${vnet.id}/subnets/snet-container-apps'
output publicAccessStillEnabled bool = true
