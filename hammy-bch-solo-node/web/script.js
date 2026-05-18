const presetMap = {
  cpu: { mindiff: 1, startdiff: 1, maxdiff: 64 },
  single: { mindiff: 1, startdiff: 16, maxdiff: 0 },
  rack: { mindiff: 1024, startdiff: 8192, maxdiff: 0 },
  farm: { mindiff: 8192, startdiff: 65536, maxdiff: 0 },
};

function setActiveTab(tabName) {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-pane").forEach((pane) => {
    pane.classList.toggle("is-active", pane.id === `tab-${tabName}`);
  });
  window.__activeTab = tabName;
}

async function fetchJson(url, options) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data && data.error ? data.error : `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return data;
}

function showToast(message) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 3200);
}

function formatPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return `${(n * 100).toFixed(2)}%`;
}

function formatThs(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return "-";
  if (n >= 1000) return `${(n / 1000).toFixed(2)} PH/s`;
  return `${n.toFixed(n >= 100 ? 0 : 2)} TH/s`;
}

function formatRelativeSeconds(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) return "-";
  if (n < 60) return `${Math.round(n)}s ago`;
  if (n < 3600) return `${Math.round(n / 60)}m ago`;
  if (n < 86400) return `${Math.round(n / 3600)}h ago`;
  return `${Math.round(n / 86400)}d ago`;
}

function formatNumber(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return n.toLocaleString();
}

function formatLuck(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return `${n.toFixed(1)}%`;
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderOverview(node, pool, blocks) {
  setText("metric-sync", formatPercent(node.verificationprogress));
  setText("metric-sync-meta", `${formatNumber(node.blocks)} / ${formatNumber(node.headers)} blocks`);
  setText("metric-peers", formatNumber(node.connections));
  setText("metric-chain", `${node.chain || "-"}${node.pruned ? " - pruned" : ""}`);
  setText("metric-hashrate", formatThs(pool.hashrate_ths));
  setText("metric-hashrate-meta", pool.hashrate_window ? `Window ${pool.hashrate_window}` : "Pool hashrate");
  setText("metric-workers", formatNumber(pool.workers));
  setText("metric-workers-meta", `${formatNumber(pool.active_workers ?? pool.workers)} active workers`);
  setText("metric-bestshare", pool.best_share_since_block != null ? formatNumber(pool.best_share_since_block) : "-");
  setText("metric-bestshare-meta", pool.best_share_since_block_worker ? `Lead worker: ${pool.best_share_since_block_worker}` : "Since latest block");

  const latestBlock = Array.isArray(blocks.events) && blocks.events.length ? blocks.events[0] : null;
  setText("metric-lastblock", latestBlock && latestBlock.height ? `#${latestBlock.height}` : "None");
  setText(
    "metric-lastblock-meta",
    latestBlock
      ? `${latestBlock.solve_worker || "unknown worker"} - ${latestBlock.status || "found"}`
      : "No solved block recorded yet"
  );
}

function renderNodeSettings(settings, node) {
  document.getElementById("network").value = settings.network || "mainnet";
  document.getElementById("prune").value = Number(settings.prune ?? 0);
  document.getElementById("txindex").checked = Boolean(settings.txindex);

  const parts = [];
  if (node.template_ready === true) parts.push("Block template ready");
  if (node.initialblockdownload) parts.push("Node is still syncing");
  if (node.reindexRequired) parts.push("Chainstate reindex required");
  if (node.reindexRequested) parts.push("Chainstate reindex already queued");
  if (node.warnings) parts.push(node.warnings);
  document.getElementById("node-note").textContent = parts.length ? parts.join(" | ") : "Node looks healthy.";
}

