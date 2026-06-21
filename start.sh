#!/bin/bash
cd "$(dirname "$0")/docker"
docker compose up -d
echo ""
echo "Splunk arrancando... esperá ~2 minutos."
echo "Después entrá a: http://localhost:8000"
echo "Usuario: admin / Contraseña: AcmeCorp2024!"
