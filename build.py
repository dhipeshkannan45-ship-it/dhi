"""
Builds two artefacts:
  1. dist/          — one self-contained .html per page (topbar + sync inlined)
  2. dashboard.html — single file with all 5 pages in srcdoc iframes + bottom nav

Run:  python build.py
Output: ~/Desktop/dashboard.html
"""
import base64, pathlib, re, shutil

ROOT  = pathlib.Path(__file__).parent
DIST  = ROOT / 'dist'
OUT   = pathlib.Path.home() / 'Desktop' / 'dashboard.html'
PAGES = [
    ('Goals',   'index.html',     'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'),
    ('Health',  'health.html',    'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'),
    ('Gym',     'gym.html',       'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z'),
    ('Finance', 'finance.html',   'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z'),
    ('Water',   'po-water.html',  'M12 21.593c-5.63-5.539-11-10.297-11-14.402 0-3.791 3.068-5.191 5.281-5.191 1.312 0 4.151.501 5.719 4.457 1.59-3.968 4.464-4.447 5.726-4.447 2.54 0 5.274 1.621 5.274 5.181 0 4.069-5.136 8.625-11 14.402z'),
]

# utf-8-sig strips the BOM that Windows text editors add
def read(path):
    return pathlib.Path(path).read_text(encoding='utf-8-sig')

# Escape </ so </script> inside inlined JS never prematurely closes the tag.
# The HTML parser reads raw bytes and never sees </script when it's </script.
# JavaScript interprets < as < inside string literals; in comments it's harmless.
def esc(js):
    return js.replace('</', '\\u003C/')

topbar = read(ROOT / 'topbar.js')
sync   = read(ROOT / 'sync.js')

# Topbar with early-exit when running inside an iframe (single-file mode)
topbar_embedded = topbar.replace(
    "(function () {\n  'use strict';",
    "(function () {\n  'use strict';\n  if (window.self !== window.top) return;",
    1
)

def inline(src, tb):
    sync_block  = '<script>\n' + esc(sync) + '\n</script>'
    topbar_block = '<script>\n' + esc(tb)  + '\n</script>'
    src = re.sub(r'<script\s+src=["\']sync\.js["\'](?:\s+defer)?>\s*</script>',
                 lambda _: sync_block, src)
    src = re.sub(r'<script\s+src=["\']topbar\.js["\'](?:\s+defer)?>\s*</script>',
                 lambda _: topbar_block, src)
    return src

# ── 1. Build dist/ (standalone pages) ───────────────────────────────────────
shutil.rmtree(DIST, ignore_errors=True)
DIST.mkdir()

for _label, page, _icon in PAGES:
    src = inline(read(ROOT / page), topbar)
    (DIST / page).write_text(src, encoding='utf-8')
    print(f'  dist/{page}')

# ── 2. Build embedded versions (topbar suppressed) ──────────────────────────
embedded = {}
for _label, page, _icon in PAGES:
    src = inline(read(ROOT / page), topbar_embedded)
    key = page.replace('.html', '').replace('po-water', 'water').replace('index', 'goals')
    embedded[key] = base64.b64encode(src.encode('utf-8')).decode('ascii')

# ── 3. Compose dashboard.html ────────────────────────────────────────────────
def page_key(page):
    return page.replace('.html','').replace('po-water','water').replace('index','goals')

nav_buttons = ''
for label, page, icon in PAGES:
    k = page_key(page)
    nav_buttons += f'''
    <button id="btn-{k}" onclick="show('{k}')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="{icon}"/>
      </svg>
      {label}
    </button>'''

page_data_js = 'const PAGES = {\n'
for label, page, _icon in PAGES:
    k = page_key(page)
    page_data_js += f"  '{k}': '{embedded[k]}',\n"
page_data_js += '};'

frame_tags = ''.join(f'    <iframe id="f-{page_key(p)}" title="{l}"></iframe>\n'
                     for l, p, _ in PAGES)

dashboard = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a0a0b">
<title>Dashboard</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;background:#0a0a0b;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Inter",sans-serif}}
.frames{{position:fixed;top:0;left:0;right:0;bottom:calc(56px + env(safe-area-inset-bottom))}}
iframe{{width:100%;height:100%;border:none;display:none;background:#0a0a0b}}
iframe.active{{display:block}}
nav{{
  position:fixed;bottom:0;left:0;right:0;
  height:calc(56px + env(safe-area-inset-bottom));
  padding-bottom:env(safe-area-inset-bottom);
  background:#0a0a0b;
  border-top:1px solid rgba(255,255,255,0.07);
  display:flex;
}}
nav button{{
  flex:1;background:none;border:none;
  color:rgba(255,255,255,0.35);
  font-family:inherit;font-size:9px;font-weight:700;
  letter-spacing:.12em;text-transform:uppercase;
  cursor:pointer;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;
  -webkit-tap-highlight-color:transparent;
  transition:color .15s;
}}
nav button svg{{width:21px;height:21px;flex-shrink:0}}
nav button.active{{color:#FAFAFA}}
nav button.active svg{{filter:drop-shadow(0 0 6px rgba(110,231,183,.5))}}
.loader{{
  position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  color:rgba(255,255,255,.2);font-size:13px;letter-spacing:.1em
}}
</style>
</head>
<body>
<div class="frames">
{frame_tags}<span class="loader" id="loader">Loading…</span>
</div>
<nav>{nav_buttons}
</nav>
<script>
{page_data_js}

function b64utf8(str){{
  const bytes=Uint8Array.from(atob(str),c=>c.charCodeAt(0));
  return new TextDecoder('utf-8').decode(bytes);
}}

let current=null;
function show(name){{
  if(current===name)return;
  if(current){{
    document.getElementById('f-'+current).classList.remove('active');
    document.getElementById('btn-'+current).classList.remove('active');
  }}
  const frame=document.getElementById('f-'+name);
  const loader=document.getElementById('loader');
  if(!frame.srcdoc){{
    if(loader)loader.style.display='block';
    frame.srcdoc=b64utf8(PAGES[name]);
    frame.onload=()=>{{if(loader)loader.style.display='none';}};
  }}
  frame.classList.add('active');
  document.getElementById('btn-'+name).classList.add('active');
  current=name;
}}

show('{page_key(PAGES[0][1])}');
</script>
</body>
</html>'''

OUT.write_text(dashboard, encoding='utf-8')
size_kb = round(OUT.stat().st_size / 1024)
print(f'\ndashboard.html -> Desktop ({size_kb} KB)')
print('AirDrop or email it, open in Safari/Chrome.')
