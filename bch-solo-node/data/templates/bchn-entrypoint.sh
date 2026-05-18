#!/bin/sh
set -eu

echo "[bch-solo-node] BCHN entrypoint starting"

if ! command -v bitcoind >/dev/null 2>&1; then
  echo "[bch-solo-node] ERROR: bitcoind not found in PATH"
  exit 127
fi

extra=""
if [ -f /data/.reindex-chainstate ]; then
  echo "[bch-solo-node] Reindex requested (chainstate)."
  rm -f /data/.reindex-chainstate || true
  extra="-reindex-chainstate"
fi

echo "[bch-solo-node] Exec: bitcoind -datadir=/data -printtoconsole $extra"
exec bitcoind -datadir=/data -printtoconsole $extra
