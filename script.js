/* =====================================================================
   STATE & CONSTANTS
===================================================================== */
let currentProvider = 'gemini';
let analysisResult = null;
let focusActive = false;
let focusMode = 'work';   // 'work' | 'rest'
let focusTimeLeft = 45 * 60;
let focusInterval = null;

const DEFAULT_TIME_SLOTS = [
  { id: 's1', time: '06:00 - 07:00', label: 'Sáng sớm' },
  { id: 's2', time: '07:00 - 08:30', label: 'Đầu sáng' },
  { id: 's3', time: '08:30 - 11:30', label: 'Giữa sáng' },
  { id: 's4', time: '11:30 - 13:00', label: 'Buổi trưa' },
  { id: 's5', time: '13:00 - 17:00', label: 'Buổi chiều' },
  { id: 's6', time: '17:00 - 18:30', label: 'Cuối chiều' },
  { id: 's7', time: '18:30 - 20:00', label: 'Đầu tối' },
  { id: 's8', time: '20:00 - 22:30', label: 'Giữa tối' },
  { id: 's9', time: '22:30 - 00:00', label: 'Đêm khuya' },
  { id: 's10', time: '00:00 - 06:00', label: 'Giấc ngủ đêm' },
];

let timeSlots = JSON.parse(JSON.stringify(DEFAULT_TIME_SLOTS));

const DAYS = [
  { id: 'mon', name: 'Thứ 2' },
  { id: 'tue', name: 'Thứ 3' },
  { id: 'wed', name: 'Thứ 4' },
  { id: 'thu', name: 'Thứ 5' },
  { id: 'fri', name: 'Thứ 6' },
  { id: 'sat', name: 'Thứ 7' },
  { id: 'sun', name: 'Chủ Nhật' },
];

const DEFAULT_ACTIVITIES = [
  { id: 'act_work', type: 'work', label: '📘 Học tập / Làm việc' },
  { id: 'act_sleep', type: 'sleep', label: '😴 Ngủ / Nghỉ ngơi' },
  { id: 'act_meal', type: 'meal', label: '🍱 Ăn uống' },
  { id: 'act_sport', type: 'sport', label: '🏃 Thể thao / Vận động' },
  { id: 'act_screen', type: 'screen', label: '📱 Màn hình / Giải trí' },
  { id: 'act_bath', type: 'bath', label: '🚿 Tắm rửa / Cá nhân' },
  { id: 'act_other', type: 'other', label: '🛋️ Tự do / Khác' },
];

let customActivities = JSON.parse(JSON.stringify(DEFAULT_ACTIVITIES));

let selectedPalette = {
  type: 'work',
  label: '📘 Học tập / Làm việc'
};

// Data grid: rows x 7 days
let timetableData = [];

