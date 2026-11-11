#!/usr/bin/env bash
# LifeInsight production bootstrap — Debian 12 (DogYun HK KC)
# Run as root. Idempotent: re-running pulls latest code, rebuilds, restarts.
#   curl -fsSL https://raw.githubusercontent.com/VinceLing0529/lifeinsight-web/main/deploy/bootstrap.sh -o /root/b.sh
#   nohup bash /root/b.sh > /root/bootstrap.log 2>&1 &
set -euxo pipefail

APP_DIR=/opt/lifeinsight
REPO=https://github.com/VinceLing0529/lifeinsight-web.git
PILOT_PUBKEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILUB/5EjUlRFzlg8jPTaI+pndV5Z6d8rswl/LiDfOQD2 hatch'

# ---- swap (protects the frontend build from OOM on 2 GiB RAM) ----
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-dev build-essential git curl ufw \
  debian-keyring debian-archive-keyring apt-transport-https gpg fonts-noto-cjk

# ---- Node 20 ----
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

# ---- Caddy ----
if ! command -v caddy >/dev/null 2>&1; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y
  apt-get install -y caddy
fi

# ---- code ----
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR" && git pull --ff-only
else
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

# ---- backend ----
python3 -m venv backend/.venv
backend/.venv/bin/pip install -q -r backend/requirements.txt
# flatlib pins pyswisseph 2.08 which is broken on newer Pythons; upgrade per repo notes
backend/.venv/bin/pip install -q -U "pyswisseph>=2.10"

# env file: created once with placeholders, never overwritten (secrets filled in later)
if [ ! -f /opt/lifeinsight/backend.env ]; then
  printf 'STRIPE_SECRET_KEY=\nSTRIPE_WEBHOOK_SECRET=\nPUBLIC_BASE_URL=http://43.247.133.19\n' > /opt/lifeinsight/backend.env
fi

cat > /etc/systemd/system/lifeinsight.service <<'UNIT'
[Unit]
Description=LifeInsight backend (uvicorn)
After=network.target

[Service]
WorkingDirectory=/opt/lifeinsight/backend/app
EnvironmentFile=/opt/lifeinsight/backend.env
ExecStart=/opt/lifeinsight/backend/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable lifeinsight
systemctl restart lifeinsight  # restart (not just enable --now) so code changes in pulled code actually take effect

# ---- 示例报告种子（reports/ 被 gitignore，演示订单从仓库内的 demo_report 播种，幂等不覆盖） ----
mkdir -p "$APP_DIR/backend/app/data/reports/LIFEDEMO1995"
cp -n "$APP_DIR/backend/app/data/demo_report/"*.json "$APP_DIR/backend/app/data/reports/LIFEDEMO1995/" 2>/dev/null || true

# ---- frontend (same-origin: empty API URL -> relative /api via Caddy) ----
cd "$APP_DIR/frontend"
npm install --no-audit --no-fund
REACT_APP_API_URL= npm run build

# ---- Caddy: static frontend + /api reverse proxy, SPA fallback ----
cat > /etc/caddy/Caddyfile <<'CADDY'
aimingpan.com, www.aimingpan.com {
	log {
		output file /var/log/caddy/access.log
		format json
	}
	handle /api/* {
		reverse_proxy 127.0.0.1:8000
	}
	handle {
		root * /opt/lifeinsight/frontend/build
		try_files {path} /index.html
		file_server
	}
}

:80 {
	handle /api/* {
		reverse_proxy 127.0.0.1:8000
	}
	handle {
		root * /opt/lifeinsight/frontend/build
		try_files {path} /index.html
		file_server
	}
}
CADDY
systemctl reload caddy || systemctl restart caddy

# ---- firewall ----
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# ---- SSH key for maintenance access ----
mkdir -p /root/.ssh && chmod 700 /root/.ssh
grep -q 'AAAAC3NzaC1lZDI1NTE5AAAAILUB' /root/.ssh/authorized_keys 2>/dev/null || echo "$PILOT_PUBKEY" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

echo "BOOTSTRAP_DONE"
systemctl is-active lifeinsight caddy
curl -s http://127.0.0.1:8000/health || true
echo
curl -s -o /dev/null -w 'frontend http %{http_code}\n' http://127.0.0.1/ || true
