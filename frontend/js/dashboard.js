setActiveNav('dashboard');

let chartData = [];
let statsData = {};

async function loadDashboard() {
  const sucursal = document.getElementById('sucursal-select').value || null;
  const dias = document.getElementById('period-select').value || 30;

  try {
    
    const [stats, chart] = await Promise.all([
      api.get(`/ventas/stats/resumen${sucursal ? `?id_sucursal=${sucursal}` : ''}`),
      api.get(`/stats/grafico?dias=${dias}${sucursal ? `&id_sucursal=${sucursal}` : ''}`),
    ]);

    statsData = stats;
    chartData  = chart;

    renderKPIs(stats);
    renderRevenueCharts(chart);
  } catch (e) {
    showToast('Error cargando dashboard: ' + e.message, 'error');
  }
}

function renderKPIs(s) {
  const ingresosMesEl = document.getElementById('kpi-ingresos-mes');
  const ventasTotalesEl = document.getElementById('kpi-ventas-totales');
  
  if (ingresosMesEl) {
    ingresosMesEl.textContent = formatCurrency(s.ingresos_mes);
  }
  if (ventasTotalesEl) {
    ventasTotalesEl.textContent = formatNumber(s.total_ventas);
  }
}

function renderRevenueCharts(data) {
  setTimeout(() => {
    drawSparkline('revenue-sparkline', data, 'ingreso');
    drawWeeklyBarChart('weekly-revenue-chart', data, 'ingreso');
  }, 50);
}

function drawSparkline(canvasId, data, valueKey) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data.length) return;
  const ctx = canvas.getContext('2d');

  const W = canvas.width  = canvas.parentElement.clientWidth;
  const H = canvas.height = canvas.parentElement.clientHeight || 60;
  ctx.clearRect(0, 0, W, H);
  
  const values = data.map(d => d[valueKey]);
  const maxV = Math.max(...values, 1);
  const minV = Math.min(...values, 0);
  const range = maxV - minV;

  ctx.strokeStyle = 'rgba(0, 0, 0, 0.05)';
  ctx.lineWidth = 1;
  const gridRows = 4;
  const gridCols = 8;
  for (let i = 0; i <= gridRows; i++) {
    const y = (H / gridRows) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  for (let i = 0; i <= gridCols; i++) {
    const x = (W / gridCols) * i;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
    ctx.stroke();
  }

  const points = data.map((d, i) => {
    const x = (W / (data.length - 1)) * i;
    const y = H - 8 - ((d[valueKey] - minV) / (range || 1)) * (H - 16);
    return { x, y };
  });
  
  ctx.beginPath();
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  if (points.length > 0) {
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
      const xc = (points[i].x + points[i + 1].x) / 2;
      const yc = (points[i].y + points[i + 1].y) / 2;
      ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
  }
  ctx.stroke();
}

function drawWeeklyBarChart(canvasId, data, valueKey) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  const W = canvas.width  = canvas.parentElement.clientWidth;
  const H = canvas.height = canvas.parentElement.clientHeight || 180;
  ctx.clearRect(0, 0, W, H);
  
  const last7 = data.slice(-7);
  const values = last7.map(d => d[valueKey]);
  const maxV = Math.max(...values, 1);
  
  const dayNames = ['D', 'L', 'M', 'M', 'J', 'V', 'S'];
  const labels = last7.map(d => {
    const dateObj = new Date(d.dia + 'T00:00:00');
    return dayNames[dateObj.getDay()];
  });
  
  const PAD = { top: 30, right: 10, bottom: 35, left: 10 };
  const numBars = last7.length;
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;
  
  const gap = 16;
  const barW = (chartW - (gap * (numBars - 1))) / numBars;

  ctx.strokeStyle = 'rgba(0, 0, 0, 0.06)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(PAD.left, H - 28);
  ctx.lineTo(W - PAD.right, H - 28);
  ctx.stroke();

  last7.forEach((d, i) => {
    const val = d[valueKey];
    const barH = Math.max((val / maxV) * chartH, 10);
    const x = PAD.left + i * (barW + gap);
    const y = PAD.top + chartH - barH;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
    ctx.beginPath();
    ctx.roundRect(x, PAD.top, barW, chartH, 99);
    ctx.fill();

    const grad = ctx.createLinearGradient(x, y, x, PAD.top + chartH);
    grad.addColorStop(0, '#7C8294');
    grad.addColorStop(1, '#1D2528');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, barH, 99);
    ctx.fill();

    ctx.fillStyle = i === numBars - 1 ? '#1D2528' : '#7C8294';
    ctx.font = i === numBars - 1 ? '600 13px Poppins, sans-serif' : '500 13px Poppins, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(labels[i], x + barW / 2, H - 8);

    ctx.fillStyle = '#7C8294';
    ctx.font = '600 11px Poppins, sans-serif';
    if (val > 0) {
      let valStr = val >= 1000 ? (val / 1000).toFixed(1) + 'k' : Math.round(val).toString();
      ctx.fillText('$' + valStr, x + barW / 2, y - 8);
    }
  });
}

