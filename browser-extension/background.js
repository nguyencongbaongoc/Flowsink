/**
 * Flowsink Browser Monitor — background service worker (Manifest V3).
 *
 * Gửi telemetry tab ẩn danh tới Flowsink Activity Engine cục bộ.
 *
 * PRIVACY BY DESIGN:
 *  - Không thu thập: mật khẩu, keyboard input, form content, page content,
 *    cookies, credentials, tokens.
 *  - URL query parameters chứa token/credential bị sanitize trước khi gửi.
 *  - Chỉ gửi: tab_id, domain, URL (sạch), title (sạch), event type, timestamp.
 *
 * OFFLINE/RETRY:
 *  - Queue tối đa 100 sự kiện (FIFO). Không vô hạn.
 *  - Retry với exponential backoff (1s, 2s, 4s, ... tối đa 60s).
 *  - Dedupe: trạng thái tab đã gửi không gửi lại.
 */

"use strict";

// === CONFIG =================================================================
const DEFAULT_CONFIG = {
  api_base_url: "http://127.0.0.1:8000",
  device_id: "unknown-device",
  max_queue: 100,
  retry_base_ms: 1000,
  retry_max_ms: 60000,
};

// === STATE ==================================================================
let config = { ...DEFAULT_CONFIG };
let queue = [];
let sending = false;
let retryDelayMs = config.retry_base_ms;
let lastSeen = new Map(); // key -> timestamp (dedupe)
const DEDUPE_WINDOW_MS = 1500;

// === INIT ===================================================================
chrome.runtime.onInstalled.addListener(() => {
  ensureConfig();
});

chrome.runtime.onStartup.addListener(() => {
  ensureConfig();
});

async function ensureConfig() {
  try {
    const res = await fetch(chrome.runtime.getURL("config.json"));
    if (res.ok) {
      const raw = await res.json();
      config = { ...DEFAULT_CONFIG, ...raw };
      retryDelayMs = config.retry_base_ms;
      console.log("[Flowsink] config loaded", {
        api_base_url: config.api_base_url,
        device_id: config.device_id,
      });
    }
  } catch (err) {
    console.warn("[Flowsink] config load failed, using defaults", err);
  }
}

// === SANITIZE ================================================================
function sanitizeUrl(rawUrl) {
  if (typeof rawUrl !== "string" || rawUrl.length === 0) return null;
  try {
    const u = new URL(rawUrl);
    const clean = new URL(u.origin + u.pathname);
    // Privacy by design: mọi query parameter đều bị loại bỏ.
    // Không log URL query có thể chứa token/credential.
    return clean.toString();
  } catch {
    return null;
  }
}

function sanitizeTitle(title) {
  if (typeof title !== "string") return null;
  const trimmed = title.trim().slice(0, 300);
  return trimmed.length > 0 ? trimmed : null;
}

function normalizeDomain(url) {
  if (typeof url !== "string") return null;
  try {
    return new URL(url).hostname.toLowerCase().replace(/^www\./, "");
  } catch {
    return null;
  }
}

// === EVENT BUILDING ===========================================================
function buildPayload(eventType, tab) {
  const url = tab && tab.url ? tab.url : null;
  if (!url || !/^https?:/i.test(url)) return null; // không gửi chrome://, file://, edge://, etc.

  const cleanUrl = sanitizeUrl(url);
  if (!cleanUrl) return null;

  const domain = normalizeDomain(cleanUrl);
  if (!domain) return null;

  return {
    kind: eventType,
    source: "extension",
    timestamp: new Date().toISOString(),
    device_id: config.device_id,
    tab_id: String(tab.id ?? ""),
    domain,
    url: cleanUrl,
    title: sanitizeTitle(tab.title),
  };
}

function dedupeKey(payload) {
  // Cùng event type + tab + domain trong cửa sổ dedupe => bỏ qua.
  return [payload.kind, payload.tab_id, payload.domain].join(":");
}

