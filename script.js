/* =====================================================================
   STATE
===================================================================== */
let currentProvider = 'gemini';
let analysisResult = null;
let focusActive = false;
let focusMode = 'work';   // 'work' | 'rest'
let focusTimeLeft = 45 * 60;
let focusInterval = null;

const PRESETS = {
  groq: { baseURL: 'https://api.groq.com/openai/v1', model: 'llama-3.3-70b-versatile', keyHint: 'Groq API Key (gsk_...)', docs: 'https://console.groq.com/keys' },
  ollama: { baseURL: 'http://localhost:11434/v1', model: 'llama3.2', keyHint: 'Nhập "ollama" hoặc để trống', docs: null },
  openrouter: { baseURL: 'https://openrouter.ai/api/v1', model: 'meta-llama/llama-3.1-8b-instruct:free', keyHint: 'OpenRouter Key (sk-or-...)', docs: 'https://openrouter.ai/keys' },
  together: { baseURL: 'https://api.together.xyz/v1', model: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo', keyHint: 'Together AI Key', docs: 'https://api.together.ai/' },
  custom: { baseURL: '', model: 'gpt-3.5-turbo', keyHint: 'API Key', docs: null },
};

/* =====================================================================
   PROVIDER PANEL
===================================================================== */
function toggleProvider() {
  const el = document.getElementById('provider-overlay');
  const btn = document.getElementById('provider-btn');
  const showing = el.classList.contains('show');
  el.classList.toggle('show', !showing);
  btn.classList.toggle('open', !showing);
}

function closeProvider(e) {
  if (!e || e.target === document.getElementById('provider-overlay')) {
    document.getElementById('provider-overlay').classList.remove('show');
    document.getElementById('provider-btn').classList.remove('open');
  }
}

function switchProvider(p) {
  currentProvider = p;
  document.getElementById('config-gemini').style.display = p === 'gemini' ? '' : 'none';
  document.getElementById('config-oai').style.display = p === 'openai' ? '' : 'none';
  document.getElementById('ptab-gemini').className = 'ptab' + (p === 'gemini' ? ' active' : '');
  document.getElementById('ptab-oai').className = 'ptab' + (p === 'openai' ? ' active' : '');
  document.getElementById('provider-icon').textContent = p === 'gemini' ? '✨' : '🔌';
  document.getElementById('provider-label').textContent = p === 'gemini' ? 'Google Gemini' : 'OpenAI Compatible';
  document.getElementById('provider-btn').style.borderColor = p === 'gemini' ? 'rgba(66,133,244,.5)' : 'rgba(16,185,129,.5)';
  document.getElementById('provider-btn').style.color = p === 'gemini' ? '#4285f4' : '#10b981';
}

function applyPreset() {
  const id = document.getElementById('oai-preset').value;
  const p = PRESETS[id];
  if (!p) return;
  document.getElementById('oai-base-url').value = p.baseURL;
  document.getElementById('oai-model').value = p.model;
  document.getElementById('oai-key').placeholder = p.keyHint;
  const docsEl = document.getElementById('oai-docs-link');
  docsEl.innerHTML = p.docs
    ? `<a class="field-link" href="${p.docs}" target="_blank">Lấy API Key tại ${id.charAt(0).toUpperCase() + id.slice(1)} →</a>`
    : '';
}

/* =====================================================================
   TAB SWITCHER
===================================================================== */
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.getElementById('content-' + name).classList.add('active');
}

/* =====================================================================
   PROMPT BUILDER
===================================================================== */
function buildPrompt(d) {
  return `Bạn là một chuyên gia y tế và tối ưu hóa hiệu suất học tập cho học sinh/sinh viên.
Hãy phân tích lịch sinh hoạt dưới đây, chỉ ra các nguy cơ sức khỏe tiềm ẩn (suy thận, đột quỵ, cận thị, đau dạ dày...) và đề xuất lịch trình mới khỏe mạnh hơn.
Ở các khung giờ học tập, chia thành các phiên "Focus Mode" 45 phút, chèn xen kẽ 5 phút giải lao với các hoạt động bảo vệ mắt và cơ thể.

Dữ liệu sinh hoạt:
- Giờ đi ngủ: ${d.sleepTime}
- Giờ thức dậy: ${d.wakeTime}
- Lượng nước uống: ${d.waterIntake} lít/ngày
- Số bữa ăn: ${d.meals} bữa/ngày
- Giờ tắm: ${d.showerTime}
- Thời gian nhìn màn hình: ${d.screenTime} giờ/ngày

Trả về BẮT BUỘC định dạng JSON hợp lệ, không có text nào bên ngoài JSON:
{
  "score": 45,
  "risks": [{ "name": "Tên nguy cơ", "probability": "Cao/Trung bình/Thấp", "reason": "Giải thích ngắn" }],
  "advice": "Lời khuyên tổng quan",
  "schedule": [{ "id": 1, "time": "06:00", "activity": "Nội dung", "type": "health" }]
}
Chú ý: "type" chỉ gồm: health, work, meal, relax.`;
}