function renderPoolSettings(settings, pool) {
  document.getElementById("payout-address").value = settings.payoutAddress || "";
  document.getElementById("mindiff").value = Number(settings.mindiff ?? 1);
  document.getElementById("startdiff").value = Number(settings.startdiff ?? 16);
  document.getElementById("maxdiff").value = Number(settings.maxdiff ?? 0);

  const configured = Boolean(settings.configured);
  setText("stratum-endpoint", "stratum+tcp://<your-host-ip>:4633");
  setText("stratum-endpoint-inline", "stratum+tcp://<your-host-ip>:4633");
  setText(
    "stratum-status",
    configured
      ? `${formatNumber(pool.workers)} worker(s) visible. Username can be workername or address.workername.`
      : "Set a payout address, save settings, then restart the app before miners connect."
  );
  setText("next-step-title", configured ? "Restart to apply pool changes" : "Set payout address");
  setText(
    "next-step-copy",
    configured
      ? "ckpool reads its config on startup. Restart the app after payout or difficulty changes."
      : "Save a BCH payout address and vardiff range first, then restart the app."
  );

  const notes = [];
  if (settings.warning) notes.push(settings.warning);
  if (settings.validationWarning) notes.push(settings.validationWarning);
  if (settings.validated === false) notes.push("Address validation did not pass.");
  if (pool.stale_error) notes.push(`Pool cache warning: ${pool.stale_error}`);
  document.getElementById("pool-note").textContent = notes.length ? notes.join(" | ") : "Worker status loaded.";
}

function renderLuck(luck) {
  const current = luck.current || {};
  const summary = luck.summary || {};
  setText("luck-effort", formatLuck(current.luckPct));
  setText("luck-since", current.started ? `Tracked since ${current.started}` : "Tracking round luck");
  setText("luck-shares", formatNumber(current.shares));
  setText("luck-total-diff", current.totalDiff != null ? `Total diff ${formatNumber(current.totalDiff)}` : "Round work not available");
  setText("luck-average", formatLuck(summary.averageLuckPct));
  setText(
    "luck-range",
    summary.bestLuckPct != null && summary.worstLuckPct != null
      ? `Best ${formatLuck(summary.bestLuckPct)} / Worst ${formatLuck(summary.worstLuckPct)}`
      : "No solved block sample yet"
  );
}

function renderWorkers(workers) {
  const body = document.getElementById("workers-body");
  const rows = Array.isArray(workers.workers_details) ? workers.workers_details : [];
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="4" class="empty">No worker stats yet</td></tr>';
    return;
  }

  body.innerHTML = rows
    .map((worker) => {
      const name = worker.workername || worker.worker || worker.workerName || "unnamed";
      const hashrate = worker.hashrate_1m_ths ?? worker.hashrate_ths;
      const lastShareAge = worker.lastshare_ago_s ?? worker.lastshareAgoS;
      const best = worker.bestshare_since_block ?? worker.bestShareSinceBlock;
      return `
        <tr>
          <td>${escapeHtml(name)}</td>
          <td>${formatThs(hashrate)}</td>
          <td>${formatRelativeSeconds(lastShareAge)}</td>
          <td>${best != null ? formatNumber(best) : "-"}</td>
        </tr>
      `;
    })
    .join("");
}

function renderBlocks(blocks) {
  const events = Array.isArray(blocks.events) ? blocks.events : [];
  const backscan = blocks.backscan || {};
  document.getElementById("blocks-summary").textContent = backscan.complete
    ? "History scan complete."
    : backscan.enabled
      ? `History scan running from height ${formatNumber(backscan.startHeight)}.`
      : "History scan is off. Turn it on if you want to backfill older solved blocks.";

  const list = document.getElementById("block-list");
  if (!events.length) {
    list.innerHTML = '<li class="empty">No solved blocks recorded yet.</li>';
    return;
  }

  list.innerHTML = events
    .map((event) => {
      const title = event.height ? `Block ${event.height}` : event.hash || "Solved block";
      const subtitle = [
        event.solve_worker || "unknown worker",
        event.foundAt || event.last_block_found || "time unavailable",
        event.luckPct != null ? `luck ${formatLuck(event.luckPct)}` : null,
      ]
        .filter(Boolean)
        .join(" - ");
      return `
        <li class="block-item">
          <div>
            <span class="block-item__title">${escapeHtml(title)}</span>
            <div>${escapeHtml(subtitle)}</div>
          </div>
          <span class="block-item__pill">${escapeHtml(event.status || "found")}</span>
        </li>
      `;
    })
    .join("");
}

