setActiveNav('inventory');

let allProducts = [];
let filtered    = [];
let currentCat  = '';

// ── Load ────────────────────────────────────────────────────────────────────

async function loadInventory() {
  try {
    allProducts = await api.get('/productos?id_sucursal=1&solo_activos=false&limit=500');
    filtered = [...allProducts];
    renderKPIs();
    renderCategoryFilters();
    renderTable(filtered);
  } catch (e) {
    showToast('Error cargando inventario: ' + e.message, 'error');
  }
}

function renderKPIs() {
  const container = document.getElementById('inv-kpis');
  if (!container) return;
  const total   = allProducts.length;
  const activos = allProducts.filter(p => p.activo).length;
  const bajo    = allProducts.filter(p => p.cantidad_actual <= p.stock_minimo_seguridad).length;
  const valorStock = allProducts.reduce((s, p) => s + p.cantidad_actual * p.precio_costo, 0);

  container.innerHTML = `
    <div class="bento-card bento-card--dark bento-flex-col">
      <div class="bento-card-title bento-card-title-white">Total Productos</div>
      <div class="bento-card-value-large" style="margin-top:auto">${total}</div>
      <div style="font-size: 0.85rem; color: var(--clr-gray); font-weight: 500; margin-top: 4px;">${activos} activos</div>
    </div>
    <div class="bento-card bento-card--white bento-glow-yellow bento-flex-col">
      <div class="bento-card-title">Stock Bajo</div>
      <div class="bento-card-value-large" style="margin-top:auto">${bajo}</div>
      <div style="font-size: 0.85rem; color: var(--clr-gray); font-weight: 500; margin-top: 4px;">Bajo mínimo de seguridad</div>
    </div>
    <div class="bento-card bento-card--white bento-glow-blue-bottom bento-flex-col">
      <div class="bento-card-title">Valor en Stock</div>
      <div class="bento-card-value" style="margin-top:auto">${formatCurrency(valorStock)}</div>
      <div style="font-size: 0.85rem; color: var(--clr-gray); font-weight: 500; margin-top: 4px;">Precio costo</div>
    </div>
    <div class="bento-card bento-card--white bento-glow-yellow bento-flex-col">
      <div class="bento-card-title">Categorías</div>
      <div class="bento-card-value-large" style="margin-top:auto">${new Set(allProducts.map(p=>p.categoria).filter(Boolean)).size}</div>
      <div style="font-size: 0.85rem; color: var(--clr-gray); font-weight: 500; margin-top: 4px;">Familias de productos</div>
    </div>
  `;
}

function renderCategoryFilters() {
  const cats = [...new Set(allProducts.map(p => p.categoria).filter(Boolean))].sort();
  const container = document.getElementById('cat-filters');
  container.innerHTML = `<span class="filter-tag active" data-cat="" onclick="selectCat(this)">Todos</span>` +
    cats.map(c => `<span class="filter-tag" data-cat="${c}" onclick="selectCat(this)">${c}</span>`).join('');
}

function selectCat(el) {
  document.querySelectorAll('#cat-filters .filter-tag').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  currentCat = el.dataset.cat;
  filterTable();
}

function filterTable(q) {
  const query  = (q ?? document.getElementById('inv-search').value).toLowerCase();

  filtered = allProducts.filter(p => {
    const matchQ = !query || p.nombre.toLowerCase().includes(query) ||
                   (p.sku && p.sku.toLowerCase().includes(query)) ||
                   (p.categoria && p.categoria.toLowerCase().includes(query));
    const matchC = !currentCat || p.categoria === currentCat;
    return matchQ && matchC;
  });

  renderTable(filtered);
}

function renderTable(products) {
  const tbody = document.getElementById('product-tbody');
  if (!products.length) {
    tbody.innerHTML = '<tr class="no-data-row"><td colspan="7">Sin productos</td></tr>';
    return;
  }
  tbody.innerHTML = products.map(p => {
    const stockPct    = p.stock_minimo_seguridad > 0 ? Math.min((p.cantidad_actual / p.stock_minimo_seguridad) * 50, 100) : 100;
    const stockClass  = p.cantidad_actual <= 0 ? 'danger' : p.cantidad_actual <= p.stock_minimo_seguridad ? 'warn' : 'ok';
    const margin      = p.precio_costo > 0 ? ((p.precio_venta - p.precio_costo) / p.precio_costo * 100).toFixed(0) : null;
    return `<tr>
      <td class="muted font-mono" style="font-size:.78rem">${p.sku || '—'}</td>
      <td><span class="fw-700">${p.nombre}</span></td>
      <td><span class="badge badge-gray">${p.categoria || '—'}</span></td>
      <td class="text-right muted">${formatCurrency(p.precio_costo)}</td>
      <td class="text-right fw-700">
        ${formatCurrency(p.precio_venta)}
        ${margin != null ? `<span class="badge badge-green" style="margin-left:4px;font-size:.65rem">+${margin}%</span>` : ''}
      </td>
      <td style="min-width:130px">
        <div class="stock-bar-wrap">
          <div class="stock-bar"><div class="stock-bar__fill stock-bar__fill--${stockClass}" style="width:${stockPct}%"></div></div>
          <span style="font-size:.8rem;font-weight:700;min-width:40px;text-align:right">${formatNumber(p.cantidad_actual,1)}</span>
        </div>
        <div style="font-size:.68rem;color:#7C8294;margin-top:2px">mín: ${p.stock_minimo_seguridad}</div>
      </td>
      <td style="text-align:center">
        <button class="btn btn-ghost btn-sm" onclick="openEditProduct(${p.id_producto})"><i class="ph ph-pencil-simple"></i> Editar</button>
      </td>
    </tr>`;
  }).join('');
}

