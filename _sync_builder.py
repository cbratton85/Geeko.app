"""
_sync_builder.py — run once to re-embed index.html + rotation.html into html_builder.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX_HTML    = HERE / "index.html"
ROTATION_HTML = HERE / "rotation.html"
BUILDER_PY    = HERE / "html_builder.py"

index_src    = INDEX_HTML.read_text(encoding="utf-8")
rotation_src = ROTATION_HTML.read_text(encoding="utf-8")

# Escape any triple-quote sequences that would break the raw string
def safe_embed(s):
    # Replace """ with the unicode escape so it can't accidentally close the raw string
    return s.replace('"""', '""\u200b"')   # zero-width space between last two quotes

index_safe    = safe_embed(index_src)
rotation_safe = safe_embed(rotation_src)

ROTATION_VIEWS = """{
    "sectors": {
        "label": "Sectors",
        "benchmark": "SHV",
        "tickers": [
            {"ticker": "XLK",  "name": "Technology",    "color": "#00AAFF"},
            {"ticker": "XLF",  "name": "Financials",    "color": "#FF6600"},
            {"ticker": "XLV",  "name": "Healthcare",    "color": "#FF3366"},
            {"ticker": "XLY",  "name": "Cons. Disc.",   "color": "#FFAA00"},
            {"ticker": "XLI",  "name": "Industrials",   "color": "#AAAACC"},
            {"ticker": "XLC",  "name": "Comm. Svcs",    "color": "#CC44FF"},
            {"ticker": "XLE",  "name": "Energy",        "color": "#FF4400"},
            {"ticker": "XLB",  "name": "Materials",     "color": "#BB8866"},
            {"ticker": "XLP",  "name": "Cons. Staples", "color": "#33CC66"},
            {"ticker": "XLRE", "name": "Real Estate",   "color": "#00CCAA"},
            {"ticker": "XLU",  "name": "Utilities",     "color": "#8855DD"},
        ],
    },
    "crossAsset": {
        "label": "Cross-Asset",
        "benchmark": "SHV",
        "tickers": [
            {"ticker": "SPY",  "name": "S&P 500",    "color": "#EAEAEA"},
            {"ticker": "DIA",  "name": "Dow Jones",  "color": "#00CCAA"},
            {"ticker": "QQQ",  "name": "Nasdaq 100", "color": "#00AAFF"},
            {"ticker": "IWM",  "name": "Small Caps", "color": "#FF6600"},
            {"ticker": "MDY",  "name": "Mid Caps",   "color": "#AADDFF"},
            {"ticker": "VEU",  "name": "Intl Stocks","color": "#33CC66"},
            {"ticker": "TLT",  "name": "20Y+ Bonds", "color": "#AAAACC"},
            {"ticker": "HYG",  "name": "High Yield", "color": "#CC44FF"},
            {"ticker": "GLD",  "name": "Gold",       "color": "#FFD700"},
            {"ticker": "SLV",  "name": "Silver",     "color": "#C0C0C0"},
            {"ticker": "USO",  "name": "Crude Oil",  "color": "#FF4400"},
            {"ticker": "CPER", "name": "Copper",     "color": "#BB8866"},
            {"ticker": "IBIT", "name": "Bitcoin",    "color": "#FF9900"},
        ],
    },
}"""

output = f'''"""
html_builder.py — Gekko V2
Generates index.html and DATA/gekko_app_rotation.html from embedded templates.
Called automatically by server.py at startup if either file is missing.
All data is served via /api/* endpoints — HTML is a static shell.
"""
import json, time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
INDEX_HTML    = _HERE / "index.html"
ROTATION_HTML = _HERE / "rotation.html"   # served from root by server.py

# ---------------------------------------------------------------------------
# ROTATION VIEWS CONFIG (copied from gekko_app.py)
# ---------------------------------------------------------------------------
ROTATION_VIEWS = {ROTATION_VIEWS}

# ---------------------------------------------------------------------------
# ROTATION HTML TEMPLATE
# ---------------------------------------------------------------------------


def build_rotation_html(rotation_json, rotation_views_json):
    return """{rotation_safe}"""


# ---------------------------------------------------------------------------
# INDEX HTML TEMPLATE
# ---------------------------------------------------------------------------


def build_index_html():
    return """{index_safe}"""


# ---------------------------------------------------------------------------
# WRITE HELPERS
# ---------------------------------------------------------------------------

def maybe_write_index():
    if not INDEX_HTML.exists():
        INDEX_HTML.write_text(build_index_html(), encoding="utf-8")
        print(f"[html_builder] Regenerated {{INDEX_HTML}}")

def maybe_write_rotation(rotation_data=None, rotation_views=None):
    if not ROTATION_HTML.exists():
        rj = json.dumps(rotation_data or {{}})
        vj = json.dumps(rotation_views or ROTATION_VIEWS)
        ROTATION_HTML.write_text(build_rotation_html(rj, vj), encoding="utf-8")
        print(f"[html_builder] Regenerated {{ROTATION_HTML}}")

def maybe_write_all(rotation_data=None, rotation_views=None):
    maybe_write_index()
    maybe_write_rotation(rotation_data, rotation_views)
'''