const PRESETS = {
  groq: { baseURL: 'https://api.groq.com/openai/v1', model: 'llama-3.3-70b-versatile', keyHint: 'Groq API Key (gsk_...)', docs: 'https://console.groq.com/keys' },
  ollama: { baseURL: 'http://localhost:11434/v1', model: 'llama3.2', keyHint: 'Nhập "ollama" hoặc để trống', docs: null },
  openrouter: { baseURL: 'https://openrouter.ai/api/v1', model: 'meta-llama/llama-3.1-8b-instruct:free', keyHint: 'OpenRouter Key (sk-or-...)', docs: 'https://openrouter.ai/keys' },
  together: { baseURL: 'https://api.together.xyz/v1', model: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo', keyHint: 'Together AI Key', docs: 'https://api.together.ai/' },
  custom: { baseURL: '', model: 'gpt-3.5-turbo', keyHint: 'API Key', docs: null },
};

/* =====================================================================
   PALETTE ENGINE (CUSTOM ACTIVITIES)
===================================================================== */
function renderPalette() {
  const container = document.getElementById('palette-container');
  if (!container) return;

  container.innerHTML = customActivities.map(act => `
    <button type="button" class="palette-tag ${act.type === selectedPalette.type && act.label === selectedPalette.label ? 'active' : ''}" data-type="${act.type}" onclick="selectPalette('${act.type}', '${act.label}')">
      ${act.label}
    </button>
  `).join('');
}

function selectPalette(type, label) {
  selectedPalette = { type, label };
  renderPalette();
}

function openNewActivityModal() {
  document.getElementById('new-act-name').value = '';
  openCustomModal('modal-activity');
}

function saveNewActivity() {
  const name = document.getElementById('new-act-name').value.trim();
  const type = document.getElementById('new-act-type').value;

  if (!name) {
    alert('Vui lòng nhập tên hoạt động!');
    return;
  }

  customActivities.push({
    id: 'act_' + Date.now(),
    type,
    label: name
  });

  selectedPalette = { type, label: name };
  renderPalette();
  closeCustomModal('modal-activity');
}

/* =====================================================================
   TIME SLOTS ENGINE (CUSTOMIZABLE ROWS)
===================================================================== */
function initTimetable() {
  timetableData = timeSlots.map(() => DAYS.map(() => ({ type: 'other', text: '🛋️ Tự do' })));
  renderTimetable();
}

function renderTimetable() {
  const tbody = document.getElementById('timetable-body');
  if (!tbody) return;

  // Make sure timetableData row count matches timeSlots
  while (timetableData.length < timeSlots.length) {
    timetableData.push(DAYS.map(() => ({ type: 'other', text: '🛋️ Tự do' })));
  }
  if (timetableData.length > timeSlots.length) {
    timetableData = timetableData.slice(0, timeSlots.length);
  }

  tbody.innerHTML = timeSlots.map((slot, rIdx) => {
    const cells = DAYS.map((day, cIdx) => {
      const item = timetableData[rIdx][cIdx] || { type: 'other', text: '🛋️ Tự do' };
      return `
        <td>
          <div class="cell-container">
            <button type="button" class="cell-btn type-${item.type}" onclick="handleCellClick(${rIdx}, ${cIdx})" title="Click để gán: ${selectedPalette.label}">
              ${item.text}
            </button>
            <button type="button" class="cell-edit-btn" onclick="openEditCellModal(${rIdx}, ${cIdx}, event)" title="Sửa chi tiết">✏️</button>
          </div>
        </td>
      `;
    }).join('');

    return `
      <tr>
        <td class="time-col">
          <div style="font-weight:700">${slot.time}</div>
          <div style="font-size:.7rem;color:var(--muted);margin:.15rem 0">${slot.label}</div>
          <div class="flex gap-1" style="justify-content:center;margin-top:.2rem">
            <button type="button" class="slot-action-btn" onclick="openEditSlotModal(${rIdx})" title="Chỉnh sửa khung giờ">✏️</button>
            <button type="button" class="slot-action-btn del" onclick="deleteSlot(${rIdx})" title="Xóa khung giờ này">🗑️</button>
          </div>
        </td>
        ${cells}
      </tr>
    `;
  }).join('');
}

function handleCellClick(rIdx, cIdx) {
  timetableData[rIdx][cIdx] = {
    type: selectedPalette.type,
    text: selectedPalette.label
  };
  renderTimetable();
}

function openAddSlotModal() {
  document.getElementById('slot-modal-title').textContent = '⏱️ Thêm Khung Giờ Mới';
  document.getElementById('slot-edit-idx').value = '-1';
  document.getElementById('slot-time-input').value = '';
  document.getElementById('slot-label-input').value = '';
  openCustomModal('modal-slot');
}

function openEditSlotModal(idx) {
  const slot = timeSlots[idx];
  document.getElementById('slot-modal-title').textContent = '✏️ Chỉnh Sửa Khung Giờ';
  document.getElementById('slot-edit-idx').value = String(idx);
  document.getElementById('slot-time-input').value = slot.time;
  document.getElementById('slot-label-input').value = slot.label;
  openCustomModal('modal-slot');
}

function saveSlot() {
  const idx = parseInt(document.getElementById('slot-edit-idx').value, 10);
  const time = document.getElementById('slot-time-input').value.trim();
  const label = document.getElementById('slot-label-input').value.trim() || 'Tùy chỉnh';

  if (!time) {
    alert('Vui lòng nhập khoảng thời gian (VD: 07:00 - 08:30)!');
    return;
  }

  if (idx >= 0 && idx < timeSlots.length) {
    // Edit existing slot
    timeSlots[idx].time = time;
    timeSlots[idx].label = label;
  } else {
    // Add new slot
    timeSlots.push({
      id: 's_' + Date.now(),
      time,
      label
    });
    timetableData.push(DAYS.map(() => ({ type: 'other', text: '🛋️ Tự do' })));
  }

  renderTimetable();
  closeCustomModal('modal-slot');
}

function deleteSlot(idx) {
  if (timeSlots.length <= 1) {
    alert('Phải giữ lại ít nhất 1 khung giờ trong bảng!');
    return;
  }
  if (confirm(`Bạn có chắc muốn xóa khung giờ "${timeSlots[idx].time}" không?`)) {
    timeSlots.splice(idx, 1);
    timetableData.splice(idx, 1);
    renderTimetable();
  }
}

function resetDefaultSlots() {
  if (confirm('Khôi phục danh sách khung giờ về mặc định ban đầu?')) {
    timeSlots = JSON.parse(JSON.stringify(DEFAULT_TIME_SLOTS));
    initTimetable();
    loadSampleSchedule('student');
  }
}

/* =====================================================================
   CELL DETAIL EDITOR MODAL
===================================================================== */
function openEditCellModal(rIdx, cIdx, event) {
  if (event) event.stopPropagation();
  const slot = timeSlots[rIdx];
  const day = DAYS[cIdx];
  const item = timetableData[rIdx][cIdx];

  document.getElementById('cell-edit-r').value = String(rIdx);
  document.getElementById('cell-edit-c').value = String(cIdx);
  document.getElementById('cell-modal-pos').textContent = `${day.name} | ${slot.time} (${slot.label})`;
  document.getElementById('cell-text-input').value = item.text;
  document.getElementById('cell-type-select').value = item.type;

  openCustomModal('modal-cell');
}

function saveCellDetail() {
  const rIdx = parseInt(document.getElementById('cell-edit-r').value, 10);
  const cIdx = parseInt(document.getElementById('cell-edit-c').value, 10);
  const text = document.getElementById('cell-text-input').value.trim();
  const type = document.getElementById('cell-type-select').value;

  if (!text) {
    alert('Vui lòng nhập nội dung hoạt động!');
    return;
  }

  timetableData[rIdx][cIdx] = { text, type };
  renderTimetable();
  closeCustomModal('modal-cell');
}

/* =====================================================================
   MODAL UTILITIES
===================================================================== */
function openCustomModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('show');
}

