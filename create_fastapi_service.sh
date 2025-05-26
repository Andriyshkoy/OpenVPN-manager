#!/usr/bin/env bash
#
# create_fastapi_service.sh
#   Quickly sets up a FastAPI application to autostart using systemd.
#   Requires sudo (creates a file /etc/systemd/system/<SERVICE_NAME>.service).

set -euo pipefail

### === SETTINGS ========================================================== ###
SERVICE_NAME="fastapi"
LINUX_USER="root"
WORK_DIR="/root/manager"
EXEC_CMD="$WORK_DIR/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000"
### ======================================================================= ###

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [[ $EUID -ne 0 ]]; then
  echo "Run the script with sudo, otherwise I can't write to /etc/systemd."; exit 1
fi

echo "👉 Writing $SERVICE_FILE"
cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=FastAPI application (${SERVICE_NAME})
After=network.target

[Service]
Type=simple
User=${LINUX_USER}
WorkingDirectory=${WORK_DIR}
ExecStart=${EXEC_CMD}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "👉 Reloading systemd daemons"
systemctl daemon-reload

echo "👉 Enabling autostart and starting the service immediately"
systemctl enable --now "${SERVICE_NAME}.service"

echo "✅ Done. Status ↓"
systemctl status "${SERVICE_NAME}.service" --no-pager