let activeAlerts = [];
let currentAlertIndex = 0;

async function loadAlerts() {
  const container = document.getElementById('alerts-container');
  const navArrows = document.getElementById('alert-nav-arrows');
  if (navArrows) navArrows.style.display = 'none';

  container.innerHTML = '<div class="spinner" style="margin:20px auto; border-color: rgba(255,255,255,0.1); border-top-color: #fff;"></div>';
  try {
    const alerts = await api.get('/alertas?solo_activas=true');
    activeAlerts = alerts;
    const titleCountEl = document.getElementById('alert-title-count');
    
    if (!alerts.length) {
      if (titleCountEl) titleCountEl.textContent = 'Alertas activas (0)';
      container.innerHTML = `
        <div style="color: rgba(255,255,255,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; width: 100%;">
          <i class="ph-fill ph-check-circle" style="font-size: 24px; margin-bottom: 6px;"></i>
          <span style="font-size: 0.85rem; font-weight: 500;">Sin alertas activas</span>
        </div>`;
      return;
    }
    
    if (titleCountEl) titleCountEl.textContent = `Alertas activas (${alerts.length})`;
    
    if (currentAlertIndex >= alerts.length) {
      currentAlertIndex = 0;
    }

    container.innerHTML = alerts.map(a => {
      let msg = a.mensaje;
      if (!msg.includes('⚠️')) {
        msg = `⚠️ ${msg}`;
      }
      return `
        <div class="alert-stack-card" id="alert-${a.id_alerta}" onclick="resolveAlert(${a.id_alerta})" style="cursor:pointer" title="Haga clic para resolver">
          <i class="ph ph-cube" style="font-size: 1.2rem; opacity: 0.8;"></i>
          <span class="bento-pill-text">${msg}</span>
          <i class="ph ph-check" style="font-size: 0.9rem; opacity: 0.8;"></i>
        </div>`;
    }).join('');

    if (alerts.length > 1) {
      if (navArrows) navArrows.style.display = 'flex';
    }

    updateAlertStackDisplay();

    const badge = document.getElementById('alert-badge');
    if (badge) { badge.textContent = alerts.length; badge.style.display = 'inline'; }
  } catch {
    container.innerHTML = '<div class="text-muted text-center" style="padding:20px">Error cargando alertas</div>';
  }
}

function updateAlertStackDisplay() {
  const cards = document.querySelectorAll('.alert-stack-card');
  if (!cards.length) return;
  
  cards.forEach((card, idx) => {
    card.className = 'alert-stack-card';
    
    const n = cards.length;
    let relIdx = (idx - currentAlertIndex + n) % n;
    
    if (relIdx === 0) {
      card.classList.add('active');
    } else if (relIdx === 1 && n > 1) {
      card.classList.add('stacked-1');
    } else if (relIdx === 2 && n > 2) {
      card.classList.add('stacked-2');
    } else {
      card.classList.add('hidden');
    }
  });
}

function prevAlert(event) {
  if (event) event.stopPropagation();
  if (activeAlerts.length <= 1) return;
  currentAlertIndex = (currentAlertIndex - 1 + activeAlerts.length) % activeAlerts.length;
  updateAlertStackDisplay();
}

function nextAlert(event) {
  if (event) event.stopPropagation();
  if (activeAlerts.length <= 1) return;
  currentAlertIndex = (currentAlertIndex + 1) % activeAlerts.length;
  updateAlertStackDisplay();
}

window.prevAlert = prevAlert;
window.nextAlert = nextAlert;

async function resolveAlert(id) {
  try {
    await api.patch(`/alertas/${id}/resolver`);
    document.getElementById(`alert-${id}`)?.remove();
    showToast('Alerta resuelta', 'success');
    loadAlertBadge();
    loadAlerts(); 
  } catch (e) { showToast(e.message, 'error'); }
}

async function loadSucursales() {
  try {
    const suc = await api.get('/sucursales');
    const sel = document.getElementById('sucursal-select');
    suc.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id_sucursal;
      opt.textContent = s.nombre;
      sel.appendChild(opt);
    });
  } catch {}
}