function closeCustomModal(id, event) {
  if (!event || event.target === document.getElementById(id)) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('show');
  }
}

/* =====================================================================
   SAMPLE PRESETS
===================================================================== */
function clearWeeklyTable() {
  if (confirm('Bạn có chắc muốn xóa toàn bộ hoạt động trong bảng không?')) {
    initTimetable();
  }
}

function loadSampleSchedule(type) {
  initTimetable();

  if (type === 'student') {
    for (let c = 0; c < 7; c++) {
      const isWeekend = c >= 5;
      if (timetableData[0]) timetableData[0][c] = { type: 'sleep', text: isWeekend ? '😴 Ngủ nướng' : '😴 Ngủ cố' };
      if (timetableData[1]) timetableData[1][c] = { type: 'meal', text: isWeekend ? '😴 Ngủ' : '🥪 Ăn sáng vội' };
      if (timetableData[2]) timetableData[2][c] = { type: 'work', text: isWeekend ? '📱 Lướt mạng' : '📘 Học trên lớp' };
      if (timetableData[3]) timetableData[3][c] = { type: 'meal', text: '🍱 Ăn trưa muộn' };
      if (timetableData[4]) timetableData[4][c] = { type: 'work', text: isWeekend ? '🎮 Chơi game' : '📘 Học ca chiều' };
      if (timetableData[5]) timetableData[5][c] = { type: isWeekend ? 'sport' : 'other', text: isWeekend ? '🏃 Đá bóng' : '📱 Lướt TikTok' };
      if (timetableData[6]) timetableData[6][c] = { type: 'meal', text: '🍱 Ăn tối' };
      if (timetableData[7]) timetableData[7][c] = { type: 'work', text: '📘 Tự học / Làm bài' };
      if (timetableData[8]) timetableData[8][c] = { type: 'screen', text: '📱 Cày phim / Game' };
      if (timetableData[9]) timetableData[9][c] = { type: 'sleep', text: '😴 Ngủ (1h sáng)' };
    }
  } else if (type === 'office') {
    for (let c = 0; c < 7; c++) {
      const isWeekend = c >= 5;
      if (timetableData[0]) timetableData[0][c] = { type: isWeekend ? 'sleep' : 'bath', text: isWeekend ? '😴 Ngủ nướng' : '🚿 Thức dậy & Cafe' };
      if (timetableData[1]) timetableData[1][c] = { type: 'work', text: isWeekend ? '🍱 Ăn sáng' : '🚗 Di chuyển đi làm' };
      if (timetableData[2]) timetableData[2][c] = { type: isWeekend ? 'other' : 'work', text: isWeekend ? '☕ Cafe bạn bè' : '📘 Ngồi máy tính' };
      if (timetableData[3]) timetableData[3][c] = { type: 'meal', text: '🍱 Cơm văn phòng' };
      if (timetableData[4]) timetableData[4][c] = { type: isWeekend ? 'other' : 'work', text: isWeekend ? '🛋️ Nghỉ ngơi' : '📘 Họp & Làm việc' };
      if (timetableData[5]) timetableData[5][c] = { type: isWeekend ? 'sport' : 'bath', text: isWeekend ? '🏃 Gym' : '🚿 Tắc đường & Tắm' };
      if (timetableData[6]) timetableData[6][c] = { type: 'meal', text: '🍱 Ăn tối' };
      if (timetableData[7]) timetableData[7][c] = { type: isWeekend ? 'screen' : 'work', text: isWeekend ? '📱 Xem Netflix' : '📘 Check mail làm thêm' };
      if (timetableData[8]) timetableData[8][c] = { type: 'screen', text: '📱 Dùng điện thoại' };
      if (timetableData[9]) timetableData[9][c] = { type: 'sleep', text: '😴 Ngủ đêm' };
    }
  }

  renderTimetable();
}

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
  const activeTab = document.getElementById('tab-' + name);
  const activeContent = document.getElementById('content-' + name);
  if (activeTab) activeTab.classList.add('active');
  if (activeContent) activeContent.classList.add('active');
}

