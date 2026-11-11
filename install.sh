#!/bin/bash
# 向 Google Chrome 注册本地程序（native messaging host），仅 macOS
set -euo pipefail

HOST_NAME="com.cheapcoder.one_click_clone"
EXTENSION_ID="ghddfnledcmjioejpfdjdfdikaapeejg"
HOST_PATH="$(cd "$(dirname "$0")/host" && pwd)/one_click_clone.py"
MANIFEST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"

chmod +x "$HOST_PATH"
mkdir -p "$MANIFEST_DIR"
cat > "$MANIFEST_DIR/$HOST_NAME.json" <<JSON
{
  "name": "$HOST_NAME",
  "description": "一键 Clone 到本地",
  "path": "$HOST_PATH",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXTENSION_ID/"]
}
JSON
echo "已注册：$MANIFEST_DIR/$HOST_NAME.json"
