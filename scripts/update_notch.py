import glob
import re

css_file = 'frontend/css/style.css'
js_file = 'frontend/js/api.js'
html_files = glob.glob('frontend/*.html')

# 1. Update JS
with open(js_file, 'r', encoding='utf-8') as f:
    js_content = f.read()

new_js = """function setActiveNav(page) {
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
}"""

js_content = re.sub(r'function setActiveNav\(page\)\s*\{.*?\n\}', new_js, js_content, flags=re.DOTALL)

with open(js_file, 'w', encoding='utf-8') as f:
    f.write(js_content)

# 2. Update CSS
with open(css_file, 'r', encoding='utf-8') as f:
    css_content = f.read()

new_css = """.sidebar__cutout {
  position: absolute;
  top: 110px; /* default, will be overridden */
  left: -1px;
  width: 30px;
  height: 80px;
  z-index: 10;
  transition: top 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar__cutout svg {
  display: block;
  width: 100%;
  height: 100%;
}
"""

# Replace the old sidebar__cutout rules
css_content = re.sub(r'\.sidebar__cutout\s*\{.*?\n\}', new_css, css_content, flags=re.DOTALL, count=1)
# Remove the pseudo elements CSS
css_content = re.sub(r'\.sidebar__cutout::before,\s*\.sidebar__cutout::after\s*\{.*?\n\}', '', css_content, flags=re.DOTALL)
css_content = re.sub(r'\.sidebar__cutout::before\s*\{.*?\n\}', '', css_content, flags=re.DOTALL)
css_content = re.sub(r'\.sidebar__cutout::after\s*\{.*?\n\}', '', css_content, flags=re.DOTALL)

with open(css_file, 'w', encoding='utf-8') as f:
    f.write(css_content)

# 3. Update HTML
svg_html = """<div class="sidebar__cutout">
    <svg width="30" height="80" viewBox="0 0 30 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M0,0 C0,25 30,15 30,40 C30,65 0,55 0,80 Z" fill="#F9F8F7" />
      <path d="M0,0 C0,25 30,15 30,40 C30,65 0,55 0,80" stroke="#3b82f6" stroke-width="1.5" />
    </svg>
  </div>"""

for html_file in html_files:
    if 'index.html' in html_file: continue
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    html = re.sub(r'<div class="sidebar__cutout">.*?</div>', svg_html, html, flags=re.DOTALL)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)

print("Done updating notch logic and shape!")
