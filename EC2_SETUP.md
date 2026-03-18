# EC2 Deployment Guide

## Prerequisites

- EC2 instance running **Ubuntu 22.04 LTS** (t2.micro or larger)
- Elastic IP assigned (recommended so the address doesn't change on restart)
- Security group inbound rules:
  | Port | Protocol | Source    | Purpose          |
  |------|----------|-----------|------------------|
  | 22   | TCP      | Your IP   | SSH              |
  | 80   | TCP      | 0.0.0.0/0 | HTTP (nginx)     |
  | 443  | TCP      | 0.0.0.0/0 | HTTPS (optional) |

Port 8000 does **not** need to be open — nginx proxies to it internally.

---

## 1. Connect to the instance

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

---

## 2. System packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx python3-pip python3-venv git

# Node.js 20 (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 3. Clone the repository

```bash
cd /home/ubuntu
git clone https://github.com/Likhith252002/ai-hedge-fund.git
cd ai-hedge-fund
```

---

## 4. Create the .env file

```bash
cat > /home/ubuntu/ai-hedge-fund/.env <<EOF
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
EOF
chmod 600 /home/ubuntu/ai-hedge-fund/.env
```

---

## 5. Python virtual environment and dependencies

```bash
python3 -m venv /home/ubuntu/ai-hedge-fund/venv
/home/ubuntu/ai-hedge-fund/venv/bin/pip install --upgrade pip
/home/ubuntu/ai-hedge-fund/venv/bin/pip install -r /home/ubuntu/ai-hedge-fund/backend/requirements.txt
```

---

## 6. Build the React frontend

No `VITE_API_URL` or `VITE_WS_URL` needed when deploying behind nginx on the
same host — `useWebSocket.js` derives the correct URL from `window.location`.

```bash
cd /home/ubuntu/ai-hedge-fund/frontend
npm install
npm run build
```

Copy the build to nginx's web root:

```bash
sudo mkdir -p /var/www/ai-hedge-fund
sudo cp -r /home/ubuntu/ai-hedge-fund/frontend/dist/. /var/www/ai-hedge-fund/
```

---

## 7. Install the systemd service

```bash
sudo cp /home/ubuntu/ai-hedge-fund/ai-hedge-fund.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-hedge-fund
sudo systemctl start ai-hedge-fund

# Verify it's running
sudo systemctl status ai-hedge-fund
```

Check logs if it fails:

```bash
sudo journalctl -u ai-hedge-fund -n 50 --no-pager
```

---

## 8. Configure nginx

```bash
sudo cp /home/ubuntu/ai-hedge-fund/nginx.conf /etc/nginx/sites-available/ai-hedge-fund
sudo ln -sf /etc/nginx/sites-available/ai-hedge-fund /etc/nginx/sites-enabled/ai-hedge-fund
sudo rm -f /etc/nginx/sites-enabled/default   # remove the default placeholder
sudo nginx -t                                  # confirm config is valid
sudo systemctl enable nginx
sudo systemctl restart nginx
```

---

## 9. Verify the deployment

```bash
# Backend health
curl http://localhost:8000/health

# Frontend via nginx
curl -I http://localhost/
```

Open `http://<EC2_PUBLIC_IP>` in a browser — you should see the AI Hedge Fund UI.

---

## 10. Future deployments

After pushing code changes to GitHub, simply SSH in and run:

```bash
cd /home/ubuntu/ai-hedge-fund
bash deploy.sh
```

`deploy.sh` pulls, rebuilds the frontend, copies static files, and restarts both
the backend service and nginx.

---

## Optional: HTTPS with Let's Encrypt

If you point a domain name at the EC2 IP:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo systemctl reload nginx
```

Certbot will rewrite `nginx.conf` to add SSL and set up auto-renewal.
WebSocket connections will automatically use `wss://` via the `resolveWsUrl()`
logic in `useWebSocket.js`.
