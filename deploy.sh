#!/bin/bash
set -e

REPO_DIR="/home/ubuntu/ai-hedge-fund"
VENV="$REPO_DIR/venv"
FRONTEND_DIR="$REPO_DIR/frontend"
BACKEND_DIR="$REPO_DIR/backend"
WWW_DIR="/var/www/ai-hedge-fund"

echo "==> Pulling latest from GitHub..."
cd "$REPO_DIR"
git pull origin main

echo "==> Installing Python dependencies..."
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install -r "$BACKEND_DIR/requirements.txt" --quiet

echo "==> Building React frontend..."
cd "$FRONTEND_DIR"
npm install --silent
npm run build

echo "==> Copying build to $WWW_DIR..."
sudo mkdir -p "$WWW_DIR"
sudo cp -r "$FRONTEND_DIR/dist/." "$WWW_DIR/"

echo "==> Restarting backend service..."
sudo systemctl restart ai-hedge-fund
sudo systemctl status ai-hedge-fund --no-pager

echo "==> Reloading nginx..."
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "Deploy complete."
