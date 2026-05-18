import base64
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


APP_ID = "bch-solo-node"
APP_VERSION = "0.3.0"

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = Path(os.getenv("STATIC_DIR", "/app/static"))
DATA_DIR = Path("/data")
STATE_DIR = DATA_DIR / "ui" / "state"
NODE_CONF_PATH = DATA_DIR / "node" / "bitcoin.conf"
NODE_REINDEX_FLAG_PATH = DATA_DIR / "node" / ".reindex-chainstate"
CKPOOL_CONF_PATH = Path(os.getenv("CKPOOL_CONF_PATH", str(DATA_DIR / "pool" / "config" / "ckpool.conf")))
CKPOOL_STATUS_DIR = Path(os.getenv("CKPOOL_STATUS_DIR", str(DATA_DIR / "pool" / "www" / "pool")))
CKPOOL_USERS_DIR = Path(os.getenv("CKPOOL_USERS_DIR", str(DATA_DIR / "pool" / "www" / "users")))
BLOCKS_STATE_PATH = STATE_DIR / "blocks.json"
LUCK_STATE_PATH = STATE_DIR / "luck.json"

BCH_RPC_HOST = os.getenv("BCH_RPC_HOST", "bchn")
BCH_RPC_PORT = int(os.getenv("BCH_RPC_PORT", "28332"))
BCH_RPC_USER = os.getenv("BCH_RPC_USER", "bch")
BCH_RPC_PASS = os.getenv("BCH_RPC_PASS", "")

DEFAULT_BLOCK_SCAN_DEPTH = 288
MAX_BLOCK_SCAN_DEPTH = 5000
ACTIVE_WORKER_WINDOW_S = 15 * 60


def ensure_dirs():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def json_response(payload, status=HTTPStatus.OK):
    body = json.dumps(payload).encode("utf-8")
    return status, body, "application/json; charset=utf-8"


