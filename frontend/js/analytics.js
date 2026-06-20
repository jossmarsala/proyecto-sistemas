/**
 * FARO Analytics — Chart.js ML Dashboard
 * Renders 7 interactive charts, ML forecast with CI band,
 * and per-product stock depletion predictions.
 */

setActiveNav('analytics');

// ── Chart instances (kept for destroy/rebuild) ────────────────────────────────

const charts = {};

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

// ── Chart.js global defaults ──────────────────────────────────────────────────

Chart.defaults.font.family = "'Poppins', sans-serif";
Chart.defaults.font.size   = 11;
Chart.defaults.color       = '#7C8294';
Chart.defaults.plugins.legend.display = false;
Chart.defaults.plugins.tooltip.backgroundColor = '#1D2528';
Chart.defaults.plugins.tooltip.padding         = 10;
Chart.defaults.plugins.tooltip.cornerRadius    = 8;
Chart.defaults.plugins.tooltip.titleFont       = { weight: '700', size: 12 };
Chart.defaults.animation.duration              = 500;
Chart.defaults.animation.easing               = 'easeInOutQuart';

// ── Colours ───────────────────────────────────────────────────────────────────

const C = {
  blue:       '#2727BA',
  bluePale:   'rgba(39,39,186,0.15)',
  blueFill:   'rgba(39,39,186,0.08)',
  accent:     '#EFFF1D',
  accentFill: 'rgba(239,255,29,0.15)',
  green:      '#22c55e',
  greenFill:  'rgba(34,197,94,0.10)',
  danger:     '#ef4444',
  dangerFill: 'rgba(239,68,68,0.10)',
  gray:       '#7C8294',
  dark:       '#1D2528',
  pink:       '#E8A898',
  // Top products palette — coherent violet/blue scale
  palette: [
    '#2727BA','#3D3DC8','#5454D0','#6B6BD8','#7B7FD4',
    '#8E91DB','#A1A4E3','#BBBDE8','#1D2528','#2C3338',
  ],
};

// ── State ─────────────────────────────────────────────────────────────────────

let productsCache = [];
let forecastData  = null;

// ── Helpers ───────────────────────────────────────────────────────────────────

function getSucursal() { return document.getElementById('anl-sucursal')?.value || ''; }
function getPeriodo()  { return document.getElementById('anl-periodo')?.value  || '60'; }
function getFuturo()   { return document.getElementById('fc-futuro')?.value    || '30'; }

function sucursalParam() { const s = getSucursal(); return s ? `&id_sucursal=${s}` : ''; }

// ── Main load orchestrator ────────────────────────────────────────────────────

async function loadAll() {
  const [_forecast, _analytics] = await Promise.allSettled([
    loadForecast(),
    loadAnalytics(),
  ]);
  loadDepletionCards();
}

// ── 1. Sales Forecast Chart ───────────────────────────────────────────────────

async function loadForecast() {
  const dias_h = getPeriodo();
  const dias_f = getFuturo();

  try {
    const data = await api.get(
      `/predicciones/ventas?dias_historial=${dias_h}&dias_futuro=${dias_f}${sucursalParam()}`
    );
    forecastData = data;
    updateForecastKPIs(data);
    renderForecastChart(data);
  } catch (e) {
    showToast('Error cargando pronóstico: ' + e.message, 'error');
  }
}

