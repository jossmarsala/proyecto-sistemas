setActiveNav('projections');

let simTimeout = null;
let trendData  = [];

function showTab(name, btn) {
  document.querySelectorAll('.proj-section').forEach(s => s.classList.remove('visible'));
  document.querySelectorAll('.proj-tab').forEach(b => b.classList.remove('active'));
  document.getElementById(`tab-${name}`).classList.add('visible');
  btn.classList.add('active');

  if (name === 'stockbreak') loadStockBreak();
  if (name === 'trend')      loadTrendChart();
}

async function loadStockBreak() {
  const suc = document.getElementById('proj-sucursal').value || 1;
  const win = document.getElementById('proj-ventana').value || 30;
  const tbody = document.getElementById('sb-tbody');
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px"><div class="spinner"></div></td></tr>';

  try {
    const data = await api.get(`/productos/prediccion-quiebre?id_sucursal=${suc}&ventana_dias=${win}`);
    renderSBKPIs(data);
    renderSBTable(data);
  } catch (e) {
    tbody.innerHTML = `<tr class="no-data-row"><td colspan="6">${e.message}</td></tr>`;
  }
}

function renderSBKPIs(data) {
  const criticos = data.filter(d => d.alerta_quiebre).length;
  const sinHistorial = data.filter(d => d.dias_restantes == null).length;
  const conStock = data.filter(d => d.stock_actual > 0).length;

  document.getElementById('sb-kpis').innerHTML = `
    <div class="kpi-card kpi-card--dark">
      <span class="kpi-label">Productos analizados</span>
      <span class="kpi-value">${data.length}</span>
      <span class="kpi-delta">${conStock} con stock activo</span>
    </div>
    <div class="kpi-card kpi-card--pink">
      <span class="kpi-label"><i class="ph-fill ph-warning"></i> Quiebre inminente</span>
      <span class="kpi-value">${criticos}</span>
      <span class="kpi-delta">Bajo tiempo de reposición</span>
    </div>
    <div class="kpi-card kpi-card--blue">
      <span class="kpi-label">Sin historial</span>
      <span class="kpi-value">${sinHistorial}</span>
      <span class="kpi-delta">No se puede predecir</span>
    </div>
  `;
}

function renderSBTable(data) {
  const tbody = document.getElementById('sb-tbody');
  if (!data.length) {
    tbody.innerHTML = '<tr class="no-data-row"><td colspan="6">Sin productos para analizar</td></tr>';
    return;
  }

  const sorted = [...data].sort((a, b) => {
    if (a.alerta_quiebre && !b.alerta_quiebre) return -1;
    if (!a.alerta_quiebre && b.alerta_quiebre) return 1;
    if (a.dias_restantes == null) return 1;
    if (b.dias_restantes == null) return -1;
    return a.dias_restantes - b.dias_restantes;
  });

  tbody.innerHTML = sorted.map(d => {
    const diasStr = d.dias_restantes != null ? `${d.dias_restantes} días` : '—';
    const statusBadge = d.alerta_quiebre
      ? '<span class="badge badge-red"><i class="ph-fill ph-warning-circle"></i> Crítico</span>'
      : d.dias_restantes == null
        ? '<span class="badge badge-gray">Sin datos</span>'
        : '<span class="badge badge-green"><i class="ph-fill ph-check-circle"></i> OK</span>';

    return `<tr ${d.alerta_quiebre ? 'style="background:#fef2f2"' : ''}>
      <td class="fw-700">${d.nombre}</td>
      <td class="text-right">${formatNumber(d.stock_actual, 2)}</td>
      <td class="text-right muted">${d.promedio_diario > 0 ? formatNumber(d.promedio_diario, 3) : '—'}</td>
      <td class="text-right ${d.alerta_quiebre ? 'highlight-negative' : d.dias_restantes != null ? 'fw-700' : 'text-muted'}">
        ${diasStr}
      </td>
      <td class="text-right muted">${d.tiempo_reposicion_dias} días</td>
      <td style="text-align:center">${statusBadge}</td>
    </tr>`;
  }).join('');
}

function scheduleSimulation() {
  clearTimeout(simTimeout);
  simTimeout = setTimeout(runSimulation, 500);
}

async function runSimulation() {
  const inf    = parseFloat(document.getElementById('slider-inflacion').value) || 0;
  const dem    = parseFloat(document.getElementById('slider-demanda').value) || 0;
  const costos = parseFloat(document.getElementById('input-costos').value) || 0;
  const suc    = document.getElementById('proj-sucursal').value || null;
  const win    = document.getElementById('proj-ventana').value || 30;

  try {
    const result = await api.get(
      `/simulacion?inflacion_pct=${inf}&variacion_demanda_pct=${dem}&costos_fijos_adicionales=${costos}` +
      `${suc ? `&id_sucursal=${suc}` : ''}&ventana_dias=${win}`
    );
    renderSimResult(result);
  } catch (e) {
    showToast('Error en simulación: ' + e.message, 'error');
  }
}