/* =====================================================================
   API KEY LOADER (From .env.local or localStorage)
===================================================================== */
async function getGeminiKey() {
  try {
    const res = await fetch('.env.local');
    if (res.ok) {
      const text = await res.text();
      const match = text.match(/(?:VITE_GEMINI_API_KEY|GEMINI_API_KEY)\s*=\s*([^\r\n#]+)/);
      if (match && match[1].trim()) return match[1].trim().replace(/^["']|["']$/g, '');
    }
  } catch (e) {}
  const inputKey = document.getElementById('gemini-key')?.value?.trim();
  if (inputKey) return inputKey;
  return localStorage.getItem('gemini_api_key') || '';
}

/* =====================================================================
   CALL GEMINI (direct REST)
===================================================================== */
async function callGemini(prompt) {
  const key = await getGeminiKey();
  if (!key) throw new Error('Không tìm thấy API Key. Vui lòng thêm key vào file .env.local (GEMINI_API_KEY=...)');
  const model = "gemma-4-31b-it";

  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }]
      })
    }
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401 || res.status === 403)
      throw new Error('Gemini API Key không hợp lệ hoặc hết hạn.');
    throw new Error(err?.error?.message || `HTTP ${res.status}`);
  }

  const data = await res.json();
  const parts = data?.candidates?.[0]?.content?.parts || [];
  // Lọc bỏ part tư duy (thought: true), lấy part chứa JSON
  const answerPart = parts.find(p => !p.thought && p.text) || parts[parts.length - 1] || {};
  const text = answerPart.text || '';
  const clean = text.replace(/```json/gi, '').replace(/```/gi, '').trim();
  const match = clean.match(/\{[\s\S]*\}/);
  if (!match) throw new Error('AI không trả về JSON hợp lệ. Hãy thử lại.');
  return JSON.parse(match[0]);
}

