# Systemd Deployment Files

This directory tracks the systemd units used on the VPS so service recovery is reproducible after reboot or machine replacement.

## Managed services

- `ap-mock-api.service`: AP mock API on port `8003`
- `ap-sso.service`: AP SSO/chat frontend on port `8002`
- `dify-compose.service`: starts the Dify Docker Compose stack after Docker is up
- `docker.service.override.conf`: overrides the host Docker unit to start `dockerd` directly instead of relying on the broken socket activation path observed on the VPS

## Install on host

Copy the unit files into `/etc/systemd/system/` and the override into `/etc/systemd/system/docker.service.d/override.conf`, then run:

```bash
systemctl daemon-reload
systemctl enable docker.service dify-compose.service ap-mock-api.service ap-sso.service
systemctl disable docker.socket
systemctl restart docker.service
systemctl restart dify-compose.service
systemctl restart ap-mock-api.service
systemctl restart ap-sso.service
```
