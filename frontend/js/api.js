/* =====================================================================
   FARO — Mini SVG Chart Library (no dependencies)
   ===================================================================== */

const API_BASE = 'http://localhost:8000/api/v1';

// ── Fetch helpers ──────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

const api = {
  get:    (path)          => apiFetch(path, { cache: 'no-store' }),
  post:   (path, body)    => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  put:    (path, body)    => apiFetch(path, { method: 'PUT',  body: JSON.stringify(body) }),
  patch:  (path, body={}) => apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path)          => apiFetch(path, { method: 'DELETE' }),
};

// ── Toast system ───────────────────────────────────────────────────────────

function initToasts() {
  if (!document.getElementById('toast-container')) {
    const el = document.createElement('div');
    el.id = 'toast-container';
    el.className = 'toast-container';
    document.body.appendChild(el);
  }
}

function showToast(message, type = 'success', duration = 3500) {
  initToasts();
  const icons = { success: '<i class="ph-fill ph-check-circle"></i>', error: '<i class="ph-fill ph-x-circle"></i>', warning: '<i class="ph-fill ph-warning"></i>', info: '<i class="ph-fill ph-info"></i>' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  document.getElementById('toast-container').appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Number formatters ──────────────────────────────────────────────────────

function formatCurrency(v) {
  if (v == null) return '—';
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(v);
}

function formatNumber(v, decimals = 0) {
  if (v == null) return '—';
  return new Intl.NumberFormat('es-AR', { maximumFractionDigits: decimals }).format(v);
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso.replace(' ', 'T'));
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso.replace(' ', 'T'));
  return d.toLocaleString('es-AR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

// ── Alert badge loader ─────────────────────────────────────────────────────

async function loadAlertBadge() {
  try {
    const alerts = await api.get('/alertas?solo_activas=true');
    const badge = document.getElementById('alert-badge');
    if (badge) {
      if (alerts.length > 0) {
        badge.textContent = alerts.length;
        badge.style.display = 'inline';
      } else {
        badge.style.display = 'none';
      }
    }
  } catch {}
}

// ── Canvas line chart ──────────────────────────────────────────────────────

function drawLineChart(canvasId, data, labelKey, valueKey, color = '#2727BA', fillColor = 'rgba(39,39,186,0.08)') {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data.length) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.parentElement.clientWidth;
  const H = canvas.height = canvas.parentElement.clientHeight || 200;
  ctx.clearRect(0, 0, W, H);

  const PAD = { top: 16, right: 16, bottom: 32, left: 60 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top  - PAD.bottom;

  const values = data.map(d => d[valueKey]);
  const maxV = Math.max(...values, 1);
  const minV = 0;

  const xStep = chartW / Math.max(data.length - 1, 1);

  const toX = (i) => PAD.left + i * xStep;
  const toY = (v) => PAD.top + chartH - ((v - minV) / (maxV - minV)) * chartH;

  // Grid lines
  ctx.strokeStyle = 'rgba(0,0,0,0.05)';
  ctx.lineWidth = 1;
  for (let t = 0; t <= 4; t++) {
    const y = PAD.top + (chartH / 4) * t;
    ctx.beginPath();
    ctx.moveTo(PAD.left, y);
    ctx.lineTo(W - PAD.right, y);
    ctx.stroke();
    // Y labels
    const val = maxV - (maxV / 4) * t;
    ctx.fillStyle = '#7C8294';
    ctx.font = '10px Poppins, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(val >= 1000 ? `$${(val/1000).toFixed(0)}k` : `$${Math.round(val)}`, PAD.left - 6, y + 4);
  }

  // Fill area
  const grad = ctx.createLinearGradient(0, PAD.top, 0, H - PAD.bottom);
  grad.addColorStop(0, fillColor.replace('0.08', '0.18'));
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.beginPath();
  data.forEach((d, i) => {
    const x = toX(i), y = toY(d[valueKey]);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo(toX(data.length - 1), H - PAD.bottom);
  ctx.lineTo(toX(0), H - PAD.bottom);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  data.forEach((d, i) => {
    const x = toX(i), y = toY(d[valueKey]);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Dots & X labels
  data.forEach((d, i) => {
    const x = toX(i), y = toY(d[valueKey]);
    ctx.beginPath();
    ctx.arc(x, y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(x, y, 1.5, 0, Math.PI * 2);
    ctx.fill();

    // X label (every 5th or first/last)
    if (data.length <= 10 || i % Math.ceil(data.length / 8) === 0 || i === data.length - 1) {
      const lbl = d[labelKey].slice(5); // MM-DD
      ctx.fillStyle = '#7C8294';
      ctx.font = '9px Poppins, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(lbl, x, H - PAD.bottom + 14);
    }
  });
}

// ── Bar chart ──────────────────────────────────────────────────────────────

function drawBarChart(canvasId, labels, values, color = '#2727BA') {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !values.length) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.parentElement.clientWidth;
  const H = canvas.height = canvas.parentElement.clientHeight || 180;
  ctx.clearRect(0, 0, W, H);

  const PAD = { top: 12, right: 12, bottom: 44, left: 12 };
  const maxV = Math.max(...values, 1);
  const barW  = Math.max(((W - PAD.left - PAD.right) / values.length) - 8, 8);
  const gap   = (W - PAD.left - PAD.right - barW * values.length) / (values.length + 1);

  values.forEach((v, i) => {
    const barH = ((v / maxV) * (H - PAD.top - PAD.bottom));
    const x = PAD.left + gap + i * (barW + gap);
    const y = H - PAD.bottom - barH;

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, barH, [5, 5, 0, 0]);
    ctx.fill();

    ctx.fillStyle = '#7C8294';
    ctx.font = '9px Poppins, sans-serif';
    ctx.textAlign = 'center';
    const lbl = labels[i].length > 10 ? labels[i].slice(0, 10) + '…' : labels[i];
    ctx.fillText(lbl, x + barW / 2, H - PAD.bottom + 14);
    ctx.fillText(formatNumber(v, 0), x + barW / 2, H - PAD.bottom + 26);
  });
}

// ── Sidebar active state ───────────────────────────────────────────────────

function setActiveNav(page) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
  
  // Move cutout
  const activeEl = document.querySelector('.nav-item.active');
  const cutout = document.querySelector('.sidebar__cutout');
  if (activeEl && cutout) {
    const offset = activeEl.offsetTop + (activeEl.offsetHeight / 2) - 40;
    cutout.style.top = `${offset}px`;
  }
}

// ── Modal helpers ──────────────────────────────────────────────────────────

function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
function closeAllModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open')); }

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAllModals(); });

// ── Init ───────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadAlertBadge();
});
