# Flowsink Browser Monitor — Windows Setup

Chrome extension thu thập tab activity (domain, title, tab id) và đẩy về
backend Activity Engine qua REST. Backend chuẩn hóa telemetry thành
`browser_navigation` events và đưa vào pipeline (Policy → State →
Escalation → Action giống như mọi nguồn khác).

## Kiến trúc

```
[Chrome Extension] --POST /api/browser/telemetry--> [FastAPI Backend]
   background.js   batched events                    BrowserStateStore
                                                     BrowserTelemetryPayload
                                                              |
                                                              v
[CLI monitor] <--GET /api/browser/active-- [ExtensionBrowserMonitor]
   --backend extension                                  |
                                                         v
                                              EventEngine -> PolicyEngine -> ...
```

## Yêu cầu

- Windows 10/11 (bản deploy chính)
- Chrome hoặc Microsoft Edge (Chromium)
- Python 3.10+ (`setup_windows.bat` chuẩn bị môi trường)
- Backend server chạy ở `http://127.0.0.1:8000`

## Cài đặt — 1 lần

```bat
:: Bước 0: chuẩn bị môi trường (nếu chưa có .venv)
setup_windows.bat

:: Bước 1: chạy installer (ghi device_id thật, tự mở chrome://extensions/)
install_browser_extension.bat

:: Hoặc tùy chỉnh backend URL:
python install_browser_extension.py --api-url http://127.0.0.1:8000
```

### Bước thủ công duy nhất trong Chrome

1. Trong `chrome://extensions/` bật **Developer mode** (góc phải trên).
2. Bấm **Load unpacked**.
3. Chọn thư mục `browser-extension/` trong project.
4. Extension hiện tên **Flowsink Browser Monitor** và bắt đầu gửi telemetry.

> Extension dùng `background.service_worker` (Manifest V3) — không cần
> `host_permissions`, chỉ theo dõi tab availability + active tab title/url
> khi có sự kiện, không đọc nội dung trang.

## Chạy hệ thống

Mở 3 terminal (hoặc dùng `run_windows.bat`).

> **Multi-worker:** Trạng thái monitoring (events, violations, screenshots)
> được lưu **in-memory, process-local**. Chỉ chạy **một** backend worker:
> `--workers 1` (mặc định uvicorn). Không dùng multi-worker.

```bat
:: Terminal 1 — Backend
run_windows.bat server

:: Terminal 2 — CLI monitor (browser source = extension bridge)
python -m activity_engine.cli.main monitor --backend extension --poll 3

:: Terminal 3 (tuỳ chọn) — dashboard web
npm run dev
```

## Kiểm tra nhanh

```bat
:: Doctor — xác nhận browser_extension bridge sẵn sàng
python -m activity_engine.cli.main doctor

:: Gửi telemetry mẫu trực tiếp
curl -X POST http://127.0.0.1:8000/api/browser/telemetry ^
  -H "Content-Type: application/json" ^
  -d "{\"events\":[{\"kind\":\"browser_navigation\",\"url\":\"https://youtube.com/watch?v=abc\",\"tab_id\":\"42\",\"device_id\":\"MY-PC\",\"title\":\"YouTube\"}]}"

:: Query active tab hiện tại
curl http://127.0.0.1:8000/api/browser/active

:: Session status
curl http://127.0.0.1:8000/api/session/status
```

Kết quả mong đợi:

```json
// POST /api/browser/telemetry
{ "status": "ok", "accepted": 1, "dropped": 0 }

// GET /api/browser/active
{ "tabs": [{ "domain": "youtube.com", "url": "https://youtube.com/",
             "tab_id": "42", "title": "YouTube", "device_id": "MY-PC" }],
  "count": 1 }

// GET /api/session/status
{ "session_id": "a1b2...", "active": true }
```

## Gỡ cài đặt

```bat
uninstall_browser_extension.bat
```

Script mở `chrome://extensions/` để bạn bấm **Remove**; đồng thời reset
`config.json` về mặc định (xoá device identity). Thư mục extension được
giữ lại cho lần cài sau.

## Cấu hình extension

`browser-extension/config.json`:

| Key            | Mặc định | Ý nghĩa                           |
|----------------|---------|-----------------------------------|
| `api_base_url` | `http://127.0.0.1:8000` | Backend gốc           |
| `device_id`    | hostname | Định danh máy (installer tự ghi)  |
| `max_queue`    | `100`   | Tối đa event chờ gửi trong bộ nhớ |
| `retry_base_ms`| `1000`  | Backoff gốc khi backend offline   |
| `retry_max_ms` | `60000` | Backoff tối đa                    |

Extension lưu queue trong `chrome.storage.session` — nếu Chrome đóng đột
ngột, telemetry chưa gửi sẽ mất (chấp nhận được vì monitor poll lại
active tab mới).

## Kiến trúc code

| Thành phần | File | Vai trò |
|-----------|------|---------|
| Extension (MV3) | `browser-extension/manifest.json` | Khai báo service worker + permissions |
| Extension logic | `browser-extension/background.js` | Bắt tab events, batching, retry gửi backend |
| Extension config | `browser-extension/config.json` | Backend URL, device id, queue tuning |
| Server bridge | `src/activity_engine/server.py` | `POST /api/browser/telemetry`, `GET /api/browser/active` |
| Store | `src/activity_engine/services/browser_state.py` | Active tabs theo device |
| Normalizer | `src/activity_engine/services/browser_events.py` | Extension payload → canonical event |
| Monitor adapter | `src/activity_engine/adapters/extension/browser_monitor.py` | BrowserMonitor port (store / HTTP poll) |
| CLI | `src/activity_engine/cli/main.py` | `--backend extension`, `--api-url` |

## Troubleshooting

| Triệu chứng | Nguyên nhân | Xử lý |
|-------------|-------------|-------|
| Extension hiện lỗi "API base URL unreachable" | Backend chưa chạy | Khởi động server, extension tự retry |
| CLI không in browser events | Chrome chưa load extension / tab chưa đổi | Bật Developer mode + Load unpacked lại |
| `accepted: 0, dropped: N` | Payload sai format hoặc domain chrome:// | Kiểm tra console extension, bỏ qua internal pages |
| CORS error khi POST | Backend cũ hơn phiên bản có CORS | Khởi động lại server mới nhất |