// ── Create product ─────────────────────────────────────────────────────────

async function createProduct() {
  const nombre = document.getElementById('np-nombre').value.trim();
  const sku    = document.getElementById('np-sku').value.trim();
  const cat    = document.getElementById('np-cat').value.trim();
  const costo  = parseFloat(document.getElementById('np-costo').value) || 0;
  const venta  = parseFloat(document.getElementById('np-venta').value) || 0;
  const stock  = parseFloat(document.getElementById('np-stock').value) || 0;
  const minimo = parseFloat(document.getElementById('np-min').value)   || 0;

  if (!nombre) { showToast('El nombre es obligatorio', 'error'); return; }
  if (costo <= 0 || venta <= 0) { showToast('Los precios deben ser mayores a 0', 'error'); return; }

  try {
    await api.post('/productos', {
      nombre, sku: sku || null, categoria: cat || null,
      precio_costo: costo, precio_venta: venta,
      stock_inicial: stock, stock_minimo_seguridad: minimo,
      id_sucursal: 1,
    });
    showToast(`Producto "${nombre}" creado`, 'success');
    closeModal('modal-new-product');
    ['np-nombre','np-sku','np-cat','np-costo','np-venta','np-stock','np-min'].forEach(id => {
      document.getElementById(id).value = '';
    });
    allProducts = [];
    await loadInventory();
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Edit product ─────────────────────────────────────────────────────────────

function openEditProduct(id) {
  const p = allProducts.find(x => x.id_producto === id);
  if (!p) return;
  document.getElementById('edit-product-id').value = p.id_producto;
  document.getElementById('edit-product-title').textContent = `Editar Producto: ${p.nombre}`;
  document.getElementById('ep-stock').value = p.cantidad_actual;
  document.getElementById('ep-costo').value = p.precio_costo;
  document.getElementById('ep-venta').value = p.precio_venta;
  openModal('modal-edit-product');
}

async function saveProductEdit() {
  const id    = parseInt(document.getElementById('edit-product-id').value);
  const stock = parseFloat(document.getElementById('ep-stock').value);
  const costo = parseFloat(document.getElementById('ep-costo').value);
  const venta = parseFloat(document.getElementById('ep-venta').value);

  if (!id || isNaN(stock) || isNaN(costo) || isNaN(venta)) { showToast('Datos inválidos', 'error'); return; }

  try {
    await api.put(`/productos/${id}`, { cantidad_actual: stock, precio_costo: costo, precio_venta: venta, id_sucursal: 1 });
    showToast('Producto actualizado correctamente', 'success');
    closeModal('modal-edit-product');
    const idx = allProducts.findIndex(p => p.id_producto === id);
    if (idx >= 0) { 
      allProducts[idx].cantidad_actual = stock; 
      allProducts[idx].precio_costo = costo; 
      allProducts[idx].precio_venta = venta; 
    }
    filterTable();
  } catch (e) { showToast(e.message, 'error'); }
}

// ── Global price update (CU05) ─────────────────────────────────────────────

async function applyGlobalPrice() {
  const cat = document.getElementById('gp-cat').value.trim();
  const pct = parseFloat(document.getElementById('gp-pct').value) / 100;

  const targets = cat ? allProducts.filter(p => p.categoria === cat) : allProducts;
  if (!targets.length) { showToast('Sin productos en esa categoría', 'warning'); return; }

  if (!confirm(`¿Aplicar un ${(pct*100).toFixed(0)}% de aumento a ${targets.length} producto(s)${cat ? ` en "${cat}"` : ''}?`)) return;

  try {
    let ok = 0;
    for (const p of targets) {
      const newCosto = +(p.precio_costo * (1 + pct)).toFixed(2);
      const newVenta = +(p.precio_venta * (1 + pct)).toFixed(2);
      await api.put(`/productos/${p.id_producto}/precio`, { precio_costo: newCosto, precio_venta: newVenta });
      ok++;
    }
    showToast(`<i class="ph-fill ph-check-circle"></i> ${ok} productos actualizados`, 'success');
    closeModal('modal-price-update');
    allProducts = [];
    await loadInventory();
  } catch (e) { showToast('Error en actualización masiva: ' + e.message, 'error'); }
}

loadInventory();