/* =====================================================================
   PROMPT BUILDER (MEDICAL SCIENTIFIC WEEKLY ANALYSIS)
===================================================================== */
function buildWeeklyPrompt(scheduleMatrix, waterIntake, stressLevel) {
  let scheduleText = '';
  DAYS.forEach((day, dIdx) => {
    scheduleText += `\n--- [${day.name}] ---\n`;
    timeSlots.forEach((slot, sIdx) => {
      const item = (scheduleMatrix[sIdx] && scheduleMatrix[sIdx][dIdx]) || { text: 'Tự do', type: 'other' };
      scheduleText += `${slot.time} (${slot.label}): ${item.text} [Loại: ${item.type}]\n`;
    });
  });

  return `Bạn là Hội đồng Chuyên gia Y học Dự phòng, Thần kinh học và Tối ưu hóa Nhịp sinh học (Circadian Neurobiology).
Nhiệm vụ: Phân tích toàn diện và chuyên sâu thời khóa biểu sinh hoạt 7 ngày trong tuần dưới đây của người dùng.

Dữ liệu bổ sung:
- Lượng nước uống trung bình: ${waterIntake} Lít/ngày
- Mức độ áp lực / Căng thẳng (Stress): ${stressLevel}

Thời khóa biểu 7 ngày:
${scheduleText}

Yêu cầu đánh giá chuẩn khoa học y tế:
1. Phân tích định lượng nhịp sinh học (Thời lượng ngủ TB, nợ ngủ, giờ tiếp xúc màn hình, giờ ngồi tĩnh tại, độ ổn định chu kỳ 24h).
2. Chỉ rõ các Nguy cơ Bệnh học Tiềm ẩn (Pathological Risks): Cận thị/mỏi mắt điều tiết (Asthenopia), thoái hóa cột sống cổ/thắt lưng, rối loạn tiết acid dạ dày do giờ ăn thất thường, suy giảm miễn dịch & ức chế Melatonin do tiếp xúc ánh sáng xanh sau 22:30, tăng gánh nặng tim mạch...
3. Nêu rõ Cơ chế Sinh học Gây bệnh (Pathophysiological Mechanism) và Hậu quả lâu dài cho từng nguy cơ.
4. Đưa ra Khuyến nghị Y khoa Lâm sàng (Evidence-based Recommendations).
5. Xây dựng Lịch trình Tối ưu Mới kết hợp các phiên học tập Pomodoro 45 phút xen kẽ 5 phút giải lao phục hồi.

BẮT BUỘC trả về định dạng JSON hợp lệ, không có bất kỳ văn bản nào khác ngoài JSON:
{
  "score": 68,
  "summary": "Đánh giá tổng quan súc tích về thói quen tuần của người dùng dưới góc nhìn y khoa",
  "metrics": {
    "avgSleep": "6.2 giờ/ngày",
    "screenTime": "7.5 giờ/ngày",
    "sedentaryHours": "8.0 giờ/ngày",
    "circadianConsistency": "Kém"
  },
  "risks": [
    {
      "name": "Hội chứng Rối loạn Nhịp sinh học & Suy giảm Melatonin",
      "probability": "Cao",
      "mechanism": "Tiếp xúc màn hình sau 22:30 ức chế tuyến tùng tiết Melatonin, làm giảm giấc ngủ sâu sóng chậm N3 và REM.",
      "consequence": "Suy giảm trí nhớ ngắn hạn, mệt mỏi ban ngày, suy yếu hệ miễn dịch và tăng đề kháng insulin."
    }
  ],
  "medicalAdvice": [
    {
      "title": "Tối ưu hóa Ánh sáng & Giấc ngủ",
      "content": "Cắt giảm thiết bị phát ánh sáng xanh trước khi ngủ 45 phút, đón ánh sáng mặt trời 15 phút sau khi thức dậy."
    },
    {
      "title": "Bảo vệ Mắt & Hệ Cơ Xương Khớp",
      "content": "Áp dụng quy tắc 20-20-20 (nhìn xa 6m trong 20s) và đứng dậy đi lại nhẹ sau mỗi 45 phút ngồi tĩnh."
    }
  ],
  "schedule": [
    { "id": 1, "time": "06:30", "activity": "Thức dậy, uống 300ml nước ấm và đón ánh sáng tự nhiên", "type": "health" },
    { "id": 2, "time": "07:15", "activity": "Ăn sáng giàu protein và chuẩn bị học tập", "type": "meal" },
    { "id": 3, "time": "08:30", "activity": "Focus Mode 1 (45p học tập chuyên sâu)", "type": "work" },
    { "id": 4, "time": "09:15", "activity": "Giải lao 5p: Thư giãn mắt và vận động nhẹ", "type": "health" }
  ]
}
Chú ý: Trong "schedule", type chỉ gồm: health, work, meal, relax.`;
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
      max_tokens: 3500,
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
   SUBMIT WEEKLY SURVEY
===================================================================== */
async function handleWeeklySubmit() {
  const waterIntake = document.getElementById('waterIntake')?.value || '2.0';
  const stressLevel = document.getElementById('stressLevel')?.value || 'Trung bình';

  const btn = document.getElementById('submit-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;margin:0"></div> Đang tiến hành phân tích y học tuần...';
  }

  renderDashboardLoading();
  switchTab('dashboard');

  try {
    const prompt = buildWeeklyPrompt(timetableData, waterIntake, stressLevel);
    const result = currentProvider === 'gemini' ? await callGemini(prompt) : await callOpenAI(prompt);
    analysisResult = result;
    renderDashboard(result);
    renderSchedule(result.schedule || []);
  } catch (err) {
    renderDashboardError(err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '🧠 Phân tích Y khoa &amp; Đề xuất Tối ưu Sinh học';
    }
  }
}

/* =====================================================================
   RENDER DASHBOARD (MEDICAL EVALUATION)
===================================================================== */
function renderDashboardLoading() {
  document.getElementById('dashboard-content').innerHTML = `
    <div class="empty-state">
      <div class="spinner"></div>
      <h3 style="font-size:1.2rem;margin-bottom:.5rem">Hội đồng Y khoa AI đang phân tích nhịp sinh học 7 ngày...</h3>
      <p style="color:var(--muted)">Đang tính toán nợ ngủ, tải trọng mắt, áp lực chuyển hóa và lập mô hình tối ưu sinh học.</p>
    </div>`;
}

function renderDashboardError(msg) {
  document.getElementById('dashboard-content').innerHTML = `
    <div class="empty-state">
      <div style="font-size:2.5rem;margin-bottom:1rem">⚠️</div>
      <h3 class="text-danger">Đã xảy ra lỗi trong quá trình phân tích</h3>
      <p style="color:var(--muted);max-width:540px;margin:.5rem auto">${msg}</p>
    </div>`;
}

function riskColor(p) {
  if (p === 'Cao' || p === 'High') return 'text-danger';
  if (p === 'Trung bình' || p === 'Medium') return 'text-warning';
  return 'text-success';
}

function renderDashboard(r) {
  const scoreColor = r.score < 50 ? 'text-danger' : r.score < 75 ? 'text-warning' : 'text-success';
  const metrics = r.metrics || {};

  // Metrics cards
  const metricsHTML = `
    <div class="biomarker-grid">
      <div class="biomarker-card">
        <div class="biomarker-title">😴 Giấc ngủ trung bình</div>
        <div class="biomarker-val">${metrics.avgSleep || 'Chưa rõ'}</div>
      </div>
      <div class="biomarker-card">
        <div class="biomarker-title">📱 Thời lượng màn hình</div>
        <div class="biomarker-val">${metrics.screenTime || 'Chưa rõ'}</div>
      </div>
      <div class="biomarker-card">
        <div class="biomarker-title">🪑 Thời gian ngồi tĩnh</div>
        <div class="biomarker-val">${metrics.sedentaryHours || 'Chưa rõ'}</div>
      </div>
      <div class="biomarker-card">
        <div class="biomarker-title">🔄 Độ ổn định nhịp sinh học</div>
        <div class="biomarker-val">${metrics.circadianConsistency || 'Chưa rõ'}</div>
      </div>
    </div>
  `;

  // Pathology Risk Cards
  const risksHTML = (r.risks || []).map(risk => `
    <div class="pathology-card">
      <div class="flex justify-between items-center mb-2" style="flex-wrap:wrap;gap:.5rem">
        <strong style="font-size:1.1rem;color:#f8fafc">⚠️ ${risk.name}</strong>
        <span class="risk-tag ${riskColor(risk.probability)}">Mức độ: ${risk.probability}</span>
      </div>
      <div class="mechanism-box">
        <strong>🔬 Cơ chế bệnh sinh học:</strong> ${risk.mechanism || 'Chưa có thông tin'}
      </div>
      ${risk.consequence ? `
        <div class="consequence-box">
          <strong>⚡ Hậu quả lâu dài:</strong> ${risk.consequence}
        </div>
      ` : ''}
    </div>
  `).join('');

  // Clinical Medical Advice
  const adviceHTML = (r.medicalAdvice || []).map(adv => `
    <div class="clinical-advice-card">
      <div class="clinical-advice-title">🩺 ${adv.title}</div>
      <div class="clinical-advice-text">${adv.content}</div>
    </div>
  `).join('') || (r.advice ? `<div class="advice-box">${r.advice}</div>` : '');

  document.getElementById('dashboard-content').innerHTML = `
    <div class="flex justify-between items-center mb-6" style="flex-wrap:wrap;gap:1rem">
      <div>
        <div class="section-header text-primary" style="margin:0;font-size:1.35rem">💓 Báo Cáo Y Khoa &amp; Nhịp Sinh Học Tuần</div>
        <p style="color:var(--muted);font-size:.9rem;margin-top:.25rem">${r.summary || 'Phân tích tự động dựa trên thời khóa biểu 7 ngày.'}</p>
      </div>
      <span class="score-badge glass">
        Chỉ số Sức khỏe: <span class="${scoreColor}" style="font-size:1.4rem;margin-left:.35rem">${r.score}/100</span>
      </span>
    </div>

    ${metricsHTML}

    <div class="mb-6">
      <div class="section-header text-danger">⚠️ Bảng Phân Tích Nguy Cơ Bệnh Học Tiềm Ẩn</div>
      ${risksHTML}
    </div>

    <div>
      <div class="section-header text-success">🛡️ Phác Đồ Can Thiệp &amp; Khuyến Nghị Y Khoa</div>
      ${adviceHTML}
    </div>
  `;
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
    <div class="section-header text-primary">📅 Lịch Trình Tối Ưu Sinh Học Mới (Áp dụng Pomodoro 45/5)</div>
    <p style="color:var(--muted);margin-bottom:1.25rem;font-size:.9rem">
      Lịch trình dưới đây được AI tái cơ cấu nhằm cân bằng thời gian học tập, giấc ngủ và bảo vệ nhịp sinh học.
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
  if (circle) {
    circle.style.borderColor = isWork ? 'var(--primary)' : 'var(--success)';
    circle.style.boxShadow = isWork ? '0 0 40px rgba(59,130,246,.25)' : '0 0 40px rgba(16,185,129,.25)';
  }
  if (label) {
    label.style.color = isWork ? 'var(--primary)' : 'var(--success)';
    label.textContent = focusActive
      ? (isWork ? '▶ Đang học tập' : '☕ Đang nghỉ ngơi')
      : (isWork ? '▶ Bắt đầu học' : '☕ Chuẩn bị nghỉ');
  }
  const tips = document.getElementById('rest-tips');
  if (tips) tips.style.display = (!isWork && focusActive) ? '' : 'none';
  const toggleBtn = document.getElementById('focus-toggle-btn');
  if (toggleBtn) toggleBtn.textContent = focusActive ? '⏸ Tạm dừng' : '▶ Bắt đầu';
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
function initApp() {
  renderPalette();
  initTimetable();
  loadSampleSchedule('student');
  applyPreset();
  updateTimerUI();
}

document.addEventListener('DOMContentLoaded', initApp);

if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initApp();
}