function updateForecastKPIs(data) {
  // Model badge
  const mb = document.getElementById('model-badge');
  mb.innerHTML = data.metodo === 'polynomial_regression' ? '<i class="ph ph-ruler"></i> Regresión Polinómica' : '<i class="ph ph-chart-bar"></i> Media Móvil';

  // R² badge
  const r2el = document.getElementById('r2-badge');
  if (data.r2_score != null) {
    r2el.textContent = `R² = ${data.r2_score}`;
    r2el.style.display = 'inline-flex';
    r2el.style.background = data.r2_score > 0.7 ? '#dcfce7' : data.r2_score > 0.4 ? '#fef9c3' : '#fee2e2';
    r2el.style.color      = data.r2_score > 0.7 ? '#15803d' : data.r2_score > 0.4 ? '#a16207' : '#b91c1c';
  }

  // Trend badge
  const tb = document.getElementById('trend-badge');
  const trendMap = { creciente: '▲ Creciente', decreciente: '▼ Decreciente', estable: '→ Estable' };
  tb.textContent = trendMap[data.tendencia] || '—';
  const trendCls = { creciente: 'pill pill--green', decreciente: 'pill pill--red', estable: 'pill pill--yellow' };
  tb.className = trendCls[data.tendencia] || 'pill pill--yellow';

  document.getElementById('fc-avg-val').textContent = formatCurrency(data.ingreso_promedio_diario);
  document.getElementById('fc-mes-val').textContent = formatCurrency(data.ingreso_mes_proyectado);
  document.getElementById('fc-mes-sub').textContent = `próximos ${getFuturo()} días`;

  const tendTexts = {
    creciente:   '▲ En crecimiento',
    decreciente: '▼ En descenso',
    estable:     '→ Estable',
  };
  document.getElementById('fc-tend-val').textContent = tendTexts[data.tendencia] || '—';
  document.getElementById('fc-tend-sub').textContent = `Basado en ${data.dias_historial_usado} días de historial`;
}

