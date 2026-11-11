#!/usr/bin/env bash
# ChartTrio (English site) production bootstrap — Debian 12 (DogYun HK KC)
# Run as root. Idempotent: re-running pulls latest code, rebuilds, restarts.
#
# PARALLEL INSTANCE — this script installs a SECOND, fully separate copy of the
# app next to the live Chinese site and must never disturb aimingpan.com:
#   Chinese site : /opt/lifeinsight, unit "lifeinsight", backend 127.0.0.1:8000
#   English site : /opt/charttrio,   unit "charttrio",   backend 127.0.0.1:8001
# Separate app dir, venv, backend.env, prompts dir, systemd unit, frontend
# build, and Caddy access log. The only shared resources are the OS packages,
# Node, Caddy itself, and the firewall.
#
# !!! BEFORE THE FIRST RUN !!!
# 1. REPO below is a PLACEHOLDER. The English tree (en-tree) currently has NO
#    git repository at all (it was rsynced from the Chinese tree). Create the
#    repo (suggested: VinceLing0529/charttrio-web), `git init` the English
#    tree, and push it there first — the clone step will fail until then.
#    NEVER point REPO at the Chinese repo (lifeinsight-web): the two trees
#    have diverged (UI text, prices, prompts, snapshot defaults).
# 2. DNS for charttrio.com / www.charttrio.com must point at this server,
#    otherwise Caddy cannot obtain the TLS certificate.
# 3. After running, fill the secrets in /opt/charttrio/backend.env (Stripe
#    live key + the charttrio webhook secret + DeepSeek key) and copy the
#    English prompt templates into /opt/charttrio/prompts/ (they live outside
#    the repo, same de-sensitisation rule as the Chinese site), then re-run
#    this script (or `systemctl restart charttrio`).
#
# CADDY WARNING: the Chinese deploy/bootstrap.sh REWRITES the whole
# /etc/caddy/Caddyfile. Any Chinese-site deploy therefore DROPS the charttrio
# block appended by this script. Re-run this script after a Chinese deploy to
# restore it (the Caddy step below is idempotent and never touches the
# aimingpan.com block).
set -euxo pipefail

APP_DIR=/opt/charttrio
REPO=https://github.com/VinceLing0529/charttrio-web.git  # PLACEHOLDER — see header note 1
BACKEND_PORT=8001
PILOT_PUBKEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILUB/5EjUlRFzlg8jPTaI+pndV5Z6d8rswl/LiDfOQD2 hatch'

# ---- swap (shared with the Chinese instance; created once, protects builds) ----
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
if [ ! -f /opt/charttrio/backend.env ]; then
  printf 'STRIPE_SECRET_KEY=\nSTRIPE_WEBHOOK_SECRET=\nDEEPSEEK_API_KEY=\nPROMPTS_DIR=/opt/charttrio/prompts\nSNAPSHOT_LANG=en\nPUBLIC_BASE_URL=https://charttrio.com\n' > /opt/charttrio/backend.env
fi
# prompt templates live outside the repo (de-sensitised); copy them here by hand
mkdir -p /opt/charttrio/prompts

cat > /etc/systemd/system/charttrio.service <<'UNIT'
[Unit]
Description=ChartTrio backend (uvicorn)
After=network.target

[Service]
WorkingDirectory=/opt/charttrio/backend/app
EnvironmentFile=/opt/charttrio/backend.env
ExecStart=/opt/charttrio/backend/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable charttrio
systemctl restart charttrio  # restart (not just enable --now) so pulled code changes take effect

# ---- 示例报告种子（reports/ 被 gitignore，演示订单从仓库内的 demo_report 播种，幂等不覆盖） ----
# NOTE: the in-repo demo_report is still the Chinese sample until the English
# demo report is generated; seeding is harmless and becomes correct once the
# English demo files replace them in the repo.
mkdir -p "$APP_DIR/backend/app/data/reports/LIFEDEMO1995"
cp -n "$APP_DIR/backend/app/data/demo_report/"*.json "$APP_DIR/backend/app/data/reports/LIFEDEMO1995/" 2>/dev/null || true

# ---- frontend (same-origin: empty API URL -> relative /api via Caddy) ----
cd "$APP_DIR/frontend"
npm install --no-audit --no-fund
REACT_APP_API_URL= npm run build

# ---- Caddy: APPEND-ONLY strategy ----
# The aimingpan.com block belongs to the Chinese bootstrap, which owns and
# rewrites /etc/caddy/Caddyfile. This script NEVER rewrites the file: it only
# removes its own previously appended block (between the CHARTRIO markers)
# and appends a fresh one, leaving every other block byte-identical.
CADDYFILE=/etc/caddy/Caddyfile
mkdir -p /var/log/caddy
touch "$CADDYFILE"
# the caddy service user must own its log file — if root (e.g. a root-run
# `caddy validate` or an earlier bootstrap) created it first, caddy fails to
# start with "permission denied" opening the log writer
touch /var/log/caddy/access-charttrio.log
chown caddy:caddy /var/log/caddy/access-charttrio.log 2>/dev/null || true
# drop our previous block if present (idempotent re-runs)
sed -i '/# BEGIN CHARTRIO/,/# END CHARTRIO/d' "$CADDYFILE"
cat >> "$CADDYFILE" <<'CADDY'
# BEGIN CHARTRIO (managed by deploy/bootstrap-en.sh — do not hand-edit)
charttrio.com, www.charttrio.com {
	log {
		output file /var/log/caddy/access-charttrio.log
		format json
	}
	handle /api/* {
		reverse_proxy 127.0.0.1:8001
	}
	handle {
		root * /opt/charttrio/frontend/build
		try_files {path} /index.html
		file_server
	}
}
# END CHARTRIO
CADDY
caddy validate --config "$CADDYFILE" || { echo "Caddyfile invalid — NOT reloading"; exit 1; }
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

echo "BOOTSTRAP_EN_DONE"
systemctl is-active charttrio caddy
systemctl is-active lifeinsight || echo "WARNING: Chinese instance not active"
curl -s http://127.0.0.1:8001/health || true
echo
curl -sk -o /dev/null -w 'charttrio frontend https %{http_code}\n' --resolve charttrio.com:443:127.0.0.1 https://charttrio.com/ || true
