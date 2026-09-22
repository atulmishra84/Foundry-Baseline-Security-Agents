using './main.bicep'

param location = 'eastus'
param prefix = 'ai-security'
param containerAppName = 'ca-ai-security-runtime'
// acrName is auto-generated from uniqueSuffix — override here if needed
// param acrName = 'myuniquacr'
// foundryRuntimeToken is injected by the CD pipeline via --parameters foundryRuntimeToken=$TOKEN
// param foundryRuntimeToken = ''
