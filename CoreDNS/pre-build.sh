#!/bin/bash

set -euo pipefail

REPO="coredns/coredns"
DIR="coredns"

LATEST_TAG=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")')
echo "Latest release: $LATEST_TAG"
LATEST_URL="https://github.com/$REPO/archive/refs/tags/$LATEST_TAG.tar.gz"
echo "Download URL: $LATEST_URL"

wget "$LATEST_URL" -O- | tar xz
mv "$DIR-$LATEST_TAG" "$DIR"