function shouldDedupe(payload) {
  const key = dedupeKey(payload);
  const now = Date.now();
  const last = lastSeen.get(key);
  if (last && now - last < DEDUPE_WINDOW_MS) {
    return true;
  }
  lastSeen.set(key, now);
  if (lastSeen.size > 512) {
    // Chỉ giữ 512 key; xóa key cũ nhất theo vòng lặp đơn giản.
    const oldest = lastSeen.keys().next().value;
    if (oldest !== undefined) lastSeen.delete(oldest);
  }
  return false;
}

// === QUEUE + SEND =============================================================
function enqueue(payload) {
  if (queue.length >= config.max_queue) {
    // FIFO: bỏ sự kiện cũ nhất, không tạo vòng lặp vô hạn.
    queue.shift();
    console.warn("[Flowsink] queue full — dropped oldest event");
  }
  queue.push(payload);
  scheduleFlush();
}

function scheduleFlush() {
  if (!sending) {
    setTimeout(flush, 250);
  }
}

async function flush() {
  if (sending || queue.length === 0) return;
  sending = true;

  const batch = queue.splice(0, 20); // gửi theo batch nhỏ
  try {
    const res = await fetch(`${config.api_base_url}/api/browser/telemetry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: batch }),
    });

    if (res.ok) {
      retryDelayMs = config.retry_base_ms;
    } else {
      // Backend trả lỗi HTTP — không retry mãi; đưa batch trở lại queue.
      queue = batch.concat(queue);
      if (queue.length > config.max_queue) {
        queue = queue.slice(0, config.max_queue);
      }
      scheduleRetry();
    }
  } catch (err) {
    // Backend offline — retry với backoff.
    console.warn("[Flowsink] send failed", err.message);
    queue = batch.concat(queue);
    if (queue.length > config.max_queue) {
      queue = queue.slice(0, config.max_queue);
    }
    scheduleRetry();
  } finally {
    sending = false;
    if (queue.length > 0 && navigator.onLine !== false) {
      // Nếu còn sự kiện và online, tiếp tục gửi với backoff hiện tại.
      setTimeout(flush, retryDelayMs);
    }
  }
}

function scheduleRetry() {
  // Exponential backoff, tối đa 60s.
  retryDelayMs = Math.min(retryDelayMs * 2, config.retry_max_ms);
  // Backoff được áp dụng trong finally của flush.
}

// === DẤU HIỆU ONLINE/OFFLINE ==================================================
self.addEventListener("online", () => {
  retryDelayMs = config.retry_base_ms;
  if (queue.length > 0 && !sending) {
    setTimeout(flush, 250);
  }
});

// === TAB EVENT LISTENERS ======================================================
function onTabUpdated(tabId, changeInfo, tab) {
  // URL đổi, title đổi hoặc tab bắt đầu load -> gửi TAB_UPDATED / WEB_NAVIGATION.
  if (!changeInfo || (!changeInfo.url && !changeInfo.title && !changeInfo.status)) return;
  const payload = buildPayload("browser_navigation", tab);
  if (payload && !shouldDedupe(payload)) enqueue(payload);
}

function onTabActivated(activeInfo) {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (chrome.runtime.lastError || !tab) return;
    const payload = buildPayload("browser_tab_focus", tab);
    if (payload && !shouldDedupe(payload)) enqueue(payload);
  });
}

function onTabCreated(tab) {
  // Tab mới với URL (ví dụ homepage) — nếu chưa load xong, tab updated sẽ gửi sau.
  const payload = buildPayload("browser_navigation", tab);
  if (payload && !shouldDedupe(payload)) enqueue(payload);
}

function onTabRemoved(tabId, removeInfo) {
  enqueue({
    kind: "browser_tab_close",
    source: "extension",
    timestamp: new Date().toISOString(),
    device_id: config.device_id,
    tab_id: String(tabId),
    domain: null,
    url: null,
    title: null,
  });
}

// === REGISTER LISTENERS =======================================================
chrome.tabs.onUpdated.addListener(onTabUpdated);
chrome.tabs.onActivated.addListener(onTabActivated);
chrome.tabs.onCreated.addListener(onTabCreated);
chrome.tabs.onRemoved.addListener(onTabRemoved);

// === MESSAGES ==================================================================
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg && msg.type === "ping") {
    sendResponse({ ok: true, queued: queue.length });
  }
  return true; // async response
});