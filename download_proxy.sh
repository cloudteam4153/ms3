#!/bin/bash
# Download Cloud SQL Proxy to current directory

# Detect architecture
ARCH=$(uname -m)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

if [[ "$OS" == "darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64"
    else
        URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64"
    fi
else
    URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64"
fi

echo "Downloading Cloud SQL Proxy for $OS $ARCH..."
curl -o cloud-sql-proxy "$URL"
chmod +x cloud-sql-proxy
echo "✅ Cloud SQL Proxy downloaded and made executable!"
echo "Run: ./cloud-sql-proxy unified-inbox-480816:us-central1:unified-inbox-db"