function renderSimResult(r) {
  
  const isPos = r.delta.rentabilidad >= 0;
  document.getElementById('sim-rent-val').textContent = formatCurrency(r.simulado.rentabilidad);
  document.getElementById('sim-rent-delta').innerHTML =
    `<span class="${isPos ? 'delta-positive' : 'delta-negative'}">
      ${isPos ? '▲' : '▼'} ${formatCurrency(Math.abs(r.delta.rentabilidad))} (${isPos ? '+' : ''}${r.delta.porcentaje}%) vs actual
    </span>`;

  document.getElementById('sim-ing-act').textContent = formatCurrency(r.actual.ingreso_total);
  document.getElementById('sim-ing-sim').textContent = formatCurrency(r.simulado.ingreso_total);
  document.getElementById('sim-cos-act').textContent = formatCurrency(r.actual.costo_total);
  document.getElementById('sim-cos-sim').textContent = formatCurrency(r.simulado.costo_total);

  const card = document.getElementById('sim-result-card');
  card.style.background = isPos
    ? 'linear-gradient(135deg, #1D2528 0%, #1a3a1a 100%)'
    : 'linear-gradient(135deg, #1D2528 0%, #3a1a1a 100%)';

  const tbody = document.getElementById('sim-products-tbody');
  if (!r.productos.length) {
    tbody.innerHTML = '<tr class="no-data-row"><td colspan="4">Sin datos de productos</td></tr>';
    return;
  }
  const sorted = [...r.productos].sort((a, b) => Math.abs(b.delta_ingreso) - Math.abs(a.delta_ingreso));
  tbody.innerHTML = sorted.map(p => `
    <tr>
      <td class="fw-700">${p.nombre}</td>
      <td class="text-right">${formatCurrency(p.ingreso_actual)}</td>
      <td class="text-right">${formatCurrency(p.ingreso_simulado)}</td>
      <td class="text-right ${p.delta_ingreso >= 0 ? 'highlight-positive' : 'highlight-negative'}">
        ${p.delta_ingreso >= 0 ? '+' : ''}${formatCurrency(p.delta_ingreso)}
      </td>
    </tr>
  `).join('');
}

async function loadTrendChart() {
  const dias = document.getElementById('trend-period').value || 30;
  const suc  = document.getElementById('proj-sucursal').value || null;
  document.getElementById('trend-days-label').textContent = dias;

  const tbody = document.getElementById('trend-tbody');
  tbody.innerHTML = '<tr class="no-data-row"><td colspan="3">Cargando…</td></tr>';

  try {
    trendData = await api.get(`/stats/grafico?dias=${dias}${suc ? `&id_sucursal=${suc}` : ''}`);
    setTimeout(() => drawLineChart('trend-chart', trendData, 'dia', 'ingreso', '#2727BA'), 50);

    const withSales = trendData.filter(d => d.ingreso > 0);
    if (!withSales.length) {
      tbody.innerHTML = '<tr class="no-data-row"><td colspan="3">Sin ventas en el período</td></tr>';
    } else {
      tbody.innerHTML = withSales.reverse().map(d => `
        <tr>
          <td>${formatDate(d.dia)}</td>
          <td class="text-right">${d.num_ventas}</td>
          <td class="text-right fw-700">${formatCurrency(d.ingreso)}</td>
        </tr>
      `).join('');
    }
  } catch (e) {
    tbody.innerHTML = `<tr class="no-data-row"><td colspan="3">${e.message}</td></tr>`;
  }
}

window.addEventListener('resize', () => {
  if (document.getElementById('tab-trend').classList.contains('visible') && trendData.length) {
    drawLineChart('trend-chart', trendData, 'dia', 'ingreso', '#2727BA');
  }
});

async function loadSucursales() {
  try {
    const suc = await api.get('/sucursales');
    const sel = document.getElementById('proj-sucursal');
    sel.innerHTML = suc.map(s => `<option value="${s.id_sucursal}">${s.nombre}</option>`).join('');
  } catch {}
}

loadSucursales().then(() => {
  loadStockBreak();
});

document.getElementById('proj-sucursal').addEventListener('change', () => {
  const tab = document.querySelector('.proj-section.visible');
  if (tab?.id === 'tab-stockbreak') loadStockBreak();
  if (tab?.id === 'tab-trend') loadTrendChart();
  if (tab?.id === 'tab-whatif') runSimulation();
});

document.getElementById('proj-ventana').addEventListener('change', () => {
  const tab = document.querySelector('.proj-section.visible');
  if (tab?.id === 'tab-stockbreak') loadStockBreak();
  if (tab?.id === 'tab-whatif') runSimulation();
});