async function loadRecentSales() {
  try {
    const ventas = await api.get('/ventas?limit=4');
    const container = document.getElementById('recent-sales-list');
    if (!ventas.length) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--clr-gray);">Sin ventas registradas</div>';
      return;
    }
    container.innerHTML = ventas.map(v => {
      const date = new Date(v.fecha_hora.replace(' ', 'T'));
      const d = date.getDate();
      const m = date.getMonth() + 1;
      let hrs = date.getHours();
      const mins = date.getMinutes().toString().padStart(2, '0');
      const ampm = hrs >= 12 ? 'p. m.' : 'a. m.';
      hrs = hrs % 12;
      hrs = hrs ? hrs : 12;
      const formattedTime = `${d}/${m}, ${hrs.toString().padStart(2, '0')}:${mins} ${ampm}`;
      const clientName = v.id_cliente ? `Cliente #${v.id_cliente}` : 'Mostrador';
      const formattedTotal = '$ ' + Math.round(v.total);
      
      const paymentIcon = v.tipo_pago.toLowerCase() === 'efectivo' ? '<i class="ph ph-money"></i>' : '<i class="ph ph-credit-card"></i>';
      const paymentPill = `<span style="background: rgba(0,0,0,0.05); padding: 4px 10px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; width: fit-content; display: inline-flex; align-items: center; gap: 4px;">${paymentIcon} ${v.tipo_pago}</span>`;
      
      return `
        <div class="bento-pill-item" style="padding: 12px 24px;">
          <div class="bento-pill-row">
            <span style="font-weight: 600; color: var(--clr-gray); font-size: 0.9rem;">#${v.id_venta}</span>
            <span style="color: var(--clr-gray); font-size: 0.85rem;">${formattedTime}</span>
            <span style="font-weight: 500;">${clientName}</span>
            <span>${paymentPill}</span>
            <span style="font-weight: 700; color: var(--clr-dark); font-size: 1rem;">${formattedTotal}</span>
          </div>
        </div>`;
    }).join('');
  } catch {}
}

async function aplicarAjusteGlobal() {
  const sliderVal = document.getElementById('global-price-slider').value;
  try {
    const btn = document.getElementById('btn-aplicar-ajuste');
    if (btn) btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;border-top-color:#fff;margin:0 auto;"></div>';
    await api.post('/productos/ajuste_global', { porcentaje: parseFloat(sliderVal) });
    showToast(`Ajuste del ${sliderVal}% aplicado con éxito`, 'success');
  } catch (e) {
    showToast('Error al aplicar ajuste', 'error');
  } finally {
    const btn = document.getElementById('btn-aplicar-ajuste');
    if (btn) btn.innerHTML = 'Aplicar Ajuste';
  }
}

const slider = document.getElementById('global-price-slider');
const sliderVal = document.getElementById('global-price-value');
if (slider && sliderVal) {
  const updateSliderTrack = () => {
    const val = slider.value;
    sliderVal.textContent = val + '%';
    const percentage = (val - slider.min) / (slider.max - slider.min) * 100;
    slider.style.background = `linear-gradient(to right, var(--clr-blue) ${percentage}%, var(--clr-beige) ${percentage}%)`;
  };
  slider.addEventListener('input', updateSliderTrack);
  updateSliderTrack();
}

document.getElementById('sucursal-select').addEventListener('change', loadDashboard);
document.getElementById('period-select').addEventListener('change', async () => {
  const dias = document.getElementById('period-select').value;
  const sucursal = document.getElementById('sucursal-select').value || null;
  try {
    chartData = await api.get(`/stats/grafico?dias=${dias}${sucursal ? `&id_sucursal=${sucursal}` : ''}`);
    renderRevenueCharts(chartData);
  } catch {}
});

window.addEventListener('resize', () => {
  if (chartData.length) renderRevenueCharts(chartData);
});

loadSucursales();
loadDashboard();

function initBorderGlow() {
  const cards = document.querySelectorAll('.bento-card');
  
  function getCenterOfElement(el) {
    const { width, height } = el.getBoundingClientRect();
    return [width / 2, height / 2];
  }

  function getEdgeProximity(el, x, y) {
    const [cx, cy] = getCenterOfElement(el);
    const dx = x - cx;
    const dy = y - cy;
    let kx = Infinity;
    let ky = Infinity;
    if (dx !== 0) kx = cx / Math.abs(dx);
    if (dy !== 0) ky = cy / Math.abs(dy);
    return Math.min(Math.max(1 / Math.min(kx, ky), 0), 1);
  }

  function getCursorAngle(el, x, y) {
    const [cx, cy] = getCenterOfElement(el);
    const dx = x - cx;
    const dy = y - cy;
    if (dx === 0 && dy === 0) return 0;
    const radians = Math.atan2(dy, dx);
    let degrees = radians * (180 / Math.PI) + 90;
    if (degrees < 0) degrees += 360;
    return degrees;
  }

  cards.forEach(card => {
    if (card.classList.contains('border-glow-card')) return;

    if (!card.querySelector('.border-glow-inner')) {
      const inner = document.createElement('div');
      inner.className = 'border-glow-inner';
      while (card.firstChild) {
        inner.appendChild(card.firstChild);
      }
      card.appendChild(inner);
    }

    if (!card.querySelector('.edge-light')) {
      const edgeLight = document.createElement('span');
      edgeLight.className = 'edge-light';
      card.appendChild(edgeLight);
    }

    card.classList.add('border-glow-card');

    card.addEventListener('pointermove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const edge = getEdgeProximity(card, x, y);
      const angle = getCursorAngle(card, x, y);

      card.style.setProperty('--edge-proximity', `${(edge * 100).toFixed(3)}`);
      card.style.setProperty('--cursor-angle', `${angle.toFixed(3)}deg`);
    });
    
    card.addEventListener('pointerleave', () => {
      card.style.setProperty('--edge-proximity', '0');
    });
  });
}

initBorderGlow();
loadSucursales();
loadDashboard();
loadAlerts();
loadRecentSales();
