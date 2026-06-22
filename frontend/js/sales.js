setActiveNav('sales');

// ── State ──────────────────────────────────────────────────────────────────

const cart = [];           // { producto, cantidad, precio_unitario_historico, subtotal }
let selectedClient = null;
let selectedPayment = 'Efectivo';
let searchTimeout = null;
let allProducts = [];

// ── Product search ─────────────────────────────────────────────────────────

document.getElementById('product-search').addEventListener('input', function () {
  clearTimeout(searchTimeout);
  const q = this.value.trim();
  const dropdown = document.getElementById('search-results');
  if (!q) { dropdown.classList.remove('visible'); return; }
  searchTimeout = setTimeout(() => doSearch(q), 280);   // <3s CU03
});

document.addEventListener('click', e => {
  if (!e.target.closest('.search-bar')) {
    document.getElementById('search-results').classList.remove('visible');
  }
});

async function doSearch(q) {
  const dropdown = document.getElementById('search-results');
  dropdown.classList.add('visible');
  dropdown.innerHTML = '<div style="padding:12px;text-align:center"><div class="spinner"></div></div>';
  try {
    if (!allProducts.length) {
      allProducts = await api.get('/productos?id_sucursal=1&limit=500');
    }
    const lq = q.toLowerCase();
    const matches = allProducts.filter(p =>
      p.nombre.toLowerCase().includes(lq) ||
      (p.sku && p.sku.toLowerCase().includes(lq)) ||
      (p.categoria && p.categoria.toLowerCase().includes(lq))
    ).slice(0, 12);

    if (!matches.length) {
      dropdown.innerHTML = '<div style="padding:14px;text-align:center;color:#7C8294;font-size:.85rem">Sin resultados</div>';
      return;
    }
    dropdown.innerHTML = matches.map(p => `
      <div class="search-result-item" onclick="addToCartById('${p.id_producto}')">
        <div>
          <div class="sri-name">${p.nombre}</div>
          <div class="sri-sku">${p.sku || 'Sin SKU'} · ${p.categoria || 'Sin categoría'}</div>
        </div>
        <div style="text-align:right">
          <div class="sri-price">${formatCurrency(p.precio_venta)}</div>
          <div class="sri-stock ${p.cantidad_actual <= p.stock_minimo_seguridad ? 'highlight-negative' : ''}">
            Stock: ${formatNumber(p.cantidad_actual, 1)} u.
          </div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    dropdown.innerHTML = `<div style="padding:14px;text-align:center;color:#ef4444">${e.message}</div>`;
  }
}

// ── Cart management ────────────────────────────────────────────────────────

function addToCartById(id_producto) {
  const producto = allProducts.find(p => String(p.id_producto) === String(id_producto));
  if (!producto) return;
  document.getElementById('search-results').classList.remove('visible');
  document.getElementById('product-search').value = '';

  const existing = cart.find(i => String(i.id_producto) === String(producto.id_producto));
  if (existing) {
    if (existing.cantidad >= producto.cantidad_actual) {
      showToast('Stock insuficiente para agregar más unidades', 'warning'); return;
    }
    existing.cantidad++;
    existing.subtotal = +(existing.cantidad * existing.precio_unitario_historico).toFixed(2);
  } else {
    if (producto.cantidad_actual <= 0) {
      showToast('Producto sin stock disponible', 'error'); return;
    }
    cart.push({
      id_producto: producto.id_producto,
      nombre: producto.nombre,
      cantidad: 1,
      precio_unitario_historico: producto.precio_venta,
      subtotal: +producto.precio_venta.toFixed(2),
      stock_max: producto.cantidad_actual,
    });
  }
  renderCart();
}

function changeQty(idx, delta) {
  const item = cart[idx];
  const newQty = item.cantidad + delta;
  if (newQty <= 0) { removeFromCart(idx); return; }
  if (newQty > item.stock_max) { showToast('Stock insuficiente', 'warning'); return; }
  item.cantidad = newQty;
  item.subtotal = +(newQty * item.precio_unitario_historico).toFixed(2);
  renderCart();
}

function removeFromCart(idx) {
  cart.splice(idx, 1);
  renderCart();
}

function renderCart() {
  const container = document.getElementById('cart-items');
  const totalsEl  = document.getElementById('cart-totals');
  const countEl   = document.getElementById('cart-count');

  if (!cart.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__icon"><i class="ph ph-shopping-cart"></i></div>
        <div class="empty-state__text">Buscá un producto para empezar</div>
      </div>`;
    totalsEl.style.display = 'none';
    countEl.textContent = '0 items';
    return;
  }

  container.innerHTML = cart.map((item, i) => `
    <div class="cart-item">
      <div class="cart-item__info">
        <div class="cart-item__name">${item.nombre}</div>
        <div class="cart-item__price">${formatCurrency(item.precio_unitario_historico)} c/u</div>
      </div>
      <div class="cart-item__qty">
        <button class="qty-btn" onclick="changeQty(${i}, -1)">−</button>
        <span class="qty-display">${item.cantidad}</span>
        <button class="qty-btn" onclick="changeQty(${i}, 1)">+</button>
      </div>
      <div class="cart-item__subtotal">${formatCurrency(item.subtotal)}</div>
      <button class="cart-remove" onclick="removeFromCart(${i})" title="Eliminar"><i class="ph ph-x"></i></button>
    </div>
  `).join('');

  const total = cart.reduce((s, i) => s + i.subtotal, 0);
  document.getElementById('cart-subtotal').textContent = formatCurrency(total);
  document.getElementById('cart-total').textContent    = formatCurrency(total);
  totalsEl.style.display = 'flex';
  countEl.textContent = `${cart.length} item${cart.length !== 1 ? 's' : ''}`;
}

// ── Payment ────────────────────────────────────────────────────────────────

function selectPayment(btn) {
  document.querySelectorAll('.payment-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedPayment = btn.dataset.pay;
}

// ── Checkout ───────────────────────────────────────────────────────────────

async function checkout() {
  if (!cart.length) { showToast('El carrito está vacío', 'warning'); return; }
  if (selectedPayment === 'Cuenta Corriente' && !selectedClient) {
    showToast('Cuenta Corriente requiere seleccionar un cliente', 'error'); return;
  }

  const btn = document.getElementById('btn-checkout');
  btn.disabled = true;
  btn.innerHTML = '<i class="ph ph-hourglass"></i> Procesando…';

  const payload = {
    id_cliente:  selectedClient?.id_cliente || null,
    id_usuario:  1,
    id_sucursal: 1,
    tipo_pago:   selectedPayment,
    tipo_venta:  'local',
    referencia:  document.getElementById('sale-ref').value.trim() || null,
    items: cart.map(i => ({ id_producto: i.id_producto, cantidad: i.cantidad })),
  };

  try {
    const result = await api.post('/ventas', payload);
    showToast(`<i class="ph-fill ph-check-circle"></i> Venta #${result.id_venta} guardada — ${formatCurrency(result.total)}`, 'success', 5000);
    cart.length = 0;
    renderCart();
    document.getElementById('sale-ref').value = '';
    allProducts = [];   // refresh cache
    loadSalesHistory();
    loadAlertBadge();   // update alerts after stock change
  } catch (e) {
    showToast('Error: ' + e.message, 'error', 6000);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="ph-fill ph-lightning"></i> Finalizar y Guardar';
  }
}

// ── Client ─────────────────────────────────────────────────────────────────

function clearClient() {
  selectedClient = null;
  document.getElementById('client-display').style.display = 'none';
}

let currentClientResults = [];

async function searchClients(q) {
  const container = document.getElementById('client-results');
  container.innerHTML = '<div class="spinner" style="margin:20px auto"></div>';
  try {
    const clients = await api.get(`/clientes${q ? `?nombre=${encodeURIComponent(q)}` : ''}?limit=20`);
    currentClientResults = clients;
    if (!clients.length) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state__text">Sin resultados</div></div>';
      return;
    }
    container.innerHTML = clients.map(c => `
      <div class="search-result-item" onclick="selectClientById('${c.id_cliente}')">
        <div>
          <div class="sri-name">${c.nombre} ${c.apellido || ''}</div>
          <div class="sri-sku">Tel: ${c.telefono || '—'} · CC: ${formatCurrency(c.saldo_cuenta_corriente)}</div>
        </div>
        <div style="text-align:right">
          <div class="sri-price ${c.saldo_cuenta_corriente > c.limite_credito * .9 && c.limite_credito > 0 ? 'highlight-negative' : ''}">
            Límite: ${formatCurrency(c.limite_credito)}
          </div>
        </div>
      </div>
    `).join('');
  } catch { container.innerHTML = '<div style="padding:14px;text-align:center;color:#ef4444">Error cargando clientes</div>'; }
}

function selectClientById(id) {
  const c = currentClientResults.find(client => String(client.id_cliente) === String(id));
  if (c) selectClient(c);
}

function selectClient(c) {
  selectedClient = c;
  document.getElementById('client-name-tag').textContent = `${selectedClient.nombre} ${selectedClient.apellido || ''}`.trim();
  document.getElementById('client-display').style.display = 'flex';
  closeModal('modal-client');
}

async function createClient() {
  const nombre   = document.getElementById('nc-nombre').value.trim();
  const apellido = document.getElementById('nc-apellido').value.trim();
  const telefono = document.getElementById('nc-tel').value.trim();
  const credito  = parseFloat(document.getElementById('nc-credito').value) || 0;

  if (!nombre) { showToast('El nombre es obligatorio', 'error'); return; }

  try {
    const c = await api.post('/clientes', { nombre, apellido, telefono, limite_credito: credito });
    selectClient(c);
    closeModal('modal-new-client');
    showToast(`Cliente "${c.nombre}" creado`, 'success');
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Sales history ──────────────────────────────────────────────────────────

async function loadSalesHistory() {
  const tbody = document.getElementById('sales-history-body');
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px"><div class="spinner"></div></td></tr>';
  try {
    const ventas = await api.get('/ventas?limit=30');
    if (!ventas.length) {
      tbody.innerHTML = '<tr class="no-data-row"><td colspan="6">Sin ventas registradas</td></tr>'; return;
    }
    const payBadge = { Efectivo: 'badge-green', Tarjeta: 'badge-blue', 'Cuenta Corriente': 'badge-yellow' };
    const stBadge  = { Pagado: 'badge-green', 'A cobrar / parcial': 'badge-yellow', Cancelado: 'badge-red' };
    tbody.innerHTML = ventas.map(v => `
      <tr class="sale-history-row" onclick="viewSaleDetail(${v.id_venta})">
        <td class="muted">#${v.id_venta}</td>
        <td>${formatDateTime(v.fecha_hora)}</td>
        <td>${v.id_cliente ? `Cliente #${v.id_cliente}` : '<span class="text-muted">Mostrador</span>'}</td>
        <td><span class="badge ${payBadge[v.tipo_pago] || 'badge-gray'}">${v.tipo_pago}</span></td>
        <td><span class="badge ${stBadge[v.estado] || 'badge-gray'}">${v.estado}</span></td>
        <td class="text-right fw-700">${formatCurrency(v.total)}</td>
      </tr>
    `).join('');
  } catch { tbody.innerHTML = '<tr class="no-data-row"><td colspan="6">Error cargando ventas</td></tr>'; }
}

async function viewSaleDetail(id) {
  openModal('modal-sale-detail');
  document.getElementById('sale-detail-title').textContent = `Detalle de Venta #${id}`;
  document.getElementById('sale-detail-body').innerHTML = '<div class="spinner" style="margin:20px auto"></div>';
  try {
    const v = await api.get(`/ventas/${id}/detalles`);
    document.getElementById('sale-detail-body').innerHTML = `
      <div class="flex gap-16 mb-16" style="flex-wrap:wrap">
        <span class="badge badge-gray">${formatDateTime(v.fecha_hora)}</span>
        <span class="badge badge-blue">${v.tipo_pago}</span>
        <span class="badge badge-green">${v.estado}</span>
        ${v.referencia ? `<span class="badge badge-gray">${v.referencia}</span>` : ''}
      </div>
      <table>
        <thead><tr><th>Producto</th><th style="text-align:right">Cant.</th><th style="text-align:right">P. Unit.</th><th style="text-align:right">Subtotal</th></tr></thead>
        <tbody>
          ${v.items.map(i => `
            <tr>
              <td>${i.nombre_producto}</td>
              <td class="text-right">${formatNumber(i.cantidad, 2)}</td>
              <td class="text-right muted">${formatCurrency(i.precio_unitario_historico)}</td>
              <td class="text-right fw-700">${formatCurrency(i.subtotal)}</td>
            </tr>
          `).join('')}
          <tr style="border-top:2px solid #1D2528">
            <td colspan="3" class="text-right fw-700">TOTAL</td>
            <td class="text-right fw-700" style="font-size:1.05rem">${formatCurrency(v.total)}</td>
          </tr>
        </tbody>
      </table>
    `;
  } catch (e) {
    document.getElementById('sale-detail-body').innerHTML = `<div class="text-muted text-center" style="padding:20px">${e.message}</div>`;
  }
}

// ── Client modal: load on open ─────────────────────────────────────────────

document.getElementById('modal-client').addEventListener('click', function(e) {
  if (e.target === this) closeModal('modal-client');
});

document.querySelector('[onclick="openModal(\'modal-client\')"]').addEventListener('click', () => {
  searchClients('');
});

document.getElementById('client-search-input').addEventListener('input', function() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => searchClients(this.value), 300);
});

// Boot
loadSalesHistory();
