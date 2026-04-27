"""
Gekko V2 Server
===============
Single-file Flask server with:
  - Cache-first SQLite reads (uses existing GEKKO_APP/DATA/ databases)
  - Background Supabase sync (holdings, insiders, GI, OHLCV)
  - Per-ticker OHLCV auto-update + watchlist refresh
  - No .env, no Schwab, no session cookies required

Run:  python server.py
"""

from __future__ import annotations
import json, sqlite3, threading, time, os, webbrowser
from pathlib import Path
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

import requests
from flask import Flask, Response, abort, make_response, request, send_file

# ---------------------------------------------------------------------------
# CONFIG — hardcoded, no .env needed
# ---------------------------------------------------------------------------
SUPABASE_URL = "ADD_THE_URL_HERE"
SUPABASE_KEY = "ADD_YOUR_KEY_HERE"  # public key
SUPA_HDRS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept":        "application/json",
}
SUPA_PAGE = 500

# Paths — self-contained within GEKKO_V2
_HERE    = Path(__file__).resolve().parent
DATA_DIR = _HERE / "DATA"
OHLCV_DB    = DATA_DIR / "ohlcv_cache.sqlite"
PAYLOAD_DB  = DATA_DIR / "payload_cache.sqlite"
INDEX_HTML  = _HERE / "index.html"
GEKKO_SESSION_FILE = DATA_DIR / "gekko_session.txt"   # paste Cookie header from dashboard.gekko.app here
SIGNALS_HTML_PATH  = Path(r"C:\Users\chris\OneDrive\Desktop\Trading\GEKKO_BACKTESTER\gekko_backtest.html")
PORT = 5000

# Tray icon blink signal — incremented by API fetch workers, decremented when done.
# The blink loop reads this; dot only shows while count > 0.
_tray_fetch_lock  = threading.Lock()
_tray_fetch_count = 0
_tray_blink_event = threading.Event()   # set = actively fetching

def _tray_fetch_start():
    global _tray_fetch_count
    with _tray_fetch_lock:
        _tray_fetch_count += 1
        _tray_blink_event.set()

def _tray_fetch_end():
    global _tray_fetch_count
    with _tray_fetch_lock:
        _tray_fetch_count = max(0, _tray_fetch_count - 1)
        if _tray_fetch_count == 0:
            _tray_blink_event.clear()

# ---------------------------------------------------------------------------
# SIGNALS cache — loaded once from GEKKO_BACKTESTER/gekko_signals_all.json
# ---------------------------------------------------------------------------
# SIGNALS  (parsed from gekko_backtest.html CURRENT array)
# ---------------------------------------------------------------------------
import re as _re
_signals_lock        = threading.Lock()
_signals_by_ticker: dict = {}   # ticker -> [signal, ...]
_signals_flat: list  = []       # all signals sorted newest-first
_signals_loaded      = False
_signals_mtime: float = 0.0     # mtime of last load so we can reload on change

def _load_signals_once(force: bool = False):
    global _signals_by_ticker, _signals_flat, _signals_loaded, _signals_mtime
    with _signals_lock:
        if _signals_loaded and not force:
            return
        if not SIGNALS_HTML_PATH.exists():
            print(f"[signals] File not found: {SIGNALS_HTML_PATH}", flush=True)
            _signals_loaded = True
            return
        mtime = SIGNALS_HTML_PATH.stat().st_mtime
        if _signals_loaded and mtime == _signals_mtime:
            return  # file hasn't changed
        try:
            text = SIGNALS_HTML_PATH.read_text(encoding="utf-8", errors="replace")
            # Extract the CURRENT=[...] array embedded as JS in the HTML
            m = _re.search(r'const CURRENT\s*=\s*(\[.*?\]);', text, _re.DOTALL)
            if not m:
                print("[signals] Could not find CURRENT array in HTML", flush=True)
                _signals_loaded = True
                return
            raw: list = json.loads(m.group(1))
            by_t: dict = defaultdict(list)
            for s in raw:
                t = (s.get("ticker") or "").strip().upper()
                if t:
                    by_t[t].append(s)
            _signals_by_ticker = dict(by_t)
            _signals_flat = sorted(raw, key=lambda s: s.get("signal_date", ""), reverse=True)
            _signals_mtime = mtime
            print(f"[signals] Loaded {len(raw):,} signals for {len(_signals_by_ticker):,} tickers from HTML", flush=True)
        except Exception as exc:
            print(f"[signals] Load error: {exc}", flush=True)
        _signals_loaded = True

def _sig_type(s: dict) -> str:
    """Return a short type code used by the chart overlay."""
    fam = (s.get("signal_family") or "").lower()
    src = (s.get("signal_source") or "").lower()
    if src == "gi" and fam == "reversal":
        return "gi_rev"
    if fam == "continuation":
        return "cust_cont"
    return "gi_rev"   # fallback

# Hardcoded themed ETF list — (ticker, display_name, theme_category)
# Full universe: ~290 tickers across 10 categories
THEMES_ETF_LIST = [
    # Broad U.S. Sectors (The Core 11 — Market-Cap Weighted SPDR)
    ("XLK",  "Technology",                  "Broad U.S. Sectors"),
    ("XLF",  "Financials",                  "Broad U.S. Sectors"),
    ("XLV",  "Healthcare",                  "Broad U.S. Sectors"),
    ("XLE",  "Energy",                      "Broad U.S. Sectors"),
    ("XLI",  "Industrials",                 "Broad U.S. Sectors"),
    ("XLY",  "Consumer Disc",               "Broad U.S. Sectors"),
    ("XLP",  "Cons Staples",                "Broad U.S. Sectors"),
    ("XLU",  "Utilities",                   "Broad U.S. Sectors"),
    ("XLRE", "Real Estate",                 "Broad U.S. Sectors"),
    ("XLC",  "Comm Services",               "Broad U.S. Sectors"),
    ("XLB",  "Materials",                   "Broad U.S. Sectors"),

    # U.S. Industries & Sub-Sectors
    ("SMH",  "Semiconductors",              "U.S. Sub-Sectors"),
    ("SOXX", "Semi Equipment",              "U.S. Sub-Sectors"),
    ("XSD",  "Equal-Wt Semis",              "U.S. Sub-Sectors"),
    ("DRAM", "Memory & Storage",            "U.S. Sub-Sectors"),
    ("IGV",  "Software",                    "U.S. Sub-Sectors"),
    ("FDN",  "Internet",                    "U.S. Sub-Sectors"),
    ("KRE",  "Regional Banks",              "U.S. Sub-Sectors"),
    ("KBE",  "Large Cap Banks",             "U.S. Sub-Sectors"),
    ("KIE",  "Insurance",                   "U.S. Sub-Sectors"),
    ("IAI",  "Broker-Dealers",              "U.S. Sub-Sectors"),
    ("IAT",  "US Regional Banks",           "U.S. Sub-Sectors"),
    ("XBI",  "Biotechnology",               "U.S. Sub-Sectors"),
    ("IBB",  "Nasdaq Biotech",              "U.S. Sub-Sectors"),
    ("IHI",  "Medical Devices",             "U.S. Sub-Sectors"),
    ("XPH",  "Pharma",                      "U.S. Sub-Sectors"),
    ("PPH",  "Pharma (VanEck)",             "U.S. Sub-Sectors"),
    ("IHF",  "Healthcare Providers",        "U.S. Sub-Sectors"),
    ("XOP",  "Oil & Gas E&P",               "U.S. Sub-Sectors"),
    ("OIH",  "Oil Services",                "U.S. Sub-Sectors"),
    ("IEO",  "US Oil & Gas E&P",            "U.S. Sub-Sectors"),
    ("AMLP", "Alerian MLP",                 "U.S. Sub-Sectors"),
    ("MLPA", "Global X MLP",               "U.S. Sub-Sectors"),
    ("ITA",  "Aero & Defense",              "U.S. Sub-Sectors"),
    ("IYT",  "Transportation",              "U.S. Sub-Sectors"),
    ("XRT",  "Retail",                      "U.S. Sub-Sectors"),
    ("XHB",  "Homebuilders",                "U.S. Sub-Sectors"),
    ("SRVR", "Data Centers",                "U.S. Sub-Sectors"),
    ("VNQ",  "Broad REITs",                 "U.S. Sub-Sectors"),
    ("MORT", "Mortgage REITs",              "U.S. Sub-Sectors"),
    ("XME",  "Metals & Mining",             "U.S. Sub-Sectors"),
    ("GDX",  "Gold Miners",                 "U.S. Sub-Sectors"),
    ("GDXJ", "Jr Gold Miners",              "U.S. Sub-Sectors"),
    ("SLX",  "Steel",                       "U.S. Sub-Sectors"),

    # Commodities
    ("GLD",  "Gold",                        "Commodities"),
    ("SLV",  "Silver",                      "Commodities"),
    ("PPLT", "Platinum",                    "Commodities"),
    ("PALL", "Palladium",                   "Commodities"),
    ("GLTR", "Precious Metals Basket",      "Commodities"),
    ("CPER", "Copper",                      "Commodities"),
    ("DBB",  "Base Metals",                 "Commodities"),
    ("URA",  "Uranium",                     "Commodities"),
    ("URNM", "Uranium Miners",              "Commodities"),
    ("USO",  "Crude Oil",                   "Commodities"),
    ("BNO",  "Brent Crude",                 "Commodities"),
    ("UNG",  "Natural Gas",                 "Commodities"),
    ("DBE",  "Energy Commodities",          "Commodities"),
    ("DBA",  "Agriculture",                 "Commodities"),
    ("CORN", "Corn",                        "Commodities"),
    ("SOYB", "Soybeans",                    "Commodities"),
    ("WEAT", "Wheat",                       "Commodities"),
    ("CANE", "Sugar",                       "Commodities"),
    ("PDBC", "Broad Commodities",           "Commodities"),
    ("KRBN", "Carbon Credits",              "Commodities"),
    ("LIT",  "Lithium",                     "Commodities"),
    ("REMX", "Rare Earth",                  "Commodities"),
    ("PHO",  "Water Resources",             "Commodities"),
    ("PICK", "Metal Miners",                "Commodities"),
    ("COPX", "Copper Miners",               "Commodities"),
    ("HYDR", "Hydrogen Economy",            "Commodities"),
    ("SETM", "Clean Energy Materials",      "Commodities"),

    # Countries & Regions
    ("MCHI", "China",                       "Countries & Regions"),
    ("KWEB", "China Tech",                  "Countries & Regions"),
    ("ASHR", "China A-Shares",              "Countries & Regions"),
    ("EWJ",  "Japan",                       "Countries & Regions"),
    ("EWU",  "United Kingdom",              "Countries & Regions"),
    ("EWG",  "Germany",                     "Countries & Regions"),
    ("EWQ",  "France",                      "Countries & Regions"),
    ("EWL",  "Switzerland",                 "Countries & Regions"),
    ("EWI",  "Italy",                       "Countries & Regions"),
    ("EWP",  "Spain",                       "Countries & Regions"),
    ("VGK",  "Europe",                      "Countries & Regions"),
    ("EWA",  "Australia",                   "Countries & Regions"),
    ("EWC",  "Canada",                      "Countries & Regions"),
    ("EWZ",  "Brazil",                      "Countries & Regions"),
    ("EWW",  "Mexico",                      "Countries & Regions"),
    ("ARGT", "Argentina",                   "Countries & Regions"),
    ("ILF",  "Latin America",               "Countries & Regions"),
    ("INDA", "India",                       "Countries & Regions"),
    ("EWY",  "South Korea",                 "Countries & Regions"),
    ("EWT",  "Taiwan",                      "Countries & Regions"),
    ("KSA",  "Saudi Arabia",                "Countries & Regions"),
    ("EIS",  "Israel",                      "Countries & Regions"),
    ("TUR",  "Turkey",                      "Countries & Regions"),
    ("EPOL", "Poland",                      "Countries & Regions"),
    ("GREK", "Greece",                      "Countries & Regions"),
    ("VWO",  "Emerging Mkts",               "Countries & Regions"),
    ("IEMG", "Core EM",                     "Countries & Regions"),
    ("EMXC", "EM ex-China",                 "Countries & Regions"),
    ("DVYE", "EM Dividend",                 "Countries & Regions"),
    ("VEA",  "Developed ex-US",             "Countries & Regions"),
    ("VEU",  "All World ex-US",             "Countries & Regions"),
    ("AFK",  "Africa",                      "Countries & Regions"),
    ("EZA",  "South Africa",                "Countries & Regions"),
    ("EIDO", "Indonesia",                   "Countries & Regions"),
    ("EWM",  "Malaysia",                    "Countries & Regions"),
    ("EPHE", "Philippines",                 "Countries & Regions"),
    ("EWS",  "Singapore",                   "Countries & Regions"),
    ("THD",  "Thailand",                    "Countries & Regions"),
    ("VNM",  "Vietnam",                     "Countries & Regions"),
    ("FRDM", "Frontier Markets",            "Countries & Regions"),

    # Bonds & Fixed Income
    ("AGG",  "US Aggregate",                "Bonds & Fixed Income"),
    ("LQD",  "IG Corporates",               "Bonds & Fixed Income"),
    ("SHV",  "Short-Term Treasury",         "Bonds & Fixed Income"),
    ("SHY",  "1-3Y Treasury",               "Bonds & Fixed Income"),
    ("IEF",  "7-10Y Treasury",              "Bonds & Fixed Income"),
    ("TLT",  "20Y+ Treasury",               "Bonds & Fixed Income"),
    ("TBF",  "Short 20Y+ Treasury",         "Bonds & Fixed Income"),
    ("ZROZ", "Zero Coupon Treasury",        "Bonds & Fixed Income"),
    ("TIP",  "TIPS",                        "Bonds & Fixed Income"),
    ("FLOT", "Floating Rate",               "Bonds & Fixed Income"),
    ("VCSH", "Short-Term Corp",             "Bonds & Fixed Income"),
    ("VCIT", "Intermediate Corp",           "Bonds & Fixed Income"),
    ("VCLT", "Long-Term Corp",              "Bonds & Fixed Income"),
    ("HYG",  "High Yield",                  "Bonds & Fixed Income"),
    ("FALN", "Fallen Angels",               "Bonds & Fixed Income"),
    ("SRLN", "Bank Loans",                  "Bonds & Fixed Income"),
    ("SJNK", "Short-Term HY",               "Bonds & Fixed Income"),
    ("BKLN", "Broad Bank Loans",            "Bonds & Fixed Income"),
    ("MUB",  "Municipals",                  "Bonds & Fixed Income"),
    ("SUB",  "Short-Term Muni",             "Bonds & Fixed Income"),
    ("HYD",  "High Yield Muni",             "Bonds & Fixed Income"),
    ("EMB",  "EM Bonds (USD)",              "Bonds & Fixed Income"),
    ("EMLC", "EM Local Currency",           "Bonds & Fixed Income"),
    ("IGOV", "International Treasury",      "Bonds & Fixed Income"),
    ("PICB", "International Corp",          "Bonds & Fixed Income"),
    ("PFF",  "Preferreds",                  "Bonds & Fixed Income"),
    ("CWB",  "Convertibles",                "Bonds & Fixed Income"),
    ("VRP",  "Variable Rate Pref",          "Bonds & Fixed Income"),
    ("MBB",  "Mortgage-Backed",             "Bonds & Fixed Income"),
    ("CMBS", "Commercial MBS",              "Bonds & Fixed Income"),
    ("BAB",  "Build America Bonds",         "Bonds & Fixed Income"),
    ("BGRN", "Green Bonds",                 "Bonds & Fixed Income"),
    ("JAAA", "AAA CLOs",                    "Bonds & Fixed Income"),
    ("BSCQ", "Target 2026 Corp",            "Bonds & Fixed Income"),
    ("BSCR", "Target 2027 Corp",            "Bonds & Fixed Income"),

    # Thematic & Innovation
    ("BOTZ", "AI & Robotics",               "Thematic & Innovation"),
    ("ROBO", "Global Robotics",             "Thematic & Innovation"),
    ("AIQ",  "AI & Technology",             "Thematic & Innovation"),
    ("ARKQ", "ARK Autonomous & Robotics",   "Thematic & Innovation"),
    ("CIBR", "Cybersecurity",               "Thematic & Innovation"),
    ("BUG",  "Cybersecurity (Global X)",    "Thematic & Innovation"),
    ("SKYY", "Cloud Computing",             "Thematic & Innovation"),
    ("CLOU", "Cloud (Global X)",            "Thematic & Innovation"),
    ("IBUY", "Online Retail",               "Thematic & Innovation"),
    ("FINX", "Fintech",                     "Thematic & Innovation"),
    ("ARKF", "ARK Fintech",                 "Thematic & Innovation"),
    ("IPAY", "Mobile Payments",             "Thematic & Innovation"),
    ("ARKG", "Genomics",                    "Thematic & Innovation"),
    ("DRIV", "EV & Autonomous",             "Thematic & Innovation"),
    ("UFO",  "Space Exploration",           "Thematic & Innovation"),
    ("ICLN", "Clean Energy",                "Thematic & Innovation"),
    ("QCLN", "Clean Edge Energy",           "Thematic & Innovation"),
    ("TAN",  "Solar",                       "Thematic & Innovation"),
    ("FAN",  "Wind Energy",                 "Thematic & Innovation"),
    ("GRID", "Smart Grid",                  "Thematic & Innovation"),
    ("BATT", "Battery Tech",                "Thematic & Innovation"),
    ("PRNT", "3D Printing",                 "Thematic & Innovation"),
    ("METV", "Metaverse",                   "Thematic & Innovation"),
    ("ESPO", "Video Gaming & eSports",      "Thematic & Innovation"),
    ("HERO", "Gaming & eSports (Global X)", "Thematic & Innovation"),
    ("SOCL", "Social Media",                "Thematic & Innovation"),
    ("QTUM", "Quantum Computing",           "Thematic & Innovation"),
    ("ARKW", "ARK Next Gen Internet",       "Thematic & Innovation"),
    ("ARKK", "ARK Innovation",              "Thematic & Innovation"),
    ("PAVE", "Infrastructure",              "Thematic & Innovation"),
    ("KROP", "Ag & Food Tech",              "Thematic & Innovation"),
    ("VEGI", "Ag Technology",               "Thematic & Innovation"),
    ("CGW",  "Global Water",                "Thematic & Innovation"),
    ("PAWZ", "Pet Care",                    "Thematic & Innovation"),
    ("AGNG", "Aging Population",            "Thematic & Innovation"),
    ("MILN", "Millennial Consumers",        "Thematic & Innovation"),
    ("BETZ", "Sports Betting",              "Thematic & Innovation"),
    ("YOLO", "Cannabis",                    "Thematic & Innovation"),
    ("BLOK", "Blockchain",                  "Thematic & Innovation"),
    ("PSIL", "Psychedelics & Therapeutics",  "Thematic & Innovation"),

    # Crypto & Digital Assets
    ("IBIT", "Bitcoin (Spot)",              "Crypto & Digital"),
    ("FBTC", "Bitcoin (Fidelity)",          "Crypto & Digital"),
    ("ETHA", "Ethereum (Spot)",             "Crypto & Digital"),
    ("BITO", "Bitcoin Futures",             "Crypto & Digital"),
    ("BITI", "Short Bitcoin",               "Crypto & Digital"),
    ("BITW", "Crypto Index",                "Crypto & Digital"),
    ("WGMI", "Crypto Miners",               "Crypto & Digital"),
    ("DAPP", "Digital Economy",             "Crypto & Digital"),
    ("BKCH", "Web3 / Blockchain",           "Crypto & Digital"),
    ("HODL", "Crypto Innovators",           "Crypto & Digital"),
    ("COIN", "Coinbase",                    "Crypto & Digital"),

    # Global Sectors
    ("IXN",  "Global Tech",                 "Global Sectors"),
    ("IXG",  "Global Financials",           "Global Sectors"),
    ("IXJ",  "Global Healthcare",           "Global Sectors"),
    ("IXC",  "Global Energy",               "Global Sectors"),
    ("EXI",  "Global Industrials",          "Global Sectors"),
    ("RXI",  "Global Cons Disc",            "Global Sectors"),
    ("KXI",  "Global Cons Staples",         "Global Sectors"),
    ("MXI",  "Global Materials",            "Global Sectors"),
    ("IXP",  "Global Telecom",              "Global Sectors"),
    ("JXI",  "Global Utilities",            "Global Sectors"),
    ("REET", "Global Real Estate",          "Global Sectors"),
    ("IGF",  "Global Infrastructure",       "Global Sectors"),
    ("GNR",  "Global Natural Resources",    "Global Sectors"),
    ("GUNR", "Nat Resources ex-US",         "Global Sectors"),
    ("MOO",  "Global Agriculture",          "Global Sectors"),
    ("PIO",  "Global Water Infra",          "Global Sectors"),
    ("ACES", "Clean Energy Transition",     "Global Sectors"),
    ("WOOD", "Timber & Forestry",           "Global Sectors"),
    ("RING", "Global Gold Miners",          "Global Sectors"),
    ("SIL",  "Global Silver Miners",        "Global Sectors"),
    ("GOEX", "Gold Explorers",              "Global Sectors"),
    ("JETS", "Airlines",                    "Global Sectors"),
    ("BOAT", "Shipping",                    "Global Sectors"),
    ("GEX",  "Global Logistics",            "Global Sectors"),
    ("NLR",  "Nuclear Energy",              "Global Sectors"),
    ("SHLD", "Global Defense",              "Global Sectors"),
    ("WTAI", "AI Hardware",                 "Global Sectors"),
    ("EBIZ", "Global E-Commerce",           "Global Sectors"),

    # Style & Factor
    ("SPY",  "S&P 500",                     "Style & Factor"),
    ("QQQ",  "Nasdaq 100",                  "Style & Factor"),
    ("DIA",  "Dow Jones",                   "Style & Factor"),
    ("MDY",  "Mid-Cap 400",                 "Style & Factor"),
    ("IWM",  "Small Cap",                   "Style & Factor"),
    ("IJH",  "Mid-Cap (iShares)",           "Style & Factor"),
    ("IWC",  "Micro Cap",                   "Style & Factor"),
    ("MGC",  "Mega Cap",                    "Style & Factor"),
    ("SPYV", "Large Cap Value",             "Style & Factor"),
    ("SPYG", "Large Cap Growth",            "Style & Factor"),
    ("SPYD", "S&P 500 High Div",            "Style & Factor"),
    ("MDYV", "Mid Cap Value",               "Style & Factor"),
    ("MDYG", "Mid Cap Growth",              "Style & Factor"),
    ("IWN",  "Small Cap Value",             "Style & Factor"),
    ("IWO",  "Small Cap Growth",            "Style & Factor"),
    ("VUG",  "Growth",                      "Style & Factor"),
    ("VTV",  "Value",                       "Style & Factor"),
    ("NOBL", "Dividend Aristocrats",        "Style & Factor"),
    ("VYM",  "High Div Yield",              "Style & Factor"),
    ("SCHD", "US Dividend",                 "Style & Factor"),
    ("VIG",  "Div Growth",                  "Style & Factor"),
    ("IDV",  "Intl High Dividend",          "Style & Factor"),
    ("DES",  "Small Cap Dividend",          "Style & Factor"),
    ("PKW",  "Share Buybacks",              "Style & Factor"),
    ("SYLD", "Shareholder Yield",           "Style & Factor"),
    ("COWZ", "Cash Cows (FCF)",             "Style & Factor"),
    ("VLUE", "Value Factor",                "Style & Factor"),
    ("MTUM", "Momentum",                    "Style & Factor"),
    ("QUAL", "Quality",                     "Style & Factor"),
    ("SIZE", "Size Factor",                 "Style & Factor"),
    ("USMV", "Min Volatility",              "Style & Factor"),
    ("SPHB", "High Beta",                   "Style & Factor"),
    ("SPLV", "Low Beta",                    "Style & Factor"),
    ("LRGF", "Multi-Factor",               "Style & Factor"),
    ("RSP",  "Equal Wt S&P",               "Style & Factor"),
    ("RYT",  "Equal Wt Tech",              "Style & Factor"),
    ("RYF",  "Equal Wt Financials",        "Style & Factor"),
    ("RYH",  "Equal Wt Healthcare",        "Style & Factor"),
    ("MOAT", "Wide Moat",                  "Style & Factor"),
    ("AVUV", "Active Small Cap Value",     "Style & Factor"),
    ("CGGR", "Active Core Growth",         "Style & Factor"),
    ("AIEQ", "AI-Managed",                 "Style & Factor"),
    ("JEPI", "Equity Income",              "Style & Factor"),
    ("PUTW", "Put Write",                  "Style & Factor"),
    ("BJUL", "Buffer / Defined Outcome",   "Style & Factor"),
    ("ESGU", "ESG Broad",                  "Style & Factor"),
    ("CATH", "Catholic Values",            "Style & Factor"),
    ("HLAL", "Sharia Compliant",           "Style & Factor"),
    ("IPO",  "Recent IPOs",                "Style & Factor"),
    ("CSD",  "Corporate Spinoffs",         "Style & Factor"),

    # Alternatives & Macro
    ("DBMF", "Managed Futures",            "Alternatives & Macro"),
    ("VIXY", "VIX Futures",                "Alternatives & Macro"),
    ("UUP",  "US Dollar",                  "Alternatives & Macro"),
    ("FXY",  "Japanese Yen",               "Alternatives & Macro"),
    ("FXE",  "Euro",                       "Alternatives & Macro"),
    ("BTAL", "Anti-Beta",                  "Alternatives & Macro"),
]

