#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

RG="${RG:-PBFLTools-RG}"
APP_NAME="${APP_NAME:-PBFL-DiscoveryTool}"

echo "→ Building frontend (npm run build)"
(cd frontend && npm ci && npm run build)

echo "→ Staging deploy bundle"
rm -rf .deploy deploy.zip
mkdir -p .deploy/frontend
cp -r backend/app                .deploy/app
cp    backend/requirements.txt   .deploy/requirements.txt
cp -r frontend/out               .deploy/frontend/out

echo "→ Zipping"
(cd .deploy && zip -qr ../deploy.zip .)

echo "→ Deploying to App Service: $APP_NAME (resource group: $RG)"
az webapp deploy \
  --resource-group "$RG" \
  --name "$APP_NAME" \
  --src-path deploy.zip \
  --type zip

rm -rf .deploy deploy.zip
echo "✓ Deployed. Tail logs with:"
echo "    az webapp log tail --resource-group $RG --name $APP_NAME"