def read_json(path: Path, default):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_conf_lines(path: Path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def read_conf_kv(path: Path):
    values = {}
    for raw in read_conf_lines(path):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def set_conf_key(lines, key, value, comment_out=False):
    target = f"{key}="
    rendered = f"{key}={value}"
    found = False
    updated = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("#"):
            uncommented = stripped[1:].strip()
            if uncommented.startswith(target):
                found = True
                updated.append(f"# {rendered}" if comment_out else rendered)
                continue
        if stripped.startswith(target):
            found = True
            updated.append(f"# {rendered}" if comment_out else rendered)
            continue
        updated.append(raw)
    if not found:
        updated.append(f"# {rendered}" if comment_out else rendered)
    return updated


def update_node_conf(network: str, prune: int, txindex: int):
    if network not in {"mainnet", "testnet", "regtest"}:
        raise ValueError("invalid network")
    lines = read_conf_lines(NODE_CONF_PATH)
    lines = set_conf_key(lines, "server", "1")
    lines = set_conf_key(lines, "txindex", str(int(bool(txindex))))
    lines = set_conf_key(lines, "prune", str(int(prune)))
    lines = set_conf_key(lines, "testnet", "1", comment_out=(network != "testnet"))
    lines = set_conf_key(lines, "regtest", "1", comment_out=(network != "regtest"))
    NODE_CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    NODE_CONF_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def current_node_settings():
    conf = read_conf_kv(NODE_CONF_PATH)
    network = "mainnet"
    if conf.get("regtest") == "1":
        network = "regtest"
    elif conf.get("testnet") == "1":
        network = "testnet"
    return {
        "network": network,
        "prune": int(conf.get("prune") or 0),
        "txindex": int(conf.get("txindex") or 0),
    }


def request_reindex():
    NODE_REINDEX_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    NODE_REINDEX_FLAG_PATH.write_text(str(int(time.time())), encoding="utf-8")


def rpc_call(method, params=None):
    payload = json.dumps(
        {
            "jsonrpc": "1.0",
            "id": APP_ID,
            "method": method,
            "params": params or [],
        }
    ).encode("utf-8")
    auth = base64.b64encode(f"{BCH_RPC_USER}:{BCH_RPC_PASS}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        f"http://{BCH_RPC_HOST}:{BCH_RPC_PORT}",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc
    if result.get("error"):
        raise RuntimeError(str(result["error"]))
    return result.get("result")


def node_status():
    info = rpc_call("getblockchaininfo")
    network = rpc_call("getnetworkinfo")
    mempool = rpc_call("getmempoolinfo")
    return {
        "chain": info.get("chain"),
        "blocks": int(info.get("blocks") or 0),
        "headers": int(info.get("headers") or 0),
        "difficulty": float(info.get("difficulty") or 0.0),
        "verificationprogress": float(info.get("verificationprogress") or 0.0),
        "initialblockdownload": bool(info.get("initialblockdownload", False)),
        "connections": int(network.get("connections") or 0),
        "subversion": str(network.get("subversion") or ""),
        "mempool_bytes": int(mempool.get("bytes") or 0),
        "size_on_disk": int(info.get("size_on_disk") or 0),
        "pruned": bool(info.get("pruned", False)),
        "warnings": str(info.get("warnings") or network.get("warnings") or "").strip() or None,
        "reindexRequested": NODE_REINDEX_FLAG_PATH.exists(),
        "reindexRequired": False,
        "template_ready": not bool(info.get("initialblockdownload", False)),
    }


def read_ckpool_conf():
    if not CKPOOL_CONF_PATH.exists():
        return {}
    try:
        return json.loads(CKPOOL_CONF_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_ckpool_conf(conf):
    CKPOOL_CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    CKPOOL_CONF_PATH.write_text(json.dumps(conf, indent=2) + "\n", encoding="utf-8")


def current_pool_settings():
    conf = read_ckpool_conf()
    payout_address = str(conf.get("btcaddress") or "").strip()
    return {
        "payoutAddress": payout_address,
        "configured": bool(payout_address) and payout_address != "CHANGEME_BCH_PAYOUT_ADDRESS",
        "validated": None,
        "validationWarning": None,
        "mindiff": int(conf.get("mindiff") or 1),
        "startdiff": int(conf.get("startdiff") or 16),
        "maxdiff": int(conf.get("maxdiff") or 0),
        "warning": None if payout_address and payout_address != "CHANGEME_BCH_PAYOUT_ADDRESS" else "Set a payout address before mining.",
    }


def update_pool_settings(payload):
    conf = read_ckpool_conf()
    conf["btcaddress"] = str(payload.get("payoutAddress") or "").strip() or "CHANGEME_BCH_PAYOUT_ADDRESS"
    conf["mindiff"] = int(payload.get("mindiff") or 1)
    conf["startdiff"] = int(payload.get("startdiff") or 16)
    conf["maxdiff"] = int(payload.get("maxdiff") or 0)
    write_ckpool_conf(conf)
    return current_pool_settings()


def extract_json_blob(text: str):
    text = text.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return {}
    return {}


def parse_worker_records():
    workers = []
    if not CKPOOL_USERS_DIR.exists():
        return workers
    for path in sorted(CKPOOL_USERS_DIR.iterdir()):
        if not path.is_file():
            continue
        obj = extract_json_blob(path.read_text(encoding="utf-8", errors="replace"))
        records = obj.get("worker") or obj.get("workers") or []
        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list):
            continue
        for item in records:
            if not isinstance(item, dict):
                continue
            lastshare = item.get("lastshare") or item.get("lastShare")
            try:
                lastshare = int(float(lastshare))
            except Exception:
                lastshare = None
            hashrate = item.get("hashrate1m") or item.get("hashrate_1m") or item.get("hashrate") or item.get("hashrate5m")
            try:
                hashrate = float(hashrate)
            except Exception:
                hashrate = 0.0
            bestshare = item.get("bestshare") or item.get("bestShare")
            try:
                bestshare = int(float(bestshare))
            except Exception:
                bestshare = None
            workers.append(
                {
                    "workername": str(item.get("workername") or item.get("worker") or path.name).strip(),
                    "hashrate_ths": hashrate / 1_000_000_000_000 if hashrate and hashrate > 1_000_000 else hashrate,
                    "hashrate_1m_ths": hashrate / 1_000_000_000_000 if hashrate and hashrate > 1_000_000 else hashrate,
                    "lastshare": lastshare,
                    "lastshare_ago_s": max(0, int(time.time()) - lastshare) if lastshare else None,
                    "bestshare_since_block": bestshare,
                }
            )
    return workers


def pool_workers_api():
    workers = parse_worker_records()
    return {
        "workers": len(workers),
        "workers_details": workers,
        "lastshare_ago_s": min((w["lastshare_ago_s"] for w in workers if w["lastshare_ago_s"] is not None), default=None),
    }


def estimate_eta_seconds(network_difficulty, hashrate_ths):
    if not network_difficulty or not hashrate_ths:
        return None
    try:
        return (float(network_difficulty) * 4294967296.0) / (float(hashrate_ths) * 1e12)
    except Exception:
        return None


def pool_summary():
    workers_payload = pool_workers_api()
    workers = workers_payload["workers_details"]
    active_workers = [
        item
        for item in workers
        if item.get("lastshare_ago_s") is not None and item["lastshare_ago_s"] <= ACTIVE_WORKER_WINDOW_S
    ]
    total_hashrate = sum(float(item.get("hashrate_ths") or 0.0) for item in active_workers)
    best = max((item.get("bestshare_since_block") or 0 for item in workers), default=0) or None
    best_worker = None
    if best is not None:
        for item in workers:
            if item.get("bestshare_since_block") == best:
                best_worker = item.get("workername")
                break
    difficulty = None
    try:
        difficulty = node_status().get("difficulty")
    except Exception:
        difficulty = None
    return {
        "workers": len(active_workers),
        "active_workers": len(active_workers),
        "hashrate_ths": total_hashrate if total_hashrate > 0 else None,
        "hashrate_window": "1m" if total_hashrate > 0 else None,
        "best_share_since_block": best,
        "best_share_since_block_worker": best_worker,
        "best_share": best,
        "network_difficulty": difficulty,
        "eta_seconds": estimate_eta_seconds(difficulty, total_hashrate if total_hashrate > 0 else None),
        "stale_error": None,
    }


def find_solved_blocks(depth: int, payout_address: str):
    if not payout_address:
        return []
    try:
        validation = rpc_call("validateaddress", [payout_address]) or {}
        script_hex = str(validation.get("scriptPubKey") or "").strip().lower()
    except Exception:
        return []
    if not script_hex:
        return []
    try:
        tip = int(rpc_call("getblockcount"))
    except Exception:
        return []
    depth = max(1, min(MAX_BLOCK_SCAN_DEPTH, depth))
    events = []
    for height in range(tip, max(-1, tip - depth), -1):
        try:
            block_hash = rpc_call("getblockhash", [height])
            block = rpc_call("getblock", [block_hash, 2])
        except Exception:
            continue
        txs = block.get("tx") if isinstance(block, dict) else None
        if not isinstance(txs, list) or not txs:
            continue
        coinbase = txs[0]
        outputs = coinbase.get("vout") if isinstance(coinbase, dict) else None
        if not isinstance(outputs, list):
            continue
        matched = any(
            isinstance(vout, dict)
            and isinstance(vout.get("scriptPubKey"), dict)
            and str(vout["scriptPubKey"].get("hex") or "").strip().lower() == script_hex
            for vout in outputs
        )
        if not matched:
            continue
        events.append(
            {
                "hash": str(block_hash),
                "height": int(block.get("height") or height),
                "confirmations": int(block.get("confirmations") or 0),
                "status": "confirmed" if int(block.get("confirmations") or 0) > 0 else "found",
                "network_difficulty": float(block.get("difficulty") or 0.0),
                "solve_worker": None,
                "luckPct": None,
                "foundAt": datetime.fromtimestamp(int(block.get("time") or 0), tz=timezone.utc).isoformat(),
                "t": int(block.get("time") or 0),
            }
        )
    return events


def blocks_state():
    ensure_dirs()
    state = read_json(BLOCKS_STATE_PATH, {"events": [], "backscan": {"enabled": False, "depth": DEFAULT_BLOCK_SCAN_DEPTH}})
    settings = current_pool_settings()
    depth = int((state.get("backscan") or {}).get("depth") or DEFAULT_BLOCK_SCAN_DEPTH)
    if settings.get("configured"):
        if not state["events"] or bool((state.get("backscan") or {}).get("enabled")):
            state["events"] = find_solved_blocks(depth, settings["payoutAddress"])
            write_json(BLOCKS_STATE_PATH, state)
    return state


def current_round_state():
    ensure_dirs()
    state = read_json(LUCK_STATE_PATH, {})
    if "startedAt" not in state:
        state["startedAt"] = int(time.time())
        write_json(LUCK_STATE_PATH, state)
    return state


def luck_payload():
    blocks = blocks_state().get("events") or []
    round_state = current_round_state()
    luck_values = [float(item["luckPct"]) for item in blocks[:5] if item.get("luckPct") is not None]
    return {
        "current": {
            "luckPct": None,
            "started": datetime.fromtimestamp(int(round_state["startedAt"]), tz=timezone.utc).isoformat(),
            "shares": None,
            "totalDiff": None,
        },
        "recent": blocks[:5],
        "summary": {
            "blocks": len(blocks[:5]),
            "averageLuckPct": (sum(luck_values) / len(luck_values)) if luck_values else None,
            "bestLuckPct": min(luck_values) if luck_values else None,
            "worstLuckPct": max(luck_values) if luck_values else None,
        },
    }


def widget_sync():
    try:
        status = node_status()
        progress = max(0.0, min(1.0, float(status["verificationprogress"])))
        return {
            "type": "text-with-progress",
            "title": "BCH sync",
            "text": f"{int(progress * 100)}%",
            "progressLabel": "In progress" if status["initialblockdownload"] else "Synchronized",
            "progress": progress,
        }
    except Exception:
        return {
            "type": "text-with-progress",
            "title": "BCH sync",
            "text": "-",
            "progressLabel": "Unavailable",
            "progress": 0,
        }


def widget_pool():
    try:
        summary = pool_summary()
        hashrate = summary.get("hashrate_ths")
        workers = summary.get("workers")
        best_share = summary.get("best_share_since_block")
        return {
            "type": "three-stats",
            "items": [
                {"title": "Hashrate", "text": str(hashrate) if hashrate is not None else "-", "subtext": "TH/s"},
                {"title": "Workers", "text": str(workers or 0)},
                {"title": "Best Share", "text": str(best_share) if best_share is not None else "-"},
            ],
        }
    except Exception:
        return {
            "type": "three-stats",
            "items": [
                {"title": "Hashrate", "text": "-", "subtext": "TH/s"},
                {"title": "Workers", "text": "0"},
                {"title": "Best Share", "text": "-"},
            ],
        }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status=HTTPStatus.OK):
        self._send(*json_response(payload, status))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        try:
            if self.path == "/api/settings":
                return self._json(current_node_settings())
            if self.path == "/api/node":
                return self._json(node_status())
            if self.path == "/api/pool/settings":
                return self._json(current_pool_settings())
            if self.path == "/api/pool":
                return self._json(pool_summary())
            if self.path == "/api/pool/workers":
                return self._json(pool_workers_api())
            if self.path == "/api/blocks":
                return self._json(blocks_state())
            if self.path == "/api/luck":
                return self._json(luck_payload())
            if self.path == "/api/widget/sync":
                return self._json(widget_sync())
            if self.path == "/api/widget/pool":
                return self._json(widget_pool())
        except Exception as exc:
            return self._json({"error": str(exc)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
        return super().do_GET()

    def do_POST(self):
        body = self._read_body()
        try:
            if self.path == "/api/settings":
                prune = int(body.get("prune") or 0)
                if prune != 0 and prune < 550:
                    return self._json({"error": "prune must be 0 or >= 550"}, status=HTTPStatus.BAD_REQUEST)
                previous = current_node_settings()
                update_node_conf(str(body.get("network") or "mainnet"), prune, int(bool(body.get("txindex"))))
                reindex_required = previous["prune"] > 0 and prune == 0
                if reindex_required:
                    request_reindex()
                return self._json({"ok": True, "restartRequired": True, "reindexRequired": reindex_required})
            if self.path == "/api/pool/settings":
                settings = update_pool_settings(body)
                return self._json({"ok": True, "restartRequired": True, "settings": settings})
            if self.path == "/api/pool/bestshare/reset":
                return self._json({"ok": True})
            if self.path == "/api/luck/reset":
                state = {"startedAt": int(time.time())}
                write_json(LUCK_STATE_PATH, state)
                return self._json({"ok": True, "resetAt": state["startedAt"]})
            if self.path == "/api/blocks/backscan":
                state = blocks_state()
                backscan = state.get("backscan") or {}
                if "enabled" in body:
                    backscan["enabled"] = bool(body.get("enabled"))
                if body.get("rescan"):
                    backscan["enabled"] = True
                    backscan["depth"] = min(MAX_BLOCK_SCAN_DEPTH, DEFAULT_BLOCK_SCAN_DEPTH * 4)
                    state["events"] = []
                state["backscan"] = backscan
                write_json(BLOCKS_STATE_PATH, state)
                return self._json({"ok": True, "backscan": backscan})
        except ValueError as exc:
            return self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self._json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


if __name__ == "__main__":
    ensure_dirs()
    ThreadingHTTPServer(("0.0.0.0", 3000), Handler).serve_forever()
