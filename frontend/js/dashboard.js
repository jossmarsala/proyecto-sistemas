setActiveNav('dashboard');

let chartData = [];
let statsData = {};

async function loadDashboard() {
  const sucursal = document.getElementById('sucursal-select').value || null;
  const dias = document.getElementById('period-select').value || 30;

  try {
    // Parallel fetch
    const [stats, chart] = await Promise.all([
      api.get(`/ventas/stats/resumen${sucursal ? `?id_sucursal=${sucursal}` : ''}`),
      api.get(`/stats/grafico?dias=${dias}${sucursal ? `&id_sucursal=${sucursal}` : ''}`),
    ]);

    statsData = stats;
    chartData  = chart;

    renderKPIs(stats);
    renderRevenueChart(chart);
    renderTopProducts(stats.top_5_productos || []);
  } catch (e) {
    showToast('Error cargando dashboard: ' + e.message, 'error');
  }
}

function renderKPIs(s) {
  const grid = document.getElementById('kpi-grid');
  grid.innerHTML = `
    <div class="kpi-card kpi-card--dark fade-in">
      <span class="kpi-label">Ingresos Hoy</span>
      <span class="kpi-value">${formatCurrency(s.ingresos_hoy)}</span>
      <span class="kpi-delta"><i class="ph ph-calendar"></i> Jornada actual</span>
      <span class="kpi-icon"><i class="ph ph-money"></i></span>
    </div>
    <div class="kpi-card kpi-card--blue fade-in">
      <span class="kpi-label">Ingresos del Mes</span>
      <span class="kpi-value">${formatCurrency(s.ingresos_mes)}</span>
      <span class="kpi-delta">Mes en curso</span>
      <span class="kpi-icon"><i class="ph ph-calendar-blank"></i></span>
    </div>
    <div class="kpi-card kpi-card--pink fade-in">
      <span class="kpi-label">Total Ventas</span>
      <span class="kpi-value">${formatNumber(s.total_ventas)}</span>
      <span class="kpi-delta">Transacciones registradas</span>
      <span class="kpi-icon"><i class="ph ph-receipt"></i></span>
    </div>
    <div class="kpi-card kpi-card--accent fade-in">
      <span class="kpi-label">Ingresos Totales</span>
      <span class="kpi-value">${formatCurrency(s.ingresos_totales)}</span>
      <span class="kpi-delta">Histórico acumulado</span>
      <span class="kpi-icon"><i class="ph ph-chart-bar"></i></span>
    </div>
  `;
}

function renderRevenueChart(data) {
  setTimeout(() => drawLineChart('revenue-chart', data, 'dia', 'ingreso'), 50);
}

function renderTopProducts(productos) {
  if (!productos.length) return;
  const labels = productos.map(p => p.nombre);
  const values = productos.map(p => p.total_vendido);
  setTimeout(() => drawBarChart('top-products-chart', labels, values, '#2727BA'), 50);
}

async function loadAlerts() {
  const container = document.getElementById('alerts-container');
  container.innerHTML = '<div class="spinner" style="margin:20px auto"></div>';
  try {
    const alerts = await api.get('/alertas?solo_activas=true');
    if (!alerts.length) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon"><i class="ph-fill ph-check-circle"></i></div>
          <div class="empty-state__text">Sin alertas activas</div>
        </div>`;
      return;
    }
    container.innerHTML = alerts.map(a => {
      const isStock = a.tipo === 'stock_minimo';
      return `
        <div class="alert-item ${isStock ? 'alert-item--warning' : 'alert-item--danger'}" id="alert-${a.id_alerta}">
          <span class="alert-icon">${isStock ? '<i class="ph ph-package"></i>' : '<i class="ph ph-credit-card"></i>'}</span>
          <span class="alert-msg">${a.mensaje}</span>
          <button class="alert-btn-resolve" onclick="resolveAlert(${a.id_alerta})">✓</button>
        </div>`;
    }).join('');

    // Update badge
    const badge = document.getElementById('alert-badge');
    if (badge) { badge.textContent = alerts.length; badge.style.display = 'inline'; }
  } catch {
    container.innerHTML = '<div class="text-muted text-center" style="padding:20px">Error cargando alertas</div>';
  }
}

async function resolveAlert(id) {
  try {
    await api.patch(`/alertas/${id}/resolver`);
    document.getElementById(`alert-${id}`)?.remove();
    showToast('Alerta resuelta', 'success');
    loadAlertBadge();
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
    const ventas = await api.get('/ventas?limit=8');
    const tbody = document.getElementById('recent-sales-body');
    if (!ventas.length) {
      tbody.innerHTML = '<tr class="no-data-row"><td colspan="5">Sin ventas registradas</td></tr>';
      return;
    }
    tbody.innerHTML = ventas.map(v => {
      const badges = { Efectivo: 'badge-green', Tarjeta: 'badge-blue', 'Cuenta Corriente': 'badge-yellow' };
      return `<tr>
        <td class="muted">#${v.id_venta}</td>
        <td>${formatDateTime(v.fecha_hora)}</td>
        <td>${v.id_cliente ? `Cliente #${v.id_cliente}` : '<span class="text-muted">Mostrador</span>'}</td>
        <td><span class="badge ${badges[v.tipo_pago] || 'badge-gray'}">${v.tipo_pago}</span></td>
        <td class="text-right fw-700">${formatCurrency(v.total)}</td>
      </tr>`;
    }).join('');
  } catch {}
}

// Event listeners
document.getElementById('sucursal-select').addEventListener('change', loadDashboard);
document.getElementById('period-select').addEventListener('change', async () => {
  const dias = document.getElementById('period-select').value;
  const sucursal = document.getElementById('sucursal-select').value || null;
  try {
    chartData = await api.get(`/stats/grafico?dias=${dias}${sucursal ? `&id_sucursal=${sucursal}` : ''}`);
    renderRevenueChart(chartData);
  } catch {}
});

window.addEventListener('resize', () => {
  if (chartData.length) renderRevenueChart(chartData);
  if (statsData.top_5_productos?.length) renderTopProducts(statsData.top_5_productos);
});

// Boot
loadSucursales();
loadDashboard();
loadAlerts();
loadRecentSales();
