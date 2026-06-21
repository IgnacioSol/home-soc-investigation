#!/bin/bash
cd "$(dirname "$0")/docker"
docker compose down
echo ""
echo "Splunk apagado. Los datos quedaron guardados."