/* =====================================================================
   CALL OPENAI-COMPATIBLE (direct REST)
===================================================================== */
async function callOpenAI(prompt) {
  const baseURL = document.getElementById('oai-base-url').value.trim();
  const model = document.getElementById('oai-model').value.trim() || 'gpt-3.5-turbo';
  const key = document.getElementById('oai-key').value.trim() || 'ollama';

  if (!baseURL) throw new Error('Vui lòng nhập Base URL của provider!');

  const res = await fetch(`${baseURL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${key}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: 'Bạn là chuyên gia y tế. Luôn trả về JSON hợp lệ, không thêm text nào bên ngoài JSON.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.4,
      max_tokens: 3000,
    })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401) throw new Error('API Key không hợp lệ. Kiểm tra lại key của provider.');
    if (res.status === 404) throw new Error(`Model "${model}" không tồn tại. Kiểm tra lại tên model.`);
    throw new Error(err?.error?.message || `HTTP ${res.status}`);
  }

  const data = await res.json();
  const text = data?.choices?.[0]?.message?.content || '';
  const clean = text.replace(/```json/gi, '').replace(/```/gi, '').trim();
  const match = clean.match(/\{[\s\S]*\}/);
  if (!match) throw new Error('AI không trả về JSON hợp lệ. Hãy thử lại hoặc đổi model.');
  return JSON.parse(match[0]);
}

/* =====================================================================
   SUBMIT SURVEY
===================================================================== */
async function handleSubmit(e) {
  e.preventDefault();

  const data = {
    sleepTime: document.getElementById('sleepTime').value,
    wakeTime: document.getElementById('wakeTime').value,
    waterIntake: document.getElementById('waterIntake').value,
    meals: document.getElementById('meals').value,
    showerTime: document.getElementById('showerTime').value,
    screenTime: document.getElementById('screenTime').value,
  };

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;margin:0"></div> Đang phân tích...';

  renderDashboardLoading();
  switchTab('dashboard');

  try {
    const prompt = buildPrompt(data);
    const result = currentProvider === 'gemini' ? await callGemini(prompt) : await callOpenAI(prompt);
    analysisResult = result;
    renderDashboard(result);
    renderSchedule(result.schedule || []);
  } catch (err) {
    renderDashboardError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '📤 Phân tích Lịch trình';
  }
}

/* =====================================================================
   RENDER DASHBOARD
===================================================================== */
function renderDashboardLoading() {
  document.getElementById('dashboard-content').innerHTML = `
    <div class="empty-state">
      <div class="spinner"></div>
      <h3>AI đang phân tích dữ liệu...</h3>
      <p>Quá trình này có thể mất vài giây. Vui lòng đợi.</p>
    </div>`;
}

function renderDashboardError(msg) {
  document.getElementById('dashboard-content').innerHTML = `
    <div class="empty-state">
      <div style="font-size:2.5rem;margin-bottom:1rem">⚠️</div>
      <h3 class="text-danger">Đã xảy ra lỗi</h3>
      <p>${msg}</p>
    </div>`;
}

function riskColor(p) {
  if (p === 'Cao') return 'text-danger';
  if (p === 'Trung bình') return 'text-warning';
  return 'text-success';
}

function renderDashboard(r) {
  const scoreColor = r.score < 50 ? 'text-danger' : r.score < 75 ? 'text-warning' : 'text-success';
  const risksHTML = (r.risks || []).map(risk => `
    <div class="risk-card">
      <div class="flex justify-between items-center mb-2" style="flex-wrap:wrap;gap:.5rem">
        <strong style="font-size:1.05rem">${risk.name}</strong>
        <span class="risk-tag ${riskColor(risk.probability)}">Nguy cơ: ${risk.probability}</span>
      </div>
      <p style="color:var(--muted);font-size:.9rem;margin:0">Nguyên nhân: ${risk.reason}</p>
    </div>`).join('');

  document.getElementById('dashboard-content').innerHTML = `
    <div class="flex justify-between items-center mb-6" style="flex-wrap:wrap;gap:1rem">
      <div class="section-header text-primary" style="margin:0">💓 Báo cáo Sức khỏe AI</div>
      <span class="score-badge glass">
        Điểm sức khỏe: <span class="${scoreColor}" style="font-size:1.3rem">${r.score}/100</span>
      </span>
    </div>
    <div class="glass mb-6" style="background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.25)">
      <div class="section-header text-danger">⚠️ Các Nguy Cơ Tiềm Ẩn</div>
      <div class="risk-grid">${risksHTML}</div>
    </div>
    <div class="advice-box">
      <div class="section-header text-success" style="margin-bottom:.75rem">🛡️ Lời khuyên từ Chuyên gia AI</div>
      ${r.advice}
    </div>`;
}

/* =====================================================================
   RENDER SCHEDULE
===================================================================== */
const TYPE_META = {
  health: { color: 'var(--success)', emoji: '💚' },
  work: { color: 'var(--primary)', emoji: '📘' },
  meal: { color: 'var(--warning)', emoji: '🍱' },
  relax: { color: '#8b5cf6', emoji: '🟣' },
};

function renderSchedule(items) {
  if (!items || items.length === 0) {
    document.getElementById('schedule-content').innerHTML = `
      <div class="empty-state"><h3>Chưa có lịch đề xuất</h3></div>`;
    return;
  }
  const html = items.map(item => {
    const m = TYPE_META[item.type] || TYPE_META.relax;
    return `
      <div class="schedule-item type-${item.type}">
        <span class="sched-time">${item.time}</span>
        <span class="sched-dot" style="background:${m.color}"></span>
        <div>
          <span style="margin-right:.35rem">${m.emoji}</span>
          ${item.activity}
        </div>
      </div>`;
  }).join('');

  document.getElementById('schedule-content').innerHTML = `
    <div class="section-header text-primary">📅 Lịch Trình Tối Ưu Đề Xuất</div>
    <p style="color:var(--muted);margin-bottom:1.25rem;font-size:.9rem">
      Lịch trình dưới đây được AI thiết kế dựa trên dữ liệu sinh hoạt của bạn.
    </p>
    ${html}`;
}

/* =====================================================================
   FOCUS MODE (POMODORO)
===================================================================== */
function formatTime(s) {
  return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
}

function updateTimerUI() {
  document.getElementById('timer-display').textContent = formatTime(focusTimeLeft);
  const circle = document.getElementById('timer-circle');
  const label = document.getElementById('timer-mode-label');
  const isWork = focusMode === 'work';
  circle.style.borderColor = isWork ? 'var(--primary)' : 'var(--success)';
  circle.style.boxShadow = isWork ? '0 0 40px rgba(59,130,246,.25)' : '0 0 40px rgba(16,185,129,.25)';
  label.style.color = isWork ? 'var(--primary)' : 'var(--success)';
  label.textContent = focusActive
    ? (isWork ? '▶ Đang học tập' : '☕ Đang nghỉ ngơi')
    : (isWork ? '▶ Bắt đầu học' : '☕ Chuẩn bị nghỉ');
  document.getElementById('rest-tips').style.display = (!isWork && focusActive) ? '' : 'none';
  document.getElementById('focus-toggle-btn').textContent = focusActive ? '⏸ Tạm dừng' : '▶ Bắt đầu';
}

function toggleFocus() {
  focusActive = !focusActive;
  if (focusActive) {
    focusInterval = setInterval(() => {
      focusTimeLeft--;
      if (focusTimeLeft <= 0) {
        if (focusMode === 'work') { focusMode = 'rest'; focusTimeLeft = 5 * 60; }
        else { focusMode = 'work'; focusTimeLeft = 45 * 60; }
      }
      updateTimerUI();
    }, 1000);
  } else {
    clearInterval(focusInterval);
  }
  updateTimerUI();
}

function resetFocus() {
  clearInterval(focusInterval);
  focusActive = false;
  focusMode = 'work';
  focusTimeLeft = 45 * 60;
  updateTimerUI();
}

/* =====================================================================
   INIT
===================================================================== */
applyPreset();
updateTimerUI();