# Tickers shown in the Majors heatmap view but NOT in THEMES_ETF_LIST.
# DIA/MDY/VEU are now in the main list so this can be empty,
# but kept for any future additions of heatmap-only tickers.
MAJORS_EXTRA: list[tuple[str, str]] = []

# Cache TTLs (hours) — used to decide when to re-fetch from Supabase
TTL_BULK   = 12    # holdings, insiders, GI scores, zone returns
TTL_THEMES = 1     # themes payload — rebuild hourly so returns stay current
TTL_OHLCV  = 36   # hours; stale if last bar > 36h old (covers overnight + weekend)
TTL_META   = 168  # ticker metadata — 7 days
OHLCV_LOOKBACK_DAYS = 760

# ---------------------------------------------------------------------------
# HARDCODED MANAGER LISTS (sourced from Supabase 2026-04-14; update as needed)
# ---------------------------------------------------------------------------
TB_MANAGERS = [
    ("0001801172", "11 Capital Partners"),
    ("0001540531", "12 West Capital"),
    ("0001982920", "9823 Capital"),
    ("0001578684", "Abdiel Capital"),
    ("0002099846", "Agave Capital"),
    ("0001858353", "Alta Fox Capital"),
    ("0002037077", "Ananym Capital"),
    ("0001817534", "Anomaly Capital"),
    ("0001906003", "Anson Capital"),
    ("0001386892", "Apis Capital"),
    ("0001777813", "Atreides Management"),
    ("0001399386", "Bandera Partners"),
    ("0001423686", "Cadian Capital"),
    ("0001697591", "CAS Investment Partners"),
    ("0001850901", "Conversant Capital"),
    ("0001104329", "Crosslink Capital"),
    ("0001754535", "DeepCurrents"),
    ("0001587114", "EcoR1 Capital"),
    ("0002053013", "Emeth Value Capital"),
    ("0001559771", "Engaged Capital"),
    ("0001665590", "Engine Capital"),
    ("0001741129", "Greenhaven Road"),
    ("0001840735", "Greenoaks Capital"),
    ("0001616659", "Harbert Fund Advisors"),
    ("0001786767", "Impactive Capital"),
    ("0002024579", "Jain Global"),
    ("0001525234", "Jericho Capital"),
    ("0001569688", "Kerrisdale Capital"),
    ("0001807489", "M28 Capital"),
    ("0001104186", "Masters Capital"),
    ("0001712901", "Melqart Asset Management"),
    ("0001425649", "MIG Capital"),
    ("0001803456", "NEW Advisory Services"),
    ("0001680843", "Nightview Capital"),
    ("0001630243", "Nitorum Capital"),
    ("0001747888", "North Peak Capital"),
    ("0001816616", "NZS Capital"),
    ("0001891904", "Octahedron Capital"),
    ("0001968437", "Perbak Capital"),
    ("0001536630", "Potrero Capital"),
    ("0001320769", "Praesidium Investment"),
    ("0001732543", "Q3 Asset Management"),
    ("0001517796", "Rangeley Capital"),
    ("0001566887", "Ratan Capital"),
    ("0001909393", "Repertoire Partners"),
    ("0001301050", "Shannon River"),
    ("0002045724", "Situational Awareness"),
    ("0001559706", "Slate Path Capital"),
    ("0001592413", "Strategy Capital"),
    ("0001960830", "SurgoCap Partners"),
    ("0001389234", "Symmetry Peak"),
    ("0001558971", "Tekne Capital"),
    ("0001624095", "Tenzing Global"),
    ("0001730145", "Voss Capital"),
    ("0001387322", "Whale Rock Capital"),
    ("0001785988", "Wolf Hill Capital"),
]

BB_MANAGERS = [
    ("0001103804", "Andreas Halvorsen"),
    ("0001336528", "Bill Ackman"),
    ("0001166559", "Bill Gates"),
    ("0001549575", "Bill Harnisch"),
    ("0001135778", "Bill Miller"),
    ("0000921669", "Carl Icahn"),
    ("0001167483", "Chase Coleman"),
    ("0001036325", "Chris Davis"),
    ("0001647251", "Christopher Hohn"),
    ("0001112520", "Chuck Akre"),
    ("0001040273", "Dan Loeb"),
    ("0001747057", "Dan Sundheim"),
    ("0001358706", "David Abrams"),
    ("0001489933", "David Einhorn"),
    ("0001656456", "David Tepper"),
    ("0001029160", "George Soros"),
    ("0001543160", "Glenn Greenberg"),
    ("0001273087", "Israel Englander"),
    ("0001035674", "John Paulson"),
    ("0001423053", "Ken Griffin"),
    ("0001138995", "Larry Robbins"),
    ("0000898382", "Leon Cooperman"),
    ("0001709323", "Li Lu"),
    ("0000807985", "Mason Hawkins"),
    ("0001671657", "Pat Dorsey"),
    ("0001791786", "Paul Singer"),
    ("0000923093", "Paul Tudor Jones"),
    ("0001135730", "Philippe Laffont"),
    ("0000915191", "Prem Watsa"),
    ("0001350694", "Ray Dalio"),
    ("0001166309", "Roberto Mignone"),
    ("0001061768", "Seth Klarman"),
    ("0001536411", "Stanley Druckenmiller"),
    ("0001603466", "Steve Cohen"),
    ("0001061165", "Steve Mandel"),
    ("0001569205", "Terry Smith"),
    ("0001096343", "Tom Gayner"),
    ("0001067983", "Warren Buffett"),
]

# Reversal thresholds — based on GI tier boundaries
RV_BUY_THRESH  = 45.0  # GI crosses UP through this  → buy signal  (enters neutral from distribution/selling)
RV_SELL_THRESH = 60.0  # GI crosses DOWN through this → sell signal (exits accumulation zone)

# SQLite bucket names — must match what GEKKO_APP writes
B_HOLDINGS   = "api_holdings"
B_INSIDERS   = "api_insiders"
B_CONVICTION = "api_conviction"
B_BUY_META   = "api_buy_meta"
B_GI_HIST    = "api_gi_history"
B_ZR         = "api_zone_returns"
B_ZR_ALL     = "api_zone_returns_all"
B_THEMES     = "api_themes"
B_ROTATION   = "api_rotation"
B_SP500      = "api_sp500"
B_REVERSALS  = "api_reversals"
B_EARNINGS   = "api_earnings"
B_FAIR_VALUE = "api_fair_value"
B_BUBBLE     = "api_bubble_size"
B_META       = "api_meta"
B_GI_SCORE   = "gi_scores"
B_NAMES      = "ticker_names"
B_GI_HIST_PER = "gi_history"       # per-ticker GI history
B_ZR_PER      = "zone_returns"     # per-ticker zone returns
B_TICKER_META = "ticker_meta"
B_PREFS       = "prefs"
ALL_KEY       = "__ALL__"
PREFS_KEY     = "__ALL__"

