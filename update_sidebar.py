import glob
import re

css_file = 'frontend/css/style.css'
html_files = glob.glob('frontend/*.html')

# 1. Update style.css
with open(css_file, 'r', encoding='utf-8') as f:
    css_content = f.read()

# Replace --sidebar-w
css_content = re.sub(r'--sidebar-w:\s*\d+px;', '--sidebar-w: 300px;', css_content)

# Define new sidebar CSS
new_sidebar_css = """
/* ══════════════════════════════════════════════════════════════════════
   SIDEBAR (REDESIGNED)
   ══════════════════════════════════════════════════════════════════════ */
.sidebar {
  width: 280px;
  height: calc(100vh - 40px);
  margin: 20px;
  background: linear-gradient(180deg, #1f272a 0%, #3e4d56 100%);
  display: flex;
  flex-direction: column;
  padding: 40px 30px;
  position: fixed;
  left: 0; top: 0;
  z-index: 100;
  border-radius: 40px;
  transition: width var(--t-slow);
}

.sidebar__cutout {
  position: absolute;
  top: 110px;
  left: -1px;
  width: 16px;
  height: 48px;
  background: var(--clr-light);
  border-radius: 0 16px 16px 0;
  z-index: 10;
}
.sidebar__cutout::before,
.sidebar__cutout::after {
  content: '';
  position: absolute;
  left: 0;
  width: 16px;
  height: 16px;
}
.sidebar__cutout::before {
  top: -16px;
  background: radial-gradient(circle at 16px 0px, transparent 15.5px, var(--clr-light) 16px);
}
.sidebar__cutout::after {
  bottom: -16px;
  background: radial-gradient(circle at 16px 16px, transparent 15.5px, var(--clr-light) 16px);
}

.sidebar__brand {
  display: flex;
  align-items: center;
  padding-left: 10px;
  margin-bottom: 50px;
}
.sidebar__logo {
  display: none;
}
.sidebar__name {
  font-size: 24px;
  font-weight: 700;
  color: var(--clr-white);
}
.sidebar__sub {
  font-size: 18px;
  font-weight: 300;
  color: var(--clr-white);
  margin-left: 6px;
  margin-top: 3px;
}

.sidebar__nav { flex: 1; display: flex; flex-direction: column; gap: 0; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 10px;
  border-radius: 0;
  color: #fff;
  font-size: 1.1rem;
  font-weight: 300;
  transition: opacity var(--t-fast);
  position: relative;
  cursor: pointer;
  opacity: 0.85;
}
.nav-item:hover { opacity: 1; background: transparent; }
.nav-item.active {
  background: transparent;
  color: #fff;
  opacity: 1;
}
.nav-icon { font-size: 24px; opacity: 1; }

.nav-divider {
  height: 1px;
  background: rgba(255,255,255,.05);
  margin: 0 10px;
}

.sidebar__footer {
  display: none;
}
"""

# Replace the sidebar CSS block
# We'll use regex to replace everything from /* SIDEBAR to the end of .nav-badge
# Wait, it's safer to just split by comments.
parts = css_content.split('/* ══════════════════════════════════════════════════════════════════════\n   SIDEBAR\n   ══════════════════════════════════════════════════════════════════════ */')
if len(parts) == 2:
    pre_sidebar = parts[0]
    post_sidebar = parts[1].split('/* ══════════════════════════════════════════════════════════════════════\n   MAIN LAYOUT\n   ══════════════════════════════════════════════════════════════════════ */')[1]
    
    new_css = pre_sidebar + new_sidebar_css + '\n/* ══════════════════════════════════════════════════════════════════════\n   MAIN LAYOUT\n   ══════════════════════════════════════════════════════════════════════ */\n' + post_sidebar
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(new_css)
    print("Updated CSS")

# 2. Update HTML files
new_sidebar_html = """<aside class="sidebar">
  <div class="sidebar__cutout"></div>
  <div class="sidebar__brand">
    <span class="sidebar__name">FARO</span>
    <span class="sidebar__sub">stock</span>
  </div>
  <nav class="sidebar__nav">
    <a href="/static/dashboard.html" class="nav-item" data-page="dashboard">
      <i class="ph ph-house nav-icon"></i> Inicio
    </a>
    <div class="nav-divider"></div>
    <a href="/static/inventory.html" class="nav-item" data-page="inventory">
      <i class="ph ph-wrench nav-icon"></i> Inventario
    </a>
    <div class="nav-divider"></div>
    <a href="/static/sales.html" class="nav-item" data-page="sales">
      <i class="ph ph-note-pencil nav-icon"></i> Ventas
    </a>
    <div class="nav-divider"></div>
    <a href="/static/projections.html" class="nav-item" data-page="projections">
      <i class="ph ph-eye nav-icon"></i> Proyecciones
      <span class="nav-badge" id="alert-badge" style="display:none">0</span>
    </a>
  </nav>
</aside>"""

for file_path in html_files:
    if 'index.html' in file_path:
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Replace the <aside> block
    html = re.sub(r'<aside class="sidebar">.*?</aside>', new_sidebar_html, html, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Updated {file_path}")

print("Done")
