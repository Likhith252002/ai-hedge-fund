# Deployment

## Live Instance

| Property | Value |
|:---|:---|
| URL | http://18.224.16.180 |
| Provider | AWS EC2 |
| Instance type | t2.micro |
| OS | Ubuntu 22.04 LTS |
| Region | us-east-2 (Ohio) |

---

## Stack on the server

```
Internet → nginx :80
              ├── /          → /var/www/ai-hedge-fund  (React build, static files)
              ├── /api/*     → localhost:8000           (FastAPI REST)
              └── /ws/*      → localhost:8000           (WebSocket, upgraded)

localhost:8000  ← uvicorn managed by systemd (ai-hedge-fund.service)
```

---

## Configuration files

| File | Purpose |
|:---|:---|
| `nginx.conf` | nginx server block — static serving + reverse proxy |
| `ai-hedge-fund.service` | systemd unit that keeps uvicorn running |
| `deploy.sh` | One-command redeploy script |
| `EC2_SETUP.md` | Full walkthrough for provisioning a fresh EC2 instance |

---

## nginx configuration

`nginx.conf` defines a single server block on port 80:

- **`/`** — serves the React build from `/var/www/ai-hedge-fund` with `try_files` SPA fallback
- **`/api/`** — proxied to `http://127.0.0.1:8000` with forwarding headers and a 120 s read timeout
- **`/ws/`** — proxied with `Upgrade: $http_upgrade` / `Connection: upgrade` for WebSocket; 300 s timeout

Installed at `/etc/nginx/sites-available/ai-hedge-fund` and symlinked into `sites-enabled/`.

---

## systemd service

`ai-hedge-fund.service` runs uvicorn as the `ubuntu` user:

```
ExecStart=/home/ubuntu/ai-hedge-fund/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
EnvironmentFile=/home/ubuntu/ai-hedge-fund/.env   # ANTHROPIC_API_KEY lives here
Restart=always / RestartSec=5
```

Installed at `/etc/systemd/system/ai-hedge-fund.service`.

Useful commands:

```bash
sudo systemctl status ai-hedge-fund        # current state
sudo systemctl restart ai-hedge-fund       # manual restart
sudo journalctl -u ai-hedge-fund -f        # live logs
```

---

## Redeploying after a code change

```bash
# 1. Push your changes to GitHub
git push origin main

# 2. SSH into the EC2 instance
ssh -i your-key.pem ubuntu@18.224.16.180

# 3. Run the deploy script
cd /home/ubuntu/ai-hedge-fund
bash deploy.sh
```

`deploy.sh` performs these steps automatically:

1. `git pull origin main`
2. `pip install -r backend/requirements.txt` (inside the venv)
3. `npm install && npm run build` (frontend)
4. `sudo cp -r frontend/dist/. /var/www/ai-hedge-fund/`
5. `sudo systemctl restart ai-hedge-fund`
6. `sudo nginx -t && sudo systemctl reload nginx`

---

## Environment variables

Secrets are stored in `/home/ubuntu/ai-hedge-fund/.env` on the server (not committed to git):

```
ANTHROPIC_API_KEY=sk-ant-...
```

The systemd service loads this file via `EnvironmentFile=`.

---

## Ports and security group

| Port | Open to | Purpose |
|------|---------|---------|
| 22 | Your IP only | SSH |
| 80 | 0.0.0.0/0 | HTTP (nginx) |
| 443 | 0.0.0.0/0 | HTTPS (if TLS is added) |

Port 8000 is **not** exposed externally — uvicorn only listens on localhost.

---

## Adding HTTPS (optional)

If you point a domain at the instance IP:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo systemctl reload nginx
```

Certbot rewrites `nginx.conf` to add TLS. The frontend's `useWebSocket.js` will
automatically use `wss://` on HTTPS pages — no rebuild needed.