# Use triple-quote delimiters that won't appear in our content
# We already escaped them above. Now write out with real triple-quotes.
# The f-string above used """ but we need to make sure the content
# replacement uses the actual triple-quotes we want, not f-string issues.
# Re-do carefully:

header = '''\
"""
html_builder.py — Gekko V2
Generates index.html and DATA/gekko_app_rotation.html from embedded templates.
Called automatically by server.py at startup if either file is missing.
All data is served via /api/* endpoints — HTML is a static shell.
"""
import json, time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
INDEX_HTML    = _HERE / "index.html"
ROTATION_HTML = _HERE / "rotation.html"   # served from root by server.py

# ---------------------------------------------------------------------------
# ROTATION VIEWS CONFIG (copied from gekko_app.py)
# ---------------------------------------------------------------------------
ROTATION_VIEWS = ''' + ROTATION_VIEWS + '''

# ---------------------------------------------------------------------------
# ROTATION HTML TEMPLATE
# ---------------------------------------------------------------------------


def build_rotation_html(rotation_json, rotation_views_json):
    return r"""''' + rotation_safe + '''"""


# ---------------------------------------------------------------------------
# INDEX HTML TEMPLATE
# ---------------------------------------------------------------------------


def build_index_html():
    return r"""''' + index_safe + '''"""


# ---------------------------------------------------------------------------
# WRITE HELPERS
# ---------------------------------------------------------------------------

def maybe_write_index():
    if not INDEX_HTML.exists():
        INDEX_HTML.write_text(build_index_html(), encoding="utf-8")
        print(f"[html_builder] Regenerated {INDEX_HTML}")

def maybe_write_rotation(rotation_data=None, rotation_views=None):
    if not ROTATION_HTML.exists():
        rj = json.dumps(rotation_data or {})
        vj = json.dumps(rotation_views or ROTATION_VIEWS)
        ROTATION_HTML.write_text(build_rotation_html(rj, vj), encoding="utf-8")
        print(f"[html_builder] Regenerated {ROTATION_HTML}")

def maybe_write_all(rotation_data=None, rotation_views=None):
    maybe_write_index()
    maybe_write_rotation(rotation_data, rotation_views)
'''

BUILDER_PY.write_text(header, encoding="utf-8")
print(f"html_builder.py updated ({BUILDER_PY.stat().st_size:,} bytes)")

# Quick round-trip verify
import importlib.util, sys
spec = importlib.util.spec_from_file_location("html_builder", BUILDER_PY)
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

idx_out = mod.build_index_html()
rot_out = mod.build_rotation_html("{}", "{}")

idx_ok  = idx_out == index_src
rot_ok  = rot_out == rotation_src

print(f"index.html  round-trip: {'OK' if idx_ok else 'MISMATCH'}")
print(f"rotation.html round-trip: {'OK' if rot_ok else 'MISMATCH'}")
if not idx_ok:
    # Find first diff
    for i,(a,b) in enumerate(zip(idx_out, index_src)):
        if a != b:
            print(f"  First diff at char {i}: got {repr(a)} expected {repr(b)}")
            print(f"  Context: {repr(idx_out[max(0,i-30):i+30])}")
            break
if not rot_ok:
    for i,(a,b) in enumerate(zip(rot_out, rotation_src)):
        if a != b:
            print(f"  First diff at char {i}: got {repr(a)} expected {repr(b)}")
            break