async function refreshAll() {
  const [
    nodeSettingsResult,
    nodeResult,
    poolSettingsResult,
    poolResult,
    workersResult,
    blocksResult,
    luckResult,
  ] = await Promise.allSettled([
    fetchJson("/api/settings"),
    fetchJson("/api/node"),
    fetchJson("/api/pool/settings"),
    fetchJson("/api/pool"),
    fetchJson("/api/pool/workers"),
    fetchJson("/api/blocks"),
    fetchJson("/api/luck"),
  ]);

  const nodeSettings = nodeSettingsResult.status === "fulfilled" ? nodeSettingsResult.value : { network: "mainnet", prune: 0, txindex: 0 };
  const node = nodeResult.status === "fulfilled" ? nodeResult.value : {};
  const poolSettings = poolSettingsResult.status === "fulfilled" ? poolSettingsResult.value : {};
  const pool = poolResult.status === "fulfilled" ? poolResult.value : {};
  const workers = workersResult.status === "fulfilled" ? workersResult.value : { workers_details: [] };
  const blocks = blocksResult.status === "fulfilled" ? blocksResult.value : { events: [], backscan: {} };
  const luck = luckResult.status === "fulfilled" ? luckResult.value : { current: {}, summary: {}, recent: [] };

  renderOverview(node, pool, blocks);
  renderNodeSettings(nodeSettings, node);
  renderPoolSettings(poolSettings, pool);
  renderLuck(luck);
  renderWorkers(workers);
  renderBlocks(blocks);

  window.__backscanEnabled = Boolean(blocks.backscan && blocks.backscan.enabled);

  const errors = [
    nodeSettingsResult,
    nodeResult,
    poolSettingsResult,
    poolResult,
    workersResult,
    blocksResult,
    luckResult,
  ]
    .filter((result) => result.status === "rejected")
    .map((result) => result.reason && result.reason.message ? result.reason.message : "Request failed");

  if (errors.length) {
    showToast(`Partial data unavailable: ${errors[0]}`);
  }
}

async function postJson(url, body) {
  return fetchJson(url, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

function wireActions() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.tab));
  });

  document.getElementById("refresh-button").addEventListener("click", async () => {
    await refreshAll();
    showToast("Dashboard refreshed.");
  });

  document.getElementById("node-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const prune = Number(document.getElementById("prune").value);
    if (prune !== 0 && prune < 550) {
      showToast("Prune must be 0 or at least 550 MiB.");
      return;
    }
    const result = await postJson("/api/settings", {
      network: document.getElementById("network").value,
      prune,
      txindex: document.getElementById("txindex").checked,
    });
    await refreshAll();
    showToast(result.reindexRequired ? "Node settings saved. Restart required and reindex queued." : "Node settings saved. Restart required.");
  });

  document.getElementById("pool-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const mindiff = Number(document.getElementById("mindiff").value);
    const startdiff = Number(document.getElementById("startdiff").value);
    const maxdiff = Number(document.getElementById("maxdiff").value);
    if (mindiff < 1 || startdiff < 1 || maxdiff < 0) {
      showToast("Difficulty values are out of range.");
      return;
    }
    await postJson("/api/pool/settings", {
      payoutAddress: document.getElementById("payout-address").value.trim(),
      mindiff,
      startdiff,
      maxdiff,
    });
    await refreshAll();
    showToast("Pool settings saved. Restart required.");
  });

  document.getElementById("reset-bestshare").addEventListener("click", async () => {
    await postJson("/api/pool/bestshare/reset", {});
    await refreshAll();
    showToast("Best share tracker reset.");
  });

  document.getElementById("reset-luck").addEventListener("click", async () => {
    await postJson("/api/luck/reset", {});
    await refreshAll();
    showToast("Luck round reset.");
  });

  document.getElementById("toggle-backscan").addEventListener("click", async () => {
    await postJson("/api/blocks/backscan", { enabled: !window.__backscanEnabled });
    await refreshAll();
    showToast(window.__backscanEnabled ? "History scan enabled." : "History scan disabled.");
  });

  document.getElementById("rescan-blocks").addEventListener("click", async () => {
    await postJson("/api/blocks/backscan", { rescan: true });
    await refreshAll();
    showToast("History rescan requested.");
  });

  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = presetMap[button.dataset.preset];
      if (!preset) return;
      document.getElementById("mindiff").value = preset.mindiff;
      document.getElementById("startdiff").value = preset.startdiff;
      document.getElementById("maxdiff").value = preset.maxdiff;
    });
  });
}

async function bootstrap() {
  wireActions();
  setActiveTab("home");
  await refreshAll();
  window.setInterval(() => {
    refreshAll().catch((error) => {
      showToast(error.message || "Background refresh failed.");
    });
  }, 15000);
}

bootstrap();