function renderForecastChart(data) {
  destroyChart('forecast');
  const ctx = document.getElementById('chart-forecast').getContext('2d');

  // Historical labels + values
  const histLabels = data.historial.map(d => d.dia.slice(5));   // MM-DD
  const histValues = data.historial.map(d => d.ingreso);

  // Prediction labels + values
  const predLabels = data.prediccion.map(d => d.dia.slice(5));
  const predValues = data.prediccion.map(d => d.ingreso_predicho);
  const ciLower    = data.prediccion.map(d => d.ci_lower);
  const ciUpper    = data.prediccion.map(d => d.ci_upper);

  const allLabels = [...histLabels, ...predLabels];

  // Pad historical values with nulls to match full length
  const histPadded = [...histValues, ...new Array(predLabels.length).fill(null)];
  const predPadded = [...new Array(histLabels.length).fill(null), ...predValues];
  const ciLPadded  = [...new Array(histLabels.length).fill(null), ...ciLower];
  const ciUPadded  = [...new Array(histLabels.length).fill(null), ...ciUpper];

  charts.forecast = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        // CI upper (invisible, for fill reference)
        {
          label: 'IC Superior',
          data: ciUPadded,
          borderColor: 'transparent',
          backgroundColor: 'rgba(39,39,186,0.10)',
          fill: '+1',  // fill to dataset below (ciLower)
          pointRadius: 0,
          tension: 0.3,
        },
        // CI lower (fill reference)
        {
          label: 'IC Inferior',
          data: ciLPadded,
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          pointRadius: 0,
          tension: 0.3,
        },
        // Historical real
        {
          label: 'Ventas reales',
          data: histPadded,
          borderColor: C.dark,
          backgroundColor: 'rgba(29,37,40,0.06)',
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 5,
          tension: 0.3,
          fill: false,
        },
        // Prediction
        {
          label: 'Pronóstico ML',
          data: predPadded,
          borderColor: C.blue,
          backgroundColor: 'rgba(39,39,186,0.08)',
          borderWidth: 2.5,
          borderDash: [6, 4],
          pointRadius: 0,
          pointHoverRadius: 5,
          tension: 0.3,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            filter: item => !['IC Superior', 'IC Inferior'].includes(item.text),
            usePointStyle: true,
            padding: 16,
          },
        },
        tooltip: {
          callbacks: {
            title: items => `Día: ${items[0].label}`,
            label: item => {
              if (['IC Superior','IC Inferior'].includes(item.dataset.label)) return null;
              const v = item.raw;
              if (v == null) return null;
              return `  ${item.dataset.label}: ${formatCurrency(v)}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxTicksLimit: 12, maxRotation: 0 },
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { callback: v => v >= 1000 ? `$${(v/1000).toFixed(0)}k` : `$${v}` },
        },
      },
    },
  });
}

// ── 2. Top Products Charts ────────────────────────────────────────────────────

function renderTopRevenue(productos) {
  destroyChart('top-revenue');
  const ctx = document.getElementById('chart-top-revenue').getContext('2d');
  const sorted = [...productos].sort((a,b) => b.revenue - a.revenue).slice(0,10);
  charts['top-revenue'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(p => p.nombre.length > 18 ? p.nombre.slice(0,18)+'…' : p.nombre),
      datasets: [{
        label: 'Ingresos',
        data: sorted.map(p => p.revenue),
        backgroundColor: sorted.map((_, i) => C.palette[i % C.palette.length]),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: { callbacks: { label: i => `  ${formatCurrency(i.raw)}` } },
      },
      scales: {
        x: { ticks: { callback: v => `$${(v/1000).toFixed(0)}k` }, grid: { color: 'rgba(0,0,0,0.04)' } },
        y: { grid: { display: false }, ticks: { font: { weight: '600' } } },
      },
    },
  });
}

function renderTopQty(productos) {
  destroyChart('top-qty');
  const ctx = document.getElementById('chart-top-qty').getContext('2d');
  const sorted = [...productos].sort((a,b) => b.qty - a.qty).slice(0,10);
  charts['top-qty'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(p => p.nombre.length > 18 ? p.nombre.slice(0,18)+'…' : p.nombre),
      datasets: [{
        label: 'Unidades',
        data: sorted.map(p => p.qty),
        backgroundColor: sorted.map((_, i) => C.palette[(i + 3) % C.palette.length]),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: { callbacks: { label: i => `  ${formatNumber(i.raw, 1)} unidades` } },
      },
      scales: {
        x: { grid: { color: 'rgba(0,0,0,0.04)' } },
        y: { grid: { display: false }, ticks: { font: { weight: '600' } } },
      },
    },
  });
}

// ── 3. Margin Chart ───────────────────────────────────────────────────────────

function renderMarginChart(margen_diario) {
  destroyChart('margin');
  const ctx = document.getElementById('chart-margin').getContext('2d');
  const recent = margen_diario.slice(-40);

  charts.margin = new Chart(ctx, {
    type: 'line',
    data: {
      labels: recent.map(d => d.dia.slice(5)),
      datasets: [
        {
          label: 'Ingreso',
          data: recent.map(d => d.ingreso),
          borderColor: C.blue,
          backgroundColor: C.blueFill,
          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
        },
        {
          label: 'Costo',
          data: recent.map(d => d.costo),
          borderColor: C.danger,
          backgroundColor: C.dangerFill,
          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: true, position: 'bottom', labels: { usePointStyle: true, padding: 12 } },
        tooltip: { callbacks: { label: i => `  ${i.dataset.label}: ${formatCurrency(i.raw)}` } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { callback: v => `$${(v/1000).toFixed(0)}k` } },
      },
    },
  });
}

// ── 4. Day-of-Week Chart ──────────────────────────────────────────────────────

function renderDOWChart(ventas_dow) {
  destroyChart('dow');
  const ctx = document.getElementById('chart-dow').getContext('2d');
  charts.dow = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ventas_dow.map(d => d.dia),
      datasets: [{
        label: 'Ingresos',
        data: ventas_dow.map(d => d.ingreso),
        backgroundColor: ventas_dow.map(d => d.dia === 'Sáb' || d.dia === 'Dom' ? C.accent : C.blue),
        borderRadius: 8,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: i => [
              `  Ingreso: ${formatCurrency(i.raw)}`,
              `  Ventas: ${ventas_dow[i.dataIndex].num_ventas}`,
            ],
          },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { callback: v => `$${(v/1000).toFixed(0)}k` } },
      },
    },
  });
}

// ── 5. Hourly chart ───────────────────────────────────────────────────────────

function renderHoraChart(ventas_hora) {
  destroyChart('hora');
  const ctx = document.getElementById('chart-hora').getContext('2d');
  // Only show business hours (6–22)
  const biz = ventas_hora.filter(h => h.hora >= 6 && h.hora <= 22);
  charts.hora = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: biz.map(h => `${String(h.hora).padStart(2,'0')}:00`),
      datasets: [{
        label: 'Ventas',
        data: biz.map(h => h.num_ventas),
        backgroundColor: biz.map(h => {
          const v = h.num_ventas / (Math.max(...biz.map(b => b.num_ventas)) || 1);
          return `rgba(39,39,186,${0.2 + v * 0.8})`;
        }),
        borderRadius: 5,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: { callbacks: { label: i => `  ${i.raw} ventas · ${formatCurrency(biz[i.dataIndex].ingreso)}` } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { stepSize: 1 } },
      },
    },
  });
}

// ── 6. Analytics advanced ─────────────────────────────────────────────────────

async function loadAnalytics() {
  const dias = getPeriodo();
  const suc  = getSucursal();
  try {
    const data = await api.get(
      `/predicciones/analytics?dias=${dias}${suc ? `&id_sucursal=${suc}` : ''}`
    );
    renderTopRevenue(data.top_10_productos);
    renderTopQty(data.top_10_productos);
    renderMarginChart(data.margen_diario);
    renderDOWChart(data.ventas_por_dia_semana);
    renderHoraChart(data.ventas_por_hora);
  } catch (e) {
    showToast('Error cargando analytics: ' + e.message, 'error');
  }
}

// ── 7. Stock Depletion cards + per-product forecast ───────────────────────────

async function loadDepletionCards() {
  const suc  = getSucursal();
  const dias = getPeriodo();
  const container = document.getElementById('depletion-cards');
  container.innerHTML = '<div class="spinner" style="margin:20px auto"></div>';

  try {
    // Get all products and forecast each (batch)
    if (!productsCache.length) {
      productsCache = await api.get(`/productos?id_sucursal=${suc || 1}&limit=500`);
      // Populate select
      const sel = document.getElementById('prod-select');
      sel.innerHTML = '<option value="">Seleccioná un producto…</option>' +
        productsCache.map(p => `<option value="${p.id_producto}">${p.nombre}</option>`).join('');
    }

    const qbData = await api.get(
      `/productos/prediccion-quiebre?id_sucursal=${suc || 1}&ventana_dias=${Math.min(dias, 60)}`
    );

    // Show top 8 most critical
    const sorted = [...qbData]
      .filter(d => d.promedio_diario > 0)
      .sort((a, b) => {
        if (a.alerta_quiebre && !b.alerta_quiebre) return -1;
        if (!a.alerta_quiebre && b.alerta_quiebre) return 1;
        const ad = a.dias_restantes ?? 999, bd = b.dias_restantes ?? 999;
        return ad - bd;
      })
      .slice(0, 8);

    if (!sorted.length) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state__icon"><i class="ph-fill ph-check-circle"></i></div><div class="empty-state__text">Sin predicciones disponibles (sin historial de ventas)</div></div>';
      return;
    }

    container.innerHTML = sorted.map(d => {
      const cls = d.alerta_quiebre ? 'critical' : d.dias_restantes != null && d.dias_restantes < 21 ? 'warn' : 'ok';
      const diasStr = d.dias_restantes != null ? `${d.dias_restantes}` : '∞';
      return `<div class="dep-card ${cls}" onclick="selectProduct(${d.id_producto})">
        <div class="dep-card__name">${d.nombre}</div>
        <div class="dep-card__days ${cls === 'critical' ? 'highlight-negative' : cls === 'warn' ? '' : 'highlight-positive'}">${diasStr}</div>
        <div class="dep-card__label">días restantes estimados</div>
      </div>`;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div class="text-muted" style="padding:12px">${e.message}</div>`;
  }
}

function selectProduct(id) {
  document.getElementById('prod-select').value = id;
  loadProductForecast();
}

async function loadProductForecast() {
  const id  = document.getElementById('prod-select').value;
  if (!id) return;
  const suc = getSucursal();
  const dias = getPeriodo();

  try {
    const data = await api.get(
      `/predicciones/productos/${id}?dias_historial=${dias}&dias_futuro=30${suc ? `&id_sucursal=${suc}` : ''}`
    );

    // Update model badge
    const mb = document.getElementById('prod-model-badge');
    mb.innerHTML = data.metodo === 'polynomial_regression' ? '<i class="ph ph-ruler"></i> Regresión' : '<i class="ph ph-chart-bar"></i> Media Móvil';
    mb.style.display = 'inline-flex';

    // Stats
    document.getElementById('prod-stats').style.display = 'grid';
    document.getElementById('ps-stock').textContent   = formatNumber(data.stock_actual, 1) + ' u.';
    document.getElementById('ps-dias').textContent    = data.dias_hasta_quiebre != null ? `${data.dias_hasta_quiebre} días` : '∞';
    document.getElementById('ps-ingreso').textContent = formatCurrency(data.ingreso_proyectado_30d);

    // Hide empty message
    document.getElementById('prod-empty').style.display = 'none';

    // Chart
    destroyChart('product');
    const ctx = document.getElementById('chart-product').getContext('2d');
    const predLabels = data.prediccion.map(d => d.dia.slice(5));
    const predQty    = data.prediccion.map(d => d.cantidad_predicha);
    const predStock  = data.prediccion.map(d => d.stock_proyectado);

    charts.product = new Chart(ctx, {
      type: 'line',
      data: {
        labels: predLabels,
        datasets: [
          {
            label: 'Demanda diaria (u.)',
            data: predQty,
            borderColor: C.blue,
            backgroundColor: C.blueFill,
            fill: true,
            borderWidth: 2.5,
            pointRadius: 2,
            tension: 0.3,
            yAxisID: 'y',
          },
          {
            label: 'Stock proyectado',
            data: predStock,
            borderColor: data.dias_hasta_quiebre != null ? C.danger : C.green,
            backgroundColor: data.dias_hasta_quiebre != null ? C.dangerFill : C.greenFill,
            fill: true,
            borderWidth: 2,
            borderDash: [5, 3],
            pointRadius: 0,
            tension: 0.3,
            yAxisID: 'y2',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: true, position: 'bottom', labels: { usePointStyle: true, padding: 12 } },
          tooltip: {
            callbacks: {
              label: i => i.datasetIndex === 0
                ? `  Demanda: ${formatNumber(i.raw, 2)} u.`
                : `  Stock: ${formatNumber(i.raw, 1)} u.`,
            },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
          y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { stepSize: 1 }, position: 'left' },
          y2: { beginAtZero: true, position: 'right', grid: { display: false } },
        },
      },
    });
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
}

// ── Events ────────────────────────────────────────────────────────────────────

async function loadSucursales() {
  try {
    const suc = await api.get('/sucursales');
    const sel = document.getElementById('anl-sucursal');
    suc.forEach(s => {
      const o = document.createElement('option');
      o.value = s.id_sucursal; o.textContent = s.nombre;
      sel.appendChild(o);
    });
  } catch {}
}

document.getElementById('anl-sucursal').addEventListener('change', () => {
  productsCache = [];
  loadAll();
});
document.getElementById('anl-periodo').addEventListener('change', () => {
  productsCache = [];
  loadAll();
});

// Boot
loadSucursales().then(loadAll);