# ---------------------------------------------------------------------------
# SQLITE HELPERS
# ---------------------------------------------------------------------------
def _pconn() -> sqlite3.Connection:
    """Thread-safe payload_cache connection with WAL mode."""
    conn = sqlite3.connect(str(PAYLOAD_DB), timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=60000")
    return conn


def _oconn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(OHLCV_DB), timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=60000")
    return conn


def init_stores() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _pconn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS payload_cache (
            bucket     TEXT NOT NULL,
            cache_key  TEXT NOT NULL,
            data_json  TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (bucket, cache_key))""")
        c.execute("""CREATE TABLE IF NOT EXISTS payload_bucket_meta (
            bucket TEXT PRIMARY KEY,
            updated_at TEXT)""")
    with _oconn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS ohlcv_bars (
            ticker TEXT NOT NULL, date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            PRIMARY KEY (ticker, date))""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv ON ohlcv_bars(ticker, date)")


def payload_get(bucket: str, key: str = ALL_KEY):
    """Return (data, updated_at_iso) or (None, None) if missing."""
    if not PAYLOAD_DB.exists():
        return None, None
    with _pconn() as c:
        row = c.execute(
            "SELECT data_json, updated_at FROM payload_cache WHERE bucket=? AND cache_key=?",
            (bucket, str(key).strip().upper()),
        ).fetchone()
    if not row:
        return None, None
    try:
        return json.loads(row["data_json"]), row["updated_at"]
    except Exception:
        return None, None


def payload_set(bucket: str, data, key: str = ALL_KEY, ts: str | None = None) -> None:
    now = ts or datetime.now(timezone.utc).isoformat()
    norm_key = str(key).strip().upper()
    with _pconn() as c:
        c.execute(
            """INSERT OR REPLACE INTO payload_cache (bucket,cache_key,data_json,updated_at)
               VALUES (?,?,?,?)""",
            (bucket, norm_key, json.dumps(data, separators=(",", ":")), now),
        )
        c.execute(
            """INSERT INTO payload_bucket_meta (bucket,updated_at) VALUES (?,?)
               ON CONFLICT(bucket) DO UPDATE SET updated_at=excluded.updated_at""",
            (bucket, now),
        )


def payload_updated_at(bucket: str) -> str:
    if not PAYLOAD_DB.exists():
        return ""
    with _pconn() as c:
        row = c.execute(
            "SELECT updated_at FROM payload_bucket_meta WHERE bucket=?", (bucket,)
        ).fetchone()
    return str(row["updated_at"] or "") if row else ""


def ohlcv_get(ticker: str) -> list[dict]:
    if not OHLCV_DB.exists():
        return []
    with _oconn() as c:
        rows = c.execute(
            "SELECT date,open,high,low,close,volume FROM ohlcv_bars WHERE ticker=? ORDER BY date",
            (ticker.upper(),),
        ).fetchall()
    return [{"t": r["date"], "o": r["open"], "h": r["high"], "l": r["low"],
             "c": r["close"], "v": r["volume"]} for r in rows]


def ohlcv_upsert(ticker: str, rows: list[dict]) -> None:
    sym = ticker.upper()
    with _oconn() as c:
        for r in rows:
            c.execute(
                """INSERT OR REPLACE INTO ohlcv_bars
                   (ticker,date,open,high,low,close,volume) VALUES (?,?,?,?,?,?,?)""",
                (sym, r["t"], r.get("o"), r.get("h"), r.get("l"), r.get("c"), r.get("v")),
            )


def ohlcv_latest_date(ticker: str) -> str | None:
    if not OHLCV_DB.exists():
        return None
    with _oconn() as c:
        row = c.execute(
            "SELECT MAX(date) AS d FROM ohlcv_bars WHERE ticker=?",
            (ticker.upper(),),
        ).fetchone()
    return row["d"] if row else None


def ohlcv_all_tickers() -> list[str]:
    if not OHLCV_DB.exists():
        return []
    with _oconn() as c:
        return [r[0] for r in c.execute("SELECT DISTINCT ticker FROM ohlcv_bars")]

# ---------------------------------------------------------------------------
# STALENESS HELPERS
# ---------------------------------------------------------------------------
def _is_stale(ts_iso: str | None, hours: float) -> bool:
    if not ts_iso:
        return True
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).total_seconds() > hours * 3600
    except Exception:
        return True


_OHLCV_INTRADAY_TTL_SECS = 5 * 60  # re-fetch today's bar every 5 min during market hours

def _ohlcv_is_stale(ticker: str) -> bool:
    """Return True if OHLCV data should be refreshed.

    Two regimes:
    • Market hours  — stale if last fetch was >5 min ago (keeps today's bar current)
    • Off hours     — stale if last bar date is >TTL_OHLCV hours old
    """
    sym = ticker.upper()
    now = datetime.now(timezone.utc)

    if _is_market_hours():
        last_fetch_iso = _ohlcv_refresh_ts.get(sym)
        if not last_fetch_iso:
            return True  # never fetched → stale
        try:
            last_fetch = datetime.fromisoformat(last_fetch_iso)
            return (now - last_fetch).total_seconds() > _OHLCV_INTRADAY_TTL_SECS
        except Exception:
            return True

    # Outside market hours: fall back to bar-date TTL
    ld = ohlcv_latest_date(sym)
    if not ld:
        return True
    try:
        last_bar = datetime.strptime(ld, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (now - last_bar).total_seconds() > TTL_OHLCV * 3600
    except Exception:
        return True


def _is_market_hours() -> bool:
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False
    et_hour = (now.hour - 4) % 24
    return 4 <= et_hour < 20


def _is_regular_session() -> bool:
    """True only during regular NYSE session: Mon–Fri 09:30–16:00 ET."""
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False
    # ET offset: UTC-5 in winter, UTC-4 in summer — approximate with fixed -4 (EDT)
    # For accuracy we do it properly using total minutes from midnight UTC
    et_minutes = (now.hour * 60 + now.minute - 4 * 60) % (24 * 60)
    return 9 * 60 + 30 <= et_minutes < 16 * 60


# Use query2 for quotes — same host as crumb source so cookies are always valid.
# query1 has been increasingly rejecting v7 quote requests even with a valid crumb.
_YAHOO_QUOTE_URL  = "https://query2.finance.yahoo.com/v7/finance/quote"
_YAHOO_QUOTE_URL2 = "https://query1.finance.yahoo.com/v7/finance/quote"   # fallback
_YAHOO_CHART_URL  = "https://query2.finance.yahoo.com/v8/finance/chart/"
_YAHOO_CRUMB_URL  = "https://query2.finance.yahoo.com/v1/test/getcrumb"
_YAHOO_CONSENT_URL = "https://finance.yahoo.com"

# Shared session + crumb — Yahoo requires a cookie-authenticated crumb token
# (obtained once, cached for _YAHOO_CRUMB_TTL seconds, auto-refreshed on 401).
_yahoo_session: requests.Session | None = None
_yahoo_crumb:   str | None = None
_yahoo_crumb_at: float = 0.0
_yahoo_crumb_lock = threading.Lock()
_YAHOO_CRUMB_TTL  = 1800   # seconds — refresh every 30 min (Yahoo crumbs expire faster now)

_YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":  "en-US,en;q=0.9",
    "Accept-Encoding":  "gzip, deflate, br",
    "Referer":          "https://finance.yahoo.com/",
    "Origin":           "https://finance.yahoo.com",
    "Sec-Ch-Ua":        '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest":   "document",
    "Sec-Fetch-Mode":   "navigate",
    "Sec-Fetch-Site":   "same-origin",
    "Cache-Control":    "no-cache",
    "Pragma":           "no-cache",
}


def _ensure_yahoo_crumb(force: bool = False) -> tuple[requests.Session, str]:
    """
    Return (session, crumb).  Builds a fresh session + crumb when:
      • first call
      • TTL expired
      • force=True (called after a 401 to hard-refresh)
    Thread-safe.
    """
    global _yahoo_session, _yahoo_crumb, _yahoo_crumb_at

    with _yahoo_crumb_lock:
        age = time.time() - _yahoo_crumb_at
        if not force and _yahoo_crumb and age < _YAHOO_CRUMB_TTL:
            return _yahoo_session, _yahoo_crumb   # type: ignore[return-value]

        sess = requests.Session()
        sess.headers.update(_YAHOO_HEADERS)

        # 1. Visit finance homepage to pick up session cookies (follow all redirects
        #    so EU/consent pages are handled automatically).
        for warm_url in (
            _YAHOO_CONSENT_URL,
            "https://finance.yahoo.com/markets/",
            "https://query2.finance.yahoo.com",
        ):
            try:
                resp = sess.get(warm_url, timeout=12, allow_redirects=True)
                # Accept any consent gate automatically via POST if redirected there
                if "consent.yahoo.com" in resp.url:
                    try:
                        sess.post(
                            resp.url,
                            data={"agree": "agree", "consentUUID": "default", "sessionId": ""},
                            timeout=10,
                            allow_redirects=True,
                        )
                    except Exception:
                        pass
            except Exception:
                pass

        # Switch Accept header to JSON for API calls
        sess.headers.update({
            "Accept":        "application/json, text/plain, */*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        })

        # 2. Fetch the crumb — try both crumb URLs
        crumb = ""
        crumb_urls = [
            "https://query2.finance.yahoo.com/v1/test/getcrumb",
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
        ]
        for attempt in range(3):
            url = crumb_urls[attempt % len(crumb_urls)]
            try:
                cr = sess.get(url, timeout=10)
                app.logger.debug(
                    "Yahoo crumb attempt %d (%s): status=%s body=%r cookies=%s",
                    attempt + 1, url, cr.status_code,
                    cr.text[:80] if cr.ok else cr.text[:200],
                    dict(sess.cookies),
                )
                if cr.status_code == 200 and cr.text.strip() and cr.text.strip() != "null":
                    crumb = cr.text.strip()
                    break
            except Exception as e:
                app.logger.warning("Yahoo crumb fetch error (attempt %d): %s", attempt + 1, e)
            time.sleep(0.8)

        _yahoo_session  = sess
        _yahoo_crumb    = crumb
        _yahoo_crumb_at = time.time()

        if crumb:
            app.logger.info("Yahoo crumb refreshed OK: %r", crumb[:20])
        else:
            app.logger.warning(
                "Yahoo crumb fetch returned empty after 2 attempts — "
                "quotes will likely 401. Cookies present: %s",
                bool(sess.cookies)
            )

        return sess, crumb


def _fetch_yahoo_names(tickers: list[str]) -> dict[str, str]:
    """Fetch company display names from Yahoo Finance search API (no auth needed).
    Returns {TICKER: name_string}.  Used to fill in any names missing from
    the screener/Supabase name_map.
    """
    if not tickers:
        return {}
    result: dict[str, str] = {}
    _SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
    _HDR = {"User-Agent": "Mozilla/5.0"}

    def _lookup(sym: str) -> tuple[str, str]:
        try:
            r = requests.get(
                _SEARCH_URL,
                params={"q": sym, "quotesCount": 1, "newsCount": 0, "enableFuzzyQuery": "false"},
                headers=_HDR,
                timeout=5,
            )
            if not r.ok:
                return sym, ""
            quotes = r.json().get("quotes") or []
            match = next((q for q in quotes if (q.get("symbol") or "").upper() == sym), None)
            if match:
                name = (match.get("longname") or match.get("shortname") or "").strip()
                return sym, name
        except Exception as e:
            print(f"[names] Yahoo search error for {sym}: {e}", flush=True)
        return sym, ""

    with ThreadPoolExecutor(max_workers=8) as ex:
        for sym, name in ex.map(_lookup, [t.upper() for t in tickers]):
            if name:
                result[sym] = name
    return result


def _enrich_name_map(name_map: dict, tickers: list[str]) -> dict:
    """Return a copy of name_map with Yahoo Finance names filled in for any
    tickers whose name is currently blank.  Safe to call even when Yahoo is
    unavailable — missing names stay blank rather than raising.
    """
    missing = [t for t in tickers if not name_map.get(t)]
    if not missing:
        return name_map
    try:
        yahoo_names = _fetch_yahoo_names(missing)
        if yahoo_names:
            enriched = dict(name_map)
            enriched.update(yahoo_names)
            print(f"[names] Yahoo filled {len(yahoo_names):,} missing company names", flush=True)
            return enriched
    except Exception as e:
        print(f"[names] _enrich_name_map error: {e}", flush=True)
    return name_map


def _fetch_yahoo_quotes(tickers: list) -> dict:
    """
    Fetch real-time quotes from Yahoo Finance for a list of tickers.
    Returns dict keyed by uppercase ticker symbol with fields:
      price, regular_session, change, changePct, close_price, open, high, low, volume
    Auto-retries once with a fresh crumb on 401.
    """
    if not tickers:
        return {}
    symbols = ",".join(t.upper() for t in tickers[:50])  # Yahoo caps at ~50
    fields = (
        "regularMarketPrice,regularMarketPreviousClose,"
        "regularMarketOpen,regularMarketDayHigh,regularMarketDayLow,"
        "regularMarketVolume,regularMarketChange,regularMarketChangePercent,"
        "preMarketPrice,postMarketPrice,marketState,marketCap,totalAssets"
    )

    def _do_fetch(force_refresh: bool, url: str = _YAHOO_QUOTE_URL) -> requests.Response:
        sess, crumb = _ensure_yahoo_crumb(force=force_refresh)
        params: dict = {"symbols": symbols, "fields": fields}
        if crumb:
            params["crumb"] = crumb
        return sess.get(url, params=params, timeout=10)

    try:
        resp = _do_fetch(False)
        if resp.status_code == 401:
            # Crumb expired — refresh once and retry on query2
            app.logger.info("Yahoo 401 on quotes (query2) — refreshing crumb and retrying")
            resp = _do_fetch(True)
        if resp.status_code == 401:
            # Last resort: try query1 with fresh crumb
            app.logger.info("Yahoo still 401 after crumb refresh — trying query1 fallback")
            resp = _do_fetch(True, url=_YAHOO_QUOTE_URL2)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        app.logger.warning("Yahoo Finance quote fetch failed: %s", exc)
        return {}

    result = {}
    quotes = (data.get("quoteResponse") or {}).get("result") or []
    for q in quotes:
        sym = (q.get("symbol") or "").upper()
        if not sym:
            continue
        market_state = (q.get("marketState") or "").upper()  # PRE, REGULAR, POST, CLOSED
        is_regular = market_state == "REGULAR"

        # Price: during extended hours show pre/post price; otherwise regular
        if market_state == "PRE" and q.get("preMarketPrice"):
            price = float(q["preMarketPrice"])
        elif market_state in ("POST", "POSTMARKET") and q.get("postMarketPrice"):
            price = float(q["postMarketPrice"])
        else:
            price = float(q.get("regularMarketPrice") or 0)

        prev_close = float(q.get("regularMarketPreviousClose") or 0)
        change     = float(q.get("regularMarketChange") or 0)
        change_pct = float(q.get("regularMarketChangePercent") or 0)

        result[sym] = {
            "price":          price,
            "regular_session": is_regular,
            "change":         round(change, 4),
            "changePct":      round(change_pct, 4),
            "close_price":    prev_close,
            "open":           float(q.get("regularMarketOpen") or 0),
            "high":           float(q.get("regularMarketDayHigh") or 0),
            "low":            float(q.get("regularMarketDayLow") or 0),
            "volume":         int(q.get("regularMarketVolume") or 0),
            "market_state":   market_state,
            "marketCap":      q.get("marketCap"),    # stocks
            "totalAssets":    q.get("totalAssets"),  # ETFs
        }
    return result


def _fetch_ohlcv_yahoo(ticker: str, start_date: str) -> list[dict]:
    """
    Fetch daily OHLCV bars from Yahoo Finance chart API.
    Returns list of {t, o, h, l, c, v} dicts, empty on failure.
    Used as fallback for ETFs not in Supabase stock_data.
    Auto-retries once with a fresh crumb on 401.
    """
    def _do_fetch(force_refresh: bool) -> requests.Response:
        sess, crumb = _ensure_yahoo_crumb(force=force_refresh)
        params: dict = {"range": "2y", "interval": "1d", "includePrePost": "false"}
        if crumb:
            params["crumb"] = crumb
        return sess.get(_YAHOO_CHART_URL + ticker.upper(), params=params, timeout=15)

    try:
        resp = _do_fetch(False)
        if resp.status_code == 401:
            app.logger.info("Yahoo 401 on OHLCV %s — refreshing crumb and retrying", ticker)
            resp = _do_fetch(True)
        resp.raise_for_status()
        data = resp.json()
        chart = (data.get("chart") or {}).get("result") or []
        if not chart:
            return []
        res = chart[0]
        timestamps = res.get("timestamp") or []
        q = (res.get("indicators") or {}).get("quote") or [{}]
        q = q[0] if q else {}
        opens   = q.get("open")   or []
        highs   = q.get("high")   or []
        lows    = q.get("low")    or []
        closes  = q.get("close")  or []
        volumes = q.get("volume") or []

        rows = []
        for i, ts in enumerate(timestamps):
            c = closes[i] if i < len(closes) else None
            if c is None:
                continue
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            if dt < start_date:
                continue
            rows.append({
                "t": dt,
                "o": round(opens[i], 4)   if i < len(opens)   and opens[i]   is not None else None,
                "h": round(highs[i], 4)   if i < len(highs)   and highs[i]   is not None else None,
                "l": round(lows[i], 4)    if i < len(lows)    and lows[i]    is not None else None,
                "c": round(c, 4),
                "v": int(volumes[i])      if i < len(volumes)  and volumes[i] is not None else 0,
            })
        return rows
    except Exception as exc:
        app.logger.warning("Yahoo OHLCV fetch failed for %s: %s", ticker, exc)
        return []


# ---------------------------------------------------------------------------
# SUPABASE HELPERS
# ---------------------------------------------------------------------------
def _supa_get(table: str, params: dict) -> list[dict]:
    """Paginated Supabase REST GET. Returns combined list of all pages."""
    rows, offset = [], 0
    while True:
        p = dict(params)
        p["limit"]  = SUPA_PAGE
        p["offset"] = offset
        resp = requests.get(f"{SUPABASE_URL}/{table}", headers=SUPA_HDRS, params=p, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < SUPA_PAGE:
            break
        offset += SUPA_PAGE
    return rows


def _safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _fmt_money_short(v) -> str:
    """Format a dollar value as $1.2T / $168.3B / $4.5M / $300K etc."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "-"
    if n == 0:
        return "$0"
    neg = n < 0
    n = abs(n)
    if n >= 1e12:
        s = f"${n/1e12:.1f}T"
    elif n >= 1e9:
        s = f"${n/1e9:.1f}B"
    elif n >= 1e6:
        s = f"${n/1e6:.1f}M"
    elif n >= 1e3:
        s = f"${n/1e3:.0f}K"
    else:
        s = f"${n:.0f}"
    return ("-" + s) if neg else s


# ---------------------------------------------------------------------------
# DATA PROCESSING — Holdings change detection
# ---------------------------------------------------------------------------
def _compute_changes(cik: str, name: str, source: str, rows: list[dict]) -> list[dict]:
    by_date: dict[str, list] = defaultdict(list)
    for r in rows:
        rd = str(r.get("report_date") or "")
        if rd:
            by_date[rd].append(r)
    dates = sorted(by_date.keys(), reverse=True)
    if not dates:
        return []
    curr_date = dates[0]
    prev_date = dates[1] if len(dates) > 1 else None
    # If no prior filing period exists in the DB we cannot determine what is
    # truly "new" — flag so callers can distinguish "genuinely new" vs "unknown"
    has_history = prev_date is not None
    if not has_history:
        print(f"[holdings] WARNING: {name} ({cik}) only has 1 filing date ({curr_date}) — "
              f"cannot determine NEW vs existing; marking positions as UNKNOWN", flush=True)
    curr_rows = by_date[curr_date]
    prev_map: dict[str, dict] = {}
    if prev_date:
        for r in by_date[prev_date]:
            t = str(r.get("ticker") or "").strip()
            if t:
                prev_map[t] = r

    result, curr_tickers = [], set()
    for r in curr_rows:
        ticker = str(r.get("ticker") or "").strip()
        if not ticker:
            continue
        curr_tickers.add(ticker)
        shares = _safe_float(r.get("shares"))
        value  = _safe_float(r.get("value_usd"))
        prev_row = prev_map.get(ticker)
        if prev_row is None:
            # Only mark NEW if we actually have a prior filing to compare against.
            # If this manager only has one filing in the DB we cannot know whether
            # it's truly new, so mark UNKNOWN to avoid false "new position" signals.
            change_type = "NEW" if has_history else "UNKNOWN"
            prev_shares = share_change = scp = None
        else:
            prev_shares = _safe_float(prev_row.get("shares"))
            if shares is not None and prev_shares is not None and prev_shares != 0:
                share_change = shares - prev_shares
                scp = share_change / prev_shares * 100
                change_type = "INCREASED" if share_change > 0 else "DECREASED" if share_change < 0 else "UNCHANGED"
            else:
                change_type = "UNCHANGED"
                share_change = scp = None
        result.append({
            "source": source, "manager_name": name, "manager_cik": cik,
            "report_date": curr_date, "ticker": ticker,
            "company_name": str(r.get("company_name") or ""),
            "shares": shares, "value_usd": value,
            "change_type": change_type, "share_change": share_change,
            "share_change_pct": scp,
        })
    for ticker, prev_row in prev_map.items():
        if ticker not in curr_tickers:
            ps = _safe_float(prev_row.get("shares"))
            result.append({
                "source": source, "manager_name": name, "manager_cik": cik,
                "report_date": curr_date, "ticker": ticker,
                "company_name": str(prev_row.get("company_name") or ""),
                "shares": 0, "value_usd": 0,
                "change_type": "SOLD", "share_change": -ps if ps else None,
                "share_change_pct": -100.0,
            })
    return result


# ---------------------------------------------------------------------------
# GI SCORE / TIER HELPERS
# ---------------------------------------------------------------------------
def _gi_tier(score) -> str:
    if score is None: return ""
    if score >= 70:   return "dark-green"
    if score >= 60:   return "green"
    if score >= 45:   return "yellow"
    if score >= 33:   return "orange"
    return "red"


def _compute_reversals_for_ticker(gi_rows: list[dict], price_map: dict[str, float]) -> list[dict]:
    """
    Detect GI score crossover events for a single ticker.
    gi_rows  : sorted list of {date, gi_score} dicts (oldest first)
    price_map: {date_str: close_price}
    Returns  : [{d, t, p}] — d=YYYY-MM-DD, t='buy'|'sell', p=close price
    """
    signals: list[dict] = []
    prev: float | None = None
    sorted_dates = sorted(price_map.keys())  # for nearest-date fallback

    def _nearest_price(date: str) -> float | None:
        """Return close price for date, or nearest prior date if exact not found."""
        if date in price_map:
            return price_map[date]
        # Walk back up to 5 trading days
        from datetime import date as _date, timedelta
        try:
            d = _date.fromisoformat(date)
            for i in range(1, 6):
                key = (d - timedelta(days=i)).isoformat()
                if key in price_map:
                    return price_map[key]
        except Exception:
            pass
        return None

    for row in gi_rows:
        date  = str(row.get("date") or row.get("t") or row.get("d") or "").strip()
        score_raw = row.get("gi_score") if row.get("gi_score") is not None else row.get("v")
        if not date or score_raw is None:
            continue
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            continue

        if prev is not None:
            # Buy: crossed UP through RV_BUY_THRESH
            if prev < RV_BUY_THRESH <= score:
                p = _nearest_price(date)
                if p is not None:
                    signals.append({"d": date, "t": "buy", "p": round(p, 2)})
            # Sell: crossed DOWN through RV_SELL_THRESH
            elif prev >= RV_SELL_THRESH > score:
                p = _nearest_price(date)
                if p is not None:
                    signals.append({"d": date, "t": "sell", "p": round(p, 2)})
        prev = score

    return signals


# ---------------------------------------------------------------------------
# SUPABASE FETCH FUNCTIONS
# ---------------------------------------------------------------------------
def _fetch_gi_scores() -> tuple[dict, dict, dict]:
    """Fetch GI scores, company names, and sectors.
    Primary source: screener_latest (stocks).
    Fallback for ETFs/missing tickers: gekko_index (latest row per ticker).
    Returns (gi_map, name_map, sector_map) all keyed by uppercase ticker.
    """
    # --- Primary: screener_latest (stocks only) ---
    rows = _supa_get("screener_latest", {"select": "ticker,gi_score,name", "order": "gi_score.desc"})
    gi_map   = {str(r["ticker"]).upper(): _safe_float(r.get("gi_score")) for r in rows if r.get("ticker")}
    name_map = {str(r["ticker"]).upper(): str(r["name"]) for r in rows if r.get("ticker") and r.get("name")}

    # --- Try to get sector from screener_latest (non-fatal if column missing) ---
    sector_map: dict = {}
    try:
        srows = _supa_get("screener_latest", {"select": "ticker,sector", "sector": "not.is.null"})
        sector_map = {str(r["ticker"]).upper(): str(r["sector"]) for r in srows if r.get("ticker") and r.get("sector")}
    except Exception:
        pass  # sector column may not exist; proceed without it

    # --- Fallback: gekko_index for ETFs / watchlist tickers missing from screener_latest ---
    # Build list of tickers we need but don't have yet
    etf_tickers: set[str] = set()
    for t, _, _ in THEMES_ETF_LIST:
        etf_tickers.add(t.upper())
    for cfg in ROTATION_TICKERS.values():
        for t in cfg.get("tickers", []):
            etf_tickers.add(t.upper())
        etf_tickers.add(cfg.get("benchmark", "").upper())

    missing = sorted(etf_tickers - set(gi_map.keys()))
    if missing:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
        # Fetch in chunks to keep URL length manageable
        chunk_size = 50
        for i in range(0, len(missing), chunk_size):
            chunk = missing[i : i + chunk_size]
            try:
                gi_rows = _supa_get("gekko_index", {
                    "select":  "ticker,gi_score,date",
                    "ticker":  f"in.({','.join(chunk)})",
                    "date":    f"gte.{cutoff}",
                    "order":   "date.desc",
                })
                seen: set[str] = set()
                for r in gi_rows:
                    t = str(r.get("ticker") or "").strip().upper()
                    if t and t not in seen and r.get("gi_score") is not None:
                        gi_map[t] = _safe_float(r["gi_score"])
                        seen.add(t)
            except Exception as e:
                print(f"[gi_scores] gekko_index fallback error: {e}", flush=True)

    return gi_map, name_map, sector_map


def _fetch_holdings_raw() -> list[dict]:
    """Fetch all holdings from Supabase using hardcoded manager lists."""
    all_rows: list[dict] = []

    def _fetch_mgr(cik, name, table, source):
        raw = _supa_get(table, {
            "select": "ticker,company_name,report_date,shares,value_usd",
            "manager_cik": f"eq.{cik}",
            "order": "report_date.desc,value_usd.desc",
        })
        return _compute_changes(cik, name, source, raw)

    jobs = (
        [(cik, name, "trailblazer_holdings", "Trailblazer") for cik, name in TB_MANAGERS] +
        [(cik, name, "billionaire_holdings", "Billionaire")  for cik, name in BB_MANAGERS]
    )
    with ThreadPoolExecutor(max_workers=8) as ex:
        for rows in ex.map(lambda j: _fetch_mgr(*j), jobs):
            all_rows.extend(rows)
    return all_rows


def _fetch_insiders_raw() -> list[dict]:
    """Fetch recent insider trades from Supabase."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=730)).strftime("%Y-%m-%d")
    return _supa_get("insider_trades", {
        "select": "*",
        "filing_date": f"gte.{cutoff}",
        "total_value": "gte.50000",
        "order": "filing_date.desc",
    })


def _fetch_ohlcv_supabase(ticker: str, start_date: str) -> list[dict]:
    """Fetch OHLCV bars for a single ticker from Supabase stock_data table."""
    raw = _supa_get("stock_data", {
        "select": "date,open,high,low,close,volume",
        "ticker": f"eq.{ticker}",
        "date": f"gte.{start_date}",
        "order": "date.asc",
    })
    rows = []
    for r in raw:
        try:
            rows.append({
                "t": r["date"],
                "o": float(r.get("open")   or 0),
                "h": float(r.get("high")   or 0),
                "l": float(r.get("low")    or 0),
                "c": float(r.get("close")  or 0),
                "v": float(r.get("volume") or 0) if r.get("volume") is not None else None,
            })
        except (KeyError, TypeError, ValueError):
            continue
    return rows


def _fetch_and_cache_ohlcv(ticker: str) -> list[dict]:
    """
    Fetch new OHLCV bars for ticker from Supabase, merge with existing cache,
    write back to SQLite, return final rows.
    """
    existing = ohlcv_get(ticker)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=OHLCV_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    if existing and len(existing) >= 50:
        start_date = existing[-1]["t"]    # incremental from last bar
    else:
        start_date = cutoff
    print(f"[ohlcv] {ticker}: fetching from {start_date}...", flush=True)
    new_rows = _fetch_ohlcv_supabase(ticker, start_date)
    if not new_rows:
        print(f"[ohlcv] {ticker}: no new data", flush=True)
        return existing
    merged = {r["t"]: r for r in existing}
    merged.update({r["t"]: r for r in new_rows})
    final = sorted(merged.values(), key=lambda r: r["t"])
    ohlcv_upsert(ticker, final)
    print(f"[ohlcv] {ticker}: +{len(new_rows)} bars -> {len(final)} total", flush=True)
    return final


def _fetch_gi_history_ticker(ticker: str, since: str | None = None) -> list[dict]:
    params = {
        "select": "date,gi_score,gi_zone,inv_rsi,rel_vol",
        "ticker": f"eq.{ticker}",
        "order": "date.asc",
    }
    if since:
        params["date"] = f"gt.{since}"
    return _supa_get("gekko_index", params)


def _fetch_zone_returns() -> list[dict]:
    return _supa_get("gi_zone_returns", {
        "select": "ticker,zone,avg_5d,avg_10d,avg_20d,avg_30d,avg_50d,sample_count",
    })


def _get_gekko_session() -> str | None:
    """Read Gekko session cookie from DATA/gekko_session.txt (if it exists)."""
    try:
        if GEKKO_SESSION_FILE.exists():
            val = GEKKO_SESSION_FILE.read_text(encoding="utf-8").strip()
            return val if val else None
    except Exception:
        pass
    return None


def _fetch_fair_value_proxy(ticker: str) -> dict | None:
    """Fetch fair value from dashboard.gekko.app using the stored session cookie."""
    session = _get_gekko_session()
    if not session:
        return None
    try:
        hdrs = {
            "Cookie":     session,
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://dashboard.gekko.app/",
        }
        r = requests.get(
            f"https://dashboard.gekko.app/api/fundamentals",
            params={"ticker": ticker},
            headers=hdrs,
            timeout=10,
        )
        if not r.ok:
            return None
        payload = r.json()
        stock = payload.get("stock") or {}
        fair_value = stock.get("gekko_fair_value")
        if fair_value is None:
            return None
        fv = float(fair_value)
        if fv <= 0:
            return None
        return {
            "fair_value": fv,
            "method":     str(stock.get("valuation_method") or ""),
            "updated_at": str(payload.get("updated_at") or ""),
        }
    except Exception as e:
        print(f"[fair-value] proxy error for {ticker}: {e}", flush=True)
        return None


def _fetch_earnings_proxy(ticker: str) -> list | None:
    """Fetch earnings data from dashboard.gekko.app using the stored session cookie."""
    session = _get_gekko_session()
    if not session:
        return None
    try:
        hdrs = {
            "Cookie":     session,
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://dashboard.gekko.app/",
        }
        r = requests.get(
            f"https://dashboard.gekko.app/api/earnings",
            params={"ticker": ticker},
            headers=hdrs,
            timeout=10,
        )
        if not r.ok:
            return None
        data = r.json()
        return data if isinstance(data, list) else None
    except Exception as e:
        print(f"[earnings] proxy error for {ticker}: {e}", flush=True)
        return None


def _fetch_ticker_meta(tickers: list[str]) -> dict[str, dict]:
    if not tickers:
        return {}
    out: dict[str, dict] = {}
    batch_size = 100
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            rows = _supa_get("tickers", {
                "select": "ticker,name,sector,industry",
                "ticker": f"in.({','.join(batch)})",
            })
            for r in rows:
                t = str(r.get("ticker") or "").strip().upper()
                if t:
                    out[t] = {"name": str(r.get("name") or ""), "sector": str(r.get("sector") or ""), "industry": str(r.get("industry") or "")}
        except Exception as e:
            print(f"[meta] batch error: {e}", flush=True)
    return out


# ---------------------------------------------------------------------------
# PAYLOAD BUILDERS — convert raw Supabase data to the format the HTML expects
# ---------------------------------------------------------------------------
import re as _re

def _clean_company(name) -> str:
    """Strip XML/SEC CDATA wrappers and normalise company name.

    SEC EDGAR XML feeds store names as  <![CDATA[APPLE INC]]>
    which renders invisible in HTML (browser treats it as a comment).
    Also title-cases ALL-CAPS names for readability.
    """
    s = str(name or "").strip()
    if not s:
        return s
    # Strip <![CDATA[...]]>
    m = _re.match(r"<!\[CDATA\[(.*?)\]\]>", s, _re.DOTALL)
    if m:
        s = m.group(1).strip()
    # If still ALL-CAPS (SEC style), convert to Title Case
    if s and s == s.upper() and len(s) > 2:
        s = s.title()
    return s
def _build_holdings_payload(raw_rows: list[dict], gi_map: dict) -> list[dict]:
    """Enrich holdings with GI score/tier and format for the frontend."""
    out = []
    for r in raw_rows:
        t = str(r.get("ticker") or "").strip().upper()
        score = gi_map.get(t)
        val = float(r.get("value_usd") or 0)
        out.append({
            **r,
            "ticker":        t,
            # Field aliases so the frontend's expected names all resolve
            "company":       _clean_company(r.get("company_name")),
            "manager":       str(r.get("manager_name")  or ""),
            "value":         val,
            "value_fmt":     f"${val:,.0f}",
            "share_chg_pct": r.get("share_change_pct"),
            "gi_score":      round(score, 1) if score is not None else None,
            "gi_tier":       _gi_tier(score),
        })
    return out


def _build_insiders_payload(raw_rows: list[dict], gi_map: dict, name_map: dict | None = None) -> list[dict]:
    out = []
    for r in raw_rows:
        t = str(r.get("ticker") or "").strip().upper()
        if not t:
            continue
        score = gi_map.get(t)

        # Map Supabase column names → frontend field names
        tx_type = str(r.get("transaction_type") or "")
        tx_upper = tx_type.upper()
        is_buy = any(w in tx_upper for w in ("PURCHASE", "BUY", "ACQUI"))
        is_sell = any(w in tx_upper for w in ("SALE", "SELL", "DISPOS"))
        tx_label = "Buy" if is_buy else ("Sell" if is_sell else tx_type or "Unknown")

        out.append({
            "ticker":       t,
            "company":      (name_map or {}).get(t) or _clean_company(r.get("company_name")),
            "insider":      str(r.get("trader_name")  or ""),
            "title":        str(r.get("trader_title") or ""),
            "trans_date":   str(r.get("filing_date")  or ""),
            "filing_date":  str(r.get("filing_date")  or ""),
            "shares":       r.get("shares"),
            "price":        r.get("price_per_share"),
            "total_value":  r.get("total_value"),
            "is_buy":       is_buy,
            "is_sell":      is_sell,
            "tx_label":     tx_label,
            "tx_type":      "B" if is_buy else ("S" if is_sell else "O"),
            "gi_score":     round(score, 1) if score is not None else None,
            "gi_tier":      _gi_tier(score),
        })
    return out


def _build_conviction_payload(holdings: list[dict], insiders: list[dict], gi_map: dict,
                               name_map: dict | None = None) -> list[dict]:
    """Build conviction summary: one row per ticker, aggregating manager + insider signals."""
    # Current holdings only (not SOLD); track per-manager change types
    curr_h: dict[str, dict] = {}
    for r in holdings:
        t = str(r.get("ticker") or "").strip().upper()
        if not t or r.get("change_type") == "SOLD":
            continue
        mgr_name = str(r.get("manager_name") or "").strip()
        ct = str(r.get("change_type") or "")
        if t not in curr_h:
            curr_h[t] = {
                "company":    _clean_company(r.get("company_name")),
                "managers":   set(),
                "new_mgrs":   [],
                "inc_mgrs":   [],
                "total_value": 0.0,
                "new_value":   0.0,   # $ value of positions opened new in latest filing
            }
        elif not curr_h[t]["company"] and r.get("company_name"):
            # Fill in missing company name from a later row for the same ticker
            curr_h[t]["company"] = _clean_company(r.get("company_name"))
        curr_h[t]["managers"].add(mgr_name)
        curr_h[t]["total_value"] += float(r.get("value_usd") or 0)
        if ct == "NEW":
            curr_h[t]["new_value"] += float(r.get("value_usd") or 0)
            if mgr_name and mgr_name not in curr_h[t]["new_mgrs"]:
                curr_h[t]["new_mgrs"].append(mgr_name)
        elif ct == "INCREASED" and mgr_name and mgr_name not in curr_h[t]["inc_mgrs"]:
            curr_h[t]["inc_mgrs"].append(mgr_name)

    # Build company name map from insiders data as fallback for tickers not in holdings
    ins_company: dict[str, str] = {}
    ins_buys:    dict[str, int]  = defaultdict(int)
    ins_sells:   dict[str, int]  = defaultdict(int)
    ins_names:   dict[str, list] = defaultdict(list)
    ins_details: dict[str, list] = defaultdict(list)   # rich lines: "Name  |  $Amount  |  Date"
    for r in insiders:
        t = str(r.get("ticker") or "").strip().upper()
        if not t:
            continue
        cn = _clean_company(r.get("company_name") or r.get("company") or "")
        if cn and t not in ins_company:
            ins_company[t] = cn
        tt   = str(r.get("transaction_type") or "").upper()
        name = str(r.get("trader_name") or r.get("insider") or "").strip()
        if "BUY" in tt or "PURCHASE" in tt or "ACQUIRE" in tt:
            ins_buys[t] += 1
            if name and name not in ins_names[t]:
                ins_names[t].append(name)
            # Build rich detail line with value and date
            val_raw  = r.get("value_usd") or r.get("value") or r.get("total_value")
            date_raw = (r.get("transaction_date") or r.get("filing_date") or r.get("trans_date") or "")
            val_str  = _fmt_money_short(float(val_raw)) if val_raw is not None else ""
            date_str = str(date_raw)[:10] if date_raw else ""
            parts    = [p for p in [name or "Unknown", val_str, date_str] if p]
            ins_details[t].append("  |  ".join(parts))
        elif "SELL" in tt or "SALE" in tt or "DISPOSE" in tt:
            ins_sells[t] += 1

    _name_map = name_map or {}
    all_tickers = set(curr_h.keys()) | set(ins_buys.keys()) | set(ins_sells.keys())
    out = []
    for t in sorted(all_tickers):
        h     = curr_h.get(t, {})
        score = gi_map.get(t)
        mgrs  = sorted(h.get("managers", set()))
        tv       = round(h.get("total_value", 0), 2)
        nv       = round(h.get("new_value",   0), 2)
        new_mgrs = h.get("new_mgrs", [])
        inc_mgrs = h.get("inc_mgrs", [])
        # Company name: prefer holdings → insiders → screener name_map
        company = h.get("company") or ins_company.get(t) or _name_map.get(t) or ""
        out.append({
            "ticker":          t,
            "company":         company,
            "manager_count":   len(mgrs),
            "manager_detail":  "\n".join(mgrs),      # newline-sep so tooltip shows one per row
            "total_value":     tv,
            "total_value_fmt": _fmt_money_short(tv),
            # new_value = $ invested in positions opened NEW in latest 13F (not insider trades)
            "new_value":       nv,
            "new_value_fmt":   _fmt_money_short(nv),
            "insider_buys":    ins_buys.get(t, 0),
            "insider_sells":   ins_sells.get(t, 0),
            "insider_detail":  "\n".join(ins_details.get(t, ins_names.get(t, []))),
            "new_count":       len(new_mgrs),
            "new_detail":      "\n".join(new_mgrs),
            "inc_count":       len(inc_mgrs),
            "inc_detail":      "\n".join(inc_mgrs),
            "gi_score":        round(score, 1) if score is not None else None,
            "gi_tier":         _gi_tier(score),
        })
    return out


def _build_buy_meta(insiders: list[dict]) -> dict:
    """Build {ticker: [{price, value, insider, title, date, trans_date}, ...]} for buy-levels chart.
    price = total_value / shares (per-share price at transaction time).
    date = filing_date, trans_date = transaction_date.
    """
    buy_map: dict[str, list] = {}
    for r in insiders:
        t  = str(r.get("ticker") or "").strip().upper()
        tt = str(r.get("transaction_type") or "").upper()
        if not t:
            continue
        if not ("BUY" in tt or "PURCHASE" in tt or "ACQUIRE" in tt):
            continue

        total_val = float(r.get("total_value") or 0)
        shares    = float(r.get("shares") or 0)
        # Prefer an explicit price_per_share field; fall back to total/shares
        price_raw = r.get("price_per_share") or r.get("price")
        if price_raw is not None:
            try:
                price = float(price_raw)
            except (TypeError, ValueError):
                price = None
        else:
            price = round(total_val / shares, 4) if shares > 0 and total_val > 0 else None

        entry = {
            "price":      price,
            "value":      total_val,
            "value_fmt":  f"${total_val:,.0f}" if total_val else "$0",
            "insider":    str(r.get("trader_name") or r.get("insider_name") or r.get("insider") or ""),
            "title":      str(r.get("trader_title") or r.get("title") or r.get("officer_title") or r.get("position") or ""),
            "date":       str(r.get("filing_date") or r.get("transaction_date") or ""),
            "trans_date": str(r.get("transaction_date") or r.get("filing_date") or ""),
            "shares":     shares,
        }
        buy_map.setdefault(t, []).append(entry)
    return buy_map


def _fetch_bubble_size() -> dict:
    """Fetch market_cap (stocks) and net_assets (ETFs) from screener_latest.
    Returns {TICKER: {market_cap: float|None, net_assets: float|None}}.
    Falls back gracefully if columns don't exist.
    """
    result: dict = {}
    # Try fetching market_cap first
    try:
        rows = _supa_get("screener_latest", {
            "select": "ticker,market_cap",
            "market_cap": "gt.0",
        })
        for r in rows:
            t = str(r.get("ticker") or "").strip().upper()
            mc = _safe_float(r.get("market_cap"))
            if t and mc:
                result.setdefault(t, {})["market_cap"] = mc
    except Exception:
        pass  # column may not exist

    # Try net_assets (ETFs)
    try:
        rows = _supa_get("screener_latest", {
            "select": "ticker,net_assets",
            "net_assets": "gt.0",
        })
        for r in rows:
            t = str(r.get("ticker") or "").strip().upper()
            na = _safe_float(r.get("net_assets"))
            if t and na:
                result.setdefault(t, {})["net_assets"] = na
    except Exception:
        pass  # column may not exist

    # If screener_latest has neither column, fall back to Yahoo Finance quotes
    # for the tickers that appear in conviction (the ones actually on the bubble chart).
    # We only do this if we got nothing from Supabase to avoid unnecessary requests.
    if not result:
        try:
            conv_data, _ = payload_get(B_CONVICTION)
            if isinstance(conv_data, list) and conv_data:
                tickers = [r["ticker"] for r in conv_data if r.get("ticker")][:200]
                quotes = _fetch_yahoo_quotes(tickers)
                for sym, q in quotes.items():
                    mc = _safe_float(q.get("marketCap"))
                    na = _safe_float(q.get("totalAssets"))
                    if mc or na:
                        entry: dict = {}
                        if mc: entry["market_cap"] = mc
                        if na: entry["net_assets"]  = na
                        result[sym] = entry
        except Exception as e:
            print(f"[bubble] Yahoo market-cap fallback error: {e}", flush=True)

    return result


def _build_zone_returns_payload(
    raw: list[dict],
    gi_map: dict,
    name_map: dict | None = None,
    sector_map: dict | None = None,
    conv_payload: list[dict] | None = None,
) -> tuple[list[dict], dict]:
    """Build (zr_rows, zr_all) from raw gi_zone_returns rows."""
    name_map   = name_map   or {}
    sector_map = sector_map or {}

    # Build quick lookup from conviction: ticker → {insider_buys, insider_detail, manager_count, manager_detail}
    conv_map: dict[str, dict] = {}
    for row in (conv_payload or []):
        t = str(row.get("ticker") or "").strip().upper()
        if t:
            conv_map[t] = row

    def _score_zone(s):
        if s is None: return None
        if s >= 70: return "buying"
        if s >= 60: return "accumulation"
        if s >= 45: return "neutral"
        if s >= 33: return "distribution"
        return "selling"

    zr_all: dict[str, dict] = {}
    for r in raw:
        t = str(r.get("ticker") or "").strip().upper()
        z = str(r.get("zone") or "")
        if not t or not z:
            continue
        if t not in zr_all:
            zr_all[t] = {}
        zr_all[t][z] = {
            "avg_5d":  r.get("avg_5d"),  "avg_10d": r.get("avg_10d"),
            "avg_20d": r.get("avg_20d"), "avg_30d": r.get("avg_30d"),
            "avg_50d": r.get("avg_50d"), "n": int(r.get("sample_count") or 0),
        }

    zr_rows = []
    for r in raw:
        t = str(r.get("ticker") or "").strip().upper()
        score = gi_map.get(t)
        if _score_zone(score) != r.get("zone"):
            continue
        cv = conv_map.get(t, {})
        zr_rows.append({
            "ticker":          t,
            "company":         name_map.get(t, ""),
            "sector":          sector_map.get(t, ""),
            "zone":            r.get("zone", ""),
            "avg_5d":          r.get("avg_5d"),  "avg_10d": r.get("avg_10d"),
            "avg_20d":         r.get("avg_20d"), "avg_30d": r.get("avg_30d"),
            "avg_50d":         r.get("avg_50d"), "n": int(r.get("sample_count") or 0),
            "insider_buys":    cv.get("insider_buys", 0),
            "insider_detail":  cv.get("insider_detail", ""),
            "manager_count":   cv.get("manager_count", 0),
            "manager_detail":  cv.get("manager_detail", ""),
            "gi_score":        round(score, 1) if score is not None else None,
            "gi_tier":         _gi_tier(score),
        })
    return zr_rows, zr_all


# ---------------------------------------------------------------------------
# RELATIVE ROTATION GRAPH (RRG)
# ---------------------------------------------------------------------------
ROTATION_TICKERS = {
    "sectors": {
        "benchmark": "SHV",
        "tickers": ["XLK","XLF","XLV","XLY","XLI","XLC","XLE","XLB","XLP","XLRE","XLU"],
    },
    "crossAsset": {
        "benchmark": "SHV",
        "tickers": ["SPY","DIA","QQQ","IWM","MDY","VEU","TLT","HYG","GLD","SLV","USO","CPER","IBIT"],
    },
    # 'themes' is populated dynamically from THEMES_ETF_LIST at payload-build time
    "themes": {
        "benchmark": "SPY",  # use SPY for themes (broader equity benchmark)
        "tickers": [],       # filled by _build_rotation_payload
    },
}


def _rrg_ema(values: list, period: int) -> list:
    k = 2.0 / (period + 1)
    result = []
    prev = None
    for v in values:
        if v is None:
            result.append(None)
            continue
        prev = v if prev is None else v * k + prev * (1 - k)
        result.append(prev)
    return result


def _rrg_sma(values: list, period: int) -> list:
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
            continue
        window = [x for x in values[i - period + 1 : i + 1] if x is not None]
        result.append(sum(window) / len(window) if len(window) == period else None)
    return result


def _resample_weekly(bars: list) -> list:
    """Return the last trading bar of each ISO calendar week."""
    from collections import defaultdict
    weeks: dict = defaultdict(list)
    for bar in bars:
        try:
            dt = datetime.strptime(bar["t"], "%Y-%m-%d")
            iso = dt.isocalendar()          # (year, week, weekday)
            key = (iso[0], iso[1])
            weeks[key].append(bar)
        except (ValueError, KeyError):
            continue
    result = []
    for key in sorted(weeks):
        week_bars = sorted(weeks[key], key=lambda b: b["t"])
        result.append(week_bars[-1])
    return result


def _compute_rrg_series(ticker_bars: list, bench_bars: list,
                         ema_period: int = 10, norm_period: int = 26) -> list:
    """
    Compute RS-Ratio (X) and RS-Momentum (Y) series for one ticker vs benchmark.
    Both bar lists should already be weekly-resampled.
    Returns [{date, rsRatio, rsMomentum}, ...] only for rows where both are finite.
    """
    bench_map = {b["t"]: float(b["c"]) for b in bench_bars if b.get("c")}
    tick_map  = {b["t"]: float(b["c"]) for b in ticker_bars if b.get("c")}
    dates = sorted(set(bench_map) & set(tick_map))
    if len(dates) < norm_period + ema_period + 5:
        return []

    # 1. RS-Line = ticker_close / bench_close
    rs_line = [tick_map[d] / bench_map[d] for d in dates]

    # 2. EMA of RS-Line, then normalize to 100 → RS-Ratio
    rs_ema     = _rrg_ema(rs_line, ema_period)
    rs_ema_sma = _rrg_sma(rs_ema, norm_period)
    rs_ratio   = [
        (e / s) * 100 if (e is not None and s) else None
        for e, s in zip(rs_ema, rs_ema_sma)
    ]

    # 3. EMA of RS-Ratio, normalize again → RS-Momentum
    rsr_ema     = _rrg_ema(rs_ratio, ema_period)
    rsr_ema_sma = _rrg_sma(rsr_ema, norm_period)
    rs_momentum = [
        (e / s) * 100 if (e is not None and s) else None
        for e, s in zip(rsr_ema, rsr_ema_sma)
    ]

    result = []
    for i, d in enumerate(dates):
        rr = rs_ratio[i]
        rm = rs_momentum[i]
        if rr is not None and rm is not None:
            result.append({"date": d, "rsRatio": round(rr, 3), "rsMomentum": round(rm, 3)})
    return result


def _build_rotation_payload() -> dict:
    """Compute RRG data for all rotation views from local OHLCV cache + Yahoo fallback."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=730)).strftime("%Y-%m-%d")

    # Populate the dynamic 'themes' view from THEMES_ETF_LIST (deduped, preserving order)
    seen_themes: set = set()
    theme_tickers: list = []
    for ticker, _name, _theme in THEMES_ETF_LIST:
        if ticker and ticker not in seen_themes:
            seen_themes.add(ticker)
            theme_tickers.append(ticker)
    if "themes" in ROTATION_TICKERS:
        ROTATION_TICKERS["themes"]["tickers"] = theme_tickers

    # Collect every unique ticker needed across all views
    all_syms: set = set()
    for cfg in ROTATION_TICKERS.values():
        all_syms.add(cfg["benchmark"])
        all_syms.update(cfg["tickers"])

    # Load / fetch OHLCV for each symbol
    bars_map: dict = {}
    for sym in sorted(all_syms):
        bars = ohlcv_get(sym)
        if not bars:
            try:
                bars = _fetch_ohlcv_supabase(sym, cutoff)
                if bars:
                    ohlcv_upsert(sym, bars)
            except Exception:
                bars = []
        if not bars:
            try:
                bars = _fetch_ohlcv_yahoo(sym, cutoff)
                if bars:
                    ohlcv_upsert(sym, bars)
            except Exception:
                bars = []
        bars_map[sym] = bars
        print(f"[rotation] {sym}: {len(bars)} daily bars", flush=True)

    # Resample to weekly once per symbol
    weekly_map = {sym: _resample_weekly(b) for sym, b in bars_map.items()}

    # Compute RRG series per view / ticker
    payload: dict = {}
    for mode, cfg in ROTATION_TICKERS.items():
        bench_sym  = cfg["benchmark"]
        bench_bars = weekly_map.get(bench_sym, [])
        mode_data: dict = {}
        for sym in cfg["tickers"]:
            series = _compute_rrg_series(weekly_map.get(sym, []), bench_bars)
            if series:
                mode_data[sym] = series
                print(f"[rotation] {mode}/{sym}: {len(series)} weeks computed", flush=True)
            else:
                print(f"[rotation] {mode}/{sym}: insufficient data", flush=True)
        payload[mode] = mode_data

    # 1D % change for every ticker (used by tooltip)
    chg1d: dict = {}
    for sym, bars in bars_map.items():
        if bars and len(bars) >= 2:
            c = float(bars[-1].get("c") or 0)
            p = float(bars[-2].get("c") or 0)
            if p > 0 and c > 0:
                chg1d[sym] = round((c / p - 1) * 100, 2)
    payload["_chg1d"] = chg1d

    # Themes ticker metadata (name + theme group) so the client can render labels
    # for the 'themes' view without hardcoding the ticker list.
    themes_meta = []
    for ticker, name, theme_group in THEMES_ETF_LIST:
        themes_meta.append({"ticker": ticker, "name": name, "theme": theme_group})
    payload["_themesMeta"] = themes_meta

    return payload


def _build_themes_payload(gi_map: dict, force: bool = False) -> list[dict]:
    """Build themes data from THEMES_ETF_LIST + GI scores + OHLCV returns."""
    today = datetime.now(timezone.utc).date()
    ytd_start = f"{today.year}-01-01"
    cutoff = (datetime.now(timezone.utc) - timedelta(days=OHLCV_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    def _pct(current, base):
        try:
            c, b = float(current), float(base)
            if b > 0 and c > 0:
                return round((c / b - 1) * 100, 2)
        except (TypeError, ValueError):
            pass
        return None

    def _price_at_offset(bars: list, offset_days: int) -> float | None:
        """Return close price N calendar days before last bar."""
        if not bars:
            return None
        target = (today - timedelta(days=offset_days)).isoformat()
        for bar in reversed(bars):
            if bar["t"] <= target:
                v = bar.get("c")
                return float(v) if v else None
        return None

    def _price_at_or_before(bars: list, date_str: str) -> float | None:
        for bar in reversed(bars):
            if bar["t"] <= date_str:
                v = bar.get("c")
                return float(v) if v else None
        return None

    # --- Pre-fetch OHLCV for all themes tickers concurrently ---
    # Tickers not already in SQLite cache are fetched from Supabase or Yahoo in parallel.
    # Doing this once upfront avoids sequential blocking in the render loop below.
    # Refresh OHLCV for tickers that are missing or stale (today's bar not yet present)
    if force:
        stale_ohlcv = [t for t, _, _ in THEMES_ETF_LIST]
    else:
        stale_ohlcv = [t for t, _, _ in THEMES_ETF_LIST if not ohlcv_get(t) or _ohlcv_is_stale(t)]
    if stale_ohlcv:
        print(f"[themes] Refreshing OHLCV for {len(stale_ohlcv)} {'(forced)' if force else 'stale/missing'} tickers...", flush=True)
        def _refresh_ohlcv(sym: str) -> None:
            try:
                bars = _fetch_ohlcv_supabase(sym, cutoff)
                if bars:
                    ohlcv_upsert(sym, bars)
                    return
            except Exception:
                pass
            try:
                time.sleep(0.15)
                bars = _fetch_ohlcv_yahoo(sym, cutoff)
                if bars:
                    ohlcv_upsert(sym, bars)
            except Exception as e:
                print(f"[themes] Yahoo OHLCV error {sym}: {e}", flush=True)
        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(_refresh_ohlcv, stale_ohlcv))
        print(f"[themes] OHLCV refresh done.", flush=True)

    result = []
    for ticker, name, theme in THEMES_ETF_LIST:
        bars = ohlcv_get(ticker)

        current = float(bars[-1]["c"]) if bars and bars[-1].get("c") else None

        r1d = r2d = r3d = r4d = r1w = r1m = r3m = r6m = rytd = r1y = r2y = None
        if bars and current:
            def _bar_close(n: int, _b=bars):
                idx = -(n + 1)
                return float(_b[idx]["c"]) if len(_b) > n and _b[idx].get("c") else None
            r1d  = _pct(current, _bar_close(1))
            r2d  = _pct(current, _bar_close(2))
            r3d  = _pct(current, _bar_close(3))
            r4d  = _pct(current, _bar_close(4))
            r1w  = _pct(current, _price_at_offset(bars, 7))
            r1m  = _pct(current, _price_at_offset(bars, 31))
            r3m  = _pct(current, _price_at_offset(bars, 92))
            r6m  = _pct(current, _price_at_offset(bars, 183))
            rytd = _pct(current, _price_at_or_before(bars, ytd_start))
            r1y  = _pct(current, _price_at_offset(bars, 365))
            r2y  = _pct(current, _price_at_offset(bars, 730))

        score = gi_map.get(ticker)
        result.append({
            "ticker":   ticker,
            "name":     name,
            "theme":    theme,
            "cat":      theme,
            "gi":       round(score, 1) if score is not None else None,
            "gi_tier":  _gi_tier(score),
            "r1d":      r1d,
            "r2d":      r2d,
            "r3d":      r3d,
            "r4d":      r4d,
            "r1w":      r1w,
            "r1m":      r1m,
            "r3m":      r3m,
            "r6m":      r6m,
            "rytd":     rytd,
            "r1y":      r1y,
            "r2y":      r2y,
            "close":    current,
        })

    # --- Append MAJORS_EXTRA tickers (hidden from Themes tab, visible to Majors view) ---
    majors_missing = [t for t, _ in MAJORS_EXTRA if not ohlcv_get(t)]
    if majors_missing:
        with ThreadPoolExecutor(max_workers=2) as ex:
            list(ex.map(_ensure_ohlcv, majors_missing))

    for ticker, name in MAJORS_EXTRA:
        bars = ohlcv_get(ticker)
        current = float(bars[-1]["c"]) if bars and bars[-1].get("c") else None
        r1d = r1w = r1m = r3m = r6m = rytd = r1y = None
        if bars and current:
            def _bar_close_m(n: int, _bars=bars):
                idx = -(n + 1)
                return float(_bars[idx]["c"]) if len(_bars) > n and _bars[idx].get("c") else None
            r1d  = _pct(current, _bar_close_m(1))
            r1w  = _pct(current, _price_at_offset(bars, 7))
            r1m  = _pct(current, _price_at_offset(bars, 31))
            r3m  = _pct(current, _price_at_offset(bars, 92))
            r6m  = _pct(current, _price_at_offset(bars, 183))
            rytd = _pct(current, _price_at_or_before(bars, ytd_start))
            r1y  = _pct(current, _price_at_offset(bars, 365))
        score = gi_map.get(ticker)
        result.append({
            "ticker":  ticker,
            "name":    name,
            "theme":   "_majors_only",
            "cat":     "_majors_only",
            "gi":      round(score, 1) if score is not None else None,
            "gi_tier": _gi_tier(score),
            "r1d": r1d, "r2d": None, "r3d": None, "r4d": None,
            "r1w": r1w, "r1m": r1m, "r3m": r3m,
            "r6m": r6m, "rytd": rytd, "r1y": r1y, "r2y": None,
            "close": current,
        })

    print(f"[themes] Built {len(result)} ETF rows (incl. {len(MAJORS_EXTRA)} majors-only)", flush=True)
    return result


# ---------------------------------------------------------------------------
# S&P 500 HEATMAP — components loaded from DATA/sp500_components.json
# Auto-refreshed weekly from Wikipedia. Falls back to last saved file.
# ---------------------------------------------------------------------------
SP500_COMPONENTS_FILE = DATA_DIR / "sp500_components.json"
_SP500_LIST_CACHE: list[tuple[str, str, str]] | None = None

def _fetch_sp500_wikipedia() -> list[tuple[str, str, str]]:
    """Fetch current S&P 500 components from Wikipedia. Returns list of (ticker, name, sector).

    Parses the table cell-by-cell rather than with a single fragile regex so that
    rows with extra text in the company-name cell (e.g. Alphabet 'Class A/C') are
    handled correctly and don't slide column offsets onto the date field.
    """
    import re

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    def _strip_tags(s: str) -> str:
        return re.sub(r"<[^>]+>", "", s).strip()

    # Wikipedia's S&P 500 constituents table has id="constituents"
    tbl = re.search(r'<table[^>]*id=["\']constituents["\'][^>]*>(.*?)</table>',
                    html, re.DOTALL)
    if not tbl:
        # Fallback: first wikitable on the page
        tbl = re.search(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>',
                        html, re.DOTALL)
    if not tbl:
        return []

    table_html = tbl.group(1)
    result: list[tuple[str, str, str]] = []

    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
        if len(cells) < 3:
            continue

        # Column 0 — ticker symbol (inside an <a> tag)
        sym_match = re.search(r">([A-Z][A-Z0-9.]{0,4})<", cells[0])
        if not sym_match:
            continue
        ticker = sym_match.group(1).replace(".", "-")   # BRK.B → BRK-B

        # Column 1 — company / security name (strip all HTML tags)
        name = _strip_tags(cells[1])
        if not name:
            continue

        # Column 2 — GICS Sector (strip tags; reject if it looks like a date)
        sector = _strip_tags(cells[2])
        if not sector or re.match(r"^\d{4}-\d{2}-\d{2}$", sector):
            continue   # column mis-parsed — skip rather than store garbage

        result.append((ticker, name, sector))

    # Deduplicate share-class duplicates — keep only the preferred share class.
    # e.g. GOOGL (Class A) is kept; GOOG (Class C) is dropped.
    # Add more pairs here if other dual-class stocks cause the same issue.
    _DROP_DUPLICATES = {"GOOG"}   # tickers to suppress in favour of their sibling
    result = [(t, n, s) for t, n, s in result if t not in _DROP_DUPLICATES]

    return result

def _load_sp500_list() -> list[tuple[str, str, str]]:
    """Return S&P 500 list, refreshing from Wikipedia if the file is >7 days old or missing."""
    global _SP500_LIST_CACHE
    if _SP500_LIST_CACHE is not None:
        return _SP500_LIST_CACHE

    needs_refresh = True
    if SP500_COMPONENTS_FILE.exists():
        age_days = (time.time() - SP500_COMPONENTS_FILE.stat().st_mtime) / 86400
        if age_days < 7:
            needs_refresh = False

    if needs_refresh:
        try:
            print("[sp500] Fetching S&P 500 components from Wikipedia...", flush=True)
            fresh = _fetch_sp500_wikipedia()
            if len(fresh) >= 450:  # sanity check
                SP500_COMPONENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
                SP500_COMPONENTS_FILE.write_text(
                    json.dumps([{"ticker": t, "name": n, "sector": s} for t, n, s in fresh], indent=2),
                    encoding="utf-8"
                )
                _SP500_LIST_CACHE = fresh
                print(f"[sp500] Saved {len(fresh)} components to {SP500_COMPONENTS_FILE.name}", flush=True)
                return _SP500_LIST_CACHE
            else:
                print(f"[sp500] Wikipedia returned only {len(fresh)} rows — skipping update", flush=True)
        except Exception as e:
            print(f"[sp500] Wikipedia fetch error: {e}", flush=True)

    if SP500_COMPONENTS_FILE.exists():
        try:
            import re as _re
            data = json.loads(SP500_COMPONENTS_FILE.read_text(encoding="utf-8"))
            loaded = [(r["ticker"], r["name"], r["sector"]) for r in data]
            # If the cached file has any date-like sector values (from the old
            # buggy parser), treat the file as corrupt and force a re-fetch.
            if any(_re.match(r"^\d{4}-\d{2}-\d{2}$", s) for _, _, s in loaded):
                print("[sp500] Cached file has corrupt sector data — forcing re-fetch", flush=True)
                SP500_COMPONENTS_FILE.unlink(missing_ok=True)
                _SP500_LIST_CACHE = None
                return _load_sp500_list()   # recurse once with needs_refresh=True
            _SP500_LIST_CACHE = loaded
            print(f"[sp500] Loaded {len(_SP500_LIST_CACHE)} components from file", flush=True)
            return _SP500_LIST_CACHE
        except Exception as e:
            print(f"[sp500] File load error: {e}", flush=True)

    # Ultimate fallback — empty (heatmap will show nothing but won't crash)
    _SP500_LIST_CACHE = []
    return _SP500_LIST_CACHE


# Keep SP500_LIST as a property-like accessor for backward compatibility
# (used in _build_sp500_payload and _fetch_gi_scores)
SP500_LIST_STUB = [
    # INFORMATION TECHNOLOGY — minimal fallback, replaced at runtime
    ("AAPL",  "Apple",               "Information Technology"),
    ("MSFT",  "Microsoft",           "Information Technology"),
    ("NVDA",  "NVIDIA",              "Information Technology"),
    ("AVGO",  "Broadcom",            "Information Technology"),
    ("ORCL",  "Oracle",              "Information Technology"),
    ("AMD",   "AMD",                 "Information Technology"),
    ("QCOM",  "Qualcomm",            "Information Technology"),
    ("TXN",   "Texas Instruments",   "Information Technology"),
    ("AMAT",  "Applied Materials",   "Information Technology"),
    ("MU",    "Micron",              "Information Technology"),
    ("KLAC",  "KLA Corp",            "Information Technology"),
    ("ADI",   "Analog Devices",      "Information Technology"),
    ("LRCX",  "Lam Research",        "Information Technology"),
    ("MCHP",  "Microchip Tech",      "Information Technology"),
    ("CSCO",  "Cisco",               "Information Technology"),
    ("IBM",   "IBM",                 "Information Technology"),
    ("INTC",  "Intel",               "Information Technology"),
    ("HPQ",   "HP Inc",              "Information Technology"),
    ("HPE",   "Hewlett Packard Ent", "Information Technology"),
    ("ANET",  "Arista Networks",     "Information Technology"),
    ("PANW",  "Palo Alto Networks",  "Information Technology"),
    ("FTNT",  "Fortinet",            "Information Technology"),
    ("CRWD",  "CrowdStrike",         "Information Technology"),
    ("NOW",   "ServiceNow",          "Information Technology"),
    ("SNPS",  "Synopsys",            "Information Technology"),
    ("CDNS",  "Cadence Design",      "Information Technology"),
    ("ADBE",  "Adobe",               "Information Technology"),
    ("CRM",   "Salesforce",          "Information Technology"),
    ("ACN",   "Accenture",           "Information Technology"),
    ("INTU",  "Intuit",              "Information Technology"),
    ("FSLR",  "First Solar",         "Information Technology"),
    ("GEN",   "Gen Digital",         "Information Technology"),
    ("EPAM",  "EPAM Systems",        "Information Technology"),
    ("CTSH",  "Cognizant",           "Information Technology"),
    ("WIT",   "Wipro",               "Information Technology"),

    # COMMUNICATION SERVICES
    ("GOOGL", "Alphabet A",          "Communication Services"),
    ("GOOG",  "Alphabet C",          "Communication Services"),
    ("META",  "Meta",                "Communication Services"),
    ("NFLX",  "Netflix",             "Communication Services"),
    ("DIS",   "Disney",              "Communication Services"),
    ("CMCSA", "Comcast",             "Communication Services"),
    ("T",     "AT&T",                "Communication Services"),
    ("VZ",    "Verizon",             "Communication Services"),
    ("TMUS",  "T-Mobile",            "Communication Services"),
    ("EA",    "Electronic Arts",     "Communication Services"),
    ("TTWO",  "Take-Two",            "Communication Services"),
    ("LYV",   "Live Nation",         "Communication Services"),
    ("OMC",   "Omnicom",             "Communication Services"),
    ("FOXA",  "Fox Corp A",          "Communication Services"),
    ("WBD",   "Warner Bros",         "Communication Services"),
    ("PARA",  "Paramount",           "Communication Services"),

    # FINANCIALS
    ("BRK.B", "Berkshire B",         "Financials"),
    ("JPM",   "JPMorgan",            "Financials"),
    ("V",     "Visa",                "Financials"),
    ("MA",    "Mastercard",          "Financials"),
    ("BAC",   "Bank of America",     "Financials"),
    ("WFC",   "Wells Fargo",         "Financials"),
    ("GS",    "Goldman Sachs",       "Financials"),
    ("MS",    "Morgan Stanley",      "Financials"),
    ("AXP",   "Amex",                "Financials"),
    ("BLK",   "BlackRock",           "Financials"),
    ("C",     "Citigroup",           "Financials"),
    ("SCHW",  "Schwab",              "Financials"),
    ("CB",    "Chubb",               "Financials"),
    ("PGR",   "Progressive",         "Financials"),
    ("MET",   "MetLife",             "Financials"),
    ("TRV",   "Travelers",           "Financials"),
    ("AON",   "Aon",                 "Financials"),
    ("MMC",   "Marsh McLennan",      "Financials"),
    ("AFL",   "Aflac",               "Financials"),
    ("ALL",   "Allstate",            "Financials"),
    ("COF",   "Capital One",         "Financials"),
    ("USB",   "US Bancorp",          "Financials"),
    ("TFC",   "Truist",              "Financials"),
    ("PNC",   "PNC Financial",       "Financials"),
    ("STT",   "State Street",        "Financials"),
    ("BK",    "BNY Mellon",          "Financials"),
    ("FI",    "Fiserv",              "Financials"),
    ("FIS",   "FIS",                 "Financials"),
    ("PYPL",  "PayPal",              "Financials"),
    ("ICE",   "ICE",                 "Financials"),
    ("CME",   "CME Group",           "Financials"),
    ("NDAQ",  "Nasdaq Inc",          "Financials"),
    ("SPGI",  "S&P Global",          "Financials"),
    ("MCO",   "Moody's",             "Financials"),
    ("MSCI",  "MSCI",                "Financials"),

    # HEALTH CARE
    ("LLY",   "Eli Lilly",           "Health Care"),
    ("JNJ",   "Johnson & Johnson",   "Health Care"),
    ("UNH",   "UnitedHealth",        "Health Care"),
    ("ABT",   "Abbott",              "Health Care"),
    ("MRK",   "Merck",               "Health Care"),
    ("TMO",   "Thermo Fisher",       "Health Care"),
    ("DHR",   "Danaher",             "Health Care"),
    ("AMGN",  "Amgen",               "Health Care"),
    ("ISRG",  "Intuitive Surgical",  "Health Care"),
    ("MDT",   "Medtronic",           "Health Care"),
    ("ZTS",   "Zoetis",              "Health Care"),
    ("ELV",   "Elevance",            "Health Care"),
    ("CI",    "Cigna",               "Health Care"),
    ("HUM",   "Humana",              "Health Care"),
    ("HCA",   "HCA Healthcare",      "Health Care"),
    ("BMY",   "Bristol-Myers",       "Health Care"),
    ("PFE",   "Pfizer",              "Health Care"),
    ("ABBV",  "AbbVie",              "Health Care"),
    ("BIIB",  "Biogen",              "Health Care"),
    ("GILD",  "Gilead",              "Health Care"),
    ("REGN",  "Regeneron",           "Health Care"),
    ("VRTX",  "Vertex Pharma",       "Health Care"),
    ("DXCM",  "Dexcom",              "Health Care"),
    ("BSX",   "Boston Scientific",   "Health Care"),
    ("SYK",   "Stryker",             "Health Care"),
    ("BDX",   "Becton Dickinson",    "Health Care"),
    ("EW",    "Edwards Lifesci",     "Health Care"),
    ("IDXX",  "Idexx Labs",          "Health Care"),
    ("IQV",   "IQVIA",               "Health Care"),
    ("COR",   "Cencora",             "Health Care"),
    ("MCK",   "McKesson",            "Health Care"),

    # CONSUMER STAPLES
    ("WMT",   "Walmart",             "Consumer Staples"),
    ("PG",    "Procter & Gamble",    "Consumer Staples"),
    ("KO",    "Coca-Cola",           "Consumer Staples"),
    ("PEP",   "PepsiCo",             "Consumer Staples"),
    ("COST",  "Costco",              "Consumer Staples"),
    ("PM",    "Philip Morris",       "Consumer Staples"),
    ("MO",    "Altria",              "Consumer Staples"),
    ("CL",    "Colgate",             "Consumer Staples"),
    ("KMB",   "Kimberly-Clark",      "Consumer Staples"),
    ("MDLZ",  "Mondelez",            "Consumer Staples"),
    ("GIS",   "General Mills",       "Consumer Staples"),
    ("K",     "Kellanova",           "Consumer Staples"),
    ("HSY",   "Hershey",             "Consumer Staples"),
    ("MKC",   "McCormick",           "Consumer Staples"),
    ("SJM",   "J.M. Smucker",       "Consumer Staples"),
    ("HRL",   "Hormel",              "Consumer Staples"),
    ("CAG",   "ConAgra",             "Consumer Staples"),
    ("KR",    "Kroger",              "Consumer Staples"),
    ("SYY",   "Sysco",               "Consumer Staples"),

    # CONSUMER DISCRETIONARY
    ("AMZN",  "Amazon",              "Consumer Discretionary"),
    ("TSLA",  "Tesla",               "Consumer Discretionary"),
    ("HD",    "Home Depot",          "Consumer Discretionary"),
    ("MCD",   "McDonald's",          "Consumer Discretionary"),
    ("NKE",   "Nike",                "Consumer Discretionary"),
    ("SBUX",  "Starbucks",           "Consumer Discretionary"),
    ("LOW",   "Lowe's",              "Consumer Discretionary"),
    ("TJX",   "TJX Companies",       "Consumer Discretionary"),
    ("BKNG",  "Booking Holdings",    "Consumer Discretionary"),
    ("CMG",   "Chipotle",            "Consumer Discretionary"),
    ("HLT",   "Hilton",              "Consumer Discretionary"),
    ("MAR",   "Marriott",            "Consumer Discretionary"),
    ("F",     "Ford",                "Consumer Discretionary"),
    ("GM",    "General Motors",      "Consumer Discretionary"),
    ("YUM",   "Yum! Brands",         "Consumer Discretionary"),
    ("DPZ",   "Domino's",            "Consumer Discretionary"),
    ("DLTR",  "Dollar Tree",         "Consumer Discretionary"),
    ("DG",    "Dollar General",      "Consumer Discretionary"),
    ("ROST",  "Ross Stores",         "Consumer Discretionary"),
    ("TGT",   "Target",              "Consumer Discretionary"),
    ("BBY",   "Best Buy",            "Consumer Discretionary"),
    ("ETSY",  "Etsy",                "Consumer Discretionary"),
    ("ABNB",  "Airbnb",              "Consumer Discretionary"),
    ("LVS",   "Las Vegas Sands",     "Consumer Discretionary"),
    ("MGM",   "MGM Resorts",         "Consumer Discretionary"),
    ("RCL",   "Royal Caribbean",     "Consumer Discretionary"),
    ("CCL",   "Carnival",            "Consumer Discretionary"),
    ("PHM",   "PulteGroup",          "Consumer Discretionary"),
    ("DHI",   "D.R. Horton",         "Consumer Discretionary"),
    ("NVR",   "NVR",                 "Consumer Discretionary"),
    ("LEN",   "Lennar",              "Consumer Discretionary"),

    # INDUSTRIALS
    ("GE",    "GE Aerospace",        "Industrials"),
    ("RTX",   "RTX",                 "Industrials"),
    ("HON",   "Honeywell",           "Industrials"),
    ("CAT",   "Caterpillar",         "Industrials"),
    ("UPS",   "UPS",                 "Industrials"),
    ("LMT",   "Lockheed Martin",     "Industrials"),
    ("DE",    "Deere & Co",          "Industrials"),
    ("EMR",   "Emerson Electric",    "Industrials"),
    ("ITW",   "Illinois Tool Works", "Industrials"),
    ("PH",    "Parker Hannifin",     "Industrials"),
    ("ETN",   "Eaton",               "Industrials"),
    ("GWW",   "W.W. Grainger",       "Industrials"),
    ("CTAS",  "Cintas",              "Industrials"),
    ("FAST",  "Fastenal",            "Industrials"),
    ("ROK",   "Rockwell Auto",       "Industrials"),
    ("XYL",   "Xylem",               "Industrials"),
    ("DOV",   "Dover",               "Industrials"),
    ("IR",    "Ingersoll Rand",      "Industrials"),
    ("TT",    "Trane Technologies",  "Industrials"),
    ("CPRT",  "Copart",              "Industrials"),
    ("ROP",   "Roper Technologies",  "Industrials"),
    ("FTV",   "Fortive",             "Industrials"),
    ("AME",   "AMETEK",              "Industrials"),
    ("TDG",   "TransDigm",           "Industrials"),
    ("NOC",   "Northrop Grumman",    "Industrials"),
    ("GD",    "General Dynamics",    "Industrials"),
    ("BA",    "Boeing",              "Industrials"),
    ("FDX",   "FedEx",               "Industrials"),
    ("CSX",   "CSX",                 "Industrials"),
    ("NSC",   "Norfolk Southern",    "Industrials"),
    ("UNP",   "Union Pacific",       "Industrials"),
    ("UBER",  "Uber",                "Industrials"),
    ("LYFT",  "Lyft",                "Industrials"),
    ("WM",    "Waste Management",    "Industrials"),
    ("RSG",   "Republic Services",   "Industrials"),

    # ENERGY
    ("XOM",   "ExxonMobil",          "Energy"),
    ("CVX",   "Chevron",             "Energy"),
    ("COP",   "ConocoPhillips",      "Energy"),
    ("SLB",   "SLB",                 "Energy"),
    ("EOG",   "EOG Resources",       "Energy"),
    ("VLO",   "Valero Energy",       "Energy"),
    ("MPC",   "Marathon Petroleum",  "Energy"),
    ("PSX",   "Phillips 66",         "Energy"),
    ("OXY",   "Occidental",          "Energy"),
    ("HAL",   "Halliburton",         "Energy"),
    ("BKR",   "Baker Hughes",        "Energy"),
    ("DVN",   "Devon Energy",        "Energy"),
    ("FANG",  "Diamondback Energy",  "Energy"),
    ("APA",   "APA Corp",            "Energy"),
    ("MRO",   "Marathon Oil",        "Energy"),
    ("KMI",   "Kinder Morgan",       "Energy"),
    ("WMB",   "Williams Cos",        "Energy"),
    ("OKE",   "ONEOK",               "Energy"),
    ("LNG",   "Cheniere Energy",     "Energy"),

    # REAL ESTATE
    ("AMT",   "American Tower",      "Real Estate"),
    ("PLD",   "Prologis",            "Real Estate"),
    ("CCI",   "Crown Castle",        "Real Estate"),
    ("SPG",   "Simon Property",      "Real Estate"),
    ("PSA",   "Public Storage",      "Real Estate"),
    ("EQIX",  "Equinix",             "Real Estate"),
    ("O",     "Realty Income",       "Real Estate"),
    ("VTR",   "Ventas",              "Real Estate"),
    ("WELL",  "Welltower",           "Real Estate"),
    ("EQR",   "Equity Residential",  "Real Estate"),
    ("AVB",   "AvalonBay",           "Real Estate"),
    ("EXR",   "Extra Space Storage", "Real Estate"),
    ("INVH",  "Invitation Homes",    "Real Estate"),
    ("BXP",   "Boston Properties",   "Real Estate"),
    ("VNO",   "Vornado",             "Real Estate"),
    ("KIM",   "Kimco Realty",        "Real Estate"),
    ("DLR",   "Digital Realty",      "Real Estate"),
    ("SBAC",  "SBA Comm",            "Real Estate"),
    ("IRM",   "Iron Mountain",       "Real Estate"),
    ("NNN",   "NNN REIT",            "Real Estate"),

    # MATERIALS
    ("LIN",   "Linde",               "Materials"),
    ("SHW",   "Sherwin-Williams",    "Materials"),
    ("APD",   "Air Products",        "Materials"),
    ("ECL",   "Ecolab",              "Materials"),
    ("PPG",   "PPG Industries",      "Materials"),
    ("NEM",   "Newmont",             "Materials"),
    ("FCX",   "Freeport-McMoRan",    "Materials"),
    ("NUE",   "Nucor",               "Materials"),
    ("STLD",  "Steel Dynamics",      "Materials"),
    ("RS",    "Reliance Steel",      "Materials"),
    ("PKG",   "Packaging Corp",      "Materials"),
    ("IP",    "International Paper", "Materials"),
    ("MLM",   "Martin Marietta",     "Materials"),
    ("VMC",   "Vulcan Materials",    "Materials"),
    ("BALL",  "Ball Corp",           "Materials"),
    ("CF",    "CF Industries",       "Materials"),
    ("MOS",   "Mosaic",              "Materials"),

    # UTILITIES
    ("NEE",   "NextEra Energy",      "Utilities"),
    ("DUK",   "Duke Energy",         "Utilities"),
    ("SO",    "Southern Co",         "Utilities"),
    ("AEP",   "AEP",                 "Utilities"),
    ("EXC",   "Exelon",              "Utilities"),
    ("SRE",   "Sempra",              "Utilities"),
    ("PCG",   "PG&E",                "Utilities"),
    ("ED",    "Con Edison",          "Utilities"),
    ("EIX",   "Edison Intl",         "Utilities"),
    ("ETR",   "Entergy",             "Utilities"),
    ("PEG",   "PSEG",                "Utilities"),
    ("FE",    "FirstEnergy",         "Utilities"),
    ("DTE",   "DTE Energy",          "Utilities"),
    ("PPL",   "PPL Corp",            "Utilities"),
    ("WEC",   "WEC Energy",          "Utilities"),
    ("AWK",   "American Water",      "Utilities"),
    ("AES",   "AES Corp",            "Utilities"),
    ("CMS",   "CMS Energy",          "Utilities"),
    ("CNP",   "CenterPoint",         "Utilities"),
    ("NI",    "NiSource",            "Utilities"),
    ("EVRG",  "Evergy",              "Utilities"),
    ("XEL",   "Xcel Energy",         "Utilities"),
]
# SP500_LIST is resolved at call-time so it always uses the freshest data
def _get_sp500_list() -> list[tuple[str, str, str]]:
    lst = _load_sp500_list()
    return lst if lst else SP500_LIST_STUB


def _build_sp500_payload(gi_map: dict, force: bool = False) -> list[dict]:
    """Build S&P 500 heatmap payload using live SP500 components + market caps + OHLCV."""
    today = datetime.now(timezone.utc).date()
    ytd_start = f"{today.year}-01-01"
    cutoff = (datetime.now(timezone.utc) - timedelta(days=OHLCV_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    def _pct(current, base):
        try:
            c, b = float(current), float(base)
            if b > 0 and c > 0:
                return round((c / b - 1) * 100, 2)
        except (TypeError, ValueError):
            pass
        return None

    def _price_at_offset(bars: list, offset_days: int) -> float | None:
        if not bars:
            return None
        target = (today - timedelta(days=offset_days)).isoformat()
        for bar in reversed(bars):
            if bar["t"] <= target:
                v = bar.get("c")
                return float(v) if v else None
        return None

    def _price_at_or_before(bars: list, date_str: str) -> float | None:
        for bar in reversed(bars):
            if bar["t"] <= date_str:
                v = bar.get("c")
                return float(v) if v else None
        return None

    # Fetch market caps from Supabase screener_latest
    cap_map: dict[str, float] = {}
    try:
        rows = _supa_get("screener_latest", {"select": "ticker,market_cap", "market_cap": "gt.0"})
        for r in rows:
            t = str(r.get("ticker") or "").strip().upper()
            mc = _safe_float(r.get("market_cap"))
            if t and mc:
                cap_map[t] = mc
    except Exception as e:
        print(f"[sp500] market cap fetch error: {e}", flush=True)

    # Pre-fetch OHLCV — force refreshes all tickers, otherwise only missing ones
    sp500_list = _get_sp500_list()
    all_syms = [t for t, _, _ in sp500_list]
    to_fetch = all_syms if force else [s for s in all_syms if not ohlcv_get(s)]
    if to_fetch:
        print(f"[sp500] {'Force-refreshing' if force else 'Pre-fetching'} OHLCV for {len(to_fetch)} tickers...", flush=True)
        def _ensure(sym: str) -> None:
            try:
                bars = _fetch_ohlcv_supabase(sym, cutoff)
                if bars:
                    ohlcv_upsert(sym, bars)
                    return
            except Exception:
                pass
            try:
                time.sleep(0.12)
                bars = _fetch_ohlcv_yahoo(sym, cutoff)
                if bars:
                    ohlcv_upsert(sym, bars)
            except Exception:
                pass
        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(_ensure, to_fetch))
        print("[sp500] OHLCV fetch done.", flush=True)

    result = []
    for ticker, name, sector in sp500_list:
        bars = ohlcv_get(ticker)
        current = float(bars[-1]["c"]) if bars and bars[-1].get("c") else None

        r1d = r1w = r1m = r3m = r6m = rytd = r1y = None
        if bars and current:
            def _bar_close(n: int):
                idx = -(n + 1)
                return float(bars[idx]["c"]) if len(bars) > n and bars[idx].get("c") else None
            r1d = _pct(current, _bar_close(1))
            r1w = _pct(current, _price_at_offset(bars, 7))
            r1m = _pct(current, _price_at_offset(bars, 31))
            r3m = _pct(current, _price_at_offset(bars, 92))
            r6m = _pct(current, _price_at_offset(bars, 183))
            rytd = _pct(current, _price_at_or_before(bars, ytd_start))
            r1y = _pct(current, _price_at_offset(bars, 365))

        score = gi_map.get(ticker)
        mc = cap_map.get(ticker)
        result.append({
            "ticker":     ticker,
            "name":       name,
            "sector":     sector,
            "gi":         round(score, 1) if score is not None else None,
            "gi_tier":    _gi_tier(score),
            "market_cap": mc,
            "r1d":        r1d,
            "r1w":        r1w,
            "r1m":        r1m,
            "r3m":        r3m,
            "r6m":        r6m,
            "rytd":       rytd,
            "r1y":        r1y,
            "close":      current,
        })

    print(f"[sp500] Built {len(result)} stock rows", flush=True)
    return result


def _build_reversals_payload() -> dict[str, list[dict]]:
    """
    Compute in-house reversals for every ticker that has both GI history and OHLCV data.
    Returns {ticker: [{d, t, p}, ...]}
    """
    # Load all per-ticker GI history rows from payload_cache in one query
    gi_by_ticker: dict[str, list[dict]] = {}
    try:
        with _pconn() as c:
            rows = c.execute(
                "SELECT cache_key, data_json FROM payload_cache WHERE bucket=?",
                (B_GI_HIST_PER,),
            ).fetchall()
        for row in rows:
            ticker = str(row["cache_key"]).strip().upper()
            try:
                data = json.loads(row["data_json"])
                if isinstance(data, list) and data:
                    gi_by_ticker[ticker] = sorted(data, key=lambda r: r.get("date") or r.get("t") or r.get("d") or "")
            except Exception:
                pass
    except Exception as e:
        print(f"[reversals] GI history load error: {e}", flush=True)

    if not gi_by_ticker:
        return {}

    # Load all OHLCV close prices in one query → {ticker: {date: close}}
    price_by_ticker: dict[str, dict[str, float]] = {}
    try:
        with _oconn() as c:
            bars = c.execute("SELECT ticker, date, close FROM ohlcv_bars").fetchall()
        for b in bars:
            t = str(b["ticker"]).strip().upper()
            if t not in price_by_ticker:
                price_by_ticker[t] = {}
            if b["close"] is not None:
                price_by_ticker[t][b["date"]] = float(b["close"])
    except Exception as e:
        print(f"[reversals] OHLCV load error: {e}", flush=True)

    result: dict[str, list[dict]] = {}
    for ticker, gi_rows in gi_by_ticker.items():
        price_map = price_by_ticker.get(ticker, {})
        signals = _compute_reversals_for_ticker(gi_rows, price_map)
        if signals:
            result[ticker] = signals

    print(f"[reversals] Computed signals for {len(result):,} tickers", flush=True)
    return result


# ---------------------------------------------------------------------------
# BACKGROUND SYNC
# ---------------------------------------------------------------------------
_sync_lock      = threading.Lock()
_sync_running   = False
_last_full_sync_ts: str | None = None   # ISO-8601, set on completion


def _run_full_sync() -> None:
    """Fetch all bulk data from Supabase and update SQLite. Called in background thread."""
    global _sync_running
    with _sync_lock:
        if _sync_running:
            return
        _sync_running = True
    _tray_fetch_start()
    try:
        print("[sync] Starting full sync...", flush=True)

        # 1. GI scores + company names + sectors
        gi_map:     dict = {}
        name_map:   dict = {}
        sector_map: dict = {}
        try:
            print("[sync] Fetching GI scores...", flush=True)
            gi_map, name_map, sector_map = _fetch_gi_scores()
            if gi_map:
                payload_set(B_GI_SCORE, gi_map)
            if name_map:
                payload_set(B_NAMES, name_map)
            print(f"[sync] GI scores: {len(gi_map):,} tickers", flush=True)
        except Exception as e:
            print(f"[sync] GI scores error: {e}", flush=True)

        # 2. Holdings
        raw_h: list = []
        try:
            print("[sync] Fetching holdings...", flush=True)
            raw_h = _fetch_holdings_raw()
            h_payload = _build_holdings_payload(raw_h, gi_map)
            payload_set(B_HOLDINGS, h_payload)
            print(f"[sync] Holdings: {len(h_payload):,} rows", flush=True)
        except Exception as e:
            print(f"[sync] Holdings error: {e}", flush=True)

        # 3. Insiders
        raw_i: list = []
        try:
            print("[sync] Fetching insider trades...", flush=True)
            raw_i = _fetch_insiders_raw()
            i_payload = _build_insiders_payload(raw_i, gi_map, name_map)
            payload_set(B_INSIDERS, i_payload)
            print(f"[sync] Insiders: {len(i_payload):,} rows", flush=True)
        except Exception as e:
            print(f"[sync] Insiders error: {e}", flush=True)

        # 4. Conviction + buy-meta (derived from holdings + insiders)
        c_payload: list = []
        try:
            print("[sync] Building conviction...", flush=True)
            # Collect all tickers that will appear in conviction so we can
            # enrich any missing company names from Yahoo before building.
            conv_tickers = list({
                str(r.get("ticker") or "").strip().upper()
                for r in (raw_h + raw_i)
                if r.get("ticker")
            })
            name_map = _enrich_name_map(name_map, conv_tickers)
            if name_map:
                payload_set(B_NAMES, name_map)
            c_payload = _build_conviction_payload(raw_h, raw_i, gi_map, name_map)
            payload_set(B_CONVICTION, c_payload)
            bm_payload = _build_buy_meta(raw_i)
            payload_set(B_BUY_META, bm_payload)
            print(f"[sync] Conviction: {len(c_payload):,} tickers", flush=True)
        except Exception as e:
            print(f"[sync] Conviction error: {e}", flush=True)

        # 4b. Bubble size data (market cap / net assets for bubble chart)
        try:
            print("[sync] Fetching bubble size data...", flush=True)
            bubble_data = _fetch_bubble_size()
            payload_set(B_BUBBLE, bubble_data)
            print(f"[sync] Bubble size: {len(bubble_data):,} tickers", flush=True)
        except Exception as e:
            print(f"[sync] Bubble size error: {e}", flush=True)

        # 5. Zone returns
        try:
            print("[sync] Fetching zone returns...", flush=True)
            raw_zr = _fetch_zone_returns()
            zr_rows, zr_all = _build_zone_returns_payload(
                raw_zr, gi_map,
                name_map=name_map, sector_map=sector_map,
                conv_payload=c_payload,
            )
            payload_set(B_ZR,     zr_rows)
            payload_set(B_ZR_ALL, zr_all)
            print(f"[sync] Zone returns: {len(zr_rows):,} rows", flush=True)
        except Exception as e:
            print(f"[sync] Zone returns error: {e}", flush=True)

        # 6. Reversals
        try:
            print("[sync] Building reversals...", flush=True)
            rv_payload = _build_reversals_payload()
            if rv_payload:
                payload_set(B_REVERSALS, rv_payload)
                n_sigs = sum(len(v) for v in rv_payload.values())
                print(f"[sync] Reversals: {n_sigs:,} signals across {len(rv_payload):,} tickers", flush=True)
            else:
                print("[sync] Reversals: no GI history yet", flush=True)
        except Exception as e:
            print(f"[sync] Reversals error: {e}", flush=True)

        # 7. Themes
        try:
            print("[sync] Building themes...", flush=True)
            th_payload = _build_themes_payload(gi_map)
            if th_payload:
                payload_set(B_THEMES, th_payload)
                print(f"[sync] Themes: {len(th_payload):,} ETFs", flush=True)
        except Exception as e:
            print(f"[sync] Themes error: {e}", flush=True)

        # 7b. S&P 500 heatmap — reset list cache so weekly Wikipedia refresh is checked
        global _SP500_LIST_CACHE
        _SP500_LIST_CACHE = None
        try:
            print("[sync] Building S&P 500 heatmap...", flush=True)
            sp500_payload = _build_sp500_payload(gi_map)
            if sp500_payload:
                payload_set(B_SP500, sp500_payload)
                print(f"[sync] S&P 500: {len(sp500_payload):,} stocks", flush=True)
        except Exception as e:
            print(f"[sync] S&P 500 error: {e}", flush=True)

        # 8. Rotation / RRG
        try:
            print("[sync] Building rotation RRG...", flush=True)
            rot_payload = _build_rotation_payload()
            if rot_payload:
                payload_set(B_ROTATION, rot_payload)
                print("[sync] Rotation: built", flush=True)
        except Exception as e:
            print(f"[sync] Rotation error: {e}", flush=True)

        # 9. Meta counts
        try:
            h_data, _ = payload_get(B_HOLDINGS)
            i_data, _ = payload_get(B_INSIDERS)
            h_list = h_data if isinstance(h_data, list) else []
            i_list = i_data if isinstance(i_data, list) else []
            meta = {
                "n_mgr":  len({r.get("manager_name") for r in h_list if r.get("manager_name")}),
                "n_pos":  sum(1 for r in h_list if r.get("change_type") != "SOLD"),
                "n_new":  sum(1 for r in h_list if r.get("change_type") == "NEW"),
                "n_inc":  sum(1 for r in h_list if r.get("change_type") == "INCREASED"),
                "n_dec":  sum(1 for r in h_list if r.get("change_type") == "DECREASED"),
                "n_sold": sum(1 for r in h_list if r.get("change_type") == "SOLD"),
                "n_ins":  len(i_list),
            }
            payload_set(B_META, meta)
        except Exception as e:
            print(f"[sync] Meta error: {e}", flush=True)

        global _last_full_sync_ts
        _last_full_sync_ts = datetime.now(timezone.utc).isoformat()
        print("[sync] Full sync complete.", flush=True)
    finally:
        _tray_fetch_end()
        with _sync_lock:
            _sync_running = False


def _sync_loop() -> None:
    """Run a single sync on startup. Subsequent syncs are triggered manually via the tray icon."""
    _run_full_sync()


# ---------------------------------------------------------------------------
# OHLCV IN-MEMORY CACHE + AUTO-UPDATE
# ---------------------------------------------------------------------------
_ohlcv_mem: dict[str, list[dict]] = {}
_ohlcv_lock = threading.Lock()
_ohlcv_fetching: set[str] = set()
_ohlcv_refresh_ts: dict[str, str] = {}  # ticker -> last fetch attempt ISO


def _ohlcv_cached(ticker: str) -> list[dict] | None:
    return _ohlcv_mem.get(ticker.upper())


def _ohlcv_load(ticker: str) -> list[dict]:
    sym = ticker.upper()
    if sym in _ohlcv_mem:
        return _ohlcv_mem[sym]
    rows = ohlcv_get(sym)
    if rows:
        _ohlcv_mem[sym] = rows
    return rows


def _ohlcv_bg_fetch(ticker: str) -> None:
    """Fetch OHLCV from Supabase in a background thread; update in-memory + SQLite."""
    sym = ticker.upper()
    with _ohlcv_lock:
        if sym in _ohlcv_fetching:
            return
        _ohlcv_fetching.add(sym)
    try:
        _ohlcv_refresh_ts[sym] = datetime.now(timezone.utc).isoformat()
        final = _fetch_and_cache_ohlcv(sym)
        _ohlcv_mem[sym] = final
    except Exception as e:
        print(f"[ohlcv] bg fetch error {sym}: {e}", flush=True)
    finally:
        with _ohlcv_lock:
            _ohlcv_fetching.discard(sym)


def _watchlist_refresh_loop() -> None:
    """Every 5 minutes during market hours, pre-fetch OHLCV for watchlist tickers."""
    while True:
        time.sleep(300)
        if not _is_market_hours():
            continue
        try:
            prefs, _ = payload_get(B_PREFS, PREFS_KEY)
            if not isinstance(prefs, dict):
                continue
            wl_data = prefs.get("gekko_watchlists_v1", {})
            watchlists = wl_data.get("watchlists", []) if isinstance(wl_data, dict) else []
            tickers = set()
            for wl in (watchlists if isinstance(watchlists, list) else []):
                for sym in (wl.get("symbols") or [] if isinstance(wl, dict) else []):
                    tickers.add(str(sym).strip().upper())
            for sym in tickers:
                if sym and _ohlcv_is_stale(sym):
                    threading.Thread(target=_ohlcv_bg_fetch, args=(sym,), daemon=True).start()
        except Exception as e:
            print(f"[watchlist-refresh] error: {e}", flush=True)


# ---------------------------------------------------------------------------
# FLASK APP
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder=None)


def _json_resp(data, status: int = 200, headers: dict | None = None) -> Response:
    body = json.dumps(data, separators=(",", ":"), default=str)
    r = Response(body, status=status, mimetype="application/json")
    r.headers["Cache-Control"] = "no-cache"
    if headers:
        for k, v in headers.items():
            r.headers[k] = v
    return r


# --- HTML ---
@app.route("/")
def index():
    if INDEX_HTML.exists():
        resp = make_response(send_file(INDEX_HTML))
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    abort(404, "index.html not found — place it alongside server.py")


@app.route("/favicon.ico")
def favicon():
    p = _HERE / "tray_icon.png"
    if p.exists():
        return send_file(p, mimetype="image/png")
    return Response("", status=204)

@app.route("/tray_icon.png")
def tray_icon_route():
    p = _HERE / "tray_icon.png"
    if p.exists():
        return send_file(p, mimetype="image/png")
    return Response("", status=204)


@app.route("/rotation-frame")
def rotation_frame():
    for p in [
        _HERE / "rotation.html",
        _HERE / "DATA" / "rotation.html",
        _HERE / "DATA" / "gekko_app_rotation.html",
    ]:
        if p.exists():
            return send_file(p)
    return Response("{}", status=404, mimetype="application/json")


# --- SYNC STATUS ---
@app.route("/api/sync-status")
def api_sync_status():
    return _json_resp({
        "running":      _sync_running,
        "completed_at": _last_full_sync_ts,
    })


@app.route("/api/refresh-all", methods=["GET", "POST"])
def api_refresh_all():
    """Trigger a full background sync. Returns immediately."""
    if not _sync_running:
        threading.Thread(target=_run_full_sync, daemon=True).start()
        return _json_resp({"ok": True, "started": True})
    return _json_resp({"ok": True, "started": False, "message": "sync already running"})


# --- BULK DATA (cache-first) ---
@app.route("/api/holdings")
def api_holdings():
    data, ts = payload_get(B_HOLDINGS)
    rows = data or []
    for r in rows:
        if r.get("company"):
            r["company"] = _clean_company(r["company"])
    return _json_resp(rows, headers={"X-Gekko-Source-Updated-At": ts or ""})


@app.route("/api/holdings/date-coverage")
def api_holdings_date_coverage():
    """Diagnostic: show how many distinct filing dates each manager has in the DB.
    Use this to verify whether NEW/INCREASED/DECREASED signals are reliable.
    If a manager only has 1 filing date, all their positions show as UNKNOWN (not NEW).
    """
    results = []
    all_jobs = (
        [(cik, name, "trailblazer_holdings", "Trailblazer") for cik, name in TB_MANAGERS] +
        [(cik, name, "billionaire_holdings", "Billionaire")  for cik, name in BB_MANAGERS]
    )
    def _check(cik, name, table, source):
        rows = _supa_get(table, {
            "select": "report_date",
            "manager_cik": f"eq.{cik}",
            "order": "report_date.desc",
        })
        dates = sorted(set(str(r.get("report_date","")) for r in rows if r.get("report_date")), reverse=True)
        return {"manager": name, "source": source, "filing_dates": dates,
                "date_count": len(dates), "has_history": len(dates) >= 2,
                "latest": dates[0] if dates else None,
                "prior":  dates[1] if len(dates) >= 2 else None}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(lambda j: _check(*j), all_jobs):
            results.append(r)
    results.sort(key=lambda r: (r["date_count"], r["manager"]))
    no_history = [r for r in results if not r["has_history"]]
    summary = {
        "total_managers": len(results),
        "managers_with_history": sum(1 for r in results if r["has_history"]),
        "managers_without_history": len(no_history),
        "warning": f"{len(no_history)} manager(s) have only 1 filing date — their positions are marked UNKNOWN, not NEW" if no_history else "All managers have comparison data",
        "managers": results,
    }
    return jsonify(summary)


@app.route("/api/insiders")
def api_insiders():
    data, ts = payload_get(B_INSIDERS)
    rows = data or []
    for r in rows:
        if r.get("company"):
            r["company"] = _clean_company(r["company"])
    return _json_resp(rows, headers={"X-Gekko-Source-Updated-At": ts or ""})


@app.route("/api/conviction")
def api_conviction():
    data, ts = payload_get(B_CONVICTION)
    rows = data or []
    # Clean CDATA wrappers from existing cached rows and backfill any still-blank names.
    for r in rows:
        if r.get("company"):
            r["company"] = _clean_company(r["company"])
    missing = [r["ticker"] for r in rows if r.get("ticker") and not r.get("company")]
    if missing:
        name_map, _ = payload_get(B_NAMES)
        name_map = name_map or {}
        still_missing = [t for t in missing if not name_map.get(t)]
        if still_missing:
            yahoo = _fetch_yahoo_names(still_missing)
            name_map.update(yahoo)
            if yahoo:
                payload_set(B_NAMES, name_map)
        if name_map:
            for r in rows:
                if r.get("ticker") and not r.get("company"):
                    r["company"] = name_map.get(r["ticker"], "")
    return _json_resp(rows, headers={"X-Gekko-Source-Updated-At": ts or ""})



@app.route("/api/buy-meta")
def api_buy_meta():
    data, _ = payload_get(B_BUY_META)
    return _json_resp(data or {})


@app.route("/api/zone-returns")
def api_zone_returns():
    data, _ = payload_get(B_ZR)
    return _json_resp(data or [])


@app.route("/api/zone-returns-all")
def api_zone_returns_all():
    data, _ = payload_get(B_ZR_ALL)
    return _json_resp(data or {})


@app.route("/api/themes")
def api_themes():
    data, ts = payload_get(B_THEMES)
    return _json_resp(data or [], headers={"X-Gekko-Source-Updated-At": ts or "", "X-Gekko-Refreshing": "0"})


@app.route("/api/themes/rebuild")
def api_themes_rebuild():
    """Force-clear the themes cache and rebuild synchronously. Dev/admin use."""
    _tray_fetch_start()
    try:
        with _pconn() as c:
            c.execute("DELETE FROM payload_cache WHERE bucket=?", (B_THEMES,))
            c.execute("DELETE FROM payload_bucket_meta WHERE bucket=?", (B_THEMES,))
        gi_map = {}
        try:
            gi_rows = _supa_get("screener_latest", {"select": "ticker,gi_score"})
            gi_map = {r["ticker"]: float(r["gi_score"]) for r in gi_rows if r.get("gi_score") is not None}
        except Exception as e:
            print(f"[themes/rebuild] GI fetch error: {e}", flush=True)
        payload = _build_themes_payload(gi_map, force=True)
        if payload:
            payload_set(B_THEMES, payload)
        return _json_resp({"ok": True, "count": len(payload)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/rotation")
def api_rotation():
    data, ts = payload_get(B_ROTATION)
    return _json_resp(data or {}, headers={"X-Gekko-Source-Updated-At": ts or ""})


@app.route("/api/rotation/rebuild")
def api_rotation_rebuild():
    """Force-clear the rotation cache and rebuild synchronously. Dev/admin use."""
    _tray_fetch_start()
    try:
        with _pconn() as c:
            c.execute("DELETE FROM payload_cache WHERE bucket=?", (B_ROTATION,))
            c.execute("DELETE FROM payload_bucket_meta WHERE bucket=?", (B_ROTATION,))
        payload = _build_rotation_payload()
        if payload:
            payload_set(B_ROTATION, payload)
        total = sum(len(v) for v in payload.values())
        return _json_resp({"ok": True, "views": list(payload.keys()), "total_series": total})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/sp500")
def api_sp500():
    data, ts = payload_get(B_SP500)
    if not data:
        # Build on-demand if sync hasn't populated it yet
        try:
            gi_map, _, _ = _fetch_gi_scores()
            data = _build_sp500_payload(gi_map)
            if data:
                payload_set(B_SP500, data)
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            print(f"[sp500] on-demand build error: {e}", flush=True)
    return _json_resp(data or [], headers={"X-Gekko-Source-Updated-At": ts or "", "X-Gekko-Refreshing": "0"})


@app.route("/api/sp500/rebuild")
def api_sp500_rebuild():
    """Force-refresh all SP500 OHLCV data and rebuild the heatmap payload."""
    _tray_fetch_start()
    try:
        with _pconn() as c:
            c.execute("DELETE FROM payload_cache WHERE bucket=?", (B_SP500,))
            c.execute("DELETE FROM payload_bucket_meta WHERE bucket=?", (B_SP500,))
        gi_map = {}
        try:
            gi_rows = _supa_get("screener_latest", {"select": "ticker,gi_score"})
            gi_map = {r["ticker"]: float(r["gi_score"]) for r in gi_rows if r.get("gi_score") is not None}
        except Exception as e:
            print(f"[sp500/rebuild] GI fetch error: {e}", flush=True)
        payload = _build_sp500_payload(gi_map, force=True)
        if payload:
            payload_set(B_SP500, payload)
        return _json_resp({"ok": True, "count": len(payload)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/holdings/rebuild")
def api_holdings_rebuild():
    """Re-fetch holdings from Supabase and rebuild the payload."""
    _tray_fetch_start()
    try:
        gi_map, name_map, _ = _fetch_gi_scores()
        raw_h = _fetch_holdings_raw()
        h_payload = _build_holdings_payload(raw_h, gi_map)
        payload_set(B_HOLDINGS, h_payload)
        return _json_resp({"ok": True, "count": len(h_payload)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/insiders/rebuild")
def api_insiders_rebuild():
    """Re-fetch insider trades from Supabase and rebuild the payload."""
    _tray_fetch_start()
    try:
        gi_map, name_map, _ = _fetch_gi_scores()
        raw_i = _fetch_insiders_raw()
        i_payload = _build_insiders_payload(raw_i, gi_map, name_map)
        payload_set(B_INSIDERS, i_payload)
        bm_payload = _build_buy_meta(raw_i)
        payload_set(B_BUY_META, bm_payload)
        return _json_resp({"ok": True, "count": len(i_payload)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/conviction/rebuild")
def api_conviction_rebuild():
    """Re-fetch holdings + insiders from Supabase and rebuild conviction payload."""
    _tray_fetch_start()
    try:
        gi_map, name_map, _ = _fetch_gi_scores()
        raw_h = _fetch_holdings_raw()
        raw_i = _fetch_insiders_raw()
        conv_tickers = list({
            str(r.get("ticker") or "").strip().upper()
            for r in (raw_h + raw_i) if r.get("ticker")
        })
        name_map = _enrich_name_map(name_map, conv_tickers)
        if name_map:
            payload_set(B_NAMES, name_map)
        payload_set(B_HOLDINGS, _build_holdings_payload(raw_h, gi_map))
        payload_set(B_INSIDERS, _build_insiders_payload(raw_i, gi_map, name_map))
        payload_set(B_BUY_META, _build_buy_meta(raw_i))
        c_payload = _build_conviction_payload(raw_h, raw_i, gi_map, name_map)
        payload_set(B_CONVICTION, c_payload)
        return _json_resp({"ok": True, "count": len(c_payload)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/bubble/rebuild")
def api_bubble_rebuild():
    """Re-fetch conviction + insiders + bubble-size from Supabase."""
    _tray_fetch_start()
    try:
        gi_map, name_map, _ = _fetch_gi_scores()
        raw_h = _fetch_holdings_raw()
        raw_i = _fetch_insiders_raw()
        conv_tickers = list({
            str(r.get("ticker") or "").strip().upper()
            for r in (raw_h + raw_i) if r.get("ticker")
        })
        name_map = _enrich_name_map(name_map, conv_tickers)
        if name_map:
            payload_set(B_NAMES, name_map)
        payload_set(B_HOLDINGS, _build_holdings_payload(raw_h, gi_map))
        payload_set(B_INSIDERS, _build_insiders_payload(raw_i, gi_map, name_map))
        payload_set(B_BUY_META, _build_buy_meta(raw_i))
        payload_set(B_CONVICTION, _build_conviction_payload(raw_h, raw_i, gi_map, name_map))
        bubble = _fetch_bubble_size()
        payload_set(B_BUBBLE, bubble)
        return _json_resp({"ok": True, "count": len(bubble)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/zreturns/rebuild")
def api_zreturns_rebuild():
    """Re-fetch zone returns from Supabase and rebuild the payload."""
    _tray_fetch_start()
    try:
        gi_map, name_map, sector_map = _fetch_gi_scores()
        raw_zr = _fetch_zone_returns()
        conv_payload, _ = payload_get(B_CONVICTION)
        zr_rows, zr_all = _build_zone_returns_payload(
            raw_zr, gi_map,
            name_map=name_map, sector_map=sector_map,
            conv_payload=conv_payload or [],
        )
        payload_set(B_ZR,     zr_rows)
        payload_set(B_ZR_ALL, zr_all)
        return _json_resp({"ok": True, "count": len(zr_rows)})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/reversals/rebuild")
def api_reversals_rebuild():
    """Rebuild reversals from the current OHLCV + GI history cache."""
    _tray_fetch_start()
    try:
        rv_payload = _build_reversals_payload()
        if rv_payload:
            payload_set(B_REVERSALS, rv_payload)
        n = sum(len(v) for v in rv_payload.values()) if rv_payload else 0
        return _json_resp({"ok": True, "signals": n})
    except Exception as e:
        return _json_resp({"ok": False, "error": str(e)}), 500
    finally:
        _tray_fetch_end()


@app.route("/api/reversals")
def api_reversals():
    data, _ = payload_get(B_REVERSALS)
    return _json_resp(data or {})


@app.route("/api/earnings")
def api_earnings():
    data, _ = payload_get(B_EARNINGS)
    return _json_resp(data or {})


# ---------------------------------------------------------------------------
# SIGNALS  (from gekko_backtest.html CURRENT array)
# ---------------------------------------------------------------------------
@app.route("/api/signals")
def api_signals():
    """Return recent signals for the Signals tab."""
    _load_signals_once(force=True)  # always check file mtime for freshness
    days = 3
    try:
        days = int(request.args.get("days", 3))
    except Exception:
        pass
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = []
    for s in _signals_flat:
        if (s.get("signal_date") or "") < cutoff:
            break
        robust_total = (
            (s.get("robust") or 0) + (s.get("robust_dims") or 0) +
            (s.get("robust_hold") or 0) + (s.get("robust_tp") or 0) +
            (s.get("robust_half") or 0) + (s.get("robust_dd") or 0)
        )
        rows.append({
            "ticker":              s.get("ticker", ""),
            "signal_date":         s.get("signal_date", ""),
            "signal_family":       s.get("signal_family", ""),
            "signal_source":       s.get("signal_source", ""),
            "signal_mode":         s.get("signal_mode", ""),
            "pos_rank":            s.get("pos_rank"),
            "score":               s.get("score"),
            "robust_total":        robust_total,
            "days_ago":            s.get("days_ago"),
            "current_gi":          s.get("current_gi"),
            "thresh":              s.get("thresh"),
            "threshold_mode":      s.get("threshold_mode", "fixed_global"),
            "threshold_label":     s.get("threshold_label", ""),
            "effective_threshold": s.get("effective_threshold"),
            "avg_atr_pct":         s.get("avg_atr_pct"),
            "atr_mult":            s.get("atr_mult"),
            "target":              s.get("target"),
            "hold":                s.get("hold"),
            "ts_days":             s.get("ts_days"),
            "win_rate":            s.get("win_rate"),
            "avg_ret":             s.get("avg_ret"),
            "expected_ret_3d":     s.get("expected_ret_3d"),
            "expected_ret_5d":     s.get("expected_ret_5d"),
            "expected_ret_10d":    s.get("expected_ret_10d"),
            "downside_tail_10d":   s.get("downside_tail_10d"),
            "expected_r_multiple": s.get("expected_r_multiple"),
            "sharpe":              s.get("sharpe"),
            "n":                   s.get("n"),
            "last_entry_px":       s.get("last_entry_px"),
            # Boolean fields used by strategy filters
            "above_prev_high":     s.get("above_prev_high"),
            "gi_reversal":         s.get("gi_reversal"),
            "vol_confirm":         s.get("vol_confirm"),
            "gi_accel":            s.get("gi_accel"),
            "atr_regime_ok":       s.get("atr_regime_ok"),
            "close_strength":      s.get("close_strength"),
            "gi_trend_up":         s.get("gi_trend_up"),
            "confirm_count":       s.get("confirm_count"),
            "type":                _sig_type(s),
        })
        if len(rows) >= 2000:
            break
    return _json_resp(rows)


@app.route("/api/signals/reload")
def api_signals_reload():
    """Force reload of signals from the HTML file."""
    _load_signals_once(force=True)
    return _json_resp({"ok": True, "count": len(_signals_flat)})


@app.route("/api/signals/<ticker>")
def api_signals_ticker(ticker: str):
    """Return chart-overlay signal points for a specific ticker."""
    _load_signals_once()
    sym = ticker.strip().upper()
    sigs = _signals_by_ticker.get(sym, [])
    result = [{"d": s.get("signal_date", ""), "t": _sig_type(s)} for s in sigs if s.get("signal_date")]
    return _json_resp(result)


@app.route("/api/fair-value")
def api_fair_value():
    data, _ = payload_get(B_FAIR_VALUE)
    return _json_resp(data or {})


@app.route("/api/bubble-size")
def api_bubble_size():
    data, _ = payload_get(B_BUBBLE)
    return _json_resp(data or {})


# --- GI HISTORY ---
@app.route("/api/gi-history")
def api_gi_history():
    data, ts = payload_get(B_GI_HIST)
    return _json_resp(data or {}, headers={"X-Gekko-Source-Updated-At": ts or ""})


@app.route("/api/gi-history/<ticker>")
def api_gi_history_ticker(ticker: str):
    sym = ticker.strip().upper()
    data, ts = payload_get(B_GI_HIST_PER, sym)
    refreshing = "0"
    if data is None:
        def _bg():
            rows = _fetch_gi_history_ticker(sym)
            if rows:
                payload_set(B_GI_HIST_PER, rows, key=sym)
                print(f"[gi-hist] {sym}: {len(rows)} rows fetched", flush=True)
        threading.Thread(target=_bg, daemon=True).start()
        refreshing = "1"
        return _json_resp([], headers={"X-Gekko-Refreshing": refreshing})
    if _is_stale(ts, TTL_BULK):
        last_date = data[-1]["date"] if data and "date" in data[-1] else None
        def _bg_inc(ld=last_date):
            rows = _fetch_gi_history_ticker(sym, since=ld)
            if rows:
                merged = {r["date"]: r for r in data}
                merged.update({r["date"]: r for r in rows})
                final = sorted(merged.values(), key=lambda r: r["date"])
                payload_set(B_GI_HIST_PER, final, key=sym)
        threading.Thread(target=_bg_inc, daemon=True).start()
        refreshing = "1"
    return _json_resp(data or [], headers={"X-Gekko-Refreshing": refreshing})


# --- PER-TICKER ZONE RETURNS ---
@app.route("/api/zone-returns/<ticker>")
def api_zone_returns_ticker(ticker: str):
    sym = ticker.strip().upper()
    data, ts = payload_get(B_ZR_PER, sym)
    if isinstance(data, dict) and not _is_stale(ts, TTL_BULK):
        return _json_resp(data)
    # Try the bulk all-zones cache
    zr_all, _ = payload_get(B_ZR_ALL)
    if isinstance(zr_all, dict) and sym in zr_all:
        return _json_resp(zr_all[sym])
    # Fetch on-demand
    try:
        raw = _supa_get("gi_zone_returns", {
            "select": "zone,avg_5d,avg_10d,avg_20d,avg_30d,avg_50d,sample_count",
            "ticker": f"eq.{sym}",
        })
        result = {r["zone"]: {
            "avg_5d": r.get("avg_5d"), "avg_10d": r.get("avg_10d"),
            "avg_20d": r.get("avg_20d"), "avg_30d": r.get("avg_30d"),
            "avg_50d": r.get("avg_50d"), "n": int(r.get("sample_count") or 0),
        } for r in raw if r.get("zone")}
        if result:
            payload_set(B_ZR_PER, result, key=sym)
        return _json_resp(result)
    except Exception as e:
        print(f"[zone-returns] {sym} error: {e}", flush=True)
        return _json_resp(data or {})


# --- PER-TICKER REVERSALS ---
@app.route("/api/reversals/<ticker>")
def api_reversals_ticker(ticker: str):
    sym = ticker.strip().upper()

    # 1. Check per-ticker slot in bulk cache
    rv_all, _ = payload_get(B_REVERSALS)
    if isinstance(rv_all, dict) and sym in rv_all:
        return _json_resp(rv_all[sym])

    # 2. Compute on-demand from cached GI history + OHLCV
    gi_rows, _ = payload_get(B_GI_HIST_PER, sym)
    if isinstance(gi_rows, list) and gi_rows:
        price_map: dict[str, float] = {}
        try:
            with _oconn() as c:
                bars = c.execute(
                    "SELECT date, close FROM ohlcv_bars WHERE ticker=? ORDER BY date",
                    (sym,),
                ).fetchall()
            price_map = {b["date"]: float(b["close"]) for b in bars if b["close"] is not None}
        except Exception:
            pass
        signals = _compute_reversals_for_ticker(gi_rows, price_map)
        return _json_resp(signals)

    return _json_resp([])


@app.route("/api/earnings/<ticker>")
def api_earnings_ticker(ticker: str):
    sym = ticker.strip().upper()
    data, ts = payload_get(B_EARNINGS, sym)
    if isinstance(data, list) and not _is_stale(ts, TTL_BULK):
        return _json_resp(data)
    # Try proxy fetch
    def _bg():
        result = _fetch_earnings_proxy(sym)
        if result is not None:
            payload_set(B_EARNINGS, result, key=sym)
    threading.Thread(target=_bg, daemon=True).start()
    return _json_resp(data or [], headers={"X-Gekko-Refreshing": "1" if _get_gekko_session() else "0"})


@app.route("/api/fair-value/<ticker>")
def api_fair_value_ticker(ticker: str):
    sym = ticker.strip().upper()
    data, ts = payload_get(B_FAIR_VALUE, sym)
    if isinstance(data, dict) and data.get("fair_value") and not _is_stale(ts, TTL_BULK):
        return _json_resp(data)
    fv_all, _ = payload_get(B_FAIR_VALUE)
    if isinstance(fv_all, dict) and sym in fv_all:
        return _json_resp(fv_all[sym])
    # Try proxy fetch in background; return 404 now so browser gets result on next load
    def _bg():
        result = _fetch_fair_value_proxy(sym)
        if result:
            payload_set(B_FAIR_VALUE, result, key=sym)
            print(f"[fair-value] cached {sym}: {result.get('fair_value')}", flush=True)
    threading.Thread(target=_bg, daemon=True).start()
    return _json_resp({}, 404)


# --- TICKER META ---
@app.route("/api/ticker-meta/<ticker>")
def api_ticker_meta(ticker: str):
    sym = ticker.strip().upper()
    data, ts = payload_get(B_TICKER_META, sym)
    if isinstance(data, dict) and not _is_stale(ts, TTL_META):
        return _json_resp({**data, "ticker": sym})
    def _bg():
        meta = _fetch_ticker_meta([sym])
        if meta.get(sym):
            payload_set(B_TICKER_META, meta[sym], key=sym)
    threading.Thread(target=_bg, daemon=True).start()
    return _json_resp({**(data or {}), "ticker": sym})


# --- OHLCV (auto-update) ---
_OHLCV_MIN_ROWS = 50


@app.route("/api/ohlcv/<ticker>")
def api_ohlcv(ticker: str):
    sym = ticker.strip().upper()
    rows = _ohlcv_load(sym)
    refreshing = False
    force_refresh = request.args.get("refresh") == "1"

    if not rows:
        # First request: fetch synchronously so chart renders immediately
        try:
            rows = _fetch_and_cache_ohlcv(sym)
            _ohlcv_mem[sym] = rows
            _ohlcv_refresh_ts[sym] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            print(f"[ohlcv] sync fetch error {sym}: {e}", flush=True)
    elif force_refresh or len(rows) < _OHLCV_MIN_ROWS or _ohlcv_is_stale(sym):
        # Stale, thin, or forced: return cached data immediately, refresh in background
        threading.Thread(target=_ohlcv_bg_fetch, args=(sym,), daemon=True).start()
        refreshing = True

    if not rows:
        return _json_resp([], 404, headers={"X-Gekko-Refreshing": "0"})
    return _json_resp(rows, headers={"X-Gekko-Refreshing": "1" if refreshing else "0"})


@app.route("/api/ohlcv-version")
def api_ohlcv_version():
    dates = []
    if OHLCV_DB.exists():
        with _oconn() as c:
            row = c.execute("SELECT MAX(date) AS d FROM ohlcv_bars").fetchone()
            if row:
                dates.append(row["d"])
    return _json_resp({"latest_date": dates[0] if dates else None})


# --- PREFS ---
# Settings are stored in DATA/user_prefs.json — completely separate from the
# market-data cache so clearing/deleting payload_cache.sqlite never loses them.
_prefs_lock = threading.Lock()
USER_PREFS_FILE = DATA_DIR / "user_prefs.json"


def _prefs_read() -> dict:
    """Read prefs from user_prefs.json, migrating from SQLite on first use."""
    if USER_PREFS_FILE.exists():
        try:
            return json.loads(USER_PREFS_FILE.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    # One-time migration: pull whatever was stored in the old SQLite bucket
    try:
        old, _ = payload_get(B_PREFS, PREFS_KEY)
        if old and isinstance(old, dict):
            _prefs_write(old)
            return old
    except Exception:
        pass
    return {}


def _prefs_write(data: dict) -> None:
    """Atomically write prefs to user_prefs.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = USER_PREFS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(USER_PREFS_FILE)


@app.route("/api/prefs", methods=["GET"])
def api_prefs_get():
    with _prefs_lock:
        data = _prefs_read()
    return _json_resp(data)


@app.route("/api/prefs", methods=["POST"])
def api_prefs_post():
    incoming = request.get_json(force=True, silent=True) or {}
    if not isinstance(incoming, dict):
        return _json_resp({"error": "expected object"}, 400)
    with _prefs_lock:
        merged = {**_prefs_read(), **incoming}
        _prefs_write(merged)
    return _json_resp({"ok": True})


# --- STATUS ---
@app.route("/api/status")
def api_status():
    buckets = [B_HOLDINGS, B_INSIDERS, B_CONVICTION, B_BUY_META,
               B_GI_HIST, B_ZR, B_ZR_ALL, B_THEMES, B_SP500,
               B_REVERSALS, B_EARNINGS, B_FAIR_VALUE, B_BUBBLE, B_META]
    info = {}
    for b in buckets:
        data, ts = payload_get(b)
        info[b] = {"present": data is not None, "updated_at": ts or ""}
    with _oconn() as c:
        tc = c.execute("SELECT COUNT(DISTINCT ticker) AS n FROM ohlcv_bars").fetchone()
    return _json_resp({"tickers_loaded": tc["n"] if tc else 0, "buckets": info,
                       "sync_running": _sync_running})


# --- MANUAL SYNC TRIGGER ---
@app.route("/api/sync", methods=["POST"])
def api_sync_trigger():
    if _sync_running:
        return _json_resp({"status": "already_running"})
    threading.Thread(target=_run_full_sync, daemon=True).start()
    return _json_resp({"status": "started"})


# --- SEARCH UNIVERSE ---
@app.route("/api/search-universe")
def api_search_universe():
    """Return {ticker: company_name} for all known tickers."""
    universe: dict[str, str] = {}
    h_data, _ = payload_get(B_HOLDINGS)
    if isinstance(h_data, list):
        for r in h_data:
            t = str(r.get("ticker") or "").strip().upper()
            if t:
                universe.setdefault(t, str(r.get("company_name") or ""))
    for sym in ohlcv_all_tickers():
        universe.setdefault(sym, "")
    return _json_resp(universe)


# --- LIVE STATUS & QUOTES (Yahoo Finance) ---
@app.route("/api/live/status")
def api_live_status():
    return _json_resp({
        "enabled": _is_market_hours(),
        "market_open": _is_market_hours(),
        "regular_session": _is_regular_session(),
        "needs_auth": False,
        "auth_in_progress": False,
    })


@app.route("/api/live/quotes")
def api_live_quotes():
    raw = request.args.get("tickers", "")
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]
    if not tickers:
        return _json_resp({})
    quotes = _fetch_yahoo_quotes(tickers)
    return _json_resp(quotes)


# ---------------------------------------------------------------------------
# SYSTEM TRAY
# ---------------------------------------------------------------------------
def _make_tray_frames():
    """Return (icon_base, icon_dot) — two PIL RGBA images.

    icon_base: tray_icon.png as-is (the black+gray G).
    icon_dot:  same image with a green blinking dot in the bottom-right corner.
    """
    from PIL import Image, ImageDraw, ImageOps

    # Load the real tray_icon.png
    png_path = _HERE / "tray_icon.png"
    if png_path.exists():
        with Image.open(png_path) as src:
            resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
            base = src.convert("RGBA")
            base = ImageOps.fit(base, (256, 256), method=resampling)
    else:
        # Fallback: plain black square
        base = Image.new("RGBA", (256, 256), (13, 13, 13, 255))

    s = base.width  # 256

    def _add_dot(src: Image.Image) -> Image.Image:
        img = src.copy()
        draw = ImageDraw.Draw(img)
        dr  = int(s * 0.13)                      # dot radius
        pad = int(s * 0.05)                      # margin from edge
        dcx = s - dr - pad                       # bottom-right x center
        dcy = s - dr - pad                       # bottom-right y center
        # Soft glow rings
        for expand in range(10, 0, -1):
            alpha = int(90 * (expand / 10) ** 1.8)
            draw.ellipse(
                [dcx - dr - expand, dcy - dr - expand,
                 dcx + dr + expand, dcy + dr + expand],
                fill=(34, 197, 94, alpha),
            )
        # Solid green dot
        draw.ellipse(
            [dcx - dr, dcy - dr, dcx + dr, dcy + dr],
            fill=(34, 197, 94, 255),
        )
        # Small white highlight
        hlr = max(1, int(dr * 0.32))
        draw.ellipse(
            [dcx - hlr - int(dr * 0.15), dcy - hlr - int(dr * 0.20),
             dcx - int(dr * 0.15) + hlr, dcy - int(dr * 0.20) + hlr],
            fill=(255, 255, 255, 100),
        )
        return img

    return base, _add_dot(base)


def _run_tray(url: str) -> None:
    """Run the system tray icon with a blinking green dot. Blocks until Stop Server."""
    try:
        import pystray
    except ImportError:
        print("[tray] pystray not installed — no tray icon", flush=True)
        threading.Event().wait()
        return

    icon_base, icon_dot = _make_tray_frames()

    def on_open(icon, item):
        webbrowser.open(url)

    def on_refresh_all(icon, item):
        """Trigger a full data refresh from the tray menu."""
        if not _sync_running:
            threading.Thread(target=_run_full_sync, daemon=True).start()

    def on_stop(icon, item):
        icon.stop()
        import os, subprocess
        # Kill the parent CMD window, then exit this process
        try:
            subprocess.Popen(
                ['taskkill', '/F', '/PID', str(os.getppid())],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass
        os._exit(0)

    tray = pystray.Icon(
        "GekkoV2",
        icon_base,         # start with no dot — only appears during API activity
        "Gekko V2",
        menu=pystray.Menu(
            pystray.MenuItem("Open in Browser",  on_open),
            pystray.MenuItem("Refresh All Data", on_refresh_all),
            pystray.MenuItem("Stop Server",      on_stop),
        ),
    )

    # Blink green dot only while API data is actively downloading.
    # Uses a fixed 0.55s sleep so the toggle is always visible.
    def _blink_loop():
        dot_on = False
        while True:
            try:
                if _tray_blink_event.is_set():
                    # Actively fetching — alternate dot on/off
                    dot_on = not dot_on
                    tray.icon = icon_dot if dot_on else icon_base
                else:
                    # Idle — make sure dot is gone
                    if dot_on:
                        dot_on = False
                        tray.icon = icon_base
                time.sleep(0.55)
            except Exception:
                break

    threading.Thread(target=_blink_loop, daemon=True).start()
    tray.run()  # blocks until on_stop calls icon.stop()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def run() -> None:
    # Auto-generate HTML files if missing before serving
    try:
        import html_builder
        html_builder.generate_if_missing()
    except Exception as e:
        print(f"[html] builder error: {e}", flush=True)

    init_stores()
    # No startup sync — serve from SQLite cache immediately.
    # Use tray → Refresh Data to pull fresh data from Supabase.
    # Watchlist OHLCV auto-refresh (charts + watchlist only — runs continuously)
    threading.Thread(target=_watchlist_refresh_loop, daemon=True).start()

    url = f"http://127.0.0.1:{PORT}"
    print(f"[server] Gekko V2 -> {url}", flush=True)

    # Flask runs in a daemon thread so the main thread can own the tray
    flask_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, debug=False,
                               use_reloader=False, threaded=True),
        daemon=True,
    )
    flask_thread.start()

    # Open browser once Flask is ready
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    # Tray blocks main thread — process lives until Stop Server is clicked
    _run_tray(url)


if __name__ == "__main__":
    run()
