#!/bin/sh
set -eu

mkdir -p /config /www /www/pool /www/users

if [ ! -f /config/ckpool.conf ]; then
  if [ ! -f /templates/ckpool.conf.template ]; then
    echo "[bch-solo-node] ERROR: missing /templates/ckpool.conf.template"
    exit 1
  fi
  echo "[bch-solo-node] Seeding /config/ckpool.conf from template"
  envsubst < /templates/ckpool.conf.template > /config/ckpool.conf
fi

rm -f /tmp/ckpool/*.pid 2>/dev/null || true

if command -v ckpool >/dev/null 2>&1; then
  exec ckpool -k -L -c /config/ckpool.conf
elif [ -x /bin/ckpool ]; then
  exec /bin/ckpool -k -L -c /config/ckpool.conf
elif [ -x /usr/bin/ckpool ]; then
  exec /usr/bin/ckpool -k -L -c /config/ckpool.conf
else
  echo "ckpool binary not found in image"
  exit 1
fi
