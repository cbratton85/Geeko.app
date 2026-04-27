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
ROTATION_VIEWS = {
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
}

# ---------------------------------------------------------------------------
# ROTATION HTML TEMPLATE
# ---------------------------------------------------------------------------


def build_rotation_html(rotation_json, rotation_views_json):
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rotation</title>
<style>
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap");

:root {
  --bg: #030507;
  --surface: #081019;
  --card: #09111a;
  --card-2: #0d1620;
  --text: #edf2f7;
  --dim: #b1bcc8;
  --muted: #667383;
  --silver: #B0B0B0;
  --silver-bright: #D4D4D4;

  --border: #1a1a1a;
  --border-hover: #2A2A2A;

  --green: #119600;
  --green-2: #33AA00;
  --green-soft: #77AA00;
  --amber: #CC9900;
  --orange: #DD6600;
  --red: #AA0000;

  --mono: 'JetBrains Mono','Cascadia Mono','Consolas',monospace;
  --sans: 'DM Sans','Segoe UI',system-ui,sans-serif;

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;

  --glow-subtle: 0 0 16px rgba(180,180,180,.05), 0 0 28px rgba(180,180,180,.025);
  --shadow-panel: 0 10px 30px rgba(0,0,0,.32);
}

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body {
  width: 100%;
  height: 100%;
  background: var(--bg);
  color: var(--text);
  overflow: hidden;
}

body {
  font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  display: flex;
}

.rot-shell {
  width: 100%;
  height: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 50% 0%, rgba(42,71,104,.20), transparent 34%),
    linear-gradient(180deg, #07111a 0%, #04070b 100%),
    var(--bg);
}

.rot-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 16px 10px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(255,255,255,.015), rgba(255,255,255,0));
  flex-shrink: 0;
}

.rot-head-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  min-width: 0;
}

.rot-title {
  margin: 0;
  font-size: 18px;
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text);
  font-family: var(--sans);
}

.rot-sub {
  font-family: var(--sans);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: .02em;
  color: var(--muted);
}

.rot-mode-group {
  display: flex;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card);
}

.rot-mode-btn {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--sans);
  letter-spacing: .01em;
  background: transparent;
  color: var(--dim);
  transition: all .16s ease;
}

.rot-mode-btn:hover {
  color: var(--text);
  background: rgba(255,255,255,.03);
}

.rot-mode-btn.active {
  background: #111111;
  border-color: #232323;
  color: var(--text);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.015), var(--glow-subtle);
}

.rot-body {
  flex: 1;
  min-height: 0;
  padding: 10px 12px 12px;
  position: relative;
  display: flex;
}

.rot-stage {
  position: relative;
  flex: 1;
  min-height: 0;
  background:
    radial-gradient(circle at 50% 42%, rgba(255,255,255,.03), transparent 54%),
    linear-gradient(180deg, rgba(14,22,34,.98), rgba(6,9,13,.98));
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.02), 0 18px 38px rgba(0,0,0,.34);
}

.rot-chart {
  position: absolute;
  inset: 0;
  cursor: default;
  background:
    radial-gradient(circle at 50% 36%, rgba(255,255,255,.02), transparent 48%),
    linear-gradient(180deg, #08111b 0%, #05090f 100%);
}

.rot-svg {
  display: block;
}

.rot-tip {
  position: absolute;
  display: none;
  pointer-events: none;
  z-index: 3;
  min-width: 180px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #262626;
  background: rgba(8,8,8,.96);
  box-shadow: 0 18px 40px rgba(0,0,0,.45);
  color: var(--text);
  font-family: var(--sans);
  font-size: 12px;
}

.rot-empty {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 12px;
  z-index: 2;
}

.rot-grid-line {
  stroke: rgba(255,255,255,0.055);
  stroke-width: 1;
}

.rot-mid-line {
  stroke: rgba(236,241,247,0.22);
  stroke-width: 1.1;
  stroke-dasharray: 5 6;
}

.rot-quad-title {
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .38em;
  opacity: .46;
  text-transform: uppercase;
}

.rot-axis-label {
  fill: rgba(230,236,243,.72);
  font-family: var(--mono);
  font-size: 11px;
}

.rot-axis-title {
  fill: #FFFFFF;
  font-family: var(--sans);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .03em;
}

.rot-last-label {
  fill: #FFFFFF;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .03em;
  stroke: rgba(0,0,0,.92);
  stroke-width: 4px;
  paint-order: stroke fill;
}

.rot-tail-glow {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.rot-tail-seg {
  fill: none;
  stroke-linecap: round;
}

.rot-tail-dot {
  stroke: none;
}
</style>
</head>
<body>
<div class="rot-shell">
  <div class="rot-body">
    <div class="rot-empty" id="rotEmpty">Rotation data unavailable.</div>
    <div class="rot-stage">
      <div class="rot-chart" id="rotationChart"></div>
      <div class="rot-tip" id="rotTip"></div>
    </div>
  </div>
</div>
<script>
const ROTATION_DATA = {};
const ROTATION_VIEWS = {"sectors":{"label":"Sectors","benchmark":"SHV","tickers":[{"ticker":"XLK","name":"Technology","color":"#00AAFF"},{"ticker":"XLF","name":"Financials","color":"#FF6600"},{"ticker":"XLV","name":"Healthcare","color":"#FF3366"},{"ticker":"XLY","name":"Cons. Disc.","color":"#FFAA00"},{"ticker":"XLI","name":"Industrials","color":"#AAAACC"},{"ticker":"XLC","name":"Comm. Svcs","color":"#CC44FF"},{"ticker":"XLE","name":"Energy","color":"#FF4400"},{"ticker":"XLB","name":"Materials","color":"#BB8866"},{"ticker":"XLP","name":"Cons. Staples","color":"#33CC66"},{"ticker":"XLRE","name":"Real Estate","color":"#00CCAA"},{"ticker":"XLU","name":"Utilities","color":"#8855DD"}]},"crossAsset":{"label":"Cross-Asset","benchmark":"SHV","tickers":[{"ticker":"SPY","name":"S&P 500","color":"#EAEAEA"},{"ticker":"DIA","name":"Dow Jones","color":"#00CCAA"},{"ticker":"QQQ","name":"Nasdaq 100","color":"#00AAFF"},{"ticker":"IWM","name":"Small Caps","color":"#FF6600"},{"ticker":"MDY","name":"Mid Caps","color":"#AADDFF"},{"ticker":"VEU","name":"Intl Stocks","color":"#33CC66"},{"ticker":"TLT","name":"20Y+ Bonds","color":"#AAAACC"},{"ticker":"HYG","name":"High Yield","color":"#CC44FF"},{"ticker":"GLD","name":"Gold","color":"#FFD700"},{"ticker":"SLV","name":"Silver","color":"#C0C0C0"},{"ticker":"USO","name":"Crude Oil","color":"#FF4400"},{"ticker":"CPER","name":"Copper","color":"#BB8866"},{"ticker":"IBIT","name":"Bitcoin","color":"#FF9900"}]}};
const SVG_NS='http://www.w3.org/2000/svg';
let rotMode='sectors';
let rotRenderTimer=0;
const rotViewByMode={};
let rotDragState=null;
let rotPanBound=0;

function rotClamp(v,min,max){
  const n=Number(v);
  if(!Number.isFinite(n)) return min;
  return Math.min(max,Math.max(min,n));
}
function rotGetView(mode){
  if(!rotViewByMode[mode]) rotViewByMode[mode]={zoom:1,cx:100,cy:100};
  return rotViewByMode[mode];
}
function rotClampView(base,state){
  if(!base||!state) return {xMin:97,xMax:103,yMin:97,yMax:103,xSpan:6,ySpan:6};
  const zoom=rotClamp(state.zoom||1,1,16);
  const halfX=Math.max(0.5,(base.xSpan/2)/zoom);
  const halfY=Math.max(0.5,(base.ySpan/2)/zoom);
  const minCx=base.xMin+halfX;
  const maxCx=base.xMax-halfX;
  const minCy=base.yMin+halfY;
  const maxCy=base.yMax-halfY;
  state.zoom=zoom;
  state.cx=rotClamp(Number.isFinite(state.cx)?state.cx:100,minCx,maxCx);
  state.cy=rotClamp(Number.isFinite(state.cy)?state.cy:100,minCy,maxCy);
  return {
    xMin:state.cx-halfX,
    xMax:state.cx+halfX,
    yMin:state.cy-halfY,
    yMax:state.cy+halfY,
    xSpan:halfX*2,
    ySpan:halfY*2
  };
}
function rotResetView(mode){
  const st=rotGetView(mode);
  st.zoom=1;
  st.cx=100;
  st.cy=100;
}
function rotBindPanHandlers(){
  if(rotPanBound) return;
  rotPanBound=1;
  window.addEventListener('mousemove',evt=>{
    if(!rotDragState) return;
    const st=rotGetView(rotDragState.mode);
    st.cx=rotDragState.startCx-(evt.clientX-rotDragState.startX)*(rotDragState.viewXSpan/rotDragState.plotW);
    st.cy=rotDragState.startCy+(evt.clientY-rotDragState.startY)*(rotDragState.viewYSpan/rotDragState.plotH);
    rotClampView(rotDragState.base,st);
    rotQueueRender();
  });
  window.addEventListener('mouseup',()=>{
    if(!rotDragState) return;
    rotDragState=null;
    const host=document.getElementById('rotationChart');
    if(host) host.classList.remove('dragging');
  });
  window.addEventListener('blur',()=>{rotDragState=null;});
}

function rotSetMode(mode,btn){
  rotMode=mode;
  document.querySelectorAll('.rot-mode-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderRotation();
}
function rotFmtDateShort(v){
  if(v==null||v==='') return '';
  if(v instanceof Date && Number.isFinite(v.getTime())) return `${v.getMonth()+1}-${v.getDate()}-${v.getFullYear()}`;
  const s=String(v).trim();
  if(!s) return '';
  const iso=s.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
  if(iso) return `${Number(iso[2])}-${Number(iso[3])}-${iso[1]}`;
  const dt=new Date(s);
  if(Number.isFinite(dt.getTime())) return `${dt.getMonth()+1}-${dt.getDate()}-${dt.getFullYear()}`;
  return s;
}
function rotTooltipHtml(item,point){
  const quad=point.x>=100?(point.y>=100?'Leading':'Weakening'):(point.y>=100?'Improving':'Lagging');
  const qc=point.x>=100?(point.y>=100?'#44bb22':'#ddaa22'):(point.y>=100?'#5599ee':'#dd5555');
  const chg=ROTATION_DATA._chg1d&&ROTATION_DATA._chg1d[item.ticker];
  const chgHtml=chg!=null
    ?`<span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:${chg>=0?'#4ade80':'#f87171'};margin-left:10px;">${chg>=0?'+':''}${chg.toFixed(2)}%</span>`
    :'';
  return `<div style="line-height:1.5;">
    <div style="margin-bottom:4px;">
      <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${item.color};margin-right:6px;vertical-align:middle"></span>
      <b style="font-family:'JetBrains Mono',monospace;color:#fff;">${item.ticker}</b>
      <span style="color:#b0b0b0;">(${item.name})</span>${chgHtml}
    </div>

    <div>
      <span style="color:#60a5fa;">RS-Ratio:</span>
      <span style="font-family:'JetBrains Mono',monospace;color:#e2e8f0;">${point.x.toFixed(2)}</span>
    </div>

    <div>
      <span style="color:#34d399;">RS-Momentum:</span>
      <span style="font-family:'JetBrains Mono',monospace;color:#e2e8f0;">${point.y.toFixed(2)}</span>
    </div>

    <div style="margin-top:4px;">
      <span style="color:#c084fc;">Quadrant:</span>
      <span style="font-family:'JetBrains Mono',monospace;color:${qc};font-weight:600;">${quad}</span>
    </div>

  </div>`;
}
function rotMakeEl(tag,attrs){
  const el=document.createElementNS(SVG_NS,tag);
  Object.entries(attrs||{}).forEach(([k,v])=>{if(v!=null)el.setAttribute(k,String(v));});
  return el;
}
function rotHexToRgba(hex,alpha){
  const raw=String(hex||'').replace('#','');
  if(raw.length!==6) return `rgba(255,255,255,${alpha})`;
  const n=parseInt(raw,16);
  if(!Number.isFinite(n)) return `rgba(255,255,255,${alpha})`;
  return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${alpha})`;
}
function rotHideTip(){
  const tip=document.getElementById('rotTip');
  if(tip) tip.style.display='none';
}
function rotShowTip(evt,host,item,point){
  const tip=document.getElementById('rotTip');
  const stage=tip&&tip.parentElement;
  if(!tip||!stage) return;
  tip.innerHTML=rotTooltipHtml(item,point);
  tip.style.display='block';
  const rect=stage.getBoundingClientRect();
  const x=(evt.clientX||0)-rect.left;
  const y=(evt.clientY||0)-rect.top;
  const pad=12;
  let left=x+20;
  let top=y+12;
  if(left+tip.offsetWidth>rect.width-pad) left=x-tip.offsetWidth-22;
  if(left<pad) left=pad;
  if(top+tip.offsetHeight>rect.height-pad) top=y-tip.offsetHeight-12;
  if(top<pad) top=pad;
  tip.style.left=left+'px';
  tip.style.top=top+'px';
}
function rotQueueRender(){
  if(rotRenderTimer) cancelAnimationFrame(rotRenderTimer);
  rotRenderTimer=requestAnimationFrame(()=>{rotRenderTimer=0;renderRotation();});
}
function rotBuildSeries(cfg,modeData){
  return (cfg.tickers||[]).map(item=>{
    const tail=(modeData[item.ticker]||[]).slice(-16).map(r=>({
      x:+Number(r.rsRatio).toFixed(2),
      y:+Number(r.rsMomentum).toFixed(2),
      date:r.date||''
    })).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
    return {item,tail};
  }).filter(s=>s.tail.length>=2);
}
function rotAttachInteractions(host,view,base,margin,plotW,plotH){
  if(!host) return;
  host.onwheel=null;
  host.onmousedown=null;
  host.ondblclick=null;
  host.onmouseleave=()=>rotHideTip();
}
function renderRotation(){
  const host=document.getElementById('rotationChart');
  const empty=document.getElementById('rotEmpty');
  const cfg=ROTATION_VIEWS[rotMode]||ROTATION_VIEWS.sectors;
  const modeData=ROTATION_DATA[rotMode]||{};
  if(!host) return;
  const built=rotBuildSeries(cfg,modeData);
  const pts=[];
  built.forEach(s=>s.tail.forEach(p=>pts.push(p)));
  if(!pts.length){
    host.innerHTML='';
    if(empty){empty.textContent='Rotation data unavailable.';empty.style.display='flex';}
    return;
  }
  if(empty) empty.style.display='none';
  const rect=host.getBoundingClientRect();
  const width=Math.max(720,Math.floor(rect.width||960));
  const height=Math.max(460,Math.floor(rect.height||560));
  const margin={top:18,right:18,bottom:18,left:18};
  const plotW=Math.max(200,width-margin.left-margin.right);
  const plotH=Math.max(160,height-margin.top-margin.bottom);
  let xMin=97,xMax=103,yMin=97,yMax=103;
  pts.forEach(p=>{
    if(p.x<xMin)xMin=p.x;
    if(p.x>xMax)xMax=p.x;
    if(p.y<yMin)yMin=p.y;
    if(p.y>yMax)yMax=p.y;
  });
  const spanX=Math.max(0.8,xMax-xMin);
  const spanY=Math.max(0.8,yMax-yMin);
  const padBase=Math.max(Math.max(spanX,spanY)*0.05,0.32);
  const xPad=Math.max(spanX*0.07,padBase);
  const yPad=Math.max(spanY*0.07,padBase);
  xMin-=xPad;
  xMax+=xPad;
  yMin-=yPad;
  yMax+=yPad;
  const midPad=Math.max(padBase*0.9,0.4);
  if(100<xMin) xMin=100-midPad;
  if(100>xMax) xMax=100+midPad;
  if(100<yMin) yMin=100-midPad;
  if(100>yMax) yMax=100+midPad;
  const base={
    xMin,yMin,xMax,yMax,
    xSpan:Math.max(1,xMax-xMin),
    ySpan:Math.max(1,yMax-yMin)
  };
  const st=rotGetView(rotMode);
  const view=rotClampView(base,st);
  const xPx=v=>margin.left+((v-view.xMin)/view.xSpan)*plotW;
  const yPx=v=>margin.top+plotH-((v-view.yMin)/view.ySpan)*plotH;
  host.innerHTML='';
  const svg=rotMakeEl('svg',{class:'rot-svg',width:'100%',height:'100%',viewBox:`0 0 ${width} ${height}`,preserveAspectRatio:'xMidYMid meet'});
  const defs=rotMakeEl('defs');
  const clipId='rotClip-'+rotMode;
  const clip=rotMakeEl('clipPath',{id:clipId});
  clip.appendChild(rotMakeEl('rect',{x:margin.left,y:margin.top,width:plotW,height:plotH}));
  defs.appendChild(clip);
  svg.appendChild(defs);

  const bg=rotMakeEl('g',{'clip-path':`url(#${clipId})`});
  const addQuad=(x0,x1,y0,y1,fill,label,color,anchor)=>{
    const xLo=Math.max(Math.min(x0,x1),view.xMin);
    const xHi=Math.min(Math.max(x0,x1),view.xMax);
    const yLo=Math.max(Math.min(y0,y1),view.yMin);
    const yHi=Math.min(Math.max(y0,y1),view.yMax);
    if(!(xHi>xLo && yHi>yLo)) return;
    const x=xPx(xLo);
    const y=yPx(yHi);
    const w=Math.max(0,xPx(xHi)-xPx(xLo));
    const h=Math.max(0,yPx(yLo)-yPx(yHi));
    bg.appendChild(rotMakeEl('rect',{x,y,width:w,height:h,fill,class:'rot-quad-fill'}));
    if(w>=130 && h>=72){
      const right=String(anchor||'').includes('right');
      const bottom=String(anchor||'').includes('bottom');
      const tx=right ? x+w-24 : x+24;
      const ty=bottom ? y+h-22 : y+26;
      const t=rotMakeEl('text',{x:tx,y:ty,'text-anchor':right?'end':'start',class:'rot-quad-title',fill:color});
      t.textContent=label;
      bg.appendChild(t);
    }
  };
  addQuad(view.xMin,100,100,view.yMax,'rgba(18,35,62,0.34)','IMPROVING','#4a78bc','left-top');
  addQuad(100,view.xMax,100,view.yMax,'rgba(10,40,16,0.34)','LEADING','#43a248','right-top');
  addQuad(view.xMin,100,view.yMin,100,'rgba(54,14,18,0.34)','LAGGING','#b14f4f','left-bottom');
  addQuad(100,view.xMax,view.yMin,100,'rgba(48,40,10,0.32)','WEAKENING','#ab8d28','right-bottom');
  const grid=rotMakeEl('g',{'clip-path':`url(#${clipId})`});
  for(let xv=Math.ceil(view.xMin);xv<=Math.floor(view.xMax);xv++){ 
    const px=xPx(xv);
    grid.appendChild(rotMakeEl('line',{x1:px,y1:margin.top,x2:px,y2:margin.top+plotH,class:'rot-grid-line'}));
  }
  for(let yv=Math.ceil(view.yMin);yv<=Math.floor(view.yMax);yv++){ 
    const py=yPx(yv);
    grid.appendChild(rotMakeEl('line',{x1:margin.left,y1:py,x2:margin.left+plotW,y2:py,class:'rot-grid-line'}));
  }
  svg.appendChild(grid);
  if(100>=view.xMin && 100<=view.xMax){
    const cx=xPx(100);
    bg.appendChild(rotMakeEl('line',{x1:cx,y1:margin.top,x2:cx,y2:margin.top+plotH,class:'rot-mid-line'}));
  }
  if(100>=view.yMin && 100<=view.yMax){
    const cy=yPx(100);
    bg.appendChild(rotMakeEl('line',{x1:margin.left,y1:cy,x2:margin.left+plotW,y2:cy,class:'rot-mid-line'}));
  }
  svg.appendChild(bg);
  const dataLayer=rotMakeEl('g',{'clip-path':`url(#${clipId})`});
  svg.appendChild(dataLayer);

  built.forEach(series=>{
    const tail=series.tail;
    const item=series.item;
    const points=tail.map(p=>`${xPx(p.x)},${yPx(p.y)}`).join(' ');
    dataLayer.appendChild(rotMakeEl('polyline',{
      points,
      class:'rot-tail-glow',
      stroke:rotHexToRgba(item.color,0.14),
      'stroke-width':'4.8'
    }));
    for(let i=0;i<tail.length-1;i++){ 
      const a=tail[i],b=tail[i+1];
      const fade=(i+1)/Math.max(tail.length-1,1);
      dataLayer.appendChild(rotMakeEl('line',{
        x1:xPx(a.x),y1:yPx(a.y),x2:xPx(b.x),y2:yPx(b.y),
        class:'rot-tail-seg',
        stroke:rotHexToRgba(item.color,0.18+fade*0.74),
        'stroke-width':(0.8+fade*2.9).toFixed(2)
      }));
    }
    for(let i=0;i<tail.length-1;i++){ 
      const p=tail[i];
      const fade=(i+1)/Math.max(tail.length-1,1);
      dataLayer.appendChild(rotMakeEl('circle',{
        cx:xPx(p.x),cy:yPx(p.y),r:(1.3+fade*1.0).toFixed(2),
        class:'rot-tail-dot',
        fill:rotHexToRgba(item.color,0.14+fade*0.42)
      }));
    }
    const last=tail[tail.length-1];
    const lx=xPx(last.x),ly=yPx(last.y);
    dataLayer.appendChild(rotMakeEl('circle',{cx:lx,cy:ly,r:8.6,fill:rotHexToRgba(item.color,0.20)}));
    dataLayer.appendChild(rotMakeEl('circle',{cx:lx,cy:ly,r:6.9,fill:item.color,stroke:'#ffffff','stroke-width':2.1,class:'rot-last-dot'}));
    const labelRight=last.x>=100;
    const labelUp=last.y>=100;
    const label=rotMakeEl('text',{
      x:lx+(labelRight?12:-12),
      y:ly+(labelUp?-14:18),
      'text-anchor':labelRight?'start':'end',
      class:'rot-last-label',
      fill:'#ffffff',
      stroke:'rgba(0,0,0,.88)'
    });
    label.textContent=item.ticker;
    svg.appendChild(label);
    // Large transparent hit circle centered on the dot (not the label)
    const hit=rotMakeEl('circle',{cx:lx,cy:ly,r:48,fill:'transparent',style:'cursor:pointer'});
    hit.addEventListener('mouseenter',evt=>rotShowTip(evt,host,item,last));
    hit.addEventListener('mousemove',evt=>rotShowTip(evt,host,item,last));
    hit.addEventListener('mouseleave',rotHideTip);
    svg.appendChild(hit);
  });
  host.appendChild(svg);
  rotAttachInteractions(host,view,base,margin,plotW,plotH);
}
window.addEventListener('message',function(evt){
  const data=evt&&evt.data;
  if(!data||data.type!=='rotation-mode'||!data.mode) return;
  rotSetMode(data.mode);
});
window.addEventListener('load',function(){
  rotBindPanHandlers();
  fetch('/api/rotation')
    .then(r=>r.ok?r.json():{})
    .then(data=>{Object.assign(ROTATION_DATA,data||{});renderRotation();})
    .catch(()=>{renderRotation();});
});
window.addEventListener('resize',rotQueueRender);

// --- WATCHLIST PANEL ---
let WATCHLISTS = [];
let ACTIVE_WATCHLIST = 0;
const WATCHLIST_KEY = 'gekko_watchlists_v1';

function loadWatchlists() {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    if (raw) {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr) && arr.length) {
        WATCHLISTS = arr;
        ACTIVE_WATCHLIST = Math.min(ACTIVE_WATCHLIST, WATCHLISTS.length-1);
      }
    }
  } catch (e) {}
  if (!WATCHLISTS.length) {
    WATCHLISTS = [{ name: 'Default', symbols: ['AAPL','MSFT','GOOG','AMZN','TSLA'] }];
    ACTIVE_WATCHLIST = 0;
  }
}
function saveWatchlists() {
  try { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(WATCHLISTS)); } catch (e) {}
  try {
    fetch('/api/prefs',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({[WATCHLIST_KEY]:{watchlists:WATCHLISTS,active:ACTIVE_WATCHLIST}})
    }).catch(()=>{});
  } catch(_e) {}
}
function renderWatchlist() {
  const wl = WATCHLISTS[ACTIVE_WATCHLIST] || { symbols: [] };
  const list = document.getElementById('watchlistList');
  if (!list) return;
  list.innerHTML = '';
  const showPrice = document.getElementById('wlShowPrice')?.checked;
  const showPct = document.getElementById('wlShowPct')?.checked;
  const showDelta = document.getElementById('wlShowDelta')?.checked;
  const candleData = getCandleData();
  wl.symbols.forEach(sym => {
    const row = document.createElement('div');
    row.className = 'watchlist-row';
    row.onclick = () => goChart(sym);
    row.title = sym;
    const symEl = document.createElement('span');
    symEl.className = 'watchlist-symbol';
    symEl.textContent = sym;
    row.appendChild(symEl);
    const bars = candleData[sym];
    let price = '', pct = '', delta = '';
    if (bars && bars.length) {
      const last = bars[bars.length-1];
      const prev = bars.length>1 ? bars[bars.length-2] : null;
      price = last.c != null ? '$'+Number(last.c).toFixed(2) : '';
      if (prev && last.c != null && prev.c != null) {
        const d = last.c - prev.c;
        delta = (d>=0?'+':'') + d.toFixed(2);
        pct = prev.c!==0 ? ((d/prev.c)*100).toFixed(2)+'%' : '';
      }
    }
    if (showPrice) { const el = document.createElement('span'); el.className='watchlist-price'; el.textContent=price; row.appendChild(el); }
    if (showPct) { const el = document.createElement('span'); el.className='watchlist-pct'; el.textContent=pct; row.appendChild(el); }
    if (showDelta) { const el = document.createElement('span'); el.className='watchlist-delta'; el.textContent=delta; row.appendChild(el); }
    list.appendChild(row);
  });
  // Dropdown
  const dd = document.getElementById('watchlistDropdown');
  if (dd) {
    dd.innerHTML = WATCHLISTS.map((w,i)=>`<option value="${i}"${i===ACTIVE_WATCHLIST?' selected':''}>${w.name}</option>`).join('');
    dd.onchange = e => { ACTIVE_WATCHLIST = Number(e.target.value)||0; renderWatchlist(); };
  }
}
function toggleWatchlistPanel() {
  document.body.classList.toggle('watchlist-open');
}
function addWatchlist() {
  const name = prompt('New watchlist name?');
  if (!name) return;
  WATCHLISTS.push({ name, symbols: [] });
  ACTIVE_WATCHLIST = WATCHLISTS.length-1;
  saveWatchlists();
  renderWatchlist();
}
function editWatchlist() {
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return;
  const input = prompt('Edit symbols (comma separated):', wl.symbols.join(','));
  if (input==null) return;
  wl.symbols = input.split(',').map(s=>s.trim().toUpperCase()).filter(Boolean);
  saveWatchlists();
  renderWatchlist();
}
function deleteWatchlist() {
  if (WATCHLISTS.length<=1) return alert('Cannot delete last watchlist.');
  if (!confirm('Delete this watchlist?')) return;
  WATCHLISTS.splice(ACTIVE_WATCHLIST,1);
  ACTIVE_WATCHLIST = Math.max(0,ACTIVE_WATCHLIST-1);
  saveWatchlists();
  renderWatchlist();
}
window.addEventListener('DOMContentLoaded',()=>{
  loadWatchlists();
  renderWatchlist();
});
</script>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# INDEX HTML TEMPLATE
# ---------------------------------------------------------------------------


def build_index_html():
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gekko App</title>
<link id="faviconEl" rel="icon" type="image/png" href="/tray_icon.png">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1/dist/chartjs-plugin-zoom.min.js"></script>
<script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap");

:root {
  --bg:#000000;
  --surface:#070707;
  --surface2:#0A0A0A;
  --surface3:#111111;
  --panel:#0D0D0D;
  --panel-2:#101010;
  --border:#1a1a1a;
  --border2:#2A2A2A;
  --grid:rgba(255,255,255,.035);
  --text:#EAEAEA;
  --dim:#B0B0B0;
  --muted:#999999;
  --silver:#B0B0B0;
  --silver-bright:#D4D4D4;
  --green:#119600;
  --green-bright:#33AA00;
  --green-soft:#77AA00;
  --red:#AA0000;
  --red-bright:#CC3300;
  --orange:#DD6600;
  --amber:#CC9900;
  --mono:'JetBrains Mono',monospace;
  --sans:'DM Sans','Segoe UI',system-ui,sans-serif;
  --radius-sm:8px;
  --radius-md:12px;
  --radius-lg:16px;
  --shadow-panel:0 12px 30px rgba(0,0,0,.32);
  --glow-subtle:0 0 16px rgba(180,180,180,.04),0 0 28px rgba(180,180,180,.02);
}

*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
html { scroll-behavior:smooth; }
html,body { min-height:100%; height:100%; background:var(--bg); color:var(--text); }
body {
  font-family:var(--sans);
  font-size:12px;
  line-height:1.4;
  background:radial-gradient(circle at top center, rgba(255,255,255,.02), transparent 28%), var(--bg);
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
  display:flex; flex-direction:column;
}
#mainArea { display:flex; flex-direction:column; flex:1; min-height:0; transition:margin-left .18s ease, margin-right .18s ease; }
body.panel-open #mainArea { margin-left:252px; }
body.watchlist-open #mainArea { margin-right:240px; }

#watchlistPanel {
  position:fixed; top:0; right:0; width:240px; height:100vh; z-index:200;
  background:#111111; border-left:1px solid #232323; border-radius:0; box-shadow:none;
  display:none; flex-direction:column; overflow:hidden;
  font-family:var(--sans); font-size:12px; color:#f3f4f6;
}
body.watchlist-open #watchlistPanel { display:flex; }
.watchlist-topbar { display:flex; align-items:stretch; padding:12px 12px 8px; }
.watchlist-controls { display:flex; flex-direction:column; gap:6px; flex:1; min-width:0; }
.watchlist-dropdown-wrap { position:relative; flex:1; min-width:0; }
.watchlist-dropdown {
  width:100%; appearance:none; -webkit-appearance:none; -moz-appearance:none; background:#111111; background-image:none; color:#f4f4f5;
  border:1px solid #232323; border-radius:8px; padding:4px 10px; min-height:30px;
  font-family:var(--sans); font-size:16px; font-weight:700; outline:none;
  color-scheme:dark;
}
.watchlist-dropdown option { background:#111111; color:#f4f4f5; }
.watchlist-dropdown-wrap::after {
  display:none;
}
.watchlist-settings-menu {
  display:none; flex-direction:column; gap:2px; padding:4px 0;
  border-top:1px solid #1e1e1e; margin-top:2px;
}
.watchlist-settings-menu.open { display:flex; }
.wl-settings-btn {
  background:none; border:none; padding:5px 4px; cursor:pointer;
  color:#888; font-family:var(--sans); font-size:11px; font-weight:500;
  text-align:left; border-radius:5px; transition:color .12s ease, background .12s ease;
}
.wl-settings-btn:hover { color:#d4d4d8; background:#181818; }
.wl-settings-btn.danger:hover { color:#f87171; background:#1e1212; }
.watchlist-colhead {
  display:grid; grid-template-columns:minmax(0,1fr) 56px 54px 18px; gap:6px; align-items:center;
  padding:8px 10px; border-bottom:1px solid #232323; color:#888888; font-family:var(--sans); font-size:12px;
}
.watchlist-head-metric { justify-self:end; text-align:right; }
.wl-sortable-head {
  cursor:pointer; user-select:none;
  transition:color .12s ease;
  display:inline-flex; align-items:center; gap:3px;
}
.wl-sortable-head:hover { color:#c0c0c8; }
.wl-sortable-head.active { color:#d4d4d8; }
.wl-sortable-head .wl-sort-arrow { font-size:9px; opacity:0.7; }
.watchlist-list { flex:1; overflow:auto; }
.watchlist-empty { padding:18px 12px; color:#757575; font-size:11px; line-height:1.45; }
.watchlist-row {
  position:relative;
  display:grid; grid-template-columns:minmax(0,1fr) 56px 54px 18px; gap:6px; align-items:center;
  padding:9px 12px; border-bottom:1px solid #1f1f1f; cursor:pointer; background:transparent; transition:background .12s ease;
}
.watchlist-row:hover { background:#151515; }
.watchlist-row.active { background:#181818; box-shadow:inset 2px 0 0 #d4d4d8; }
.watchlist-section-row {
  grid-template-columns:minmax(0,1fr) auto auto;
  padding:8px 12px;
  background:#101010;
  border-top:1px solid #222222;
  border-bottom:1px solid #1b1b1b;
  cursor:default;
}
.watchlist-section-row:hover { background:#131313; }
.watchlist-row.reorderable { cursor:grab; }
.watchlist-row.reorderable:active { cursor:grabbing; }
.watchlist-row.dragging { opacity:.34; }
.watchlist-row.drop-before { box-shadow:inset 0 2px 0 rgba(196,204,214,.92); }
.watchlist-row.drop-after { box-shadow:inset 0 -2px 0 rgba(196,204,214,.92); }
.watchlist-symbol-wrap { min-width:0; display:flex; align-items:center; gap:0; }
.watchlist-drag-handle {
  width:4px; flex-shrink:0; user-select:none;
}
.watchlist-row.reorderable .watchlist-drag-handle { cursor:grab; }
.watchlist-section-main { min-width:0; display:flex; align-items:center; gap:8px; overflow:hidden; }
.watchlist-section-label {
  min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  color:#d0d4da; font-family:var(--sans); font-size:10px; font-weight:700;
  letter-spacing:.12em; text-transform:uppercase;
}
.watchlist-section-rule {
  flex:1; min-width:14px; height:1px;
  background:linear-gradient(90deg, rgba(166,174,188,.50), rgba(166,174,188,0));
}
.watchlist-symbol {
  min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  font-family:var(--sans); font-size:12px; font-weight:600; color:#f3f4f6; letter-spacing:.01em;
}
.watchlist-price,
.watchlist-pct {
  justify-self:end; font-family:var(--sans); font-size:12px;
  font-variant-numeric:tabular-nums; font-feature-settings:'tnum' 1;
}
.watchlist-price { color:#ffffff; }
.watchlist-price.na { color:#8a8a8a; }
.watchlist-pct.pos { color:#00c176; }
.watchlist-pct.neg { color:#ff4d5f; }
.watchlist-pct.neu { color:#b8b8b8; }
.watchlist-remove,
.watchlist-section-btn,
.watchlist-add-btn {
  min-height:20px; border:1px solid #2a2a2a; background:#141414; color:#7f8792;
  border-radius:6px; font-family:var(--sans); font-size:10px; font-weight:700;
  line-height:1; cursor:pointer; transition:opacity .12s ease,color .12s ease,border-color .12s ease,background .12s ease;
}
.watchlist-remove { width:20px; padding:0; opacity:0; }
.watchlist-section-btn { padding:0 8px; opacity:0; letter-spacing:.04em; }
.watchlist-row:hover .watchlist-remove,
.watchlist-row:hover .watchlist-section-btn { opacity:1; }

.watchlist-remove:hover,
.watchlist-section-btn:hover,
.watchlist-add-btn:hover { color:#ffffff; border-color:#3b3b3b; background:#1a1a1a; }
.watchlist-add-row {
  display:flex; justify-content:flex-end; gap:6px;
  padding:8px 12px 10px; border-bottom:1px solid #1f1f1f; background:transparent;
}
.watchlist-add-btn { padding:0 8px; color:#a3aab4; }
::-webkit-scrollbar { width:8px; height:8px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:#262626; border-radius:999px; }
::-webkit-scrollbar-thumb:hover { background:#363636; }
.topbar { display:none; }
.topbar-meta { font-family:var(--mono); font-size:11px; letter-spacing:.02em; color:var(--muted); }
.topbar-meta em { color:var(--silver-bright); font-style:normal; font-weight:600; }
.tabs { display:flex; align-items:center; gap:10px; flex-wrap:wrap; padding:12px 16px; border-bottom:1px solid var(--border); background:linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,0)); flex-shrink:0; transition:margin-left .18s ease, margin-right .18s ease; }
body.panel-open .tabs { margin-left:272px; }
body.watchlist-open .tabs { margin-right:240px; }
.tabs-spacer { flex:1 1 auto; }
.tab-btn { appearance:none; border:1px solid var(--border); background:var(--surface2); color:var(--dim); border-radius:11px; padding:9px 14px; font-family:var(--sans); font-size:12px; font-weight:600; letter-spacing:.01em; cursor:pointer; transition:all .16s ease; }
.tab-btn:hover { color:var(--text); border-color:var(--border2); background:var(--panel); transform:translateY(-1px); }
.tab-btn.active { color:var(--text); background:#111111; border-color:#232323; box-shadow:inset 0 0 0 1px rgba(255,255,255,.015), var(--glow-subtle); }
.watchlist-toggle-btn {
  position:fixed; top:10px; right:240px;
  z-index:201; width:14px; height:30px;
  background:#1a1a1a; border:1px solid #2a2a2a; border-right:none;
  border-radius:6px 0 0 6px;
  color:#555; cursor:pointer; appearance:none;
  display:flex; align-items:center; justify-content:center;
  transition:background .15s, color .15s, right .18s ease;
  padding:0; overflow:visible;
}
.watchlist-toggle-btn::after {
  content:''; display:block; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) translateY(-9px);
  width:4px; height:4px;
  background:currentColor; border-radius:2px;
  box-shadow:0 9px 0 currentColor, 0 18px 0 currentColor;
}
.watchlist-toggle-btn:hover { background:#222; color:#888; }
body:not(.watchlist-open) .watchlist-toggle-btn { right:0; }
.left-panel-toggle-btn {
  position:fixed; top:10px; left:252px;
  z-index:201; width:14px; height:30px;
  background:#1a1a1a; border:1px solid #2a2a2a; border-left:none;
  border-radius:0 6px 6px 0;
  color:#555; cursor:pointer; appearance:none;
  display:flex; align-items:center; justify-content:center;
  transition:background .15s, color .15s, left .18s ease;
  padding:0; overflow:visible;
}
.left-panel-toggle-btn::after {
  content:''; display:block; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%) translateY(-9px);
  width:4px; height:4px;
  background:currentColor; border-radius:2px;
  box-shadow:0 9px 0 currentColor, 0 18px 0 currentColor;
}
.left-panel-toggle-btn:hover { background:#222; color:#888; }
body:not(.panel-open) .left-panel-toggle-btn { left:0; }
.tab-pane { display:none; }
.tab-pane.active { display:flex; flex-direction:column; flex:1; min-height:0; overflow-y:auto; }
#tab-heatmap.active { overflow:hidden; }
.buy-layout { padding:0; display:flex; flex-direction:column; flex:1; min-height:0; overflow:hidden; }
.buy-grid { flex:1; min-height:0; display:grid; grid-template-columns:minmax(0,1fr); grid-template-rows:1fr; gap:8px; overflow:hidden; }
.side-panel { background:linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01)), var(--surface); border:1px solid var(--border); border-radius:14px; padding:6px; font-family:var(--mono); font-size:10px; display:flex; flex-direction:column; gap:5px; overflow-y:auto; overflow-x:hidden; box-shadow:var(--shadow-panel); }
#giSignalPanel {
  position:fixed; top:0; left:0; width:252px; height:100vh; z-index:200;
  background:#0a0a0a; border-right:1px solid #1e1e1e; border-radius:0; box-shadow:none;
  display:none; flex-direction:column; gap:6px; padding:10px 4px; overflow-y:auto; overflow-x:hidden;
  font-family:var(--mono); font-size:10px; color:var(--text);
}
body.panel-open #giSignalPanel { display:flex; }
.panel-card { background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.05); border-radius:10px; padding:5px 6px; }
.gisp-summary-card {
  display:flex; align-items:center; justify-content:space-between; gap:10px;
  padding:6px 8px; border-radius:10px;
  background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015));
  border:1px solid rgba(255,255,255,.06);
}
.gisp-summary-main,.gisp-summary-side { min-width:0; display:flex; flex-direction:column; gap:2px; }
.gisp-summary-side { align-items:flex-end; text-align:right; }
.gisp-summary-label { color:var(--muted); font-size:7px; text-transform:uppercase; letter-spacing:.1em; font-weight:700; }
.gisp-summary-score {
  font-family:var(--mono); font-size:21px; line-height:1; font-weight:800;
  font-variant-numeric:tabular-nums; font-feature-settings:'tnum' 1;
}
.gisp-summary-zone {
  display:inline-flex; align-items:center; justify-content:center;
  min-height:22px; padding:0 9px; border-radius:999px;
  border:1px solid rgba(255,255,255,.08);
  font-size:10px; font-weight:700; line-height:1; white-space:nowrap;
}
.gisp-fv-card { display:flex; flex-direction:column; gap:5px; padding:5px 8px; }
.gisp-fv-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.gisp-fv-copy { min-width:0; display:flex; flex-direction:column; gap:0; }
.gisp-fv-label { color:var(--muted); font-size:8px; text-transform:uppercase; letter-spacing:.12em; font-weight:700; }
.gisp-fv-value {
  font-family:var(--mono); font-size:14px; line-height:1; font-weight:800;
  font-variant-numeric:tabular-nums; font-feature-settings:'tnum' 1;
}
.gisp-fv-last { display:none; }
.gisp-fv-track {
  position:relative; height:6px; border-radius:999px; overflow:visible;
  background:linear-gradient(90deg, rgba(17,150,0,.84) 0%, rgba(108,176,24,.78) 36%, rgba(170,138,26,.56) 50%, rgba(182,92,28,.72) 68%, rgba(170,0,0,.84) 100%);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.06);
}
.gisp-fv-mid { position:absolute; left:50%; top:1px; bottom:1px; width:1px; background:rgba(255,255,255,.18); transform:translateX(-50%); }
.gisp-fv-dot {
  position:absolute; top:50%; width:8px; height:8px; border-radius:999px; transform:translate(-50%,-50%);
  background:#f8fafc; border:1.5px solid #0a0a0a; box-shadow:0 0 0 1px rgba(255,255,255,.22), 0 2px 4px rgba(0,0,0,.45);
}
.gisp-fv-meta { display:flex; align-items:center; gap:6px; font-size:9px; font-weight:700; }
.panel-title { font-size:8px; color:var(--muted); text-transform:uppercase; letter-spacing:.12em; margin-bottom:4px; font-weight:700; }
.metric-grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:5px; }
.metric-grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:5px; }
.metric-card { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.04); border-radius:8px; padding:6px 7px; min-width:0; }
.metric-label { color:var(--muted); font-size:7px; margin-bottom:2px; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { font-size:10px; font-weight:700; line-height:1.1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mini-table { width:100%; border-collapse:separate; border-spacing:0; table-layout:fixed; }
.mini-table td,.mini-table th { padding:2px 3px; font-size:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bt-grid { display:grid; grid-template-columns:1fr 1fr; gap:4px; }
.bt-metric { display:flex; flex-direction:column; gap:2px; background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.04); border-radius:8px; padding:6px 8px; min-width:0; }
.bt-metric .k { color:#666; font-size:7.5px; text-transform:uppercase; letter-spacing:.09em; font-weight:700; }
.bt-metric .v { min-width:0; display:flex; flex-direction:column; gap:0; }
.bt-main { display:block; max-width:100%; font-size:12px; font-weight:700; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:1.2; }
.bt-sub { display:block; max-width:100%; color:#888; font-size:8px; font-weight:600; line-height:1.25; letter-spacing:-.01em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.gisp-matrix { display:grid; grid-template-columns:22px repeat(5,1fr); gap:0; font-family:var(--mono); font-size:9px; border-radius:7px; overflow:hidden; border:1px solid rgba(255,255,255,.06); }
.gm-hdr { padding:3px 3px; font-size:8px; font-weight:700; color:#666; text-transform:uppercase; letter-spacing:.07em; background:rgba(255,255,255,.04); border-bottom:1px solid rgba(255,255,255,.06); text-align:center; white-space:nowrap; overflow:hidden; }
.gm-cell { padding:4px 2px; border-bottom:1px solid rgba(255,255,255,.03); display:flex; align-items:center; min-width:0; overflow:hidden; }
.gm-period { font-size:9px; font-weight:600; color:var(--muted); }
.gm-spark { width:100%; height:3px; background:rgba(255,255,255,.07); border-radius:2px; overflow:hidden; flex-shrink:0; }
.gm-zone-col { justify-content:center; font-size:10px; font-weight:700; }
.gm-loading { color:rgba(255,255,255,.42); letter-spacing:.08em; animation:gmPulse 1.1s ease-in-out infinite; }
@keyframes gmPulse {
  0%,100% { opacity:.42; }
  50% { opacity:.95; }
}
.gm-act-col { background:rgba(255,255,255,.08) !important; }
.gm-unified-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:5px; }
.gm-zone-dot { width:6px; height:6px; border-radius:50%; display:inline-block; flex-shrink:0; }
.gisp-fv-track { position:relative; height:8px; border-radius:999px; overflow:visible; background:linear-gradient(90deg,rgba(17,150,0,.88) 0%,rgba(70,160,40,.7) 30%,rgba(160,130,30,.5) 50%,rgba(180,90,25,.75) 65%,rgba(200,30,30,.85) 100%); box-shadow:inset 0 0 0 1px rgba(255,255,255,.06); }
.gisp-sizer-controls { display:flex; flex-direction:column; gap:5px; margin-bottom:5px; }
.gisp-sizer-duo { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:5px; }
.gisp-sizer-field { min-width:0; display:flex; flex-direction:column; gap:2px; }
.gisp-sizer-label { color:rgba(255,255,255,.45); font-size:8px; text-transform:uppercase; letter-spacing:.09em; font-weight:700; }
.gisp-sizer-field .ctrl-input { width:100%; min-width:0; }
.gisp-sizer-toggle { display:grid; grid-template-columns:1fr 1fr; gap:4px; }
.gisp-sizer-toggle .th-cat-btn { min-height:26px; padding:5px 8px; font-size:10px; border-radius:7px; }
.gisp-sizer-note { color:var(--muted); font-size:9px; line-height:1.25; margin-top:1px; }
.gisp-mode-row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.gisp-mode-pills { display:flex; gap:2px; background:rgba(255,255,255,.05); border-radius:6px; padding:2px; }
.gisp-mode-btn { background:transparent; border:none; color:var(--muted); font-size:10px; font-weight:600; padding:3px 5px; border-radius:4px; cursor:pointer; font-family:inherit; transition:background .15s,color .15s; white-space:nowrap; }
.gisp-mode-btn.active { background:rgba(255,255,255,.12); color:var(--text); }
.gisp-atr-pills { display:grid; grid-template-columns:repeat(6,1fr); gap:2px; background:rgba(255,255,255,.05); border-radius:6px; padding:2px; }
.gisp-atr-pills .gisp-mode-btn { text-align:center; width:100%; padding:4px 2px; }
.gisp-summary-container { background:rgba(255,255,255,.03); border-radius:6px; padding:7px 8px; margin-top:6px; border:1px solid rgba(255,255,255,.07); }
.gisp-summary-row { display:flex; justify-content:space-between; align-items:baseline; font-family:var(--mono); font-size:11px; padding:3px 0; color:var(--text); border-bottom:1px solid rgba(255,255,255,.04); }
.gisp-summary-row:last-child { border-bottom:none; padding-bottom:0; }
.gisp-summary-row:first-child { padding-top:0; }
.gisp-value-pos { color:#00e5cc; font-weight:700; }
.gisp-value-neg { color:#ff5555; font-weight:700; }
.gisp-value-neu { color:#ffd700; font-weight:700; }
.gisp-label-muted { color:var(--muted); }

/* ======= v2 Position Sizer Results ======= */
.gsz-results { margin-top:7px; display:flex; flex-direction:column; gap:6px; }
/* Hero row: Shares (left, big) | R/R verdict (right) */
.gsz-hero {
  display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:6px;
  background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.09); border-radius:8px; padding:7px 9px;
}
.gsz-hero-cell { min-width:0; display:flex; flex-direction:column; gap:2px; }
.gsz-hero-cell.right { align-items:flex-end; text-align:right; border-left:1px solid rgba(255,255,255,.07); padding-left:8px; }
.gsz-hero-label { font-size:8px; color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-weight:700; display:flex; align-items:center; gap:4px; }
.gsz-hero-val {
  font-family:var(--mono); font-size:22px; line-height:1.05; font-weight:800; color:var(--text);
  font-variant-numeric:tabular-nums; font-feature-settings:'tnum' 1; letter-spacing:-.01em;
}
.gsz-hero-val.capped { color:#ffd36b; }
.gsz-hero-val.rr-good { color:#34e38a; }
.gsz-hero-val.rr-ok { color:var(--text); }
.gsz-hero-val.rr-bad { color:#ff6b6b; }
.gsz-hero-sub { font-family:var(--mono); font-size:10px; color:var(--muted); line-height:1.25; }
.gsz-copy-btn {
  background:transparent; border:1px solid rgba(255,255,255,.12); color:var(--muted);
  font-size:9px; font-weight:700; padding:1px 5px 2px; border-radius:4px; cursor:pointer;
  font-family:inherit; letter-spacing:.04em; transition:all .12s ease; line-height:1;
}
.gsz-copy-btn:hover { color:var(--text); border-color:rgba(255,255,255,.28); background:rgba(255,255,255,.04); }
.gsz-copy-btn.copied { color:#34e38a; border-color:rgba(52,227,138,.45); }
.gsz-badge {
  display:inline-flex; align-items:center; gap:3px; font-size:8px; font-weight:700;
  padding:1px 5px 2px; border-radius:3px; text-transform:uppercase; letter-spacing:.08em; line-height:1;
}
.gsz-badge.good { background:rgba(52,227,138,.14); color:#34e38a; border:1px solid rgba(52,227,138,.28); }
.gsz-badge.warn { background:rgba(255,211,107,.14); color:#ffd36b; border:1px solid rgba(255,211,107,.28); }
.gsz-badge.bad { background:rgba(255,107,107,.14); color:#ff6b6b; border:1px solid rgba(255,107,107,.28); }

/* Risk/Reward visual bar */
.gsz-rr {
  position:relative; height:26px; border-radius:6px;
  background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
  overflow:hidden; margin:1px 0 2px;
}
.gsz-rr-fill-risk { position:absolute; top:0; bottom:0; background:linear-gradient(90deg,rgba(255,107,107,.32),rgba(255,107,107,.10)); }
.gsz-rr-fill-reward { position:absolute; top:0; bottom:0; background:linear-gradient(90deg,rgba(52,227,138,.10),rgba(52,227,138,.32)); }
.gsz-rr-entry { position:absolute; top:0; bottom:0; width:1px; background:rgba(255,255,255,.55); box-shadow:0 0 6px rgba(255,255,255,.35); }
.gsz-rr-tick {
  position:absolute; top:0; bottom:0; display:flex; align-items:flex-end; padding-bottom:2px;
  font-family:var(--mono); font-size:8.5px; font-weight:700; line-height:1; letter-spacing:-.01em; white-space:nowrap;
  font-variant-numeric:tabular-nums;
}
.gsz-rr-tick.stop { left:4px; color:#ff8a8a; }
.gsz-rr-tick.entry-lbl { top:1px; transform:translateX(-50%); color:var(--text); font-size:8px; font-weight:800;
  display:flex; align-items:flex-start; padding-bottom:0; }
.gsz-rr-tick.target { right:4px; color:#6be2a4; }
.gsz-rr-pct {
  position:absolute; top:50%; transform:translateY(-50%);
  font-family:var(--mono); font-size:10.5px; font-weight:700; letter-spacing:-.01em;
  color:var(--muted); font-variant-numeric:tabular-nums;
}
.gsz-rr-pct.left { left:6px; }
.gsz-rr-pct.right { right:6px; }

/* Two-column metric split: Risk (red) | Reward (green) */
.gsz-split { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
.gsz-split-cell {
  min-width:0; padding:6px 8px; border-radius:7px;
  background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.06);
  display:flex; flex-direction:column; gap:3px;
}
.gsz-split-cell.risk { border-left:2px solid rgba(255,107,107,.55); }
.gsz-split-cell.reward { border-left:2px solid rgba(52,227,138,.55); }
.gsz-split-head { display:flex; align-items:center; justify-content:space-between; gap:6px; }
.gsz-split-title { font-size:8px; color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-weight:700; }
.gsz-split-src { font-family:var(--mono); font-size:8.5px; color:var(--muted); font-weight:600; }
.gsz-split-price { font-family:var(--mono); font-size:14px; font-weight:800; line-height:1; letter-spacing:-.01em;
  font-variant-numeric:tabular-nums; font-feature-settings:'tnum' 1; }
.gsz-split-price.risk { color:#ff8a8a; }
.gsz-split-price.reward { color:#6be2a4; }
.gsz-split-delta { font-family:var(--mono); font-size:9.5px; font-weight:600; color:var(--muted); }
.gsz-split-dollar { font-family:var(--mono); font-size:10.5px; font-weight:700; }
.gsz-split-dollar.risk { color:#ff8a8a; }
.gsz-split-dollar.reward { color:#6be2a4; }
.gsz-split-pct { font-size:9px; color:var(--muted); font-weight:600; margin-left:3px; font-variant-numeric:tabular-nums; }

/* Detail chips under split */
.gsz-meta {
  display:flex; flex-wrap:wrap; gap:4px 6px; font-family:var(--mono); font-size:9.5px;
  color:var(--muted); padding:0 2px;
}
.gsz-meta-item { display:inline-flex; align-items:baseline; gap:3px; }
.gsz-meta-item .k { font-size:10px; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }
.gsz-meta-item .v { color:var(--text); font-weight:700; font-variant-numeric:tabular-nums; }
.gsz-meta-sep { color:rgba(255,255,255,.18); }

/* Pill-row labels (subtle header above ATR / RR pill rows) */
.gsz-pill-label {
  font-size:8px; color:var(--muted); text-transform:uppercase; letter-spacing:.1em; font-weight:700;
  margin:2px 2px 1px; display:flex; align-items:center; justify-content:space-between; gap:6px;
}
.gsz-pill-label .hint { color:rgba(255,255,255,.3); font-weight:500; letter-spacing:.04em; text-transform:none; font-size:9px; }
.chart-main { min-width:0; min-height:0; height:100%; display:flex; flex-direction:column; gap:0; overflow:hidden; position:relative; }
.chart-wrap.clean { padding:0; background:transparent; border:none; border-radius:0; box-shadow:none; overflow:hidden; }
.chart-subwrap { display:none; height:88px; flex-shrink:0; padding:0; background:transparent; border:none; border-radius:0; box-shadow:none; }
.chart-subwrap canvas { display:block; }
@media (max-width: 1240px) {
  .buy-grid { grid-template-columns:220px minmax(0,1fr); }
}
@media (max-width: 1220px) {
  .buy-grid { height:auto; grid-template-columns:1fr; grid-template-rows:minmax(0,1fr) auto; }
  .chart-main { order:1; }
  .side-panel { overflow:visible; }
  #giSignalPanel { order:2; position:relative; width:auto; max-width:none; height:auto; max-height:40vh; border-right:none; }
  body.panel-open #mainArea { margin-left:0; }
  body.panel-open .tabs { margin-left:0; }
}
.controls,.chart-controls,.hm-controls { display:flex; align-items:center; gap:8px; row-gap:4px; flex-wrap:wrap; padding:5px 12px; background:linear-gradient(180deg, rgba(255,255,255,.012), rgba(255,255,255,0)), var(--surface2); border-bottom:1px solid var(--border); }
.ctrl-label { font-family:var(--sans); font-size:11px; font-weight:700; letter-spacing:.06em; color:var(--muted); text-transform:uppercase; }
.ctrl-sep { width:1px; height:22px; background:var(--border); }
.ctrl-input { appearance:none; background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:9px; padding:6px 11px; min-height:30px; font-family:var(--mono); font-size:12px; line-height:1.2; outline:none; transition:border-color .15s ease, box-shadow .15s ease, background .15s ease, transform .12s ease; }
.ctrl-input:hover { border-color:var(--border2); background:#0f0f0f; }
.ctrl-input:focus { border-color:var(--green-bright); box-shadow:0 0 0 3px rgba(51,170,0,.12); }
.ctrl-input::placeholder { color:var(--muted); }
.ctrl-input[type=number] { appearance:textfield; -moz-appearance:textfield; }
.ctrl-input[type=number]::-webkit-outer-spin-button,.ctrl-input[type=number]::-webkit-inner-spin-button { -webkit-appearance:none; margin:0; }
select.ctrl-input { cursor:pointer; padding-right:28px; background-image:url("data:image/svg+xml,%3Csvg width='10' height='6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23777777'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 10px center; }
.num-stepper { display:inline-flex; align-items:stretch; overflow:hidden; border:1px solid var(--border); border-radius:9px; background:var(--surface); min-height:30px; }
.num-stepper .ctrl-input { border:none; border-radius:0; background:transparent; min-height:30px; padding:0 7px; text-align:center; }
.num-stepper .ctrl-input:focus { box-shadow:none; }
.num-step-btn { min-width:26px; border:none; background:var(--panel-2); color:var(--dim); font-family:var(--mono); font-size:11px; font-weight:700; cursor:pointer; transition:all .12s ease; }
.num-step-btn:hover { background:#171717; color:var(--text); }
.num-step-btn.step-dec { border-right:1px solid var(--border); }
.num-step-btn.step-inc { border-left:1px solid var(--border); }
.num-stepper.vsplit { width:100%; }
.num-stepper.vsplit .ctrl-input { flex:1; min-width:0; width:100% !important; overflow:hidden; text-overflow:ellipsis; }
.num-stepper-stack { display:flex; flex-direction:column; min-width:24px; width:24px; border-left:1px solid var(--border); flex-shrink:0; }
.num-stepper.vsplit .num-step-btn { min-width:0; width:100%; flex:1; padding:0; line-height:1; }
.num-stepper.vsplit .num-step-btn.step-inc { border-left:none; border-bottom:1px solid var(--border); }
.num-stepper.vsplit .num-step-btn.step-dec { border-right:none; }
.result-count,.chart-note,.hm-legend-row { font-family:var(--mono); font-size:11px; color:var(--muted); }
.result-count { padding:10px 14px 6px; }
.chart-note { padding:8px 2px 0; }
.table-wrap,.chart-section { padding:14px 16px 18px; }
.table-scroll { overflow:auto; background:linear-gradient(180deg, rgba(255,255,255,.015), rgba(255,255,255,0)), var(--surface2); border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow-panel); }
table { width:100%; border-collapse:separate; border-spacing:0; min-width:1120px; }
thead th { position:sticky; top:0; z-index:2; background:#0b0b0b; border-bottom:1px solid var(--border); padding:13px 12px; text-align:left; user-select:none; cursor:pointer; white-space:nowrap; font-family:var(--sans); font-size:13px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); box-shadow:0 1px 0 rgba(255,255,255,.02); }
thead th:hover { color:var(--silver-bright); background:#101010; }
thead th.sort-asc::after { content:' \2191'; color:var(--green-bright); }
thead th.sort-desc::after { content:' \2193'; color:var(--green-bright); }
tbody tr { border-bottom:1px solid rgba(255,255,255,.035); transition:background .12s ease, box-shadow .12s ease; }
tbody tr:nth-child(even) { background:rgba(255,255,255,.012); }
tbody tr:hover { background:rgba(255,255,255,.035); box-shadow:inset 0 0 0 999px rgba(255,255,255,.01); }
tbody tr.sold-row { opacity:.58; }
tbody td { padding:11px 12px; white-space:nowrap; font-family:var(--mono); font-size:14px; color:var(--text); border-bottom:1px solid rgba(255,255,255,.03); }
.rank-cell,.muted { color:var(--muted); }
.rank-cell { width:46px; text-align:right; padding-right:12px; font-size:11px; }
.sym-cell { min-width:72px; color:var(--silver-bright); padding:0 !important; }
.sym-link {
  appearance:none; border:none; background:none;
  display:inline; width:auto; padding:0; margin:0;
  color:var(--silver-bright); font:inherit; font-weight:700; letter-spacing:.02em;
  cursor:default; text-decoration:none;
}
.sym-link-text {
  cursor:pointer;
}
.sym-link:hover .sym-link-text, .sym-link-text:hover { color:#60a5fa; text-decoration:underline; }
.sym-link:focus-visible {
  outline:1px solid rgba(96,165,250,.75);
  outline-offset:2px;
  border-radius:3px;
}
.sym-chart-popup {
  position:fixed; left:0; top:0; z-index:2100;
  display:none; width:min(85vw,1350px); height:min(82vh,800px);
  background:#0f0f0f; border:1px solid var(--border2); border-radius:12px;
  box-shadow:0 18px 42px rgba(0,0,0,.62); overflow:hidden;
}
.sym-chart-popup.show { display:block; }
.hm-mini-popup {
  position:fixed; left:0; top:0; z-index:2050;
  display:none; width:380px; height:220px;
  background:#0f0f0f; border:1px solid var(--border2); border-radius:10px;
  box-shadow:0 12px 32px rgba(0,0,0,.62); overflow:hidden;
  pointer-events:none;
}
.hm-mini-popup.show { display:block; }
/* Bubble chart custom tooltip */
.bubble-tip {
  position:fixed; left:0; top:0; z-index:2100;
  display:none; width:360px;
  background:#0d0d10; border:1px solid rgba(255,255,255,.13); border-radius:12px;
  box-shadow:0 16px 48px rgba(0,0,0,.75);
  font-family:var(--mono); overflow:hidden;
  cursor:pointer; pointer-events:all;
}
.bubble-tip.show { display:block; }
.bubble-tip-tv { width:100%; height:180px; overflow:hidden; display:block; }
.bubble-tip-tv tv-mini-chart { width:100%; height:208px; display:block; margin-top:-2px; }
.bubble-tip-body { padding:10px 14px 12px; }
.bubble-tip-header { display:flex; align-items:baseline; gap:8px; margin-bottom:8px; }
.bubble-tip-ticker { font-size:18px; font-weight:700; color:#fff; letter-spacing:.02em; }
.bubble-tip-company { font-size:11px; color:#8b8fa8; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.bubble-tip-row { display:flex; justify-content:space-between; align-items:center; padding:3px 0; border-top:1px solid rgba(255,255,255,.05); }
.bubble-tip-row:first-child { border-top:none; }
.bubble-tip-lbl { font-size:10px; color:#6b7080; text-transform:uppercase; letter-spacing:.05em; }
.bubble-tip-val { font-size:12px; font-weight:600; color:#e2e8f0; }
.bubble-tip-click { text-align:center; padding:7px 0 2px; font-size:10px; color:#4a5568; letter-spacing:.04em; }
.bubble-tip-mgr-list { font-size:10px; color:#8b8fa8; line-height:1.6; padding-top:4px; border-top:1px solid rgba(255,255,255,.05); }
/* ---- Bubble Chart v2 ---- */
.bc-cmdbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 12px;border-bottom:1px solid var(--border);background:var(--surface2);}
.bc-search-wrap{position:relative;display:flex;align-items:center}
.bc-search{padding:5px 12px 5px 26px;border-radius:999px;background:var(--panel);border:1px solid #2a2a2a;color:var(--text);font-family:var(--mono);font-size:11px;min-width:160px;outline:none;transition:border-color .12s;}
.bc-search:focus{border-color:#3a3a3a}
.bc-search::placeholder{color:var(--muted)}
.bc-search-icon{position:absolute;left:9px;color:var(--muted);font-size:11px;pointer-events:none}
.bc-cmd-sep{width:1px;height:18px;background:#2a2a2a;margin:0 2px}
.chip{display:inline-flex;align-items:center;gap:5px;padding:4px 9px;border-radius:999px;background:transparent;border:1px solid #222;font-family:var(--mono);font-size:10px;color:var(--dim);cursor:pointer;transition:all .12s;white-space:nowrap;user-select:none;}
.chip:hover{border-color:#3a3a3a;color:var(--text);background:var(--panel)}
.chip.active{background:#16200f;border-color:#33AA0055;color:#a5e077}
.chip-label{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.06em;margin-right:1px}
.chip-val{font-weight:600}
.chip-caret{opacity:.5;margin-left:1px;font-size:9px}
.chip.control{background:transparent;border-color:#222}
.chip.control:hover{border-color:#3a3a3a;background:var(--panel)}
.chip.action{background:transparent;border-style:dashed}
.chip.action:hover{border-style:solid;background:var(--panel)}
.pop{position:fixed;z-index:3000;background:#0C0C0C;border:1px solid #2a2a2a;border-radius:10px;padding:8px;min-width:220px;max-width:320px;box-shadow:0 10px 40px rgba(0,0,0,.8);font-family:var(--sans);font-size:11px;animation:bc-popIn .12s ease-out;}
@keyframes bc-popIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
.pop-title{font-family:var(--mono);font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;padding:4px 8px 8px}
.pop-item{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;cursor:pointer;color:var(--dim);transition:background .08s;}
.pop-item:hover{background:var(--panel);color:var(--text)}
.pop-item.on{color:var(--text)}
.pop-item .check{color:#33AA00;opacity:0;font-size:10px;width:10px}
.pop-item.on .check{opacity:1}
.pop-item .sub{margin-left:auto;color:var(--muted);font-family:var(--mono);font-size:10px}
.pop-row{display:flex;align-items:center;gap:10px;padding:8px;color:var(--dim);}
.pop-row label{font-family:var(--mono);font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;min-width:60px}
.pop-row input[type="range"]{flex:1;accent-color:#33AA00}
.pop-row .val{font-family:var(--mono);color:var(--text);min-width:28px;text-align:right}
.pop-toggle{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 8px;border-radius:6px;cursor:pointer;}
.pop-toggle:hover{background:var(--panel)}
.pop-toggle .label{color:var(--dim)}
.pop-toggle.on .label{color:var(--text)}
.pop-sw{width:28px;height:16px;border-radius:999px;background:#222;position:relative;transition:background .12s;flex-shrink:0}
.pop-sw::after{content:'';position:absolute;top:2px;left:2px;width:12px;height:12px;border-radius:50%;background:#888;transition:all .12s}
.pop-toggle.on .pop-sw{background:#16200f}
.pop-toggle.on .pop-sw::after{left:14px;background:#33AA00}
.pop-sep{height:1px;background:#1a1a1a;margin:4px 0}
.pop-btn{width:100%;padding:6px 10px;border-radius:6px;background:var(--panel);border:1px solid #2a2a2a;color:var(--text);font-family:var(--sans);font-size:11px;cursor:pointer;text-align:left;margin-bottom:2px;}
.pop-btn:hover{background:var(--panel-2);border-color:#3a3a3a}
.pop-btn.danger:hover{border-color:#aa3333;color:#ff9a9a}
.bc-seg{display:inline-flex;background:var(--panel);border-radius:8px;border:1px solid #2a2a2a;padding:2px;gap:2px}
.seg-btn{padding:4px 9px;border-radius:6px;background:transparent;border:none;color:var(--muted);font-family:var(--mono);font-size:10px;letter-spacing:.04em;cursor:pointer;transition:all .12s;text-transform:uppercase;}
.seg-btn:hover{color:var(--dim)}
.seg-btn.active{background:#111;color:var(--text)}
#bcChartArea{flex:1;display:flex;min-height:0;position:relative}
.bc-canvas-wrap{flex:1;position:relative;min-height:0;overflow:hidden}
#bcChart{display:block;width:100%;height:100%;cursor:crosshair}
.quad-label{position:absolute;pointer-events:none;font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.1em;padding:3px 8px;border-radius:4px;background:rgba(10,10,12,.6);display:none;opacity:.8}
.quad-label.on{display:block}
#bc-rail{width:0;border-left:1px solid var(--border);background:var(--surface);display:flex;flex-direction:column;overflow:hidden;transition:width .2s cubic-bezier(.2,.8,.2,1);}
#bc-rail.open{width:300px}
#bc-railInner{flex:1;overflow:auto;display:flex;flex-direction:column}
#bc-railInner::-webkit-scrollbar{width:5px}
#bc-railInner::-webkit-scrollbar-thumb{background:#222;border-radius:3px}
.rail-head{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.rail-head h3{font-size:12px;font-weight:600;letter-spacing:.02em}
.rail-head .close{margin-left:auto;background:none;border:none;color:var(--muted);cursor:pointer;font-size:16px;line-height:1}
.rail-head .close:hover{color:var(--text)}
.rail-stats{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);margin:10px;border-radius:8px;overflow:hidden}
.rail-stat{background:var(--panel);padding:8px 10px}
.rail-stat-lbl{font-family:var(--mono);font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px}
.rail-stat-val{font-size:14px;font-weight:600;font-family:var(--mono)}
.rail-section-title{padding:5px 14px;font-family:var(--mono);font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;border-top:1px solid var(--border)}
.rail-list{display:flex;flex-direction:column}
.rail-row{display:grid;grid-template-columns:auto 1fr auto auto;gap:8px;align-items:center;padding:7px 14px;border-top:1px solid var(--border);cursor:pointer;transition:background .1s}
.rail-row:hover{background:var(--panel)}
.rail-row .dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.rail-row .tk{font-family:var(--mono);font-size:11px;font-weight:600}
.rail-row .co{font-size:10px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:80px}
.rail-row .gi{font-family:var(--mono);font-size:10px;font-weight:600}
.rail-row .star{background:none;border:none;color:var(--muted);cursor:pointer;font-size:12px;padding:2px 4px}
.rail-row .star.on{color:#facc15}
.rail-row .star:hover{color:#facc15}
#bc-tip{position:fixed;z-index:2200;background:rgba(8,8,10,.96);backdrop-filter:blur(8px);border:1px solid #2a2a2a;border-radius:10px;padding:0;min-width:240px;max-width:290px;box-shadow:0 20px 60px rgba(0,0,0,.6);pointer-events:none;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s;overflow:hidden;}
#bc-tip.show{opacity:1;transform:translateY(0)}
.tip-head{padding:10px 14px 8px;display:flex;align-items:baseline;gap:8px;border-bottom:1px solid rgba(255,255,255,.04)}
.tip-tk{font-size:15px;font-weight:700;font-family:var(--mono);letter-spacing:.02em}
.tip-co{font-size:10px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0}
.tip-sector{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.06em;padding:2px 5px;border-radius:4px;background:rgba(255,255,255,.04)}
.tip-body{padding:3px 0 8px}
.tip-row{display:flex;justify-content:space-between;align-items:baseline;padding:4px 14px}
.tip-row .lbl{font-family:var(--mono);font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.tip-row .val{font-size:11px;font-weight:600;font-family:var(--mono)}
.tip-spark{height:28px;margin:5px 14px 3px;position:relative}
.tip-spark svg{width:100%;height:100%;display:block}
.tip-arch{margin:6px 14px 8px;padding:5px 8px;border-radius:6px;background:rgba(255,255,255,.03);font-family:var(--mono);font-size:10px;color:var(--dim);display:flex;align-items:center;gap:6px}
.tip-arch .arch-icon{font-size:11px}
.tip-hint{padding:6px 14px;font-family:var(--mono);font-size:9px;color:var(--muted);text-align:center;letter-spacing:.1em;border-top:1px solid rgba(255,255,255,.04);text-transform:uppercase}
.bc-menu{position:fixed;z-index:2500;background:#111;border:1px solid #2a2a2a;border-radius:10px;padding:6px;min-width:210px;box-shadow:0 20px 60px rgba(0,0,0,.6)}
.bc-menu-title{font-family:var(--mono);font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;padding:5px 8px 4px}
.bc-menu-item{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;font-family:var(--sans);font-size:12px;color:var(--text);cursor:pointer;transition:background .1s}
.bc-menu-item:hover{background:var(--panel-2)}
.bc-menu-item.on{background:var(--panel-2)}
.bc-menu-item .check{width:12px;color:#33AA00;font-size:11px;visibility:hidden}
.bc-menu-item.on .check{visibility:visible}
.bc-menu-item .sub{color:var(--muted);font-size:10px;margin-left:auto;font-family:var(--mono)}
.bc-foot{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:7px 14px;border-top:1px solid var(--border);background:var(--surface);font-family:var(--mono);font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.bc-gi-scale{display:inline-flex;align-items:center;border-radius:999px;overflow:hidden;border:1px solid #2a2a2a}
.gi-seg{padding:3px 7px;font-family:var(--mono);font-size:9px;cursor:pointer;transition:opacity .12s}
.gi-seg.dim{opacity:.3}
.gi-seg:hover{opacity:1}
.bc-axis-meta{display:flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.bc-axis-meta b{color:var(--text);font-weight:600;letter-spacing:.02em;text-transform:none;cursor:pointer;border-bottom:1px dashed #2a2a2a;padding-bottom:1px}
.bc-result-count{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--muted)}
.bc-result-count b{color:var(--text)}
.bc-empty{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;font-family:var(--mono);color:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase;pointer-events:none}
.sym-chart-popup.large-chart { width:min(88vw,1500px); }
.sym-chart-popup .tradingview-widget-container,
.sym-chart-popup .tradingview-widget-container__widget {
  width:100%; height:100%;
}
.name-cell { color:var(--dim); max-width:240px; overflow:hidden; text-overflow:ellipsis; }
.label-cell { color:var(--muted); font-size:11px; }
.chg-pos { color:var(--green-bright); }
.chg-neg { color:var(--red-bright); }
.badge,.gi-badge { display:inline-flex; align-items:center; justify-content:center; gap:5px; border-radius:999px; padding:4px 9px; font-size:11px; font-weight:700; line-height:1; font-family:var(--mono); letter-spacing:.01em; }
.b-new,.b-buy { background:rgba(17,150,0,.12); color:var(--green-bright); border:1px solid rgba(51,170,0,.22); }
.b-inc { background:rgba(119,170,0,.12); color:var(--green-soft); border:1px solid rgba(119,170,0,.22); }
.b-dec { background:rgba(221,102,0,.12); color:var(--orange); border:1px solid rgba(221,102,0,.22); }
.b-sold,.b-sell { background:rgba(170,0,0,.12); color:var(--red-bright); border:1px solid rgba(170,0,0,.22); }
.gi-dark-green { background:rgba(17,150,0,.12); color:var(--green-bright); border:1px solid rgba(51,170,0,.22); }
.gi-green { background:rgba(119,170,0,.12); color:var(--green-soft); border:1px solid rgba(119,170,0,.22); }
.gi-yellow { background:rgba(204,153,0,.12); color:var(--amber); border:1px solid rgba(204,153,0,.22); }
.gi-orange { background:rgba(221,102,0,.12); color:var(--orange); border:1px solid rgba(221,102,0,.22); }
.gi-red { background:rgba(170,0,0,.12); color:var(--red-bright); border:1px solid rgba(170,0,0,.22); }
.gi-none { background:rgba(255,255,255,.04); color:var(--muted); border:1px solid var(--border); }
.gi-bar-wrap { width:96px; height:8px; background:#141414; border-radius:999px; overflow:hidden; display:inline-block; vertical-align:middle; }
.gi-bar { height:100%; border-radius:999px; }
.grp-hdr { cursor:pointer; background:rgba(255,255,255,.01); }
.grp-hdr:hover { background:rgba(255,255,255,.04); }
.grp-hdr.open { background:rgba(255,255,255,.06); }
.grp-hdr td.expand-arrow::before { content:'+ '; font-size:9px; color:var(--muted); }
.grp-hdr.open td.expand-arrow::before { content:'- '; }
.grp-child { display:none; background:#000 !important; border-left:2px solid rgba(255,255,255,.10); }
.grp-child td:first-child { padding-left:22px; color:var(--muted); font-size:10px; }
.trade-count { display:inline-block; border-radius:999px; padding:3px 8px; font-size:10px; margin-left:4px; }
.pct-bar { width:60px; height:4px; background:var(--surface2,#1a1a1a); border-radius:2px; margin-top:3px; overflow:hidden; }
.pct-bar-fill { height:100%; border-radius:2px; background:linear-gradient(90deg,#3b82f6,#60a5fa); }
.badge-trades { background:rgba(96,165,250,.12); border:1px solid rgba(96,165,250,.3); color:#60a5fa; }
.badge-insiders { background:rgba(251,191,36,.12); border:1px solid rgba(251,191,36,.3); color:#fbbf24; }
.badge-managers { background:rgba(99,179,237,.12); border:1px solid rgba(99,179,237,.3); color:#63b3ed; }
.pagination { display:flex; align-items:center; justify-content:center; gap:8px; padding:12px 10px 14px; font-family:var(--mono); font-size:11px; }
.pagination button,.th-cat-btn { appearance:none; border:1px solid var(--border); border-radius:9px; background:var(--surface); color:var(--dim); padding:7px 12px; cursor:pointer; font-family:var(--mono); font-size:11px; transition:all .14s ease; }
.pagination button:hover,.th-cat-btn:hover { color:var(--text); border-color:var(--border2); background:#111111; }
.pagination button:disabled { opacity:.35; cursor:default; }
.th-cat-btn.active { color:var(--text); border-color:#232323; background:#111111; box-shadow:inset 0 0 0 1px rgba(255,255,255,.015); }
/* Refresh buttons – blue gradient, subtle opacity */
.th-cat-btn[title*="Reload"],.th-cat-btn[title*="Refresh"],.th-cat-btn[title*="refresh"] {
  background:linear-gradient(135deg,#1a4fa3 0%,#2563eb 60%,#3b82f6 100%);
  border-color:#2563eb; color:#e0eaff; font-weight:600; letter-spacing:.02em;
  opacity:0.5;
}
.th-cat-btn[title*="Reload"]:hover,.th-cat-btn[title*="Refresh"]:hover,.th-cat-btn[title*="refresh"]:hover {
  background:linear-gradient(135deg,#1e5cb8 0%,#3b7fff 60%,#60a5fa 100%);
  border-color:#60a5fa; color:#fff; opacity:0.85;
}
.th-cat-btn[title*="Reload"]:disabled,.th-cat-btn[title*="Refresh"]:disabled {
  background:linear-gradient(135deg,#0f2d5c 0%,#1a3a7a 100%); color:#6b8ec7; border-color:#1a3a7a; opacity:0.35;
}
/* "Updated X ago" timestamp label in controls bars */
.tab-refresh-ts { font-family:var(--mono); font-size:10px; color:var(--muted); white-space:nowrap; margin-left:4px; }
/* Signals tab — ultra-compact table */
#tab-reversals thead th { padding:6px 5px; font-size:9px; letter-spacing:.04em; }
#tab-reversals tbody td { padding:5px 5px; font-size:10px; }
#tab-reversals table { min-width:0; }
.bubble-size-controls { display:inline-flex; align-items:center; gap:4px; flex-wrap:wrap; }
.bubble-size-controls .ctrl-label { margin-right:1px; }
.bubble-size-controls .th-cat-btn { padding:5px 8px; border-radius:8px; }
.page-info { color:var(--muted); }
.chart-title { font-family:var(--sans); font-size:12px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }
.chart-wrap { background:linear-gradient(180deg, rgba(255,255,255,.012), rgba(255,255,255,0)), var(--surface2); border:1px solid var(--border); border-radius:16px; padding:12px; box-shadow:var(--shadow-panel); }
.hover-stat { cursor:help; text-decoration:underline dotted; text-underline-offset:3px; font-weight:600; }
.hover-tip { position:fixed; left:0; top:0; z-index:2000; pointer-events:none; display:none; max-width:min(640px,calc(100vw - 24px)); max-height:min(60vh,400px); overflow:auto; padding:8px 10px; border-radius:10px; border:1px solid var(--border2); background:rgba(8,8,8,.97); box-shadow:0 16px 40px rgba(0,0,0,.58); color:var(--text); font-family:var(--mono); font-size:12px; line-height:1.4; white-space:normal; }
.hover-tip.show { display:block; pointer-events:auto; }
.hover-tip[data-kind="heatmap"] { min-width:272px; max-width:318px; padding:10px 11px; border-radius:12px; border-color:#343434; background:rgba(10,10,10,.985); box-shadow:0 18px 42px rgba(0,0,0,.62); }
.tip-line { margin:0 0 2px 0; white-space:nowrap; }
.tip-date { color:#93a0b3; }
.tip-metric { color:var(--amber); }
.tip-name { color:var(--green-soft); }
.tip-meta { color:#c0c0c0; }
.tip-heatmap { display:flex; flex-direction:column; gap:7px; min-width:258px; }
.tip-hm-ticker { font-family:var(--mono); font-size:15px; font-weight:800; line-height:1; letter-spacing:.04em; color:#f3f4f6; }
.tip-hm-name { font-family:var(--sans); font-size:12px; line-height:1.2; color:rgba(255,255,255,.76); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tip-hm-grid { display:grid; grid-template-columns:minmax(0,.72fr) minmax(0,.90fr) minmax(0,1.20fr) minmax(58px,1.02fr); column-gap:7px; row-gap:3px; align-items:end; }
.tip-hm-k { font-family:var(--mono); font-size:9px; line-height:1; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:rgba(255,255,255,.42); white-space:nowrap; }
.tip-hm-v { font-family:var(--mono); font-size:13px; line-height:1.1; font-weight:800; color:#f3f4f6; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tip-hm-v.muted { color:rgba(255,255,255,.62); }
.tip-hm-k-metric,.tip-hm-v-metric { justify-self:end; text-align:right; min-width:58px; }
.hm-grid {
  --hm-cols: 6;
  --hm-cell: 88px;
  --hm-gap: 4px;
  --hm-pad: 4px;
  display:grid;
  flex:1;
  min-height:0;
  grid-template-columns:repeat(var(--hm-cols), minmax(0, var(--hm-cell)));
  grid-auto-rows:var(--hm-cell);
  justify-content:center;
  align-content:flex-start;
  gap:var(--hm-gap);
  padding:var(--hm-pad);
  overflow:hidden;
}
.hm-cell {
  width:var(--hm-cell);
  height:var(--hm-cell);
  min-width:0;
  max-width:none;
  aspect-ratio:1 / 1;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:clamp(1px, calc(var(--hm-cell) * 0.04), 5px);
  border-radius:0;
  cursor:pointer;
  padding:clamp(2px, calc(var(--hm-cell) * 0.05), 6px);
  border:1px solid rgba(255,255,255,.05);
  transition:border-color .12s ease, transform .12s ease;
}
.hm-cell:hover { border-color:rgba(255,255,255,.26)!important; transform:translateY(-1px); }
.hm-ticker { font-family:var(--mono); font-weight:700; font-size:clamp(9px, calc(var(--hm-cell) * 0.18), 13px); line-height:1; color:rgba(255,255,255,.92); letter-spacing:.03em; text-align:center; }
.hm-name {
  font-family:var(--mono);
  font-size:clamp(7px, calc(var(--hm-cell) * 0.108), 10px);
  line-height:1.08;
  color:rgba(255,255,255,.64);
  text-align:center;
  overflow:hidden;
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  white-space:normal;
  word-break:break-word;
  max-width:100%;
  margin:0;
}
.hm-val { font-family:var(--mono); font-weight:600; font-size:clamp(9px, calc(var(--hm-cell) * 0.135), 12px); line-height:1; color:rgba(255,255,255,.9); text-align:center; }
.hm-grid.hm-tight .hm-cell { border-radius:0; }
.hm-grid.hm-tight .hm-name { -webkit-line-clamp:1; }
.hm-grid.hm-sp500 {
  display:block;
  position:relative;
  flex:1;
  min-height:0;
  padding:4px;
  background:#050505;
  overflow:hidden;
}
.hm-sp-sector {
  position:absolute;
  box-sizing:border-box;
  border:1px solid rgba(255,255,255,.14);
  background:rgba(255,255,255,.02);
  border-radius:0;
  overflow:hidden;
}
.hm-sp-sector-title {
  position:absolute;
  left:5px;
  top:3px;
  right:5px;
  font-family:var(--mono);
  font-size:10px;
  line-height:1.1;
  font-weight:700;
  letter-spacing:.07em;
  text-transform:uppercase;
  color:rgba(255,255,255,.92);
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  pointer-events:none;
}
.hm-sp-sector-body { position:absolute; left:2px; right:2px; top:18px; bottom:2px; }
.hm-sp-cell {
  position:absolute;
  box-sizing:border-box;
  display:flex;
  align-items:center;
  justify-content:center;
  text-align:center;
  border:1px solid rgba(0,0,0,.45);
  cursor:pointer;
  overflow:hidden;
  border-radius:0;
  padding:2px;
  color:#fff;
}
.hm-sp-label {
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:2px;
  width:100%;
  min-width:0;
  pointer-events:none;
  text-shadow:0 1px 2px rgba(0,0,0,.45);
}
.hm-sp-ticker {
  font-family:var(--mono);
  font-weight:700;
  line-height:1;
  letter-spacing:.03em;
  color:rgba(255,255,255,.96);
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  max-width:100%;
}
.hm-sp-ret {
  font-family:var(--mono);
  font-weight:700;
  line-height:1;
  color:rgba(255,255,255,.94);
  white-space:nowrap;
}
.hm-sp-empty {
  display:flex;
  align-items:center;
  justify-content:center;
  height:100%;
  color:var(--muted);
  font-family:var(--mono);
  font-size:12px;
}
.rot-frame-wrap { position:relative; flex:1; min-height:0; background:#000; display:flex; }
.rot-frame { display:block; flex:1; min-width:0; min-height:0; width:100%; height:100%; border:none; background:#000; }
.rot-frame-msg { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:var(--muted); font-family:var(--mono); font-size:12px; pointer-events:none; }
.rot-mode-btn { padding:7px 16px; border-radius:8px; border:1px solid var(--border2); cursor:pointer; font-size:11px; font-weight:600; font-family:var(--mono); letter-spacing:.04em; background:var(--surface); color:var(--muted); transition:all .15s ease; text-transform:uppercase; }
.rot-mode-btn:hover { color:var(--text); border-color:var(--border2); background:#111; }
.rot-mode-btn.active { background:#111111; border-color:#333; color:var(--text); box-shadow:0 0 0 1px rgba(255,255,255,.06), 0 2px 8px rgba(0,0,0,.4); }
@media (max-width: 900px) { .tabs { gap:6px; padding:10px 12px; } .tab-btn { padding:8px 11px; font-size:11px; } .controls,.chart-controls,.hm-controls { padding:10px 12px; gap:8px; } .table-wrap,.chart-section { padding:10px 12px 14px; } table { min-width:920px; } thead th { padding:11px 10px; font-size:10px; } tbody td { padding:10px 10px; font-size:11px; } .rot-frame-wrap { min-height:300px; } }
.ind-menu-btn { appearance:none; background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02)); color:var(--dim); border:1px solid var(--border2); border-radius:9px; padding:6px 12px 6px 10px; min-height:30px; font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:.02em; cursor:pointer; transition:all .15s ease; display:inline-flex; align-items:center; gap:5px; outline:none; }
.ind-menu-btn:hover { color:var(--text); border-color:#3a3a3a; background:linear-gradient(135deg,rgba(255,255,255,.09),rgba(255,255,255,.04)); box-shadow:0 2px 8px rgba(0,0,0,.3); }
.ind-menu-btn.open { color:var(--text); border-color:#3a3a3a; background:linear-gradient(135deg,rgba(255,255,255,.09),rgba(255,255,255,.04)); box-shadow:0 0 0 2px rgba(51,170,0,.15), 0 2px 8px rgba(0,0,0,.3); }
.ind-menu-btn .ind-chevron { font-size:8px; opacity:.6; transition:transform .15s ease; }
.ind-menu-btn.open .ind-chevron { transform:rotate(180deg); }
.ind-dropdown { position:absolute; top:calc(100% + 6px); left:0; min-width:230px; background:#0d0d0d; border:1px solid #252525; border-radius:10px; padding:5px; z-index:1200; box-shadow:0 14px 36px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04); }
.ind-section-label { padding:5px 10px 2px; color:#444; font-family:var(--mono); font-size:9px; text-transform:uppercase; letter-spacing:.1em; font-weight:700; }
.ind-sep { height:1px; background:rgba(255,255,255,.05); margin:3px 4px; }
.bl-ind-item { padding:5px 10px; cursor:pointer; border-radius:5px; font-family:var(--mono); font-size:11px; color:#888; display:flex; align-items:center; gap:0; transition:background .1s ease, color .1s ease; user-select:none; }
.bl-ind-item:hover { background:rgba(255,255,255,.065); color:var(--text); }
.bl-ind-item .ind-chk { width:16px; flex-shrink:0; color:var(--green-bright); font-size:11px; text-align:center; }
.bl-ind-item .ind-label { flex:1; }
.bl-color-swatch { display:inline-block;width:16px;height:16px;border-radius:3px;border:1px solid #444;cursor:pointer;flex-shrink:0;transition:border-color .1s,transform .1s; }
.bl-color-swatch:hover { border-color:#eaeaea;transform:scale(1.18); }
.bl-lb-btn { background:#111;border:1px solid #2a2a2a;border-radius:4px;color:#555;font-family:var(--mono);font-size:9px;font-weight:600;padding:2px 7px;cursor:pointer;letter-spacing:.04em;transition:color .12s,border-color .12s; }
.bl-lb-btn:hover { color:#aaa;border-color:#555; }
.bl-lb-btn.active { color:#60a5fa;border-color:#3b82f6; }
.bl-lb-btn.active.lb-past { color:#f59e0b;border-color:#f59e0b; }
.bl-ind-item .ind-badge { color:#3a3a3a; font-size:9px; font-weight:600; margin-left:4px; transition:color .1s ease; }
.bl-ind-item:hover .ind-badge { color:#555; }
.bl-settings-row { padding:4px 8px; gap:6px; cursor:default; }
.bl-settings-row:hover { background:rgba(255,255,255,.035); color:#9f9f9f; }
.bl-settings-row .ind-label { flex:0 0 auto; min-width:70px; font-size:10px; color:#9f9f9f; }
.bl-settings-row .ctrl-input { width:52px; min-height:24px; padding:3px 6px; border-radius:7px; font-size:10px; }
.bl-settings-row--stack { flex-direction:column; align-items:stretch; gap:4px; }
.bl-settings-row-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.bl-settings-value { color:#9ca3af; font-size:10px; letter-spacing:.01em; font-variant-numeric:tabular-nums; }
.bl-settings-slider { -webkit-appearance:none; appearance:none; width:100%; height:3px; border-radius:999px; background:#2a2a2a; outline:none; cursor:pointer; }
.bl-settings-slider::-webkit-slider-thumb { -webkit-appearance:none; appearance:none; width:10px; height:10px; border-radius:50%; border:1px solid #7a7a7a; background:#d4d4d8; }
.bl-settings-slider::-moz-range-thumb { width:10px; height:10px; border-radius:50%; border:1px solid #7a7a7a; background:#d4d4d8; }
.bl-vc-pill { display:inline-flex;align-items:center;padding:1px 5px;border-radius:3px;border:1px solid #444;background:#1e222d;cursor:pointer;font-size:9px;color:#aaa;user-select:none;line-height:1.4; }
.bl-ticker-search { position:relative; width:88px; flex:0 0 auto; }
.bl-ticker-search .ctrl-input { width:100%; }
.bl-ticker-menu { position:absolute; top:calc(100% + 6px); left:0; min-width:300px; max-width:min(420px,calc(100vw - 28px)); max-height:min(320px,50vh); overflow:auto; display:none; padding:5px; border:1px solid #252525; border-radius:10px; background:#0d0d0d; z-index:1250; box-shadow:0 14px 36px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04); }
.bl-ticker-menu.show { display:block; }
.bl-ticker-item { width:100%; display:flex; align-items:center; gap:10px; border:none; background:transparent; color:var(--text); padding:8px 10px; border-radius:8px; cursor:pointer; text-align:left; font-family:var(--mono); font-size:11px; transition:background .1s ease, box-shadow .1s ease; }
.bl-ticker-item:hover,.bl-ticker-item.active { background:rgba(255,255,255,.07); }
.bl-ticker-item.active { box-shadow:inset 0 0 0 1px rgba(51,170,0,.28); }
.bl-ticker-symbol { width:66px; flex-shrink:0; font-weight:700; color:#f0f0f0; letter-spacing:.03em; }
.bl-ticker-name { flex:1; min-width:0; color:#8a8a8a; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bl-ticker-empty { padding:9px 10px; color:var(--muted); font-family:var(--mono); font-size:11px; }

/* ============================================================
   REFINED OVERRIDES — toggle on body.refined
   Small, targeted polish: tabs, watchlist selector, tf pills.
   ============================================================ */

body.refined {
  --refined-accent: #d4d4d8;
  --refined-border: #1f1f1f;
  --refined-border-strong: #2e2e2e;
}

/* ---- Tabs: cleaner pill row ---- */
body.refined .tabs {
  padding: 8px 12px 7px 22px;
  gap: 2px;
  border-bottom: 1px solid #1b1b1b;
  background: #0a0a0a;
}
body.refined .tab-btn {
  appearance: none;
  background: transparent;
  border: 1px solid transparent;
  color: #8a8a8a;
  border-radius: 6px;
  padding: 7px 12px;
  font-family: var(--sans);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.005em;
  transition: color .12s ease, background .12s ease, border-color .12s ease;
  transform: none !important;
  box-shadow: none !important;
}
body.refined .tab-btn:hover {
  color: #e8e8e8;
  background: #141414;
  border-color: transparent;
}
body.refined .tab-btn.active {
  color: #ffffff;
  background: #171717;
  border-color: #262626;
  font-weight: 600;
}

/* ---- Watchlist selector: clean, understated ---- */
body.refined .watchlist-topbar {
  padding: 8px 12px 8px;
  display: flex !important;
  align-items: flex-start;
  gap: 6px;
}
body.refined .watchlist-controls {
  flex-direction: column;
  gap: 0 !important;
  flex: 1;
  min-width: 0;
  position: relative;
}
body.refined .watchlist-dropdown-wrap {
  position: relative;
}
body.refined .watchlist-dropdown {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 5px 26px 5px 10px;
  min-height: 30px;
  font-size: 14px;
  font-weight: 600;
  color: #f2f2f2;
  letter-spacing: 0.005em;
  transition: background .12s, border-color .12s;
  cursor: pointer;
}
body.refined .watchlist-dropdown:hover {
  background: #161616;
  border-color: #262626;
}
body.refined .watchlist-dropdown:focus {
  background: #161616;
  border-color: #333;
  box-shadow: none;
}
body.refined .watchlist-dropdown-wrap::after {
  display: block;
  content: "";
  position: absolute;
  right: 10px; top: 50%;
  width: 8px; height: 8px;
  border-right: 1.5px solid #777;
  border-bottom: 1.5px solid #777;
  transform: translateY(-75%) rotate(45deg);
  pointer-events: none;
}

/* Gear settings button, sits to the RIGHT of the selector */
body.refined #refinedWlGear {
  flex-shrink: 0;
  width: 30px; height: 30px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: #888;
  display: inline-flex;
  align-items: center; justify-content: center;
  cursor: pointer;
  transition: background .12s, color .12s, border-color .12s;
  padding: 0;
}
body.refined #refinedWlGear:hover {
  color: #fff;
  background: #161616;
  border-color: #262626;
}
body.refined #refinedWlGear.open {
  color: #fff;
  background: #1c1c1c;
  border-color: #333;
}
body.refined #refinedWlGear svg { width: 15px; height: 15px; }

/* Settings menu — float below the gear as a popover */
body.refined .watchlist-settings-menu {
  position: absolute !important;
  right: 10px !important;
  top: 44px !important;
  min-width: 180px;
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 12px 28px rgba(0,0,0,.6);
  padding: 5px;
  margin-top: 0;
  gap: 1px;
  z-index: 300;
}
body.refined .wl-settings-btn {
  padding: 7px 10px !important;
  font-size: 11.5px;
  border-radius: 5px;
  color: #b0b0b0;
}
body.refined .wl-settings-btn:hover {
  background: #1a1a1a;
  color: #fff;
}

/* Watchlist panel edge — slightly softer */
body.refined #watchlistPanel {
  background: #0c0c0c;
  border-left: 1px solid #1b1b1b;
}
body.refined .watchlist-colhead {
  border-bottom: 1px solid #1b1b1b;
  color: #6a6a6a;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
body.refined .watchlist-row {
  border-bottom: 1px solid #141414;
}
body.refined .watchlist-row:hover { background: #141414; }
body.refined .watchlist-row.active {
  background: #181818;
  box-shadow: inset 2px 0 0 #e8e8e8;
}
body.refined .watchlist-symbol {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: #ffffff;
}

/* ---- Timeframe pills (replaces the <select> visually) ---- */
body.refined #blChartPeriod { display: none !important; }
body.refined .ctrl-label-chart-tf { display: none !important; }

.tf-pills {
  display: none;
  align-items: stretch;
  gap: 0;
  border: 1px solid #262626;
  border-radius: 6px;
  overflow: hidden;
  background: #0f0f0f;
  height: 28px;
}
body.refined .tf-pills { display: inline-flex; }

.tf-pill {
  appearance: none;
  border: 0;
  background: transparent;
  color: #888;
  font-family: var(--sans);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.03em;
  padding: 0 10px;
  cursor: pointer;
  transition: color .1s, background .1s;
  border-right: 1px solid #1e1e1e;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
}
.tf-pill:last-child { border-right: 0; }
.tf-pill:hover { color: #e5e5e5; background: #161616; }
.tf-pill.active {
  color: #ffffff;
  background: #1e1e1e;
}

/* Slightly calmer chart-controls separators */
body.refined .chart-controls { padding: 6px 12px; gap: 8px; background: #0a0a0a; border-bottom: 1px solid #1b1b1b; }
body.refined .ctrl-sep { background: #1a1a1a; height: 18px; }
body.refined .ctrl-label { font-size: 10px; letter-spacing: 0.08em; color: #6a6a6a; }

/* Indicators / chart-settings buttons — subtle match to tabs */
body.refined .ind-menu-btn {
  background: transparent;
  border: 1px solid #222;
  color: #b4b4b4;
  font-size: 11.5px;
  font-weight: 500;
  padding: 5px 11px 5px 11px;
  border-radius: 6px;
  box-shadow: none;
}
body.refined .ind-menu-btn:hover {
  background: #141414;
  border-color: #2e2e2e;
  color: #fff;
  box-shadow: none;
}

/* ---- Tweak panel (refined mode toggle) ---- */
#refinedTweaks {
  position: fixed; right: 12px; bottom: 12px; z-index: 9998;
  background: #0f0f0f; border: 1px solid #262626;
  border-radius: 10px;
  padding: 8px;
  display: flex; flex-direction: column; gap: 6px;
  font-family: var(--sans);
  box-shadow: 0 10px 30px rgba(0,0,0,.6);
  display: none;
}
#refinedTweaks.open { display: flex; }
#refinedTweaks .rt-title {
  font-size: 9.5px; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: #6a6a6a;
  padding: 0 4px 4px;
}
#refinedTweaks .rt-opts { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
#refinedTweaks .rt-opt {
  appearance: none;
  background: transparent; border: 1px solid #222;
  color: #a8a8a8;
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 11px; font-weight: 600;
  cursor: pointer;
  transition: all .12s;
}
#refinedTweaks .rt-opt:hover { color: #fff; border-color: #333; }
#refinedTweaks .rt-opt.active {
  background: #1c1c1c; border-color: #3a3a3a; color: #fff;
}
</style>
</head>
<body>
<div id="jsErrorBanner" style="display:none;position:fixed;top:8px;right:8px;z-index:99999;max-width:560px;background:#2a0f12;color:#ffd7dc;border:1px solid #7f1d1d;padding:10px 12px;border-radius:10px;font:12px/1.4 JetBrains Mono,monospace;white-space:pre-wrap;box-shadow:0 10px 30px rgba(0,0,0,.45)"></div>

<div class="topbar" aria-hidden="true" style="display:none">
  <div class="topbar-meta"><em id="updatedAt"></em></div>
</div>

<div class="tabs">
  <button class="tab-btn active"  onclick="switchTab('buylevels',this)">Charts</button>
  <button class="tab-btn"         onclick="switchTab('themes',this)">Themes</button>
  <button class="tab-btn"         onclick="switchTab('rotation',this)">Rotation</button>
  <button class="tab-btn"         onclick="switchTab('heatmap',this)">Heatmap</button>
  <button class="tab-btn"         onclick="switchTab('managers',this)">Managers</button>
  <button class="tab-btn"         onclick="switchTab('insider',this)">Insider Trades</button>
  <button class="tab-btn"         onclick="switchTab('reversals',this)">Signals</button>
  <button class="tab-btn"         onclick="switchTab('bubble',this)">Bubble Chart</button>
  <button class="tab-btn"         onclick="switchTab('zreturns',this)">GI Returns</button>
  <div class="tabs-spacer"></div>
  <button id="watchlistToggleBtn" class="watchlist-toggle-btn" type="button" onclick="toggleWatchlistPanel()"></button>
</div>


<div id="watchlistPanel">
  <div class="watchlist-topbar">
    <div class="watchlist-controls">
      <div class="watchlist-dropdown-wrap">
        <select id="watchlistDropdown" class="watchlist-dropdown"></select>
      </div>
      <div id="wlSettingsMenu" class="watchlist-settings-menu">
        <button type="button" class="wl-settings-btn" onclick="addWatchlist()">+ New Watchlist</button>
        <button type="button" class="wl-settings-btn" onclick="renameWatchlist()">Rename Watchlist</button>
        <button type="button" class="wl-settings-btn" onclick="moveWatchlist(-1)">Move Watchlist Up</button>
        <button type="button" class="wl-settings-btn" onclick="moveWatchlist(1)">Move Watchlist Down</button>
        <button type="button" class="wl-settings-btn danger" onclick="deleteWatchlist()">Delete Watchlist</button>
      </div>
    </div>
  </div>
  <div class="watchlist-colhead">
    <span id="wlHeadSym"  class="wl-sortable-head" onclick="wlToggleSort('alpha')">Symbol</span>
    <span id="wlHeadPrice" class="wl-sortable-head watchlist-head-metric" onclick="wlToggleSort('price')">Last</span>
    <span id="wlHeadPct"  class="wl-sortable-head watchlist-head-metric" onclick="wlToggleSort('pct')">Chg%</span>
    <span></span>
  </div>
  <div class="watchlist-list" id="watchlistList" tabindex="0"></div>
</div>

<div id="mainArea">

<!-- TAB 1: MANAGERS (merged Conviction + Holdings) -->
<div id="tab-managers" class="tab-pane">
<div class="controls">
  <input id="mgrS" class="ctrl-input" placeholder="Ticker or company..." style="width:150px" oninput="mgrFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Manager</span>
  <select id="mgrMgr" class="ctrl-input" onchange="mgrFilter()" style="max-width:160px">
    <option value="">All managers</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Change</span>
  <select id="mgrCh" class="ctrl-input" onchange="mgrFilter()">
    <option value="">All</option><option value="NEW">New</option><option value="INCREASED">Increased</option>
    <option value="DECREASED">Decreased</option><option value="SOLD">Sold</option><option value="UNCHANGED">Unchanged</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">GI</span>
  <select id="mgrGI" class="ctrl-input" onchange="mgrFilter()">
    <option value="">All</option><option value="dark-green">Strong Accum</option><option value="green">Accumulation</option>
    <option value="yellow">Neutral</option><option value="orange">Distribution</option><option value="red">Heavy Dist</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Min Managers</span>
  <input id="mgrMM" class="ctrl-input" type="number" min="1" placeholder="1" style="width:60px" oninput="mgrFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Min Insiders</span>
  <input id="mgrMinIns" class="ctrl-input" type="number" min="0" placeholder="0" style="width:60px" oninput="mgrFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Buy Period</span>
  <select id="mgrIBPeriod" class="ctrl-input" onchange="mgrFilter()">
    <option value="">Any time</option>
    <option value="7">1 week</option>
    <option value="14">2 weeks</option>
    <option value="30">1 month</option>
    <option value="90">3 months</option>
    <option value="180">6 months</option>
    <option value="365">1 year</option>
  </select>
  <div style="flex-basis:100%;height:0"></div>
  <div class="result-count" id="mgrCnt" style="padding:0;align-self:center;margin-right:10px"></div>
  <button class="th-cat-btn" onclick="tabRefresh('managers',this)" title="Reload manager data">↻ Refresh</button>
  <span class="tab-refresh-ts" id="mgrRefreshTs"></span>
</div>
<div class="table-wrap"><div class="table-scroll"><table><thead><tr>
  <th onclick="mgrSort('ticker')" data-col="ticker">Ticker</th>
  <th onclick="mgrSort('company')" data-col="company">Company</th>
  <th onclick="mgrSort('totalVal')" data-col="totalVal" class="sort-desc">Total Held</th>
  <th onclick="mgrSort('managerCount')" data-col="managerCount">Managers</th>
  <th onclick="mgrSort('gi_score')" data-col="gi_score" style="width:110px;text-align:center">GI</th>
  <th onclick="mgrSort('new_count')" data-col="new_count">New</th>
  <th onclick="mgrSort('inc_count')" data-col="inc_count">Increased</th>
  <th onclick="mgrSort('dec_count')" data-col="dec_count">Decreased</th>
  <th onclick="mgrSort('insider_buys')" data-col="insider_buys">Insider Buys</th>
</tr></thead><tbody id="mgrBody"></tbody></table></div></div>
<div class="pagination" id="mgrPag"></div>
</div>

<!-- TAB 2: BUBBLE CHART -->
<div id="tab-bubble" class="tab-pane" style="overflow:hidden;display:flex;flex-direction:column">
<!-- v2 command bar — chips rendered by React via portal into #chipsWrap -->
<div class="bc-cmdbar">
  <div class="bc-search-wrap">
    <span class="bc-search-icon">⌕</span>
    <input id="searchInput" class="bc-search" placeholder="Search ticker or company…" autocomplete="off" spellcheck="false">
  </div>
  <div class="bc-cmd-sep"></div>
  <div id="chipsWrap" style="display:flex;gap:5px;flex-wrap:wrap;align-items:center"></div>
  <div style="flex:1"></div>
  <div class="bc-seg" id="viewModeSeg">
    <button class="seg-btn active" data-mode="default">Default</button>
    <button class="seg-btn" data-mode="sector">By Sector</button>
    <button class="seg-btn" data-mode="density">Heatmap</button>
  </div>
  <button class="th-cat-btn" onclick="tabRefresh('bubble',this)" title="Reload bubble chart data" style="margin-left:6px">↻ Refresh</button>
  <span class="tab-refresh-ts" id="bubbleRefreshTs"></span>
</div>
<!-- axis meta strip -->
<div style="display:flex;align-items:center;gap:14px;padding:6px 14px;border-bottom:1px solid var(--border);background:var(--surface)">
  <div class="bc-axis-meta"><span>Y ↕</span><b id="yAxisLabel">GI Score</b></div>
  <div class="bc-axis-meta"><span>X ↔</span><b id="xAxisLabel">Managers Holding</b></div>
  <div class="bc-axis-meta"><span>⬤ size</span><b id="sizeLabel">Held Value</b></div>
  <div class="bc-result-count"><b id="rcShown">0</b> of <span id="rcTotal">0</span></div>
</div>
<!-- chart + rail -->
<div id="bcChartArea">
  <div class="bc-canvas-wrap">
    <canvas id="chart"></canvas>
    <!-- quadrant labels -->
    <div class="quad-label" id="q-tl" style="top:10px;left:10px"></div>
    <div class="quad-label" id="q-tr" style="top:10px;right:10px"></div>
    <div class="quad-label" id="q-bl" style="bottom:32px;left:10px"></div>
    <div class="quad-label" id="q-br" style="bottom:32px;right:10px"></div>
    <div id="emptyState" class="bc-empty" style="display:none">
      <div>No tickers match current filters</div>
      <div style="font-size:10px">Try loosening constraints</div>
    </div>
  </div>
  <!-- selection rail -->
  <aside id="bc-rail">
    <div id="bc-railInner"></div>
  </aside>
</div>
<!-- legend foot -->
<div class="bc-foot">
  <span style="text-transform:none;letter-spacing:0;color:var(--muted)">GI Tier</span>
  <div class="bc-gi-scale" id="giScale">
    <span class="gi-seg" data-tier="red" style="background:#ef444422;color:#ef4444">Heavy Dist</span>
    <span class="gi-seg" data-tier="orange" style="background:#f9731622;color:#f97316">Dist</span>
    <span class="gi-seg" data-tier="yellow" style="background:#facc1522;color:#facc15">Neutral</span>
    <span class="gi-seg" data-tier="green" style="background:#86efac22;color:#86efac">Accum</span>
    <span class="gi-seg" data-tier="dark-green" style="background:#22c55e22;color:#22c55e">Strong Accum</span>
  </div>
  <span style="margin-left:auto;text-transform:none;letter-spacing:0;font-size:10px;color:#333">scroll=zoom · drag=lasso · ⇧drag=pan · dbl-click=reset</span>
</div>
<!-- tooltip -->
<div id="bc-tip"></div>
<div id="bubbleOverlay" style="display:none;position:absolute;inset:0;align-items:center;justify-content:center;background:rgba(10,10,12,.85);z-index:5"><span id="bubbleOverlayMsg" class="muted" style="font-family:var(--mono);font-size:12px"></span></div>
</div>

<!-- TAB 3: BUY LEVELS -->
<div id="tab-buylevels" class="tab-pane active" style="overflow:hidden">
<div class="chart-controls">
  <input id="blTicker" type="hidden" value="">
  <div id="blTickerSearchWrap" class="bl-ticker-search">
    <input id="blTF" class="ctrl-input" placeholder="" autocomplete="off" spellcheck="false" oninput="blHandleFilterInput()" onfocus="blHandleFilterFocus()" onblur="blHandleFilterBlur()" onkeydown="return blHandleFilterKeydown(event)">
    <div id="blTickerMenu" class="bl-ticker-menu"></div>
  </div>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Chart</span>
  <select id="blChartPeriod" class="ctrl-input" onchange="blChartPeriodChange()">
    <option value="7">1 week</option>
    <option value="14">2 weeks</option>
    <option value="30">1 month</option>
    <option value="90">3 months</option>
    <option value="180">6 months</option>
    <option value="365" selected>1 year</option>
    <option value="730">2 years</option>
    <option value="0">Full</option>
  </select>
  <div class="ctrl-sep"></div>
  <div style="position:relative;display:inline-block">
    <button id="blBtnChartType" class="ind-menu-btn" onclick="blToggleChartTypeMenu(event)">Chart Settings <span class="ind-chevron">&#9660;</span></button>
    <div id="blChartTypeMenu" class="ind-dropdown" style="display:none;min-width:240px">
      <div class="bl-ind-item" onclick="blSetChartType('line')"><span class="ind-chk" id="blChartTypeLineChk"></span><span class="ind-label">Line Chart</span></div>
      <div class="bl-ind-item" onclick="blSetChartType('ohlc')"><span class="ind-chk" id="blChartTypeOhlcChk"></span><span class="ind-label">OHLC</span></div>
      <div class="bl-ind-item" onclick="blSetChartType('hlc')"><span class="ind-chk" id="blChartTypeHlcChk"></span><span class="ind-label">HLC</span></div>
      <div class="bl-ind-item" onclick="blSetChartType('hollow')"><span class="ind-chk" id="blChartTypeHollowChk">&#10003;</span><span class="ind-label">Hollow Candle</span></div>
      <div class="bl-ind-item" onclick="blSetChartType('candle')"><span class="ind-chk" id="blChartTypeCandleChk"></span><span class="ind-label">Candle</span></div>
      <div class="bl-ind-item" onclick="blSetChartType('volcndle')"><span class="ind-chk" id="blChartTypeVolcndleChk"></span><span class="ind-label">Volume Candle</span><span style="display:flex;align-items:center;gap:3px"><span id="blVcFilledToggleWrap" title="Candle style: hollow or filled" onclick="event.stopPropagation();blToggleVcFilled()" class="bl-vc-pill"><span id="blVcFilledToggleLabel">hollow</span></span><span id="blVcGapsToggleWrap" title="Gap style: consistent or variable" onclick="event.stopPropagation();blToggleVcGaps()" class="bl-vc-pill"><span id="blVcGapsToggleLabel">≡ gaps</span></span></span></div>
      <div id="blVcWidthScaleRow" class="bl-ind-item bl-settings-row" onclick="event.stopPropagation()" style="display:none;gap:8px">
        <span class="ind-label" style="min-width:72px;font-size:10px">Width Scale</span>
        <input id="blVcWidthScaleInput" class="bl-settings-slider" style="flex:1" type="range" min="0.25" max="3.00" step="0.05" value="1"
          oninput="blSetVcWidthScale(this.value)" onchange="blSetVcWidthScale(this.value)">
        <span id="blVcWidthScaleValue" class="bl-settings-value" style="min-width:34px;text-align:right">1.00x</span>
      </div>
      <div class="ind-sep"></div>
      <div class="ind-section-label" style="display:flex;align-items:center;justify-content:space-between">
        <span>Colors</span>
        <span style="display:flex;gap:4px;margin-right:4px">
          <span id="blUpColorSwatch" class="bl-color-swatch" style="background:#33AA00" title="Up bar color" onclick="event.stopPropagation();blToggleIndColorPicker('blUpColorPanel','blUpColorCustom',_blUpColor)"></span>
          <span id="blDownColorSwatch" class="bl-color-swatch" style="background:#CC3300" title="Down bar color" onclick="event.stopPropagation();blToggleIndColorPicker('blDownColorPanel','blDownColorCustom',_blDownColor)"></span>
        </span>
      </div>
      <div id="blUpColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Up bar color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetUpColor('#33AA00')" style="background:#33AA00" title="Green"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#22c55e')" style="background:#22c55e" title="Bright green"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#4ade80')" style="background:#4ade80" title="Light green"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetUpColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blUpColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blUpColorCustom" value="#33AA00" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetUpColor(this.value)" onchange="blSetUpColor(this.value)">
      </div>
      <div id="blDownColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Down bar color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetDownColor('#CC3300')" style="background:#CC3300" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#FF4444')" style="background:#FF4444" title="Bright red"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#f87171')" style="background:#f87171" title="Light red"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetDownColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blDownColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blDownColorCustom" value="#CC3300" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetDownColor(this.value)" onchange="blSetDownColor(this.value)">
      </div>
      <div class="bl-ind-item" onclick="blSetChartColorMode('open')"><span class="ind-chk" id="blChartColorOpenChk"></span><span class="ind-label">Color by Opening</span></div>
      <div class="bl-ind-item" onclick="blSetChartColorMode('change')"><span class="ind-chk" id="blChartColorChangeChk"></span><span class="ind-label">Color by Change</span></div>
      <div class="bl-ind-item" onclick="blSetChartColorMode('neutral')" style="flex-wrap:wrap;gap:0">
        <span class="ind-chk" id="blChartColorNeutralChk"></span>
        <span class="ind-label">Single Color</span>
        <span id="blNeutralColorSwatch" class="bl-color-swatch" style="background:#CCCCCC;margin-left:6px" title="Change color" onclick="event.stopPropagation();blToggleColorPicker(event)"></span>
      </div>
      <div id="blColorPickerPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Pick color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px">
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#FF4444')" style="background:#FF4444" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetNeutralColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blNeutralColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blNeutralColorCustom" value="#CCCCCC" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetNeutralColor(this.value)" onchange="blSetNeutralColor(this.value)">
      </div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">Chart Margins</div>
      <div class="bl-ind-item bl-settings-row" onclick="event.stopPropagation()">
        <span class="ind-label">Top %</span>
        <input id="blMarginTopInput" class="ctrl-input" type="number" min="0" max="20" step="1" value="3"
          data-min-ch="3" oninput="blSetMarginTop(this.value)" onchange="blSetMarginTop(this.value)">
      </div>
      <div class="bl-ind-item bl-settings-row" onclick="event.stopPropagation()">
        <span class="ind-label">Bottom %</span>
        <input id="blMarginBotInput" class="ctrl-input" type="number" min="0" max="50" step="1" value="30"
          data-min-ch="3" oninput="blSetMarginBot(this.value)" onchange="blSetMarginBot(this.value)">
      </div>
      <div class="bl-ind-item bl-settings-row" onclick="event.stopPropagation()">
        <span class="ind-label">Right Bars</span>
        <input id="blMarginRightInput" class="ctrl-input" type="number" min="0" max="100" step="1" value="0"
          data-min-ch="3" oninput="blSetMarginRight(this.value)" onchange="blSetMarginRight(this.value)">
      </div>
    </div>
  </div>
  <div class="ctrl-sep"></div>
  <div style="position:relative;display:inline-block">
    <button id="blBtnIndicators" class="ind-menu-btn" onclick="blToggleIndicatorsMenu(event)"><svg width="13" height="13" viewBox="0 0 13 13" fill="none" style="opacity:.7"><rect x="1" y="3" width="11" height="1.4" rx=".7" fill="currentColor"/><rect x="1" y="5.8" width="11" height="1.4" rx=".7" fill="currentColor"/><rect x="1" y="8.6" width="11" height="1.4" rx=".7" fill="currentColor"/></svg> Indicators <span class="ind-chevron">&#9660;</span></button>
    <div id="blIndicatorsMenu" class="ind-dropdown" style="display:none">
      <div class="ind-section-label">Signals</div>
      <div class="bl-ind-item" onclick="blToggleEarnings()"><span class="ind-chk" id="blIndEarningsChk">&#10003;</span><span class="ind-label">Earnings</span></div>
      <div class="bl-ind-item" onclick="blToggleReversals()"><span class="ind-chk" id="blIndReversalsChk">&#10003;</span><span class="ind-label">Signals</span></div>
      <div class="bl-ind-item" onclick="blToggleInsiders()" style="flex-wrap:wrap;gap:0">
        <span class="ind-chk" id="blIndInsidersChk">&#10003;</span>
        <span class="ind-label">Insiders</span>
        <span id="blInsiderDotSwatch" class="bl-color-swatch" style="background:#facc15;margin-left:6px" title="Change dot color" onclick="event.stopPropagation();blToggleInsiderColorPicker(event)"></span>
      </div>
      <div id="blInsiderColorPickerPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Dot color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#FF4444')" style="background:#FF4444" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetInsiderDotColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blInsiderDotColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blInsiderDotColorCustom" value="#facc15" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetInsiderDotColor(this.value)" onchange="blSetInsiderDotColor(this.value)">
      </div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">Overlays</div>
      <div class="bl-ind-item" onclick="blToggleValueChart()" style="flex-wrap:wrap;gap:0">
        <span class="ind-chk" id="blIndVCChk">&#10003;</span>
        <span class="ind-label">Value Chart</span>
        <span id="blVCSwatch" class="bl-color-swatch" style="background:#f97316;margin-left:6px" title="Change color" onclick="event.stopPropagation();blToggleIndColorPicker('blVCColorPanel','blVCColorCustom',_blVCColor)"></span>
      </div>
      <div id="blVCColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Value Chart color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetVCColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#FF4444')" style="background:#FF4444" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetVCColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blVCColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blVCColorCustom" value="#f97316" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetVCColor(this.value)" onchange="blSetVCColor(this.value)">
      </div>
      <div class="bl-ind-item" onclick="blToggleVwap()" style="flex-wrap:wrap;gap:0">
        <span class="ind-chk" id="blIndVwapChk"></span>
        <span class="ind-label">VWAP (20)</span>
        <span id="blVwapSwatch" class="bl-color-swatch" style="background:#facc15;margin-left:6px" title="Change color" onclick="event.stopPropagation();blToggleIndColorPicker('blVwapColorPanel','blVwapColorCustom',_blVwapColor)"></span>
      </div>
      <div id="blVwapColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">VWAP color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetVwapColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#FF4444')" style="background:#FF4444" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetVwapColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blVwapColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blVwapColorCustom" value="#facc15" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetVwapColor(this.value)" onchange="blSetVwapColor(this.value)">
      </div>
      <div class="bl-ind-item" onclick="blToggleMA50()" style="flex-wrap:wrap;gap:0">
        <span class="ind-chk" id="blIndMA50Chk"></span>
        <span class="ind-label">Moving Avg (50)</span>
        <span id="blMA50Swatch" class="bl-color-swatch" style="background:#3b82f6;margin-left:6px" title="Change color" onclick="event.stopPropagation();blToggleIndColorPicker('blMA50ColorPanel','blMA50ColorCustom',_blMA50Color)"></span>
      </div>
      <div id="blMA50ColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Moving Avg (50) color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetMA50Color('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#FF4444')" style="background:#FF4444" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetMA50Color('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blMA50ColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blMA50ColorCustom" value="#3b82f6" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetMA50Color(this.value)" onchange="blSetMA50Color(this.value)">
      </div>
      <div class="bl-ind-item" onclick="blToggleMA200()" style="flex-wrap:wrap;gap:0">
        <span class="ind-chk" id="blIndMA200Chk"></span>
        <span class="ind-label">Moving Avg (200)</span>
        <span id="blMA200Swatch" class="bl-color-swatch" style="background:#ef4444;margin-left:6px" title="Change color" onclick="event.stopPropagation();blToggleIndColorPicker('blMA200ColorPanel','blMA200ColorCustom',_blMA200Color)"></span>
      </div>
      <div id="blMA200ColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Moving Avg (200) color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetMA200Color('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#FF4444')" style="background:#FF4444" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetMA200Color('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blMA200ColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blMA200ColorCustom" value="#ef4444" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetMA200Color(this.value)" onchange="blSetMA200Color(this.value)">
      </div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">Volume</div>
      <div class="bl-ind-item bl-settings-row" onclick="event.stopPropagation()" style="gap:8px">
        <span class="ind-label" style="min-width:72px;font-size:10px">Volume Scale</span>
        <input id="blVolumeScaleInput" class="bl-settings-slider" style="flex:1" type="range" min="0.25" max="2.50" step="0.05" value="1"
          oninput="blSetVolumeScale(this.value)" onchange="blSetVolumeScale(this.value)">
        <span id="blVolumeScaleValue" class="bl-settings-value" style="min-width:34px;text-align:right">1.00x</span>
      </div>
      <div class="ind-section-label" style="display:flex;align-items:center;justify-content:space-between">
        <span>Volume Colors</span>
        <span style="display:flex;gap:4px;margin-right:4px">
          <span id="blVolUpColorSwatch" class="bl-color-swatch" style="background:#33AA00" title="Up volume color" onclick="event.stopPropagation();blToggleIndColorPicker('blVolUpColorPanel','blVolUpColorCustom',_blVolUpColor)"></span>
          <span id="blVolDownColorSwatch" class="bl-color-swatch" style="background:#CC3300" title="Down volume color" onclick="event.stopPropagation();blToggleIndColorPicker('blVolDownColorPanel','blVolDownColorCustom',_blVolDownColor)"></span>
        </span>
      </div>
      <div id="blVolUpColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Up volume color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#33AA00')" style="background:#33AA00" title="Green"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#00CC88')" style="background:#00CC88" title="Teal"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#22c55e')" style="background:#22c55e" title="Bright green"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#4ade80')" style="background:#4ade80" title="Light green"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#FFCC00')" style="background:#FFCC00" title="Gold"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetVolUpColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blVolUpColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blVolUpColorCustom" value="#33AA00" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetVolUpColor(this.value)" onchange="blSetVolUpColor(this.value)">
      </div>
      <div id="blVolDownColorPanel" style="display:none;padding:8px 12px 10px;border-top:1px solid #1e1e1e">
        <div style="color:#555;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">Down volume color</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#CC3300')" style="background:#CC3300" title="Red"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#FF4444')" style="background:#FF4444" title="Bright red"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#f87171')" style="background:#f87171" title="Light red"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#FF6688')" style="background:#FF6688" title="Pink"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#FF8800')" style="background:#FF8800" title="Orange"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#EEAA44')" style="background:#EEAA44" title="Amber"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#AA66FF')" style="background:#AA66FF" title="Purple"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#4466FF')" style="background:#4466FF" title="Indigo"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#00AAFF')" style="background:#00AAFF" title="Blue"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#5599BB')" style="background:#5599BB" title="Steel blue"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#FFFFFF')" style="background:#FFFFFF" title="White"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#CCCCCC')" style="background:#CCCCCC" title="Silver"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#AAAAAA')" style="background:#AAAAAA" title="Grey"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#666666')" style="background:#666666" title="Dark grey"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#99DDFF')" style="background:#99DDFF" title="Sky"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#FF99CC')" style="background:#FF99CC" title="Rose"></span>
          <span class="bl-color-swatch" onclick="blSetVolDownColor('#44DDAA')" style="background:#44DDAA" title="Mint"></span>
          <span class="bl-color-swatch" style="background:linear-gradient(135deg,#ff4444,#ff8800,#ffcc00,#44ddaa,#00aaff,#aa66ff)" title="Custom color" onclick="blTriggerCustomColor('blVolDownColorCustom',this,event)"></span>
        </div>
        <input type="color" id="blVolDownColorCustom" value="#CC3300" style="position:fixed;left:-999px;top:-999px;width:0;height:0;opacity:0;pointer-events:none" oninput="blSetVolDownColor(this.value)" onchange="blSetVolDownColor(this.value)">
      </div>
      <div class="bl-ind-item" onclick="blToggleVSA()"><span class="ind-chk" id="blIndVSAChk"></span><span class="ind-label">VSA Colors</span></div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">Projections</div>
      <div class="bl-ind-item" onclick="blToggleTargetLines()"><span class="ind-chk" id="blIndTargetLinesChk">&#10003;</span><span class="ind-label">Target Lines</span></div>
      <div class="bl-ind-item" onclick="blToggleStopLine()"><span class="ind-chk" id="blIndStopLineChk">&#10003;</span><span class="ind-label">Target/Stop Line</span></div>
      <div class="bl-ind-item" onclick="blToggleLookbackBar()"><span class="ind-chk" id="blIndLookbackBarChk">&#10003;</span><span class="ind-label">Lookback Bar</span></div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">GI Panel</div>
      <div class="bl-ind-item" onclick="blToggleGIReturns()"><span class="ind-chk" id="blIndGIReturnsChk">&#10003;</span><span class="ind-label">Zone Returns</span></div>
      <div class="bl-ind-item" onclick="blToggleGIBacktest()"><span class="ind-chk" id="blIndGIBacktestChk">&#10003;</span><span class="ind-label">Trade Statistics</span></div>
      <div class="bl-ind-item" onclick="blToggleGISizer()"><span class="ind-chk" id="blIndGISizerChk">&#10003;</span><span class="ind-label">Trade Size</span></div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">Display</div>
      <div class="bl-ind-item" onclick="blCycleGIPos()"><span class="ind-chk" id="blIndGIChk">&#10003;</span><span class="ind-label">GI Score</span><span id="blGIBtnLbl" style="font-size:9px;opacity:.5;margin-left:auto">Lower</span></div>
      <div class="bl-ind-item" onclick="blToggleCrosshair()"><span class="ind-chk" id="blIndCrosshairChk">&#10003;</span><span class="ind-label">Crosshair</span></div>
      <div class="bl-ind-item" onclick="blToggleDataTooltip()"><span class="ind-chk" id="blIndTooltipChk"></span><span class="ind-label">Tooltip</span></div>
      <div class="ind-sep"></div>
      <div class="ind-section-label">Layout</div>
      <div class="bl-ind-item" onclick="blToggleProfile()"><span class="ind-chk" id="blIndProfileChk">&#10003;</span><span class="ind-label">Company Info</span></div>
    </div>
  </div>
  <div class="ctrl-sep"></div>
  <span id="blLiveBadge" style="display:none;align-items:center;gap:5px;font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;padding:2px 10px;border-radius:12px;border:1px solid currentColor;opacity:.9;cursor:default;margin-left:auto">
    <span id="blLiveDot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor"></span>
    <span id="blLiveBadgeLabel">Connected</span>
    <span id="blLiveCountdown" style="display:none;color:#ffffff;font-weight:400;letter-spacing:.03em;margin-left:2px"></span>
  </span>
  <div class="ctrl-sep"></div>
  <button class="th-cat-btn" id="blManualRefreshBtn" onclick="tabRefresh('buylevels',this)" title="Refresh chart + watchlist prices">↻ Refresh</button>
  <span class="tab-refresh-ts" id="blRefreshTs"></span>
  <select id="blAutoRefreshSelect" class="ctrl-input" onchange="blSetAutoRefresh(this.value)" title="Auto-refresh interval" style="font-size:11px;padding:4px 6px;min-width:0">
    <option value="0" selected>Off</option>
    <option value="3">3s</option>
    <option value="5">5s</option>
    <option value="10">10s</option>
    <option value="15">15s</option>
    <option value="30">30s</option>
    <option value="60">1m</option>
    <option value="120">2m</option>
    <option value="300">5m</option>
    <option value="600">10m</option>
  </select>
</div>
<div id="blEmpty" style="padding:42px 12px;text-align:center;color:var(--muted);font-family:var(--mono);font-size:11px">
  Enter a ticker above to view the candlestick chart with insider buy levels.
</div>
<div id="blChartSection" class="buy-layout" style="display:none">
  <button id="leftPanelToggleBtn" class="left-panel-toggle-btn" type="button" onclick="toggleLeftPanel()"></button>
  <div class="buy-grid">
    <div id="giSignalPanel" class="side-panel">
      <div id="gisp-content" style="display:none;flex-direction:column;gap:5px;min-height:0">
        <div id="gisp-returns-card" class="panel-card">
          <div id="gisp-unified"></div>
        </div>
        <div id="gisp-fairvalue" class="panel-card gisp-fv-card" style="display:none"></div>
        <div id="gisp-backtest-card" class="panel-card">

          <div id="gisp-backtest"></div>
        </div>
        <div id="gisp-sizer-card" class="panel-card">

          <div class="gisp-sizer-controls">
            <div class="gisp-sizer-duo">
              <label class="gisp-sizer-field">
                <span class="gisp-sizer-label">Account Value</span>
                <input id="gispAcctValue" class="ctrl-input" type="number" min="0" step="1000" value="100000" style="width:100%" data-min-ch="7" data-stepper-layout="vsplit" oninput="gispPositionSizerChanged()" onchange="gispPositionSizerChanged()">
              </label>
              <div class="gisp-sizer-field">
                <span class="gisp-sizer-label">Stop Level</span>
                <div style="position:relative">
                  <input id="gispManualStop" class="ctrl-input" type="number" min="0" step="0.01" placeholder="Auto" style="width:100%;padding-left:14px" data-min-ch="5" data-stepper-layout="vsplit" data-auto-seed="gispGetAutoStopPrice" oninput="gispAtrClearOnManual();gispPositionSizerChanged()" onchange="gispAtrClearOnManual();gispPositionSizerChanged()">
                  <span style="position:absolute;left:5px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:10px;pointer-events:none">$</span>
                </div>
              </div>
            </div>
            <div class="gsz-pill-label"><span>ATR Stop</span></div>
            <div class="gisp-atr-pills">
              <button id="gispAtr05" class="gisp-mode-btn" onclick="gispSetAtrStop(0.5)" title="Stop = Entry - 0.5xATR14">0.5x</button>
              <button id="gispAtr10" class="gisp-mode-btn" onclick="gispSetAtrStop(1.0)" title="Stop = Entry - 1.0xATR14">1.0x</button>
              <button id="gispAtr15" class="gisp-mode-btn" onclick="gispSetAtrStop(1.5)" title="Stop = Entry - 1.5xATR14">1.5x</button>
              <button id="gispAtr20" class="gisp-mode-btn" onclick="gispSetAtrStop(2.0)" title="Stop = Entry - 2.0xATR14">2.0x</button>
              <button id="gispAtr25" class="gisp-mode-btn" onclick="gispSetAtrStop(2.5)" title="Stop = Entry - 2.5xATR14">2.5x</button>
              <button id="gispAtr30" class="gisp-mode-btn" onclick="gispSetAtrStop(3.0)" title="Stop = Entry - 3.0xATR14">3.0x</button>
            </div>
            <div style="display:flex;align-items:stretch;gap:5px">
              <div class="gisp-sizer-field" style="flex:0 0 55%;min-width:0">
                <span class="gisp-sizer-label">Target Level</span>
                <div style="position:relative">
                  <input id="gispManualTarget" class="ctrl-input" type="number" min="0" step="0.01" placeholder="Auto" style="width:100%;padding-left:14px" data-min-ch="5" data-stepper-layout="vsplit" data-auto-seed="gispGetAutoTargetPrice" oninput="gispTargetClearOnManual();gispPositionSizerChanged()" onchange="gispTargetClearOnManual();gispPositionSizerChanged()">
                  <span style="position:absolute;left:5px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:10px;pointer-events:none">$</span>
                </div>
              </div>
              <div style="flex:1;display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-rows:1fr 1fr;gap:2px;align-self:flex-end;background:rgba(255,255,255,.05);border-radius:6px;padding:2px">
                <button id="gispRMult10" class="gisp-mode-btn" onclick="gispSetRMult(1.0)" style="padding:2px 1px;font-size:9px">1.0R</button>
                <button id="gispRMult15" class="gisp-mode-btn" onclick="gispSetRMult(1.5)" style="padding:2px 1px;font-size:9px">1.5R</button>
                <button id="gispRMult20" class="gisp-mode-btn" onclick="gispSetRMult(2.0)" style="padding:2px 1px;font-size:9px">2.0R</button>
                <button id="gispRMult25" class="gisp-mode-btn" onclick="gispSetRMult(2.5)" style="padding:2px 1px;font-size:9px">2.5R</button>
                <button id="gispRMult30" class="gisp-mode-btn" onclick="gispSetRMult(3.0)" style="padding:2px 1px;font-size:9px">3.0R</button>
                <button id="gispRMult35" class="gisp-mode-btn" onclick="gispSetRMult(3.5)" style="padding:2px 1px;font-size:9px">3.5R</button>
              </div>
            </div>
            <div style="display:flex;align-items:stretch;gap:5px">
              <label class="gisp-sizer-field" style="flex:1;min-width:0">
                <span class="gisp-sizer-label">Risk Amount</span>
                <div style="display:flex;align-items:center;gap:2px">
                  <div class="gisp-mode-pills" style="flex-shrink:0;padding:1px">
                    <button id="gispModeFixed" class="gisp-mode-btn active" onclick="gispSetRiskMode('fixed')" style="padding:3px 4px">$</button>
                    <button id="gispModePct" class="gisp-mode-btn" onclick="gispSetRiskMode('pct')" style="padding:3px 4px">%</button>
                  </div>
                  <div id="gispRiskFixedRow" style="flex:1;min-width:0">
                    <input id="gispRiskCash" class="ctrl-input" type="number" min="0" step="100" value="500" style="width:100%" data-min-ch="5" data-stepper-layout="vsplit" oninput="gispPositionSizerChanged()" onchange="gispPositionSizerChanged()">
                  </div>
                  <div id="gispRiskPctRow" style="flex:1;min-width:0;display:none">
                    <input id="gispRiskPct" class="ctrl-input" type="number" min="0" step="0.05" value="0.5" style="width:100%" data-min-ch="4" data-stepper-layout="vsplit" oninput="gispPositionSizerChanged()" onchange="gispPositionSizerChanged()">
                  </div>
                </div>
              </label>
              <label class="gisp-sizer-field" style="flex:0 0 90px">
                <span class="gisp-sizer-label">Max Port %</span>
                <input id="gispMaxRiskPct" class="ctrl-input" type="number" min="0" max="100" step="0.05" value="100" style="width:100%" data-min-ch="5" data-stepper-layout="vsplit" oninput="gispPositionSizerChanged()" onchange="gispPositionSizerChanged()">
              </label>
            </div>
          </div>
          <div id="gispSizerOut"></div>
        </div>
      </div>
      <div id="gisp-empty" style="color:var(--muted);font-size:10px;text-align:center;padding:20px 4px;line-height:1.5">Select a ticker to view chart stats, trade sizing, and GI backtest.</div>
    </div>
    <div class="chart-main">
      <div id="blNoData" style="display:none;padding:20px 8px;text-align:center;color:var(--muted);font-family:var(--mono);font-size:10px"></div>
      <div id="blChartWrap" class="chart-wrap clean" style="flex:1;min-height:0;position:relative">
        <div id="blProfileBadge" style="position:absolute;top:8px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:0;pointer-events:none;z-index:10;white-space:nowrap"></div>
        <canvas id="buyLevelChart"></canvas>
      </div>
      <div id="blLookbackBar" style="display:none;position:absolute;bottom:34px;z-index:200;flex-direction:column;align-items:center;gap:3px;pointer-events:none">
        <span style="color:#444;font-size:8px;font-family:var(--mono);text-transform:uppercase;letter-spacing:.08em;white-space:nowrap;pointer-events:none">Lookback</span>
        <div style="display:flex;gap:3px;pointer-events:auto">
          <button class="bl-lb-btn active" id="blLb0"  onclick="blSetLookback(0)">Now</button>
          <button class="bl-lb-btn"        id="blLb5"  onclick="blSetLookback(5)">5D</button>
          <button class="bl-lb-btn"        id="blLb10" onclick="blSetLookback(10)">10D</button>
          <button class="bl-lb-btn"        id="blLb20" onclick="blSetLookback(20)">20D</button>
          <button class="bl-lb-btn"        id="blLb30" onclick="blSetLookback(30)">30D</button>
          <button class="bl-lb-btn"        id="blLb50" onclick="blSetLookback(50)">50D</button>
        </div>
      </div>
      <div id="blTooltip" style="display:none;position:fixed;z-index:1100;background:rgba(10,10,10,0.97);border:1px solid var(--border2);border-radius:6px;padding:5px 8px;font-family:var(--mono);font-size:11px;color:var(--text);pointer-events:none;line-height:1.45;white-space:nowrap;"></div>
      <div id="blGISection" class="chart-subwrap">
        <canvas id="giHistChart"></canvas>
      </div>
    </div>
  </div>
</div>
</div>

<!-- TAB 6: GI ZONE RETURNS -->
<div id="tab-zreturns" class="tab-pane">
<div class="controls">
  <input id="zrS" class="ctrl-input" placeholder="Ticker or company..." style="width:140px" oninput="zrFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Zone</span>
  <select id="zrZone" class="ctrl-input" onchange="zrFilter()">
    <option value="">All zones</option>
    <option value="buying">Buying (70+)</option>
    <option value="accumulation">Accumulation (60-70)</option>
    <option value="neutral">Neutral (45-60)</option>
    <option value="distribution">Distribution (33-45)</option>
    <option value="selling">Selling (&lt;33)</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Min samples</span>
  <input id="zrMinN" class="ctrl-input" type="number" min="1" value="10" style="width:68px" oninput="zrFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Insiders in last</span>
  <select id="zrIBPeriod" class="ctrl-input" onchange="zrFilter()">
    <option value="">Any time</option>
    <option value="7">1 week</option>
    <option value="14">2 weeks</option>
    <option value="30">30 days</option>
    <option value="90">90 days</option>
    <option value="180">6 months</option>
    <option value="365">1 year</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Sort by</span>
  <select id="zrSortCol" class="ctrl-input" onchange="zrSort()">
    <option value="avg_5d">5d Return</option>
    <option value="avg_10d">10d Return</option>
    <option value="avg_20d">20d Return</option>
    <option value="avg_30d">30d Return</option>
    <option value="avg_50d">50d Return</option>
    <option value="insider_buys">Insider Buys</option>
    <option value="manager_count">Managers</option>
    <option value="gi_score">GI Score</option>
    <option value="n">Samples</option>
  </select>
  <div style="flex-basis:100%;height:0"></div>
  <div class="result-count" id="zrCnt" style="padding:0;align-self:center;margin-right:10px"></div>
  <button class="th-cat-btn" onclick="tabRefresh('zreturns',this)" title="Reload GI returns data">↻ Refresh</button>
  <span class="tab-refresh-ts" id="zrRefreshTs"></span>
</div>
<div class="table-wrap"><div class="table-scroll"><table><thead><tr>
  <th onclick="zrSortBy('ticker')" data-col="ticker">Ticker</th>
  <th onclick="zrSortBy('company')" data-col="company">Company</th>
  <th onclick="zrSortBy('sector')" data-col="sector">Sector</th>
  <th onclick="zrSortBy('insider_buys')" data-col="insider_buys">Insider Buys</th>
  <th onclick="zrSortBy('manager_count')" data-col="manager_count">Managers</th>
  <th onclick="zrSortBy('avg_5d')" data-col="avg_5d">5d %</th>
  <th onclick="zrSortBy('avg_10d')" data-col="avg_10d">10d %</th>
  <th onclick="zrSortBy('avg_20d')" data-col="avg_20d">20d %</th>
  <th onclick="zrSortBy('avg_30d')" data-col="avg_30d">30d %</th>
  <th onclick="zrSortBy('avg_50d')" data-col="avg_50d">50d %</th>
  <th onclick="zrSortBy('n')" data-col="n">n</th>
  <th onclick="zrSortBy('gi_score')" data-col="gi_score" style="width:110px;text-align:center">GI</th>
</tr></thead><tbody id="zrBody"></tbody></table></div></div>
<div class="pagination" id="zrPag"></div>
</div>

<!-- TAB: SIGNALS -->
<div id="tab-reversals" class="tab-pane">
<div class="controls">
  <input id="rvS" class="ctrl-input" placeholder="Filter ticker..." style="width:130px" oninput="rvFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Strategy</span>
  <select id="rvStrategy" class="ctrl-input" onchange="rvFilter()" style="max-width:320px">
    <option value="">All Signals</option>
    <optgroup label="Position Limit">
      <option value="1_">Top 1/day</option>
      <option value="2_">Top 2/day</option>
      <option value="3_">Top 3/day</option>
    </optgroup>
    <optgroup label="Watchlist Overlay">
      <option value="score_90">Score ≥ 90 — High Conviction Overlay (sparse, not core)</option>
    </optgroup>
    <optgroup label="Entry Filter - How Trades Enter">
      <option value="1__mom">Top 1/day + Momentum (open crossed above prior day high)</option>
      <option value="1__vol">Top 1/day + Volume Confirm (entry-day volume > 20-day average)</option>
      <option value="1__giacc">Top 1/day + GI Accelerating (GI rising 2+ consecutive days)</option>
      <option value="1__atrok">Top 1/day + ATR Normal Regime (ATR in normal regime, not extreme)</option>
      <option value="1__conf3">Top 1/day + Confirm Count ≥3 (at least 3 of 6 confirmations active)</option>
      <option value="1__conf2">Top 1/day + Confirm Count ≥2 (at least 2 of 6 confirmations active)</option>
      <option value="1__gitrend">Top 1/day + GI Trend Up (GI trending upward)</option>
      <option value="1__clstr">Top 1/day + Close Strength (prior close in upper half of range)</option>
    </optgroup>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Source</span>
  <select id="rvSource" class="ctrl-input" onchange="rvFilter()">
    <option value="BOTH">Both</option>
    <option value="GI">GI only</option>
    <option value="CUSTOM">Custom only</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Family</span>
  <select id="rvFamily" class="ctrl-input" onchange="rvFilter()">
    <option value="">All</option>
    <option value="reversal">Reversal</option>
    <option value="continuation">Continuation</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Mode</span>
  <select id="rvMode" class="ctrl-input" onchange="rvFilter()">
    <option value="">All</option>
    <option value="gi">GI</option>
    <option value="native_legacy">Native Legacy</option>
    <option value="native_relaxed">Native Relaxed</option>
    <option value="mechanics_continuation">Mech Continuation</option>
    <option value="mechanics_reversal">Mech Reversal</option>
    <option value="gi_style">GI-Style</option>
    <option value="reversal">Reversal</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Target</span>
  <select id="rvTgt" class="ctrl-input" onchange="rvFilter()">
    <option value="">All</option>
    <option value="atr_1">ATR 1:1</option>
    <option value="0.15">+15%</option>
    <option value="0.2">+20%</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">ATR Mult</span>
  <select id="rvAtrM" class="ctrl-input" onchange="rvFilter()">
    <option value="">All</option>
    <option value="0.5">0.5x</option>
    <option value="1">1x</option>
    <option value="1.5">1.5x</option>
  </select>
  <div class="ctrl-sep"></div>
  <label style="display:flex;align-items:center;gap:5px;cursor:pointer;color:var(--muted);font-size:11px">
    <input id="rvToday" type="checkbox" onchange="rvFilter()" style="accent-color:var(--green)"> Today Only
  </label>
  <div style="flex-basis:100%;height:0"></div>
  <div class="result-count" id="rvCnt" style="padding:0;align-self:center;margin-right:10px"></div>
  <button class="th-cat-btn" onclick="ensureSignalsData(true)" title="Reload signals">↻ Refresh</button>
  <span class="tab-refresh-ts" id="rvRefreshTs"></span>
</div>
<div class="table-wrap"><div class="table-scroll"><table><thead><tr>
  <th onclick="rvSortBy('pos_rank')" data-col="pos_rank" style="min-width:44px;text-align:right">Pos #</th>
  <th onclick="rvSortBy('ticker')" data-col="ticker">Ticker</th>
  <th onclick="rvSortBy('signal_source')" data-col="signal_source">Source</th>
  <th onclick="rvSortBy('signal_mode')" data-col="signal_mode">Mode</th>
  <th onclick="rvSortBy('signal_family')" data-col="signal_family">Family</th>
  <th onclick="rvSortBy('score')" data-col="score" style="min-width:120px">Score</th>
  <th onclick="rvSortBy('robust_total')" data-col="robust_total" style="min-width:100px">Robust</th>
  <th onclick="rvSortBy('signal_date')" data-col="signal_date" class="sort-desc">Signal Date</th>
  <th onclick="rvSortBy('days_ago')" data-col="days_ago" style="text-align:right">Days Ago</th>
  <th onclick="rvSortBy('current_gi')" data-col="current_gi">Score Now</th>
  <th onclick="rvSortBy('thresh')" data-col="thresh" style="text-align:right">Threshold</th>
  <th onclick="rvSortBy('avg_atr_pct')" data-col="avg_atr_pct" style="text-align:right">ATR Stop</th>
  <th onclick="rvSortBy('atr_mult')" data-col="atr_mult" style="text-align:right">ATR Mult</th>
  <th onclick="rvSortBy('target')" data-col="target" style="text-align:right">Target</th>
  <th onclick="rvSortBy('hold')" data-col="hold" style="text-align:right">Hold</th>
  <th onclick="rvSortBy('ts_days')" data-col="ts_days" style="text-align:right">Time Stop</th>
  <th onclick="rvSortBy('win_rate')" data-col="win_rate" style="text-align:right">Win %</th>
  <th onclick="rvSortBy('avg_ret')" data-col="avg_ret" style="text-align:right">Avg Ret</th>
  <th onclick="rvSortBy('expected_ret_3d')" data-col="expected_ret_3d" style="text-align:right">Exp 3D</th>
  <th onclick="rvSortBy('expected_ret_5d')" data-col="expected_ret_5d" style="text-align:right">Exp 5D</th>
  <th onclick="rvSortBy('expected_ret_10d')" data-col="expected_ret_10d" style="text-align:right">Exp 10D</th>
  <th onclick="rvSortBy('downside_tail_10d')" data-col="downside_tail_10d" style="text-align:right">Tail 10D</th>
  <th onclick="rvSortBy('expected_r_multiple')" data-col="expected_r_multiple" style="text-align:right">Exp R</th>
  <th onclick="rvSortBy('sharpe')" data-col="sharpe" style="text-align:right">Sharpe</th>
  <th onclick="rvSortBy('n')" data-col="n" style="text-align:right">Trades</th>
</tr></thead><tbody id="rvBody"></tbody></table></div></div>
<div class="pagination" id="rvPag"></div>
</div>

<div id="tab-heatmap" class="tab-pane">
<div class="hm-controls">
  <span class="ctrl-label">View</span>
  <button class="th-cat-btn" id="hmViewMajors" onclick="hmSetView('majors',this)">Majors</button>
  <button class="th-cat-btn" id="hmViewSP500" onclick="hmSetView('sp500',this)">S&amp;P 500</button>
  <button class="th-cat-btn active" id="hmViewThemes" onclick="hmSetView('themes',this)">Themes</button>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Metric</span>
  <button class="th-cat-btn" id="hmMgi" onclick="hmSetMetric('gi',this)">GI Score</button>
  <button class="th-cat-btn active" id="hmM1d" onclick="hmSetMetric('r1d',this)">1D %</button>
  <button class="th-cat-btn" id="hmM1w" onclick="hmSetMetric('r1w',this)">1W %</button>
  <button class="th-cat-btn" id="hmM1m" onclick="hmSetMetric('r1m',this)">1M %</button>
  <button class="th-cat-btn" id="hmM3m" onclick="hmSetMetric('r3m',this)">3M %</button>
  <button class="th-cat-btn" id="hmM6m" onclick="hmSetMetric('r6m',this)">6M %</button>
  <button class="th-cat-btn" id="hmMYtd" onclick="hmSetMetric('rytd',this)">YTD %</button>
  <button class="th-cat-btn" id="hmM1y" onclick="hmSetMetric('r1y',this)">1Y %</button>
  <div id="hmCatWrap" style="display:flex;align-items:center;gap:8px">
    <div class="ctrl-sep"></div>
    <span class="ctrl-label">Theme</span>
    <select id="hmCat" class="ctrl-input" onchange="renderHeatmap()" style="min-width:140px">
      <option value="">All</option>
    </select>
  </div>
  <div class="ctrl-sep"></div>
  <button class="th-cat-btn" id="hmRefreshBtn" onclick="tabRefreshHeatmap(this)" title="Reload heatmap data">↻ Refresh</button>
  <span class="tab-refresh-ts" id="hmRefreshTs"></span>
</div>
<div class="hm-legend-row" id="hmLegend"></div>
<div class="hm-grid" id="hmGrid"></div>
</div>

<!-- TAB: THEMES -->
<div id="tab-themes" class="tab-pane">
<div class="controls" style="padding:3px 10px;gap:4px;flex-wrap:wrap">
  <button class="th-cat-btn active" onclick="thSetCat('',this)">All Themes</button>
  <button class="th-cat-btn" onclick="thSetCat('Broad U.S. Sectors',this)">Broad Sectors</button>
  <button class="th-cat-btn" onclick="thSetCat('U.S. Sub-Sectors',this)">Sub-Sectors</button>
  <button class="th-cat-btn" onclick="thSetCat('Countries &amp; Regions',this)">Countries</button>
  <button class="th-cat-btn" onclick="thSetCat('Commodities',this)">Commodities</button>
  <button class="th-cat-btn" onclick="thSetCat('Bonds &amp; Fixed Income',this)">Bonds</button>
  <button class="th-cat-btn" onclick="thSetCat('Thematic &amp; Innovation',this)">Thematic</button>
  <button class="th-cat-btn" onclick="thSetCat('Crypto &amp; Digital',this)">Crypto</button>
  <button class="th-cat-btn" onclick="thSetCat('Global Sectors',this)">Global Sectors</button>
  <button class="th-cat-btn" onclick="thSetCat('Style &amp; Factor',this)">Style & Factor</button>
  <button class="th-cat-btn" onclick="thSetCat('Alternatives &amp; Macro',this)">Alternatives</button>
</div>
<div class="controls" style="padding:3px 10px;gap:8px">
  <span id="thCnt" style="font-family:var(--mono);font-size:11px;color:var(--muted)"></span>
  <div class="ctrl-sep"></div>
  <button class="th-cat-btn" onclick="tabRefresh('themes',this)" title="Reload themes data">↻ Refresh</button>
  <span class="tab-refresh-ts" id="thRefreshTs"></span>
</div>
<!-- hidden inputs kept for JS compatibility -->
<input id="thS" type="hidden" value="">
<select id="thSortSel" style="display:none"><option value="r1d" selected>1D %</option></select>
<div class="table-wrap"><div class="table-scroll"><table><thead><tr>
  <th onclick="thSort('ticker')" data-col="ticker">Ticker</th>
  <th onclick="thSort('name')" data-col="name">Theme</th>
  <th onclick="thSort('gi')" data-col="gi" style="width:110px;text-align:center">GI Score</th>
  <th onclick="thSort('r1d')" data-col="r1d" class="sort-desc">1D %</th>
  <th onclick="thSort('r2d')" data-col="r2d">2D %</th>
  <th onclick="thSort('r3d')" data-col="r3d">3D %</th>
  <th onclick="thSort('r4d')" data-col="r4d">4D %</th>
  <th onclick="thSort('r1w')" data-col="r1w">1W %</th>
  <th onclick="thSort('r1m')" data-col="r1m">1M %</th>
  <th onclick="thSort('r3m')" data-col="r3m">3M %</th>
  <th onclick="thSort('r6m')" data-col="r6m">6M %</th>
  <th onclick="thSort('rytd')" data-col="rytd">YTD %</th>
  <th onclick="thSort('r1y')" data-col="r1y">1Y %</th>
  <th onclick="thSort('r2y')" data-col="r2y">2Y %</th>
</tr></thead><tbody id="thBody"></tbody></table></div></div>
<div class="pagination" id="thPag"></div>
</div>

<!-- TAB: ROTATION -->
<div id="tab-rotation" class="tab-pane" style="overflow:hidden">
<div class="controls">
  <button class="rot-mode-btn active" id="rotModeSectors2" onclick="rotSetModeOuter('sectors',this)">Sectors</button>
  <button class="rot-mode-btn" id="rotModeCross2" onclick="rotSetModeOuter('crossAsset',this)">Cross-Asset</button>
  <div class="ctrl-sep"></div>
  <button class="th-cat-btn" onclick="tabRefresh('rotation',this)" title="Reload rotation chart">↻ Refresh</button>
  <span class="tab-refresh-ts" id="rotRefreshTs"></span>
</div>
<div style="position:relative;flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden">
  <div class="rot-frame-wrap">
    <iframe id="rotationFrame" class="rot-frame" title="Rotation"></iframe>
    <div id="rotationFrameMsg" class="rot-frame-msg">Loading rotation...</div>
  </div>
</div>
</div>

<!-- (Holdings tab removed — merged into tab-managers) -->
<div id="tab-holdings" class="tab-pane" style="display:none!important">
<div class="controls">
  <span class="ctrl-label">Manager</span>
  <select id="hMgr" class="ctrl-input" onchange="hFilter()" style="max-width:160px">
    <option value="">All managers</option>
    <option value="11 Capital Partners">11 Capital Partners</option>
<option value="12 West Capital">12 West Capital</option>
<option value="9823 Capital">9823 Capital</option>
<option value="Abdiel Capital">Abdiel Capital</option>
<option value="Agave Capital">Agave Capital</option>
<option value="Alta Fox Capital">Alta Fox Capital</option>
<option value="Ananym Capital">Ananym Capital</option>
<option value="Andreas Halvorsen">Andreas Halvorsen</option>
<option value="Anomaly Capital">Anomaly Capital</option>
<option value="Anson Capital">Anson Capital</option>
<option value="Apis Capital">Apis Capital</option>
<option value="Atreides Management">Atreides Management</option>
<option value="Bandera Partners">Bandera Partners</option>
<option value="Bill Ackman">Bill Ackman</option>
<option value="Bill Gates">Bill Gates</option>
<option value="Bill Harnisch">Bill Harnisch</option>
<option value="Bill Miller">Bill Miller</option>
<option value="CAS Investment Partners">CAS Investment Partners</option>
<option value="Cadian Capital">Cadian Capital</option>
<option value="Carl Icahn">Carl Icahn</option>
<option value="Chase Coleman">Chase Coleman</option>
<option value="Chris Davis">Chris Davis</option>
<option value="Christopher Hohn">Christopher Hohn</option>
<option value="Chuck Akre">Chuck Akre</option>
<option value="Conversant Capital">Conversant Capital</option>
<option value="Crosslink Capital">Crosslink Capital</option>
<option value="Dan Loeb">Dan Loeb</option>
<option value="Dan Sundheim">Dan Sundheim</option>
<option value="David Abrams">David Abrams</option>
<option value="David Einhorn">David Einhorn</option>
<option value="David Tepper">David Tepper</option>
<option value="DeepCurrents">DeepCurrents</option>
<option value="EcoR1 Capital">EcoR1 Capital</option>
<option value="Emeth Value Capital">Emeth Value Capital</option>
<option value="Engaged Capital">Engaged Capital</option>
<option value="Engine Capital">Engine Capital</option>
<option value="George Soros">George Soros</option>
<option value="Glenn Greenberg">Glenn Greenberg</option>
<option value="Greenhaven Road">Greenhaven Road</option>
<option value="Greenoaks Capital">Greenoaks Capital</option>
<option value="Harbert Fund Advisors">Harbert Fund Advisors</option>
<option value="Impactive Capital">Impactive Capital</option>
<option value="Israel Englander">Israel Englander</option>
<option value="Jain Global">Jain Global</option>
<option value="Jericho Capital">Jericho Capital</option>
<option value="John Paulson">John Paulson</option>
<option value="Ken Griffin">Ken Griffin</option>
<option value="Kerrisdale Capital">Kerrisdale Capital</option>
<option value="Larry Robbins">Larry Robbins</option>
<option value="Leon Cooperman">Leon Cooperman</option>
<option value="Li Lu">Li Lu</option>
<option value="M28 Capital">M28 Capital</option>
<option value="MIG Capital">MIG Capital</option>
<option value="Mason Hawkins">Mason Hawkins</option>
<option value="Masters Capital">Masters Capital</option>
<option value="Melqart Asset Management">Melqart Asset Management</option>
<option value="NEW Advisory Services">NEW Advisory Services</option>
<option value="NZS Capital">NZS Capital</option>
<option value="Nightview Capital">Nightview Capital</option>
<option value="Nitorum Capital">Nitorum Capital</option>
<option value="North Peak Capital">North Peak Capital</option>
<option value="Octahedron Capital">Octahedron Capital</option>
<option value="Pat Dorsey">Pat Dorsey</option>
<option value="Paul Singer">Paul Singer</option>
<option value="Paul Tudor Jones">Paul Tudor Jones</option>
<option value="Perbak Capital">Perbak Capital</option>
<option value="Philippe Laffont">Philippe Laffont</option>
<option value="Potrero Capital">Potrero Capital</option>
<option value="Praesidium Investment">Praesidium Investment</option>
<option value="Prem Watsa">Prem Watsa</option>
<option value="Q3 Asset Management">Q3 Asset Management</option>
<option value="Rangeley Capital">Rangeley Capital</option>
<option value="Ratan Capital">Ratan Capital</option>
<option value="Ray Dalio">Ray Dalio</option>
<option value="Repertoire Partners">Repertoire Partners</option>
<option value="Roberto Mignone">Roberto Mignone</option>
<option value="Seth Klarman">Seth Klarman</option>
<option value="Shannon River">Shannon River</option>
<option value="Situational Awareness">Situational Awareness</option>
<option value="Slate Path Capital">Slate Path Capital</option>
<option value="Stanley Druckenmiller">Stanley Druckenmiller</option>
<option value="Steve Cohen">Steve Cohen</option>
<option value="Steve Mandel">Steve Mandel</option>
<option value="Strategy Capital">Strategy Capital</option>
<option value="SurgoCap Partners">SurgoCap Partners</option>
<option value="Symmetry Peak">Symmetry Peak</option>
<option value="Tekne Capital">Tekne Capital</option>
<option value="Tenzing Global">Tenzing Global</option>
<option value="Terry Smith">Terry Smith</option>
<option value="Tom Gayner">Tom Gayner</option>
<option value="Voss Capital">Voss Capital</option>
<option value="Warren Buffett">Warren Buffett</option>
<option value="Whale Rock Capital">Whale Rock Capital</option>
<option value="Wolf Hill Capital">Wolf Hill Capital</option>
  </select>
  <div class="ctrl-sep"></div>
  <input id="hS" class="ctrl-input" placeholder="Ticker or company..." style="width:140px" oninput="hFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Change</span>
  <select id="hCh" class="ctrl-input" onchange="hFilter()">
    <option value="">All</option><option value="NEW">New</option><option value="INCREASED">Increased</option>
    <option value="DECREASED">Decreased</option><option value="SOLD">Sold</option><option value="UNCHANGED">Unchanged</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">GI</span>
  <select id="hGI" class="ctrl-input" onchange="hFilter()">
    <option value="">All</option><option value="dark-green">Strong Accum</option><option value="green">Accumulation</option>
    <option value="yellow">Neutral</option><option value="orange">Distribution</option><option value="red">Heavy Dist</option>
  </select>
  <div style="flex-basis:100%;height:0"></div>
  <div class="result-count" id="hCnt" style="padding:0;align-self:center;margin-right:10px"></div>
  <button class="th-cat-btn" onclick="tabRefresh('holdings',this)" title="Reload holdings data">↻ Refresh</button>
  <span class="tab-refresh-ts" id="holdRefreshTs"></span>
</div>
<div class="table-wrap"><div class="table-scroll"><table><thead><tr>
  <th onclick="hSort('ticker')" data-col="ticker">Ticker</th>
  <th onclick="hSort('company')" data-col="company">Company</th>
  <th onclick="hSort('value')" data-col="value" class="sort-desc">Total Value</th>
  <th onclick="hSort('managerCount')" data-col="managerCount">Managers</th>
  <th onclick="hSort('gi_score')" data-col="gi_score" style="width:110px;text-align:center">GI</th>
  <th onclick="hSort('change_type')" data-col="change_type">Change</th>
</tr></thead><tbody id="hBody"></tbody></table></div></div>
<div class="pagination" id="hPag"></div>
</div>

<!-- TAB 5: INSIDER TRADES -->
<div id="tab-insider" class="tab-pane">
<div class="controls">
  <input id="iS" class="ctrl-input" placeholder="Ticker, company, insider..." style="width:150px" oninput="iFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Sort</span>
  <select id="blSortBy" class="ctrl-input" onchange="blSortChange()">
    <option value="amount">$ Amount</option>
    <option value="recent">Most Recent</option>
    <option value="count">Trade Count</option>
    <option value="alpha">A-Z</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Buys Within</span>
  <select id="blLookback" class="ctrl-input" onchange="blLookbackChange()">
    <option value="7">1 week</option>
    <option value="14">2 weeks</option>
    <option value="30" selected>1 month</option>
    <option value="90">3 months</option>
    <option value="180">6 months</option>
    <option value="365">1 year</option>
    <option value="730">2 years</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Title</span>
  <select id="iTit" class="ctrl-input" onchange="iFilter()" style="max-width:180px">
    <option value="">All titles</option>
  </select>
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Min Insiders</span>
  <input id="iMinIns" class="ctrl-input" type="number" min="1" max="20" value="1" style="width:58px" title="Min distinct insiders" oninput="iFilter()">
  <div class="ctrl-sep"></div>
  <span class="ctrl-label">Buy Period</span>
  <select id="iWinDaysSelect" class="ctrl-input" onchange="iWinDaysFromSelect();iFilter()">
    <option value="7">1 week</option>
    <option value="14">2 weeks</option>
    <option value="30" selected>1 month</option>
    <option value="90">3 months</option>
    <option value="180">6 months</option>
    <option value="365">1 year</option>
    <option value="730">2 years</option>
  </select>
  <input id="iWinDays" type="hidden" value="30">
  <div style="flex-basis:100%;height:0"></div>
  <div class="result-count" id="iCnt" style="padding:0;align-self:center;margin-right:10px"></div>
  <button class="th-cat-btn" onclick="tabRefresh('insider',this)" title="Reload insider data">↻ Refresh</button>
  <span class="tab-refresh-ts" id="insRefreshTs"></span>
</div>
<div class="table-wrap"><div class="table-scroll"><table><thead><tr>
  <th onclick="iSort('ticker')" data-col="ticker">Ticker / Insider</th>
  <th onclick="iSort('company')" data-col="company">Company / Title</th>
  <th onclick="iSort('trade_count')" data-col="trade_count">Trades / Shares @ Price</th>
  <th onclick="iSort('total_value')" data-col="total_value">Value</th>
  <th onclick="iSort('gi_score')" data-col="gi_score" style="width:110px;text-align:center">GI</th>
  <th onclick="iSort('filing_date')" data-col="filing_date" class="sort-desc">Date</th>
</tr></thead><tbody id="iBody"></tbody></table></div></div>
<div class="pagination" id="iPag"></div>
</div>

<div id="app-loading-overlay" style="position:fixed;inset:0;z-index:99999;background:#000;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:18px">

  <div id="app-loading-msg" style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#777;min-width:220px;text-align:center">Loading market data...</div>
  <div style="width:220px;height:3px;background:#1a1a1a;border-radius:2px;overflow:hidden">
    <div id="app-loading-bar" style="height:100%;width:0%;background:#4ade80;border-radius:2px;transition:width .25s ease"></div>
  </div>
</div>
<script>
const _JSON_TAG_CACHE={};
function parseJsonTag(id,fallback){
  if(Object.prototype.hasOwnProperty.call(_JSON_TAG_CACHE,id)) return _JSON_TAG_CACHE[id];
  const el=document.getElementById(id);
  if(!el) return fallback;
  try{
    const parsed=JSON.parse(el.textContent||'null');
    _JSON_TAG_CACHE[id]=(parsed==null?fallback:parsed);
    return _JSON_TAG_CACHE[id];
  }catch(err){
    console.error('Failed to parse JSON tag', id, err);
    _JSON_TAG_CACHE[id]=fallback;
    return fallback;
  }
}
const REVERSALS_LIST_LOOKBACK_DAYS = 30;
const BUILD_TS   = 1776045438681;
const ROTATION_FRAME_SRC = '/rotation-frame';
let CONV       = [];
let BUBBLE_SIZE_DATA = {};
let HOLDINGS   = [];
let INSIDERS   = [];
let BUY_META   = {};
let ZR_DATA    = [];
let ZR_ALL     = {};
let THEMES_DATA = [];
let SP500_DATA  = [];
let REVERSALS_DATA = {};
let REVERSALS_LIST_DATA = {};
let REVERSAL_ROWS = [];
let EARNINGS_DATA  = {};
let FAIR_VALUE_DATA = {};
const FAIR_VALUE_PENDING = Object.create(null);
const TAB_INIT = Object.create(null);

// ── Favicon activity dot ──────────────────────────────────────────────────────
// Favicon is served as /tray_icon.png — no canvas generation needed.
// _favFetchStart/_favFetchEnd are no-ops kept so the global fetch wrapper
// continues to compile without errors.
window._favFetchStart = function(){};
window._favFetchEnd   = function(){};

// Wrap fetch globally to auto-track all network activity
(function(){
  const _origFetch = window.fetch;
  window.fetch = function(...args) {
    window._favFetchStart();
    return _origFetch.apply(this, args).finally(() => window._favFetchEnd());
  };
})();
const THEMES_REFRESH_MS = 15 * 60 * 1000;
const TAB_DATA_REFRESH_MS = 15 * 60 * 1000;
const PROFILE_META_REFRESH_MS = 24 * 60 * 60 * 1000;
let _themesLastLoadedAt = 0;
let _themesLastCheckedAt = 0;
let _themesFetchPromise = null;
let _themesServerRefreshing = false;
const THEMES_UPDATING_MIN_MS = 900;
let _themesUpdatingToken = 0;
let _convictionLastLoadedAt = 0;
let _convictionFetchPromise = null;
let _holdingsLastLoadedAt = 0;
let _holdingsFetchPromise = null;
let _buyMetaLastLoadedAt = 0;
let _buyMetaFetchPromise = null;
let _insidersLastLoadedAt = 0;
let _insidersFetchPromise = null;
let _reversalsLastLoadedAt = 0;
let _reversalsFetchPromise = null;
let _sp500LastLoadedAt = 0;
let _sp500LastCheckedAt = 0;
let _sp500FetchPromise = null;
let _bubbleSizeLastLoadedAt = 0;
let _bubbleSizeFetchPromise = null;
const _COUNT_FRESHNESS_IDS = ['cCnt','zrCnt','rvCnt','hCnt','iCnt','thCnt'];
const _AUTO_REFRESH_TIMERS = Object.create(null);
function _parseSourceTs(v){
  const s=String(v||'').trim();
  if(!s) return 0;
  const ts=Date.parse(s);
  return Number.isFinite(ts) ? ts : 0;
}
function _scheduleAutoRefresh(key, fn, delayMs=15000){ /* disabled — no background auto-refresh */ }
function _fmtAgeAgo(ts){
  const n=Number(ts);
  if(!Number.isFinite(n)||n<=0) return '';
  const sec=Math.max(0, Math.floor((Date.now()-n)/1000));
  if(sec<5) return 'just now';
  if(sec<60) return sec+'s';
  const min=Math.floor(sec/60);
  if(min<60) return min+'m';
  const hr=Math.floor(min/60);
  if(hr<24) return hr+'h';
  const day=Math.floor(hr/24);
  return day+'d';
}
function _countTextWithFreshness(baseText,lastTs,updating){
  let out=String(baseText||'');
  const age=_fmtAgeAgo(lastTs);
  if(age) out+=(age==='just now') ? ' | Updated just now' : ` | Updated ${age} ago`;
  if(updating) out+=' | Updating...';
  return out;
}
function _refreshCountEl(el){
  if(!el) return;
  const base=String(el.dataset.baseCount||'');
  const lastTs=Number(el.dataset.lastTs||0);
  const updating=String(el.dataset.updating||'0')==='1';
  if(!base && !lastTs && !updating) return;
  el.textContent=_countTextWithFreshness(base,lastTs,updating);
}
function setCountMeta(elId,baseText,lastTs,updating=false){
  const el=document.getElementById(elId);
  if(!el) return;
  el.dataset.baseCount=String(baseText||'');
  el.dataset.lastTs=String(Number(lastTs||0));
  el.dataset.updating=updating?'1':'0';
  _refreshCountEl(el);
}
function setCountUpdating(elId,updating){
  const el=document.getElementById(elId);
  if(!el) return;
  if(!el.dataset.baseCount) return;
  el.dataset.updating=updating?'1':'0';
  _refreshCountEl(el);
}
function refreshCountFreshness(){
  _COUNT_FRESHNESS_IDS.forEach(id=>_refreshCountEl(document.getElementById(id)));
}
setInterval(refreshCountFreshness, 30000);
function _isTabActive(name){
  return !!document.getElementById('tab-' + name)?.classList.contains('active');
}
// Auto-polling removed — data refreshes only on manual ↻ button press per tab
function refreshActiveTabData(){ /* disabled */ }

// ---- Tray "Refresh All Data" — master sync detection ----
let _lastSeenSyncTs = null;

async function masterRefresh() {
  // Mark all data tabs as updating
  ['conviction','holdings','insider','reversals','zreturns'].forEach(t => _setRefreshBusy(t, true));
  try {
    // Reload ZR_DATA (no ensureZRData fn — loaded at startup only)
    try {
      const [zrResp, zrAllResp] = await Promise.all([
        fetch('/api/zone-returns'),
        fetch('/api/zone-returns-all'),
      ]);
      if (zrResp.ok && zrAllResp.ok) {
        const [zrJson, zrAllJson] = await Promise.all([zrResp.json(), zrAllResp.json()]);
        ZR_DATA.length = 0;
        ZR_DATA.push(...(Array.isArray(zrJson) ? zrJson : []));
        const newAll = (zrAllJson && typeof zrAllJson === 'object') ? zrAllJson : {};
        Object.keys(ZR_ALL).forEach(k => delete ZR_ALL[k]);
        Object.assign(ZR_ALL, newAll);
        ZR_DATA.forEach(r => { if(r&&!r.company) r.company=BL_TICKER_INFO[r.ticker]||''; blRememberTickerCompany(r?.ticker, r?.company); });
      }
    } catch(e) {}

    // Force-reload all other tab data from updated server cache
    CONV.length = 0; HOLDINGS.length = 0; INSIDERS.length = 0;
    await Promise.allSettled([
      ensureConvictionData(true),
      ensureHoldingsData(true),
      ensureInsidersData(true),
      ensureReversalsData(true),
      ensureThemesData(true),
    ]);

    // Stamp all tabs as "just updated" and clear busy state
    ['managers','insider','reversals','zreturns','themes'].forEach(t => _updateRefreshTs(t));

    // Re-render whichever data tab is currently active
    if (_isTabActive('managers'))    { _mgrInitManagerDropdown(); mgrSt.filtered=[...HOLDINGS]; mgrFilter(); }
    else if (_isTabActive('insider'))   { iFilter(); }
    else if (_isTabActive('reversals')) { rvInit(); }
    else if (_isTabActive('zreturns'))  { zrFilter(); }
    else if (_isTabActive('themes'))    { thFilter(); }
  } finally {
    ['managers','insider','reversals','zreturns'].forEach(t => _setRefreshBusy(t, false));
  }
}

function _pollSyncStatus() {
  fetch('/api/sync-status')
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (!data) return;
      const ts = data.completed_at;
      if (_lastSeenSyncTs === null) {
        // First poll — record current state without triggering refresh
        _lastSeenSyncTs = ts || '';
        return;
      }
      if (ts && ts !== _lastSeenSyncTs) {
        _lastSeenSyncTs = ts;
        masterRefresh();
      }
    })
    .catch(() => {});
}
// Poll every 20s; first poll on startup to seed _lastSeenSyncTs
setInterval(_pollSyncStatus, 20000);
setTimeout(_pollSyncStatus, 3000);

// ---- Per-tab last-refresh timestamps ----
const _tabRefreshTs = {};     // tab key → Date
const _tabRefreshBusy = {};   // tab key → bool
// Restore persisted timestamps (survive browser F5)
(function(){
  try {
    const saved = JSON.parse(localStorage.getItem('_tabRefreshTs') || '{}');
    for (const [k, v] of Object.entries(saved)) {
      const d = new Date(v);
      if (!isNaN(d.getTime())) _tabRefreshTs[k] = d;
    }
  } catch(_e) {}
})();
function _tabTsId(tab) {
  const map = {
    'themes':        'thRefreshTs',
    'rotation':      'rotRefreshTs',
    'heatmap-sp500': 'hmRefreshTs',
    'heatmap-themes':'hmRefreshTs',
    'managers':      'mgrRefreshTs',
    'conviction':    'mgrRefreshTs',
    'bubble':        'bubbleRefreshTs',
    'buylevels':     'blRefreshTs',
    'zreturns':      'zrRefreshTs',
    'reversals':     'rvRefreshTs',
    'holdings':      'mgrRefreshTs',
    'insider':       'insRefreshTs',
  };
  return map[tab] || null;
}
function _fmtAgo(date) {
  if (!date) return '';
  const secs = Math.round((Date.now() - date.getTime()) / 1000);
  if (secs < 5) return 'Updated just now';
  if (secs < 60) return `Updated ${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `Updated ${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  return `Updated ${hrs}h ago`;
}
function _renderRefreshTs(tab) {
  const id = _tabTsId(tab);
  if (!id) return;
  const el = document.getElementById(id);
  if (!el) return;
  const date = _tabRefreshTs[tab];
  const busy = _tabRefreshBusy[tab];
  if (!date && !busy) { el.textContent = ''; return; }
  const agoText = date ? _fmtAgo(date) : '';
  el.textContent = busy ? (agoText ? agoText + ' · Updating…' : 'Updating…') : agoText;
}
function _updateRefreshTs(tab, dateOverride) {
  _tabRefreshTs[tab] = dateOverride instanceof Date ? dateOverride : new Date();
  _tabRefreshBusy[tab] = false;
  _renderRefreshTs(tab);
  try {
    const saved = {};
    for (const [k, v] of Object.entries(_tabRefreshTs)) if (v) saved[k] = v.toISOString();
    localStorage.setItem('_tabRefreshTs', JSON.stringify(saved));
  } catch(_e) {}
}
function _setRefreshBusy(tab, busy) {
  _tabRefreshBusy[tab] = !!busy;
  _renderRefreshTs(tab);
}
// Tick every 30s to keep "X ago" current
setInterval(() => {
  for (const tab of Object.keys(_tabRefreshTs)) {
    _renderRefreshTs(tab);
  }
}, 30000);
// Render any timestamps restored from localStorage on page load
setTimeout(() => {
  for (const tab of Object.keys(_tabRefreshTs)) _renderRefreshTs(tab);
}, 0);

async function tabRefresh(tab, btn) {
  if (btn) { btn.disabled = true; btn.textContent = '↻ Loading…'; }
  try {
    if (tab === 'themes') {
      // Don't clear existing data — keep showing it while updating
      _setRefreshBusy('themes', true);
      // Trigger a full server-side rebuild (re-fetches OHLCV for all theme tickers)
      await fetch('/api/themes/rebuild').catch(()=>{});
      // Now fetch the freshly rebuilt data
      await ensureThemesData(true);
      thFilter();
      // _updateRefreshTs is called inside _applyThemesData via sourceUpdatedAt
      _setRefreshBusy('themes', false);
      if (TAB_INIT.heatmap && _isTabActive('heatmap') && _hmView !== 'sp500') { hmPopulateCats(); renderHeatmap(); }
    } else if (tab === 'heatmap-themes') {
      // Themes heatmap is tied to the themes data — rebuild themes then re-render
      _setRefreshBusy('heatmap-themes', true);
      await fetch('/api/themes/rebuild').catch(()=>{});
      await ensureThemesData(true);
      hmPopulateCats(); renderHeatmap();
      _setRefreshBusy('heatmap-themes', false);
      // timestamp is set inside _applyThemesData
    } else if (tab === 'heatmap-sp500') {
      // Force-refresh all SP500 + majors OHLCV then rebuild
      _setRefreshBusy('heatmap-sp500', true);
      await fetch('/api/sp500/rebuild').catch(()=>{});
      await ensureSp500Data(true);
      renderHeatmap();
      // timestamp is set inside _applySp500Data
      _setRefreshBusy('heatmap-sp500', false);
    } else if (tab === 'managers' || tab === 'conviction' || tab === 'holdings') {
      _setRefreshBusy('managers', true);
      await Promise.all([
        fetch('/api/conviction/rebuild').catch(()=>{}),
        fetch('/api/holdings/rebuild').catch(()=>{})
      ]);
      CONV.length = 0; HOLDINGS.length = 0;
      await Promise.all([ensureConvictionData(true), ensureHoldingsData(true)]);
      _mgrInitManagerDropdown();
      mgrSt.filtered=[...HOLDINGS]; mgrFilter();
      _updateRefreshTs('managers');
      _setRefreshBusy('managers', false);
    } else if (tab === 'insider') {
      _setRefreshBusy('insider', true);
      await fetch('/api/insiders/rebuild').catch(()=>{});
      INSIDERS.length = 0;
      await ensureInsidersData(true);
      iFilter();
      _updateRefreshTs('insider');
      _setRefreshBusy('insider', false);
    } else if (tab === 'reversals') {
      _setRefreshBusy('reversals', true);
      await fetch('/api/reversals/rebuild').catch(()=>{});
      await ensureReversalsData(true);
      rvInit();
      _updateRefreshTs('reversals');
      _setRefreshBusy('reversals', false);
    } else if (tab === 'buylevels') {
      _setRefreshBusy('buylevels', true);
      const sym = blCurrentTicker();
      if (sym) { await _bgRefreshOhlcv(sym); renderBuyLevels().catch(()=>{}); }
      await Promise.allSettled((WATCHLISTS[ACTIVE_WATCHLIST]?.items||[]).filter(it=>it.type==='symbol'&&it.sym&&it.sym!==sym).map(it=>_bgRefreshOhlcv(it.sym)));
      renderWatchlist();
      _updateRefreshTs('buylevels');
    } else if (tab === 'bubble') {
      _setRefreshBusy('bubble', true);
      await fetch('/api/bubble/rebuild').catch(()=>{});
      CONV.length = 0; INSIDERS.length = 0;
      await Promise.allSettled([ensureConvictionData(true), ensureInsidersData(true), ensureBubbleSizeData(true)]);
      updateBubbleChartDataset();
      _updateRefreshTs('bubble');
    } else if (tab === 'zreturns') {
      _setRefreshBusy('zreturns', true);
      await fetch('/api/zreturns/rebuild').catch(()=>{});
      zrFilter();
      _updateRefreshTs('zreturns');
    } else if (tab === 'rotation') {
      const rotFrame = document.getElementById('rotationFrame');
      if (rotFrame) {
        _setRefreshBusy('rotation', true);
        await fetch('/api/rotation/rebuild').catch(()=>{});
        rotFrame.src = ROTATION_FRAME_SRC + '?_r=' + Date.now();
        await new Promise(r => setTimeout(r, 600));
        _updateRefreshTs('rotation');
      }
    }
  } catch(e) {
    console.error('tabRefresh error', tab, e);
    // Clear busy state on error so the spinner doesn't get stuck
    _setRefreshBusy(tab, false);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '↻ Refresh'; }
  }
}

// --- Charts auto-refresh timer ---
let _blAutoRefreshTimer = null;
let _blAutoRefreshSecs = 0;

async function _blAutoRefreshTick() {
  const sym = blCurrentTicker();
  if (!sym) return;
  await _bgRefreshOhlcv(sym);
  if (blCurrentTicker() === sym) {
    if (!_blSilentUpdateChart(sym)) renderBuyLevels().catch(() => {});
  }
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  const wlSyms = (wl?.items || []).filter(it => it.type === 'symbol' && it.sym && it.sym !== sym).map(it => it.sym);
  if (wlSyms.length) {
    await Promise.allSettled(wlSyms.map(s => _bgRefreshOhlcv(s)));
    renderWatchlist();
  }
}

function blSetAutoRefresh(val, { save = true, fireNow = true } = {}) {
  _blAutoRefreshSecs = parseInt(val) || 0;
  if (_blAutoRefreshTimer) { clearInterval(_blAutoRefreshTimer); _blAutoRefreshTimer = null; }
  // Sync the dropdown to the new value
  const sel = document.getElementById('blAutoRefreshSelect');
  if (sel && String(sel.value) !== String(_blAutoRefreshSecs)) sel.value = String(_blAutoRefreshSecs);
  if (save) saveBuyLevelsPrefs();
  // Restart live poll at new interval (or stop it if timer is Off)
  blEnsureLivePollTimer();
  if (_blAutoRefreshSecs > 0) {
    // Fire immediately so the user sees it switch right away, then start the interval
    if (fireNow) _blAutoRefreshTick().catch(() => {});
    _blAutoRefreshTimer = setInterval(() => { _blAutoRefreshTick().catch(() => {}); }, _blAutoRefreshSecs * 1000);
  }
}

function tabRefreshHeatmap(btn) {
  tabRefresh(_hmView === 'sp500' ? 'heatmap-sp500' : 'heatmap-themes', btn);
}

// --- Auto-refresh: timed loop removed — chart/watchlist refresh on manual ↻ button press ---
let _autoRefreshBusy = false;
let _autoRefreshStarted = false;

function _parseOhlcvRows(rows){
  return (rows||[]).map(r=>{
    if(Array.isArray(r)) return {t:r[0],o:r[1],h:r[2],l:r[3],c:r[4],v:r.length>5?r[5]:null};
    return {t:r?.t??null,o:r?.o??null,h:r?.h??null,l:r?.l??null,c:r?.c??null,v:r?.v??null};
  }).filter(d=>d.t!=null);
}

async function _bgRefreshOhlcv(sym){
  // Fetch fresh data without blanking existing cache — cache stays visible during fetch
  return fetch('/api/ohlcv/'+encodeURIComponent(sym)+'?refresh=1')
    .then(r=>r.ok?r.json():[])
    .then(rows=>{
      const parsed=_parseOhlcvRows(rows);
      if(parsed.length) CANDLE_DATA[sym]=parsed;
      return parsed;
    })
    .catch(()=>[]);
}

// Patch the last candle in-place after a background OHLCV refresh.
// Returns true  → silently updated, no re-render needed.
// Returns false → caller should fall back to renderBuyLevels().
function _blSilentUpdateChart(sym){
  if(!blChart||!_blRenderedTicker||sym!==_blRenderedTicker) return false;
  const fresh=CANDLE_DATA[sym]||[];
  if(!fresh.length||!_blOhlcv.length) return false;
  // Bar count changed (new candle today) — need full re-render to extend x-axis
  if(fresh.length!==_blOhlcv.length) return false;
  const nw=fresh[fresh.length-1];
  const cur=_blOhlcv[_blOhlcv.length-1];
  // Nothing changed — skip entirely, no chart call needed
  if(nw.o===cur.o&&nw.h===cur.h&&nw.l===cur.l&&nw.c===cur.c&&nw.v===cur.v) return true;
  // Price moved outside current y-axis — re-render so scale adjusts
  try{
    const sy=blChart.scales?.y;
    if(sy&&(Number(nw.h)>sy.max||Number(nw.l)<sy.min)) return false;
  }catch(_e){}
  // Patch _blOhlcv in-place — all custom plugins (wickPlugin, volumePlugin, etc.)
  // read this array directly, so blChart.update('none') will redraw them correctly.
  cur.o=nw.o; cur.h=nw.h; cur.l=nw.l; cur.c=nw.c; cur.v=nw.v;
  // Also patch dataset[1] (close-price line) for line-chart display mode
  try{
    const ds=blChart.data.datasets[1];
    if(ds&&ds.data&&ds.data.length){
      const pt=ds.data[ds.data.length-1];
      if(pt&&typeof pt==='object') pt.y=Number(nw.c);
    }
  }catch(_e){}
  try{blChart.update('none');}catch(_e){}
  return true;
}

async function _autoRefreshTick(){
  if(_autoRefreshBusy) return;
  _autoRefreshBusy = true;
  try {
    // 1. Chart ticker first — await so it renders before we move to watchlist
    const cur = blCurrentTicker();
    if(cur){
      await _bgRefreshOhlcv(cur);
      if(blCurrentTicker()===cur){
        // Prefer a silent in-place patch (no flash); fall back to full re-render
        // only when bar count changed or price escaped the y-axis bounds.
        if(!_blSilentUpdateChart(cur)) renderBuyLevels().catch(()=>{});
      }
    }
    // 2. Watchlist tickers — run concurrently, skip the chart ticker
    const wl = WATCHLISTS[ACTIVE_WATCHLIST];
    const wlSyms = (wl?.items||[])
      .filter(it=>it.type==='symbol'&&it.sym&&it.sym!==cur)
      .map(it=>it.sym);
    if(wlSyms.length){
      await Promise.allSettled(wlSyms.map(sym=>_bgRefreshOhlcv(sym)));
      renderWatchlist();
    }
  } finally {
    _autoRefreshBusy = false;
  }
}

function startAutoRefresh(){
  // Timed loop disabled — chart refreshes only on manual ↻ button press.
  // OHLCV for background watchlist tickers loads on-demand when each ticker is opened.
}

const BL_PROFILE_META = Object.create(null);
const _blProfileMetaFetchedAt = Object.create(null);
const _blProfileMetaFetching = Object.create(null);
const BL_TICKER_INFO = Object.create(null);
const BL_SEARCH_UNIVERSE = {"A":"AGILENT TECHNOLOGIES INC","AA":"ALCOA CORP","AAAU":"Goldman Sachs Physical Gold ETF Shares","AAL":"AMERICAN AIRLS GROUP INC","AAMI":"ACADIAN ASSET MANAGEMENT INC","AAOI":"APPLIED OPTOELECTRONICS INC","AAON":"AAON INC","AAP":"ADVANCE AUTO PARTS INC","AAPL":"APPLE INC","AAPU":"Direxion Daily AAPL Bull 2X Shares","AARD":"Aardvark Therapeutics, Inc.","AAT":"American Assets Trust, Inc.","AAUC":"ALLIED GOLD CORP","AAXJ":"iShares MSCI All Country Asia ex Japan ETF","AB":"AllianceBernstein Holding L.P.","ABAT":"American Battery Technology Company","ABBV":"ABBVIE INC","ABCB":"Ameris Bancorp","ABCL":"Abcellera Biologics Inc - US","ABEO":"ABEONA THERAPEUTICS INC","ABEQ":"Absolute Select Value ETF","ABEV":"Ambev S.A.","ABFL":"Abacus FCF Leaders ETF","ABG":"ASBURY AUTOMOTIVE GROUP INC","ABM":"ABM Industries Incorporated","ABNB":"AIRBNB INC","ABOS":"Acumen Pharmaceuticals, Inc.","ABR":"ARBOR REALTY TRUST INC","ABSI":"Absci Corporation","ABT":"ABBOTT LABS","ABTC":"American Bitcoin Corp.","ABUS":"ARBUTUS BIOPHARMA CORP","ABVX":"ABIVAX SA","ABX":"Abacus Global Management, Inc.","ACA":"ARCOSA INC","ACAD":"ACADIA PHARMACEUTICALS INC","ACB":"Aurora Cannabis Inc.","ACCO":"ACCO BRANDS CORP","ACDC":"ProFrac Holding Corp.","ACEL":"ACCEL ENTERTAINMENT INC","ACES":"ALPS Clean Energy ETF","ACGL":"Arch Capital Group Ltd.","ACH":"Accendra Health, Inc.","ACHC":"ACADIA HEALTHCARE COMPANY IN","ACHR":"ARCHER AVIATION INC","ACHV":"Achieve Life Sciences, Inc.","ACI":"Albertsons Companies, Inc.","ACIC":"American Coastal Insurance Corporation","ACIO":"Aptus Collared Income Opportunity ETF","ACIU":"AC Immune SA","ACIW":"ACI WORLDWIDE INC","ACLC":"American Century Large Cap Equity ETF","ACLS":"AXCELIS TECHNOLOGIES INC","ACLX":"ARCELLX INC","ACM":"AECOM","ACMR":"ACM RESH INC","ACN":"ACCENTURE PLC IRELAND","ACNB":"ACNB Corporation","ACNT":"Ascent Industries Co.","ACOG":"Alpha Cognition Inc.","ACRS":"Aclaris Therapeutics, Inc.","ACT":"Enact Holdings, Inc.","ACTG":"Acacia Research Corporation","ACU":"Acme","ACVA":"ACV AUCTIONS INC","ACWI":"ISHARES TR","ACWV":"iShares MSCI Global Min Vol Factor ETF","ACWX":"iShares MSCI ACWI ex U.S. ETF","AD":"ARRAY DIGITAL INFRASTRUCTURE","ADAM":"Adamas Trust, Inc.","ADBE":"ADOBE INC","ADC":"Agree Realty Corporation","ADCT":"ADC THERAPEUTICS SA","ADEA":"Adeia Inc.","ADI":"ANALOG DEVICES INC","ADM":"ARCHER DANIELS MIDLAND CO","ADMA":"ADMA BIOLOGICS INC","ADNT":"ADIENT PLC","ADP":"Automatic Data Processing, Inc.","ADPT":"ADAPTIVE BIOTECHNOLOGIES COR","ADSK":"AUTODESK INC","ADT":"ADT Inc.","ADTN":"ADTRAN HOLDINGS INC","ADUR":"Aduro Clean Technologies Inc.","ADUS":"Addus HomeCare Corporation","AEBI":"Aebi Schmidt Holding AG","AEE":"AMEREN CORP","AEG":"Aegon Ltd. New York Registry Shares","AEHR":"Aehr Test Systems","AEIS":"Advanced Energy Industries, Inc.","AEM":"AGNICO EAGLE MINES LTD","AEO":"AMERICAN EAGLE OUTFITTERS IN","AEP":"AMERICAN ELEC PWR CO INC","AER":"AERCAP HOLDINGS NV","AERO":"Grupo Aeromexico, S.A.B. de C.V.","AES":"AES CORP","AESI":"ATLAS ENERGY SOLUTIONS INC","AESR":"Anfield U.S. Equity Sector Rotation ETF","AEVA":"AEVA TECHNOLOGIES INC","AEXA":"American Exceptionalism Acquisition Corp. A","AFG":"AMERICAN FINL GROUP INC OHIO","AFIF":"Anfield Universal Fixed Income ETF","AFK":"VanEck Africa Index ETF","AFL":"AFLAC Incorporated","AFLG":"First Trust Active Factor Large Cap ETF","AFMC":"First Trust Active Factor Mid Cap ETF","AFOS":"ARS Focused Opportunity Strategy ETF","AFRM":"AFFIRM HLDGS INC","AFYA":"Afya Limited","AG":"FIRST MAJESTIC SILVER CORP","AGCC":"Agencia Comercial Spirits Ltd","AGCO":"AGCO Corporation","AGEN":"Agenus Inc.","AGG":"iShares Core U.S. Aggregate Bond ETF","AGGH":"Simplify Aggregate Bond ETF","AGGY":"WisdomTree Yield Enhanced U.S. Aggregate Bond Fund","AGI":"ALAMOS GOLD INC NEW","AGIG":"Abundia Global Impact Group Inc.","AGIO":"Agios Pharmaceuticals, Inc.","AGIX":"KraneShares Artificial Intelligence & Technology ETF","AGL":"AGILON HEALTH INC","AGM":"Federal Agricultural Mortgage Corporation","AGNC":"AGNC INVT CORP","AGO":"ASSURED GUARANTY LTD","AGOX":"Adaptive Alpha Opportunities ETF","AGQ":"ProShares Ultra Silver","AGRO":"Adecoagro S.A.","AGX":"ARGAN INC","AGYS":"Agilysys, Inc.","AGZ":"iShares Agency Bond ETF","AHCO":"AdaptHealth Corp.","AHR":"AMERICAN HEALTHCARE REIT INC","AI":"C3 AI INC","AIA":"iShares Asia 50 ETF","AIG":"AMERICAN INTL GROUP INC","AII":"American Integrity Insurance Group, Inc.","AIN":"Albany International Corporation","AIOT":"POWERFLEET INC","AIP":"ARTERIS INC","AIPI":"REX AI Equity Premium Income ETF","AIQ":"Global X Artificial Intelligence & Technology ETF","AIR":"AAR Corp.","AIRJ":"AirJoule Technologies Corporation","AIRO":"AIRO Group Holdings, Inc.","AIRR":"First Trust RBA American Industrial Renaissance ETF","AIRS":"AIRSCULPT TECHNOLOGIES INC","AIS":"VistaShares Artificial Intelligence Supercycle ETF","AISP":"Airship AI Holdings, Inc","AIT":"APPLIED INDL TECHNOLOGIES IN","AIV":"Apartment Investment and Management Company","AIZ":"ASSURANT   INC","AJG":"GALLAGHER ARTHUR J &amp; CO","AKAM":"AKAMAI TECHNOLOGIES INC","AKBA":"Akebia Therapeutics, Inc.","AKR":"Acadia Realty Trust","AKRE":"Akre Focus ETF","AKTS":"Aktis Oncology, Inc.","AL":"AIR LEASE CORP","ALAB":"ASTERA LABS INC","ALAI":"Alger AI Enablers & Adopters ETF","ALB":"ALBEMARLE CORP","ALC":"ALCON AG","ALCO":"Alico, Inc.","ALDX":"Aldeyra Therapeutics, Inc.","ALEC":"Alector, Inc.","ALG":"Alamo Group, Inc.","ALGM":"ALLEGRO   MICROSYSTEMS      INC","ALGN":"ALIGN TECHNOLOGY INC","ALGT":"Allegiant Travel Company","ALH":"Alliance Laundry Holdings Inc.","ALHC":"ALIGNMENT HEALTHCARE INC","ALIT":"ALIGHT INC","ALK":"ALASKA AIR GROUP INC","ALKS":"ALKERMES PLC","ALKT":"ALKAMI TECHNOLOGY INC","ALL":"ALLSTATE CORP","ALLE":"ALLEGION PLC","ALLO":"Allogene Therapeutics, Inc.","ALLT":"ALLOT LTD","ALLW":"SPDR Bridgewater All Weather ETF","ALLY":"ALLY FINL INC","ALM":"Almonty Industries Inc.","ALMS":"Alumis Inc.","ALMU":"AELUMA INC","ALNT":"ALLIENT INC","ALNY":"ALNYLAM PHARMACEUTICALS INC","ALRM":"ALARM COM HLDGS INC","ALRS":"Alerus Financial Corporation","ALSN":"Allison Transmission Holdings, Inc.","ALT":"Altimmune, Inc.","ALTG":"ALTA EQUIPMENT GROUP INC","ALTO":"Alto Ingredients, Inc.","ALTS":"ALT5 SIGMA CORP","ALV":"Autoliv Inc - US","ALVO":"Alvotech","ALX":"ALEXANDERS INC","ALXO":"ALX Oncology Holdings Inc.","AM":"ANTERO MIDSTREAM CORP","AMAL":"Amalgamated Financial Corp.","AMAT":"APPLIED MATLS INC","AMBA":"AMBARELLA INC","AMBP":"Ardagh Metal Packaging S.A.","AMBQ":"AMBIQ MICRO INC","AMC":"AMC Entertainment Holdings, Inc.","AMCR":"AMCOR PLC","AMCX":"AMC NETWORKS INC","AMD":"ADVANCED MICRO DEVICES INC","AMDL":"GraniteShares 2x Long AMD Daily ETF","AMDY":"Yieldmax AMD Option Income Strategy ETF","AME":"AMETEK INC","AMG":"AFFILIATED MANAGERS GROUP IN","AMGN":"AMGEN INC","AMH":"American Homes 4 Rent - Class A","AMJB":"Alerian MLP Index ETN","AMKR":"AMKOR TECHNOLOGY INC","AMLP":"Alerian MLP ETF","AMLX":"Amylyx Pharmaceuticals, Inc.","AMN":"AMN Healthcare Services Inc","AMP":"AMERIPRISE FINL INC","AMPH":"Amphastar Pharmaceuticals, Inc.","AMPL":"AMPLITUDE     INC","AMPX":"AMPRIUS TECHNOLOGIES INC","AMPY":"AMPLIFY ENERGY CORP NEW","AMR":"ALPHA METALLURGICAL RESOUR I","AMRC":"AMERESCO INC","AMRX":"AMNEAL PHARMACEUTICALS INC","AMRZ":"AMRIZE LTD","AMSC":"AMERICAN SUPERCONDUCTOR CORP","AMSF":"AMERISAFE, Inc.","AMT":"AMERICAN TOWER CORP NEW","AMTB":"AMERANT BANCORP INC","AMTM":"AMENTUM HOLDINGS INC","AMWD":"American Woodmark Corporation","AMX":"America Movil, S.A.B. de C.V.","AMZA":"InfraCap MLP ETF","AMZN":"AMAZON COM INC","AMZU":"Direxion Daily AMZN Bull 2X Shares","AMZY":"YieldMax AMZN Option Income Strategy ETF","AN":"Autonation Inc - US","ANAB":"ANAPTYSBIO INC","ANDE":"The Andersons, Inc.","ANDG":"ANDERSEN GROUP INC","ANET":"ARISTA NETWORKS INC","ANF":"ABERCROMBIE &amp; FITCH CO","ANGI":"ANGI Inc., Class A","ANGL":"VanEck Fallen Angel High Yield Bond ETF","ANGO":"ANGIODYNAMICS INC","ANGX":"Angel Studios, Inc.","ANIK":"ANIKA THERAPEUTICS INC","ANIP":"ANI PHARMACEUTICALS INC","ANNX":"Annexon, Inc.","ANPA":"Rich Sparkle Holdings Limited","ANRO":"ALTO NEUROSCIENCE INC","AOA":"iShares Core 80/20 Aggressive Allocation ETF","AOK":"iShares Core 30/70 Conservative Allocation ETF","AOM":"iShares Core 40/60 Moderate Allocation ETF","AON":"AON PLC","AOR":"iShares Core 60/40 Balanced Allocation ETF","AORT":"ARTIVION INC","AOS":"A.O. Smith Corporation","AOSL":"Alpha and Omega Semiconductor Limited","AP":"Ampco-Pittsburgh Corporation","APA":"APA CORPORATION","APAD":"A Paradise Acquisition Corp.","APAM":"Artisan Partners Asset Management Inc.","APCB":"ActivePassive Core Bond ETF","APD":"AIR PRODS &amp; CHEMS INC","APEI":"American Public Education, Inc.","APG":"API GROUP CORP","APGE":"APOGEE THERAPEUTICS INC","APH":"AMPHENOL CORP NEW","APIE":"ActivePassive International Equity ETF","APLD":"APPLIED DIGITAL CORP","APLE":"Apple Hospitality REIT, Inc.","APLS":"APELLIS PHARMACEUTICALS INC","APLY":"YieldMax AAPL Option Income Strategy ETF","APMU":"ActivePassive Intermediate Municipal Bond ETF","APO":"APOLLO GLOBAL MGMT INC","APOG":"APOGEE ENTERPRISES INC","APP":"APPLOVIN CORP","APPF":"<![CDATA[APPFOLIO INC]]>","APPN":"APPIAN CORP","APPS":"DIGITAL TURBINE INC","APPX":"Tradr 2X Long APP Daily ETF","APTV":"APTIV PLC","APUE":"ActivePassive U.S. Equity ETF","AQN":"Algonquin Power & Utilities Corp.","AQST":"AQUESTIVE THERAPEUTICS INC","AR":"ANTERO RESOURCES CORP","ARBE":"Arbe Robotics Ltd.","ARCB":"ARCBEST CORP","ARCC":"ARES CAPITAL CORP","ARCO":"ARCOS DORADOS HOLDINGS INC","ARCT":"Arcturus Therapeutics Holdings Inc.","ARDT":"Ardent Health, Inc.","ARDX":"ARDELYX   INC","ARE":"ALEXANDRIA REAL ESTATE EQ","AREC":"American Resources Corporation","ARES":"ARES MANAGEMENT CORPORATION","ARGT":"Global X MSCI Argentina ETF","ARGX":"ARGENX SE","ARHS":"ARHAUS INC","ARI":"Apollo Commercial Real Estate Finance, Inc","ARIS":"Aris Mining Corporation","ARKB":"ARK 21SHARES BITCOIN ETF","ARKF":"ARK Blockchain & Fintech Innovation ETF","ARKG":"ARK Genomic Revolution ETF","ARKK":"ARK ETF TR","ARKO":"ARKO CORP","ARKQ":"ARK Autonomous Technology & Robotics ETF","ARKW":"ARK Next Generation Internet ETF","ARKX":"ARK Space & Defense Innovation ETF","ARLO":"Arlo Technologies, Inc.","ARM":"ARM HOLDINGS PLC","ARMK":"ARAMARK","ARMP":"Armata Pharmaceuticals, Inc.","AROC":"ARCHROCK   INC","AROW":"Arrow Financial Corporation","ARQ":"Arq, Inc.","ARQQ":"Arqit Quantum Inc.","ARQT":"ARCUTIS BIOTHERAPEUTICS INC","ARR":"ARMOUR Residential REIT, Inc.","ARRY":"ARRAY TECHNOLOGIES INC","ARTNA":"Artesian Resources Corporation","ARTV":"Artiva Biotherapeutics, Inc.","ARTY":"iShares Future AI & Tech ETF","ARVN":"ARVINAS INC","ARW":"Arrow Electronics, Inc.","ARWR":"ARROWHEAD PHARMACEUTICALS IN","ARX":"ACCELERANT HOLDINGS","AS":"AMER SPORTS INC","ASAN":"ASANA INC","ASB":"ASSOCIATED BANC CORP","ASC":"Ardmore Shipping Corporation","ASGN":"ASGN Incorporated","ASH":"ASHLAND INC","ASHR":"Xtrackers Harvest CSI 300 China A-Shares ETF","ASIC":"Ategrity Specialty Insurance Company Holdings","ASIX":"ADVANSIX INC","ASLE":"AerSale Corporation","ASLV":"Allspring Special Large Value ETF","ASM":"Avino Silver & Gold Mines Ltd.","ASMB":"ASSEMBLY BIOSCIENCES INC","ASML":"ASML HOLDING N V","ASND":"ASCENDIS PHARMA A/S","ASO":"Academy Sports and Outdoors, Inc.","ASPI":"ASP Isotopes Inc.","ASPN":"ASPEN AEROGELS INC","ASR":"Grupo Aeroportuario del Sureste, S.A. de C.V.","ASST":"Strive, Inc.","ASTE":"Astec Industries, Inc.","ASTH":"Astrana Health Inc.","ASTL":"Algoma Steel Group Inc.","ASTS":"AST SPACEMOBILE CL A","ASUR":"Asure Software Inc","ASX":"ASE Technology Holding Co., Ltd.","ASYS":"Amtech Systems, Inc.","ATAI":"AtaiBeckley Inc.","ATAT":"ATOUR LIFESTYLE HLDGS LTD","ATEC":"ALPHATEC HLDGS INC","ATEN":"A10 Networks Inc - US","ATEX":"Anterix Inc.","ATHM":"Autohome Inc.","ATI":"ATI Inc.","ATKR":"ATKORE INC","ATLC":"Atlanticus Holdings Corporation","ATLN":"Atlantic International Corp.","ATLO":"Ames National Corporation","ATLX":"Atlas Lithium Corporation","ATMU":"ATMUS FILTRATION TECHNOLOGIE","ATNI":"ATN International, Inc.","ATO":"ATMOS ENERGY CORP","ATOM":"Atomera Incorporated","ATR":"APTARGROUP INC","ATRC":"AtriCure, Inc.","ATRO":"ASTRONICS CORP","ATS":"ATS CORP","AU":"ANGLOGOLD ASHANTI PLC","AUB":"Atlantic Union Bankshares Corporation","AUDC":"AudioCodes Ltd.","AUGO":"AURA MINERALS INC","AUNA":"Auna SA","AUPH":"AURINIA PHARMACEUTICALS INC","AUR":"AURORA INNOVATION INC","AURA":"Aura Biosciences, Inc.","AUSF":"Global X Adaptive U.S. Factor ETF","AVA":"AVISTA CORP","AVAH":"Aveanna Healthcare Holdings Inc.","AVAV":"AEROVIRONMENT INC","AVB":"AvalonBay Communities Inc","AVBC":"Avidia Bancorp, Inc.","AVBH":"Avidbank Holdings, Inc.","AVBP":"ARRIVENT BIOPHARMA INC","AVD":"American Vanguard Corporation","AVDE":"Avantis International Equity ETF","AVDS":"Avantis International Small Cap Equity ETF","AVDV":"Avantis International Small Cap Value ETF","AVEE":"Avantis Emerging Markets Small Cap Equity ETF","AVEM":"Avantis Emerging Markets Equity ETF","AVES":"Avantis Emerging Markets Value ETF","AVGE":"AMERICAN CENTY ETF TR","AVGO":"BROADCOM INC","AVGV":"Avantis All Equity Markets Value ETF","AVGX":"Defiance Daily Target 2X Long AVGO ETF","AVIG":"Avantis Core Fixed Income ETF","AVIR":"ATEA PHARMACEUTICALS INC","AVIV":"Avantis International Large Cap Value ETF","AVL":"Direxion Daily AVGO Bull 2X Shares","AVLC":"Avantis U.S. Large Cap Equity ETF","AVLV":"Avantis U.S. Large Cap Value ETF","AVMC":"Avantis U.S. Mid Cap Equity ETF","AVMV":"Avantis U.S. Mid Cap Value ETF","AVNM":"Avantis All International Markets Equity ETF","AVNS":"Avanos Medical, Inc.","AVNT":"AVIENT   CORPORATION","AVNW":"Aviat Networks, Inc.","AVO":"Mission Produce, Inc.","AVPT":"AVEPOINT INC","AVR":"Anteris Technologies Global Corp.","AVRE":"Avantis Real Estate ETF","AVSC":"Avantis U.S Small Cap Equity ETF","AVSD":"Avantis Responsible International Equity ETF","AVSE":"Avantis Responsible Emerging Markets Equity ETF","AVSF":"Avantis Short-Term Fixed Income ETF","AVSU":"Avantis Responsible U.S. Equity ETF","AVT":"AVNET INC","AVTR":"AVANTOR INC","AVTX":"AVALO THERAPEUTICS INC","AVUS":"Avantis U.S. Equity ETF","AVUV":"Avantis U.S. Small Cap Value ETF","AVXC":"Avantis Emerging Markets ex-China Equity ETF","AVXL":"ANAVEX LIFE SCIENCES CORP","AVY":"AVERY DENNISON CORP","AWI":"ARMSTRONG WORLD INDS INC NEW","AWK":"American Water Works Company, Inc.","AWR":"American States Water Company","AX":"Axos Financial, Inc.","AXG":"Solowin Holdings","AXGN":"AXOGEN   INC","AXIA":"AXIA Energia","AXON":"AXON ENTERPRISE INC","AXP":"AMERICAN EXPRESS CO","AXS":"Axis Capital Holdings Limited","AXSM":"AXSOME THERAPEUTICS INC","AXTA":"Axalta Coating Systems Ltd.","AXTI":"AXT INC","AYI":"ACUITY INC","AZ":"A2Z Cust2Mate Solutions Corp.","AZN":"ASTRAZENECA     PLC","AZO":"AUTOZONE INC","AZTA":"AZENTA  INC","AZZ":"AZZ Inc.","B":"BARRICK MINING CORP","BA":"BOEING CO","BAB":"Invesco Taxable Municipal Bond ETF","BABA":"ALIBABA GROUP HLDG LTD","BABX":"GraniteShares 2x Long BABA Daily ETF","BAC":"BANK AMERICA CORP","BACC":"Blue Acquisition Corp.","BACQ":"Inflection Point Acquisition Corp. IV","BAER":"Bridger Aerospace Group Holdings, Inc.","BAFE":"Brown Advisory Flexible Equity ETF","BAH":"BOOZ ALLEN HAMILTON HLDG COR","BAI":"iShares A.I. Innovation and Tech Active ETF","BAK":"Braskem SA","BALI":"iShares U.S. Large Cap Premium Income Active ETF","BALL":"BALL CORP","BALT":"Innovator Defined Wealth Shield ETF","BALY":"Bally's Corporation","BAM":"Brookfield Asset Management Inc","BAMD":"Brookstone Dividend Stock ETF","BAMG":"Brookstone Growth Stock ETF","BANC":"BANC   OF  CALIFORNIA       INC","BAND":"BANDWIDTH INC","BANF":"BancFirst Corporation","BANR":"Banner Corporation","BAP":"CREDICORP LTD","BAR":"GraniteShares Gold Trust Shares of Beneficial Interest","BARK":"BARK INC","BASG":"Brown Advisory Sustainable Growth ETF","BATRA":"Atlanta Braves Holdings, Inc. - Series A","BATRK":"Atlanta Braves Holdings, Inc. - Series C","BATT":"Amplify Lithium & Battery Technology ETF","BAX":"Baxter International Inc.","BB":"BlackBerry Limited","BBAG":"JPMorgan BetaBuilders U.S. Aggregate Bond ETF","BBAI":"BIGBEAR AI HLDGS INC","BBAR":"Banco BBVA Argentina S.A.","BBAX":"JPMorgan BetaBuilders Developed Asia Pacific-ex Japan ETF","BBBI":"BondBloxx BBB Rated 5-10 Year Corporate Bond ETF","BBBS":"BondBloxx BBB Rated 1-5 Year Corporate Bond ETF","BBBY":"Bed Bath & Beyond, Inc.","BBCA":"JPMorgan BetaBuilders Canada ETF","BBCP":"Concrete Pumping Holdings, Inc.","BBCQ":"Bleichroeder Acquisition Corp. II","BBD":"Banco Bradesco Sa","BBDC":"Barings BDC, Inc.","BBEM":"JPMorgan BetaBuilders Emerging Markets Equity ETF","BBEU":"JPMorgan BetaBuilders Europe ETF","BBH":"VanEck Biotech ETF","BBHY":"JPMorgan BetaBuilders USD High Yield Corporate Bond ETF","BBIN":"JPMorgan BetaBuilders International Equity ETF","BBIO":"BRIDGEBIO PHARMA INC","BBJP":"JPMorgan BetaBuilders Japan ETF","BBLU":"EA Bridgeway Blue Chip ETF","BBMC":"JPMorgan BetaBuilders U.S. Mid Cap Equity ETF","BBNX":"BETA BIONICS INC","BBOT":"BridgeBio Oncology Therapeutics, Inc.","BBRE":"JPMorgan BetaBuilders MSCI U.S. REIT ETF","BBSC":"JPMorgan BetaBuilders U.S. Small Cap Equity ETF","BBSI":"Barrett Business Services, Inc.","BBT":"BEACON FINANCIAL CORP.","BBU":"Brookfield Business Partners L.P. Limited Partnership","BBUC":"Brookfield Business Corporation","BBUS":"JPMorgan BetaBuilders U.S. Equity ETF","BBVA":"Banco Bilbao Vizcaya Argentaria S.A.","BBW":"BUILD-A-BEAR WORKSHOP INC","BBWI":"BATH &amp; BODY WORKS INC","BBY":"BEST BUY INC","BC":"BRUNSWICK CORP","BCAL":"California BanCorp","BCAR":"D. Boral ARC Acquisition I Corp.","BCAX":"Bicara Therapeutics Inc.","BCBP":"BCB Bancorp, Inc. (NJ)","BCC":"Boise Cascade, L.L.C.","BCD":"abrdn Bloomberg All Commodity Longer Dated Strategy K-1 Free ETF","BCE":"BCE INC","BCH":"Banco De Chile","BCHP":"Principal Focused Blue Chip ETF","BCI":"abrdn Bloomberg All Commodity Strategy K-1 Free ETF","BCIC":"BCP Investment Corporation","BCML":"BayCom Corp","BCO":"BRINKS CO","BCPC":"BALCHEM CORP","BCPL":"BNY Mellon Core Plus ETF","BCRX":"BIOCRYST PHARMACEUTICALS INC","BCS":"BARCLAYS PLC","BCSF":"Bain Capital Specialty Finance, Inc.","BCTK":"Baron Technology ETF","BDBT":"Bluemonte Core Bond ETF","BDC":"Belden Inc","BDSX":"Biodesix, Inc.","BDTX":"Black Diamond Therapeutics, Inc.","BDVL":"iShares Disciplined Volatility Equity Active ETF","BDX":"Becton, Dickinson and Company","BDYN":"iShares Dynamic Equity Active ETF","BE":"BLOOM ENERGY CORP","BEAG":"Bold Eagle Acquisition Corp.","BEAM":"Beam Therapeutics Inc.","BEBE":"TGE Value Creative Solutions Corp","BEDY":"BNY Mellon Enhanced Dividend and Income ETF","BEKE":"KE Holdings Inc","BELFA":"BEL FUSE INC","BELFB":"Bel Fuse Inc.","BEN":"FRANKLIN RESOURCES INC","BENJ":"Horizon Landmark ETF","BEP":"Brookfield Renewable Partners L.P. Limited Partnership","BEPC":"BROOKFIELD RENEWABLE CORP","BETA":"BETA TECHNOLOGIES INC","BETR":"Better Home & Finance Holding Company","BFAM":"BRIGHT HORIZONS FAM SOL IN D","BFC":"BANK FIRST CORP","BFEB":"Innovator U.S. Equity Buffer ETF - February","BFH":"BREAD FINANCIAL HOLDINGS INC","BFLY":"BUTTERFLY NETWORK INC","BFRZ":"Innovator Equity Managed 100 Buffer ETF","BFS":"Saul Centers, Inc.","BFST":"Business First Bancshares, Inc.","BG":"Bunge Limited","BGC":"BGC GROUP INC","BGIG":"Bahl & Gaynor Income Growth ETF","BGRN":"iShares USD Green Bond ETF","BGS":"B&G Foods, Inc.","BGSI":"Boyd Group Services Inc.","BH":"Biglari Holdings Inc.","BHB":"Bar Harbor Bankshares, Inc.","BHC":"BAUSCH HEALTH COS INC","BHE":"Benchmark Electronics, Inc.","BHF":"BRIGHTHOUSE FINL INC","BHP":"BHP Group Limited","BHRB":"Burke & Herbert Financial Services Corp.","BHVN":"BIOHAVEN LTD","BIBL":"Inspire 100 ETF","BIDD":"iShares International Dividend Active ETF","BIDU":"BAIDU INC","BIIB":"BIOGEN INC","BIL":"State Street SPDR Bloomberg 1-3 Month T-Bill ETF","BILI":"BILIBILI INC","BILL":"BILL HOLDINGS INC","BILS":"State Street SPDR Bloomberg 3-12 Month T-Bill ETF","BILZ":"PIMCO Ultra Short Government Active Exchange-Traded Fund","BINC":"iShares Flexible Income Active ETF","BINT":"Bluemonte Global Equity ETF","BINV":"Brandes International ETF","BIO":"BIO RAD LABS INC","BIOA":"BioAge Labs, Inc.","BIP":"Brookfield Infrastructure Partners LP Limited Partnership","BIPC":"BROOKFIELD INFRASTRUCTURE CO","BIRK":"BIRKENSTOCK HOLDING PLC","BITB":"Bitwise Bitcoin ETF","BITF":"BITFARMS LTD","BITI":"ProShares Short Bitcoin ETF","BITO":"ProShares Bitcoin ETF","BITQ":"Bitwise Crypto Industry Innovators ETF","BITU":"ProShares Ultra Bitcoin ETF","BITW":"BITWISE 10 CRYPTO INDEX ETF","BITX":"2x Bitcoin Strategy ETF","BIV":"Vanguard Intermediate-Term Bond ETF","BIZD":"VanEck BDC Income ETF","BJ":"BJ's Wholesale Club Holdings, Inc.","BJAN":"Innovator U.S. Equity Buffer ETF - January","BJRI":"BJ's Restaurants, Inc.","BK":"BANK NEW YORK MELLON CORP","BKAG":"BNY Mellon Core Bond ETF","BKCH":"Global X Blockchain ETF","BKD":"Brookdale Senior Living Inc.","BKDV":"BNY Mellon Dynamic Value ETF","BKE":"Buckle, Inc. (The)","BKFI":"BNY Mellon Active Core Bond ETF","BKGI":"BNY Mellon Global Infrastructure Income ETF","BKH":"BLACK HILLS CORP","BKHY":"BNY Mellon High Yield ETF","BKIE":"BNY Mellon International Equity ETF","BKKT":"Bakkt, Inc.","BKLC":"BNY Mellon US Large Cap Core Equity ETF","BKLN":"Invesco Senior Loan ETF","BKMC":"BNY Mellon US Mid Cap Core Equity ETF","BKMI":"BNY Mellon Municipal Intermediate ETF","BKMS":"BNY Mellon Municipal Short Duration ETF","BKNG":"BOOKING HOLDINGS INC","BKR":"BAKER HUGHES COMPANY","BKSY":"BlackSky Technology Inc.","BKTI":"BK Technologies Corporation","BKU":"BANKUNITED INC","BKUI":"BNY MELLON ULTRA SHORT INCOME ETF","BKV":"BKV Corporation","BL":"BLACKLINE INC","BLBD":"Blue Bird Corp - US","BLCO":"Bausch Lomb Corp","BLD":"TOPBUILD CORP","BLDP":"Ballard Power Systems, Inc.","BLDR":"BUILDERS FIRSTSOURCE INC","BLFS":"BioLife Solutions, Inc.","BLFY":"Blue Foundry Bancorp","BLK":"BLACKROCK INC","BLKB":"BLACKBAUD INC","BLLN":"BILLIONTOONE INC","BLMN":"Bloomin' Brands, Inc.","BLND":"BLEND LABS INC","BLOK":"Amplify Blockchain Technology ETF","BLOX":"Nicholas Crypto Income ETF","BLSH":"BULLISH","BLTE":"BELITE   BIO   INC","BLUC":"Bluemonte Large Cap Core ETF","BLUX":"Bluemonte Dynamic Total Market ETF","BLV":"Vanguard Long-Term Bond ETF","BLX":"Banco Latinoamericano de Comercio Exterior, S.A.","BLZE":"BACKBLAZE INC","BMA":"Banco Macro S.A.","BMAR":"Innovator U.S. Equity Buffer ETF - March","BMBL":"BUMBLE INC","BMI":"BADGER METER INC","BMNR":"BitMine Immersion Technologies, Inc.","BMO":"BANK MONTREAL QUE","BMOP":"BNY Mellon Municipal Opportunities ETF","BMRC":"Bank of Marin Bancorp","BMRN":"BIOMARIN PHARMACEUTICAL INC","BMY":"BRISTOL-MYERS SQUIBB CO","BN":"BROOKFIELD CORP","BNAI":"Brand Engagement Network Inc.","BNC":"CEA Industries Inc.","BND":"Vanguard Total Bond Market ETF","BNDI":"NEOS Enhanced Income Aggregate Bond ETF","BNDP":"Vanguard Core-Plus Bond Index ETF","BNDW":"Vanguard Total World Bond ETF","BNDX":"Vanguard Total International Bond ETF","BNED":"Barnes & Noble Education, Inc","BNL":"BROADSTONE NET LEASE INC","BNO":"United States Brent Oil Fund, LP ETV","BNS":"Bank Nova Scotia Halifax Pfd 3","BNT":"Brookfield Wealth Solutions Ltd.","BNTC":"Benitec Biopharma Inc.","BNTX":"BIONTECH SE","BOBS":"Bob's Discount Furniture, Inc.","BOC":"Boston Omaha Corporation","BOCT":"Innovator U.S. Equity Buffer ETF - October","BOH":"Bank of Hawaii Corporation","BOIL":"ProShares Ultra Bloomberg Natural Gas","BOKF":"BOK Financial Corporation","BOND":"PIMCO Active Bond Exchange-Traded Fund Exchange-Traded Fund","BOOM":"DMC GLOBAL INC","BOOT":"Boot Barn Holdings, Inc.","BORR":"BORR DRILLING LTD","BOTZ":"GLOBAL X FDS","BOW":"Bowhead Specialty Holdings Inc.","BOX":"BOX INC","BOXX":"Alpha Architect 1-3 Month Box ETF","BP":"BP PLC","BPOP":"POPULAR INC","BPRN":"Princeton Bancorp, Inc.","BR":"Broadridge Financial Solutions, Inc.","BRBR":"BELLRING BRANDS INC","BRBS":"Blue Ridge Bankshares, Inc.","BRC":"Brady Corporation","BRCB":"Black Rock Coffee Bar Inc","BRCC":"BRC INC","BRHY":"iShares High Yield Active ETF","BRKR":"BRUKER CORP","BRNY":"Burney U.S. Factor Rotation ETF","BRO":"Brown & Brown, Inc.","BROS":"DUTCH BROS INC","BRR":"ProCap Financial, Inc.","BRRR":"Coinshares Bitcoin ETF","BRSL":"Brightstar Lottery PLC Trading under the Legal Name to begin at the market open on July 21, 2025.","BRTR":"iShares Total Return Active ETF","BRX":"BRIXMOR PPTY GROUP INC","BRZE":"BRAZE INC","BRZU":"Direxion Daily Brazil Bull 2X Shares","BSAC":"Banco Santander - Chile","BSBR":"Banco Santander Brasil SA","BSCQ":"Invesco BulletShares 2026 Corporate Bond ETF","BSCR":"Invesco BulletShares 2027 Corporate Bond ETF","BSCS":"Invesco BulletShares 2028 Corporate Bond ETF","BSCT":"Invesco BulletShares 2029 Corporate Bond ETF","BSCU":"Invesco BulletShares 2030 Corporate Bond ETF","BSCV":"Invesco BulletShares 2031 Corporate Bond ETF","BSCW":"Invesco BulletShares 2032 Corporate Bond ETF","BSCX":"Invesco BulletShares 2033 Corporate Bond ETF","BSCY":"Invesco BulletShares 2034 Corporate Bond ETF","BSCZ":"Invesco BulletShares 2035 Corporate Bond ETF","BSJQ":"Invesco BulletShares 2026 High Yield Corporate Bond ETF","BSJR":"Invesco BulletShares 2027 High Yield Corporate Bond ETF","BSJS":"Invesco BulletShares 2028 High Yield Corporate Bond ETF","BSJT":"Invesco BulletShares 2029 High Yield Corporate Bond ETF","BSJU":"Invesco BulletShares 2030 High Yield Corporate Bond ETF","BSM":"Black Stone Minerals, L.P.","BSMQ":"Invesco BulletShares 2026 Municipal Bond ETF","BSMR":"Invesco BulletShares 2027 Municipal Bond ETF","BSMS":"Invesco BulletShares 2028 Municipal Bond ETF","BSMT":"Invesco BulletShares 2029 Municipal Bond ETF","BSMU":"Invesco BulletShares 2030 Municipal Bond ETF","BSMV":"Invesco BulletShares 2031 Municipal Bond ETF","BSOL":"Bitwise Solana Staking ETF","BSRR":"Sierra Bancorp","BSV":"Vanguard Short-Term Bond ETF","BSVO":"EA Bridgeway Omni Small-Cap Value ETF","BSX":"BOSTON SCIENTIFIC CORP","BSY":"BENTLEY SYS INC","BTAL":"AGF U.S. Market Neutral Anti-Beta Fund","BTBT":"BIT DIGITAL INC","BTC":"GRAYSCALE BITCOIN MINI TR ET","BTCI":"NEOS Bitcoin High Income ETF","BTCO":"Invesco Galaxy Bitcoin ETF","BTCW":"WisdomTree Bitcoin Fund","BTDR":"BITDEER TECHNOLOGIES GROUP","BTE":"Baytex Energy Corp","BTG":"B2GOLD     CORP","BTGO":"BitGo Holdings, Inc.","BTI":"BRITISH AMERN TOB PLC","BTSG":"BRIGHTSPRING HEALTH SVCS INC","BTU":"PEABODY ENERGY CORP","BUCK":"Simplify Treasury Option Income ETF","BUD":"Anheuser-Busch Inbev SA Sponsored","BUFC":"AB Conservative Buffer ETF","BUFD":"FT Vest Laddered Deep Buffer ETF","BUFF":"Innovator Laddered Allocation Power Buffer ETF","BUFG":"FT Vest Buffered Allocation Growth ETF","BUFP":"PGIM Laddered S&P 500 Buffer 12 ETF","BUFQ":"FT Vest Laddered Nasdaq Buffer ETF","BUFR":"FT Vest Laddered Buffer ETF","BUFZ":"FT Vest Laddered Moderate Buffer ETF","BUG":"Global X Cybersecurity ETF","BULL":"WEBULL CORP","BULZ":"MicroSectors FANG & Innovation 3x Leveraged ETN","BUR":"BURFORD CAP LTD","BURL":"BURLINGTON STORES INC","BUSA":"Brandes U.S. Value ETF","BUSE":"First Busey Corporation","BUXX":"Strive Enhanced Income Short Maturity ETF","BUYW":"Main BuyWrite ETF","BV":"BrightView Holdings, Inc.","BVAL":"Bluemonte Large Cap Value ETF","BVN":"Buenaventura Mining Company Inc.","BVS":"Bioventus Inc.","BW":"Babcock & Wilcox Enterprises, Inc.","BWA":"BORGWARNER INC","BWB":"Bridgewater Bancshares, Inc.","BWFG":"Bankwell Financial Group, Inc.","BWIN":"The Baldwin Insurance Group, Inc.","BWLP":"BW LPG Limited","BWMN":"Bowman Consulting Group Ltd.","BWMX":"Betterware de Mexico, S.A.P.I. de C.V.","BWX":"SPDR Bloomberg International Treasury Bond ETF","BWXT":"BWX TECHNOLOGIES INC","BWZ":"SPDR Bloomberg Short Term International Treasury Bond ETF","BX":"BLACKSTONE INC","BXC":"Bluelinx Holdings Inc.","BXMT":"Blackstone Mortgage Trust, Inc.","BXP":"BXP, Inc.","BXSL":"Blackstone Secured Lending Fund","BY":"Byline Bancorp, Inc.","BYD":"BOYD GAMING CORP","BYLD":"iShares Yield Optimized Bond ETF","BYND":"BEYOND MEAT INC","BYRN":"Byrna Technologies, Inc.","BZ":"KANZHUN LIMITED","BZAI":"Blaize Holdings, Inc.","BZH":"BEAZER HOMES USA INC","C":"CITIGROUP INC","CAAP":"CORPORACION AMER ARPTS S A","CABA":"CABALETTA BIO INC","CABO":"CABLE ONE INC","CAC":"Camden National Corporation","CACC":"CREDIT ACCEP CORP MICH","CACI":"CACI International, Inc.","CADL":"Candel Therapeutics, Inc.","CAE":"CAE Inc.","CAEP":"Cantor Equity Partners III, Inc.","CAFX":"Congress Intermediate Bond ETF","CAG":"CONAGRA BRANDS INC","CAH":"Cardinal Health, Inc.","CAI":"CARIS LIFE SCIENCES INC","CAIE":"Calamos Autocallable Income ETF","CAIQ":"Calamos Nasdaq Autocallable Income ETF","CAKE":"CHEESECAKE FACTORY INC","CAL":"Caleres, Inc.","CALF":"Pacer US Small Cap Cash Cows ETF","CALI":"iShares Short-Term California Muni Active ETF","CALM":"CAL MAINE FOODS INC","CALX":"CALIX INC","CALY":"Callaway Golf Company","CAML":"Congress Large Cap Growth ETF","CAMT":"CAMTEK LTD","CANC":"Tema Oncology ETF","CANG":"Cango Inc.","CAOS":"Alpha Architect Tail Risk ETF","CAPE":"DoubleLine Shiller CAPE U.S. Equities ETF","CAPL":"CrossAmerica Partners LP","CAPR":"CAPRICOR THERAPEUTICS INC","CAR":"AVIS BUDGET GROUP","CARE":"Carter Bankshares, Inc.","CARG":"CARGURUS INC","CARK":"CastleArk Large Growth ETF","CARL":"Carlsmed, Inc.","CARR":"CARRIER GLOBAL CORPORATION","CARS":"Cars.com Inc.","CART":"MAPLEBEAR INC","CARY":"Angel Oak Income ETF","CASH":"Pathward Financial, Inc.","CASS":"Cass Information Systems, Inc","CASY":"CASEYS GEN STORES INC","CAT":"CATERPILLAR INC","CATH":"Global X S&P 500 Catholic Values ETF","CATX":"Perspective Therapeutics, Inc.","CATY":"Cathay General Bancorp","CAVA":"CAVA GROUP INC","CB":"CHARTER COMMUNICATIONS INC N","CBAN":"Colony Bankcorp, Inc.","CBC":"CENTRAL BANCOMPANY","CBIO":"Crescent Biopharma, Inc.","CBK":"Commercial Bancgroup, Inc.","CBL":"CBL & Associates Properties, Inc.","CBLL":"CeriBell, Inc.","CBNK":"Capital Bancorp, Inc.","CBOE":"CBOE GLOBAL MKTS INC","CBRE":"CBRE GROUP INC","CBRL":"Cracker Barrel Old Country Store, Inc.","CBSH":"COMMERCE BANCSHARES INC","CBT":"CABOT CORP","CBU":"Community Financial System, Inc.","CBUS":"Cibus, Inc.","CBZ":"CBIZ INC","CC":"CHEMOURS CO","CCAP":"Crescent Capital BDC, Inc.","CCB":"Coastal Financial Corporation","CCBG":"Capital City Bank Group","CCC":"CCC Intelligent Solutions Holdings Inc.","CCCC":"C4 THERAPEUTICS INC","CCEP":"COCA COLA EUROPACIFIC PARTNE","CCI":"Crown Castle, Inc.","CCJ":"CAMECO CORP","CCK":"Crown Holdings, Inc.","CCL":"CARNIVAL CORP","CCNE":"CNB Financial Corporation","CCNR":"ALPS/CoreCommodity Natural Resources ETF","CCO":"CLEAR CHANNEL OUTDOOR HLDGS","CCOI":"COGENT COMMUNICATIONS HLDGS","CCS":"CENTURY CMNTYS INC","CCSI":"Consensus Cloud Solutions, Inc.","CCU":"Compania Cervecerias Unidas, S.A.","CD":"Chaince Digital Holdings Inc. - American","CDC":"VictoryShares US EQ Income Enhanced Volatility Wtd ETF","CDE":"COEUR MNG INC","CDLR":"Cadeler A/S","CDNA":"CareDx, Inc.","CDNL":"Cardinal Infrastructure Group Inc.","CDNS":"CADENCE DESIGN SYSTEM INC","CDP":"COPT Defense Properties","CDRE":"Cadre Holdings, Inc.","CDW":"CDW Corporation","CDX":"Simplify High Yield ETF","CDZI":"CADIZ INC","CE":"CELANESE CORP DEL","CECO":"Ceco Environmental Corp - US","CEFS":"Saba Closed-End Funds ETF","CEG":"CONSTELLATION ENERGY CORP","CELC":"CELCUITY INC","CELH":"CELSIUS HLDGS INC","CEMB":"iShares J.P. Morgan EM Corporate Bond ETF","CENTA":"Central Garden & Pet Company","CENX":"Century Aluminum Company","CEPO":"CANTOR EQUITY PARTNERS I INC","CEPT":"Cantor Equity Partners II, Inc.","CEPU":"Central Puerto S.A.","CERS":"Cerus Corporation","CERT":"CERTARA INC","CERY":"SPDR Bloomberg Enhanced Roll Yield Commodity Strategy No K-1 ETF","CEVA":"CEVA INC","CF":"CF Industries Holdings, Inc.","CFA":"VictoryShares US 500 Volatility Wtd ETF","CFBK":"CF Bankshares Inc.","CFFN":"Capitol Federal Financial, Inc.","CFG":"CITIZENS FINL GROUP INC","CFLT":"CONFLUENT INC","CFR":"Cullen/Frost Bankers, Inc.","CG":"CARLYLE GROUP INC","CGAU":"Centerra Gold Inc.","CGBD":"Carlyle Secured Lending, Inc.","CGBL":"Capital Group Core Balanced ETF","CGC":"Canopy Growth Corporation","CGCP":"Capital Group Core Plus Income ETF","CGCV":"Capital Group Conservative Equity ETF","CGDG":"Capital Group Dividend Growers ETF","CGDV":"Capital Group Dividend Value ETF","CGEM":"CULLINAN THERAPEUTICS INC","CGGE":"Capital Group Global Equity ETF","CGGO":"Capital Group Global Growth Equity ETF","CGGR":"Capital Group Growth ETF","CGHM":"Capital Group Municipal High-Income ETF","CGIB":"Capital Group International Bond ETF (USD-Hedged)","CGIC":"Capital Group International Core Equity ETF","CGIE":"Capital Group International Equity ETF","CGMM":"Capital Group U.S. Small and Mid Cap ETF","CGMS":"Capital Group U.S. Multi-Sector Income ETF","CGMU":"Capital Group Municipal Income ETF","CGNG":"Capital Group New Geography Equity ETF","CGNT":"Cognyte Software Ltd.","CGNX":"COGNEX CORP","CGON":"CG ONCOLOGY INC","CGSD":"Capital Group Short Duration Income ETF","CGSM":"Capital Group Short Duration Municipal Income ETF","CGUI":"Capital Group Ultra Short Income ETF","CGUS":"Capital Group Core Equity ETF","CGW":"Invesco S&P Global Water Index ETF","CGXU":"Capital Group International Focus Equity ETF","CHA":"Chagee Holdings Limited","CHAC":"Crane Harbor Acquisition Corp.","CHAR":"Charlton Aria Acquisition Corporation","CHAT":"Roundhill Generative AI & Technology ETF","CHAU":"Direxion Daily CSI 300 China A Share Bull 2X Shares","CHCO":"City Holding Company","CHD":"Church & Dwight Company, Inc.","CHDN":"CHURCHILL DOWNS INC","CHE":"CHEMED   CORP    NEW","CHEC":"Chenghe Acquisition III Co.","CHEF":"CHEFS WHSE INC","CHH":"CHOICE HOTELS INTL INC","CHKP":"CHECK POINT SOFTWARE TECH LT","CHPT":"CHARGEPOINT HOLDINGS INC","CHPY":"YieldMax Semiconductor Portfolio Option Income ETF","CHRD":"CHORD ENERGY CORPORATION","CHRS":"Coherus Oncology, Inc.","CHRW":"C H ROBINSON WORLDWIDE INC","CHT":"Chunghwa Telecom Co., Ltd.","CHTR":"Charter Communications, Inc.","CHWY":"CHEWY INC","CHYM":"CHIME FINL INC","CI":"THE CIGNA GROUP","CIB":"GRUPO CIBEST SA","CIBR":"First Trust NASDAQ Cybersecurity ETF","CIEN":"CIENA CORP","CIFR":"CIPHER MINING INC","CIG":"Comp En De Mn Cemig","CIGI":"Colliers International Group Inc. - Subordinate Voting Shares","CIM":"Chimera Investment Corporation","CINF":"Cincinnati Financial Corporation","CINT":"CI&T Inc","CION":"CION Investment Corporation","CIVB":"Civista Bancshares, Inc.","CL":"COLGATE PALMOLIVE CO","CLAR":"Clarus Corporation","CLB":"Core Laboratories Inc.","CLBK":"Columbia Financial, Inc.","CLBT":"CELLEBRITE DI LTD","CLDX":"Celldex Therapeutics, Inc.","CLF":"CLEVELAND-CLIFFS INC NEW","CLFD":"Clearfield, Inc.","CLH":"CLEAN HARBORS INC","CLIP":"Global X 1-3 Month T-Bill ETF","CLMB":"Climb Global Solutions, Inc.","CLMT":"CALUMET INC","CLNE":"Clean Energy Fuels Corp.","CLOA":"iShares AAA CLO Active ETF","CLOB":"VanEck AA-BB CLO ETF","CLOI":"VanEck CLO ETF","CLOU":"Global X Cloud Computing ETF","CLOV":"Clover Health Investments, Corp.","CLOX":"Eldridge AAA CLO ETF","CLOZ":"Eldridge BBB-B CLO ETF","CLPT":"ClearPoint Neuro Inc.","CLS":"CELESTICA INC","CLSE":"Convergence Long/Short Equity ETF","CLSK":"CLEANSPARK INC","CLVT":"CLARIVATE PLC","CLW":"CLEARWATER PAPER CORP","CLX":"CLOROX CO DEL","CLYM":"Climb Bio, Inc.","CM":"Canadian Imperial Bank of Commerce","CMBS":"iShares CMBS Bond ETF","CMBT":"CMB.TECH NV","CMC":"Commercial Metals Company","CMCL":"Caledonia Mining Corporation Plc","CMCO":"Columbus McKinnon Corporation","CMCSA":"COMCAST CORP NEW","CMDB":"Costamare Bulkers Holdings Limited","CMDT":"PIMCO Commodity Strategy Active Exchange-Traded Fund","CMDY":"iShares Bloomberg Roll Select Commodity Strategy ETF","CME":"CME GROUP INC","CMF":"iShares California Muni Bond ETF","CMG":"CHIPOTLE MEXICAN GRILL INC","CMI":"CUMMINS INC","CMP":"COMPASS MINERALS INTL INC","CMPR":"Cimpress plc","CMPX":"Compass Therapeutics, Inc.","CMRC":"Commerce.com, Inc. - Series 1","CMRE":"Costamare Inc.","CMS":"CMS ENERGY CORP","CMT":"Core Molding Technologies Inc","CMTL":"Comtech Telecommunications Corp.","CNA":"CNA Financial Corporation","CNC":"CENTENE CORP DEL","CNDT":"Conduent Incorporated","CNEQ":"Alger Concentrated Equity ETF","CNH":"CNH Industrial N.V.","CNI":"CANADIAN NATL RY CO","CNK":"Cinemark Holdings, Inc.","CNL":"Collective Mining Ltd.","CNM":"CORE &amp; MAIN INC","CNMD":"CONMED CORP","CNNE":"CANNAE HLDGS INC","CNO":"CNO Financial Group, Inc.","CNOB":"CONNECTONE BANCORP INC","CNP":"CENTERPOINT ENERGY INC","CNQ":"CANADIAN NAT RES LTD","CNR":"CORE NATURAL RESOURCES INC","CNRG":"State Street SPDR S&P Kensho Clean Power ETF","CNS":"Cohen & Steers Inc","CNTA":"CENTESSA PHARMACEUTICALS PLC","CNTN":"Canton Strategic Holdings, Inc.","CNTX":"Context Therapeutics Inc.","CNX":"CNX RES CORP","CNXC":"CONCENTRIX CORPORATION","CNXN":"PC Connection, Inc.","CNYA":"iShares MSCI China A ETF","COCO":"The Vita Coco Company, Inc.","CODA":"Coda Octopus Group, Inc.","CODI":"D/B/A Compass Diversified Holdings Shares of Beneficial Interest","COF":"CAPITAL ONE FINANCIAL CORP","COFS":"ChoiceOne Financial Services, Inc.","COGT":"COGENT BIOSCIENCES INC","COHR":"COHERENT CORP","COHU":"Cohu, Inc.","COIN":"COINBASE GLOBAL INC","COKE":"Coca-Cola Consolidated, Inc.","COLB":"Columbia Banking System, Inc.","COLD":"Americold Realty Trust Inc","COLL":"Collegium Pharmaceutical, Inc.","COLM":"COLUMBIA SPORTSWEAR CO","COLO":"Global X MSCI Colombia ETF","COM":"Direxion Auspice Broad Commodity Strategy ETF","COMB":"GraniteShares Bloomberg Commodity Broad Strategy No K-1 ETF","COMP":"COMPASS INC","COMT":"iShares GSCI Commodity Dynamic Roll Strategy ETF","CON":"Concentra Group Holdings Parent, Inc.","CONL":"GraniteShares 2x Long COIN Daily ETF","CONY":"YieldMax COIN Option Income Strategy ETF","COO":"COOPER COS INC","COP":"CONOCOPHILLIPS","COPJ":"Sprott Junior Copper Miners ETF","COPP":"Sprott Copper Miners ETF","COPX":"Global X Copper Miners ETF","COPY":"Tweedy, Browne Insider + Value ETF","COR":"CENCORA INC","CORP":"PIMCO Investment Grade Corporate Bond Index Exchange-Traded Fund","CORT":"Corcept Therapeutics Incorporated","CORZ":"CORE SCIENTIFIC INC NEW","COSO":"CoastalSouth Bancshares, Inc.","COST":"COSTCO WHSL CORP NEW","COTY":"COTY INC","COUR":"Coursera, Inc.","COWG":"Pacer US Large Cap Cash Cows Growth Leaders ETF","COWZ":"PACER FDS TR","CP":"CANADIAN PACIFIC KANSAS CITY","CPA":"COPA HOLDINGS SA","CPAG":"F/m Compoundr U.S. Aggregate Bond ETF","CPAI":"Counterpoint Quantitative Equity ETF","CPAY":"CORPAY INC","CPB":"The Campbell's Company","CPER":"United States Copper Index Fund ETV","CPF":"Central Pacific Financial Corp New","CPK":"Chesapeake Utilities Corporation","CPLB":"NYLI MacKay Core Plus Bond ETF","CPNG":"COUPANG INC","CPRI":"CAPRI HOLDINGS LIMITED","CPRT":"COPART INC","CPRX":"CATALYST PHARMACEUTICALS INC","CPS":"Cooper-Standard Holdings Inc.","CPT":"CAMDEN PPTY TR","CQP":"Cheniere Energy Partners, LP","CQQQ":"Invesco China Technology ETF","CR":"CRANE COMPANY","CRAI":"CRA International,Inc.","CRAQ":"CAL REDWOOD ACQUISITION CORP","CRBG":"COREBRIDGE FINL INC","CRBN":"iShares Low Carbon Optimized MSCI ACWI ETF","CRBP":"Corbus Pharmaceuticals Holdings, Inc.","CRBU":"Caribou Biosciences, Inc.","CRC":"California Resources Corporation","CRCL":"CIRCLE INTERNET GROUP INC","CRCT":"Cricut, Inc.","CRD.A":"Crawford & Company","CRDF":"Cardiff Oncology, Inc.","CRDO":"CREDO TECHNOLOGY GROUP HOLDI","CRGY":"Crescent Energy Company","CRH":"CRH PLC","CRI":"Carter's, Inc.","CRK":"Comstock Resources, Inc.","CRL":"CHARLES RIV LABS INTL INC","CRM":"SALESFORCE INC","CRMD":"CorMedix Inc.","CRML":"CRITICAL METALS CORP","CRMT":"America's Car-Mart, Inc.","CRNC":"Cerence Inc.","CRNT":"Ceragon Networks Ltd.","CRNX":"CRINETICS PHARMACEUTICALS IN","CRON":"Cronos Group Inc. Common Share","CROX":"CROCS INC","CRS":"CARPENTER TECHNOLOGY CORP","CRSP":"CRISPR THERAPEUTICS AG","CRSR":"Corsair Gaming, Inc.","CRUS":"CIRRUS LOGIC INC","CRVL":"CORVEL CORP","CRVS":"CORVUS PHARMACEUTICALS INC","CRWD":"<![CDATA[CROWDSTRIKE HOLDINGS INC]]>","CRWG":"Leverage Shares 2X Long CRWV Daily ETF","CRWV":"COREWEAVE INC","CSAN":"Cosan S.A.","CSB":"VictoryShares US Small Cap High Div Volatility Wtd ETF","CSCO":"CISCO SYS INC","CSD":"Invesco S&P Spin-Off ETF","CSGP":"COSTAR GROUP INC","CSGS":"CSG Systems International, Inc.","CSHI":"NEOS Enhanced Income Cash Alternative ETF","CSIQ":"CANADIAN SOLAR INC","CSL":"CARLISLE COS INC","CSMD":"Congress SMid Growth ETF","CSPF":"Cohen & Steers Preferred and Income Opportunities Active ETF","CSR":"D/B/A Centerspace","CSRE":"Cohen & Steers Real Estate Active ETF","CSTL":"Castle Biosciences Inc - US","CSTM":"CONSTELLIUM SE","CSV":"Carriage Services, Inc.","CSW":"CSW INDUSTRIALS INC","CSWC":"Capital Southwest Corporation","CSX":"CSX CORP","CTA":"Simplify Managed Futures Strategy ETF","CTAP":"Simplify US Equity PLUS Managed Futures Strategy ETF","CTAS":"CINTAS CORP","CTBI":"Community Trust Bancorp, Inc.","CTEV":"CLARITEV CORPORATION","CTGO":"CONTANGO ORE INC","CTKB":"Cytek Biosciences, Inc.","CTLP":"CANTALOUPE INC","CTMX":"CYTOMX THERAPEUTICS INC","CTNM":"Contineum Therapeutics, Inc.","CTO":"CTO Realty Growth, Inc.","CTOS":"Custom Truck One Source, Inc.","CTRA":"COTERRA ENERGY INC","CTRE":"CARETRUST REIT INC","CTRI":"Centuri Holdings Inc","CTRN":"Citi Trends, Inc.","CTS":"CTS Corporation","CTSH":"Cognizant Technology Solutions Corporation","CTVA":"CORTEVA INC","CUBE":"CUBESMART","CUBI":"CUSTOMERS BANCORP INC","CUK":"CARNIVAL CORP","CURB":"Curbline Properties Corp.","CURE":"Direxion Daily Healthcare Bull 3X Shares","CURI":"CuriosityStream Inc.","CUZ":"COUSINS PPTYS INC","CV":"CapsoVision, Inc.","CVBF":"CVB Financial Corporation","CVCO":"Cavco Industries, Inc.","CVE":"CENOVUS   ENERGY         INC","CVEO":"CIVEO CORP CDA","CVGW":"Calavo Growers, Inc.","CVI":"CVR ENERGY INC","CVIE":"Calvert International Responsible Index ETF","CVLC":"Calvert US Large-Cap Core Responsible Index ETF","CVLG":"Covenant Logistics Group, Inc.","CVLT":"Commvault Systems, Inc.","CVNA":"CARVANA CO CL A","CVRX":"CVRx, Inc.","CVS":"CVS HEALTH CORP","CVSA":"Adtalem Global Education Inc.","CVSB":"Calvert Ultra-Short Investment Grade ETF","CVX":"CHEVRON CORP NEW","CW":"CURTISS WRIGHT CORP","CWAN":"CLEARWATER ANALYTICS HLDGS I","CWB":"State Street SPDR Bloomberg Convertible Securities ETF","CWBC":"Community West Bancshares","CWCO":"Consolidated Water Co. Ltd.","CWEB":"Direxion Daily CSI China Internet Index Bull 2X Shares","CWEN":"Clearway Energy, Inc.","CWH":"Camping World Holdings, Inc.","CWI":"State Street SPDR MSCI ACWI ex-US ETF","CWK":"Cushman & Wakefield Ltd.","CWS":"AdvisorShares Focused Equity ETF","CWST":"Casella Waste Systems, Inc.","CWT":"California Water Service Group","CX":"Cemex, S.A.B. de C.V. Sponsored","CXDO":"Crexendo, Inc.","CXM":"Sprinklr Inc - US","CXSE":"WisdomTree China ex-State-Owned Enterprises Fund","CXT":"Crane NXT, Co.","CYD":"China Yuchai International Limited","CYH":"Community Health Systems, Inc.","CYRX":"CRYOPORT INC","CYTK":"Cytokinetics, Incorporated","CZNC":"Citizens & Northern Corp","CZR":"CAESARS ENTERTAINMENT INC NE","CZWI":"Citizens Community Bancorp, Inc.","D":"DOMINION ENERGY INC","DAAQ":"Digital Asset Acquisition Corp.","DAC":"Danaos Corporation","DAKT":"DAKTRONICS INC","DAL":"DELTA AIR LINES INC DEL","DAN":"Dana Incorporated","DAPP":"VanEck Digital Transformation ETF","DAR":"DARLING INGREDIENTS INC","DASH":"<![CDATA[DOORDASH INC]]>","DAVE":"DAVE INC","DAWN":"Day One Biopharmaceuticals, Inc.","DAX":"Global X DAX Germany ETF","DB":"DEUTSCHE BANK A G","DBA":"Invesco DB Agriculture Fund","DBB":"Invesco DB Base Metals Fund","DBC":"Invesco DB Commodity Index Tracking Fund","DBD":"Diebold Nixdorf Incorporated","DBEF":"Xtrackers MSCI EAFE Hedged Equity ETF","DBEU":"Xtrackers MSCI Europe Hedged Equity ETF","DBI":"Designer Brands Inc.","DBJP":"Xtrackers MSCI Japan Hedged Equity ETF","DBMF":"iMGP DBi Managed Futures Strategy ETF","DBND":"DoubleLine Opportunistic Bond ETF","DBO":"Invesco DB Oil Fund","DBP":"Invesco DB Precious Metals Fund","DBVT":"DBV Technologies S.A.","DBX":"DROPBOX INC","DC":"Dakota Gold Corp.","DCBO":"Docebo Inc.","DCH":"Dauch Corporation","DCI":"DONALDSON INC","DCO":"Ducommun Incorporated","DCOM":"Dime Community Bancshares, Inc.","DCOR":"Dimensional US Core Equity 1 ETF","DCRE":"DoubleLine Commercial Real Estate Debt ETF","DCTH":"Delcath Systems, Inc.","DD":"DUPONT DE NEMOURS INC","DDD":"3D Systems Corporation","DDLS":"WisdomTree Dynamic International SmallCap Equity Fund","DDM":"ProShares Ultra Dow30","DDOG":"<![CDATA[DATADOG INC]]>","DDS":"DILLARDS INC","DDWM":"WisdomTree Dynamic International Equity Fund","DE":"DEERE   CO","DEA":"Easterly Government Properties, Inc.","DEC":"Diversified Energy Company","DECK":"DECKERS OUTDOOR CORP","DEFT":"Defi Technologies, Inc.","DEHP":"Dimensional Emerging Markets High Profitability ETF","DEI":"Douglas Emmett, Inc","DELL":"DELL TECHNOLOGIES INC","DEM":"WisdomTree Emerging Markets High Dividend Fund","DEO":"DIAGEO PLC","DERM":"Journey Medical Corporation","DES":"WisdomTree U.S. SmallCap Dividend Fund","DEUS":"Xtrackers Russell US Multifactor ETF","DEXC":"Dimensional Emerging Markets ex China Core Equity ETF","DFAC":"Dimensional U.S. Core Equity 2 ETF","DFAE":"Dimensional Emerging Core Equity Market ETF","DFAI":"Dimensional International Core Equity Market ETF","DFAR":"Dimensional US Real Estate ETF","DFAS":"Dimensional U.S. Small Cap ETF","DFAT":"Dimensional U.S. Targeted Value ETF","DFAU":"Dimensional US Core Equity Market ETF","DFAW":"Dimensional World Equity ETF","DFAX":"Dimensional World ex U.S. Core Equity 2 ETF","DFCA":"Dimensional California Municipal Bond ETF","DFCF":"Dimensional Core Fixed Income ETF","DFDV":"DEFI DEVELOPMENT CORP","DFE":"WisdomTree Europe SmallCap Dividend Fund","DFEB":"FT Vest U.S. Equity Deep Buffer ETF - February","DFEM":"Dimensional Emerging Markets Core Equity 2 ETF","DFEN":"Direxion Daily Aerospace & Defense Bull 3X Shares","DFEV":"Dimensional Emerging Markets Value ETF","DFGP":"Dimensional Global Core Plus Fixed Income ETF","DFGR":"Dimensional Global Real Estate ETF","DFGX":"Dimensional Global ex US Core Fixed Income ETF","DFH":"DREAM FINDERS HOMES INC","DFIC":"Dimensional International Core Equity 2 ETF","DFIN":"Donnelley Financial Solutions, Inc.","DFIP":"Dimensional Inflation-Protected Securities ETF","DFIS":"Dimensional International Small Cap ETF","DFIV":"Dimensional International Value ETF","DFJ":"WisdomTree Japan SmallCap Fund","DFLV":"Dimensional US Large Cap Value ETF","DFNL":"Davis Select Financial ETF","DFNM":"Dimensional National Municipal Bond ETF","DFSB":"Dimensional Global Sustainability Fixed Income ETF","DFSD":"Dimensional Short-Duration Fixed Income ETF","DFSE":"Dimensional Emerging Markets Sustainability Core 1 ETF","DFSI":"Dimensional International Sustainability Core 1 ETF","DFSU":"Dimensional US Sustainability Core 1 ETF","DFSV":"Dimensional US Small Cap Value ETF","DFTX":"Definium Therapeutics, Inc.","DFUS":"Dimensional U.S. Equity Market ETF","DFUV":"Dimensional US Marketwide Value ETF","DFVX":"Dimensional US Large Cap Vector ETF","DG":"DOLLAR GEN CORP NEW","DGCB":"Dimensional Global Credit ETF","DGICA":"Donegal Group, Inc.","DGII":"Digi International Inc.","DGNX":"Diginex Limited","DGP":"DB Gold Double Long ETN due February 15, 2038","DGRO":"ISHARES TR","DGRS":"WisdomTree U.S. SmallCap Quality Dividend Growth Fund","DGRW":"WisdomTree U.S. Quality Dividend Growth Fund","DGS":"WisdomTree Emerging Market SmallCap Fund","DGT":"State Street SPDR Global Dow ETF","DGX":"Quest Diagnostics Incorporated","DGXX":"Digi Power X Inc.","DH":"Definitive Healthcare Corp.","DHC":"Diversified Healthcare Trust","DHI":"D R HORTON INC","DHIL":"Diamond Hill Investment Group, Inc.","DHR":"DANAHER CORPORATION","DHS":"WisdomTree U.S. High Dividend Fund","DHT":"DHT HOLDINGS INC","DHX":"DHI Group, Inc.","DIA":"SPDR DOW JONES INDL AVERAGE","DIAL":"Columbia Diversified Fixed Income Allocation ETF","DIBS":"1stdibs.com, Inc.","DIHP":"Dimensional International High Profitability ETF","DIM":"WisdomTree International MidCap Dividend Fund","DIN":"Dine Brands Global, Inc. Common Stock","DINO":"HF SINCLAIR CORP","DINT":"Davis Select International ETF","DIOD":"Diodes Incorporated","DIS":"DISNEY WALT CO","DISV":"Dimensional International Small Cap Value ETF","DIV":"Global X Super Dividend ETF","DIVB":"iShares Core Dividend ETF","DIVI":"Franklin International Core Dividend Tilt Index ETF","DIVO":"Amplify CWP Enhanced Dividend Income ETF","DIVZ":"Polen Dividend Income ETF","DJAN":"FT Vest U.S. Equity Deep Buffer ETF - January","DJCO":"Daily Journal Corp. (S.C.)","DJD":"Invesco Dow Jones Industrial Average Dividend ETF","DJIA":"Global X Dow 30 Covered Call ETF","DJP":"iPath Bloomberg Commodity Index Total Return ETN","DJT":"TRUMP MEDIA &amp; TECHNOLOGY GRO","DJUN":"FT Vest U.S. Equity Deep Buffer ETF - June","DK":"DELEK US HLDGS INC NEW","DKL":"Delek Logistics Partners, L.P.","DKNG":"DRAFTKINGS INC NEW","DKS":"DICKS SPORTING GOODS INC","DLB":"DOLBY LABORATORIES INC","DLN":"WisdomTree U.S. LargeCap Dividend Fund","DLO":"DLocal Limited","DLR":"DIGITAL RLTY TR INC","DLS":"WisdomTree International SmallCap Fund","DLTR":"DOLLAR    TREE    INC","DLX":"Deluxe Corporation","DMAA":"Drugs Made In America Acquisition Corp.","DMAC":"DIAMEDICA THERAPEUTICS INC","DMAR":"FT Vest U.S. Equity Deep Buffer ETF - March","DMAY":"FT Vest U.S. Equity Deep Buffer ETF - May","DMBS":"DoubleLine Mortgage ETF","DMLP":"DORCHESTER MINERALS LP","DMRC":"Digimarc Corporation","DMXF":"iShares ESG Advanced MSCI EAFE ETF","DNA":"GINKGO BIOWORKS HOLDINGS INC","DNL":"WisdomTree Global ex-U.S. Quality Growth Fund","DNLI":"DENALI THERAPEUTICS INC","DNN":"DENISON MINES CORP","DNOV":"FT Vest U.S. Equity Deep Buffer ETF - November","DNOW":"DNOW INC","DNTH":"DIANTHUS THERAPEUTICS INC","DNUT":"Krispy Kreme Inc - US","DOC":"HEALTHPEAK PROPERTIES INC","DOCN":"DigitalOcean Holdings, Inc.","DOCS":"DOXIMITY INC","DOCT":"FT Vest U.S. Equity Deep Buffer ETF - October","DOCU":"DOCUSIGN INC","DOG":"ProShares Short Dow30","DOL":"WisdomTree True Developed International Fund","DOLE":"DOLE PLC","DOMO":"Domo, Inc.","DON":"WisdomTree U.S. MidCap Dividend Fund","DOO":"BRP Inc.","DORM":"Dorman Products, Inc.","DOUG":"DOUGLAS ELLIMAN INC","DOV":"DOVER CORP","DOW":"DOW INC","DOX":"Amdocs Limited","DPRO":"Draganfly Inc.","DPST":"Direxion Daily Regional Banks Bull 3X Shares","DPZ":"DOMINOS PIZZA INC","DQ":"DAQO NEW ENERGY CORP","DRD":"DRDGOLD Limited","DRH":"Diamondrock Hospitality Company","DRI":"DARDEN RESTAURANTS INC","DRIV":"Global X Autonomous & Electric Vehicles ETF","DRLL":"Strive U.S. Energy ETF","DRS":"LEONARDO DRS INC","DRSK":"Aptus Defined Risk ETF","DRTS":"Alpha Tau Medical Ltd.","DRUG":"Bright Minds Biosciences Inc.","DRVN":"DRIVEN BRANDS HLDGS INC","DSAC":"Daedalus Special Acquisition Corp.","DSCO":"DoubleLine Securitized Credit ETF","DSGN":"DESIGN THERAPEUTICS INC","DSGR":"Distribution Solutions Group, Inc.","DSGX":"DESCARTES SYS GROUP INC","DSI":"iShares ESG MSCI KLD 400 ETF","DSP":"Viant Technology Inc.","DSTL":"Distillate U.S. Fundamental Stability & Value ETF","DSX":"Diana Shipping inc.","DT":"DYNATRACE INC","DTCR":"Global X Data Center & Digital Infrastructure ETF","DTD":"WisdomTree U.S. Total Dividend Fund","DTE":"DTE ENERGY CO","DTH":"WisdomTree International High Dividend Fund","DTM":"DT MIDSTREAM INC","DUBS":"Aptus Large Cap Enhanced Yield ETF","DUHP":"Dimensional US High Profitability ETF","DUK":"DUKE ENERGY CORP NEW","DUOL":"DUOLINGO INC","DUOT":"DUOS TECHNOLOGIES GROUP INC","DUSA":"Davis Select U.S. Equity ETF","DUSB":"Dimensional Ultrashort Fixed Income ETF","DUST":"Direxion Daily Gold Miners Index Bear 2X Shares","DV":"DOUBLEVERIFY HLDGS INC","DVA":"DAVITA       INC","DVAL":"BrandywineGLOBAL-Dynamic US Large Cap Value ETF","DVLT":"Datavault AI Inc.","DVN":"DEVON ENERGY CORP NEW","DVS":"Dolly Varden Silver Corporation","DVY":"ISHARES TR","DVYE":"iShares Emerging Markets Dividend Index Fund Exchange Traded Fund","DWAS":"Invesco Dorsey Wright SmallCap Momentum ETF","DWLD":"Davis Select Worldwide ETF","DWM":"WisdomTree International Equity Fund","DWX":"State Street SPDR S&P International Dividend ETF","DX":"Dynex Capital, Inc.","DXC":"DXC Technology Company","DXCM":"DEXCOM INC","DXIV":"Dimensional International Vector Equity ETF","DXJ":"WisdomTree Japan Hedged Equity Fund","DXPE":"DXP Enterprises, Inc.","DXUV":"Dimensional US Vector Equity ETF","DY":"Dycom Industries, Inc.","DYN":"DYNE THERAPEUTICS INC","DYNF":"iShares U.S. Equity Factor Rotation Active ETF","E":"ENI S.p.A.","EA":"ELECTRONIC ARTS INC","EAF":"GrafTech International Ltd.","EAGG":"iShares ESG Aware U.S. Aggregate Bond ETF","EAGL":"Eagle Capital Select Equity ETF","EAT":"Brinker International, Inc.","EB":"EVENTBRITE INC","EBAY":"EBAY INC","EBC":"EASTERN BANKSHARES INC","EBF":"Ennis, Inc.","EBMT":"Eagle Bancorp Montana, Inc.","EBND":"SPDR Bloomberg Emerging Markets Local Bond ETF","EBS":"EMERGENT BIOSOLUTIONS INC","EC":"ECOPETROL S A","ECG":"Everus Construction Group, Inc.","ECH":"iShares MSCI Chile ETF","ECL":"ECOLAB INC","ECO":"Okeanis Eco Tankers Corp.","ECON":"Columbia Research Enhanced Emerging Economies ETF","ECOW":"Pacer Emerging Markets Cash Cows 100 ETF","ECPG":"Encore Capital Group Inc","ECVT":"ECOVYST INC","ED":"CONSOLIDATED EDISON INC","EDC":"Direxion Emerging Markets Bull 3X Shares","EDEN":"iShares MSCI Denmark ETF","EDGF":"3EDGE Dynamic Fixed Income ETF","EDGH":"3EDGE Dynamic Hard Assets ETF","EDGI":"3EDGE Dynamic International Equity ETF","EDIT":"EDITAS MEDICINE INC","EDIV":"State Street SPDR S&P Emerging Markets Dividend ETF","EDN":"Empresa Distribuidora Y Comercializadora Norte S.A. (Edenor)","EDOW":"First Trust Dow 30 Equal Weight ETF","EDU":"New Oriental Education & Technology Group, Inc. Sponsored","EDV":"Vanguard Extended Duration Treasury ETF","EE":"EXCELERATE ENERGY INC","EEFT":"EURONET WORLDWIDE INC","EELV":"Invesco S&P Emerging Markets Low Volatility ETF","EEM":"ISHARES TR","EEMA":"iShares MSCI Emerging Markets Asia ETF","EEMS":"iShares MSCI Emerging Markets Small Cap ETF","EEMV":"iShares MSCI Emerging Markets Min Vol Factor ETF","EES":"WisdomTree U.S. SmallCap Fund","EFA":"ISHARES TR","EFAA":"Invesco MSCI EAFE Income Advantage ETF","EFAV":"iShares MSCI EAFE Min Vol Factor ETF","EFAX":"State Street SPDR MSCI EAFE Fossil Fuel Reserves Free ETF","EFC":"Ellington Financial Inc.","EFG":"iShares MSCI EAFE Growth ETF","EFIV":"State Street SPDR S&P 500 ESG ETF","EFSC":"Enterprise Financial Services Corporation","EFSI":"Eagle Financial Services Inc","EFV":"iShares MSCI EAFE Value ETF","EFX":"EQUIFAX INC","EFXT":"ENERFLEX LTD","EG":"Everest Group, Ltd.","EGAN":"eGain Corporation","EGBN":"Eagle Bancorp, Inc.","EGHT":"8x8 Inc","EGO":"ELDORADO     GOLD  CORP  NEW","EGP":"Eastgroup Properties, Inc.","EGY":"VAALCO Energy, Inc.","EHAB":"Enhabit, Inc.","EHC":"ENCOMPASS     HEALTH       CORP","EIDO":"iShares MSCI Indonesia ETF","EIG":"Employers Holdings Inc","EIKN":"Eikon Therapeutics, Inc.","EINC":"VanEck Energy Income ETF","EIPI":"FT Energy Income Partners Enhanced Income ETF","EIS":"iShares MSCI Israel ETF","EIX":"Edison International","EL":"LAUDER ESTEE COS INC","ELA":"Envela Corporation","ELAN":"ELANCO ANIMAL HEALTH INC","ELCV":"Strategy Shares Eventide High Dividend ETF","ELD":"WisdomTree Emerging Markets Local Debt Fund","ELDN":"Eledon Pharmaceuticals, Inc.","ELE":"Elemental Royalty Corporation","ELF":"E L F BEAUTY INC","ELFY":"ALPS Electrification Infrastructure ETF","ELM":"Elm Market Navigator ETF","ELMD":"Electromed, Inc.","ELPC":"Companhia Paranaense de Energia (COPEL)","ELS":"Equity Lifestyle Properties, Inc.","ELTX":"Elicio Therapeutics, Inc.","ELV":"ELEVANCE HEALTH INC FORMERLY","ELVA":"Electrovaya Inc.","ELVN":"Enliven Therapeutics Inc","EMA":"Emera Incorporated","EMAT":"Evolution Metals & Technologies Corp.","EMB":"ISHARES TR","EMBC":"Embecta Corp.","EMBJ":"Embraer S.A.","EMBX":"VanEck Emerging Markets Bond ETF","EME":"EMCOR GROUP INC","EMEQ":"Nomura Focused Emerging Markets Equity ETF","EMGF":"iShares Emerging Markets Equity Factor ETF","EMHC":"State Street SPDR Bloomberg Emerging Markets USD Bond ETF","EMHY":"iShares J.P. Morgan EM High Yield Bond ETF","EMKT":"Lazard Emerging Markets Opportunities ETF","EMLC":"VanEck J. P. Morgan EM Local Currency Bond ET","EMLP":"First Trust North American Energy Infrastructure Fund","EMMF":"WisdomTree Emerging Markets Multifactor Fund","EMN":"EASTMAN CHEM CO","EMNT":"PIMCO Enhanced Short Maturity Active ESG Exchange-Traded Fund","EMOP":"AB Emerging Markets Opportunities ETF","EMPD":"Empery Digital Inc.","EMQQ":"EMQQ The Emerging Markets Internet ETF","EMR":"EMERSON ELEC CO","EMXC":"iShares MSCI Emerging Markets ex China ETF","ENB":"ENBRIDGE INC","ENFR":"Alerian Energy Infrastructure ETF","ENGN":"enGene Holdings Inc.","ENIC":"Enel Chile S.A.","ENLT":"Enlight Renewable Energy Ltd.","ENLV":"Enlivex Therapeutics Ltd.","ENOV":"ENOVIS CORPORATION","ENPH":"ENPHASE ENERGY INC","ENR":"Energizer Holdings, Inc.","ENS":"ENERSYS","ENSG":"The Ensign Group, Inc.","ENTA":"ENANTA PHARMACEUTICALS INC","ENTG":"ENTEGRIS INC","ENVA":"Enova International, Inc.","ENVX":"ENOVIX CORPORATION","EOG":"EOG RES INC","EOLS":"Evolus, Inc. Common Stock","EOSE":"EOS ENERGY ENTERPRISES INC","EPAC":"Enerpac Tool Group Corp - US","EPAM":"EPAM Systems, Inc.","EPC":"Edgewell Personal Care Company","EPD":"ENTERPRISE PRODS PARTNERS L","EPHE":"iShares MSCI Philippines ETF","EPI":"WisdomTree India Earnings Fund","EPM":"Evolution Petroleum Corporation, Inc.","EPOL":"iShares MSCI Poland ETF","EPP":"iShares MSCI Pacific Ex-Japan Index Fund","EPR":"EPR PPTYS","EPRT":"Essential Properties Realty Trust, Inc.","EPRX":"Eupraxia Pharmaceuticals Inc.","EPS":"WisdomTree U.S. LargeCap Fund","EPSN":"Epsilon Energy Ltd.","EPU":"iShares MSCI Peru and Global Exposure ETF","EQAL":"Invesco Russell 1000 Equal Weight ETF","EQBK":"Equity Bancshares, Inc.","EQH":"Equitable Holdings, Inc.","EQIN":"Columbia U.S. Equity Income ETF","EQIX":"Equinix, Inc.","EQL":"ALPS Equal Sector Weight ETF","EQNR":"EQUINOR ASA","EQPT":"EquipmentShare.com Inc","EQR":"EQUITY RESIDENTIAL","EQT":"EQT CORP","EQTY":"Kovitz Core Equity ETF","EQWL":"Invesco S&P 100 Equal Weight ETF","EQX":"EQUINOX GOLD CORP","ERAS":"ERASCA INC","ERIC":"Ericsson","ERIE":"Erie Indemnity Company","ERII":"Energy Recovery, Inc.","ERO":"ERO COPPER CORP","ERX":"ENTREPRENEURSHARES SERIES TR","ES":"Eversource Energy (D/B/A)","ESAB":"ESAB CORPORATION","ESE":"Esco Technologies Inc - US","ESEA":"Euroseas Ltd.","ESGD":"iShares ESG Aware MSCI EAFE ETF","ESGE":"iShares ESG Aware MSCI EM ETF","ESGU":"iShares ESG Aware MSCI USA ETF","ESGV":"Vanguard ESG U.S. Stock ETF","ESI":"ELEMENT SOLUTIONS INC","ESLT":"Elbit Systems Ltd.","ESML":"iShares ESG Aware MSCI USA Small-Cap ETF","ESN":"Essential 40 Stock ETF","ESNT":"ESSENT GROUP LTD","ESOA":"Energy Services of America Corporation","ESP":"Espey Mfg. & Electronics Corp.","ESPO":"VanEck Video Gaming and eSports ETF","ESPR":"Esperion Therapeutics, Inc.","ESQ":"Esquire Financial Holdings, Inc.","ESRT":"Empire State Realty Trust, Inc.","ESS":"Essex Property Trust, Inc.","ESTA":"Establishment Labs Holdings Inc.","ESTC":"ELASTIC N V","ESUM":"Eventide US Market ETF","ET":"ENERGY TRANSFER L P","ETD":"Ethan Allen Interiors Inc.","ETH":"Grayscale Ethereum Staking Mini ETF Shares","ETHA":"ISHARES ETHEREUM TR","ETHE":"Grayscale Ethereum Staking ETF Shares","ETHM":"Dynamix Corporation","ETHT":"ProShares Ultra Ether ETF","ETHU":"2x Ether ETF","ETHV":"VanEck Ethereum ETF","ETHW":"Bitwise Ethereum ETF","ETN":"Eaton Corporation, PLC","ETON":"ETON PHARMACEUTICALS INC","ETOR":"ETORO GROUP LTD","ETR":"ENTERGY CORP NEW","ETSY":"ETSY INC","EU":"enCore Energy Corp.","EUAD":"Select STOXX Europe Aerospace & Defense ETF","EUFN":"iShares MSCI Europe Financials ETF","EUHY":"iShares Euro High Yield Corporate Bond USD Hedged ETF","EUSA":"iShares MSCI USA Equal Weighted ETF","EUSB":"iShares ESG Advanced Universal USD Bond ETF","EVC":"Entravision Communications Corporation","EVCM":"EverCommerce Inc.","EVER":"EverQuote, Inc.","EVEX":"EVE HLDG INC","EVGO":"EVGO INC","EVH":"EVOLENT HEALTH INC","EVI":"EVI Industries, Inc.","EVIM":"Eaton Vance Intermediate Municipal Income ETF","EVLN":"Eaton Vance Floating-Rate ETF","EVLV":"Evolv Technologies Holdings, Inc.","EVMN":"Evommune, Inc.","EVR":"EVERCORE INC","EVRG":"EVERGY INC","EVSB":"Eaton Vance Ultra-Short Income ETF","EVSD":"Eaton Vance Short Duration Income ETF","EVSM":"Eaton Vance Short Duration Municipal Income ETF","EVTC":"Evertec, Inc.","EVTL":"VERTICAL AEROSPACE LTD","EVTR":"Eaton Vance Total Return Bond ETF","EVUS":"iShares ESG Aware MSCI USA Value ETF","EW":"EDWARDS LIFESCIENCES CORP","EWA":"iShares MSCI Australia Index Fund","EWBC":"EAST WEST BANCORP INC","EWC":"iShares MSCI Canada Index Fund","EWCZ":"European Wax Center, Inc.","EWD":"iShares MSCI Sweden ETF","EWG":"iShares MSCI Germany Index Fund","EWH":"iShares MSCI Hong Kong Index Fund","EWI":"iShares MSCI Italy ETF","EWJ":"iShares MSCI Japan Index Fund","EWJV":"iShares MSCI Japan Value ETF","EWL":"iShares MSCI Switzerland ETF","EWM":"iShares MSCI Malaysia Index Fund","EWN":"iShares MSCI Netherlands Index Fund","EWO":"iShares MSCI Austria ETF","EWP":"iShares MSCI Spain ETF","EWQ":"iShares MSCI France Index Fund","EWS":"iShares MSCI Singapore ETF","EWT":"iShares MSCI Taiwan ETF","EWTX":"EDGEWISE THERAPEUTICS INC","EWU":"iShares MSCI United Kingdom ETF","EWW":"iShares MSCI Mexico ETF","EWX":"State Street SPDR S&P Emerging Markets Small Cap ETF","EWY":"iShares MSCI South Korea ETF","EWZ":"iShares MSCI Brazil ETF","EWZS":"iShares MSCI Brazil Small-Cap ETF","EXAS":"EXACT SCIENCES CORP","EXC":"EXELON CORP","EXE":"EXPAND ENERGY CORPORATION","EXEL":"EXELIXIS INC","EXFY":"Expensify, Inc.","EXI":"iShares Global Industrials ETF","EXK":"Endeavour Silver Corp - US","EXLS":"EXLSERVICE HOLDINGS INC","EXP":"EAGLE MATLS INC","EXPD":"EXPEDITORS INTL WASH INC","EXPE":"EXPEDIA GROUP INC","EXPI":"eXp World Holdings, Inc.","EXPO":"Exponent Inc - US","EXR":"Extra Space Storage, Inc.","EXTR":"EXTREME NETWORKS","EYE":"NATIONAL VISION HLDGS INC","EYLD":"Cambria Emerging Shareholder Yield ETF","EYPT":"EyePoint, Inc.","EZA":"iShares MSCI South Africa Index Fund","EZBC":"Franklin Templeton Digital Holdings Trust Shares of Franklin Bitcoin ETF","EZM":"WisdomTree U.S. MidCap Fund","EZPW":"Ezcorp Inc - US","EZU":"iShares MSCI Eurozone ETF","F":"FORD MTR CO","FA":"First Advantage Corporation","FAAR":"First Trust Alternative Absolute Return Strategy ETF","FAD":"First Trust Multi Cap Growth AlphaDEX Fund","FAF":"First American Corporation (New)","FALN":"iShares Fallen Angels USD Bond ETF","FAN":"First Trust Global Wind Energy ETF","FANG":"DIAMONDBACK ENERGY INC","FAPR":"FT Vest U.S. Equity Buffer ETF - April","FAS":"Direxion Financial Bull 3X Shares","FAST":"FASTENAL CO","FATE":"Fate Therapeutics, Inc.","FAUG":"FT Vest U.S. Equity Buffer ETF - August","FAZ":"Direxion Financial Bear 3X Shares","FBCG":"Fidelity Blue Chip Growth ETF","FBCV":"Fidelity Blue Chip Value ETF","FBIN":"FORTUNE BRANDS INNOVATIONS I","FBIO":"Fortress Biotech, Inc.","FBIZ":"First Business Financial Services, Inc.","FBK":"FB Financial Corporation","FBL":"GraniteShares 2x Long META Daily ETF","FBLA":"FB Bancorp, Inc.","FBNC":"First Bancorp","FBND":"Fidelity Total Bond ETF","FBOT":"Fidelity Disruptive Automation ETF","FBP":"FIRST BANCORP P R","FBRT":"Franklin BSP Realty Trust, Inc.","FBRX":"FORTE BIOSCIENCES INC","FBT":"First Trust Amex Biotech Index Fund","FBTC":"FIDELITY WISE ORIGIN BITCOIN","FBY":"YieldMax META Option Income Strategy ETF","FC":"Franklin Covey Company","FCA":"First Trust China AlphaDEX Fund","FCAL":"First Trust California Municipal High income ETF","FCBC":"First Community Bankshares, Inc.","FCCO":"First Community Corporation","FCEL":"FuelCell Energy, Inc.","FCF":"First","FCFS":"FIRSTCASH HOLDINGS INC","FCG":"First Trust Natural Gas ETF","FCN":"FTI CONSULTING INC","FCNCA":"First Citizens BancShares, Inc.","FCOM":"Fidelity MSCI Communication Services Index ETF","FCOR":"Fidelity Corporate Bond ETF","FCPI":"Fidelity Stocks for Inflation ETF","FCPT":"Four Corners Property Trust, Inc.","FCRS":"FUTURECREST ACQUISITION CORP","FCVT":"First Trust SSI Strategic Convertible Securities ETF","FCX":"FREEPORT-MCMORAN INC","FDD":"First Trust STOXX European Select Dividend Index Fund","FDEC":"FT Vest U.S. Equity Buffer ETF - December","FDEM":"Fidelity Emerging Markets Multifactor ETF","FDEV":"Fidelity Emerging Markets Multifactor ETF","FDG":"American Century Focused Dynamic Growth ETF","FDHY":"Fidelity Enhanced High Yield ETF","FDIG":"Fidelity Crypto Industry and Digital Payments ETF","FDIS":"Fidelity MSCI Consumer Discretionary Index ETF","FDLO":"Fidelity Low Volatility Factor ETF","FDLS":"Inspire Fidelis Multi Factor ETF","FDM":"First Trust DJ Select MicroCap ETF","FDMO":"Fidelity Momentum Factor ETF","FDMT":"4D MOLECULAR THERAPEUTICS IN","FDN":"FIRST TR EXCHANGE TRADED FD","FDP":"Fresh Del Monte Produce, Inc.","FDRR":"Fidelity Dividend ETF for Rising Rates","FDS":"FACTSET RESH SYS INC","FDT":"First Trust Developed Markets Ex-US AlphaDEX Fund","FDTX":"Fidelity Disruptive Technology ETF","FDUS":"Fidus Investment Corporation","FDV":"Federated Hermes U.S. Strategic Dividend ETF","FDVV":"Fidelity High Dividend ETF","FDX":"FEDEX CORP","FE":"FIRSTENERGY CORP","FEGE":"First Eagle Global Equity ETF","FEIM":"FREQUENCY ELECTRS INC","FELC":"Fidelity Enhanced Large Cap Core ETF","FELE":"Franklin Electric Co., Inc.","FELG":"Fidelity Enhanced Large Cap Growth ETF","FELV":"Fidelity Enhanced Large Cap Value ETF","FEM":"First Trust Emerging Markets AlphaDEX Fund","FEMB":"First Trust Emerging Markets Local Currency Bond ETF","FEMS":"First Trust Emerging Markets Small Cap AlphaDEX Fund","FENC":"FENNEC PHARMACEUTICALS INC","FENI":"Fidelity Enhanced International ETF","FENY":"Fidelity MSCI Energy Index ETF","FEOE":"First Eagle Overseas Equity ETF","FEP":"First Trust Europe AlphaDEX Fund","FEPI":"REX FANG & Innovation Equity Premium Income ETF","FER":"FERROVIAL SE","FERG":"FERGUSON ENTERPRISES INC","FESM":"Fidelity Enhanced Small Cap ETF","FET":"Forum Energy Technologies, Inc.","FETH":"Fidelity Ethereum Fund","FEX":"First Trust Large Cap Core AlphaDEX Fund","FEZ":"State Street SPDR EURO STOXX 50 ETF","FF":"FutureFuel Corp.","FFAI":"Faraday Future Intelligent Electric Inc.","FFBC":"First Financial Bancorp.","FFEB":"FT Vest U.S. Equity Buffer ETF - February","FFIC":"Flushing Financial Corporation","FFIN":"First Financial Bankshares, Inc.","FFIV":"F5, Inc.","FFLC":"Fidelity Fundamental Large Cap Core ETF","FFLG":"Fidelity Fundamental Large Cap Growth ETF","FFOG":"Franklin Focused Growth ETF","FFOX":"FundX Future Fund Opportunities ETF","FFSM":"Fidelity Fundamental Small-Mid Cap ETF","FFWM":"First Foundation Inc.","FG":"F&G Annuities & Life, Inc.","FGD":"First Trust DJ Global Select Dividend","FGDL":"Franklin Responsibly Sourced Gold ETF","FHB":"First Hawaiian, Inc.","FHI":"FEDERATED HERMES INC","FHLC":"FIDELITY COVINGTON TRUST","FHN":"FIRST  HORIZON    CORPORATION","FIBK":"First Interstate BancSystem, Inc.","FICO":"FAIR ISAAC CORP","FICS":"First Trust International Developed Capital Strength ETF","FID":"First Trust S&P International Dividend Aristocrats ETF","FIDI":"Fidelity International High Dividend ETF","FIDU":"Fidelity MSCI Industrials Index ETF","FIG":"FIGMA INC","FIGB":"Fidelity Investment Grade Bond ETF","FIGR":"Figure Technology Solutions Inc","FIGS":"FIGS INC","FIHL":"Fidelis Insurance Holdings Limited","FIIG":"First Trust Intermediate Duration Investment Grade Corporate ETF","FINV":"FinVolution Group","FINX":"Global X FinTech ETF","FIP":"FTAI Infrastructure Inc.","FIS":"FIDELITY NATL INFORMATION SV","FISI":"Financial Institutions, Inc.","FISR":"State Street Fixed Income Sector Rotation ETF","FISV":"FISERV INC","FITB":"FIFTH THIRD BANCORP","FITE":"State Street SPDR S&P Kensho Future Security ETF","FIVA":"Fidelity International Value Factor ETF","FIVE":"FIVE BELOW INC","FIVN":"FIVE9 INC","FIW":"First Trust Water ETF","FIX":"COMFORT SYS USA INC","FIXD":"First Trust Smith Opportunistic Fixed Income ETF","FIZZ":"National Beverage Corp.","FJAN":"FT Vest U.S. Equity Buffer ETF - January","FJET":"Starfighters Space, Inc.","FJP":"First Trust Japan AlphaDEX Fund","FJUL":"FT Vest U.S. Equity Buffer ETF - July","FJUN":"FT Vest U.S. Equity Buffer ETF - June","FLBL":"Franklin Senior Loan ETF","FLBR":"Franklin FTSE Brazil ETF","FLCA":"Franklin FTSE Canada ETF","FLCB":"Franklin U.S. Core Bond ETF","FLCG":"Federated Hermes MDT Large Cap Growth ETF","FLCH":"Franklin FTSE China ETF","FLCO":"Franklin Investment Grade Corporate ETF","FLDR":"Fidelity Low Duration Bond Factor ETF","FLEE":"Franklin FTSE Europe ETF","FLEX":"FLEX LTD","FLG":"Flagstar Bank, N.A.","FLGB":"Franklin FTSE","FLGT":"Fulgent Genetics, Inc.","FLGV":"Franklin U.S. Treasury Bond ETF","FLHY":"Franklin High Yield Corporate ETF","FLIA":"Franklin International Aggregate Bond ETF","FLIN":"Franklin FTSE India ETF","FLJH":"Franklin FTSE Japan Hedged ETF","FLJP":"Franklin FTSE Japan ETF","FLKR":"Franklin FTSE South Korea ETF","FLMI":"Franklin Dynamic Municipal Bond ETF","FLNC":"FLUENCE ENERGY INC","FLNG":"FLEX LNG Ltd.","FLO":"FLOWERS FOODS INC","FLOC":"Flowco Holdings Inc.","FLOT":"iShares Floating Rate Bond ETF","FLQL":"Franklin U.S. Large Cap Multifactor Index ETF","FLQM":"Franklin U.S. Mid Cap Multifactor Index ETF","FLR":"FLUOR CORP NEW","FLRN":"State Street SPDR Bloomberg Investment Grade Floating Rate ETF","FLRT":"Pacer Aristotle Pacific Floating Rate High Income ETF","FLS":"FLOWSERVE CORP","FLSP":"Franklin Systematic Style Premia ETF","FLTB":"Fidelity Limited Term Bond ETF","FLTR":"VanEck IG Floating Rate ETF","FLTW":"Franklin FTSE Taiwan ETF","FLUD":"Franklin Ultra Short Bond ETF","FLUT":"FLUTTER ENTMT PLC","FLV":"American Century Focused Large Cap Value ETF","FLWS":"1-800-FLOWERS.COM, Inc.","FLXR":"TCW Flexible Income ETF","FLXS":"Flexsteel Industries, Inc.","FLY":"Firefly Aerospace Inc - US","FLYW":"FLYWIRE CORPORATION","FMAG":"Fidelity Magellan ETF","FMAO":"Farmers & Merchants Bancorp, Inc.","FMAR":"FT Vest U.S. Equity Buffer ETF - March","FMAT":"Fidelity MSCI Materials Index ETF","FMAY":"FT Vest U.S. Equity Buffer ETF - May","FMB":"First Trust Managed Municipal ETF","FMBH":"First Mid Bancshares, Inc.","FMC":"FMC Corporation","FMDE":"Fidelity Enhanced Mid Cap ETF","FMF":"First Trust Managed Futures Strategy Fund","FMHI":"First Trust Municipal High Income ETF","FMNB":"Farmers National Banc Corp.","FMS":"FRESENIUS MEDICAL CARE AG","FMUB":"Fidelity Municipal Bond Opportunities ETF","FMX":"Fomento Economico Mexicano S.A.B. de C.V.","FN":"FABRINET","FNB":"F.N.B. Corporation","FNCL":"Fidelity MSCI Financials Index ETF","FND":"FLOOR &amp; DECOR HLDGS INC","FNDA":"Schwab Fundamental U.S. Small Company ETF","FNDB":"Schwab Fundamental U.S. Broad Market ETF","FNDC":"Schwab Fundamental International Small Equity ETF","FNDE":"Schwab Fundamental Emerging Markets Equity ETF","FNDF":"Schwab Fundamental International Equity ETF","FNDX":"Schwab Fundamental U.S. Large Company ETF","FNF":"Fidelity National Financial Inc - US","FNGD":"MicroSectors FANG Index -3X Inverse Leveraged ETNs due January 8, 2038","FNGG":"Direxion Daily NYSE FANG+ Bull 2X Shares","FNGO":"MicroSectors FANG Index 2X Leveraged ETNs due January 8, 2038","FNGS":"MicroSectors FANG ETNs due January 8, 2038","FNGU":"MicroSectors FANG+ 3X Leveraged ETNs","FNKO":"FUNKO INC","FNOV":"FT Vest U.S. Equity Buffer ETF - November","FNV":"FRANCO NEV CORP","FNX":"First Trust Mid Cap Core AlphaDEX Fund","FNY":"First Trust Mid Cap Growth AlphaDEX Fund","FOA":"Finance of America Companies Inc.","FOCT":"FT Vest U.S. Equity Buffer ETF - October","FOLD":"AMICUS THERAPEUTICS INC","FONR":"FONAR CORP","FOR":"Forestar Group Inc","FORM":"FORMFACTOR INC","FORR":"Forrester Research, Inc.","FOSL":"FOSSIL GROUP INC","FOUR":"SHIFT4 PMTS INC","FOX":"Fox Corporation","FOXA":"FOX CORP","FOXF":"FOX FACTORY HLDG CORP","FPAG":"FPA Global Equity ETF","FPE":"First Trust Preferred Securities and Income ETF","FPEI":"First Trust Institutional Preferred Securities and Income ETF","FPH":"Five Point Holdings, LLC","FPS":"Forgent Power Solutions, Inc.","FPX":"First Trust US Equity Opportunities ETF","FQAL":"Fidelity Quality Factor ETF","FR":"First Industrial Realty Trust, Inc.","FRAF":"Franklin Financial Services Corporation","FRBA":"First Bank","FRDM":"Freedom 100 Emerging Markets ETF","FREL":"Fidelity MSCI Real Estate Index ETF","FRGE":"FORGE GLOBAL HOLDINGS INC","FRHC":"Freedom Holding Corp.","FRME":"First Merchants Corporation","FRMI":"Fermi Inc","FRO":"FRONTLINE PLC","FROG":"JFROG LTD","FRPH":"FRP Holdings, Inc.","FRPT":"FRESHPET INC","FRSH":"FRESHWORKS INC","FRST":"Primis Financial Corp.","FRT":"Federal Realty Investment Trust","FRTY":"Alger Mid Cap 40 ETF","FSBC":"Five Star Bancorp","FSCC":"Federated Hermes MDT Small Cap Core ETF","FSEC":"Fidelity Investment Grade Securitized ETF","FSEP":"FT Vest U.S. Equity Buffer ETF - September","FSIG":"First Trust Limited Duration Investment Grade Corporate ETF","FSK":"FS KKR Capital Corp.","FSLR":"FIRST SOLAR INC","FSLY":"FASTLY INC","FSM":"Fortuna Mining Corp.","FSMB":"First Trust Short Duration Managed Municipal ETF","FSMD":"Fidelity Small-Mid Multifactor ETF","FSS":"FEDERAL SIGNAL CORP","FSTA":"Fidelity MSCI Consumer Staples Index ETF","FSTR":"L.B. Foster Company","FSUN":"FirstSun Capital Bancorp","FSV":"FirstService Corp - US","FSYD":"Fidelity Sustainable High Yield ETF","FTA":"First Trust Large Cap Value AlphaDEX Fund","FTAI":"FTAI   AVIATION     LTD","FTC":"First Trust Large Cap Growth AlphaDEX Fund","FTCA":"Franklin California Municipal Income ETF","FTCB":"First Trust Core Investment Grade ETF","FTCI":"FTC Solar, Inc.","FTCS":"First Trust Capital Strength ETF","FTDR":"Frontdoor Inc - US","FTEC":"Fidelity MSCI Information Technology Index ETF","FTGC":"First Trust Global Tactical Commodity Strategy Fund","FTGS":"First Trust Growth Strength ETF","FTHI":"First Trust BuyWrite Income ETF","FTI":"TECHNIPFMC PLC","FTK":"Flotek Industries, Inc.","FTLS":"First Trust Long/Short Equity","FTMH":"Franklin Municipal High Yield ETF","FTMS":"Franklin Short-Term Municipal Income ETF","FTNJ":"Franklin New Jersey Municipal Income ETF","FTNT":"FORTINET INC","FTNY":"Franklin New York Municipal Income ETF","FTQI":"First Trust Nasdaq BuyWrite Income ETF","FTRB":"Federated Hermes Total Return Bond ETF","FTRE":"Fortrea Holdings Inc.","FTRI":"First Trust Indxx Global Natural Resources Income ETF","FTS":"Fortis Inc.","FTSD":"Franklin Short Duration U.S. Government ETF","FTSL":"First Trust Senior Loan Fund","FTSM":"First Trust Enhanced Short Maturity ETF","FTV":"FORTIVE CORP","FTW":"EQV Ventures Acquisition Corp.","FTXL":"First Trust Nasdaq Semiconductor ETF","FTXO":"First Trust Nasdaq Bank ETF","FUBO":"FUBOTV INC","FUL":"H. B. Fuller Company","FULC":"FULCRUM THERAPEUTICS INC","FULT":"Fulton Financial Corporation","FUMB":"First Trust Ultra Short Duration Municipal ETF","FUN":"SIX FLAGS ENTERTAINMENT CORP","FUTU":"FUTU HLDGS LTD","FUTY":"Fidelity MSCI Utilities Index ETF","FV":"First Trust Dorsey Wright Focus 5 ETF","FVAL":"Fidelity Value Factor ETF","FVCB":"FVCBankcorp, Inc.","FVD":"First Trust VL Dividend","FVRR":"FIVERR INTL LTD","FWD":"AB Disruptors ETF","FWDI":"Forward Industries, Inc.","FWONA":"LIBERTY MEDIA CORP DEL","FWONK":"Liberty Media Corporation - Series C Liberty Formula One","FWRD":"FORWARD AIR CORP","FWRG":"FIRST WATCH RESTAURANT GROUP","FXA":"Invesco CurrencyShares Australian Dollar Trust","FXD":"First Trust Cons. Discret. AlphaDEX","FXE":"Invesco CurrencyShares Euro Currency Trust","FXF":"Invesco CurrencyShares Swiss Franc Trust","FXG":"First Trust Cons. Staples AlphaDEX","FXH":"First Trust Health Care AlphaDEX","FXI":"iShares China Large-Cap ETF","FXL":"First Trust Technology AlphaDEX","FXN":"First Trust Energy AlphaDEX Fund","FXNC":"First National Corporation","FXO":"First Trust Financials AlphaDEX","FXR":"First Trust Industrials AlphaDEX","FXU":"First Trust Utilities AlphaDEX Fund","FXY":"Invesco CurrencyShares Japanese Yen Trust","FXZ":"First Trust Materials AlphaDEX Fund","FYC":"First Trust Small Cap Growth AlphaDEX Fund","FYLD":"Cambria Foreign Shareholder Yield ETF","FYT":"First Trust Small Cap Value AlphaDEX Fund","FYX":"First Trust Small Cap Core AlphaDEX Fund","G":"GENPACT  LIMITED","GABC":"German American Bancorp, Inc.","GAIN":"Gladstone Investment Corporation - Business Development Company","GALT":"Galectin Therapeutics Inc.","GAMB":"Gambling.com Group Limited","GANX":"GAIN THERAPEUTICS INC","GAP":"Gap, Inc. (The)","GARP":"iShares MSCI USA Quality GARP ETF","GASS":"StealthGas, Inc.","GATX":"Gatx Corp - US","GAU":"Galiano Gold Inc.","GAUG":"FT Vest U.S. Equity Moderate Buffer ETF - August","GBCI":"Glacier Bancorp, Inc.","GBDC":"Golub Capital BDC, Inc.","GBFH":"GBank Financial Holdings Inc.","GBIL":"Goldman Sachs Access Treasury 0-1 Year ETF","GBTC":"Grayscale Bitcoin Trust (BTC)","GBTG":"GLOBAL BUSINESS TRAVEL GROUP","GBUG":"Sprott Active Gold & Silver Miners ETF","GBX":"Greenbrier Companies, Inc. (The)","GCAL":"Goldman Sachs Dynamic California Municipal Income ETF","GCC":"WisdomTree EnhancedContinuous Commodity Index Fund","GCMG":"GCM Grosvenor Inc.","GCO":"Genesco Inc.","GCOR":"Goldman Sachs Access U.S. Aggregate Bond ETF","GCOW":"Pacer Global Cash Cows Dividend ETF","GCT":"GigaCloud Technology Inc - US","GD":"GENERAL DYNAMICS CORP","GDDY":"GODADDY INC","GDE":"WisdomTree Efficient Gold Plus Equity Strategy Fund","GDEC":"FT Vest U.S. Equity Moderate Buffer ETF - December","GDEN":"Golden Entertainment, Inc.","GDLC":"Grayscale CoinDesk Crypto 5 ETF","GDMN":"WisdomTree Efficient Gold Plus Gold Miners Strategy Fund","GDOT":"Green Dot Corporation","GDRX":"GoodRx Holdings, Inc.","GDS":"GDS HLDGS LTD","GDX":"VANECK ETF TRUST","GDXJ":"VANECK ETF TRUST","GDXU":"MicroSectors Gold Miners 3x Leveraged ETN","GDXY":"YieldMax Gold Miners Option Income Strategy ETF","GDYN":"Grid Dynamics Holdings, Inc.","GE":"GE AEROSPACE","GEF":"Greif Inc.","GEHC":"GE HEALTHCARE TECHNOLOGIES I","GEL":"Genesis Energy, L.P.","GEM":"Goldman Sachs ActiveBeta Emerging Markets Equity ETF","GEME":"Pacific North of South EM Equity Active ETF","GEMI":"Gemini Space Station, Inc.","GEN":"GEN DIGITAL INC","GENI":"GENIUS SPORTS LIMITED","GEOS":"Geospace Technologies Corporation","GERN":"Geron Corporation","GETY":"Getty Images Holdings, Inc.","GEV":"GE VERNOVA INC","GEVO":"Gevo, Inc.","GFEB":"FT Vest U.S. Equity Moderate Buffer ETF - February","GFF":"GRIFFON CORP","GFI":"Gold Fields Limited","GFL":"GFL Environmental Inc. Subordinate voting shares, no par value","GFS":"GLOBALFOUNDRIES INC","GGAL":"GRUPO FINANCIERO GALICIA S.A","GGB":"Gerdau S.A.","GGG":"GRACO   INC","GGLL":"Direxion Daily GOOGL Bull 2X Shares","GGUS":"Goldman Sachs MarketBeta Russell 1000 Growth Equity ETF","GH":"GUARDANT HEALTH INC","GHC":"Graham Holdings Company","GHI":"Greystone Housing Impact Investors LP Beneficial","GHM":"GRAHAM HLDGS CO","GHRS":"GH Research PLC","GHYG":"iShares US & Intl High Yield Corp Bond ETF","GIB":"CGI Inc.","GIC":"Global Industrial Company","GIGB":"Goldman Sachs Access Investment Grade Corporate Bond ETF","GII":"State Street SPDR S&P Global Infrastructure ETF","GIII":"G-III Apparel Group, LTD.","GIL":"GILDAN ACTIVEWEAR INC","GILD":"GILEAD SCIENCES INC","GILT":"Gilat Satellite Networks Ltd.","GIS":"GENERAL MLS INC","GJAN":"FT Vest U.S. Equity Moderate Buffer ETF - January","GJUL":"FT Vest U.S. Equity Moderate Buffer ETF - July","GJUN":"FT Vest U.S. Equity Moderate Buffer ETF - June","GKOS":"GLAUKOS CORP","GL":"GLOBE LIFE INC","GLAD":"Gladstone Capital Corporation","GLBE":"GLOBAL E ONLINE LTD","GLD":"SPDR GOLD TR","GLDD":"Great Lakes Dredge & Dock Corporation","GLDG":"GoldMining Inc.","GLDI":"ETRACS Gold Shares Covered Call ETNs due February 2, 2033","GLDM":"WORLD GOLD TR","GLIBA":"GCI Liberty, Inc. - Series A GCI Group","GLIBK":"GCI Liberty, Inc. - Series C GCI Group","GLIN":"VanEck India Growth Leaders ETF","GLNG":"GOLAR LNG LTD","GLOB":"Globant S.A.","GLOF":"iShares Global Equity Factor ETF","GLP":"Global Partners LP","GLPG":"GALAPAGOS NV","GLPI":"Gaming and Leisure Properties, Inc.","GLRE":"Greenlight Reinsurance, Ltd.","GLRY":"Inspire Growth ETF","GLSI":"Greenwich LifeSciences, Inc.","GLTO":"GALECTO INC","GLTR":"abrdn Physical Precious Metals Basket Shares ETF","GLUE":"MONTE ROSA THERAPEUTICS INC","GLW":"CORNING INC","GLXY":"GALAXY DIGITAL INC.","GM":"GENERAL MTRS CO","GMAB":"Genmab A/S","GMAY":"FT Vest U.S. Equity Moderate Buffer ETF - May","GME":"GAMESTOP CORP NEW","GMED":"Globus Medical, Inc.","GMF":"State Street SPDR S&P Emerging Asia Pacific ETF","GMOI":"GMO International Value ETF","GMUB":"Goldman Sachs Municipal Income ETF","GNE":"Genie Energy Ltd.","GNK":"Genco Shipping & Trading Limited","GNL":"Global Net Lease Inc","GNMA":"iShares GNMA Bond ETF","GNOV":"FT Vest U.S. Equity Moderate Buffer ETF - November","GNR":"State Street SPDR S&P Global Natural Resources ETF","GNRC":"GENERAC HLDGS INC","GNTX":"GENTEX CORP","GNW":"GENWORTH FINL INC","GO":"Grocery Outlet Holding Corp.","GOAU":"US Global GO Gold and Precious Metal Miners ETF","GOCT":"FT Vest U.S. Equity Moderate Buffer ETF - October","GOEX":"Global X Gold Explorers ETF","GOGO":"GOGO INC","GOLD":"BARRICK MINING CORP","GOLF":"Acushnet Holdings Corp.","GOLY":"Strategy Shares Gold Enhanced Yield ETF","GOOD":"Gladstone Commercial Corporation - Real Estate Investment Trust","GOOG":"ALPHABET INC","GOOGL":"ALPHABET INC","GOOS":"Canada Goose Holdings Inc. Subordinate Voting Shares","GOOY":"YieldMax GOOGL Option Income Strategy ETF","GORO":"Gold Resource Corporation","GOVI":"Invesco Equal Weight 0-30 Year Treasury ETF","GOVT":"iShares U.S. Treasury Bond ETF","GOVZ":"iShares 25 Year Treasury STRIPS Bond ETF","GPAT":"GP-ACT III ACQUISITION CORP","GPC":"Genuine Parts Company","GPCR":"STRUCTURE THERAPEUTICS INC","GPGI":"GPGI, Inc.","GPI":"GROUP 1 AUTOMOTIVE INC","GPIQ":"Goldman Sachs Nasdaq-100 Premium Income ETF","GPIX":"Goldman Sachs S&P 500 Premium Income ETF","GPK":"GRAPHIC PACKAGING HLDG CO","GPN":"GLOBAL PMTS INC","GPOR":"GULFPORT ENERGY CORP","GPRE":"GREEN PLAINS INC","GPRK":"Geopark Ltd","GPRO":"GOPRO INC","GPZ":"VanEck Alternative Asset Manager ETF","GQGU":"GQG US Equity ETF","GQI":"Natixis Gateway Quality Income ETF","GQRE":"FlexShares Global Quality Real Estate Index Fund","GRAB":"GRAB HOLDINGS LIMITED","GRAL":"GRAIL INC","GRBK":"GREEN BRICK PARTNERS INC","GRC":"Gorman-Rupp Company (The)","GRDN":"Guardian Pharmacy Services, Inc.","GREK":"Global X MSCI Greece ETF","GRFS":"Grifols, S.A.","GRID":"First Trust NASDAQ Clean Edge Smart Grid Infrastructure Index Fund","GRMN":"GARMIN LTD","GRNB":"VanEck Green Bond ETF","GRND":"GRINDR INC","GRNJ":"Fundstrat Granny Shots US Small- & Mid-Cap ETF","GRNT":"Granite Ridge Resources, Inc.","GRNY":"Fundstrat Granny Shots US Large Cap ETF","GRO":"BRAZIL POTASH CORP","GROY":"Gold Royalty Corp.","GRPM":"Invesco S&P MidCap 400 GARP ETF","GRPN":"GROUPON INC","GRRR":"GORILLA TECHNOLOGY GROUP INC","GS":"GOLDMAN SACHS GROUP INC","GSAT":"GLOBALSTAR INC","GSBC":"Great Southern Bancorp, Inc.","GSBD":"Goldman Sachs BDC, Inc.","GSEE":"Goldman Sachs MarketBeta Emerging Markets Equity ETF","GSEP":"FT Vest U.S. Equity Moderate Buffer ETF - September","GSEW":"Goldman Sachs Equal Weight U.S. Large Cap Equity ETF","GSG":"iShares GSCI Commodity-Indexed Trust Fund","GSHD":"Goosehead Insurance, Inc.","GSIE":"Goldman Sachs ActiveBeta International Equity ETF","GSIT":"GSI TECHNOLOGY INC","GSK":"GSK PLC","GSL":"Global Ship Lease Inc - US","GSLC":"Goldman Sachs ActiveBeta U.S. Large Cap Equity ETF","GSM":"FERROGLOBE PLC","GSOL":"Grayscale Solana Staking ETF","GSSC":"GS ActiveBeta U.S. Small Cap Equity ETF","GSST":"Goldman Sachs Ultra Short Bond ETF","GSUS":"Goldman Sachs MarketBeta U.S. Equity ETF","GSWO":"Goldman Sachs ActiveBeta World Equity ETF","GSY":"Invesco Ultra Short Duration ETF","GT":"The Goodyear Tire & Rubber Company","GTE":"Gran Tierra Energy Inc.","GTEK":"Goldman Sachs Future Tech Leaders Equity ETF","GTES":"GATES INDL CORP PLC","GTIP":"Goldman Sachs Access Inflation Protected USD Bond ETF","GTLB":"GITLAB INC","GTLS":"CHART INDS INC","GTM":"ZOOMINFO TECHNOLOGIES INC","GTN":"GRAY MEDIA INC","GTO":"Invesco Total Return Bond ETF","GTOP":"Goldman Sachs Technology Opportunities ETF","GTX":"GARRETT MOTION INC","GTY":"Getty Realty Corporation","GUNR":"FlexShares Global Upstream Natural Resources Index Fund ETF","GUSE":"Goldman Sachs Enhanced U.S. Equity ETF","GUSH":"Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares","GVA":"Granite Construction Incorporated","GVAL":"Cambria Global Value ETF","GVI":"iShares Intermediate Government/Credit Bond ETF","GVIP":"Goldman Sachs Hedge Industry VIP ETF","GWRE":"GUIDEWIRE SOFTWARE INC","GWW":"GRAINGER W W INC","GWX":"State Street SPDR S&P International Small Cap ETF","GXC":"State Street SPDR S&P China ETF","GXO":"GXO LOGISTICS INCORPORATED","GYRE":"Gyre Therapeutics, Inc.","H":"HYATT HOTELS CORP","HACK":"Amplify Cybersecurity ETF","HAE":"HAEMONETICS CORP MASS","HAFC":"Hanmi Financial Corporation","HAFN":"Hafnia Limited","HAL":"HALLIBURTON CO","HALO":"HALOZYME THERAPEUTICS INC","HAP":"VanEck Natural Resources ETF","HAS":"HASBRO INC","HASI":"HA Sustainable Infrastructure Capital, Inc.","HAUZ":"Xtrackers International Real Estate ETF","HAVA":"Harvard Ave Acquisition Corporation","HAWX":"iShares Currency Hedged MSCI ACWI ex U.S. ETF","HAYW":"HAYWARD HLDGS INC","HBAN":"HUNTINGTON BANCSHARES INC","HBCP":"Home Bancorp, Inc.","HBDC":"Hilton BDC Corporate Bond ETF","HBM":"HUDBAY MINERALS INC","HBNC":"Horizon Bancorp, Inc.","HBT":"HBT Financial, Inc.","HCA":"HCA HEALTHCARE INC","HCAT":"HEALTH CATALYST INC","HCC":"WARRIOR MET COAL INC","HCI":"HCI Group, Inc.","HCKT":"The Hackett Group, Inc.","HCMT":"Direxion HCM Tactical Enhanced US ETF","HCSG":"Healthcare Services Group, Inc.","HD":"HOME DEPOT INC","HDB":"HDFC Bank Ltd","HDEF":"Xtrackers MSCI EAFE High Dividend Yield Equity ETF","HDSN":"HUDSON TECHNOLOGIES INC","HDV":"ISHARES TR","HE":"HAWAIIAN ELEC INDUSTRIES","HECA":"Hedgeye Capital Allocation ETF","HEDG":"Equable Shares Hedged Equity ETF","HEDJ":"WisdomTree Europe Hedged Equity Fund","HEEM":"iShares Currency Hedged MSCI Emerging Markets ETF","HEFA":"iShares Currency Hedged MSCI EAFE ETF","HEGD":"Swan Hedged Equity US Large Cap ETF","HEI":"Heico Corporation","HELE":"Helen of Troy Limited","HELO":"JPMorgan Hedged Equity Laddered Overlay ETF","HEQT":"Simplify Hedged Equity ETF","HESM":"Hess Midstream Lp - US","HEWJ":"iShares Currency Hedged MSCI Japan ETF","HEZU":"iShares Currency Hedged MSCI Eurozone ETF","HFGM":"Unlimited HFGM Global Macro ETF","HFGO":"Hartford Large Cap Growth ETF","HFSI":"Hartford Strategic Income ETF","HFWA":"Heritage Financial Corporation","HFXI":"NYLI FTSE International Equity Currency Neutral ETF","HG":"HAMILTON INSURANCE GROUP LTD","HGER":"Harbor All-Weather Inflation Focus ETF","HGTY":"HAGERTY INC","HGV":"HILTON GRAND VACATIONS","HHH":"HOWARD HUGHES HOLDINGS INC","HIFS":"Hingham Institution for Savings","HIG":"HARTFORD FINL SVCS GROUP INC","HII":"Huntington Ingalls Industries, Inc.","HIMS":"HIMS &amp;amp; HERS HEALTH INC","HIMX":"Himax Technologies, Inc.","HIPO":"Hippo Holdings Inc.","HITI":"High Tide Inc.","HIVE":"HIVE Digital Technologies Ltd","HIW":"Highwoods Properties, Inc.","HL":"Hecla Mining Company","HLAL":"Wahed FTSE USA Shariah ETF","HLF":"HERBALIFE LTD","HLI":"HOULIHAN LOKEY INC","HLIO":"Helios Technologies, Inc.","HLIT":"Harmonic Inc.","HLLY":"Holley Inc.","HLMN":"HILLMAN SOLUTIONS CORP","HLN":"HALEON PLC","HLNE":"Hamilton Lane Incorporated","HLT":"HILTON WORLDWIDE HLDGS INC","HLX":"Helix Energy Solutions Group, Inc.","HMC":"Honda Motor Company, Ltd.","HMN":"Horace Mann Educators Corporation","HMOP":"Hartford Municipal Opportunities ETF","HMY":"Harmony Gold Mining Company Limited","HNDL":"Strategy Shares Nasdaq 7HANDL Index ETF","HNGE":"HINGE HEALTH INC","HNI":"HNI Corporation","HNRG":"HALLADOR ENERGY COMPANY","HNST":"The Honest Company, Inc.","HODL":"VanEck Bitcoin Trust","HOG":"HARLEY DAVIDSON INC","HOLA":"JPMorgan International Hedged Equity Laddered Overlay ETF","HOLX":"HOLOGIC INC","HOMB":"Home Bancshares Inc/Ar - US","HON":"HONEYWELL INTL INC","HOOD":"ROBINHOOD MKTS INC","HOOW":"Roundhill HOOD WeeklyPay ETF","HOPE":"HOPE BANCORP INC","HOV":"Hovnanian Enterprises, Inc.","HP":"Helmerich & Payne, Inc.","HPE":"HEWLETT PACKARD ENTERPRISE C","HPK":"HighPeak Energy, Inc.","HPQ":"HP INC","HQY":"HEALTHEQUITY INC","HR":"Healthcare Realty Trust Incorporated","HRB":"H&R Block, Inc.","HRI":"Herc Holdings Inc.","HRL":"HORMEL FOODS CORP","HRMY":"Harmony Biosciences Holdings, Inc.","HROW":"Harrow, Inc.","HRTG":"Heritage Insurance Holdings, Inc.","HRTX":"HERON THERAPEUTICS INC","HSAI":"HESAI GROUP","HSBC":"HSBC Holdings, plc.","HSCZ":"iShares Currency Hedged MSCI EAFE Small-Cap ETF","HSHP":"Himalaya Shipping Ltd.","HSIC":"HENRY SCHEIN INC","HST":"Host Hotels & Resorts, Inc.","HSTM":"HealthStream, Inc.","HSY":"HERSHEY CO","HTAB":"Hartford Schroders Tax-Aware Bond ETF","HTB":"HomeTrust Bancshares, Inc.","HTBK":"Heritage Commerce Corp","HTFL":"HEARTFLOW INC","HTGC":"Hercules Capital, Inc.","HTH":"Hilltop Holdings Inc - US","HTHT":"H World Group Limited","HTLD":"Heartland Express, Inc.","HTLM":"HomesToLife Ltd","HTO":"H2O America","HTRB":"Hartford Total Return Bond ETF","HTZ":"HERTZ GLOBAL HLDGS INC","HUBB":"HUBBELL INC","HUBG":"Hub Group, Inc.","HUBS":"HUBSPOT INC","HUM":"HUMANA INC","HUMA":"Humacyte, Inc.","HUN":"HUNTSMAN CORP","HURN":"HURON CONSULTING GROUP INC","HUT":"HUT 8 CORP","HVII":"Hennessy Capital Investment Corp. VII","HVMC":"HIGHVIEW MERGER CORP","HVT":"Haverty Furniture Companies, Inc.","HWC":"Hancock Whitney Corporation","HWKN":"Hawkins, Inc.","HWM":"HOWMET AEROSPACE INC","HXL":"HEXCEL   CORP   NEW","HY":"Hyster-Yale, Inc.","HYBB":"iShares BB Rated Corporate Bond ETF","HYBI":"NEOS Enhanced Income Credit Select ETF","HYBL":"State Street Blackstone High Income ETF","HYD":"VanEck High Yield Muni ETF","HYDB":"iShares High Yield Systematic Bond ETF","HYEM":"VanEck Emerging Markets High Yield Bond ETF","HYFI":"AB High Yield ETF","HYG":"iShares iBoxx $ High Yield Corporate Bond ETF","HYGH":"iShares Interest Rate Hedged High Yield Bond ETF","HYGV":"FlexShares High Yield Value-Scored Bond Index Fund","HYGW":"iShares High Yield Corporate Bond BuyWrite Strategy ETF","HYHG":"ProShares High Yield Interest Rate Hedged","HYLB":"Xtrackers USD High Yield Corporate Bond ETF","HYLN":"Hyliion Holdings Corp.","HYLS":"First Trust Tactical High Yield ETF","HYMB":"State Street SPDR Nuveen ICE High Yield Municipal Bond ETF","HYMC":"HYCROFT MINING HOLDING CORP","HYS":"PIMCO 0-5 Year High Yield Corporat Bond Index Exchange-Traded Fund","HYTR":"Counterpoint High Yield Trend ETF","HZO":"MarineMax, Inc. (FL)","IAC":"IAC INC","IAG":"IAMGOLD CORP","IAGG":"iShares International Aggregate Bond Fund","IAI":"iShares U.S. Broker-Dealers & Securities Exchanges ETF","IAK":"iShares U.S. Insurance ETF","IALT":"iShares Systematic Alternatives Active ETF","IAPR":"Innovator International Developed Power Buffer ETF April","IART":"Integra LifeSciences Holdings Corporation","IAT":"iShares U.S. Regional Banks ETF","IAU":"ISHARES GOLD TR","IAUI":"NEOS Gold High Income ETF","IAUM":"iShares Gold Trust Micro Shares","IAUX":"I-80 GOLD CORP","IBB":"ISHARES TR","IBCA":"iShares iBonds Dec 2035 Term Corporate ETF","IBCP":"Independent Bank Corporation","IBD":"Inspire Corporate Bond ETF","IBDR":"iShares iBonds Dec 2026 Term Corporate ETF","IBDS":"iShares iBonds Dec 2027 Term Corporate ETF","IBDT":"iShares iBonds Dec 2028 Term Corporate ETF","IBDU":"iShares iBonds Dec 2029 Term Corporate ETF","IBDV":"iShares iBonds Dec 2030 Term Corporate ETF","IBDW":"iShares iBonds Dec 2031 Term Corporate ETF","IBDX":"iShares iBonds Dec 2032 Term Corporate ETF","IBDY":"iShares iBonds Dec 2033 Term Corporate ETF","IBDZ":"iShares iBonds Dec 2034 Term Corporate ETF","IBEX":"IBEX Limited","IBHF":"iShares iBonds 2026 Term High Yield and Income ETF","IBHG":"iShares iBonds 2027 Term High Yield and Income ETF","IBHH":"iShares iBonds 2028 Term High Yield and Income ETF","IBHI":"iShares iBonds 2029 Term High Yield and Income ETF","IBIG":"iShares iBonds Oct 2030 Term TIPS ETF","IBIT":"ISHARES TR","IBKR":"INTERACTIVE BROKERS GROUP IN","IBM":"INTERNATIONAL BUSINESS MACHS","IBMO":"iShares iBonds Dec 2026 Term Muni Bond ETF","IBMP":"iShares iBonds Dec 2027 Term Muni Bond ETF","IBMQ":"iShares iBonds Dec 2028 Term Muni Bond ETF","IBMR":"iShares iBonds Dec 2029 Term Muni Bond ETF","IBN":"ICICI   BANK     LIMITED","IBND":"SPDR Bloomberg International Corporate Bond ETF","IBOC":"International Bancshares Corporation","IBP":"INSTALLED BLDG PRODS INC","IBRX":"ImmunityBio, Inc.","IBTA":"Ibotta, Inc.","IBTG":"iShares iBonds Dec 2026 Term Treasury ETF","IBTH":"iShares iBonds Dec 2027 Term Treasury ETF","IBTI":"iShares iBonds Dec 2028 Term Treasury ETF","IBTJ":"iShares iBonds Dec 2029 Term Treasury ETF","IBTK":"iShares iBonds Dec 2030 Term Treasury ETF","IBTL":"iShares iBonds Dec 2031 Term Treasury ETF","IBTM":"iShares iBonds Dec 2032 Term Treasury ETF","IBTO":"iShares iBonds Dec 2033 Term Treasury ETF","IBTQ":"iShares iBonds Dec 2035 Term Treasury ETF","IBUY":"Amplify Online Retail ETF","ICE":"INTERCONTINENTAL EXCHANGE IN","ICF":"iShares Select U.S. REIT ETF","ICFI":"ICF International, Inc.","ICHR":"Ichor Holdings","ICL":"ICL GROUP LTD","ICLN":"iShares Global Clean Energy ETF","ICLO":"Invesco AAA CLO Floating Rate Note ETF","ICLR":"ICON PLC","ICOP":"iShares Copper and Metals Mining ETF","ICOW":"Pacer Developed Markets International Cash Cows 100 ETF","ICSH":"iShares Ultra Short Duration Bond Active ETF","ICUI":"ICU MED INC","ICVT":"iShares Convertible Bond ETF","IDA":"IDACORP INC","IDCC":"INTERDIGITAL INC","IDEQ":"Lazard International Dynamic Equity ETF","IDEV":"iShares Core MSCI International Developed Markets ETF","IDGT":"iShares U.S. Digital Infrastructure and Real Estate ETF","IDHQ":"Invesco S&P International Developed Quality ETF","IDLV":"Invesco S&P International Developed Low Volatility ETF","IDMO":"Invesco S&P International Developed Momentum ETF","IDNA":"iShares Genomics Immunology and Healthcare ETF","IDOG":"ALPS International Sector Dividend Dogs ETF","IDR":"IDAHO STRATEGIC RESOURCES","IDRV":"iShares Self-Driving EV and Tech ETF","IDT":"IDT Corporation","IDU":"iShares U.S. Utilities ETF","IDUB":"Aptus International Enhanced Yield ETF","IDV":"iShares International Select Dividend ETF","IDVO":"Amplify International Enhanced Dividend Income ETF","IDXX":"IDEXX LABS INC","IDYA":"IDEAYA BIOSCIENCES INC","IE":"IVANHOE ELECTRIC INC","IEF":"iShares 7-10 Year Treasury Bond ETF","IEFA":"iShares Core MSCI EAFE ETF","IEI":"iShares 3-7 Year Treasury Bond ETF","IEMG":"ISHARES TR","IEO":"iShares U.S. Oil & Gas Exploration & Production ETF","IEP":"Icahn Enterprises LP","IESC":"IES Holdings, Inc.","IETC":"iShares U.S. Tech Independence Focused ETF","IEUR":"iShares Core MSCI Europe ETF","IEUS":"iShares MSCI Europe Small-Cap ETF","IEV":"iShares Europe ETF","IEX":"IDEX   CORP","IEZ":"iShares U.S. Oil Equipment & Services ETF","IFF":"INTERNATIONAL FLAVORS&amp;FRAGRA","IFLN":"Invesco Bloomberg Enhanced Fallen Angels ETF","IFRA":"iShares U.S. Infrastructure ETF","IFS":"Intercorp Financial Services Inc.","IFV":"First Trust Dorsey Wright International Focus 5 ETF","IGBH":"iShares Interest Rate Hedged Long-Term Corporate Bond ETF","IGE":"iShares North American Natural Resources ETF","IGEB":"iShares Investment Grade Systematic Bond ETF","IGF":"iShares Global Infrastructure ETF","IGHG":"ProShares Investment Grade-Interest Rate Hedged","IGIB":"iShares 5-10 Year Investment Grade Corporate Bond ETF","IGIC":"International General Insurance Holdings Ltd.","IGLB":"iShares 10 Year Investment Grade Corporate Bond ETF","IGLD":"FT Vest Gold Strategy Target Income ETF","IGM":"iShares Expanded Tech Sector ETF","IGOV":"iShares International Treasury Bond ETF","IGPT":"Invesco AI and Next Gen Software ETF","IGRO":"iShares International Dividend Growth ETF","IGSB":"iShares 1-5 Year Investment Grade Corporate Bond ETF","IGV":"ISHARES TR","IHAK":"iShares Cybersecurity and Tech ETF","IHDG":"WisdomTree International Hedged Quality Dividend Growth Fund","IHF":"iShares U.S. Health Care Providers ETF","IHG":"Intercontinental Hotels Group","IHI":"iShares U.S. Medical Devices ETF","IHPCF":"IShares Plc.","IHRT":"IHEARTMEDIA INC","IHS":"IHS Holding Limited","III":"Information Services Group, Inc.","IIIN":"Insteel Industries, Inc.","IIIV":"<![CDATA[I3 VERTICALS INC]]>","IIPR":"Innovative Industrial Properties, Inc.","IJH":"iShares China Large-Cap ETF","IJJ":"iShares S&P Mid-Cap 400 Value ETF","IJK":"iShares S&P Mid-Cap 400 Growth ETF","IJR":"iShares Core S&P Small-Cap ETF","IJS":"iShares S&P SmallCap 600 Value ETF","IJT":"iShares S&P SmallCap 600 Growth ETF","IKT":"Inhibikase Therapeutics, Inc.","ILCB":"iShares Morningstar Large-Cap ETF","ILCG":"iShares Morningstar Large-Cap Growth ETF","ILCV":"iShares Morningstar Large-Cap Value ETF","ILDR":"First Trust Innovation Leaders ETF","ILF":"iShares Latin America 40 ETF","ILMN":"ILLUMINA INC","ILOW":"AB International Low Volatility Equity ETF","ILTB":"iShares Core 10 Year USD Bond ETF","IMAX":"IMAX CORP","IMCB":"iShares Morningstar Mid-Cap ETF","IMCG":"iShares Morningstar Mid-Cap Growth ETF","IMCR":"Immunocore Holdings plc","IMCV":"iShares Morningstar Mid-Cap Value ETF","IMFL":"Invesco International Developed Dynamic Multifactor ETF","IMKTA":"Ingles Markets, Incorporated","IMMR":"Immersion Corporation","IMMX":"Immix Biopharma, Inc.","IMNM":"IMMUNOME INC","IMO":"Imperial Oil Limited","IMOM":"Alpha Architect International Quantitative Momentum ETF","IMPP":"Imperial Petroleum Inc.","IMRX":"Immuneering Corporation","IMSR":"TERRESTRIAL ENERGY INC","IMTB":"iShares Core 5-10 Year USD Bond ETF","IMTM":"iShares MSCI Intl Momentum Factor ETF","IMTX":"IMMATICS N.V","IMUX":"Immunic, Inc.","IMVP":"Invesco India ETF","IMVT":"IMMUNOVANT INC","IMXI":"INTERNATIONAL MNY EXPRESS IN","INBK":"First Internet Bancorp","INBX":"INHIBRX BIOSCIENCES INC","INCE":"Franklin Income Equity Focus ETF","INCM":"Franklin Income Focus ETF","INCO":"Columbia India Consumer ETF","INCY":"INCYTE CORP","INDA":"iShares MSCI India ETF","INDB":"Independent Bank Corp.","INDI":"INDIE SEMICONDUCTOR INC","INDV":"INDIVIOR PLC","INDY":"iShares India 50 ETF","INFL":"Horizon Kinetics Inflation Beneficiaries ETF","INFO":"Harbor PanAgora Dynamic Large Cap Core ETF","INFQ":"Infleqtion, Inc.","INFU":"InfuSystems Holdings, Inc.","INFY":"INFOSYS LTD","ING":"ING Group, N.V.","INGM":"Ingram Micro Holding Corporation","INGN":"Inogen, Inc","INGR":"INGREDION INC","INMD":"InMode Ltd.","INMU":"iShares Intermediate Muni Income Active ETF","INN":"SUMMIT HOTEL PPTYS INC","INNV":"InnovAge Holding Corp.","INO":"Inovio Pharmaceuticals, Inc.","INOD":"INNODATA INC","INR":"Infinity Natural Resources, Inc.","INSG":"Inseego Corp.","INSM":"INSMED INC","INSP":"Inspire Medical Systems, Inc.","INSW":"International Seaways Inc - US","INTA":"INTAPP INC","INTC":"INTEL CORP","INTF":"iShares International Equity Factor ETF","INTL":"Main International ETF","INTR":"Inter & Co. Inc.","INTU":"INTUIT","INTW":"GraniteShares 2x Long INTC Daily ETF","INV":"Innventure, Inc.","INVA":"INNOVIVA   INC","INVH":"INVITATION HOMES INC","INVX":"Innovex International, Inc.","INVZ":"INNOVIZ TECHNOLOGIES LTD","IOCT":"Innovator International Developed Power Buffer ETF - October","IONQ":"IONQ INC","IONS":"IONIS PHARMACEUTICALS INC","IONX":"Defiance Daily Target 2X Long IONQ ETF","IOO":"iShares Global 100 ETF","IOSP":"INNOSPEC INC","IOT":"SAMSARA INC","IOVA":"IOVANCE BIOTHERAPEUTICS INC","IP":"INTERNATIONAL PAPER CO","IPAC":"iShares Core MSCI Pacific ETF","IPAR":"INTERPARFUMS INC","IPAY":"Amplify Digital Payments ETF","IPGP":"IPG PHOTONICS CORP","IPI":"Intrepid Potash, Inc","IPKW":"Invesco International BuyBack Achievers ETF","IPO":"Renaissance IPO ETF","IPSC":"Century Therapeutics, Inc.","IQ":"iQIYI, Inc.","IQDF":"FlexShares International Quality Dividend Index Fund","IQDG":"WisdomTree International Quality Dividend Growth Fund","IQLT":"iShares MSCI Intl Quality Factor ETF","IQQQ":"ProShares Nasdaq-100 High Income ETF","IQV":"IQVIA HLDGS INC","IR":"INGERSOLL RAND INC","IRD":"OPUS GENETICS INC","IRDM":"Iridium Communications Inc - US","IRE":"Defiance Daily Target 2X Long IREN ETF","IREN":"IREN LIMITED","IRM":"Iron Mountain Incorporated (Delaware)","IRMD":"IRADIMED CORP","IRON":"DISC MEDICINE INC","IRS":"IRSA Inversiones Y Representaciones S.A. Global Depositary Shares (Each representing ten shares of","IRT":"Independence Realty Trust Inc","IRTC":"iRhythm Holdings, Inc.","IRWD":"IRONWOOD PHARMACEUTICALS INC","ISBA":"Isabella Bank Corporation","ISCB":"iShares Morningstar Small-Cap ETF","ISCF":"iShares International Small-Cap Equity Factor ETF","ISCG":"iShares Morningstar Small-Cap Growth ETF","ISCV":"iShares Morningstar Small-Cap Value ETF","ISEP":"Innovator International Developed Power Buffer ETF September","ISHG":"iShares 1-3 Year International Treasury Bond ETF","ISMCF":"IShares VII PLC","ISOU":"IsoEnergy Ltd.","ISPY":"ProShares S&P 500 High Income ETF","ISRG":"INTUITIVE SURGICAL INC","ISSC":"Innovative Solutions and Support, Inc.","ISTB":"iShares Core 1-5 Year USD Bond ETF","ISTR":"Investar Holding Corporation","ISVL":"iShares International Developed Small Cap Value Factor ETF","IT":"GARTNER INC","ITA":"iShares U.S. Aerospace & Defense ETF","ITB":"iShares U.S. Home Construction ETF","ITGR":"Integer Holdings Corporation","ITHA":"ITHAX ACQUISITION CORP III","ITIC":"Investors Title Company","ITM":"VanEck Intermediate Muni ETF","ITOT":"iShares Core S&P Total U.S. Stock Market ETF","ITRG":"Integra Resources Corp.","ITRI":"ITRON INC","ITRN":"ITURAN LOCATION AND CONTROL","ITT":"ITT Inc.","ITUB":"Itau Unibanco Banco Holding SA","ITW":"ILLINOIS TOOL WKS INC","IUS":"Invesco RAFI Strategic US ETF","IUSB":"ISHARES TR","IUSG":"iShares Core S&P U.S. Growth ETF","IUSV":"iShares Core S&P U.S. Value ETF","IVAL":"Alpha Architect International Quantitative Value ETF","IVE":"iShares S&P 500 Value ETF","IVES":"Dan IVES Wedbush AI Revolution ETF","IVLU":"iShares MSCI Intl Value Factor ETF","IVOG":"Vanguard S&P Mid-Cap 400 Growth ETF","IVOL":"Quadratic Interest Rate Volatility and Inflation Hedge ETF","IVOO":"Vanguard S&P Mid-Cap 400 ETF","IVOV":"Vanguard S&P Mid-Cap 400 Value ETF","IVR":"INVESCO MORTGAGE CAPITAL INC","IVT":"InvenTrust Properties Corp.","IVV":"INVESCO QQQ TR","IVVD":"INVIVYD INC","IVVW":"iShares S&P 500 BuyWrite ETF","IVW":"ISHARES TR","IVZ":"INVESCO  LTD","IWB":"ISHARES TR","IWC":"iShares Microcap ETF","IWD":"ISHARES TR","IWF":"ISHARES TR","IWL":"iShares Russell Top 200 ETF","IWLG":"IQ Winslow Large Cap Growth ETF","IWM":"ISHARES TR","IWMI":"NEOS Russell 2000 High Income ETF","IWMY":"Defiance R2000 Weekly Distribution ETF","IWN":"ISHARES TR","IWO":"ISHARES TR","IWP":"iShares Russell Midcap Growth ETF","IWR":"iShares Russell Mid-Cap ETF","IWS":"iShares Russell Mid-Cap Value ETF","IWV":"iShares Russell 3000 Fund","IWX":"iShares Russell Top 200 Value ETF","IWY":"iShares Russell Top 200 Growth ETF","IX":"ORIX Corporation","IXC":"iShares Global Energy ETF","IXG":"iShares Global Financial ETF","IXJ":"iShares Global Healthcare ETF","IXN":"ISHARES TR","IXP":"iShares Global Comm Services ETF","IXUS":"ISHARES TR","IYC":"iShares U.S. Consumer Discretionary ETF","IYE":"iShares U.S. Energy ETF","IYF":"iShares U.S. Financial ETF","IYG":"iShares U.S. Financial Services ETF","IYH":"iShares U.S. Healthcare ETF","IYJ":"iShares U.S. Industrials ETF","IYK":"iShares U.S. Consumer Staples ETF","IYLD":"iShares Morningstar Multi-Asset Income ETF","IYM":"iShares U.S. Basic Materials ETF","IYR":"ISHARES TR","IYRI":"NEOS Real Estate High Income ETF","IYT":"iShares U.S. Transportation ETF","IYW":"ISHARES TR","IYY":"iShares Dow Jones U.S. ETF","IYZ":"iShares U.S. Telecommunications ETF","IZRL":"ARK Israel Innovative Technology ETF","J":"JACOBS SOLUTIONS INC","JAAA":"Janus Henderson AAA CLO ETF","JACK":"JACK IN THE BOX INC","JACS":"Jackson Acquisition Company II","JAJL":"Innovator Equity Defined Protection ETF - 6 Mo Jan/Jul","JAKK":"JAKKS Pacific, Inc.","JANW":"AllianzIM U.S. Large Cap Buffer20 Jan ETF","JANX":"JANUX THERAPEUTICS INC","JAVA":"JPMorgan Active Value ETF","JAZZ":"JAZZ PHARMACEUTICALS PLC","JBBB":"Janus Henderson B-BBB CLO ETF","JBGS":"JBG SMITH Properties","JBHT":"HUNT J B TRANS SVCS INC","JBI":"Janus International Group Inc","JBIO":"JADE BIOSCIENCES INC","JBL":"JABIL INC","JBLU":"JETBLUE AWYS CORP","JBND":"JPMorgan Active Bond ETF","JBS":"JBS N.V., Class A","JBSS":"John B. Sanfilippo & Son, Inc.","JBTM":"JBT MAREL CORPORATION","JCAP":"Jefferson Capital, Inc.","JCI":"JOHNSON CTLS INTL PLC","JCPB":"JPMorgan Core Plus Bond ETF","JCPI":"JPMorgan Inflation Managed Bond ETF","JD":"JD.COM INC","JEF":"JEFFERIES FINL GROUP INC","JELD":"JELD-WEN Holding, Inc.","JEMA":"JPMorgan ActiveBuilders Emerging Markets Equity ETF","JENA":"Jena Acquisition Corporation II","JEPI":"JPMorgan Equity Premium Income ETF","JEPQ":"JPMorgan Nasdaq Equity Premium Income ETF","JETS":"U.S. Global Jets ETF","JFB":"JFB Construction Holdings","JFLX":"JPMorgan Flexible Debt ETF","JGLO":"JPMorgan Global Select Equity ETF","JGRO":"JPMorgan Active Growth ETF","JHEM":"John Hancock Multifactor Emerging Markets ETF","JHG":"JANUS HENDERSON GROUP PLC","JHMB":"John Hancock Mortgage-Backed Securities ETF","JHMD":"John Hancock Multifactor Developed International ETF","JHML":"John Hancock Multifactor Large Cap ETF","JHMM":"John Hancock Multifactor Mid Cap ETF","JHPI":"John Hancock Preferred Income ETF","JHSC":"John Hancock Multifactor Small Cap ETF","JHX":"JAMES HARDIE INDS PLC","JIG":"JPMorgan International Growth ETF","JILL":"J. Jill, Inc.","JIRE":"JPMorgan International Research Enhanced Equity ETF","JIVE":"JPMorgan International Value ETF","JJSF":"J & J Snack Foods Corp.","JKHY":"HENRY JACK   ASSOC INC","JKS":"JinkoSolar Holding Company Limited","JLL":"Jones Lang LaSalle Incorporated","JMBS":"Janus Henderson Mortgage-Backed Securities ETF","JMEE":"JPMorgan Small & Mid Cap Enhanced Equity ETF","JMHI":"JPMorgan High Yield Municipal ETF","JMOM":"JPMorgan U.S. Momentum Factor ETF","JMSI":"JPMorgan Sustainable Municipal Income ETF","JMST":"JPMorgan Ultra-Short Municipal Income ETF","JMTG":"JPMorgan Mortgage-Backed Securities ETF","JMUB":"JPMorgan Municipal ETF","JNJ":"JOHNSON &amp;amp; JOHNSON","JNK":"State Street SPDR Bloomberg High Yield Bond ETF","JNUG":"Direxion Daily Junior Gold Miners Index Bull 2X Shares","JOBY":"JOBY AVIATION INC","JOE":"ST JOE CO","JOET":"Virtus Terranova U.S. Quality Momentum ETF","JOUT":"Johnson Outdoors Inc.","JOYY":"JOYY INC","JPEF":"JPMorgan Equity Focus ETF","JPEM":"JPMorgan Diversified Return Emerging Markets Equity ETF","JPHY":"JPMorgan Active High Yield ETF","JPIB":"JPMorgan International Bond Opportunities ETF","JPIE":"JPMorgan Income ETF","JPIN":"JPMorgan Diversified Return International Equity ETF","JPLD":"JPMorgan Limited Duration Bond ETF","JPM":"JPMORGAN CHASE &amp; CO.","JPME":"JPMorgan Diversified Return U.S. Mid Cap Equity ETF","JPRE":"JPMorgan Realty Income ETF","JPSE":"JPMorgan Diversified Return U.S. Small Cap Equity ETF","JPST":"JPMorgan Ultra-Short Income ETF","JPUS":"JPMorgan Diversified Return U.S. Equity ETF","JPXN":"iShares JPX-Nikkei 400 ETF","JQUA":"JPMorgan U.S. Quality Factor ETF","JRVR":"James River Group Holdings, Inc.","JSCP":"JPMorgan Short Duration Core Plus ETF","JSI":"Janus Henderson Securitized Income ETF","JSMD":"Janus Henderson Small/Mid Cap Growth Alpha ETF","JSML":"Janus Henderson Small Cap Growth Alpha ETF","JTEK":"JPMorgan U.S. Tech Leaders ETF","JUCY":"Aptus Enhanced Yield ETF","JULW":"AllianzIM U.S. Large Cap Buffer20 Jul ETF","JUST":"Goldman Sachs JUST U.S. Large Cap Equity ETF","JVAL":"JPMorgan U.S. Value Factor ETF","JXI":"iShares Global Utilities ETF","JXN":"JACKSON FINANCIAL INC","KAI":"KADANT INC","KALU":"Kaiser Aluminum Corporation","KALV":"KALVISTA    PHARMACEUTICALS       INC","KARO":"Karooooo Ltd.","KB":"KB Financial Group Inc","KBA":"KraneShares Bosera MSCI China A 50 Connect Index ETF","KBE":"State Street SPDR S&P Bank ETF","KBH":"KB HOME","KBR":"KBR INC","KBWB":"Invesco KBW Bank ETF","KBWD":"Invesco KBW High Dividend Yield Financial ETF","KBWP":"Invesco KBW Property & Casualty Insurance ETF","KBWY":"Invesco KBW Premium Yield Equity REIT ETF","KC":"Kingsoft Cloud Holdings Limited","KCCA":"KraneShares California Carbon Allowance Strategy ETF","KCE":"State Street SPDR S&P Capital Markets ETF","KD":"KYNDRYL HLDGS INC","KDEF":"PLUS Korea Defense Industry Index ETF","KDK":"KODIAK AI INC.","KDP":"KEURIG DR PEPPER INC","KE":"Kimball Electronics, Inc.","KELYA":"Kelly Services, Inc.","KELYB":"Kelly Services, Inc.","KEMX":"KraneShares MSCI Emerging Markets ex China Index ETF","KEN":"Kenon Holdings Ltd.","KEP":"Korea Electric Power Corporation","KEX":"KIRBY CORP","KEY":"KEYCORP","KEYS":"KEYSIGHT TECHNOLOGIES INC","KFRC":"Kforce, Inc.","KFS":"KINGSWAY FINL SVCS INC","KFY":"KORN FERRY","KGC":"KINROSS GOLD CORP","KGEI":"Kolibri Global Energy Inc.","KGS":"Kodiak Gas Services, Inc.","KHC":"KRAFT HEINZ CO","KIDS":"OrthoPediatrics Corp.","KIE":"State Street SPDR S&P Insurance ETF","KIM":"Kimco Realty Corporation (HC)","KINS":"Kingstone Companies, Inc","KJAN":"Innovator U.S. Small Cap Power Buffer ETF - January","KKR":"KKR &amp; CO INC","KLAC":"KLA CORP","KLAR":"KLARNA GROUP PLC","KLC":"KinderCare Learning Companies, Inc.","KLIC":"Kulicke and Soffa Industries, Inc.","KLIP":"KraneShares KWEB Covered Call Strategy ETF","KLRS":"Kalaris Therapeutics, Inc.","KMB":"KIMBERLY-CLARK CORP","KMDA":"Kamada Ltd.","KMI":"KINDER MORGAN INC DEL","KMLM":"KraneShares Mount Lucas Managed Futures Index Strategy ETF","KMPR":"KEMPER CORP","KMT":"Kennametal Inc.","KMTS":"Kestra Medical Technologies, Ltd.","KMX":"CARMAX INC","KN":"Knowles Corp - US","KNF":"KNIFE RIVER CORP","KNG":"FT Vest S&P 500 Dividend Aristocrats Target Income ETF","KNOP":"KNOT Offshore Partners LP","KNSA":"Kiniksa Pharmaceuticals International, plc","KNSL":"KINSALE CAP GROUP INC","KNTK":"KINETIK HOLDINGS INC","KNX":"KNIGHT-SWIFT TRANSN HLDGS IN","KO":"COCA COLA CO","KOD":"KODIAK SCIENCES INC","KODK":"Eastman Kodak Company","KOF":"Coca Cola Femsa S.A.B. de C.V.","KOID":"KraneShares Global Humanoid and Embodied Intelligence Index ETF","KOLD":"ProShares UltraShort Bloomberg Natural Gas","KOMP":"State Street SPDR S&P Kensho New Economies Composite ETF","KOP":"Koppers Holdings Inc.","KOPN":"KOPIN CORP","KORP":"American Century Diversified Corporate Bond ETF","KORU":"Direxion Daily South Korea Bull 3X Shares","KOS":"Kosmos Energy Ltd.","KOYN":"CSLM Digital Asset Acquisition Corp III","KPTI":"Karyopharm Therapeutics Inc.","KR":"KROGER CO","KRC":"KILROY RLTY CORP","KRE":"State Street SPDR S&P Regional Banking ETF","KRG":"Kite Realty Group Trust","KRMD":"KORU Medical Systems, Inc.","KRMN":"Karman Holdings Inc.","KRNT":"Kornit Digital Ltd.","KRNY":"Kearny Financial","KRO":"Kronos Worldwide Inc","KROS":"KEROS THERAPEUTICS INC","KRP":"Kimbell Royalty Partners","KRRO":"Korro Bio, Inc.","KRT":"Karat Packaging Inc.","KRUS":"KURA SUSHI USA INC","KRYS":"KRYSTAL BIOTECH INC","KSA":"iShares MSCI Saudi Arabia ETF","KSPI":"KASPI KZ JSC","KSS":"KOHLS CORP","KSTR":"KraneShares SSE STAR Market 50 Index ETF","KT":"KT Corporation","KTB":"KONTOOR     BRANDS    INC","KTOS":"Kratos Defense & Security Solutions, Inc.","KULR":"KULR Technology Group, Inc.","KURA":"KURA ONCOLOGY INC","KVHI":"KVH Industries, Inc.","KVUE":"KENVUE INC","KVYO":"KLAVIYO INC","KW":"KENNEDY-WILSON HOLDINGS INC","KWEB":"KRANESHARES TRUST","KWR":"Quaker Houghton","KXI":"iShares Global Consumer Staples ETF","KYIV":"Kyivstar Group Ltd.","KYMR":"KYMERA THERAPEUTICS INC","KYTX":"Kyverna Therapeutics, Inc.","L":"Loews Corp.","LAB":"STANDARD BIOTOOLS INC","LABU":"Direxion Daily S&P Biotech Bull 3X Shares","LAC":"Lithium Americas Corp.","LAD":"LITHIA MTRS INC","LADR":"Ladder Capital Corp","LAES":"SEALSQ Corp - US","LAMR":"LAMAR ADVERTISING CO NEW","LAR":"LITHIUM ARGENTINA AG","LASR":"NLIGHT INC","LAUR":"LAUREATE EDUCATION INC","LAW":"CS Disco, Inc.","LAZ":"LAZARD INC","LB":"LandBridge Company LLC","LBRDA":"GCI LIBERTY INC","LBRDK":"Liberty Broadband Corporation","LBRT":"LIBERTY ENERGY INC","LBRX":"LB Pharmaceuticals Inc","LBTYA":"Liberty Global Ltd.","LBTYK":"LIBERTY GLOBAL LTD","LC":"LENDINGCLUB CORP","LCAP":"Principal Capital Appreciation Select ETF","LCID":"LUCID GROUP INC","LCII":"LCI Industries","LCTU":"iShares U.S. Carbon Transition Readiness Aware Active ETF","LCTX":"Lineage Cell Therapeutics, Inc.","LDI":"loanDepot, Inc.","LDOS":"LEIDOS HOLDINGS INC","LDRX":"SGI Enhanced Market Leaders ETF","LDUR":"PIMCO Enhanced Low Duration Active Exchange-Traded Fund","LE":"Lands' End, Inc.","LEA":"LEAR CORP","LECO":"Lincoln Electric Holdings, Inc.","LEE":"Lee Enterprises, Incorporated","LEG":"Leggett & Platt, Incorporated","LEGH":"LEGACY HOUSING CORP","LEGN":"LEGEND BIOTECH CORP","LEMB":"iShares J.P. Morgan EM Local Currency Bond","LEN":"LENNAR CORP","LENZ":"LENZ Therapeutics, Inc.","LEU":"CENTRUS ENERGY CORP","LEVI":"Levi Strauss & Co","LFCR":"LIFECORE BIOMEDICAL INC","LFMD":"LifeMD, Inc.","LFST":"LifeStance Health Group, Inc.","LFUS":"LITTELFUSE INC","LGCY":"Legacy Education Inc.","LGH":"HCM Defender 500 Index ETF","LGIH":"LGI HOMES INC","LGLV":"State Street SPDR US Large Cap Low Volatility Index ETF","LGN":"LEGENCE CORP","LGND":"Ligand Pharmaceuticals Incorporated","LGO":"Largo Inc.","LGOV":"First Trust Long Duration Opportunities ETF","LH":"LABCORP HOLDINGS INC","LHX":"L3HARRIS TECHNOLOGIES INC","LI":"LI AUTO INC","LIEN":"Chicago Atlantic BDC, Inc.","LIF":"Life360, Inc.","LIFE":"Ethos Technologies Inc.","LII":"LENNOX INTL INC","LILA":"Liberty Latin America Ltd.","LILAK":"LIBERTY LATIN AMERICA LTD","LIN":"LINDE PLC","LINC":"Lincoln Educational Services Corporation","LIND":"Lindblad Expeditions Holdings Inc.","LINE":"LINEAGE INC","LION":"LIONSGATE STUDIOS CORP","LIT":"Global X Lithium & Battery Tech ETF","LITE":"LUMENTUM HLDGS INC","LITX":"Tradr 2X Long LITE Daily ETF","LIVN":"LIVANOVA    PLC","LKFN":"Lakeland Financial Corporation","LKQ":"LKQ CORP","LLY":"ELI LILLY &amp;amp; CO","LLYVA":"LIBERTY LIVE HOLDINGS INC","LLYVK":"LIBERTY LIVE HOLDINGS INC","LMAT":"Lemaitre Vascular Inc - US","LMB":"Limbach Holdings, Inc.","LMBS":"First Trust Low Duration Opportunities ETF","LMND":"LEMONADE INC","LMNR":"Limoneira Co","LMRI":"Lumexa Imaging Holdings, Inc.","LMT":"LOCKHEED MARTIN CORP","LNC":"LINCOLN NATL CORP IND","LNG":"CHENIERE ENERGY INC","LNKB":"LINKBANCORP, Inc.","LNN":"Lindsay Corporation","LNT":"ALLIANT ENERGY CORP","LNTH":"LANTHEUS HLDGS INC","LOAR":"LOAR HOLDINGS INC","LOB":"Live Oak Bancshares, Inc.","LOCO":"El Pollo Loco Holdings, Inc.","LODE":"COMSTOCK INC","LOGI":"LOGITECH INTL S A","LOMA":"Loma Negra Compania Industrial Argentina Sociedad Anonima","LONZ":"PIMCO Senior Loan Active Exchange-Traded Fund","LOPE":"GRAND CANYON ED INC","LOUP":"Innovator Deepwater Frontier Tech ETF","LOVE":"The Lovesac Company","LOW":"LOWES COS INC","LOWV":"AB US Low Volatility Equity ETF","LPG":"DORIAN LPG LTD","LPL":"LG Display Co, Ltd AMERICAN DEPOSITORY SHARES","LPLA":"LPL FINL HLDGS INC","LPRO":"Open Lending Corporation","LPTH":"LIGHTPATH TECHNOLOGIES INC","LPX":"LOUISIANA PAC CORP","LQD":"ISHARES TR","LQDA":"LIQUIDIA CORPORATION","LQDH":"iShares Interest Rate Hedged Corporate Bond ETF","LQDT":"Liquidity Services, Inc.","LQDW":"iShares Investment Grade Corporate Bond BuyWrite Strategy ETF","LQTI":"FT Vest Investment Grade & Target Income ETF","LRCX":"<![CDATA[LAM RESEARCH CORP]]>","LRGC":"AB US Large Cap Strategic Equities ETF","LRGE":"ClearBridge Large Cap Growth Select ETF","LRGF":"iShares U.S. Equity Factor ETF","LRGG":"Nomura Focused Large Growth ETF","LRMR":"Larimar Therapeutics, Inc.","LRN":"STRIDE INC","LSCC":"LATTICE SEMICONDUCTOR CORP","LSGR":"Natixis Loomis Sayles Focused Growth ETF","LSPD":"Lightspeed Commerce Inc. Subordinate Voting Shares","LST":"Leuthold Select Industries ETF","LSTR":"Landstar System, Inc.","LTBR":"Lightbridge Corporation","LTC":"LTC Properties, Inc.","LTH":"LIFE TIME GROUP HOLDINGS INC","LTM":"LATAM AIRLINES GROUP SA","LTPZ":"Pimco 15 Year U.S. TIPS Index Exchange-Traded Fund","LTRX":"Lantronix, Inc.","LU":"Lufax Holding Ltd","LUCD":"LUCID DIAGNOSTICS INC","LUCK":"Lucky Strike Entertainment Corporation","LULU":"LULULEMON ATHLETICA INC","LUMN":"LUMEN TECHNOLOGIES INC","LUNR":"INTUITIVE MACHINES INC","LUV":"SOUTHWEST AIRLS CO","LVHD":"Franklin U.S. Low Volatility High Dividend Index ETF","LVHI":"Franklin International Low Volatility High Dividend Index ETF","LVS":"LAS VEGAS SANDS CORP","LW":"Lamb Weston Holdings, Inc.","LWAC":"LightWave Acquisition Corp.","LWAY":"Lifeway Foods, Inc.","LWLG":"LIGHTWAVE LOGIC INC","LXEO":"LEXEO THERAPEUTICS INC","LXFR":"Luxfer Holdings PLC","LXP":"LXP INDUSTRIAL TRUST","LXRX":"Lexicon Pharmaceuticals, Inc.","LXU":"LSB Industries, Inc.","LYB":"LYONDELLBASELL INDUSTRIES N","LYEL":"LYELL IMMUNOPHARMA INC","LYFT":"LYFT INC","LYG":"LLOYDS BANKING GROUP PLC","LYTS":"LSI Industries Inc.","LYV":"LIVE NATION ENTERTAINMENT IN","LZ":"LegalZoom.com, Inc.","LZB":"La-Z-Boy Incorporated","LZM":"Lifezone Metals Limited","M":"Macy's Inc","MA":"MASTERCARD INCORPORATED","MAA":"MID-AMER APT CMNTYS INC","MAC":"Macerich Company (The)","MAGN":"MAGNERA CORP","MAGS":"Roundhill Magnificent Seven ETF","MAGY":"Roundhill Magnificent Seven Covered Call ETF","MAIN":"Main Street Capital Corporation","MAMA":"Mama's Creations, Inc.","MAMB":"Monarch Ambassador Income Index ETF","MAN":"ManpowerGroup","MANE":"Veradermics, Incorporated","MANH":"MANHATTAN ASSOCIATES INC","MANU":"Manchester","MAPS":"WM Technology, Inc.","MAR":"MARRIOTT INTL INC NEW","MARA":"MARA HOLDINGS INC","MAS":"Masco Corporation","MASI":"MASIMO CORP","MASS":"908 Devices Inc.","MAT":"MATTEL INC","MATV":"Mativ Holdings, Inc.","MATW":"Matthews International Corporation","MATX":"MATSON INC","MAX":"MediaAlpha, Inc.","MAZE":"Maze Therapeutics, Inc.","MBAV":"M3-Brigade Acquisition V Corp.","MBB":"ISHARES TR","MBC":"MASTERBRAND INC","MBCC":"Monarch Blue Chips Core Index ETF","MBCN":"Middlefield Banc Corp.","MBI":"MBIA INC","MBIN":"Merchants Bancorp","MBLY":"MOBILEYE GLOBAL INC","MBOT":"Microbot Medical Inc.","MBSF":"Regan Floating Rate MBS ETF","MBUU":"Malibu Boats, Inc.","MBVI":"M3-Brigade Acquisition VI Corp.","MBWM":"Mercantile Bank Corporation","MBX":"MBX BIOSCIENCES INC","MC":"Moelis & Company","MCB":"Metropolitan Bank Holding Corp.","MCBS":"MetroCity Bankshares, Inc.","MCD":"MCDONALDS CORP","MCFT":"MasterCraft Boat Holdings, Inc.","MCHB":"Mechanics Bancorp","MCHI":"iShares MSCI China ETF","MCHP":"MICROCHIP TECHNOLOGY INC.","MCK":"MCKESSON CORP","MCO":"MOODYS CORP","MCRI":"Monarch Casino & Resort, Inc.","MCRP":"Micropolis AI Robotics","MCS":"Marcus Corporation (The)","MCW":"MISTER CAR WASH INC","MCY":"Mercury General Corporation","MD":"Pediatrix Medical Group, Inc.","MDB":"MONGODB INC","MDGL":"MADRIGAL PHARMACEUTICALS INC","MDIV":"Multi-Asset Diversified Income Index Fund","MDLN":"MEDLINE INC","MDLZ":"Mondelez International, Inc.","MDST":"Westwood Salient Enhanced Midstream Income ETF","MDT":"MEDTRONIC PLC","MDU":"MDU Resources Group, Inc.","MDWD":"MediWound Ltd.","MDXG":"MiMedx Group, Inc","MDY":"SPDR S P MIDCAP 400 ETF TR","MDYG":"State Street SPDR S&P 400 Mid Cap Growth ETF","MDYV":"State Street SPDR S&P 400 Mid Cap Value ETF","MEAR":"iShares Short Maturity Municipal Bond Active ETF","MEC":"Mayville Engineering Company, Inc.","MED":"MEDIFAST INC","MEDP":"MEDPACE HLDGS INC","MEG":"Montrose Environmental Group Inc - US","MEI":"Methode Electronics, Inc.","MELI":"MERCADOLIBRE INC","MENS":"Jyong Biotech Ltd.","MEOH":"Methanex Corporation","MERC":"Mercer International Inc.","MESO":"Mesoblast Limited","MET":"METLIFE INC","META":"META PLATFORMS INC","METC":"Ramaco Resources, Inc.","METL":"Sprott Active Metals & Miners ETF","METU":"Direxion Daily META Bull 2X Shares","METV":"Roundhill Ball Metaverse ETF","MEVO":"M Evo Global Acquisition Corp II","MFA":"MFA Financial, Inc.","MFC":"MANULIFE FINL CORP","MFDX":"PIMCO RAFI Dynamic Multi-Factor International Equity ETF","MFEM":"PIMCO RAFI Dynamic Multi-Factor Emerging Markets Equity ETF","MFG":"Mizuho Financial Group, Inc. Sponosred","MFIN":"Medallion Financial Corp.","MFUS":"PIMCO RAFI Dynamic Multi-Factor U.S. Equity ETF","MG":"Mistras Group Inc","MGA":"Magna International, Inc.","MGC":"Vanguard Mega Cap ETF","MGEE":"Mge Energy Inc - US","MGIC":"Magic Software Enterprises Ltd.","MGK":"Vanguard Mega Cap Growth ETF","MGM":"MGM RESORTS INTERNATIONAL","MGNI":"MAGNITE INC","MGNR":"American Beacon Select Funds American Beacon GLG Natural Resources ETF","MGNX":"MACROGENICS INC","MGPI":"MGP Ingredients, Inc.","MGRC":"MCGRATH RENTCORP","MGTX":"MeiraGTx Holdings plc","MGV":"Vanguard Mega Cap Value ETF","MGY":"Magnolia Oil & Gas Corporation","MH":"MCGRAW HILL INC","MHK":"MOHAWK INDS INC","MHO":"M/I HOMES INC","MIAX":"Miami International Holdings, Inc.","MICC":"The Magnum Ice Cream Company N.V.","MIDD":"The Middleby Corporation","MILN":"Global X Millennial Consumer ETF","MINO":"PIMCO Municipal Income Opportunities Active Exchange-Traded Fund","MINT":"PIMCO Enhanced Short Maturity Active Exchange-Traded Fund","MIR":"MIRION TECHNOLOGIES INC","MIRM":"MIRUM PHARMACEUTICALS INC","MISL":"First Trust Indxx Aerospace & Defense ETF","MIST":"Milestone Pharmaceuticals Inc.","MITK":"Mitek Systems, Inc.","MJ":"ETFMG Alternative Harvest ETF","MKC":"MCCORMICK   CO INC","MKL":"Markel Group, Inc","MKOR":"Matthews Korea Active ETF","MKSI":"MKS INC.","MKTX":"MarketAxess Holdings, Inc.","MLAB":"Mesa Laboratories, Inc.","MLAC":"MOUNTAIN LAKE ACQUISITION CO","MLCO":"MELCO RESORTS AND ENTMNT LTD","MLI":"MUELLER INDS INC","MLKN":"MillerKnoll, Inc.","MLM":"MARTIN MARIETTA MATLS INC","MLN":"VanEck Long Muni ETF","MLP":"Maui Land & Pineapple Company, Inc.","MLPA":"Global X MLP ETF","MLPI":"NEOS MLP & Energy Infrastructure High Income ETF","MLPX":"Global X MLP & Energy Infrastructure ETF","MLR":"Miller Industries, Inc.","MLTX":"MOONLAKE IMMUNOTHERAPEUTICS","MLYS":"Mineralys Therapeutics Inc - US","MMI":"Marcus & Millichap, Inc.","MMIN":"NYLI MacKay Muni Insured ETF","MMIT":"NYLI MacKay Muni Intermediate ETF","MMM":"3M CO","MMS":"MAXIMUS INC","MMSI":"MERIT MED SYS INC","MMYT":"MAKEMYTRIP LIMITED MAURITIUS","MNA":"NYLI Merger Arbitrage ETF","MNDY":"MONDAY COM LTD","MNKD":"MANNKIND CORP","MNPR":"Monopar Therapeutics Inc.","MNR":"Mach Natural Resources LP","MNRO":"Monro, Inc.","MNSB":"MainStreet Bancshares, Inc.","MNSO":"MINISO Group Holding Limited","MNST":"MONSTER BEVERAGE CORP NEW","MNTN":"MNTN INC","MO":"ALTRIA GROUP INC","MOAT":"VANECK ETF TRUST","MOD":"Modine Manufacturing Company","MODL":"VictoryShares WestEnd U.S. Sector ETF","MOG.A":"MOOG   INC","MOH":"MOLINA HEALTHCARE INC","MOO":"VanEck Agribusiness ETF","MORN":"MORNINGSTAR INC","MORT":"VanEck Mortgage REIT Income ETF","MOS":"Mosaic Company (The)","MOV":"Movado Group Inc.","MP":"MP MATERIALS CORP","MPAA":"Motorcar Parts of America, Inc.","MPB":"Mid Penn Bancorp","MPC":"Marathon Petroleum Corporation","MPLT":"MAPLIGHT THERAPEUTICS INC","MPLX":"MPLX LP","MPRO":"Monarch ProCap Index ETF","MPT":"Medical Properties Trust, Inc.","MPTI":"M-tron Industries, Inc.","MPWR":"MONOLITHIC PWR SYS INC","MQ":"MARQETA INC","MQQQ":"Tradr 2X Long Innovation 100 Monthly ETF","MRAM":"Everspin Technologies, Inc.","MRBK":"Meridian Corporation","MRCC":"Monroe Capital Corporation","MRCY":"Mercury Systems Inc","MRK":"MERCK &amp; CO INC","MRNA":"MODERNA INC","MRSH":"Marsh","MRSK":"Toews Agility Shares Managed Risk ETF","MRTN":"Marten Transport, Ltd.","MRVI":"MARAVAI LIFESCIENCES HLDGS I","MRVL":"MARVELL TECHNOLOGY INC","MRX":"MAREX GROUP PLC","MS":"MORGAN STANLEY","MSA":"MSA Safety Incorporated","MSBI":"Midland States Bancorp, Inc.","MSCI":"MSCI INC","MSEX":"Middlesex Water Company","MSFT":"MICROSOFT CORP","MSFU":"Direxion Daily MSFT Bull 2X Shares","MSGE":"MADISON SQUARE GARDEN ENTMT","MSGS":"MADISON SQUARE GRDN SPRT COR","MSI":"MOTOROLA SOLUTIONS INC","MSIF":"MSC Income Fund, Inc.","MSM":"MSC Industrial Direct Company, Inc.","MSMR":"McElhenny Sheffield Managed Risk ETF","MSOS":"AdvisorShares Pure US Cannabis ETF","MSTR":"STRATEGY INC","MSTU":"T-Rex 2X Long MSTR Daily Target ETF","MSTX":"Defiance Daily Target 2x Long MSTR ETF","MSTY":"YieldMax MSTR Option Income Strategy ETF","MT":"Arcelor Mittal NY Registry Shares NEW","MTA":"Metalla Royalty & Streaming Ltd.","MTB":"M&T Bank Corporation","MTBA":"Simplify MBS ETF","MTCH":"MATCH GROUP INC NEW","MTD":"METTLER TOLEDO INTERNATIONAL","MTDR":"Matador Resources Company","MTG":"MGIC INVT CORP WIS","MTH":"MERITAGE HOMES CORP","MTN":"VAIL RESORTS INC","MTRN":"Materion Corporation","MTRX":"MATRIX SVC CO","MTSI":"MACOM Technology Solutions Holdings, Inc.","MTUM":"iShares MSCI USA Momentum Factor ETF","MTUS":"Metallus Inc.","MTW":"MANITOWOC CO INC","MTX":"MINERALS TECHNOLOGIES INC","MTZ":"MASTEC INC","MU":"MICRON TECHNOLOGY INC","MUB":"iShares National Muni Bond ETF","MUFG":"Mitsubishi UFJ Financial Group, Inc.","MULL":"GraniteShares 2x Long MU Daily ETF","MUNI":"PIMCO Intermediate Municipal Bond Active Exchange-Traded Fund","MUR":"Murphy Oil Corporation","MUSA":"MURPHY USA INC","MUSI":"American Century Multisector Income ETF","MUST":"Columbia Multi-Sector Municipal Income ETF","MUU":"Direxion Daily MU Bull 2X Shares","MUX":"McEwen Inc - US","MVBF":"MVB Financial Corp.","MVIS":"MicroVision, Inc.","MVST":"Microvast Holdings, Inc.","MVV":"ProShares Ultra MidCap400","MWA":"MUELLER WATER PRODUCTS","MXI":"iShares Global Materials ETF","MXL":"MAXLINEAR INC","MYCH":"State Street My2028 Corporate Bond ETF","MYE":"Myers Industries, Inc.","MYGN":"MYRIAD GENETICS INC","MYRG":"MYR Group, Inc.","MZTI":"The Marzetti Company","NABL":"N-able, Inc.","NAGE":"Niagen Bioscience, Inc.","NAIL":"Direxion Daily Homebuilders & Supplies Bull 3X Shares","NAK":"Northern Dynasty Minerals, Ltd.","NAKA":"Nakamoto Inc.","NAMM":"Namib Minerals","NAMS":"NEWAMSTERDAM PHARMA COMPANY","NANC":"Unusual Whales Subversive Democratic Trading ETF","NANR":"State Street SPDR S&P North American Natural Resources ETF","NAT":"Nordic American Tankers Limited","NATH":"Nathan's Famous, Inc.","NATL":"NCR ATLEOS CORPORATION","NATR":"Nature's Sunshine Products, Inc.","NAUT":"Nautilus Biotechnology, Inc.","NAVI":"Navient Corp - US","NAVN":"NAVAN INC","NB":"NioCorp Developments Ltd.","NBBK":"NB Bancorp, Inc.","NBCM":"Neuberger Berman Commodity Strategy ETF","NBCR":"Neuberger Core Equity ETF","NBHC":"National Bank Holdings Corporation","NBIS":"NEBIUS GROUP N.V.","NBIX":"NEUROCRINE     BIOSCIENCES        INC","NBJP":"Neuberger Japan Equity ETF","NBN":"Northeast Bank","NBR":"NABORS INDUSTRIES LTD","NBSD":"Neuberger Berman Short Duration Income ETF","NBTB":"Nbt Bancorp Inc - US","NCLH":"NORWEGIAN CRUISE LINE HLDG L","NCMI":"National CineMedia, Inc.","NCNO":"NCINO INC","NDAQ":"NASDAQ   INC","NDSN":"NORDSON CORP","NE":"Noble Corporation plc A","NEAR":"iShares Short Duration Bond Active ETF","NECB":"NorthEast Community Bancorp, Inc.","NEE":"NEXTERA ENERGY INC","NEGG":"Newegg Commerce, Inc.","NEM":"NEWMONT CORP","NEO":"NEOGENOMICS INC","NEOG":"Neogen Corporation","NEOV":"NeoVolta Inc.","NERV":"Minerva Neurosciences, Inc","NESR":"National Energy Services Reunited Corp","NET":"CLOUDFLARE INC","NEU":"NEWMARKET CORP","NEWP":"New Pacific Metals Corp.","NEWT":"NewtekOne, Inc.","NEXA":"Nexa Resources S.A.","NEXN":"Nexxen International Ltd.","NEXT":"NEXTDECADE CORP","NFBK":"Northfield Bancorp, Inc.","NFE":"NEW FORTRESS ENERGY INC","NFG":"National Fuel Gas Company","NFGC":"New Found Gold Corp","NFLT":"Virtus Newfleet Multi-Sector Bond ETF","NFLX":"NETFLIX INC","NFRA":"FlexShares STOXX Global Broad Infrastructure Index Fund","NFTY":"First Trust India Nifty 50 Equal Weight ETF","NG":"Novagold Resources Inc.","NGD":"NEW GOLD INC CDA","NGEN":"NervGen Pharma Corp.","NGG":"National Grid Transco, PLC National Grid PLC (NEW)","NGL":"NGL ENERGY PARTNERS LP","NGNE":"NEUROGENE INC","NGS":"Natural Gas Services Group, Inc.","NGVC":"Natural Grocers by Vitamin Cottage, Inc.","NGVT":"INGEVITY   CORP","NHC":"National HealthCare Corporation","NHI":"National Health Investors, Inc.","NI":"NISOURCE INC","NIC":"NICOLET BANKSHARES INC","NICE":"NICE LTD","NIHI":"NEOS MSCI EAFE High Income ETF","NIO":"NIO INC","NIQ":"NIQ GLOBAL INTELLIGENCE PLC","NJAN":"Innovator Growth-100 Power Buffer ETF - January","NJR":"NewJersey Resources Corporation","NJUL":"Innovator Growth-100 Power Buffer ETF - July","NKE":"NIKE INC","NKLR":"Terra Innovatum Global N.V.","NKTR":"NEKTAR THERAPEUTICS","NKTX":"NKARTA INC","NLR":"VanEck Uranium and Nuclear ETF","NLY":"Annaly Capital Management Inc.","NMAX":"NEWSMAX INC","NMFC":"New Mountain Finance Corporation","NMG":"Nouveau Monde Graphite Inc.","NMIH":"NMI Holdings Inc","NMM":"Navios Maritime Partners LP","NMR":"Nomura Holdings Inc","NMRA":"Neumora Therapeutics, Inc.","NMRK":"NEWMARK GROUP INC","NN":"NEXTNAV INC","NNE":"NANO NUCLEAR ENERGY INC","NNI":"NELNET INC","NNN":"NNN REIT INC","NNNN":"Anbio Biotechnology","NNOX":"NANO-X IMAGING LTD","NOA":"North American Construction Group Ltd.","NOBL":"ProShares S&P 500 Dividend Aristocrats ETF","NOC":"NORTHROP GRUMMAN CORP","NODK":"NI Holdings, Inc.","NOG":"Northern Oil and Gas, Inc.","NOK":"NOKIA CORP","NOMD":"Nomad Foods Limited","NOV":"NOV INC","NOVT":"NOVANTA INC","NOW":"UNUM GROUP","NP":"Neptune Insurance Holdings Inc.","NPB":"Northpointe Bancshares, Inc.","NPCE":"Neuropace, Inc.","NPK":"National Presto Industries, Inc.","NPKI":"NPK International Inc.","NPO":"Enpro Inc.","NPWR":"NET Power Inc.","NRC":"National Research Corporation","NRDS":"NerdWallet, Inc.","NRDY":"NERDY INC","NRG":"NRG ENERGY INC","NRGV":"ENERGY VAULT HOLDINGS INC","NRIM":"Northrim BanCorp Inc","NRIX":"NURIX THERAPEUTICS INC","NRP":"Natural Resource Partners LP Limited Partnership","NSA":"National Storage Affiliates Trust","NSC":"NORFOLK SOUTHN CORP","NSIT":"INSIGHT ENTERPRISES INC","NSP":"INSPERITY INC","NSSC":"NAPCO Security Technologies, Inc.","NTAP":"NETAPP INC","NTB":"Bank of N.T. Butterfield & Son Limited (The) Voting","NTCT":"NetScout Systems, Inc.","NTES":"NetEase Inc. - ADR","NTGR":"NETGEAR INC","NTLA":"INTELLIA THERAPEUTICS INC","NTNX":"NUTANIX INC","NTR":"NUTRIEN LTD","NTRA":"NATERA INC","NTRS":"Northern Trust Corporation","NTSI":"WisdomTree International Efficient Core Fund","NTSK":"NETSKOPE INC","NTST":"NetSTREIT Corp.","NTSX":"WisdomTree U.S. Efficient Core Fund","NTWO":"Newbury Street II Acquisition Corp","NU":"NU HLDGS LTD","NUAI":"New Era Energy & Digital, Inc.","NUBD":"Nuveen ESG U.S. Aggregate Bond ETF","NUDM":"Nuveen ESG International Developed Markets Equity ETF","NUE":"NUCOR CORP","NUEM":"Nuveen ESG Emerging Markets Equity ETF","NUGT":"Direxion Daily Gold Miners Index Bull 2XShares","NUKZ":"Range Nuclear Renaissance Index ETF","NULG":"Nuveen ESG Large-Cap Growth ETF","NULV":"Nuveen ESG Large-Cap Value ETF","NUMG":"Nuveen ESG Mid-Cap Growth ETF","NUMV":"Nuveen ESG Mid-Cap Value ETF","NUS":"Nu Skin Enterprises, Inc.","NUSC":"Nuveen ESG Small-Cap ETF","NUTX":"Nutex Health Inc.","NUVB":"NUVATION BIO INC","NUVL":"NUVALENT INC","NVAX":"NOVAVAX    INC","NVCR":"NOVOCURE LTD","NVDA":"NVIDIA CORPORATION","NVDL":"GraniteShares 2x Long NVDA Daily ETF","NVDU":"Direxion Daily NVDA Bull 2X Shares","NVDX":"T-Rex 2X Long NVIDIA Daily Target ETF","NVDY":"YieldMax NVDA Option Income Strategy ETF","NVEC":"NVE Corporation","NVGS":"Navigator Holdings Ltd.","NVMI":"NOVA LTD","NVO":"NOVO-NORDISK A S","NVR":"NVR   INC","NVRI":"ENVIRI CORP","NVS":"NOVARTIS AG","NVST":"ENVISTA HOLDINGS CORPORATION","NVT":"NVENT ELECTRIC PLC","NVTS":"NAVITAS SEMICONDUCTOR CORP","NWBI":"Northwest Bancshares, Inc.","NWE":"NorthWestern Energy Group, Inc.","NWFL":"Norwood Financial Corp.","NWG":"NATWEST GROUP PLC","NWL":"NEWELL BRANDS INC","NWN":"Northwest Natural Holding Company","NWPX":"NWPX Infrastructure, Inc.","NWS":"NEWS CORP NEW","NWSA":"News Corporation","NX":"Quanex Building Products Corporation","NXDR":"NEXTDOOR HOLDINGS INC","NXE":"NEXGEN ENERGY LTD","NXPI":"NXP SEMICONDUCTORS N V","NXRT":"NexPoint Residential Trust, Inc.","NXST":"NEXSTAR MEDIA GROUP INC","NXT":"NEXTPOWER INC","NXTG":"First Trust Indxx NextG ETF","NYF":"iShares New York Muni Bond ETF","NYT":"NEW YORK TIMES CO","NZAC":"State Street SPDR MSCI ACWI Climate Paris Aligned ETF","O":"REALTY INCOME CORP","OACP":"OneAscent Core Plus Bond ETF","OAIM":"OneAscent International Equity ETF","OAKM":"Oakmark U.S. Large Cap ETF","OALC":"OneAscent Large Cap Core ETF","OBDC":"Blue Owl Capital Corp - US","OBE":"OBSIDIAN ENERGY LTD","OBIL":"US Treasury 12 Month Bill ETF","OBK":"ORIGIN BANCORP INC","OBT":"Orange County Bancorp, Inc.","OC":"OWENS CORNING NEW","OCFC":"OceanFirst Financial Corp.","OCGN":"OCUGEN INC","OCS":"Oculis Holding AG","OCSL":"Oaktree Specialty Lending Corporation","OCTW":"AllianzIM U.S. Large Cap Buffer20 Oct ETF","OCUL":"OCULAR THERAPEUTIX INC","ODC":"Oil-Dri Corporation Of America","ODD":"ODDITY TECH LTD","ODFL":"OLD DOMINION FREIGHT LINE IN","ODV":"Osisko Development Corp.","OEC":"ORION GROUP HLDGS INC","OEF":"iShares S&P 100 Fund","OFG":"OFG  BANCORP","OFIX":"ORTHOFIX MED INC","OFLX":"Omega Flex, Inc.","OFRM":"Once Upon a Farm, PBC","OGE":"OGE ENERGY CORP","OGI":"Organigram Global Inc.","OGN":"Organon & Co.","OGS":"ONE GAS INC","OHI":"Omega Healthcare Investors, Inc.","OI":"O-I GLASS INC","OIH":"VanEck Oil Services ETF","OII":"Oceaneering International, Inc.","OIS":"Oil States International, Inc.","OKE":"ONEOK INC NEW","OKLL":"Defiance Daily Target 2x Long OKLO ETF","OKLO":"OKLO INC","OKTA":"OKTA INC","OLED":"UNIVERSAL DISPLAY CORP","OLLI":"Ollie's Bargain Outlet Holdings, Inc.","OLMA":"OLEMA PHARMACEUTICALS INC","OLN":"OLIN CORP","OLPX":"Olaplex Holdings, Inc.","OMAB":"Grupo Aeroportuario del Centro Norte S.A.B. de C.V.","OMAH":"VistaShares Target 15 Berkshire Select Income ETF","OMC":"OMNICOM GROUP INC","OMCL":"OMNICELL COM","OMDA":"OMADA   HEALTH   INC","OMER":"OMEROS CORP","OMF":"ONEMAIN HLDGS INC","OMFL":"Invesco Russell 1000 Dynamic Multifactor ETF","ON":"ON SEMICONDUCTOR CORP","ONB":"Old National Bancorp","ONC":"BEONE MEDICINES LTD","ONCH":"1RT ACQUISITION CORP.","ONCY":"Oncolytics Biotech Inc.","ONDS":"ONDAS HLDGS INC","ONEQ":"Fidelity Nasdaq Composite Index ETF","ONEV":"State Street SPDR Russell 1000 Low Volatility Focus ETF","ONEW":"OneWater Marine Inc.","ONEY":"State Street SPDR Russell 1000 Yield Focus ETF","ONIT":"Onity Group Inc.","ONOF":"Global X Adaptive U.S. Risk Management ETF","ONON":"ON HLDG AG","ONTF":"ON24, Inc.","ONTO":"ONTO INNOVATION INC","OOMA":"Ooma, Inc.","OPAL":"OPAL Fuels Inc.","OPCH":"OPTION CARE HEALTH INC","OPEN":"OPENDOOR TECHNOLOGIES INC","OPER":"ClearShares Ultra-Short Maturity ETF","OPFI":"Oppfi Inc - US","OPK":"Opko Health, Inc.","OPLN":"OPENLANE INC","OPPE":"WisdomTree European Opportunities Fund","OPPJ":"WisdomTree Japan Opportunities Fund","OPRA":"Opera Limited","OPRT":"Oportun Financial Corporation","OPRX":"OptimizeRx Corporation","OPTU":"Optimum Communications, Inc.","OPTX":"Syntec Optics Holdings, Inc.","OPY":"Oppenheimer Holdings, Inc.","OR":"OR ROYALTIES INC.","ORA":"ORMAT TECHNOLOGIES INC","ORBS":"EIGHTCO HOLDINGS INC","ORC":"Orchid Island Capital, Inc.","ORCL":"ORACLE CORP","ORCX":"Defiance Daily Target 2X Long ORCL ETF","ORGO":"Organogenesis Holdings Inc.","ORI":"Old Republic International Corporation","ORIC":"ORIC PHARMACEUTICALS INC","ORKA":"ORUKA THERAPEUTICS INC","ORLA":"ORLA MNG LTD NEW","ORLY":"O'Reilly Automotive, Inc.","ORMP":"ORAMED PHARMACEUTICALS INC","ORN":"Orion Group Holdings, Inc.","ORR":"Militia Long/Short Equity ETF","ORRF":"Orrstown Financial Services, Inc.","OS":"ONESTREAM INC","OSBC":"Old Second Bancorp, Inc.","OSCR":"OSCAR HEALTH INC","OSCV":"Opus Small Cap Value ETF","OSEA":"Harbor International Compounders ETF","OSG":"AMBAC FINL GROUP INC","OSIS":"OSI SYSTEMS INC","OSK":"OSHKOSH CORP","OSPN":"ONESPAN INC","OSS":"One Stop Systems, Inc.","OSUR":"OraSure Technologies, Inc.","OSW":"ONESPAWORLD HOLDINGS LIMITED","OTEX":"OPEN TEXT CORP","OTF":"Blue Owl Technology Finance Corp.","OTIS":"OTIS WORLDWIDE CORP","OTTR":"OTTER TAIL CORP","OUNZ":"VanEck Merk Gold ETF","OUST":"OUSTER INC","OUT":"OUTFRONT MEDIA INC","OVBC":"Ohio Valley Banc Corp.","OVID":"Ovid Therapeutics Inc.","OVLY":"Oak Valley Bancorp (CA)","OVV":"Ovintiv Inc. (DE)","OWL":"BLUE OWL CAPITAL INC","OWLT":"Owlet, Inc.","OXM":"Oxford Industries, Inc.","OXSQ":"Oxford Square Capital Corp.","OXY":"OCCIDENTAL PETE CORP","OZ":"Belpointe PREP, LLC","OZK":"Bank OZK","PAA":"Plains All American Pipeline, L.P.","PAAA":"PGIM AAA CLO ETF","PAAS":"PAN AMERN SILVER CORP","PABU":"iShares Paris-Aligned Climate Optimized MSCI USA ETF","PACB":"Pacific Biosciences of California, Inc.","PACK":"Ranpak Holdings Corp","PACS":"PACS Group, Inc.","PAG":"Penske Automotive Group, Inc.","PAGP":"Plains GP Holdings, L.P.","PAGS":"PAGSEGURO DIGITAL LTD","PAHC":"Phibro Animal Health Corporation","PAL":"Proficient Auto Logistics, Inc.","PALI":"PALISADE BIO INC","PALL":"abrdn Physical Palladium Shares ETF","PAM":"Pampa Energia S.A.","PANL":"Pangaea Logistics Solutions Ltd.","PANW":"PALO ALTO NETWORKS INC","PAPI":"Parametric Equity Premium Income ETF","PAPR":"Innovator U.S. Equity Power Buffer ETF - April","PAR":"PAR TECHNOLOGY CORP","PARR":"Par Pacific Holdings, Inc. Common Stock","PATH":"UIPATH INC","PATK":"Patrick Industries, Inc.","PAUG":"Innovator U.S. Equity Power Buffer ETF - August","PAVE":"Global X U.S. Infrastructure Development ETF","PAX":"Patria Investments Ltd - US","PAY":"PAYMENTUS HOLDINGS INC","PAYC":"PAYCOM SOFTWARE INC","PAYO":"PAYONEER GLOBAL INC","PAYP":"PayPay Corporation - American Depository Shares","PAYS":"Paysign, Inc.","PAYX":"PAYCHEX INC","PB":"PROSPERITY BANCSHARES INC","PBA":"PEMBINA PIPELINE CORP","PBD":"Invesco Global Clean Energy ETF","PBDC":"Putnam BDC Income ETF","PBEU":"Portfolio Building Block European Banks Index ETF","PBF":"PBF   ENERGY    INC","PBH":"Prestige Consumer Healthcare Inc.","PBI":"PITNEY BOWES INC","PBOG":"Portfolio Building Block Integrated Oil and Gas and Exploration and Production Index ETF","PBP":"Invesco S&P 500 BuyWrite ETF","PBPH":"Portfolio Building Block World Pharma and Biotech Index ETF","PBR":"PETROLEO BRASILEIRO SA PETRO","PBUS":"Invesco MSCI USA ETF","PBW":"INVESCO WILDERHILL CLEAN ENERGY ETF","PBYI":"Puma Biotechnology Inc","PCAR":"PACCAR INC","PCB":"PCB Bancorp","PCEF":"Invesco CEF Income Composite ETF","PCG":"PG&amp;E CORP","PCGG":"Polen Capital Global Growth ETF","PCOR":"PROCORE TECHNOLOGIES INC","PCRB":"Putnam ESG Core Bond ETF","PCRX":"Pacira BioSciences, Inc.","PCT":"PURECYCLE TECHNOLOGIES INC","PCTY":"Paylocity Holding Corporation","PCVX":"VAXCYTE INC","PCY":"Invesco Emerging Markets Sovereign Debt ETF","PCYO":"Pure Cycle Corporation","PD":"PAGERDUTY INC","PDBC":"Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF","PDD":"PDD HOLDINGS INC","PDEC":"Innovator U.S. Equity Power Buffer ETF - December","PDEX":"Pro-Dex, Inc.","PDFS":"PDF Solutions, Inc.","PDLB":"Ponce Financial Group, Inc.","PDM":"Piedmont Realty Trust, Inc.","PDN":"Invesco RAFI Developed Markets ex-U.S. Small-Mid ETF","PDP":"Invesco Dorsey Wright Momentum ETF","PDS":"Precision Drilling Corporation","PDYN":"Palladyne AI Corp.","PEB":"Pebblebrook Hotel Trust","PEBK":"Peoples Bancorp of North Carolina, Inc.","PEBO":"PEOPLES BANCORP INC","PECO":"Phillips Edison & Company, Inc.","PEG":"PUBLIC SVC ENTERPRISE GRP IN","PEGA":"PEGASYSTEMS INC","PEJ":"Invesco Leisure and Entertainment ETF","PELI":"Pelican Acquisition Corporation","PEN":"PENUMBRA INC","PENG":"<![CDATA[PENGUIN SOLUTIONS INC]]>","PENN":"PENN ENTERTAINMENT INC","PEP":"PEPSICO INC","PEPG":"PEPGEN INC","PERI":"PERION NETWORK LTD","PESI":"Perma-Fix Environmental Services, Inc.","PEY":"Invesco High Yield Equity Dividend Achievers ETF","PFBC":"Preferred Bank","PFDE":"Pathfinder Disciplined US Equity ETF","PFE":"PFIZER INC","PFEB":"Innovator U.S. Equity Power Buffer ETF - February","PFF":"iShares Preferred and Income Securities ETF","PFFA":"Virtus InfraCap U.S. Preferred Stock ETF","PFFD":"Global X U.S. Preferred ETF","PFFR":"InfraCap REIT Preferred ETF","PFFV":"Global X Variable Rate Preferred ETF","PFG":"PRINCIPAL FINANCIAL GROUP IN","PFGC":"Performance Food Group Company","PFIG":"Invesco Fundamental Investment Grade Corporate Bond ETF","PFIS":"Peoples Financial Services Corp.","PFIX":"Simplify Interest Rate Hedge ETF","PFLD":"AAM Low Duration Preferred and Income Securities ETF","PFLT":"PennantPark Floating Rate Capital Ltd.","PFM":"Invesco Dividend Achievers ETF","PFRL":"PGIM Floating Rate Income ETF","PFS":"Provident Financial Services, Inc","PFSI":"PennyMac Financial Services, Inc.","PFUT":"Putnam Sustainable Future ETF","PFXF":"VanEck Preferred Securities ex Financials ETF","PG":"PROCTER AND GAMBLE CO","PGC":"Peapack-Gladstone Financial Corporation","PGEN":"PRECIGEN INC","PGF":"Invesco Financial Preferred ETF","PGHY":"Invesco Global ex-US High Yield Corporate Bond ETF","PGNY":"PROGYNY INC","PGR":"PROGRESSIVE CORP","PGX":"Invesco Preferred ETF","PGY":"PAGAYA TECHNOLOGIES LTD","PH":"PARKER-HANNIFIN CORP","PHAT":"PHATHOM PHARMACEUTICALS INC","PHG":"Koninklijke Philips N.V. NY Registry Shares","PHI":"PLDT Inc. Sponsored","PHIN":"PHINIA INC","PHM":"PULTE GROUP INC","PHO":"Invesco Water Resources ETF","PHR":"Phreesia Inc - US","PHVS":"Pharvaris N.V.","PHYD":"Putnam ESG High Yield ETF","PHYL":"PGIM Active High Yield Bond ETF","PI":"IMPINJ INC","PICB":"Invesco International Corporate Bond ETF","PICK":"iShares MSCI Global Select Metals & Mining Producers Fund","PICS":"PicS N.V.","PID":"Invesco International Dividend Achievers ETF","PIE":"Invesco Dorsey Wright Emerging Markets Momentum ETF","PII":"POLARIS INC","PINK":"Simplify Health Care ETF","PINS":"PINTEREST INC","PIPR":"PIPER SANDLER COMPANIES","PIT":"VanEck Commodity Strategy ETF","PIZ":"Invesco Dorsey Wright Developed Markets Momentum ETF","PJAN":"Innovator U.S. Equity Power Buffer ETF - January","PJP":"Invesco Pharmaceuticals ETF","PJT":"PJT PARTNERS INC","PJUL":"Innovator U.S. Equity Power Buffer ETF - July","PJUN":"Innovator U.S. Equity Power Buffer ETF - June","PK":"Park Hotels & Resorts Inc.","PKB":"Invesco Building & Construction ETF","PKBK":"Parke Bancorp, Inc.","PKE":"Park Aerospace Corp.","PKG":"PACKAGING CORP AMER","PKOH":"Park-Ohio Holdings Corp.","PKST":"Peakstone Realty Trust","PKW":"Invesco BuyBack Achievers ETF","PKX":"POSCO HOLDINGS INC.","PL":"PLANET LABS PBC","PLAB":"PHOTRONICS INC","PLAY":"Dave & Buster's Entertainment, Inc.","PLBC":"Plumas Bancorp","PLBY":"Playboy, Inc.","PLD":"PROLOGIS INC.","PLDR":"Putnam Sustainable Leaders ETF","PLG":"Platinum Group Metals Ltd.","PLMR":"PALOMAR HLDGS INC","PLNT":"PLANET FITNESS INC","PLOW":"Douglas Dynamics, Inc.","PLPC":"Preformed Line Products Company","PLSE":"Pulse Biosciences, Inc","PLTK":"Playtika Holding Corp.","PLTM":"GraniteShares Platinum Shares ETF","PLTR":"PALANTIR TECHNOLOGIES INC","PLTU":"Direxion Daily PLTR Bull 2X Shares","PLTW":"Roundhill PLTR WeeklyPay ETF","PLTY":"YieldMax PLTR Option Income Strategy ETF","PLUG":"PLUG POWER INC","PLUS":"ePlus inc.","PLX":"Protalix BioTherapeutics, Inc. (DE)","PLXS":"PLEXUS CORP","PLYX":"Polaryx Therapeutics, Inc.","PM":"PHILIP MORRIS INTL INC","PMAR":"Innovator U.S. Equity Power Buffer ETF - March","PMAY":"Innovator U.S. Equity Power Buffer ETF - May","PMMF":"iShares Prime Money Market ETF","PMT":"PennyMac Mortgage Investment Trust","PMTS":"CPI CARD GROUP INC","PNC":"PNC Financial Services Group, Inc. (The)","PNFP":"Pinnacle Financial Partners, Inc.","PNOV":"Innovator U.S. Equity Power Buffer ETF - November","PNQI":"Invesco Nasdaq Internet ETF","PNR":"PENTAIR PLC","PNRG":"PrimeEnergy Resources Corporation","PNTG":"The Pennant Group, Inc.","PNW":"PINNACLE WEST CAP CORP","POCT":"Innovator U.S. Equity Power Buffer ETF - October","PODD":"INSULET CORP","POET":"POET Technologies Inc.","POLE":"Andretti Acquisition Corp. II","PONY":"PONY AI INC","POOL":"POOL CORP","POR":"Portland General Electric Co","POST":"Post Holdings, Inc.","POWI":"Power Integrations, Inc.","POWL":"POWELL INDS INC","POWR":"iShares U.S. Power Infrastructure ETF","POWW":"Outdoor Holding Company","PPA":"Invesco Aerospace & Defense ETF","PPC":"PILGRIMS PRIDE CORP","PPG":"PPG Industries, Inc.","PPH":"VanEck Pharmaceutical ETF","PPHC":"Public Policy Holding Company, Inc.","PPI":"Astoria Real Assets ETF","PPIE":"Putnam PanAgora ESG International Equity ETF","PPIH":"Perma-Pipe International Holdings, Inc.","PPL":"PPL Corporation","PPLT":"ABRDN PHYSICAL PLATINUM SHARES ETF","PPTA":"PERPETUA RESOURCES CORP","PR":"PERMIAN RESOURCES CORP","PRA":"PROASSURANCE CORP","PRAA":"PRA Group, Inc.","PRAX":"Praxis Precision Medicines, Inc.","PRCH":"PORCH GROUP INC","PRCT":"PROCEPT BioRobotics Corporation","PRDO":"Perdoceo Education Corporation","PRE":"Prenetics Global Limited","PREF":"Principal Spectrum Preferred Securities Active ETF","PRF":"Invesco RAFI US 1000 ETF","PRFZ":"Invesco RAFI US 1500 Small-Mid ETF","PRG":"PROG HOLDINGS INC","PRGO":"PERRIGO CO PLC","PRGS":"PROGRESS SOFTWARE CORP","PRI":"PRIMERICA   INC","PRIM":"Primoris Services Corporation","PRIV":"SPDR SSGA IG Public & Private Credit ETF","PRK":"Park National Corporation","PRKS":"UNITED PARKS &amp; RESORTS INC","PRLB":"Proto Labs, Inc.","PRLD":"Prelude Therapeutics Incorporated","PRM":"PERIMETER SOLUTIONS INC","PRMB":"PRIMO BRANDS CORPORATION","PRME":"PRIME MEDICINE INC","PRN":"Invesco Dorsey Wright Industrials Momentum ETF","PROF":"Profound Medical Corp.","PROK":"ProKidney Corp.","PROP":"Prairie Operating Co.","PRSD":"State Street Short Duration IG Public & Private Credit ETF","PRSU":"Pursuit Attractions and Hospitality, Inc.","PRTA":"PROTHENA CORP PLC","PRTH":"Priority Technology Holdings, Inc.","PRU":"PRUDENTIAL FINL INC","PRVA":"PRIVIA HEALTH GROUP INC","PSA":"Public Storage, Inc.","PSBD":"Palmer Square Capital BDC Inc.","PSC":"Principal U.S. Small-Cap ETF","PSCE":"Invesco S&P SmallCap Energy ETF","PSCI":"Invesco S&P SmallCap Industrials ETF","PSCT":"Invesco S&P SmallCap Information Technology ETF","PSFE":"Paysafe Limited","PSFF":"Pacer Swan SOS Fund of Funds ETF","PSH":"PGIM Short Duration High Yield ETF","PSI":"Invesco Semiconductors ETF","PSIX":"POWER SOLUTIONS INTL INC","PSK":"State Street SPDR ICE Preferred Securities ETF","PSKY":"PARAMOUNT SKYDANCE CORP","PSMT":"PRICESMART INC","PSN":"Parsons Corporation","PSNL":"Personalis, Inc.","PSO":"Pearson, Plc","PSP":"Invesco Global Listed Private Equity ETF","PSQ":"ProShares Short QQQ","PSTG":"PURE STORAGE INC","PSTL":"Postal Realty Trust, Inc.","PSX":"PHILLIPS 66","PTC":"PTC INC","PTCT":"PTC THERAPEUTICS INC","PTEN":"PATTERSON-UTI       ENERGY  INC","PTF":"Invesco Dorsey Wright Technology Momentum ETF","PTGX":"PROTAGONIST THERAPEUTICS INC","PTIR":"GraniteShares 2x Long PLTR Daily ETF","PTL":"Inspire 500 ETF","PTLC":"Pacer Trendpilot US Large Cap ETF","PTLO":"PORTILLOS INC","PTMC":"Pacer Trendpilot US Mid Cap ETF","PTNQ":"Pacer Trendpilot 100 ETF","PTON":"PELOTON INTERACTIVE INC","PTRB":"PGIM Total Return Bond ETF","PTRN":"Pattern Group Inc. - Series A","PUBM":"PubMatic, Inc.","PUK":"Prudential Public Limited Company","PULS":"PGIM Ultra Short Bond ETF","PULT":"Putnam ESG Ultra Short ETF","PUMP":"ProPetro Holding Corp","PURR":"HYPERLIQUID STRATEGIES INC","PVAL":"Putnam Focused Large Cap Value ETF","PVH":"PVH Corp.","PVLA":"Palvella Therapeutics, Inc.","PWB":"Invesco Large Cap Growth ETF","PWP":"Perella Weinberg Partners","PWR":"QUANTA SVCS INC","PWRD":"TCW Transform Systems ETF","PWV":"Invesco Large Cap Value ETF","PWZ":"Invesco California AMT-Free Municipal Bond Portfolio","PXED":"Phoenix Education Partners, Inc.","PXF":"Invesco RAFI Developed Markets ex-U.S. ETF","PXH":"Invesco RAFI Emerging Markets ETF","PY":"Principal Value ETF","PYLD":"PIMCO Multisector Bond Active Exchange-Traded Fund","PYPL":"PAYPAL HLDGS INC","PYZ":"Invesco Dorsey Wright Basic Materials Momentum ETF","PZA":"Invesco National AMT-Free Municipal Bond ETFo","PZG":"Paramount Gold Nevada Corp.","PZT":"Invesco New York AMT-Free Municipal Bond ETF","PZZA":"Papa John's International, Inc.","Q":"QNITY ELECTRONICS INC","QAI":"NYLI Hedge Multi-Strategy Tracker ETF","QBTS":"D WAVE QUANTUM INC","QCLN":"First Trust NASDAQ Clean Edge Green Energy Index Fund","QCOM":"QUALCOMM INC","QCRH":"QCR Holdings, Inc.","QDEC":"FT Vest Nasdaq-100 Buffer ETF - December","QDEF":"FlexShares Quality Dividend Defensive Index Fund","QDEL":"QuidelOrtho Corporation","QDF":"FlexShares Quality Dividend Index Fund","QDPL":"Pacer Metaurus US Large Cap Dividend Multiplier 400 ETF","QDTE":"Roundhill Innovation-100 0DTE Covered Call Strategy ETF","QDVO":"Amplify CWP Growth & Income ETF","QEFA":"State Street SPDR MSCI EAFE StrategicFactors ETF","QFIN":"Qfin Holdings, Inc.","QFLR":"Innovator Nasdaq-100 Managed Floor ETF","QGEN":"QIAGEN NV","QGRO":"American Century U.S. Quality Growth ETF","QGRW":"WisdomTree U.S. Quality Growth Fund","QHY":"WisdomTree U.S. High Yield Corporate Bond Fund","QID":"ProShares UltraShort QQQ","QINT":"American Century Quality Diversified International ETF","QIPT":"Quipt Home Medical Corp.","QLC":"FlexShares US Quality Large Cap Index Fund","QLD":"ProShares Ultra QQQ","QLTA":"iShares Aaa A Rated Corporate Bond ETF","QLTY":"GMO U.S. Quality ETF","QLYS":"QUALYS INC","QMOM":"Alpha Architect U.S. Quantitative Momentum ETF","QNC":"QUANTUM EMOTION CORP","QNST":"QuinStreet, Inc.","QQA":"Invesco QQQ Income Advantage ETF","QQEW":"First Trust Nasdaq-100 Select Equal Weight ETF","QQH":"HCM Defender 100 Index ETF","QQMG":"Invesco ESG NASDAQ 100 ETF","QQQ":"Invesco QQQ Trust, Series 1","QQQE":"Direxion NASDAQ-100 Equal Weighted Index Shares","QQQH":"NEOS Nasdaq-100 Hedged Equity Income ETF","QQQI":"NEOS Nasdaq 100 High Income ETF","QQQJ":"Invesco NASDAQ Next Gen 100 ETF","QQQM":"INVESCO EXCH TRADED FD TR II","QQQY":"Defiance Nasdaq 100 Weekly Distribution ETF","QQXT":"First Trust NASDAQ-100 Ex-Technology Sector Index Fund","QRVO":"QORVO INC","QS":"QUANTUMSCAPE CORP","QSI":"Quantum-Si Incorporated","QSR":"RESTAURANT BRANDS INTL INC","QTEC":"First Trust NASDAQ-100-Technology Sector Index Fund","QTOP":"iShares Nasdaq Top 30 Stocks ETF","QTRX":"Quanterix Corporation","QTUM":"Defiance Quantum ETF","QTWO":"Q2 Holdings, Inc.","QUAD":"Quad Graphics, Inc","QUAL":"iShares MSCI USA Quality Factor ETF","QUBT":"QUANTUM COMPUTING INC","QUIK":"QuickLogic Corporation","QURE":"UNIQURE NV","QUS":"State Street SPDR MSCI USA StrategicFactors ETF","QVAL":"Alpha Architect U.S. Quantitative Value ETF","QVMT":"Invesco S&P 500 Concentrated QVM ETF","QXO":"QXO, Inc.","QYLD":"Global X NASDAQ 100 Covered Call ETF","QYLG":"Global X Nasdaq 100 Covered Call & Growth ETF","R":"RYDER SYS INC","RAA":"SMI 3Fourteen REAL Asset Allocation ETF","RAAQ":"REAL ASSET ACQUISITION CORP","RAAX":"VanEck Real Assets ETF","RACE":"FERRARI N V","RAFE":"PIMCO RAFI ESG U.S. ETF","RAIL":"Freightcar America, Inc.","RAL":"RALLIANT CORP","RAMP":"LiveRamp Holdings, Inc.","RANI":"Rani Therapeutics Holdings, Inc.","RAPP":"Rapport Therapeutics, Inc.","RAPT":"RAPT THERAPEUTICS INC","RARE":"Ultragenyx Pharmaceutical Inc.","RAVI":"FlexShares Ultra-Short Income Fund","RBA":"RB GLOBAL INC","RBB":"RBB Bancorp","RBBN":"Ribbon Communications Inc.","RBC":"RBC BEARINGS INC","RBCAA":"Republic Bancorp, Inc.","RBLX":"ROBLOX CORP","RBRK":"RUBRIK INC.","RCAT":"RED CAT HLDGS INC","RCEL":"Avita Medical, Inc.","RCI":"Rogers Communication, Inc.","RCKT":"ROCKET PHARMACEUTICALS INC","RCKY":"Rocky Brands, Inc.","RCL":"Royal Caribbean Cruises Ltd.","RCMT":"RCM TECHNOLOGIES INC","RCUS":"Arcus Biosciences Inc - US","RDAG":"Republic Digital Acquisition Company","RDCM":"Radcom Ltd.","RDDT":"REDDIT INC","RDIV":"Invesco S&P Ultra Dividend Revenue ETF","RDN":"RADIAN GROUP INC","RDNT":"RADNET INC","RDTE":"Roundhill Russell 2000 0DTE Covered Call Strategy ETF","RDVI":"FT Vest Rising Dividend Achievers Target Income ETF","RDVT":"Red Violet Inc - US","RDVY":"First Trust Rising Dividend Achievers ETF","RDW":"REDWIRE CORPORATION","RDWR":"Radware Ltd.","RDY":"Dr. Reddy's Laboratories Ltd","REAL":"THE REALREAL INC","REAX":"The Real Brokerage, Inc.","RECS":"Columbia Research Enhanced Core ETF","REET":"iShares Global REIT ETF","REG":"REGENCY CTRS CORP","REGL":"ProShares S&P MidCap 400 Dividend Aristocrats ETF","REGN":"REGENERON PHARMACEUTICALS","REI":"Ring Energy, Inc.","REKR":"Rekor Systems, Inc.","RELL":"Richardson Electronics, Ltd.","RELX":"RELX PLC","RELY":"REMITLY GLOBAL INC","REM":"iShares Mortgage Real Estate ETF","REMX":"VanEck Rare Earth and Strategic Metals ETF","REPL":"REPLIMUNE GROUP INC","REPX":"Riley Exploration Permian, Inc.","RERE":"ATRENEW INC","RES":"RPC, Inc.","REVS":"Columbia Research Enhanced Value ETF","REX":"REX American Resources Corporation","REXR":"Rexford Industrial Realty, Inc.","REYN":"Reynolds Consumer Products Inc.","REZ":"iShares Residential and Multisector Real Estate ETF","REZI":"RESIDEO TECHNOLOGIES INC","RF":"Regions Financial Corporation","RFIL":"RF Industries, Ltd.","RFV":"Invesco S&P MidCap 400 Pure Value ETF","RGA":"Reinsurance Group of America, Incorporated","RGC":"Regencell Bioscience Holdings Limited","RGEN":"REPLIGEN CORP","RGLD":"ROYAL   GOLD   INC","RGNX":"REGENXBIO INC","RGP":"Resources Connection, Inc.","RGR":"Sturm, Ruger & Company, Inc.","RGTI":"RIGETTI COMPUTING INC","RH":"RH","RHI":"ROBERT HALF INC.","RHLD":"Resolute Holdings Management","RHP":"Ryman Hospitality Properties, Inc. (REIT)","RICK":"RCI Hospitality Holdings, Inc.","RIG":"TRANSOCEAN LTD","RIGL":"Rigel Pharmaceuticals, Inc.","RILY":"BRC Group Holdings, Inc.","RING":"iShares MSCI Global Gold Miners ETF","RIO":"RIO TINTO PLC","RIOT":"RIOT PLATFORMS INC","RISR":"FolioBeyond Alternative Income and Interest Rate Hedge ETF","RITM":"Rithm Capital Corp","RIVN":"RIVIAN AUTOMOTIVE INC","RJET":"Republic Airways Holdings Inc.","RJF":"Raymond James Financial, Inc.","RKLB":"ROCKET LAB CORP","RKLX":"Defiance Daily Target 2X Long RKLB ETF","RKT":"ROCKET COS INC","RL":"RALPH LAUREN CORP","RLAY":"RELAY THERAPEUTICS INC","RLGT":"Radiant Logistics, Inc.","RLI":"RLI Corp.","RLJ":"RLJ Lodging Trust","RLMD":"Relmada Therapeutics, Inc.","RLX":"RLX Technology Inc.","RLY":"State Street Multi-Asset Real Return ETF","RM":"Regional Management Corp.","RMAX":"RE/MAX Holdings, Inc.","RMBS":"Rambus, Inc.","RMD":"RESMED INC","RMNI":"RIMINI STR INC DEL","RMOP":"Rockefeller Opportunistic Municipal Bond ETF","RMR":"The RMR Group Inc.","RNA":"AVIDITY BIOSCIENCES INC","RNAC":"CARTESIAN THERAPEUTICS INC","RNG":"RINGCENTRAL INC","RNGR":"Ranger Energy Services, Inc.","RNR":"RENAISSANCERE HLDGS LTD","RNST":"RENASANT CORP","RNW":"RENEW   ENERGY    GLOBAL      PLC","ROAD":"CONSTRUCTION PARTNERS INC","ROBO":"ROBO Global Robotics and Automation Index ETF","ROBT":"EXCHANGE TRADED CONCEPTS TRU","ROCK":"Gibraltar Industries, Inc.","RODM":"Hartford Multifactor Developed Markets (ex-US) ETF","ROE":"Astoria US Equal Weight Quality Kings ETF","ROG":"ROGERS CORP","ROIV":"ROIVANT SCIENCES LTD","ROK":"ROCKWELL AUTOMATION INC","ROKU":"ROKU INC","ROL":"ROLLINS INC","ROM":"ProShares Ultra Technology","ROOT":"Root, Inc.","ROP":"ROPER TECHNOLOGIES INC","ROST":"ROSS STORES INC","ROUS":"Hartford Multifactor U.S. Equity ETF","RPAR":"RPAR Risk Parity ETF","RPAY":"Repay Holdings Corporation","RPC":"Ridgepost Capital, Inc.","RPD":"RAPID7 INC","RPG":"Invesco S&P 500 Pure Growth ETF","RPM":"RPM INTL INC","RPRX":"ROYALTY PHARMA PLC","RPV":"Invesco S&P 500 Pure Value ETF","RR":"Richtech Robotics Inc.","RRBI":"Red River Bancshares, Inc.","RRC":"Range Resources Corporation","RRR":"RED ROCK RESORTS INC","RRX":"REGAL REXNORD CORPORATION","RS":"RELIANCE INC","RSBT":"Return Stacked Bonds & Managed Futures ETF","RSG":"REPUBLIC SVCS INC","RSHO":"Tema American Reshoring ETF","RSI":"RUSH STREET INTERACTIVE INC","RSKD":"RISKIFIED LTD","RSMC":"Rockefeller U.S. Small-Mid Cap ETF","RSP":"INVESCO EXCHANGE TRADED FD T","RSPA":"Invesco S&P 500 Equal Weight Income Advantage ETF","RSPD":"Invesco S&P 500 Equal Weight Consumer Discretionary ETF","RSPF":"Invesco S&P 500 Equal Weight Financial ETF","RSPG":"Invesco S&P 500 Equal Weight Energy ETF","RSPH":"Invesco S&P 500 Equal Weight Health Care ETF","RSPM":"Invesco S&P 500 Equal Weight Materials ETF","RSPN":"Invesco S&P 500 Equal Weight Industrials Portfolio","RSPR":"Invesco S&P 500 Equal Weight Real Estate ETF","RSPS":"Invesco S&P 500 Equal Weight Consumer Staples ETF","RSPT":"Invesco S&P 500 Equal Weight Technology ETF","RSPU":"Invesco S&P 500 Equal Weight Utilities ETF","RSSB":"Return Stacked Global Stocks & Bonds ETF","RSST":"Return Stacked U.S. Stocks & Managed Futures ETF","RTAC":"Renatus Tactical Acquisition Corp I","RTH":"VanEck Retail ETF","RTO":"RENTOKIL INITIAL PLC","RTX":"RTX CORPORATION","RUM":"RUMBLE INC","RUN":"SUNRUN INC","RUNN":"Running Oak Efficient Growth ETF","RUSHA":"Rush Enterprises, Inc.","RUSHB":"Rush Enterprises Inc - CL A","RVLV":"REVOLVE GROUP INC","RVMD":"REVOLUTION    MEDICINES     INC","RVTY":"REVVITY INC","RWAY":"Runway Growth Finance Corp.","RWJ":"Invesco S&P SmallCap 600 Revenue ETF","RWK":"Invesco S&P MidCap 400 Revenue ETF","RWL":"Invesco S&P 500 Revenue ETF","RWM":"ProShares Short Russell2000","RWO":"State Street SPDR Dow Jones Global Real Estate ETF","RWR":"State Street SPDR Dow Jones REIT ETF","RWT":"Redwood Trust, Inc.","RWX":"State Street SPDR Dow Jones International Real Estate ETF","RXI":"iShares Global Consumer Discretionary ETF","RXO":"RXO, Inc.","RXRX":"Recursion Pharmaceuticals, Inc.","RXST":"RXSIGHT INC","RXT":"Rackspace Technology, Inc.","RY":"Royal Bank Of Canada","RYAAY":"RYANAIR HOLDINGS PLC","RYAM":"Rayonier Advanced Materials Inc.","RYAN":"RYAN SPECIALTY HOLDINGS INC","RYLD":"Global X Russell 2000 Covered Call ETF","RYN":"Rayonier Inc. REIT","RYTM":"RHYTHM PHARMACEUTICALS INC","RYZ":"Ryerson Holding Corporation","RZLT":"REZOLUTE INC","RZLV":"Rezolve AI PLC","RZV":"Invesco S&P SmallCap 600 Pure Value ETF","S":"SENTINELONE INC","SA":"SEABRIDGE GOLD INC","SABR":"SABRE CORP","SABS":"SAB Biotherapeutics, Inc.","SAC":"Safeguard Acquisition Corp.","SAFE":"Safehold Inc. New","SAFT":"Safety Insurance Group, Inc.","SAH":"Sonic Automotive, Inc.","SAIA":"SAIA INC","SAIC":"Science Applications International Corporation","SAIL":"SAILPOINT INC","SAM":"BOSTON BEER INC","SAMT":"Strategas Macro Thematic Opportunities ETF","SAN":"Banco Santander, S.A. Sponsored","SANA":"Sana Biotechnology, Inc.","SANM":"SANMINA CORPORATION","SAP":"SAP SE","SARO":"STANDARDAERO INC","SATL":"Satellogic Inc.","SATS":"ECHOSTAR CORP","SAVA":"Cassava Sciences, Inc.","SB":"Safe Bulkers, Inc","SBAC":"SBA Communications Corporation","SBAR":"Simplify Barrier Income ETF","SBCF":"Seacoast Banking Corporation of Florida","SBET":"Sharplink, Inc.","SBGI":"Sinclair, Inc.","SBH":"Sally Beauty Holdings, Inc. (Name to be changed from Sally Holdings, Inc.)","SBIL":"Simplify Government Money Market ETF","SBIO":"ALPS Medical Breakthroughs ETF","SBIT":"ProShares UltraShort Bitcoin ETF","SBLK":"STAR BULK CARRIERS CORP.","SBND":"Columbia Short Duration Bond ETF","SBRA":"SABRA   HEALTH     CARE   REIT     INC","SBS":"Companhia de saneamento Basico Do Estado De Sao Paulo - Sabesp","SBSI":"Southside Bancshares, Inc.","SBSW":"SIBANYE STILLWATER LTD","SBUX":"STARBUCKS CORP","SCCO":"SOUTHERN COPPER CORP","SCCR":"Schwab Core Bond ETF","SCEC":"Sterling Capital Enhanced Core Bond ETF","SCHA":"Schwab U.S. Small-Cap ETF","SCHB":"SCHWAB STRATEGIC TR","SCHC":"Schwab International Small-Cap Equity ETF","SCHD":"SCHWAB STRATEGIC TR","SCHE":"Schwab Emerging Markets Equity ETF","SCHF":"Schwab International Equity ETF","SCHG":"SCHWAB STRATEGIC TR","SCHH":"Schwab U.S. REIT ETF","SCHI":"Schwab 5-10 Year Corporate Bond ETF","SCHJ":"Schwab 1-5 Year Corporate Bond ETF","SCHK":"Schwab 1000 Index ETF","SCHL":"SCHOLASTIC CORP","SCHM":"Schwab U.S. Mid Cap ETF","SCHO":"Schwab Short-Term U.S. Treasury ETF","SCHP":"Schwab U.S. TIPS ETF","SCHQ":"Schwab Long-Term U.S. Treasury ETF","SCHR":"Schwab Intermediate-Term U.S. Treasury ETF","SCHV":"SCHWAB STRATEGIC TR","SCHW":"SCHWAB CHARLES CORP","SCHX":"SCHWAB STRATEGIC TR","SCHY":"Schwab International Dividend Equity ETF","SCHZ":"SCHWAB STRATEGIC TR","SCI":"SERVICE CORP INTL","SCIO":"First Trust Structured Credit Income Opportunities ETF","SCJ":"iShares MSCI Japan Sm Cap","SCL":"Stepan Company","SCM":"Stellus Capital Investment Corporation","SCMB":"Schwab Municipal Bond ETF","SCO":"ProShares UltraShort Bloomberg Crude Oil","SCSC":"ScanSource, Inc.","SCUS":"Schwab Ultra-Short Income ETF","SCVL":"Shoe Carnival, Inc.","SCYB":"Schwab High Yield Bond ETF","SCZ":"iShares MSCI EAFE Small-Cap ETF","SCZM":"Santacruz Silver Mining Ltd.","SD":"SANDRIDGE ENERGY INC","SDCI":"USCF SummerHaven Dynamic Commodity Strategy No K-1 Fund","SDFI":"AB Short Duration Income ETF","SDGR":"SCHRODINGER INC","SDHC":"Smith Douglas Homes Corp.","SDIV":"Global X SuperDividend ETF","SDOG":"ALPS Sector Dividend Dogs ETF","SDOW":"UltraPro Short Dow30","SDRL":"Seadrill Limited","SDS":"ProShares UltraShort S&P500","SDSI":"American Century Short Duration Strategic Income ETF","SDVY":"FIRST TR EXCHANGE TRADED FD","SDY":"State Street SPDR S&P Dividend ETF","SE":"SEA LTD","SEB":"Seaboard Corporation","SECT":"Main Sector Rotation ETF","SEDG":"SOLAREDGE TECHNOLOGIES INC","SEE":"SEALED AIR CORP NEW","SEG":"SEAPORT ENTMT GROUP INC","SEI":"SOLARIS ENERGY INFRAS INC","SEIC":"SEI Investments Company","SEIM":"SEI Enhanced U.S. Large Cap Momentum Factor ETF","SEIQ":"SEI Enhanced U.S. Large Cap Quality Factor ETF","SEIV":"SEI Enhanced U.S. Large Cap Value Factor ETF","SEIX":"Virtus Seix Senior Loan ETF","SELV":"SEI Enhanced Low Volatility U.S. Large Cap ETF","SEM":"Select Medical Holdings Corporation","SEMR":"SEMrush Holdings, Inc.","SENEA":"Seneca Foods Corp.","SENS":"Senseonics Holdings, Inc.","SEPN":"SEPTERNA INC","SEPW":"AllianzIM U.S. Large Cap Buffer20 Sep ETF","SEPZ":"TrueShares Structured Outcome (September) ETF","SERV":"SERVE ROBOTICS INC","SES":"SES AI CORPORATION","SETM":"Sprott Critical Materials ETF","SEZL":"Sezzle Inc - US","SF":"Stifel Financial Corporation","SFBS":"Servisfirst Bancshares Inc - US","SFD":"SMITHFIELD FOODS INC","SFIX":"STITCH FIX INC","SFL":"SFL CORPORATION LTD","SFLO":"VictoryShares Small Cap Free Cash Flow ETF","SFLR":"Innovator Equity Managed Floor ETF","SFM":"SPROUTS FMRS MKT INC","SFNC":"Simmons First National Corporation","SFST":"Southern First Bancshares, Inc.","SFTX":"Horizon International Managed Risk ETF","SFY":"SoFi Select 500 ETF","SG":"SWEETGREEN INC","SGDJ":"Sprott Junior Gold Miners ETF","SGDM":"Sprott Gold Miners ETF","SGHC":"Super Group (SGHC) Limited","SGHT":"Sight Sciences, Inc.","SGI":"SOMNIGROUP INTERNATIONAL INC","SGLC":"SGI U.S. Large Cap Core ETF","SGML":"SIGMA LITHIUM CORPORATION","SGMO":"Sangamo Therapeutics, Inc.","SGMT":"Sagimet Biosciences Inc. - Series A","SGOL":"ETFS GOLD TR","SGOV":"iShares 0-3 Month Treasury Bond ETF","SGP":"SpyGlass Pharma, Inc.","SGRY":"SURGERY PARTNERS INC","SGVT":"Schwab Government Money Market ETF","SH":"ProShares Short S&P500","SHAK":"SHAKE SHACK INC","SHBI":"Shore Bancshares, Inc.","SHC":"SOTERA HEALTH CO","SHEL":"SHELL PLC","SHEN":"Shenandoah Telecommunications Co","SHG":"Shinhan Financial Group Co Ltd","SHIP":"Seanergy Maritime Holdings Corp.","SHLD":"Global X Defense Tech ETF","SHLS":"Shoals Technologies Group, Inc.","SHM":"State Street SPDR Nuveen ICE Short Term Municipal Bond ETF","SHMD":"SCHMID Group N.V.","SHNY":"MicroSectors Gold 3X Leveraged ETNs due January 29, 2043","SHO":"Sunstone Hotel Investors, Inc.","SHOC":"Strive U.S. Semiconductor ETF","SHOO":"Steven Madden, Ltd.","SHOP":"SHOPIFY INC","SHV":"iShares 0-1 Year Treasury Bond ETF","SHW":"SHERWIN WILLIAMS CO","SHY":"ISHARES TR","SHYD":"VanEck Short High Yield Muni ETF","SHYG":"iShares 0-5 Year High Yield Corporate Bond ETF","SHYL":"Xtrackers Short Duration High Yield Bond ETF","SHYM":"iShares Short Duration High Yield Muni Active ETF","SI":"Shoulder Innovations, Inc.","SIBN":"SI-BONE INC","SID":"Companhia Siderurgica Nacional S.A.","SIDU":"Sidus Space, Inc.","SIG":"SIGNET JEWELERS LIMITED","SIGA":"SIGA Technologies Inc.","SIGI":"Selective Insurance Group, Inc.","SIHY":"Harbor Scientific Alpha High-Yield ETF","SII":"SPROTT INC","SIL":"Global X Silver Miners ETF","SILA":"Sila Realty Trust Inc","SILC":"Silicom Ltd","SILJ":"Amplify Junior Silver Miners ETF","SIMO":"SILICON MOTION TECHNOLOGY CO","SIO":"Touchstone Strategic Income Opportunities ETF","SION":"SIONNA THERAPEUTICS INC","SIRI":"SIRIUSXM HOLDINGS INC","SITE":"SITEONE LANDSCAPE SUPPLY INC","SITM":"SITIME CORP","SIVR":"abrdn Physical Silver Shares ETF","SIXA":"ETC 6 Meridian Mega Cap Equity ETF","SIXG":"Defiance Connective Technologies ETF","SIXH":"ETC 6 Meridian Hedged Equity Index Option ETF","SIXO":"AllianzIM U.S. Large Cap 6 Month Buffer10 Apr/Oct ETF","SIZE":"iShares MSCI USA Size Factor ETF","SJM":"SMUCKER J M CO","SJNK":"State Street SPDR Bloomberg Short Term High Yield Bond ETF","SKE":"Skeena Resources Limited","SKIN":"The Beauty Health Company","SKM":"SK Telecom Co., Ltd.","SKT":"Tanger Inc.","SKWD":"Skyward Specialty Insurance Group, Inc.","SKY":"CHAMPION HOMES INC","SKYH":"Sky Harbour Group Corporation","SKYT":"SkyWater Technology, Inc.","SKYW":"SKYWEST INC","SKYX":"SKYX Platforms Corp.","SKYY":"First Trust Cloud Computing ETF","SLAB":"Silicon Laboratories Inc - US","SLB":"SLB LIMITED","SLDB":"SOLID BIOSCIENCES INC","SLDE":"Slide Insurance Holdings, Inc.","SLDP":"SOLID POWER INC","SLF":"SUN  LIFE  FINANCIAL       INC.","SLG":"SL Green Realty Corp","SLGL":"Sol-Gel Technologies Ltd.","SLGN":"Silgan Holdings Inc.","SLI":"Standard Lithium Ltd.","SLM":"SLM CORP","SLNO":"SOLENO THERAPEUTICS INC","SLNZ":"TCW Senior Loan ETF","SLP":"Simulations Plus, Inc.","SLQD":"iShares 0-5 Year Investment Grade Corporate Bond ETF","SLQT":"SelectQuote, Inc.","SLRC":"SLR INVESTMENT CORP","SLS":"SELLAS Life Sciences Group, Inc.","SLSR":"Solaris Resources Inc.","SLV":"ISHARES SILVER TR","SLVM":"SYLVAMO CORP","SLVO":"ETRACS Silver Shares Covered Call ETNs due April 21, 2033","SLVP":"iShares MSCI Global Silver Miners Fund","SLVR":"Sprott Silver Miners & Physical Silver ETF","SLX":"VanEck Steel ETF","SLYG":"State Street SPDR S&P 600 Small Cap Growth ETF","SLYV":"State Street SPDR S&P 600 Small Cap Value ETF","SM":"SM Energy Company","SMA":"SmartStop Self Storage REIT, Inc.","SMB":"VanEck Short Muni ETF","SMBC":"Southern Missouri Bancorp, Inc.","SMBK":"SmartFinancial, Inc.","SMC":"Summit Midstream Corporation","SMCI":"SUPER MICRO COMPUTER INC","SMCX":"Defiance Daily Target 2X Long SMCI ETF","SMCY":"YieldMax SMCI Option Income Strategy ETF","SMDV":"ProShares Russell 2000 Dividend Growers ETF","SMFG":"Sumitomo Mitsui Financial Group Inc Unsponsored","SMG":"Scotts Miracle-Gro Company (The)","SMH":"VANECK ETF TRUST","SMHI":"SEACOR Marine Holdings Inc.","SMHX":"VanEck Fabless Semiconductor ETF","SMIG":"AAM Bahl & Gaynor Small/Mid Cap Income Growth ETF","SMIN":"Ishares MSCI India Small Cap ETF","SMIZ":"Zacks Small/Mid Cap ETF","SMLF":"iShares U.S. Small-Cap Equity Factor ETF","SMMD":"iShares Russell 2500 ETF","SMMT":"SUMMIT THERAPEUTICS INC","SMMU":"Short Term Municipal Bond Active Exchange-Traded Fund","SMOT":"VanEck Morningstar SMID Moat ETF","SMP":"Standard Motor Products, Inc.","SMPL":"The Simply Good Foods Company","SMR":"NUSCALE PWR CORP","SMRT":"SMARTRENT INC","SMTC":"SEMTECH CORP","SMTH":"ALPS Smith Core Plus Bond ETF","SMTI":"Sanara MedTech Inc.","SMWB":"Similarweb Ltd.","SN":"SHARKNINJA INC","SNA":"SNAP ON INC","SNAP":"SNAP INC","SNBR":"SLEEP NUMBER CORP","SNCY":"Sun Country Airlines Holdings, Inc.","SND":"Smart Sand, Inc.","SNDA":"Sonida Senior Living Inc","SNDK":"SANDISK CORP","SNDL":"SNDL Inc.","SNDR":"SCHNEIDER NATIONAL INC","SNDX":"SYNDAX PHARMACEUTICALS INC","SNEX":"StoneX Group Inc.","SNN":"Smith & Nephew SNATS, Inc.","SNOW":"SNOWFLAKE INC","SNPE":"Xtrackers S&P 500 Scored & Screened ETF","SNPS":"SYNOPSYS INC","SNTH":"MRP SynthEquity ETF","SNWV":"SANUWAVE Health, Inc.","SNX":"TD SYNNEX CORPORATION","SNXX":"Tradr 2X Long SNDK Daily ETF","SNY":"SANOFI SA","SO":"SOUTHERN CO","SOBO":"South Bow Corporation","SOC":"SABLE OFFSHORE CORP","SOCA":"Solarius Capital Acquisition Corp.","SOFI":"SOFI TECHNOLOGIES INC","SOFR":"Amplify Samsung SOFR ETF","SOLS":"Solstice Advanced Materials Inc.","SOLT":"2x Solana ETF","SOLV":"SOLVENTUM CORP","SON":"Sonoco Products Company","SONO":"SONOS INC","SONY":"SONY GROUP CORP","SOPH":"SOPHIA GENETICS SA","SOUL":"Soulpower Acquisition Corporation","SOUN":"SOUNDHOUND AI INC","SOXL":"DIREXION SHS ETF TR","SOXQ":"Invesco PHLX Semiconductor ETF","SOXS":"Direxion Daily Semiconductor Bear 3X Shares","SOXX":"iShares PHLX SOX Semiconductor Sector Index Fund","SPAB":"State Street SPDR Portfolio Aggregate Bond ETF","SPB":"Spectrum Brands Holdings, Inc.","SPBO":"State Street SPDR Portfolio Corporate Bond ETF","SPBU":"AllianzIM Buffer15 Uncapped Allocation ETF","SPCE":"VIRGIN GALACTIC HOLDINGS INC","SPDN":"Direxion Daily S&P 500 Bear 1X Shares","SPDW":"SPDR INDEX SHS FDS","SPEM":"State Street SPDR Portfolio Emerging Markets ETF","SPEU":"State Street SPDR Portfolio Europe ETF","SPFI":"South Plains Financial, Inc.","SPG":"SIMON PPTY GROUP INC NEW","SPGI":"S P GLOBAL INC","SPGM":"State Street SPDR Portfolio MSCI Global Stock Market ETF","SPGP":"Invesco S&P 500 GARP ETF","SPH":"Suburban Propane Partners, L.P.","SPHB":"Invesco S&P 500 High Beta ETF","SPHD":"Invesco S&P 500 High Dividend Low Volatility ETF","SPHQ":"Invesco S&P 500 Quality ETF","SPHR":"SPHERE ENTERTAINMENT CO","SPHY":"State Street SPDR Portfolio High Yield Bond ETF","SPIB":"State Street SPDR Portfolio Intermediate Term Corporate Bond ETF","SPIP":"State Street SPDR Portfolio TIPS ETF","SPIR":"Spire Global, Inc.","SPLB":"State Street SPDR Portfolio Long Term Corporate Bond ETF","SPLV":"Invesco S&P 500 Low Volatility ETF","SPMB":"STATE STREET SPDR PORTFOLIO MORTGAGE BACKED BOND ETF","SPMD":"SPDR SERIES TRUST","SPMO":"Invesco S&P 500 Momentum ETF","SPNT":"SiriusPoint Ltd.","SPOK":"Spok Holdings, Inc.","SPOT":"SPOTIFY TECHNOLOGY S A","SPRE":"SP Funds S&P Global REIT Sharia ETF","SPRO":"SPERO THERAPEUTICS INC","SPRX":"Spear Alpha ETF","SPRY":"ARS PHARMACEUTICALS INC","SPSB":"State Street SPDR Portfolio Short Term Corporate Bond ETF","SPSC":"SPS Commerce, Inc.","SPSK":"SP Funds Dow Jones Global Sukuk ETF","SPSM":"State Street SPDR Portfolio S&P 600 Small Cap ETF","SPT":"SPROUT SOCIAL INC","SPTE":"SP Funds S&P Global Technology ETF","SPTI":"State Street SPDR Portfolio Intermediate Term Treasury ETF","SPTL":"SPDR SER TR","SPTM":"State Street SPDR Portfolio S&P 1500 Composite Stock Market ETF","SPTS":"State Street SPDR Portfolio Short Term Treasury ETF","SPUS":"SP Funds S&P 500 Sharia Industry Exclusions ETF","SPUU":"Direxion Daily S&P 500 Bull 2X Shares","SPWO":"SP Funds S&P World (ex-US) ETF","SPWR":"SunPower Inc.","SPXC":"SPX   TECHNOLOGIES  INC","SPXL":"Direxion Daily S&P 500 Bull 3X Shares","SPXS":"Direxion Daily S&P 500 Bear 3X","SPXT":"ProShares S&P 500 Ex-Technology ETF","SPXU":"ProShares UltraPro Short S&P500","SPY":"SPDR S&amp;amp;P 500 ETF TR","SPYD":"State Street SPDR Portfolio S&P 500 High Dividend ETF","SPYG":"SPDR SERIES TRUST","SPYI":"NEOS S&P 500 High Income ETF","SPYM":"State Street SPDR Portfolio S&P 500 ETF","SPYT":"Defiance S&P 500 Target Income ETF","SPYU":"MAX S&P 500 4X Leveraged ETNs due October 30, 2043","SPYV":"SPDR SERIES TRUST","SPYX":"State Street SPDR S&P 500 Fossil Fuel Reserves Free ETF","SQM":"Sociedad Quimica y Minera S.A.","SQQQ":"ProShares UltraPro Short QQQ","SR":"SPIRE INC","SRAD":"SPORTRADAR GROUP AG","SRBK":"SR Bancorp, Inc.","SRCE":"1st Source Corporation","SRE":"DBA Sempra","SRET":"Global X SuperDividend REIT ETF","SRFM":"SURF AIR MOBILITY INC","SRI":"Stoneridge, Inc.","SRLN":"State Street Blackstone Senior Loan ETF","SRPT":"SAREPTA THERAPEUTICS INC","SRRK":"Scholar Rock Holding Corporation","SRTA":"BLADE AIR MOBILITY INC","SRVR":"Pacer Data & Infrastructure Real Estate ETF","SRZN":"SURROZEN INC","SSB":"SouthState Bank Corporation","SSD":"SIMPSON MFG INC","SSL":"Sasol Ltd.","SSNC":"SS&amp;C TECHNOLOGIES HLDGS INC","SSO":"ProShares Ultra S&P500","SSP":"E.W. Scripps Company (The)","SSRM":"SSR MINING IN","SSSS":"SURO CAPITAL CORP","SSTK":"SHUTTERSTOCK INC","SSUS":"Day Hagan Smart Sector ETF","SSYS":"STRATASYS LTD","ST":"SENSATA TECHNOLOGIES HLDG PL","STAA":"STAAR Surgical Company","STAG":"Stag Industrial, Inc.","STBA":"S&T Bancorp, Inc.","STC":"Stewart Information Services Corporation","STCE":"Schwab Crypto Thematic ETF","STE":"STERIS PLC","STEL":"STELLAR BANCORP INC","STEP":"STEPSTONE     GROUP    INC","STEX":"Streamex Corp.","STGW":"Stagwell Inc.","STIP":"iShares 0-5 Year TIPS Bond ETF","STKL":"SUNOPTA INC","STLA":"STELLANTIS N.V","STLD":"STEEL DYNAMICS INC","STM":"STMICROELECTRONICS N V","STN":"Stantec Inc","STNE":"STONECO LTD","STNG":"SCORPIO TANKERS INC","STOK":"STOKE THERAPEUTICS INC","STOT":"State Street DoubleLine Short Duration Total Return Tactical ETF","STPZ":"PIMCO 1-5 Year U.S. TIPS Index Exchange-Traded Fund","STRA":"Strategic Education, Inc.","STRL":"STERLING     INFRASTRUCTURE        INC","STRO":"Sutro Biopharma, Inc.","STRT":"STRATTEC SECURITY CORPORATION","STRV":"Strive 500 ETF","STRZ":"STARZ ENTERTAINMENT CORP.","STT":"State Street Corp.","STTK":"Shattuck Labs, Inc.","STUB":"STUBHUB HLDGS INC","STVN":"Stevanato Group S.p.A.","STWD":"Starwood Property Trust Inc.","STX":"SEAGATE TECHNOLOGY HLDNGS PL","STXS":"Stereotaxis, Inc.","STZ":"CONSTELLATION BRANDS INC","SU":"SUNCOR ENERGY INC NEW","SUB":"iShares Short-Term National Muni Bond ETF","SUI":"Sun Communities, Inc.","SUIG":"Sui Group Holdings Limited","SUN":"SUNOCO LP SUNOCO FIN CORP","SUNC":"SUNOCOCORP LLC","SUPN":"SUPERNUS PHARMACEUTICALS INC","SUPX":"SuperX AI Technology Limited","SUSA":"iShares ESG Optimized MSCI USA ETF","SUSB":"iShares ESG Aware 1-5 Year USD Corporate Bond ETF","SUSC":"iShares ESG Aware USD Corporate Bond ETF","SUSL":"iShares ESG MSCI USA Leaders ETF","SUUN":"PowerBank Corporation","SUZ":"Suzano S.A.","SVAC":"Spring Valley Acquisition Corp. III","SVAL":"iShares US Small Cap Value Factor ETF","SVAQ":"Silicon Valley Acquisition Corp.","SVIX":"-1x Short VIX Futures ETF","SVM":"SILVERCORP METALS INC","SVOL":"Simplify Volatility Premium ETF","SVRA":"SAVARA INC","SVV":"Savers Value Village, Inc.","SVXY":"ProShares Short VIX Short Term Futures ETF","SW":"SMURFIT WESTROCK PLC","SWBI":"Smith & Wesson Brands, Inc.","SWIM":"LATHAM GROUP","SWK":"STANLEY BLACK &amp; DECKER INC","SWKS":"SKYWORKS    SOLUTIONS     INC","SWX":"SOUTHWEST GAS HLDGS INC","SXC":"SunCoke Energy, Inc.","SXI":"Standex International Corporation","SXT":"SENSIENT TECHNOLOGIES CORP","SYBT":"Stock Yards Bancorp, Inc.","SYF":"SYNCHRONY FINANCIAL","SYFI":"AB Short Duration High Yield ETF","SYK":"STRYKER CORPORATION","SYLD":"Cambria Shareholder Yield ETF","SYM":"SYMBOTIC INC","SYNA":"Synaptics Incorporated","SYRE":"SPYRE THERAPEUTICS INC","SYSB":"iShares Systematic Bond ETF","SYY":"SYSCO CORP","T":"AT&amp;T INC","TAC":"TRANSALTA CORP","TACO":"BERTO ACQUISITION CORP","TAFI":"AB Tax-Aware Short Duration Municipal ETF","TAFM":"AB Tax-Aware Intermediate Municipal ETF","TAGG":"T. Rowe Price QM U.S. Bond ETF","TAIL":"Cambria Tail Risk ETF","TAK":"Takeda Pharmaceutical Company Limited","TAL":"TAL Education Group","TALK":"Talkspace, Inc.","TALO":"Talos Energy, Inc.","TAN":"INVESCO EXCH TRADED FD TR II","TAP":"Molson Coors Beverage Company","TARA":"Protara Therapeutics, Inc.","TARS":"TARSUS PHARMACEUTICALS INC","TASK":"TASKUS INC","TATT":"TAT TECHNOLOGIES LTD","TAXF":"American Century Diversified Municipal Bond ETF","TAXX":"BondBloxx IR+M Tax-Aware Short Duration ETF","TAYD":"Taylor Devices, Inc.","TBBB":"BBB FOODS INC","TBBK":"The Bancorp, Inc.","TBCH":"Turtle Beach Corporation","TBG":"TBG Dividend Focus ETF","TBI":"TrueBlue, Inc.","TBIL":"F/m US Treasury 3 Month Bill Fund","TBLA":"TABOOLA.COM LTD","TBLL":"Invesco Short Term Treasury ETF","TBN":"Tamboran Resources Corporation","TBPH":"Theravance Biopharma, Inc.","TBRG":"TruBridge, Inc.","TBT":"ProShares UltraShort Lehman 20 Year Treasury","TBUX":"T. Rowe Price Ultra Short-Term Bond ETF","TCAF":"T. Rowe Price Capital Appreciation Equity ETF","TCAL":"T. Rowe Price Capital Appreciation Premium Income ETF","TCBI":"Texas Capital Bancshares, Inc.","TCBK":"TRICO BANCSHARES","TCBX":"Third Coast Bancshares, Inc.","TCHP":"T. Rowe Price Blue Chip Growth ETF","TCMD":"TACTILE SYS TECHNOLOGY INC","TCOM":"Trip.com Group Limited","TCPB":"Thrivent Core Plus Bond ETF","TCPC":"BlackRock TCP Capital Corp.","TD":"Toronto Dominion Bank (The)","TDAQ":"TappAlpha Innovation 100 Growth & Daily Income ETF","TDAY":"USA TODAY Co., Inc.","TDC":"Teradata Corporation","TDG":"TRANSDIGM GROUP INC","TDI":"Touchstone Dynamic International ETF","TDIV":"First Trust NASDAQ Technology Dividend Index Fund","TDOC":"TELADOC HEALTH INC","TDS":"Telephone and Data Systems, Inc.","TDSC":"ETC Cabana Target Drawdown 10 ETF","TDTF":"FlexShares iBoxx 5 Year Target Duration TIPS Index Fund","TDTT":"FlexShares iBoxx 3 Year Target Duration TIPS Index Fund","TDUP":"THREDUP INC","TDV":"ProShares S&P Technology Dividend Aristocrats ETF","TDVG":"T ROWE PRICE ETF INC","TDW":"Tidewater Inc - US","TDY":"Teledyne Technologies Incorporated","TE":"T1 ENERGY INC","TEAM":"ATLASSIAN CORPORATION","TECB":"iShares U.S. Tech Breakthrough Multisector ETF","TECH":"BIO-TECHNE CORP","TECK":"Teck Resources Ltd., Class B","TECL":"Direxion Technology Bull 3X Shares","TECS":"Direxion Technology Bear 3X Shares","TECX":"TECTONIC THERAPEUTIC INC","TEL":"TE CONNECTIVITY PLC","TEM":"TEMPUS AI INC","TEN":"Tsakos Energy Navigation Ltd","TENB":"TENABLE HLDGS INC","TEO":"Telecom Argentina SA","TEQI":"T. Rowe Price Equity Income ETF","TER":"TERADYNE INC","TERN":"TERNS PHARMACEUTICALS INC","TEVA":"TEVA PHARMACEUTICAL INDS LTD","TEX":"TEREX CORP NEW","TFC":"TRUIST FINL CORP","TFI":"State Street SPDR Nuveen ICE Municipal Bond ETF","TFII":"TFI International Inc.","TFIN":"TRIUMPH FINANCIAL INC","TFLO":"iShares Treasury Floating Rate Bond ETF","TFLR":"T. Rowe Price Floating Rate ETF","TFPM":"TRIPLE FLAG PRECIOUS METAL","TFSL":"TFS Financial Corporation","TFX":"TELEFLEX INCORPORATED","TG":"Tredegar Corporation","TGB":"Taseko Mines Ltd - US","TGEN":"TECOGEN INC NEW","TGLS":"Tecnoglass Inc.","TGNA":"TEGNA INC","TGRT":"T. Rowe Price Growth ETF","TGRW":"T. Rowe Price Growth Stock ETF","TGS":"Transportadora de Gas del Sur SA TGS","TGT":"TARGET CORP","TGTX":"TG THERAPEUTICS INC","TH":"Target Hospitality Corp.","THC":"TENET HEALTHCARE CORP","THD":"iShares MSCI Thailand ETF","THFF":"First Financial Corporation","THG":"Hanover Insurance Group Inc","THIR":"THOR Index Rotation ETF","THM":"International Tower Hill Mines, Ltd.","THNQ":"ROBO Global Artificial Intelligence ETF","THO":"THOR INDS INC","THR":"Thermon Group Holdings, Inc.","THRM":"Gentherm Inc","THRO":"iShares U.S. Thematic Rotation Active ETF","THRY":"Thryv Holdings, Inc.","THYF":"T. Rowe Price U.S. High Yield ETF","TIC":"ACUREN CORP","TIGO":"Millicom International Cellular S.A.","TIGR":"UP Fintech Holding Limited","TII":"Titan Mining Corporation","TILE":"Interface, Inc.","TILT":"FlexShares Mornigstar US Market Factors Tilt Index Fund ETF","TIMB":"TIM S.A.","TIP":"ISHARES TR","TIPT":"TIPTREE INC","TIPX":"State Street SPDR Bloomberg 1a??10 Year TIPS ETF","TITN":"Titan Machinery Inc.","TJUL":"Innovator Equity Defined Protection ETF - 2 Yr to July 2027","TJX":"TJX COS INC NEW","TK":"Teekay Corporation Ltd.","TKC":"Turkcell Iletisim Hizmetleri AS","TKO":"TKO GROUP HOLDINGS INC","TKR":"Timken Company (The)","TLH":"iShares 10-20 Year Treasury Bond ETF","TLK":"PT Telekomunikasi Indonesia, Tbk","TLN":"TALEN ENERGY CORP","TLRY":"TILRAY BRANDS INC","TLS":"TELOS CORP MD","TLSI":"TriSalus Life Sciences, Inc.","TLT":"iShares 20+ Year Treasury Bond ETF","TLTD":"FlexShares Morningstar Developed Markets ex-US Factor Tilt Index Fund","TLTE":"FlexShares Morningstar Emerging Markets Factor Tilt Index Fund","TLTW":"iShares 20+ Year Treasury Bond BuyWrite Strategy ETF","TLX":"Telix Pharmaceuticals Limited","TM":"TOYOTA MOTOR CORP","TMC":"TMC THE METALS COMPANY INC","TMCI":"Treace Medical Concepts, Inc.","TMDX":"TRANSMEDICS GROUP INC","TME":"Tencent Music Entertainment Group","TMF":"Direxion Daily 20-Yr Treasury Bull 3x Shrs","TMFC":"Motley Fool 100 Index ETF","TMFG":"Motley Fool Global Opportunities ETF","TMHC":"TAYLOR MORRISON HOME CORP","TMO":"THERMO FISHER SCIENTIFIC INC","TMP":"Tompkins Financial Corporation","TMQ":"TRILOGY METALS INC NEW","TMSL":"T. Rowe Price Small-Mid Cap ETF","TMUS":"T-MOBILE US INC","TMV":"Direxion Daily 20-Year Treasury Bear 3X","TNA":"Direxion Small Cap Bull 3X Shares","TNC":"Tennant Company","TNDM":"TANDEM DIABETES CARE INC","TNET":"TRINET GROUP INC","TNGX":"TANGO THERAPEUTICS INC","TNK":"Teekay Tankers Ltd - US","TNL":"Travel Leisure Co.","TNXP":"Tonix Pharmaceuticals Holding Corp.","TNYA":"Tenaya Therapeutics, Inc.","TOGA":"Managed Portfolio Series Tremblant Global ETF","TOI":"The Oncology Institute, Inc.","TOL":"TOLL     BROTHERS     INC","TOLZ":"ProShares DJ Brookfield Global Infrastructure ETF","TONX":"TON Strategy Company","TOPT":"iShares Top 20 U.S. Stocks ETF","TOST":"TOAST INC","TOTL":"State Street DoubleLine Total Return Tactical ETF","TOUS":"T. Rowe Price International Equity ETF","TOWN":"Towne Bank","TOYO":"TOYO Co., Ltd","TPB":"TURNING PT BRANDS INC","TPC":"TUTOR PERINI CORP","TPG":"TPG Inc.","TPH":"TRI POINTE HOMES INC","TPHD":"Timothy Plan High Dividend Stock ETF","TPIF":"Timothy Plan International ETF","TPL":"Texas Pacific Land Corporation","TPLC":"Timothy Plan US Large/Mid Cap Core ETF","TPR":"TAPESTRY INC","TPSC":"Timothy Plan US Small Cap Core ETF","TPVG":"TriplePoint Venture Growth BDC Corp.","TPYP":"Tortoise North American Pipeline Fund","TQQQ":"PROSHARES TR","TR":"Tootsie Roll Industries, Inc.","TRAK":"ReposiTrak, Inc.","TRC":"Tejon Ranch Co","TRDA":"Entrada Therapeutics, Inc.","TREE":"LENDINGTREE INC NEW","TREX":"TREX CO INC","TRFK":"Pacer Data and Digital Revolution ETF","TRFM":"AAM Transformers ETF","TRGP":"TARGA RES CORP","TRI":"THOMSON REUTERS CORP","TRIN":"Trinity Capital Inc.","TRIP":"TRIPADVISOR INC","TRMB":"TRIMBLE    INC","TRMD":"TORM plc","TRMK":"Trustmark Corp - US","TRN":"Trinity Industries, Inc.","TRNO":"Terreno Realty Corp.","TRNS":"Transcat, Inc.","TROO":"TROOPS, Inc.","TROW":"PRICE T ROWE GROUP INC","TROX":"TRONOX HOLDINGS PLC","TRP":"TC ENERGY CORP","TRPA":"Hartford AAA CLO ETF","TRS":"TRIMAS CORP","TRST":"TrustCo Bank Corp NY","TRTX":"TPG RE Finance Trust, Inc.","TRU":"TRANSUNION","TRUP":"Trupanion Inc - US","TRV":"TRAVELERS COMPANIES INC","TRVI":"TREVI THERAPEUTICS INC","TRX":"TRX Gold Corporation","TS":"Tenaris S.A.","TSAT":"Telesat Corporation","TSBK":"Timberland Bancorp, Inc.","TSCO":"TRACTOR SUPPLY CO","TSEL":"Touchstone Sands Capital US Select Growth ETF","TSEM":"TOWER SEMICONDUCTOR LTD","TSHA":"TAYSHA GENE THERAPIES INC","TSLA":"TESLA INC","TSLL":"Direxion Daily TSLA Bull 2X Shares","TSLQ":"Tradr 2X Short TSLA Daily ETF","TSLR":"GraniteShares 2x Long TSLA Daily ETF","TSLT":"T-REX 2X Long Tesla Daily Target ETF","TSLW":"Roundhill TSLA WeeklyPay ETF","TSLX":"Sixth Street Specialty Lending, Inc.","TSLY":"YieldMax TSLA Option Income Strategy ETF","TSM":"TAIWAN SEMICONDUCTOR MFG LTD","TSME":"Thrivent Small-Mid Cap ESG ETF","TSMX":"Direxion Daily TSM Bull 2X Shares","TSN":"Tyson Foods Inc","TSPA":"T. Rowe Price U.S. Equity Research ETF","TSPY":"TappAlpha SPY Growth & Daily Income ETF","TSQ":"Townsquare Media, Inc.","TSSI":"TSS, Inc.","TSYY":"GraniteShares YieldBOOST TSLA ETF","TT":"TRANE TECHNOLOGIES PLC","TTAM":"Titan America SA","TTAN":"SERVICETITAN INC","TTC":"Toro Company (The)","TTD":"THE TRADE DESK INC","TTE":"TOTALENERGIES SE","TTEC":"TTEC Holdings, Inc.","TTEK":"TETRA TECH INC NEW","TTEQ":"T. Rowe Price Technology ETF","TTGT":"TechTarget, Inc.","TTI":"Tetra Technologies, Inc.","TTMI":"TTM TECHNOLOGIES INC","TTWO":"TAKE TWO INTERACTIVE SOFTWAR","TU":"TELUS CORPORATION","TUA":"Simplify Short Term Treasury Futures Strategy ETF","TUR":"iShares MSCI Turkey ETF","TUSB":"Thrivent Ultra Short Bond ETF","TUSI":"Touchstone Ultra Short Income ETF","TUYA":"TUYA INC","TV":"Grupo Televisa S.A.B.","TVA":"Texas Ventures Acquisition III Corp","TVAL":"T. Rowe Price Value ETF","TVTX":"TRAVERE THERAPEUTICS INC","TW":"TRADEWEB MKTS INC","TWFG":"TWFG, Inc.","TWI":"Titan International, Inc. (DE)","TWIN":"Twin Disc, Incorporated","TWLO":"TWILIO INC","TWO":"Two Harbors Investment Corp","TWST":"TWIST BIOSCIENCE CORP","TX":"Ternium S.A.","TXG":"10X GENOMICS INC","TXN":"TYSON FOODS INC","TXNM":"TXNM ENERGY INC","TXO":"TXO Partners, L.P.","TXRH":"TEXAS ROADHOUSE INC","TXT":"TEXTRON INC","TXUE":"Thornburg International Equity ETF","TYGO":"TIGO ENERGY INC","TYL":"TYLER TECHNOLOGIES INC","TYRA":"TYRA BIOSCIENCES INC","TZA":"Direxion Small Cap Bear 3X Shares","U":"UNITY SOFTWARE INC","UA":"Under Armour, Inc.","UAA":"UNDER ARMOUR INC","UAE":"iShares MSCI UAE ETF","UAL":"UNITED AIRLS HLDGS INC","UAMY":"United States Antimony Corporation","UAN":"CVR PARTNERS LP","UBER":"UBER TECHNOLOGIES INC","UBND":"VictoryShares Core Plus Bond ETF","UBS":"UBS GROUP AG","UBSI":"United Bankshares, Inc.","UCB":"United Community Banks, Inc.","UCO":"ProShares Ultra Bloomberg Crude Oil","UCON":"First Trust Smith Unconstrained Bond ETF","UCTT":"Ultra Clean Holdings, Inc.","UDEC":"Innovator U.S. Equity Ultra Buffer ETF - December","UDIV":"Franklin U.S. Core Dividend Tilt Index ETF","UDMY":"UDEMY INC","UDN":"Invesco DB USD Index Bearish ETF","UDOW":"ProShares UltraPro Dow30","UDR":"UDR Inc","UE":"Urban Edge Properties","UEC":"URANIUM ENERGY CORP","UFCS":"United Fire Group, Inc","UFEB":"Innovator U.S. Equity Ultra Buffer ETF - February","UFO":"Procure Space ETF","UFPI":"UFP Industries, Inc.","UFPT":"UFP TECHNOLOGIES INC","UGI":"UGI Corporation","UGL":"ProShares Ultra Gold","UGP":"Ultrapar Participacoes S.A. (New)","UHAL":"U HAUL HOLDING COMPANY","UHS":"UNIVERSAL HLTH SVCS INC","UHT":"Universal Health Realty Income Trust","UI":"UBIQUITI INC","UIS":"Unisys Corporation New","UITB":"VictoryShares Core Intermediate Bond ETF","UL":"UNILEVER PLC","ULCC":"Frontier Group Holdings, Inc.","ULS":"UL SOLUTIONS INC","ULST":"State Street Ultra Short Term Bond ETF","ULTA":"ULTA BEAUTY INC","ULTY":"YieldMax Ultra Option Income Strategy ETF","UMAC":"Unusual Machines, Inc.","UMBF":"UMB FINL CORP","UMC":"United Microelectronics Corporation (NEW)","UMH":"UMH Properties, Inc.","UMI":"USCF Midstream Energy Income Fund ETF","UMMA":"Wahed Dow Jones Islamic World ETF","UNCY":"Unicycive Therapeutics, Inc.","UNF":"UNIFIRST CORP MASS","UNFI":"United Natural Foods, Inc.","UNG":"United States Natural Gas Fund LP","UNH":"UNITEDHEALTH GROUP INC","UNIT":"UNITI GROUP LLC","UNIY":"WisdomTree Voya Yield Enhanced USD Universal Bond Fund","UNM":"Unum Group","UNOV":"Innovator U.S. Equity Ultra Buffer ETF - November","UNP":"UNION PAC CORP","UNTY":"Unity Bancorp, Inc.","UP":"WHEELS UP EXPERIENCE INC","UPB":"UPSTREAM BIO INC","UPBD":"UPBOUND GROUP INC","UPRO":"ProShares UltraPro S&P 500","UPS":"UNITED PARCEL SERVICE INC","UPST":"UPSTART HLDGS INC","UPWK":"UPWORK INC","URA":"Global X Uranium ETF","URBN":"URBAN OUTFITTERS INC","URG":"Ur Energy Inc","URGN":"UroGen Pharma Ltd.","URI":"UNITED RENTALS INC","URNJ":"Sprott Junior Uranium Miners ETF","URNM":"Sprott Uranium Miners ETF","UROY":"Uranium Royalty Corp.","URTH":"iShares MSCI World ETF","URTY":"ProShares UltraPro Russell2000","USAC":"USA Compression Partners, LP","USAR":"USA RARE EARTH INC","USAS":"Americas Gold and Silver Corporation","USAU":"U.S. Gold Corp.","USB":"US BANCORP DEL","USCB":"USCB Financial Holdings, Inc.","USCI":"United States Commodity Index Fund ETV","USD":"ProShares Ultra Semiconductors","USDU":"WisdomTree Bloomberg U.S. Dollar Bullish Fund","USDX":"SGI Enhanced Core ETF","USFD":"US FOODS HLDG CORP","USFR":"WisdomTree Floating Rate Treasury Fund","USGO":"U.S. GoldMining Inc.","USHY":"iShares Broad USD High Yield Corporate Bond ETF","USIG":"iShares Broad USD Investment Grade Corporate Bond ETF","USLM":"United States Lime & Minerals, Inc.","USMC":"Principal U.S. Mega-Cap ETF","USMF":"WisdomTree U.S. Multifactor Fund","USMV":"ISHARES TR","USNA":"USANA Health Sciences, Inc.","USO":"United States Oil Fund","USOI":"ETRACS Crude Oil Shares Covered Call ETNs due April 24, 2037","USPH":"U.S. Physical Therapy, Inc.","USPX":"Franklin U.S. Equity Index ETF","USRT":"iShares Core U.S. REIT ETF","USSE":"Segall Bryant & Hamill Trust Segall Bryant & Hamill Select Equity ETF","USSG":"Xtrackers MSCI USA Selection Equity ETF","USTB":"VictoryShares Short-Term Bond ETF","USVM":"VictoryShares US Small Mid Cap Value Momentum ETF","USXF":"iShares ESG Advanced MSCI USA ETF","UTEN":"US Treasury 10 Year Note ETF","UTES":"Virtus Reaves Utilities ETF","UTHR":"UNITED THERAPEUTICS CORP DEL","UTI":"Universal Technical Institute Inc","UTL":"UNITIL Corporation","UTMD":"Utah Medical Products, Inc.","UTWO":"US Treasury 2 Year Note ETF","UTZ":"Utz Brands Inc","UUP":"Invesco DB USD Index Bullish Fund ETF","UUUU":"ENERGY FUELS INC","UVE":"UNIVERSAL INSURANCE HOLDINGS INC","UVIX":"2x Long VIX Futures ETF","UVSP":"Univest Financial Corporation","UVV":"Universal Corporation","UVXY":"ProShares Ultra VIX Short Term Futures ETF","UWM":"ProShares Ultra Russell2000","UWMC":"UWM HOLDINGS CORPORATION","UYG":"ProShares Ultra Financials","UYLD":"Angel Oak UltraShort Income ETF","V":"VISA INC","VAC":"MARRIOTT VACATIONS WORLD","VACI":"Viking Acquisition Corp. I","VAL":"VALARIS LTD","VALE":"VALE S A","VAW":"Vanguard Materials ETF","VB":"VANGUARD INDEX FDS","VBIL":"Vanguard 0-3 Month Treasury Bill ETF","VBK":"Vanguard Small-Cap Growth ETF","VBND":"Vident U.S. Bond Strategy ETF","VBNK":"VersaBank","VBR":"VANGUARD INDEX FDS","VC":"VISTEON CORP","VCEB":"Vanguard World Funds ETF","VCEL":"VERICEL CORP","VCIT":"Vanguard Intermediate-Term Corporate Bond ETF","VCLT":"Vanguard Long-Term Corporate Bond ETF","VCOB":"Voya Core Bond ETF","VCR":"VANGUARD WORLD FD","VCRB":"Vanguard Core Bond ETF","VCSH":"VANGUARD SCOTTSDALE FDS","VCTR":"Victory Capital Holdings, Inc. Class A Common Stock","VCYT":"VERACYTE INC","VDC":"VANGUARD WORLD FD","VDE":"Vanguard Energy ETF","VEA":"VANGUARD INDEX FDS","VECO":"Veeco Instruments Inc.","VEEV":"<![CDATA[VEEVA SYS INC]]>","VEGI":"iShares MSCI Agriculture Producers ETF","VEGN":"US Vegan Climate Index","VEL":"Velocity Financial, Inc.","VELO":"Velo3D, Inc.","VENU":"Venu Holding Corporation","VEON":"VEON Ltd.","VERA":"VERA THERAPEUTICS INC","VERI":"VERITONE INC","VERX":"VERTEX INC","VET":"VERMILION   ENERGY       INC","VEU":"Vanguard FTSE All World Ex US ETF","VEXC":"Vanguard Emerging Markets Ex-China ETF","VFC":"V F CORP","VFF":"Village Farms International, Inc.","VFH":"VANGUARD WORLD FD","VFLO":"VictoryShares Free Cash Flow ETF","VFMF":"Vanguard U.S. Multifactor ETF","VFMO":"Vanguard U.S. Momentum Factor ETF","VFMV":"Vanguard U.S. Minimum Volatility ETF","VFQY":"Vanguard U.S. Quality Factor ETF","VFS":"VinFast Auto Ltd.","VFVA":"Vanguard Wellington Fund ETF","VG":"Venture Global Inc - US","VGIT":"VANGUARD ADMIRAL FDS INC","VGK":"Vanguard FTSEEuropean ETF","VGLT":"VANGUARD STAR FDS","VGSH":"Vanguard Short-Term Treasury ETF","VGSR":"Vert Global Sustainable Real Estate ETF","VGT":"VANGUARD WORLD FD","VGUS":"Vanguard Ultra-Short Treasury ETF","VGZ":"Vista Gold Corp","VHT":"VANGUARD SPECIALIZED FUNDS","VHUB":"VenHub Global, Inc.","VIA":"Via Transportation, Inc.","VIAV":"VIAVI   SOLUTIONS   INC","VICI":"VICI Properties, Inc.","VICR":"VICOR CORP","VIDI":"Vident International Equity Strategy ETF","VIG":"Vanguard Div Appreciation ETF","VIGI":"Vanguard International Dividend Appreciation ETF","VIK":"VIKING HOLDINGS LTD","VINP":"Vinci Compass Investments Ltd.","VIOG":"Vanguard S&P Small-Cap 600 Growth ETF","VIOO":"Vanguard S&P Small-Cap 600 ETF","VIOV":"Vanguard S&P Small-Cap 600 Value ETF","VIPS":"Vipshop Holdings Limited","VIR":"VIR BIOTECHNOLOGY INC","VIRT":"Virtu Financial, Inc.","VIS":"VANGUARD WORLD FD","VISN":"Vistance Networks, Inc.","VIST":"Vista Energy S.A.B. de C.V.","VITL":"VITAL FARMS INC","VIV":"Telefonica Brasil S.A.","VIXY":"VIX Short-Term Futures ETF","VKTX":"VIKING THERAPEUTICS INC","VLGEA":"Village Super Market, Inc.","VLN":"Valens Semiconductor Ltd.","VLO":"Valero Energy Corporation","VLTO":"VERALTO CORP","VLU":"State Street SPDR S&P 1500 Value Tilt ETF","VLUE":"ISHARES TR","VLY":"Valley National Bancorp","VMBS":"VANGUARD MALVERN FDS","VMC":"VULCAN MATLS CO","VMD":"Viemed Healthcare, Inc.","VMI":"VALMONT INDS INC","VMSB":"Voya Multi-Sector Income ETF","VNDA":"Vanda Pharmaceuticals Inc.","VNET":"VNET   GROUP    INC","VNLA":"Janus Henderson Short Duration Income ETF","VNM":"VanEck Vietnam ETF","VNO":"Vornado Realty Trust","VNOM":"VIPER ENERGY INC","VNQ":"Vanguard Real Estate ETF","VNQI":"Vanguard Global ex-U.S. Real Estate ETF","VNT":"VONTIER CORPORATION","VO":"VANGUARD INDEX FDS","VOD":"VODAFONE GROUP PLC NEW","VOE":"Vanguard Mid-Cap Value ETF","VOLT":"Tema Electrification ETF","VONE":"Vanguard Russell 1000 ETF","VONG":"Vanguard Russell 1000 Growth ETF","VONV":"Vanguard Russell 1000 Value ETF","VOO":"VANGUARD INDEX FDS","VOOG":"Vanguard S&P 500 Growth ETF","VOOV":"Vanguard S&P 500 Value ETF","VOR":"Vor Biopharma Inc.","VOT":"Vanguard Mid-Cap Growth ETF","VOTE":"TCW Transform 500 ETF","VOX":"VANGUARD WORLD FD","VOXR":"Vox Royalty Corp.","VOYA":"VOYA       FINANCIAL      INC","VOYG":"VOYAGER TECHNOLOGIES INC","VPG":"Vishay Precision Group, Inc.","VPL":"Vanguard FTSE Pacific ETF","VPLS":"Vanguard Core Plus Bond ETF","VPU":"Vanguard Utilities ETF","VRDN":"Viridian Therapeutics, Inc.","VRE":"Veris Residential, Inc.","VREX":"Varex Imaging Corporation","VRIG":"Invesco Variable Rate Investment Grade ETF","VRNS":"VARONIS SYS INC","VRP":"Invesco Variable Rate Preferred ETF","VRRM":"VERRA MOBILITY CORP","VRSK":"VERISK ANALYTICS INC","VRSN":"VERISIGN INC","VRT":"VERTIV HOLDINGS CO","VRTS":"Virtus Investment Partners, Inc.","VRTX":"VERTEX PHARMACEUTICALS INC","VSAT":"Viasat Inc - US","VSCO":"Victorias Secret & Co.","VSDA":"VictoryShares Dividend Accelerator ETF","VSEC":"VSE Corporation","VSGX":"Vanguard ESG International Stock ETF","VSH":"VISHAY INTERTECHNOLOGY INC","VSLU":"Applied Finance Valuation Large Cap ETF","VSNT":"Versant Media Group, Inc.","VSS":"Vanguard FTSE All-Wld ex-US SmCp Idx ETF","VST":"VISTRA CORP","VSTM":"Verastem, Inc.","VSTS":"Vestis Corporation","VT":"Vanguard Total World Stock Index ETF","VTC":"Vanguard Total Corporate Bond ETF","VTEB":"VANGUARD SCOTTSDALE FDS","VTES":"Vanguard Wellington Fund Vanguard Short-Term Tax Exempt Bond ETF","VTEX":"VTEX","VTHR":"Vanguard Russell 3000 ETF","VTI":"VANGUARD INDEX FDS","VTIP":"Vanguard Short-Term Inflation-Protected Securities Index Fund ETF Shares","VTIX":"Virtuix Holdings Inc.","VTOL":"Bristow Group, Inc.","VTR":"VENTAS INC","VTRS":"VIATRIS INC","VTS":"Vitesse Energy Inc.","VTV":"VANGUARD INDEX FDS","VTVT":"vTv Therapeutics Inc.","VTWG":"Vanguard Russell 2000 Growth ETF","VTWO":"Vanguard Russell 2000 ETF","VTWV":"Vanguard Russell 2000 Value ETF","VTYX":"Ventyx Biosciences Inc - US","VUG":"VANGUARD INDEX FDS","VUSB":"Vanguard Ultra-Short Bond ETF","VUSE":"Vident Core US Equity ETF","VUZI":"VUZIX CORP","VV":"Vanguard Large-Cap ETF","VVV":"VALVOLINE     INC","VVX":"V2X, Inc.","VWAV":"VisionWave Holdings, Inc.","VWO":"VANGUARD INTL EQUITY INDEX F","VWOB":"Vanguard Emerging Markets Government Bond ETF","VXF":"Vanguard Extended Market ETF","VXUS":"VANGUARD INTL EQUITY INDEX F","VXX":"iPath Series B S&P 500 VIX Short-Term Futures ETN","VYGR":"VOYAGER THERAPEUTICS INC","VYM":"VANGUARD WHITEHALL FDS","VYMI":"Vanguard International High Dividend Yield ETF","VYX":"NCR VOYIX CORPORATION","VZ":"VERIZON COMMUNICATIONS INC","VZLA":"Vizsla Silver Corp.","W":"WAYFAIR INC","WAB":"WABTEC","WABC":"Westamerica Bancorporation","WAFD":"WaFd, Inc.","WAGN":"Pabrai Wagons ETF","WAL":"Western Alliance Bancorporation","WASH":"Washington Trust Bancorp, Inc.","WAT":"WATERS CORP","WAY":"Waystar Holding Corp.","WB":"Weibo Corporation","WBD":"WARNER BROS DISCOVERY INC","WBI":"WaterBridge Infrastructure LLC","WBS":"WEBSTER FINL CORP","WBTN":"WEBTOON Entertainment Inc.","WCC":"Wesco International, Inc.","WCLD":"WisdomTree Cloud Computing Fund","WCMI":"First Trust WCM International Equity ETF","WCN":"WASTE CONNECTIONS INC","WCPB":"Weitz Core Plus Bond ETF","WD":"Walker &amp; Dunlop Inc","WDAY":"WORKDAY INC","WDC":"WESTERN DIGITAL CORP","WDFC":"WD 40 CO","WDIV":"State Street SPDR S&P Global Dividend ETF","WDS":"Woodside Energy Group Limited","WEAT":"Teucrium Wheat Fund ETV","WEAV":"<![CDATA[WEAVE COMMUNICATIONS INC]]>","WEC":"WEC ENERGY GROUP INC","WEEK":"Roundhill Weekly T-Bill ETF","WELL":"WELLTOWER INC","WEN":"WENDYS CO","WENN":"WEN ACQUISITION CORP","WERN":"WERNER ENTERPRISES INC","WES":"Western Midstream Partners, LP","WEST":"Westrock Coffee Company","WEX":"WEX INC","WF":"Woori Financial Group Inc.","WFC":"WELLS FARGO CO NEW","WFG":"West Fraser Timber Co. Ltd","WFRD":"Weatherford International plc","WGMI":"CoinShares Bitcoin Mining ETF","WGO":"Winnebago Industries, Inc.","WGS":"GeneDx Holdings Corp.","WH":"WYNDHAM HOTELS   RESORTS INC","WHD":"Cactus, Inc. Class A Common Stock","WHF":"WhiteHorse Finance, Inc.","WHR":"WHIRLPOOL CORP","WINA":"Winmark Corporation","WING":"WINGSTOP INC","WINN":"Harbor Long-Term Growers ETF","WIP":"SPDR FTSE International Government Inflation-Protected Bond ETF","WIT":"Wipro Limited","WIX":"WIX COM LTD","WK":"WORKIVA INC","WKC":"WORLD KINECT CORPORATION","WLAC":"WILLOW LANE ACQUISITION CORP","WLDN":"WILLDAN GROUP INC","WLFC":"Willis Lease Finance Corporation","WLK":"WESTLAKE CORPORATION","WLKP":"Westlake Chemical Partners LP","WLTH":"WEALTHFRONT CORP","WLY":"John Wiley & Sons, Inc.","WM":"WASTE MGMT INC DEL","WMB":"WILLIAMS COS INC","WMG":"WARNER MUSIC GROUP CORP","WMK":"Weis Markets, Inc.","WMS":"ADVANCED DRAIN SYS INC DEL","WMT":"WALMART INC","WNC":"Wabash National Corporation","WNEB":"Western New England Bancorp, Inc.","WOLF":"WOLFSPEED INC","WOOD":"iShares Global Timber & Forestry ETF","WOOF":"Petco Health and Wellness Company, Inc.","WOR":"WORTHINGTON ENTERPRISES INC","WPAY":"Roundhill WeeklyPay Universe ETF","WPC":"W. P. Carey Inc. REIT","WPM":"WHEATON   PRECIOUS    METALS        CORP","WPP":"WPP plc","WRB":"BERKLEY W R CORP","WRBY":"WARBY PARKER INC","WRD":"WERIDE INC","WRLD":"World Acceptance Corporation","WRN":"Western Copper and Gold Corporation","WS":"Worthington Steel, Inc.","WSBC":"WESBANCO INC","WSBF":"Waterstone Financial, Inc.","WSC":"WILLSCOT HLDGS CORP","WSFS":"WSFS Financial Corporation","WSHP":"WeShop Holdings Limited","WSM":"WILLIAMS SONOMA INC","WSO":"WATSCO INC","WSR":"Whitestone REIT","WST":"WEST PHARMACEUTICAL SVSC INC","WT":"WISDOMTREE INC","WTAI":"WisdomTree Artificial Intelligence and Innovation Fund","WTBA":"West Bancorporation","WTFC":"WINTRUST FINL CORP","WTI":"W&T Offshore, Inc.","WTM":"White Mountains Insurance Group, Ltd.","WTMF":"WisdomTree Managed Futures Strategy Fund","WTPI":"WisdomTree Equity Premium Income Fund","WTRG":"Essential Utilities, Inc.","WTS":"WATTS WATER TECHNOLOGIES INC","WTTR":"Select Water Solutions, Inc.","WTV":"WisdomTree U.S. Value Fund","WTW":"WILLIS TOWERS WATSON PLC LTD","WU":"Western Union Company (The)","WULF":"TERAWULF INC","WVE":"WAVE LIFE SCIENCES LTD","WW":"WW International, Inc.","WWD":"WOODWARD INC","WWJD":"Inspire International ETF","WWR":"Westwater Resources, Inc.","WWW":"WOLVERINE WORLD WIDE INC","WY":"Weyerhaeuser Company","WYFI":"WHITEFIBER INC","WYNN":"WYNN RESORTS LTD","XAR":"State Street SPDR S&P Aerospace & Defense ETF","XBI":"State Street SPDR S&P Biotech ETF","XBIL":"US Treasury 6 Month Bill ETF","XCCC":"BondBloxx CCC-Rated USD High Yield Corporate Bond ETF","XCEM":"Columbia EM Core ex-China ETF","XDTE":"Roundhill S&P 500 0DTE Covered Call Strategy ETF","XEL":"XCEL ENERGY INC","XEMD":"BondBloxx JP Morgan USD Emerging Markets 1-10 Year Bond ETF","XENE":"XENON PHARMACEUTICALS INC","XERS":"XERIS BIOPHARMA HOLDINGS INC","XES":"State Street SPDR S&P Oil & Gas Equipment & Services ETF","XFIV":"BondBloxx Bloomberg Five Year Target Duration US Treasury ETF","XFOR":"X4 Pharmaceuticals, Inc.","XHB":"State Street SPDR S&P Homebuilders ETF","XHLF":"BondBloxx Bloomberg Six Month Target Duration US Treasury ETF","XHR":"","XIFR":"XPLR INFRASTRUCTURE LP","XJH":"iShares ESG Select Screened S&P Mid-Cap ETF","XJR":"iShares ESG Select Screened S&P Small-Cap ETF","XLB":"SELECT SECTOR SPDR TR","XLC":"SELECT SECTOR SPDR TR","XLE":"SELECT SECTOR SPDR TR","XLF":"SELECT SECTOR SPDR TR","XLG":"Invesco S&P 500 Top 50 ETF","XLI":"SELECT SECTOR SPDR TR","XLK":"SELECT SECTOR SPDR TR","XLP":"State Street Consumer Staples Select Sector SPDR ETF","XLRE":"SELECT SECTOR SPDR TR","XLSR":"State Street US Sector Rotation ETF","XLU":"SELECT SECTOR SPDR TR","XLV":"SELECT SECTOR SPDR TR","XLY":"State Street Consumer Discretionary Select Sector SPDR ETF","XMAG":"Defiance Large Cap ex-Mag 7 ETF","XMAR":"FT Vest U.S. Equity Enhance & Moderate Buffer ETF - March","XME":"State Street SPDR S&P Metals & Mining ETF","XMHQ":"Invesco S&P MidCap Quality ETF","XMLV":"Invesco S&P MidCap Low Volatility ETF","XMMO":"Invesco S&P MidCap Momentum ETF","XMPT":"VanEck CEF Muni Income ETF","XMTR":"XOMETRY INC","XMVM":"Invesco S&P MidCap Value with Momentum ETF","XNCR":"XENCOR INC","XNTK":"State Street SPDR NYSE Technology ETF","XOM":"EXXON MOBIL CORP","XOMA":"XOMA Royalty Corporation","XONE":"BondBloxx Bloomberg One Year Target Duration US Treasury ETF","XOP":"State Street SPDR S&P Oil & Gas Exploration & Production ETF","XOVR":"ERShares Private-Public Crossover ETF","XP":"XP Inc.","XPAY":"Roundhill S&P 500 Target 20 Managed Distribution ETF","XPEL":"XPEL INC","XPER":"Xperi Inc.","XPEV":"XPENG INC","XPH":"State Street SPDR S&P Pharmaceuticals ETF","XPO":"XPO INC","XPOF":"XPONENTIAL FITNESS INC","XPRO":"Expro Group Holdings N.V.","XRAY":"DENTSPLY SIRONA INC","XRP":"Bitwise XRP ETF","XRPC":"CANARY XRP ETF","XRPI":"Volatility Shares Trust XRP ETF","XRT":"State Street SPDR S&P Retail ETF","XRX":"XEROX HOLDINGS CORP","XSD":"State Street SPDR S&P Semiconductor ETF","XSHQ":"Invesco S&P SmallCap Quality ETF","XSMO":"Invesco S&P SmallCap Momentum ETF","XSOE":"WisdomTree Emerging Markets Ex-State Owned Enterprises Fund","XSVM":"Invesco S&P SmallCap Value with Momentum ETF","XSVN":"BondBloxx Bloomberg Seven Year Target Duration US Treasury ETF","XSW":"State Street SPDR S&P Software & Services ETF","XT":"iShares Future Exponential Technologies ETF","XTEN":"BondBloxx Bloomberg Ten Year Target Duration US Treasury ETF","XTL":"State Street SPDR S&P Telecom ETF","XTN":"State Street SPDR S&P Transportation ETF","XTRE":"BondBloxx Bloomberg Three Year Target Duration US Treasury ETF","XTWO":"BondBloxx Bloomberg Two Year Target Duration US Treasury ETF","XVV":"iShares ESG Select Screened S&P 500 ETF","XWIN":"XMAX, Inc.","XXI":"Twenty One Capital, Inc.","XXRP":"Teucrium 2x Long Daily XRP ETF","XYL":"XYLEM  INC","XYLD":"Global X S&P 500 Covered Call ETF","XYZ":"BLOCK INC","XZO":"Exzeo Group, Inc.","YANG":"Direxion Daily FTSE China Bear 3X Shares","YBTC":"Roundhill Bitcoin Covered Call Strategy ETF","YDEC":"FT Vest International Equity Moderate Buffer ETF - December","YEAR":"AB Ultra Short Income ETF","YELP":"YELP INC","YETI":"YETI HLDGS INC","YEXT":"YEXT INC","YINN":"Direxion Daily FTSE China Bull 3X Shares","YJUN":"FT Vest International Equity Moderate Buffer ETF - June","YLD":"Principal Active High Yield ETF","YLDE":"Franklin ClearBridge Enhanced Income ETF","YMAG":"YieldMax Magnificent 7 Fund of Option Income ETFs","YMAX":"YieldMax Universe Fund of Option Income ETFs","YMM":"FULL TRUCK ALLIANCE CO LTD","YORW":"The York Water Company","YOU":"CLEAR SECURE INC","YPF":"YPF SOCIEDAD ANONIMA","YSEP":"FT Vest International Equity Buffer ETF - September","YSS":"York Space Systems Inc.","YUM":"YUM BRANDS INC","YUMC":"Yum China Holdings, Inc.","YYY":"Amplify CEF High Income ETF","Z":"ZILLOW GROUP INC","ZALT":"Innovator U.S. Equity 10 Buffer ETF - Quarterly","ZAP":"Global X U.S. Electrification ETF","ZBH":"ZIMMER BIOMET HOLDINGS INC","ZBIO":"ZENAS BIOPHARMA INC","ZBRA":"Zebra Technologies Corporation","ZD":"ZIFF DAVIS INC","ZECP":"Zacks Earnings Consistent Portfolio ETF","ZENA":"ZenaTech, Inc.","ZETA":"ZETA GLOBAL HOLDINGS CORP","ZG":"Zillow Group, Inc.","ZGN":"Ermenegildo Zegna N.V.","ZIM":"ZIM Integrated Shipping Services Ltd.","ZION":"Zions Bancorporation N.A.","ZIP":"ZIPRECRUITER INC","ZLAB":"Zai Lab Limited","ZM":"ZOOM COMMUNICATIONS INC","ZNTL":"Zentalis Pharmaceuticals, Inc.","ZROZ":"PIMCO 25 Year Zero Coupon U.S. Treasury Index Exchange-Traded Fund","ZS":"ZSCALER INC","ZSL":"ProShares UltraShort Silver","ZTO":"","ZTS":"ZOETIS INC","ZUMZ":"Zumiez Inc.","ZURA":"Zura Bio Limited","ZVIA":"Zevia PBC","ZVRA":"Zevra Therapeutics Inc - US","ZWS":"ZURN ELKAY WATER SOLNS CORP","ZYME":"ZYMEWORKS INC","REVG":"REV GROUP INC","JYNT":"JOINT CORP","SGU":"STAR GROUP L P","BTMD":"BIOTE CORP","RRGB":"RED ROBIN GOURMET BURGERS IN","CYBR":"CYBERARK SOFTWARE LTD","GEO":"GEO GROUP INC NEW","ITRYF":"ISHARES INC","BRK.B":"BERKSHIRE HATHAWAY INC DEL","ARMN":"ARIS MNG CORP","OABI":"OMNIAB INC","MXCT":"MAXCYTE INC","CNTB":"CENTESSA PHARMACEUTICALS PLC","DAY":"DAYFORCE INC","ASRT":"ASSERTIO HOLDINGS INC","CDLX":"CARDLYTICS INC","THS":"TREEHOUSE FOODS INC","LNW":"LIGHT &amp; WONDER INC","HEI.A":"HEICO CORP NEW","FERA":"FIFTH ERA ACQUISITION CORP I","CCCS":"CCC INTELLIGENT SOLUTIONS HL","FYBR":"FRONTIER COMMUNICATIONS PARE","PCH":"POTLATCHDELTIC CORPORATION","ELME":"ELME COMMUNITIES","DBRG":"DIGITALBRIDGE GROUP INC","CDXS":"CODEXIS INC","AXL":"AMERICAN AXLE &amp; MFG HLDGS IN","GUTS":"FRACTYL HEALTH INC","CYTO":"CYTOKINETICS INC","DNP":"DNP SELECT INCOME FD INC","ATVI":"AUTOMATIC DATA PROCESSING IN","ATGE":"ADTALEM GLOBAL ED INC","MMC":"MARSH &amp; MCLENNAN COS INC","CMMB":"COMMERCE.COM INC","ETHZ":"ETHZILLA CORPORATION","OMEX":"ODYSSEY MARINE EXPL INC","HEPS":"D MARKET ELECTR SVCS &amp; TRADI","PLRX":"PLIANT THERAPEUTICS INC","GCI":"USA TODAY CO INC","ETNB":"89BIO INC","SKYD":"PARAMOUNT SKYDANCE CORP","BWC":"BABCOCK &amp; WILCOX ENTERPRISES","CAN":"CANAAN INC","CNHI":"CNH INDL N V","BRK.A":"Berkshire Hathaway Inc., Class A","BRAV":"ATLANTA BRAVES HLDGS INC","CWEN.A":"CLEARWAY ENERGY INC","BF.A":"BROWN FORMAN CORP"};

// ranks assigned after data loads in loadAppData()

function _applyThemesData(rows, sourceUpdatedAtIso=''){
  THEMES_DATA.length = 0;
  (rows || []).forEach((r, i) => {
    if (!r || !r.ticker) return;
    r.cat = r.cat || r.theme || '';
    r.theme = r.theme || r.cat || '';
    r.rank = i + 1;
    THEMES_DATA.push(r);
    blRememberTickerCompany(r.ticker, r.name);
  });
  const srcTs = _parseSourceTs(sourceUpdatedAtIso);
  if (srcTs) {
    _themesLastLoadedAt = srcTs;
    _updateRefreshTs('themes', new Date(srcTs));
    _updateRefreshTs('heatmap-themes', new Date(srcTs));
  } else if (THEMES_DATA.length) {
    _themesLastLoadedAt = Date.now();
    _updateRefreshTs('themes');
    _updateRefreshTs('heatmap-themes');
  }
}

function _themesDataStale(){
  const now = Date.now();
  if (!_themesLastCheckedAt) return true;
  if ((now - _themesLastCheckedAt) > THEMES_REFRESH_MS) return true;
  // Also treat stale source timestamps as stale, even if we checked recently.
  if (!_themesLastLoadedAt) return true;
  return (now - _themesLastLoadedAt) > THEMES_REFRESH_MS;
}

function _renderThemesLoading(msg='Loading themes...'){
  const body = document.getElementById('thBody');
  const cnt = document.getElementById('thCnt');
  if (body) body.innerHTML = `<tr><td colspan="14" class="muted" style="text-align:center;padding:16px">${msg}</td></tr>`;
  if (cnt) cnt.textContent = 'Loading...';
}
function _setThemesCountUpdating(updating){
  const el=document.getElementById('thCnt');
  if(!el) return;
  const isUpdating = !!updating || !!_themesServerRefreshing;
  if(!el.dataset.baseCount){
    const n=Array.isArray(THEMES_DATA)?THEMES_DATA.length:0;
    setCountMeta('thCnt', `${Number(n||0).toLocaleString()} themes`, 0, isUpdating);
    return;
  }
  setCountUpdating('thCnt', isUpdating);
}

async function ensureThemesData(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_themesDataStale() && !_themesServerRefreshing) return THEMES_DATA;
  if (_themesFetchPromise) {
    _setThemesCountUpdating(true);
    return _themesFetchPromise;
  }
  if (!background && !THEMES_DATA.length) _renderThemesLoading('Loading themes...');
  const _themesUpdateToken = ++_themesUpdatingToken;
  const _themesUpdateStartedAt = Date.now();
  if (THEMES_DATA.length) _setThemesCountUpdating(true);
  _themesFetchPromise = fetch('/api/themes')
    .then(r => {
      if (!r.ok) throw new Error('Themes ' + r.status);
      const sourceUpdatedAt = r.headers.get('X-Gekko-Source-Updated-At') || '';
      const refreshing = String(r.headers.get('X-Gekko-Refreshing') || '0') === '1';
      return r.json().then(rows => ({ rows, sourceUpdatedAt, refreshing }));
    })
    .then(({rows, sourceUpdatedAt, refreshing}) => {
      _themesServerRefreshing = !!refreshing;
      _applyThemesData(Array.isArray(rows) ? rows : [], sourceUpdatedAt);
      if (_themesServerRefreshing && !THEMES_DATA.length && !background) {
        _renderThemesLoading('Updating themes... this can take a minute');
      }
      if (refreshing) {
        _scheduleAutoRefresh('themes', () => {
          ensureThemesData(false, {background:true}).then(() => {
            if (document.getElementById('tab-themes')?.classList.contains('active')) thFilter();
            if (document.getElementById('tab-heatmap')?.classList.contains('active') && _hmView==='themes') renderHeatmap();
          }).catch(() => {});
        }, 12000);
      }
      return THEMES_DATA;
    })
    .catch(err => {
      _themesServerRefreshing = false;
      if (!THEMES_DATA.length && !background) {
        const body = document.getElementById('thBody');
        const cnt = document.getElementById('thCnt');
        if (body) body.innerHTML = '<tr><td colspan="14" class="muted" style="text-align:center;padding:16px">Failed to load themes.</td></tr>';
        if (cnt) cnt.textContent = '0 themes';
      }
      throw err;
    })
    .finally(() => {
      _themesFetchPromise = null;
      _themesLastCheckedAt = Date.now();
      const _clearUpdating = () => {
        if (_themesUpdateToken !== _themesUpdatingToken) return;
        _setThemesCountUpdating(false);
      };
      const _elapsed = Date.now() - _themesUpdateStartedAt;
      const _wait = Math.max(0, THEMES_UPDATING_MIN_MS - _elapsed);
      if (_wait > 0) setTimeout(_clearUpdating, _wait);
      else _clearUpdating();
    });
  return _themesFetchPromise;
}

function _applyConvictionData(rows, sourceUpdatedAtIso=''){
  CONV.length = 0;
  (rows || []).forEach((r, i) => {
    if (!r || !r.ticker) return;
    r.rank = i + 1;
    // Backfill missing company name from local lookup table
    if (!r.company) r.company = BL_TICKER_INFO[r.ticker] || '';
    CONV.push(r);
    blRememberTickerCompany(r.ticker, r.company);
  });
  const srcTs = _parseSourceTs(sourceUpdatedAtIso);
  if (srcTs) {
    _convictionLastLoadedAt = srcTs;
  } else if (!_convictionLastLoadedAt && CONV.length) {
    _convictionLastLoadedAt = Date.now();
  }
  const _convFiltered = (typeof cSt === 'object' && Array.isArray(cSt.filtered)) ? cSt.filtered.length : CONV.length;
  setCountMeta('cCnt', Number(_convFiltered || 0).toLocaleString() + ' tickers', 0, !!_convictionFetchPromise);
}

function _convictionDataStale(){
  if (!CONV.length || !_convictionLastLoadedAt) return true;
  return (Date.now() - _convictionLastLoadedAt) > TAB_DATA_REFRESH_MS;
}

async function ensureConvictionData(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_convictionDataStale()) return CONV;
  if (_convictionFetchPromise) return _convictionFetchPromise;
  if (CONV.length) setCountUpdating('cCnt', true);
  _convictionFetchPromise = fetch('/api/conviction')
    .then(r => {
      if (!r.ok) throw new Error('Conviction ' + r.status);
      const sourceUpdatedAt = r.headers.get('X-Gekko-Source-Updated-At') || '';
      return r.json().then(rows => ({ rows, sourceUpdatedAt }));
    })
    .then(({rows, sourceUpdatedAt}) => {
      _applyConvictionData(Array.isArray(rows) ? rows : [], sourceUpdatedAt);
      return CONV;
    })
    .catch(err => {
      if (!background) console.error('Conviction load failed', err);
      throw err;
    })
    .finally(() => {
      _convictionFetchPromise = null;
      setCountUpdating('cCnt', false);
    });
  return _convictionFetchPromise;
}

function _applyHoldingsData(rows, sourceUpdatedAtIso=''){
  HOLDINGS.length = 0;
  (rows || []).forEach((r, i) => {
    if (!r || !r.ticker) return;
    r.rank = i + 1;
    if (!r.company) r.company = BL_TICKER_INFO[r.ticker] || '';
    HOLDINGS.push(r);
    blRememberTickerCompany(r.ticker, r.company);
  });
  const srcTs = _parseSourceTs(sourceUpdatedAtIso);
  if (srcTs) {
    _holdingsLastLoadedAt = srcTs;
  }
}

function _holdingsDataStale(){
  if (!HOLDINGS.length || !_holdingsLastLoadedAt) return true;
  return (Date.now() - _holdingsLastLoadedAt) > TAB_DATA_REFRESH_MS;
}

async function ensureHoldingsData(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_holdingsDataStale()) return HOLDINGS;
  if (_holdingsFetchPromise) return _holdingsFetchPromise;
  if (HOLDINGS.length) setCountUpdating('hCnt', true);
  _holdingsFetchPromise = fetch('/api/holdings')
    .then(r => {
      if (!r.ok) throw new Error('Holdings ' + r.status);
      const sourceUpdatedAt = r.headers.get('X-Gekko-Source-Updated-At') || '';
      return r.json().then(rows => ({ rows, sourceUpdatedAt }));
    })
    .then(({rows, sourceUpdatedAt}) => {
      _applyHoldingsData(Array.isArray(rows) ? rows : [], sourceUpdatedAt);
      return HOLDINGS;
    })
    .catch(err => {
      if (!background) console.error('Holdings load failed', err);
      throw err;
    })
    .finally(() => {
      _holdingsFetchPromise = null;
      setCountUpdating('hCnt', false);
    });
  return _holdingsFetchPromise;
}

function _applyBuyMetaData(rowsByTicker){
  Object.keys(BUY_META).forEach(k => delete BUY_META[k]);
  if (rowsByTicker && typeof rowsByTicker === 'object') {
    Object.assign(BUY_META, rowsByTicker);
  }
  _buyMetaLastLoadedAt = Date.now();
}

function _buyMetaDataStale(){
  if (!Object.keys(BUY_META || {}).length || !_buyMetaLastLoadedAt) return true;
  return (Date.now() - _buyMetaLastLoadedAt) > TAB_DATA_REFRESH_MS;
}

async function ensureBuyMetaData(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_buyMetaDataStale()) return BUY_META;
  if (_buyMetaFetchPromise) return _buyMetaFetchPromise;
  _buyMetaFetchPromise = fetch('/api/buy-meta')
    .then(r => { if (!r.ok) throw new Error('Buy-meta ' + r.status); return r.json(); })
    .then(rows => {
      _applyBuyMetaData((rows && typeof rows === 'object') ? rows : {});
      return BUY_META;
    })
    .catch(err => {
      if (!background) console.error('Buy-meta load failed', err);
      throw err;
    })
    .finally(() => { _buyMetaFetchPromise = null; });
  return _buyMetaFetchPromise;
}

function _applyInsidersData(rows, sourceUpdatedAtIso=''){
  INSIDERS.length = 0;
  Object.keys(INSIDER_BUY_INDEX).forEach(k => delete INSIDER_BUY_INDEX[k]);
  (rows || []).forEach((r, i) => {
    if (!r || !r.ticker) return;
    r.rank = i + 1;
    if (!r.company) r.company = BL_TICKER_INFO[r.ticker] || '';
    INSIDERS.push(r);
    const key = normInsiderKey(r.insider);
    if (key) {
      const buyVal = Number(r.total_value);
      (INSIDER_BUY_INDEX[r.ticker] = INSIDER_BUY_INDEX[r.ticker] || []).push({
        k: key,
        d: r.trans_date || r.filing_date || '',
        v: Number.isFinite(buyVal) && buyVal > 0 ? buyVal : 0
      });
    }
    blRememberTickerCompany(r.ticker, r.company);
  });
  const srcTs = _parseSourceTs(sourceUpdatedAtIso);
  _insidersLastLoadedAt = srcTs || Date.now();
  const _insTradeCount = Array.isArray(INSIDERS) ? INSIDERS.length : 0;
  const _insTickerCount = new Set(
    INSIDERS.map(r => String(r?.ticker || '').trim()).filter(Boolean)
  ).size;
  setCountMeta(
    'iCnt',
    Number(_insTickerCount || 0).toLocaleString() + ' tickers (' + Number(_insTradeCount || 0).toLocaleString() + ' trades)',
    0,
    !!_insidersFetchPromise
  );
}

function _insidersDataStale(){
  if (!INSIDERS.length || !_insidersLastLoadedAt) return true;
  return (Date.now() - _insidersLastLoadedAt) > TAB_DATA_REFRESH_MS;
}

function _renderInsidersLoading(msg='Loading insiders...'){
  const body = document.getElementById('iBody');
  const cnt = document.getElementById('iCnt');
  if (body) body.innerHTML = `<tr><td colspan="6" class="muted" style="text-align:center;padding:16px">${msg}</td></tr>`;
  if (cnt) cnt.textContent = 'Loading...';
}

async function ensureInsidersData(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_insidersDataStale()) return INSIDERS;
  if (_insidersFetchPromise) return _insidersFetchPromise;
  if (!background && !INSIDERS.length) _renderInsidersLoading('Loading insiders...');
  if (INSIDERS.length) setCountUpdating('iCnt', true);
  _insidersFetchPromise = fetch('/api/insiders')
    .then(r => {
      if (!r.ok) throw new Error('Insiders ' + r.status);
      const sourceUpdatedAt = r.headers.get('X-Gekko-Source-Updated-At') || '';
      return r.json().then(rows => ({ rows, sourceUpdatedAt }));
    })
    .then(({rows, sourceUpdatedAt}) => {
      _applyInsidersData(Array.isArray(rows) ? rows : [], sourceUpdatedAt);
      return INSIDERS;
    })
    .catch(err => {
      if (!INSIDERS.length && !background) {
        const body = document.getElementById('iBody');
        const cnt = document.getElementById('iCnt');
        if (body) body.innerHTML = '<tr><td colspan="6" class="muted" style="text-align:center;padding:16px">Failed to load insiders.</td></tr>';
        if (cnt) cnt.textContent = '0 tickers';
      }
      throw err;
    })
    .finally(() => {
      _insidersFetchPromise = null;
      setCountUpdating('iCnt', false);
    });
  return _insidersFetchPromise;
}

function _applySignalsData(rows){
  // rows = flat array of signal objects from /api/signals
  REVERSAL_ROWS = Array.isArray(rows) ? rows : [];
  _reversalsLastLoadedAt = Date.now();
  _updateRefreshTs('reversals', new Date());
}

function _hasReversalsData(){
  if (_reversalsLastLoadedAt > 0) return true;
  return REVERSAL_ROWS.length > 0;
}

function _reversalsDataStale(){
  if (!_hasReversalsData() || !_reversalsLastLoadedAt) return true;
  return (Date.now() - _reversalsLastLoadedAt) > TAB_DATA_REFRESH_MS;
}

function _renderReversalsLoading(msg='Loading signals...'){
  const body = document.getElementById('rvBody');
  const cnt = document.getElementById('rvCnt');
  if (body) body.innerHTML = `<tr><td colspan="25" class="muted" style="text-align:center;padding:16px">${msg}</td></tr>`;
  if (cnt) cnt.textContent = 'Loading...';
}

async function ensureSignalsData(force=false){
  if (!force && !_reversalsDataStale()) { rvFilter(); return; }
  if (_reversalsFetchPromise) return _reversalsFetchPromise;
  if (!_hasReversalsData()) _renderReversalsLoading('Loading signals...');
  else setCountUpdating('rvCnt', true);
  _reversalsFetchPromise = fetch('/api/signals?days=60')
    .then(r => { if (!r.ok) throw new Error('Signals ' + r.status); return r.json(); })
    .then(rows => {
      _applySignalsData(rows);
      rvFilter();
    })
    .catch(() => {
      const body = document.getElementById('rvBody');
      const cnt = document.getElementById('rvCnt');
      if (body) body.innerHTML = '<tr><td colspan="25" class="muted" style="text-align:center;padding:16px">Failed to load signals.</td></tr>';
      if (cnt) cnt.textContent = '0 signals';
    })
    .finally(() => { _reversalsFetchPromise = null; setCountUpdating('rvCnt', false); });
  return _reversalsFetchPromise;
}

// Keep old name as alias so any remaining callers don't break
function ensureReversalsData(force=false){ return ensureSignalsData(force); }

function _applySp500Data(rows, sourceUpdatedAtIso=''){
  SP500_DATA.length = 0;
  (rows || []).forEach(r => {
    if (!r || !r.ticker) return;
    SP500_DATA.push(r);
    blRememberTickerCompany(r.ticker, r.name);
  });
  const srcTs = _parseSourceTs(sourceUpdatedAtIso);
  _sp500LastLoadedAt = srcTs || Date.now();
  _updateRefreshTs('heatmap-sp500', srcTs ? new Date(srcTs) : new Date());
}

function _sp500DataStale(){
  if (!_sp500LastCheckedAt) return true;
  return (Date.now() - _sp500LastCheckedAt) > TAB_DATA_REFRESH_MS;
}

function _renderHeatmapLoading(msg='Loading heatmap...'){
  const grid = document.getElementById('hmGrid');
  if (!grid) return;
  grid.classList.toggle('hm-sp500', _hmView === 'sp500');
  grid.innerHTML = `<div class="hm-sp-empty">${msg}</div>`;
}

async function ensureSp500Data(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_sp500DataStale()) return SP500_DATA;
  if (_sp500FetchPromise) return _sp500FetchPromise;
  if (!background && !SP500_DATA.length) _renderHeatmapLoading('Loading S&P 500 heatmap...');
  _sp500FetchPromise = fetch('/api/sp500')
    .then(r => {
      if (!r.ok) throw new Error('S&P 500 ' + r.status);
      const sourceUpdatedAt = r.headers.get('X-Gekko-Source-Updated-At') || '';
      const refreshing = String(r.headers.get('X-Gekko-Refreshing') || '0') === '1';
      return r.json().then(rows => ({ rows, sourceUpdatedAt, refreshing }));
    })
    .then(({rows, sourceUpdatedAt, refreshing}) => {
      _applySp500Data(Array.isArray(rows) ? rows : [], sourceUpdatedAt);
      if (refreshing) {
        _scheduleAutoRefresh('sp500', () => {
          ensureSp500Data(false, {background:true}).then(() => {
            if (document.getElementById('tab-heatmap')?.classList.contains('active') && _hmView==='sp500') renderHeatmap();
          }).catch(() => {});
        }, 12000);
      }
      return SP500_DATA;
    })
    .catch(err => {
      if (!SP500_DATA.length && !background) _renderHeatmapLoading('Failed to load S&P 500 heatmap.');
      throw err;
    })
    .finally(() => {
      _sp500FetchPromise = null;
      _sp500LastCheckedAt = Date.now();
    });
  return _sp500FetchPromise;
}

function _applyBubbleSizeData(rowsByTicker){
  Object.keys(BUBBLE_SIZE_DATA).forEach(k => delete BUBBLE_SIZE_DATA[k]);
  if (rowsByTicker && typeof rowsByTicker === 'object') Object.assign(BUBBLE_SIZE_DATA, rowsByTicker);
  _bubbleSizeLastLoadedAt = Date.now();
}

function _bubbleSizeDataStale(){
  if (!Object.keys(BUBBLE_SIZE_DATA || {}).length || !_bubbleSizeLastLoadedAt) return true;
  return (Date.now() - _bubbleSizeLastLoadedAt) > TAB_DATA_REFRESH_MS;
}

async function ensureBubbleSizeData(force=false, opts={}){
  const background = !!(opts && opts.background);
  if (!force && !_bubbleSizeDataStale()) return BUBBLE_SIZE_DATA;
  if (_bubbleSizeFetchPromise) return _bubbleSizeFetchPromise;
  _bubbleSizeFetchPromise = fetch('/api/bubble-size')
    .then(r => { if (!r.ok) throw new Error('Bubble size ' + r.status); return r.json(); })
    .then(rows => {
      _applyBubbleSizeData((rows && typeof rows === 'object') ? rows : {});
      return BUBBLE_SIZE_DATA;
    })
    .catch(err => {
      if (!background) console.error('Bubble-size load failed', err);
      throw err;
    })
    .finally(() => { _bubbleSizeFetchPromise = null; });
  return _bubbleSizeFetchPromise;
}

function _profileMetaStale(sym){
  const ts = Number(_blProfileMetaFetchedAt[sym] || 0);
  if (!ts) return true;
  return (Date.now() - ts) > PROFILE_META_REFRESH_MS;
}

async function blEnsureProfileMeta(ticker, force=false){
  const sym = String(ticker || '').trim().toUpperCase();
  if (!sym) return {};
  if (!force && BL_PROFILE_META[sym] && !_profileMetaStale(sym)) return BL_PROFILE_META[sym];
  if (_blProfileMetaFetching[sym]) return _blProfileMetaFetching[sym];
  _blProfileMetaFetching[sym] = fetch('/api/ticker-meta/' + encodeURIComponent(sym))
    .then(r => { if (!r.ok) throw new Error('Ticker meta ' + r.status); return r.json(); })
    .then(row => {
      const out = {
        ticker: sym,
        name: String(row?.name || ''),
        sector: String(row?.sector || ''),
        industry: String(row?.industry || ''),
      };
      BL_PROFILE_META[sym] = out;
      _blProfileMetaFetchedAt[sym] = Date.now();
      return out;
    })
    .catch(_err => {
      _blProfileMetaFetchedAt[sym] = Date.now();
      return BL_PROFILE_META[sym] || { ticker:sym, name:'', sector:'', industry:'' };
    })
    .finally(() => { delete _blProfileMetaFetching[sym]; });
  return _blProfileMetaFetching[sym];
}

function blNormalizeCompanyName(name){
  let s=String(name||'');
  // Strip XML CDATA wrappers e.g. <![CDATA[CROWDSTRIKE HOLDINGS INC]]>
  s=s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1');
  return s.replace(/\s+/g,' ').trim();
}
function blRememberTickerCompany(ticker, company){
  const sym=String(ticker||'').trim().toUpperCase();
  const clean=blNormalizeCompanyName(company);
  if(!sym || !clean) return;
  BL_TICKER_INFO[sym]=clean;
}
Object.entries(BL_SEARCH_UNIVERSE).forEach(([sym,name])=>{ if(sym&&name) BL_TICKER_INFO[sym.toUpperCase()]=blNormalizeCompanyName(name); });
[CONV,HOLDINGS,INSIDERS,ZR_DATA].forEach(rows=>{
  (rows||[]).forEach(r=>blRememberTickerCompany(r?.ticker, r?.company));
});

function fmtDateShort(v){
  if(v==null||v==='') return '';
  if(v instanceof Date && Number.isFinite(v.getTime())) return `${v.getMonth()+1}-${v.getDate()}-${v.getFullYear()}`;
  const s=String(v).trim();
  if(!s) return '';
  const iso=s.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
  if(iso) return `${Number(iso[2])}-${Number(iso[3])}-${iso[1]}`;
  const slash=s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if(slash) return `${Number(slash[1])}-${Number(slash[2])}-${slash[3]}`;
  const dt=new Date(s);
  if(Number.isFinite(dt.getTime())) return `${dt.getMonth()+1}-${dt.getDate()}-${dt.getFullYear()}`;
  return s;
}
function fmtDateTimeShort(v){
  const dt=(v instanceof Date) ? v : new Date(v);
  if(!Number.isFinite(dt.getTime())) return String(v??'');
  return `${fmtDateShort(dt)} ${dt.toLocaleTimeString()}`;
}

const _buildUpdatedAt = fmtDateTimeShort(new Date());
const _updatedAtEl = document.getElementById('updatedAt');
if(_updatedAtEl) _updatedAtEl.textContent = _buildUpdatedAt;

function showJsError(msg, err){
  const el=document.getElementById('jsErrorBanner');
  if(!el) return;
  const extra=err && (err.stack||err.message||String(err)) ? '\n'+(err.stack||err.message||String(err)) : '';
  el.textContent='JS error: '+msg+extra;
  el.style.display='block';
}
window.addEventListener('error', ev=>{ showJsError(ev.message||'Unknown error', ev.error||ev); });
window.addEventListener('unhandledrejection', ev=>{ showJsError('Unhandled promise rejection', ev.reason||ev); });

const UI = {green:'#119600',greenBright:'#33AA00',greenSoft:'#77AA00',red:'#AA0000',redBright:'#CC3300',orange:'#DD6600',amber:'#CC9900',border:'#1a1a1a',border2:'#2A2A2A',text:'#EAEAEA',muted:'#777777',surface:'#0A0A0A',hollowCandle:'#CCCCCC'};
const GIC = {'dark-green':UI.green,'green':UI.greenSoft,'yellow':UI.amber,'orange':UI.orange,'red':UI.redBright,'none':UI.muted};
const BUBBLE_GIC = GIC;
let CANDLE_DATA={};
let GI_HISTORY=null;
const INSIDER_BUY_INDEX={};
const INSIDER_COLOR_MAP={};
const MANAGER_COLOR_MAP={};
let _blOhlcvServerMtime=0;
function getCandleData(){
  return CANDLE_DATA || {};
}
// On startup and periodically: check if server has newer ohlcv data.
// If yes, clear CANDLE_DATA so tickers are re-fetched with fresh bars.
async function blCheckOhlcvVersion(){
  // Only auto-update when the timer is running; when Off, user refreshes manually
  if(_blAutoRefreshSecs===0) return;
  try{
    const r=await fetch('/api/ohlcv-version');
    if(!r.ok) return;
    const v=await r.json();
    const mtime=v.mtime||0;
    if(_blOhlcvServerMtime&&mtime>_blOhlcvServerMtime){
      // Server has newer bars — only evict and reload the active chart ticker.
      // Watchlist tickers will pick up new bars next time they're explicitly refreshed.
      const cur=blCurrentTicker();
      if(cur){
        delete CANDLE_DATA[cur];
        delete _blOHLCVFetching[cur];
        blEnsureTickerOHLCV(cur).then(()=>renderBuyLevels());
      }
    }
    _blOhlcvServerMtime=mtime;
  }catch(_e){}
}
const _blOHLCVFetching={};
let _blRenderToken=0;
// Per-ticker chart overlay fetch (GI history, zone returns, earnings,
// reversals, fair value).
const _blChartDataFetching={};
const _blChartDataLastCheckedAt=Object.create(null);
const BL_CHART_DATA_REFRESH_MS=5*60*1000;
function _blChartDataStale(sym){
  const ts=Number(_blChartDataLastCheckedAt[sym]||0);
  if(!ts) return true;
  return (Date.now()-ts)>BL_CHART_DATA_REFRESH_MS;
}
function _blChartDataHasCoreLoaded(sym){
  const giLoaded=!!(GI_HISTORY&&Object.prototype.hasOwnProperty.call(GI_HISTORY, sym));
  const zrLoaded=!!(ZR_ALL&&Object.prototype.hasOwnProperty.call(ZR_ALL, sym));
  return giLoaded&&zrLoaded;
}
function _blChartDataHasOverlaysLoaded(sym){
  const rvLoaded=Object.prototype.hasOwnProperty.call(REVERSALS_DATA||{}, sym);
  return rvLoaded;
}
async function blEnsureTickerChartData(sym, force=false){
  if(!sym) return;
  const key=String(sym||'').trim().toUpperCase();
  if(!key) return;
  if(!force&&_blChartDataHasCoreLoaded(key)&&_blChartDataHasOverlaysLoaded(key)&&!_blChartDataStale(key)) return;
  if(_blChartDataFetching[key]){ await _blChartDataFetching[key]; return; }

  // Priority order:
  // 1) OHLCV is loaded by blEnsureTickerOHLCV() (blocking for chart render).
  // 2) GI history is fetched first.
  // 3) Secondary overlays (zone/earnings/reversals/fair-value) follow.
  const giTask=fetch('/api/gi-history/'+encodeURIComponent(key))
    .then(async r=>{
      const refreshing=String(r.headers.get('X-Gekko-Refreshing')||'0')==='1';
      if(!r.ok){
        if(refreshing){
          _scheduleAutoRefresh('giHist-'+key,()=>{
            blEnsureTickerChartData(key,true).catch(()=>{});
          },12000);
        }
        return;
      }
      const giHist=await r.json();
      if(Array.isArray(giHist)){
        if(!GI_HISTORY) GI_HISTORY={};
        GI_HISTORY[key]=_normalizeGiRows(giHist);
        gispInvalidateTickerCaches(key);
        if(blCurrentTicker()===key){
          // GI data arrived after chart rendered — re-render buy levels so
          // the GI panel is drawn with proper layout (same path as manual refresh).
          renderGISignalPanel(key);
          // Only re-run the full render if GI section is missing/blank
          const giSec=document.getElementById('blGISection');
          const giMissing=!giHistChart||(giSec&&giSec.style.display==='none'&&_blGIPos==='lower');
          if(giMissing){
            renderBuyLevels().catch(()=>{});
          }
        }
      }
      if(refreshing){
        _scheduleAutoRefresh('giHist-'+key,()=>{
          blEnsureTickerChartData(key,true).catch(()=>{});
        },12000);
      }
    })
    .catch(()=>{});

  const loadSecondary=()=>Promise.allSettled([
    fetch('/api/zone-returns/'+encodeURIComponent(key))
      .then(r=>r.ok?r.json():{})
      .then(zoneReturns=>{
        if(zoneReturns&&typeof zoneReturns==='object'){
          ZR_ALL[key]=zoneReturns;
          if(blCurrentTicker()===key){
            renderGISignalPanel(key);
          }
        }
      })
      .catch(()=>{}),
    fetch('/api/signals/'+encodeURIComponent(key))
      .then(r=>r.ok?r.json():null)
      .then(reversals=>{
        if(Array.isArray(reversals)){
          REVERSALS_DATA[key]=reversals;
          if(blCurrentTicker()===key){
            if(_gispZone) gispCalc();
            renderBuyLevels().catch(()=>{});
          }
        }
      })
      .catch(()=>{}),
  ]);

  _blChartDataFetching[key]=(async()=>{
    await giTask;
    await loadSecondary();
  })().finally(()=>{
    _blChartDataLastCheckedAt[key]=Date.now();
    delete _blChartDataFetching[key];
  });
  await _blChartDataFetching[key];
}

async function blEnsureTickerOHLCV(ticker, force=false){
  const key=String(ticker||'').trim().toUpperCase();
  if(!key) return;
  // Only pull full chart data (GI history, zone returns, reversals) for the active ticker.
  // Background watchlist tickers only need OHLCV bars for price display.
  if(key===blCurrentTicker()) blEnsureTickerChartData(key, !!force).catch(()=>{});
  if(!force && CANDLE_DATA[key]!=null){
    return;
  }
  if(_blOHLCVFetching[key]){ await _blOHLCVFetching[key]; return; }
  _blOHLCVFetching[key]=fetch('/api/ohlcv/'+encodeURIComponent(key))
    .then(async r=>{
      const refreshing=String(r.headers.get('X-Gekko-Refreshing')||'0')==='1';
      const rows=r.ok?await r.json():[];
      return {rows,refreshing};
    })
    .then(({rows,refreshing})=>{
      CANDLE_DATA[key]=(rows||[]).map(r=>{
        if(Array.isArray(r)) return {t:r[0],o:r[1],h:r[2],l:r[3],c:r[4],v:r.length>5?r[5]:null};
        return {t:r?.t??null,o:r?.o??null,h:r?.h??null,l:r?.l??null,c:r?.c??null,v:r?.v??null};
      }).filter(d=>d.t!=null);
      gispInvalidateTickerCaches(key);
      if(refreshing){
        _scheduleAutoRefresh('ohlcv-'+key,()=>{
          blEnsureTickerOHLCV(key,true).then(()=>{
            if(blCurrentTicker()===key) renderBuyLevels();
            renderWatchlist();
          }).catch(()=>{});
        },12000);
      }
    })
    .catch(()=>{
      // Avoid pinning a symbol to empty data on transient request failures.
      if(CANDLE_DATA[key]==null) CANDLE_DATA[key]=[];
    })
    .finally(()=>{
      delete _blOHLCVFetching[key];
    });
  await _blOHLCVFetching[key];
}

function getGIHistory(){
  return GI_HISTORY || {};
}

function _normalizeGiRows(rows){
  if(!Array.isArray(rows)) return [];
  return rows
    .map(d=>{
      if(Array.isArray(d)) return {t:String(d[0]||''), v:Number(d[1])};
      if(d && typeof d==='object') return {t:String(d.t||d.date||''), v:Number(d.v??d.gi_score)};
      return null;
    })
    .filter(d=>d && d.t && Number.isFinite(d.v));
}

let WATCHLISTS = [];
let ACTIVE_WATCHLIST = 0;
const WATCHLIST_KEY = 'gekko_watchlists_v1';
const WATCHLIST_UI_KEY = 'gekko_watchlist_ui_v2';
const BUYLEVELS_UI_KEY = 'gekko_buylevels_ui_v1';
const TAB_UI_KEY = 'gekko_tab_ui_v1';
const BL_FIRST_RUN_DEFAULT_TICKER = 'AAPL';
const BL_CHART_TYPE_LABELS = {hollow:'Hollow', candle:'Candle', line:'Line', ohlc:'OHLC', hlc:'HLC', volcndle:'Vol Candle'};

// -- Server-sync: persist prefs to SQLite via /api/prefs -----------------------
const _syncTimers={};
function _syncPrefsToServer(key, data, opts){
  const cfg=(opts&&typeof opts==='object')?opts:{};
  const immediate=!!cfg.immediate;
  const keepalive=!!cfg.keepalive;
  const send=()=>{
    try{
      fetch('/api/prefs',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        keepalive,
        body:JSON.stringify({[key]:data})
      }).catch(()=>{});
    }catch(_e){}
  };
  clearTimeout(_syncTimers[key]);
  if(immediate){
    send();
    return;
  }
  _syncTimers[key]=setTimeout(send,400);
}
// Load all prefs from server file once at startup; returns a Promise<object>
let _serverPrefsCache=null;
let _serverPrefsFetching=null;
function _fetchServerPrefs(){
  if(_serverPrefsCache!==null) return Promise.resolve(_serverPrefsCache);
  if(_serverPrefsFetching) return _serverPrefsFetching;
  _serverPrefsFetching=fetch('/api/prefs')
    .then(r=>r.ok?r.json():{})
    .then(d=>{_serverPrefsCache=(d&&typeof d==='object')?d:{};return _serverPrefsCache;})
    .catch(()=>{_serverPrefsCache={};return _serverPrefsCache;});
  return _serverPrefsFetching;
}
const BL_CHART_COLOR_LABELS = {open:'By Open', change:'By Change', neutral:'Neutral'};
let _blSizerAccountValue=100000;
let _blSizerRiskCash=500;
let _blSizerRiskPct=0.5;
let _blSizerMaxRiskPct=100;
let _blSizerRiskMode='fixed';
let _blSizerManualStop=0;
let _blSizerAutoFilledKey='';
let _blSizerAtrMult=null;
let _blSizerManualTarget=0;
let _blSizerRMult=null;
let _blSizerAutoFilledTargetKey='';
let _blSizerLastAutoStop=NaN;   // last resolved stop price (auto mode) — seed for steppers
let _blSizerLastAutoTarget=NaN; // last resolved target price (auto mode) — seed for steppers
let _blSortBy='recent';
let _blLookbackDays=30;
const WATCHLIST_SORT_OPTIONS = ['manual','alpha','alpha-desc','price','price-desc','pct','pct-desc'];
const WATCHLIST_SETTINGS_VALUE = '__settings__';
const WATCHLIST_BACKUP_DB = 'gekko_watchlist_backup_db_v1';
const WATCHLIST_BACKUP_STORE = 'files';
const WATCHLIST_BACKUP_HANDLE_KEY = 'watchlists';
const WATCHLIST_BACKUP_FILENAME = 'gekko_watchlists_backup.json';
let WATCHLIST_DRAG_ID = '';
let WATCHLIST_BACKUP_HANDLE = null;
let WATCHLIST_BACKUP_SAVE_TIMER = 0;

function syncWatchlistPanelButton(){
  const btn=document.getElementById('watchlistToggleBtn');
  if(btn) btn.classList.toggle('active', document.body.classList.contains('watchlist-open'));
}
function loadWatchlistPrefs(){
  try {
    const raw = localStorage.getItem(WATCHLIST_UI_KEY);
    if (!raw) return;
    const cfg = JSON.parse(raw) || {};
    if (Number.isFinite(cfg.active)) ACTIVE_WATCHLIST = Math.max(0, Math.floor(cfg.active));
  } catch (e) {}
}
function saveWatchlistPrefs(){
  try {
    localStorage.setItem(WATCHLIST_UI_KEY, JSON.stringify({
      active: ACTIVE_WATCHLIST
    }));
  } catch (e) {}
}
function blApplySavedControlState(){
  const setSelect=(id,val)=>{
    const el=document.getElementById(id);
    if(!el) return;
    const next=String(val ?? '');
    if(Array.from(el.options||[]).some(opt=>String(opt.value)===next)) el.value=next;
  };
  setSelect('blChartPeriod', _blPeriod);
  setSelect('blSortBy', _blSortBy);
  setSelect('blLookback', _blLookbackDays);
  setSelect('blAutoRefreshSelect', _blAutoRefreshSecs);
  blSyncIndicatorChecks();
  blSyncChartTypeUI();
  gispSyncPositionSizerInputs();
  // Keep iWinDays in sync whenever blLookback is programmatically updated
  iApplyLookbackFromMovedControl();
}
function blPullSavedControlState(){
  const period=parseInt(document.getElementById('blChartPeriod')?.value);
  const lookback=parseInt(document.getElementById('blLookback')?.value);
  const sortBy=String(document.getElementById('blSortBy')?.value||'').trim().toLowerCase();
  if(Number.isFinite(period)) _blPeriod=period;
  if(Number.isFinite(lookback)) _blLookbackDays=lookback;
  if(['amount','recent','count','alpha'].includes(sortBy)) _blSortBy=sortBy;
}
function _applyBuyLevelsCfg(cfg){
  try {
    if(!cfg||typeof cfg!=='object') { blApplySavedControlState(); return; }
    const ticker = String(cfg.ticker || '').trim().toUpperCase();
    const acct = Number(cfg.account_value);
    const riskCash = Number(cfg.risk_cash);
    const riskPct = Number(cfg.risk_pct);
    const maxRiskPct = Number(cfg.max_risk_pct ?? cfg.cap_pct);
    const chartPeriod = Number(cfg.chart_period);
    const lookbackDays = Number(cfg.lookback_days);
    const chartType = String(cfg.chart_type || '').trim().toLowerCase();
    const chartColorMode = String(cfg.chart_color_mode || '').trim().toLowerCase();
    const sortBy = String(cfg.sort_by || '').trim().toLowerCase();
    _blSizerAccountValue = Number.isFinite(acct) && acct >= 0 ? acct : 100000;
    _blSizerRiskCash = Number.isFinite(riskCash) && riskCash >= 0 ? riskCash : _blSizerRiskCash;
    _blSizerRiskPct = Number.isFinite(riskPct) && riskPct >= 0 ? riskPct : _blSizerRiskPct;
    _blSizerMaxRiskPct = Number.isFinite(maxRiskPct) && maxRiskPct >= 0 ? maxRiskPct : 100;
    if (typeof cfg.risk_mode === 'string' && ['fixed','pct'].includes(cfg.risk_mode)) _blSizerRiskMode = cfg.risk_mode;
    if (Number.isFinite(Number(cfg.manual_stop)) && Number(cfg.manual_stop)>=0) _blSizerManualStop=Number(cfg.manual_stop);
    const atrMult=Number(cfg.atr_mult); if([1.0,1.5,2.0,2.5,3.0].includes(atrMult)) _blSizerAtrMult=atrMult; else if(cfg.atr_mult===null||cfg.atr_mult===undefined) _blSizerAtrMult=null;
    // Restore auto-filled keys from saved ticker so refresh keeps the user's stop/target
    if(typeof cfg.sizer_ticker==='string'&&cfg.sizer_ticker){
      _blSizerAutoFilledKey=cfg.sizer_ticker;
      _blSizerAutoFilledTargetKey=cfg.sizer_ticker;
    }
    if(Number.isFinite(Number(cfg.manual_target))&&Number(cfg.manual_target)>=0) _blSizerManualTarget=Number(cfg.manual_target);
    const rMult=Number(cfg.r_mult); if([1.5,2.0,2.5,3.0].includes(rMult)) _blSizerRMult=rMult; else if(cfg.r_mult===null||cfg.r_mult===undefined) _blSizerRMult=null;
    _blPeriod = Number.isFinite(chartPeriod) ? chartPeriod : _blPeriod;
    _blLookbackDays = Number.isFinite(lookbackDays) ? lookbackDays : _blLookbackDays;
    _blChartType = Object.prototype.hasOwnProperty.call(BL_CHART_TYPE_LABELS, chartType) ? chartType : _blChartType;
    if (Object.prototype.hasOwnProperty.call(BL_CHART_COLOR_LABELS, chartColorMode)) _blChartColorMode = chartColorMode;
    _blSortBy = ['amount','recent','count','alpha'].includes(sortBy) ? sortBy : _blSortBy;
    _blGIPos = ['lower','overlay','off'].includes(String(cfg.gi_pos || '').toLowerCase()) ? String(cfg.gi_pos).toLowerCase() : _blGIPos;
    if (typeof cfg.show_earnings === 'boolean') _blShowEarnings = cfg.show_earnings;
    if (typeof cfg.show_reversals === 'boolean') _blShowReversals = cfg.show_reversals;
    if (typeof cfg.show_insiders === 'boolean') _blShowInsiders = cfg.show_insiders;
    if (typeof cfg.show_vwap === 'boolean') _blShowVwap = cfg.show_vwap;
    if (typeof cfg.show_value_chart === 'boolean') _blShowValueChart = cfg.show_value_chart;
    if (typeof cfg.show_ma50 === 'boolean') _blShowMA50 = cfg.show_ma50;
    if (typeof cfg.show_ma200 === 'boolean') _blShowMA200 = cfg.show_ma200;
    if (typeof cfg.show_profile === 'boolean') _blShowProfile = cfg.show_profile;
    if (typeof cfg.show_vsa === 'boolean') _blShowVSA = cfg.show_vsa;
    if (typeof cfg.show_data_tooltip === 'boolean') _blShowDataTooltip = cfg.show_data_tooltip;
    if (typeof cfg.show_crosshair === 'boolean') _blShowCrosshair = cfg.show_crosshair;
    if (typeof cfg.show_target_lines === 'boolean') _blShowTargetLines = cfg.show_target_lines;
    if (typeof cfg.show_stop_line === 'boolean') _blShowStopLine = cfg.show_stop_line;
    if (typeof cfg.show_lookback_bar === 'boolean') _blShowLookbackBar = cfg.show_lookback_bar;
    if (Number.isFinite(Number(cfg.margin_top_pct))&&Number(cfg.margin_top_pct)>=0) _blMarginTopPct=Math.round(Number(cfg.margin_top_pct));
    if (Number.isFinite(Number(cfg.margin_bot_pct))&&Number(cfg.margin_bot_pct)>=0) _blMarginBotPct=Math.round(Number(cfg.margin_bot_pct));
    if (Number.isFinite(Number(cfg.right_bars))&&Number(cfg.right_bars)>=0) _blRightBars=Math.round(Number(cfg.right_bars));
    if (Number.isFinite(Number(cfg.volume_scale))&&Number(cfg.volume_scale)>0) _blVolumeScale=clampNum(Number(cfg.volume_scale),0.25,2.5);
    if (typeof cfg.vc_consistent_gaps === 'boolean') _blVcConsistentGaps=cfg.vc_consistent_gaps;
    if (Number.isFinite(Number(cfg.vc_width_scale))&&Number(cfg.vc_width_scale)>0) _blVcWidthScale=clampNum(Number(cfg.vc_width_scale),0.25,3.0);
    if (typeof cfg.vc_filled === 'boolean') _blVcFilled=cfg.vc_filled;
    if (typeof cfg.show_gi_returns === 'boolean') _blShowGIReturns=cfg.show_gi_returns;
    if (typeof cfg.show_gi_backtest === 'boolean') _blShowGIBacktest=cfg.show_gi_backtest;
    if (typeof cfg.show_gi_sizer === 'boolean') _blShowGISizer=cfg.show_gi_sizer;
    if (typeof cfg.neutral_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.neutral_color)) _blNeutralColor=cfg.neutral_color;
    if (typeof cfg.up_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.up_color)) _blUpColor=cfg.up_color;
    if (typeof cfg.down_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.down_color)) _blDownColor=cfg.down_color;
    if (typeof cfg.vol_up_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.vol_up_color)) _blVolUpColor=cfg.vol_up_color;
    if (typeof cfg.vol_down_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.vol_down_color)) _blVolDownColor=cfg.vol_down_color;
    if (typeof cfg.insider_dot_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.insider_dot_color)) _blInsiderDotColor=cfg.insider_dot_color;
    if (typeof cfg.vc_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.vc_color)) _blVCColor=cfg.vc_color;
    if (typeof cfg.vwap_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.vwap_color)) _blVwapColor=cfg.vwap_color;
    if (typeof cfg.ma50_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.ma50_color)) _blMA50Color=cfg.ma50_color;
    if (typeof cfg.ma200_color==='string'&&/^#[0-9a-fA-F]{6}$/.test(cfg.ma200_color)) _blMA200Color=cfg.ma200_color;
    if (!Object.prototype.hasOwnProperty.call(BL_CHART_COLOR_LABELS, chartColorMode) && typeof cfg.show_prev_close_colors === 'boolean') {
      _blChartColorMode = cfg.show_prev_close_colors ? 'change' : 'open';
    }
    blApplySavedControlState();
    _blSyncGIPanelVis();
    // Restore auto-refresh timer setting (don't fire immediately on load)
    const savedRefreshSecs = parseInt(cfg.auto_refresh_secs) || 0;
    if (savedRefreshSecs > 0) blSetAutoRefresh(savedRefreshSecs, { save: false, fireNow: false });
    if (ticker) blOpenTicker(ticker);
  } catch (e) {}
}
function loadBuyLevelsPrefs(){
  // Try server file first (source of truth), fall back to localStorage
  _fetchServerPrefs().then(serverPrefs=>{
    const serverCfg = serverPrefs[BUYLEVELS_UI_KEY];
    if(serverCfg&&typeof serverCfg==='object'){
      // Write back to localStorage so it's available instantly on next load
      try{ localStorage.setItem(BUYLEVELS_UI_KEY, JSON.stringify(serverCfg)); }catch(_e){}
      _applyBuyLevelsCfg(serverCfg);
      return;
    }
    // Fall back to localStorage
    try {
      const raw = localStorage.getItem(BUYLEVELS_UI_KEY);
      if (raw) {
        _applyBuyLevelsCfg(JSON.parse(raw));
      } else {
        _applyBuyLevelsCfg({
          ticker: BL_FIRST_RUN_DEFAULT_TICKER,
          chart_type: 'hollow',
          chart_color_mode: 'neutral',
          show_value_chart: false,
          margin_top_pct: 3,
          margin_bot_pct: 30,
          right_bars: 0
        });
      }
    } catch(e) { blApplySavedControlState(); }
  });
}
function saveBuyLevelsPrefs(){
  try {
    blPullSavedControlState();
    const ticker = blCurrentTicker();
    const prefs = {
      ticker: ticker || '',
      active_tab: _loadSavedTab() || '',
      account_value: _blSizerAccountValue,
      risk_cash: _blSizerRiskCash,
      risk_pct: _blSizerRiskPct,
      max_risk_pct: _blSizerMaxRiskPct,
      chart_period: _blPeriod,
      chart_type: _blChartType,
      chart_color_mode: _blChartColorMode,
      sort_by: _blSortBy,
      lookback_days: _blLookbackDays,
      gi_pos: _blGIPos,
      show_earnings: !!_blShowEarnings,
      show_reversals: !!_blShowReversals,
      show_insiders: !!_blShowInsiders,
      show_vwap: !!_blShowVwap,
      show_value_chart: !!_blShowValueChart,
      show_ma50: !!_blShowMA50,
      show_ma200: !!_blShowMA200,
      show_profile: !!_blShowProfile,
      show_vsa: !!_blShowVSA,
      show_data_tooltip: !!_blShowDataTooltip,
      show_crosshair: !!_blShowCrosshair,
      show_target_lines: !!_blShowTargetLines,
      show_stop_line: !!_blShowStopLine,
      show_lookback_bar: !!_blShowLookbackBar,
      margin_top_pct: _blMarginTopPct,
      margin_bot_pct: _blMarginBotPct,
      right_bars: _blRightBars,
      volume_scale: _blVolumeScale,
      neutral_color: _blNeutralColor,
      up_color: _blUpColor,
      down_color: _blDownColor,
      vol_up_color: _blVolUpColor,
      vol_down_color: _blVolDownColor,
      insider_dot_color: _blInsiderDotColor,
      vc_color: _blVCColor,
      vwap_color: _blVwapColor,
      ma50_color: _blMA50Color,
      ma200_color: _blMA200Color,
      risk_mode: _blSizerRiskMode,
      manual_stop: _blSizerManualStop,
      atr_mult: _blSizerAtrMult,
      sizer_ticker: blCurrentTicker()||'',
      manual_target: _blSizerManualTarget,
      r_mult: _blSizerRMult,
      auto_refresh_secs: _blAutoRefreshSecs,
      vc_consistent_gaps: !!_blVcConsistentGaps,
      vc_width_scale: _blVcWidthScale,
      vc_filled: !!_blVcFilled,
      show_gi_returns: !!_blShowGIReturns,
      show_gi_backtest: !!_blShowGIBacktest,
      show_gi_sizer: !!_blShowGISizer
    };
    localStorage.setItem(BUYLEVELS_UI_KEY, JSON.stringify(prefs));
    _syncPrefsToServer(BUYLEVELS_UI_KEY, prefs);
  } catch (e) {}
}
function watchlistSetBackupStatus(msg, tone=''){
  const el = document.getElementById('watchlistBackupStatus');
  if (!el) return;
  el.textContent = msg;
  el.className = 'watchlist-backup-status' + (tone ? ' ' + tone : '');
}
function watchlistBackupPayload(){
  return {
    version: 1,
    exported_at: new Date().toISOString(),
    active: ACTIVE_WATCHLIST,
    watchlists: WATCHLISTS.map((w,i)=>watchlistNormalizeList(w, i))
  };
}
function watchlistBackupJson(){
  return JSON.stringify(watchlistBackupPayload(), null, 2);
}
function watchlistDownloadBackupFile(){
  const blob = new Blob([watchlistBackupJson()], { type:'application/json' });
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = WATCHLIST_BACKUP_FILENAME;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(href);
    try { a.remove(); } catch (_e) {}
  }, 0);
  watchlistSetBackupStatus('Backup download started', 'ok');
}
async function watchlistOpenBackupDb(){
  if (!window.indexedDB) return null;
  try {
    return await new Promise((resolve, reject) => {
      const req = indexedDB.open(WATCHLIST_BACKUP_DB, 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(WATCHLIST_BACKUP_STORE)) db.createObjectStore(WATCHLIST_BACKUP_STORE);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  } catch (_e) {
    return null;
  }
}
async function watchlistStoreBackupHandle(handle){
  const db = await watchlistOpenBackupDb();
  if (!db) return false;
  return await new Promise(resolve => {
    try {
      const tx = db.transaction(WATCHLIST_BACKUP_STORE, 'readwrite');
      tx.objectStore(WATCHLIST_BACKUP_STORE).put(handle, WATCHLIST_BACKUP_HANDLE_KEY);
      tx.oncomplete = () => { try { db.close(); } catch (_e) {} resolve(true); };
      tx.onerror = tx.onabort = () => { try { db.close(); } catch (_e) {} resolve(false); };
    } catch (_e) {
      try { db.close(); } catch (_e2) {}
      resolve(false);
    }
  });
}
async function watchlistLoadBackupHandle(){
  const db = await watchlistOpenBackupDb();
  if (!db) return null;
  return await new Promise(resolve => {
    try {
      const tx = db.transaction(WATCHLIST_BACKUP_STORE, 'readonly');
      const req = tx.objectStore(WATCHLIST_BACKUP_STORE).get(WATCHLIST_BACKUP_HANDLE_KEY);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => resolve(null);
      tx.oncomplete = () => { try { db.close(); } catch (_e) {} };
      tx.onabort = () => { try { db.close(); } catch (_e) {} resolve(null); };
    } catch (_e) {
      try { db.close(); } catch (_e2) {}
      resolve(null);
    }
  });
}
async function watchlistClearBackupHandle(){
  WATCHLIST_BACKUP_HANDLE = null;
  const db = await watchlistOpenBackupDb();
  if (!db) return false;
  return await new Promise(resolve => {
    try {
      const tx = db.transaction(WATCHLIST_BACKUP_STORE, 'readwrite');
      tx.objectStore(WATCHLIST_BACKUP_STORE).delete(WATCHLIST_BACKUP_HANDLE_KEY);
      tx.oncomplete = () => { try { db.close(); } catch (_e) {} resolve(true); };
      tx.onerror = tx.onabort = () => { try { db.close(); } catch (_e) {} resolve(false); };
    } catch (_e) {
      try { db.close(); } catch (_e2) {}
      resolve(false);
    }
  });
}
async function watchlistQueryBackupPermission(handle){
  if (!handle?.queryPermission) return 'granted';
  try {
    return await handle.queryPermission({ mode:'readwrite' });
  } catch (_e) {
    return 'prompt';
  }
}
async function watchlistWriteBackupHandle(handle){
  const writable = await handle.createWritable();
  await writable.write(watchlistBackupJson());
  await writable.close();
}
async function watchlistAutoBackup(){
  const handle = WATCHLIST_BACKUP_HANDLE;
  if (!handle) return false;
  const perm = await watchlistQueryBackupPermission(handle);
  if (perm !== 'granted') {
    watchlistSetBackupStatus('Backup file linked; click Backup to reconnect', 'warn');
    return false;
  }
  try {
    await watchlistWriteBackupHandle(handle);
    watchlistSetBackupStatus('Backup file updated', 'ok');
    return true;
  } catch (_e) {
    await watchlistClearBackupHandle();
    watchlistSetBackupStatus('Backup file unavailable; click Backup again', 'warn');
    return false;
  }
}
function watchlistScheduleAutoBackup(){
  if (!WATCHLIST_BACKUP_HANDLE) return;
  if (WATCHLIST_BACKUP_SAVE_TIMER) clearTimeout(WATCHLIST_BACKUP_SAVE_TIMER);
  WATCHLIST_BACKUP_SAVE_TIMER = setTimeout(() => {
    WATCHLIST_BACKUP_SAVE_TIMER = 0;
    watchlistAutoBackup().catch(() => {});
  }, 140);
}
async function watchlistBackupToFile(forcePicker=false){
  if (!forcePicker && WATCHLIST_BACKUP_HANDLE) {
    const perm = await watchlistQueryBackupPermission(WATCHLIST_BACKUP_HANDLE);
    if (perm === 'granted') {
      const ok = await watchlistAutoBackup();
      if (ok) return true;
    } else if (WATCHLIST_BACKUP_HANDLE.requestPermission) {
      try {
        const nextPerm = await WATCHLIST_BACKUP_HANDLE.requestPermission({ mode:'readwrite' });
        if (nextPerm === 'granted') {
          await watchlistWriteBackupHandle(WATCHLIST_BACKUP_HANDLE);
          watchlistSetBackupStatus('Backup file linked', 'ok');
          return true;
        }
      } catch (_e) {}
    }
  }
  if (window.showSaveFilePicker) {
    let handle = null;
    try {
      handle = await window.showSaveFilePicker({
        suggestedName: WATCHLIST_BACKUP_FILENAME,
        types: [{ description:'JSON Files', accept: { 'application/json': ['.json'] } }]
      });
    } catch (err) {
      if (err && err.name === 'AbortError') return false;
    }
    if (handle) {
      try {
        await watchlistWriteBackupHandle(handle);
        WATCHLIST_BACKUP_HANDLE = handle;
        await watchlistStoreBackupHandle(handle);
        watchlistSetBackupStatus('Backup file linked', 'ok');
        return true;
      } catch (_e) {
        watchlistSetBackupStatus('Could not write backup file', 'warn');
        return false;
      }
    }
  }
  watchlistDownloadBackupFile();
  return true;
}
function watchlistImportBackup(){
  const input = document.getElementById('watchlistImportInput');
  if (!input) return;
  input.value = '';
  input.click();
}
async function watchlistHandleImportFile(evt){
  const input = evt?.target;
  const file = input?.files && input.files[0];
  if (!file) return;
  try {
    const parsed = JSON.parse(await file.text());
    const items = Array.isArray(parsed)
      ? parsed
      : (Array.isArray(parsed?.watchlists) ? parsed.watchlists : null);
    if (!items || !items.length) throw new Error('missing watchlists');
    WATCHLISTS = items.map((w,i)=>watchlistNormalizeList(w, i));
    const nextActiveRaw = Number(parsed?.active);
    const nextActive = Number.isFinite(nextActiveRaw) ? Math.max(0, Math.floor(nextActiveRaw)) : 0;
    ACTIVE_WATCHLIST = Math.min(nextActive, WATCHLISTS.length-1);
    saveWatchlists();
    const _importSyms=[...new Set(
      WATCHLISTS.flatMap(wl=>(wl.items||[])
        .filter(it=>it&&it.type==='symbol'&&it.sym)
        .map(it=>it.sym))
    )].filter(s=>CANDLE_DATA[s]==null);
    renderWatchlist();
    if(_importSyms.length){
      Promise.all(_importSyms.map(s=>blEnsureTickerOHLCV(s)))
        .then(()=>renderWatchlist())
        .catch(()=>{});
    }
    watchlistSetBackupStatus('Backup imported', 'ok');
  } catch (_e) {
    watchlistSetBackupStatus('Import failed', 'warn');
    alert('Could not import watchlist backup file.');
  }
  if (input) input.value = '';
}
async function watchlistInitBackup(){
  const input = document.getElementById('watchlistImportInput');
  if (input && !input.dataset.bound) {
    input.dataset.bound = '1';
    input.addEventListener('change', watchlistHandleImportFile);
  }
  WATCHLIST_BACKUP_HANDLE = await watchlistLoadBackupHandle();
  if (!WATCHLIST_BACKUP_HANDLE) {
    watchlistSetBackupStatus('Local browser storage only');
    return;
  }
  const perm = await watchlistQueryBackupPermission(WATCHLIST_BACKUP_HANDLE);
  watchlistSetBackupStatus(
    perm === 'granted' ? 'Backup file linked' : 'Backup file linked; click Backup to reconnect',
    perm === 'granted' ? 'ok' : 'warn'
  );
}
function watchlistSafeName(name, fallback){
  const v = String(name || '').trim();
  return v || fallback;
}
function watchlistSafeSort(v){
  const sort = String(v || '').trim().toLowerCase();
  return WATCHLIST_SORT_OPTIONS.includes(sort) ? sort : 'manual';
}
function watchlistCurrentSort(wl){
  return watchlistSafeSort(wl?.sort);
}
function watchlistSafeSectionLabel(label, fallback='Section'){
  const v = String(label || '').trim();
  return v || fallback;
}
function watchlistMakeSectionId(){
  return 'wlsec_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}
function normalizeWatchlistSymbols(input){
  const parts = Array.isArray(input)
    ? input.flatMap(v => String(v ?? '').split(/[\s,]+/))
    : String(input ?? '').split(/[\s,]+/);
  const out = [];
  const seen = new Set();
  parts.forEach(raw => {
    const sym = String(raw || '').trim().toUpperCase().replace(/[^A-Z0-9._-]/g, '');
    if (!sym || seen.has(sym)) return;
    seen.add(sym);
    out.push(sym);
  });
  return out;
}
function watchlistNormalizeItems(input){
  const arr = Array.isArray(input) ? input : [];
  const out = [];
  const seenSym = new Set();
  const seenIds = new Set();
  arr.forEach(raw => {
    if (raw && typeof raw === 'object' && String(raw.type || '').toLowerCase() === 'section') {
      let id = String(raw.id || '').trim();
      if (!id || seenIds.has(id)) id = watchlistMakeSectionId();
      seenIds.add(id);
      const secItem = {
        type: 'section',
        id,
        label: watchlistSafeSectionLabel(raw.label ?? raw.name, 'Section')
      };
      if (raw.color && typeof raw.color === 'string') secItem.color = raw.color;
      out.push(secItem);
      return;
    }
    const seed = raw && typeof raw === 'object' ? (raw.sym ?? raw.value ?? raw.ticker ?? raw.symbol ?? '') : raw;
    const sym = normalizeWatchlistSymbols([seed])[0];
    if (!sym || seenSym.has(sym)) return;
    seenSym.add(sym);
    out.push({ type: 'symbol', sym });
  });
  return out;
}
function watchlistNormalizeList(w, i){
  const srcItems = Array.isArray(w?.items) ? w.items : w?.symbols;
  return {
    name: watchlistSafeName(w?.name, `List ${i+1}`),
    sort: watchlistSafeSort(w?.sort),
    items: watchlistNormalizeItems(srcItems)
  };
}
function watchlistEnsureItems(wl){
  if (!wl) return [];
  const norm = watchlistNormalizeList(wl, 0);
  wl.name = norm.name;
  wl.sort = norm.sort;
  wl.items = norm.items;
  try { delete wl.symbols; } catch (_e) {}
  return wl.items;
}
function _applyWatchlistData(arr, active){
  if(Array.isArray(arr)&&arr.length){
    WATCHLISTS=arr.map((w,i)=>watchlistNormalizeList(w,i));
    if(Number.isFinite(active)) ACTIVE_WATCHLIST=Math.min(active,WATCHLISTS.length-1);
    else ACTIVE_WATCHLIST=Math.min(ACTIVE_WATCHLIST,WATCHLISTS.length-1);
    return true;
  }
  return false;
}
function _activeWatchlistSymbols(){
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return [];
  return [...new Set(
    watchlistEnsureItems(wl)
      .filter(it=>it&&it.type==='symbol'&&it.sym)
      .map(it=>String(it.sym||'').trim().toUpperCase())
      .filter(Boolean)
  )];
}
function _allWatchlistSymbols(){
  return [...new Set(
    (WATCHLISTS||[]).flatMap(wl=>
      watchlistEnsureItems(wl)
        .filter(it=>it&&it.type==='symbol'&&it.sym)
        .map(it=>String(it.sym||'').trim().toUpperCase())
        .filter(Boolean)
    )
  )];
}
// Prefetch GI chart data for watchlist symbols not yet cached, staggered to
// avoid server overload. Fires quietly in background – no render callbacks.
let _prefetchGITimer=null;
function _prefetchWatchlistGIData(){
  if(_prefetchGITimer) return; // already scheduled
  _prefetchGITimer=setTimeout(()=>{
    _prefetchGITimer=null;
    const syms=_activeWatchlistSymbols().filter(s=>!_blChartDataHasCoreLoaded(s));
    if(!syms.length) return;
    let idx=0;
    const maxConcurrent=3;
    let active=0;
    const pump=()=>{
      while(active<maxConcurrent&&idx<syms.length){
        const sym=syms[idx++];
        active++;
        blEnsureTickerChartData(sym).catch(()=>{}).finally(()=>{
          active--;
          if(idx<syms.length) pump();
        });
      }
    };
    pump();
  }, 800); // small delay so the active ticker loads first
}
function _prefetchWatchlistOHLCV(){
  // Only fetch for the currently open watchlist — other lists load when switched to
  const activeSyms=_activeWatchlistSymbols();
  const syms=activeSyms.filter(s=>CANDLE_DATA[s]==null);
  if(!syms.length) return;
  const activeSet=new Set(activeSyms);
  const maxConcurrent=6;
  let idx=0,active=0;
  const pump=()=>{
    while(active<maxConcurrent&&idx<syms.length){
      const sym=syms[idx++];
      active++;
      blEnsureTickerOHLCV(sym)
        .catch(()=>{})
        .finally(()=>{
          active--;
          if(activeSet.has(sym)) renderWatchlist();
          if(idx<syms.length) pump();
          else if(active===0) renderWatchlist();
        });
    }
  };
  pump();
}
function loadWatchlists(){
  loadWatchlistPrefs();
  let loadedFromLocal=false;
  // Sync from localStorage immediately so WATCHLISTS is populated before live poll
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    if(raw){
      const arr=JSON.parse(raw);
      loadedFromLocal=_applyWatchlistData(arr, null)||loadedFromLocal;
    }
  } catch (e) {}
  if(!WATCHLISTS.length){
    WATCHLISTS = [{
      name: 'Owned',
      sort: 'manual',
      items: ['AAPL','MSFT','GOOG','AMZN','TSLA'].map(sym=>({ type:'symbol', sym }))
    }];
    ACTIVE_WATCHLIST = 0;
  }
  // Then sync from server (authoritative), update if newer
  _fetchServerPrefs().then(serverPrefs=>{
    const sd=serverPrefs[WATCHLIST_KEY];
    if(sd&&typeof sd==='object'&&Array.isArray(sd.watchlists)&&sd.watchlists.length){
      try{ localStorage.setItem(WATCHLIST_KEY, JSON.stringify(sd.watchlists)); }catch(_e){}
      _applyWatchlistData(sd.watchlists, sd.active);
      renderWatchlist();
      _prefetchWatchlistOHLCV();
      return;
    }
    // Backfill server prefs when local browser state exists but server file is missing.
    if(loadedFromLocal&&WATCHLISTS.length){
      _syncPrefsToServer(WATCHLIST_KEY, {watchlists:WATCHLISTS, active:ACTIVE_WATCHLIST}, {immediate:true, keepalive:true});
    }
  }).catch(()=>{});
}
function saveWatchlists(){
  WATCHLISTS = WATCHLISTS.map((w,i)=>watchlistNormalizeList(w, i));
  try { localStorage.setItem(WATCHLIST_KEY, JSON.stringify(WATCHLISTS)); } catch (e) {}
  saveWatchlistPrefs();
  watchlistScheduleAutoBackup();
  _syncPrefsToServer(WATCHLIST_KEY, {watchlists:WATCHLISTS, active:ACTIVE_WATCHLIST}, {immediate:true, keepalive:true});
}
function getActiveWatchTicker(){
  return blCurrentTicker() || String(document.getElementById('blTF')?.value || '').trim().toUpperCase();
}
function watchlistFocusList(){
  const list = document.getElementById('watchlistList');
  if (!list) return;
  try { list.focus({ preventScroll:true }); } catch (_e) {
    try { list.focus(); } catch (_e2) {}
  }
}
function watchlistVisibleSymbols(){
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return [];
  return watchlistSortedItems(wl, getCandleData())
    .filter(item=>item && item.type==='symbol' && item.sym)
    .map(item=>item.sym);
}
function watchlistScrollToSymbol(sym){
  const rows = Array.from(document.querySelectorAll('#watchlistList .watchlist-row[data-watch-sym]'));
  const row = rows.find(el=>el.getAttribute('data-watch-sym')===sym) || document.querySelector('#watchlistList .watchlist-row.active');
  if (!row) return;
  try { row.scrollIntoView({ block:'nearest' }); } catch (_e) {}
}
function watchlistStepSelection(step){
  const symbols = watchlistVisibleSymbols();
  if (!symbols.length) return false;
  const active = getActiveWatchTicker();
  let idx = symbols.indexOf(active);
  if (idx < 0) idx = step > 0 ? -1 : symbols.length;
  const nextIdx = Math.max(0, Math.min(symbols.length - 1, idx + step));
  const nextSym = symbols[nextIdx];
  if (!nextSym) return false;
  if (nextSym !== active) goChart(nextSym);
  watchlistFocusList();
  setTimeout(() => watchlistScrollToSymbol(nextSym), 0);
  return true;
}
function watchlistIconHue(sym){
  let hash = 0;
  String(sym || '').split('').forEach(ch => { hash = (hash * 33 + ch.charCodeAt(0)) % 360; });
  return hash;
}
function watchlistIconBg(sym){
  const hue = watchlistIconHue(sym);
  return `linear-gradient(135deg, hsla(${hue},78%,58%,0.98), hsla(${(hue+28)%360},80%,43%,0.98))`;
}
function watchlistInitial(sym){
  const clean = String(sym || '').replace(/[^A-Z0-9]/gi, '').toUpperCase();
  return clean ? clean[0] : '?';
}
function blSymbolChangeSnapshot(sym, bars){
  const series = Array.isArray(bars) ? bars : [];
  const last = series.length ? (series[series.length - 1] || {}) : null;
  const prev = series.length > 1 ? (series[series.length - 2] || null) : null;
  const barClose = Number(last?.c);
  const prevClose = Number(prev?.c);
  if (Number.isFinite(barClose) && Number.isFinite(prevClose) && prevClose !== 0) {
    const delta = barClose - prevClose;
    const pct = (delta / prevClose) * 100;
    return { price: barClose, delta, pct };
  }
  const live = sym ? _blLiveQuoteCache[sym] : null;
  const livePrice = (live?.regular_session===true && _blLiveRegularSession) ? Number(live?.price) : NaN;
  if (Number.isFinite(livePrice)) {
    let delta = Number(live?.change);
    let pct = Number(live?.changePct);
    if (!(Number.isFinite(delta) && Number.isFinite(pct))) {
      const liveClose = Number(live?.close_price);
      if (Number.isFinite(liveClose) && liveClose !== 0) {
        delta = livePrice - liveClose;
        pct = (delta / liveClose) * 100;
      }
    }
    if (!(Number.isFinite(delta) && Number.isFinite(pct))) {
      delta = null;
      pct = null;
    }
    return { price: livePrice, delta, pct };
  }
  if (Number.isFinite(barClose)) return { price: barClose, delta: null, pct: null };
  return null;
}
function watchlistQuoteFromBars(sym, bars){
  const snap = blSymbolChangeSnapshot(sym, bars);
  if (!snap || !Number.isFinite(Number(snap.price))) {
    return { price:'--', delta:'--', pct:'--', cls:'neu', priceNum:null, deltaNum:null, pctNum:null };
  }
  const close = Number(snap.price);
  const delta = Number.isFinite(Number(snap.delta)) ? Number(snap.delta) : null;
  const pct = Number.isFinite(Number(snap.pct)) ? Number(snap.pct) : null;
  let cls = 'neu';
  if (delta != null) {
    if (delta > 0) cls = 'pos';
    else if (delta < 0) cls = 'neg';
  }
  return {
    price: '$' + close.toFixed(2),
    delta: delta == null ? '--' : `${delta>=0?'+':''}${delta.toFixed(2)}`,
    pct: pct == null ? '--' : `${pct>=0?'+':''}${pct.toFixed(2)}%`,
    cls,
    priceNum: close,
    deltaNum: delta,
    pctNum: pct
  };
}
function watchlistItemId(item){
  if (!item) return '';
  return item.type === 'section' ? String(item.id || '') : 'sym:' + String(item.sym || '');
}
function watchlistMakeSection(label){
  return {
    type: 'section',
    id: watchlistMakeSectionId(),
    label: watchlistSafeSectionLabel(label, 'Section')
  };
}
function watchlistSortSymbolItems(items, sort){
  const sorted = [...items];
  const cmpNum = (a,b,key,desc) => {
    const av = a.quote[key];
    const bv = b.quote[key];
    const aOk = Number.isFinite(av);
    const bOk = Number.isFinite(bv);
    if (aOk && bOk && bv !== av) return desc ? bv - av : av - bv;
    if (aOk !== bOk) return aOk ? -1 : 1;
    return a.sym.localeCompare(b.sym);
  };
  if (sort === 'alpha')       sorted.sort((a,b)=>a.sym.localeCompare(b.sym));
  else if (sort === 'alpha-desc') sorted.sort((a,b)=>b.sym.localeCompare(a.sym));
  else if (sort === 'price')      sorted.sort((a,b)=>cmpNum(a,b,'priceNum',true));
  else if (sort === 'price-desc') sorted.sort((a,b)=>cmpNum(a,b,'priceNum',false));
  else if (sort === 'pct')        sorted.sort((a,b)=>cmpNum(a,b,'pctNum',true));
  else if (sort === 'pct-desc')   sorted.sort((a,b)=>cmpNum(a,b,'pctNum',false));
  return sorted;
}
function watchlistSortedItems(wl, candleData){
  const items = watchlistEnsureItems(wl).map(item=>
    item.type === 'symbol'
      ? Object.assign({}, item, { quote: watchlistQuoteFromBars(item.sym, candleData[item.sym] || []) })
      : Object.assign({}, item)
  );
  const sort = watchlistCurrentSort(wl);
  if (sort === 'manual') return items;
  const out = [];
  let bucket = [];
  const flush = ()=>{
    if (!bucket.length) return;
    out.push(...watchlistSortSymbolItems(bucket, sort));
    bucket = [];
  };
  items.forEach(item=>{
    if (item.type === 'section') {
      flush();
      out.push(item);
      return;
    }
    bucket.push(item);
  });
  flush();
  return out;
}
function watchlistClearDragClasses(){
  document.querySelectorAll('#watchlistList .watchlist-row').forEach(row=>{
    row.classList.remove('dragging','drop-before','drop-after');
  });
}
function watchlistHandleDragEnd(){
  WATCHLIST_DRAG_ID = '';
  watchlistClearDragClasses();
}
function watchlistMoveItem(wl, fromId, toId, placeAfter){
  if (!wl) return false;
  const items = [...watchlistEnsureItems(wl)];
  const fromIdx = items.findIndex(item=>watchlistItemId(item)===fromId);
  const toIdx = items.findIndex(item=>watchlistItemId(item)===toId);
  if (fromIdx < 0 || toIdx < 0 || fromIdx === toIdx) return false;
  const [moved] = items.splice(fromIdx, 1);
  let insertIdx = items.findIndex(item=>watchlistItemId(item)===toId);
  if (insertIdx < 0) return false;
  if (placeAfter) insertIdx += 1;
  items.splice(insertIdx, 0, moved);
  wl.items = items;
  return true;
}
function watchlistBindRowDrag(row, item, wl){
  if (!row || watchlistCurrentSort(wl) !== 'manual') return;
  const itemId = watchlistItemId(item);
  if (!itemId) return;
  row.draggable = true;
  row.classList.add('reorderable');
  row.addEventListener('dragstart', evt=>{
    WATCHLIST_DRAG_ID = itemId;
    row.classList.add('dragging');
    try {
      evt.dataTransfer.effectAllowed = 'move';
      evt.dataTransfer.setData('text/plain', itemId);
    } catch (_e) {}
  });
  row.addEventListener('dragover', evt=>{
    if (!WATCHLIST_DRAG_ID) return;
    evt.preventDefault();
    try { evt.dataTransfer.dropEffect = 'move'; } catch (_e) {}
    watchlistClearDragClasses();
    if (WATCHLIST_DRAG_ID === itemId) {
      row.classList.add('dragging');
      return;
    }
    const rect = row.getBoundingClientRect();
    const after = (evt.clientY - rect.top) > rect.height / 2;
    row.classList.add(after ? 'drop-after' : 'drop-before');
  });
  row.addEventListener('drop', evt=>{
    if (!WATCHLIST_DRAG_ID) return;
    evt.preventDefault();
    evt.stopPropagation();
    const rect = row.getBoundingClientRect();
    const after = (evt.clientY - rect.top) > rect.height / 2;
    const moved = WATCHLIST_DRAG_ID !== itemId && watchlistMoveItem(wl, WATCHLIST_DRAG_ID, itemId, after);
    watchlistHandleDragEnd();
    if (moved) {
      saveWatchlists();
      renderWatchlist();
    }
  });
  row.addEventListener('dragend', watchlistHandleDragEnd);
}
function promptAddWatchlistSymbols(){
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return;
  const cur = getActiveWatchTicker();
  const input = prompt('Add symbols (comma or space separated):', cur || '');
  if (input == null) return;
  const items = [...watchlistEnsureItems(wl)];
  const seen = new Set(items.filter(item=>item.type==='symbol').map(item=>item.sym));
  const newSyms = [];
  normalizeWatchlistSymbols(input).forEach(sym=>{
    if (seen.has(sym)) return;
    seen.add(sym);
    items.push({ type:'symbol', sym });
    newSyms.push(sym);
  });
  wl.items = items;
  saveWatchlists();
  renderWatchlist();
  if (newSyms.length) {
    // Immediately fetch OHLCV + chart data for the newly added symbols
    _prefetchWatchlistOHLCV();
    _prefetchWatchlistGIData();
  }
}
function promptAddWatchlistSection(){
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return;
  const label = prompt('Section name?', 'Section');
  if (label == null) return;
  const items = [...watchlistEnsureItems(wl)];
  items.push(watchlistMakeSection(label));
  wl.items = items;
  saveWatchlists();
  renderWatchlist();
}
function renameWatchlistSection(sectionId, evt){ editWatchlistSection(sectionId, evt); }
let _wlEditPopupEl=null, _wlEditSectionItem=null;
function _getWlEditPopup(){
  if(_wlEditPopupEl) return _wlEditPopupEl;
  const p=document.createElement('div');
  p.id='wlSectionEditPop';
  p.style.cssText='position:fixed;z-index:2400;background:#181818;border:1px solid #2a2a2a;border-radius:9px;padding:10px 12px;box-shadow:0 8px 24px rgba(0,0,0,.6);display:none;min-width:190px';
  p.innerHTML=`<div style="font-size:9px;color:#666;text-transform:uppercase;letter-spacing:.08em;margin-bottom:7px">Edit Section</div>
<input id="wlSecNameInp" type="text" style="width:100%;box-sizing:border-box;background:#0f0f0f;border:1px solid #2e2e2e;border-radius:5px;color:#e8e8e8;font-size:12px;padding:5px 8px;outline:none;margin-bottom:8px" placeholder="Section name">
<div style="display:flex;align-items:center;gap:7px;margin-bottom:10px">
  <span style="font-size:10px;color:#777;flex-shrink:0">Color</span>
  <input id="wlSecColorInp" type="color" title="Section label color" style="width:26px;height:20px;border:1px solid #333;border-radius:4px;cursor:pointer;padding:0;background:none">
  <button id="wlSecClearClr" type="button" style="font-size:10px;color:#777;background:none;border:1px solid #2a2a2a;border-radius:4px;padding:2px 7px;cursor:pointer;white-space:nowrap">Clear</button>
</div>
<div style="display:flex;gap:6px;justify-content:flex-end">
  <button id="wlSecCancelBtn" type="button" style="font-size:11px;color:#888;background:#111;border:1px solid #2a2a2a;border-radius:5px;padding:4px 10px;cursor:pointer">Cancel</button>
  <button id="wlSecSaveBtn" type="button" style="font-size:11px;color:#fff;background:#1e4a2e;border:1px solid #28603e;border-radius:5px;padding:4px 12px;cursor:pointer;font-weight:700">Save</button>
</div>`;
  document.body.appendChild(p);
  _wlEditPopupEl=p;
  document.addEventListener('mousedown',e=>{
    if(!_wlEditPopupEl||_wlEditPopupEl.style.display==='none') return;
    if(!_wlEditPopupEl.contains(e.target)) _closeWlEditPopup();
  },true);
  return p;
}
function _closeWlEditPopup(){
  if(_wlEditPopupEl) _wlEditPopupEl.style.display='none';
  _wlEditSectionItem=null;
}
function editWatchlistSection(sectionId, evt){
  evt?.preventDefault?.();
  evt?.stopPropagation?.();
  const wl=WATCHLISTS[ACTIVE_WATCHLIST];
  if(!wl) return;
  const item=watchlistEnsureItems(wl).find(e=>e.type==='section'&&e.id===sectionId);
  if(!item) return;
  _wlEditSectionItem=item;
  const p=_getWlEditPopup();
  document.getElementById('wlSecNameInp').value=item.label||'';
  document.getElementById('wlSecColorInp').value=item.color||'#d0d4da';
  const btn=evt?.currentTarget||evt?.target;
  const ref=btn?btn.getBoundingClientRect():{left:200,bottom:200,right:220,top:180};
  const PW=210,PH=148;
  let left=ref.left, top=ref.bottom+4;
  if(left+PW>window.innerWidth-10) left=window.innerWidth-PW-10;
  if(top+PH>window.innerHeight-10) top=ref.top-PH-4;
  if(left<6) left=6;
  p.style.left=left+'px'; p.style.top=top+'px'; p.style.display='block';
  const nameInp=document.getElementById('wlSecNameInp');
  nameInp.focus(); nameInp.select();
  function doSave(){
    const newLabel=nameInp.value.trim();
    if(newLabel) item.label=watchlistSafeSectionLabel(newLabel,item.label||'Section');
    const col=document.getElementById('wlSecColorInp').value;
    item.color=(col&&col!=='#d0d4da')?col:'';
    _closeWlEditPopup(); saveWatchlists(); renderWatchlist();
  }
  document.getElementById('wlSecSaveBtn').onclick=doSave;
  document.getElementById('wlSecCancelBtn').onclick=_closeWlEditPopup;
  document.getElementById('wlSecClearClr').onclick=()=>{ item.color=''; _closeWlEditPopup(); saveWatchlists(); renderWatchlist(); };
  nameInp.onkeydown=e=>{ if(e.key==='Enter') doSave(); if(e.key==='Escape') _closeWlEditPopup(); };
}
function removeWatchlistSection(sectionId, evt){
  evt?.preventDefault?.();
  evt?.stopPropagation?.();
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return;
  wl.items = watchlistEnsureItems(wl).filter(item=>!(item.type==='section'&&item.id===sectionId));
  saveWatchlists();
  renderWatchlist();
}
function removeWatchlistSymbol(sym, evt){
  evt?.preventDefault?.();
  evt?.stopPropagation?.();
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return;
  wl.items = watchlistEnsureItems(wl).filter(item=>!(item.type==='symbol'&&item.sym===sym));
  saveWatchlists();
  renderWatchlist();
}
function renderWatchlist(){
  const wl = WATCHLISTS[ACTIVE_WATCHLIST] || { sort:'manual', items: [] };
  const list = document.getElementById('watchlistList');
  if (!list) return;
  list.innerHTML = '';
  const candleData = getCandleData();
  const activeTicker = getActiveWatchTicker();
  const items = watchlistSortedItems(wl, candleData);
  const manualMode = watchlistCurrentSort(wl) === 'manual';
  if (!items.length) {
    list.innerHTML = '<div class="watchlist-empty">No items in this watchlist. Use the buttons below to add symbols or sections.</div>';
  } else items.forEach(item => {
    if (item.type === 'section') {
      const secColor = item.color || '';
      const row = document.createElement('div');
      row.className = 'watchlist-row watchlist-section-row';
      row.title = manualMode ? 'Section | drag to reorder' : 'Section';
      const main = document.createElement('div');
      main.className = 'watchlist-section-main';
      main.ondblclick = evt => editWatchlistSection(item.id, evt);
      const label = document.createElement('span');
      label.className = 'watchlist-section-label';
      label.textContent = item.label || 'Section';
      if (secColor) label.style.color = secColor;
      const rule = document.createElement('span');
      rule.className = 'watchlist-section-rule';
      if (secColor) {
        rule.style.background = `linear-gradient(90deg, ${secColor}80, ${secColor}00)`;
      }
      main.appendChild(label);
      main.appendChild(rule);
      row.appendChild(main);
      const renameBtn = document.createElement('button');
      renameBtn.type = 'button';
      renameBtn.className = 'watchlist-section-btn';
      renameBtn.title = 'Edit name & color';
      renameBtn.textContent = 'Edit';
      renameBtn.onclick = evt => editWatchlistSection(item.id, evt);
      row.appendChild(renameBtn);
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'watchlist-remove';
      removeBtn.title = 'Remove section';
      removeBtn.textContent = 'x';
      removeBtn.onclick = evt => removeWatchlistSection(item.id, evt);
      row.appendChild(removeBtn);
      watchlistBindRowDrag(row, item, wl);
      list.appendChild(row);
      return;
    }
    const sym = item.sym;
    const quote = item.quote;
    const row = document.createElement('div');
    row.className = 'watchlist-row' + (sym === activeTicker ? ' active' : '');
    row.setAttribute('data-watch-sym', sym);
    row.onclick = () => {
      watchlistFocusList();
      goChart(sym);
    };
    const symWrap = document.createElement('div');
    symWrap.className = 'watchlist-symbol-wrap';
    const handle = document.createElement('span');
    handle.className = 'watchlist-drag-handle';
    handle.textContent = '';
    symWrap.appendChild(handle);
    const symEl = document.createElement('span');
    symEl.className = 'watchlist-symbol';
    symEl.textContent = sym;
    symWrap.appendChild(symEl);
    row.appendChild(symWrap);
    const price = document.createElement('span');
    price.className = 'watchlist-price';
    price.textContent = quote.price;
    if (quote.price === '--') price.classList.add('na');
    row.appendChild(price);
    const pct = document.createElement('span');
    pct.className = 'watchlist-pct ' + quote.cls;
    pct.textContent = quote.pct;
    row.appendChild(pct);
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'watchlist-remove';
    removeBtn.textContent = 'x';
    removeBtn.onclick = evt => removeWatchlistSymbol(sym, evt);
    row.appendChild(removeBtn);
    watchlistBindRowDrag(row, item, wl);
    list.appendChild(row);
  });
  const addRow = document.createElement('div');
  addRow.className = 'watchlist-add-row';
  const addSymbolBtn = document.createElement('button');
  addSymbolBtn.type = 'button';
  addSymbolBtn.className = 'watchlist-add-btn';
  addSymbolBtn.title = 'Add symbol (or press Alt+W on chart)';
  addSymbolBtn.textContent = '+ Symbol';
  addSymbolBtn.onclick = evt => {
    evt.preventDefault();
    evt.stopPropagation();
    promptAddWatchlistSymbols();
  };
  addRow.appendChild(addSymbolBtn);
  const addSectionBtn = document.createElement('button');
  addSectionBtn.type = 'button';
  addSectionBtn.className = 'watchlist-add-btn';
  addSectionBtn.title = 'Add section';
  addSectionBtn.textContent = '+ Section';
  addSectionBtn.onclick = evt => {
    evt.preventDefault();
    evt.stopPropagation();
    promptAddWatchlistSection();
  };
  addRow.appendChild(addSectionBtn);
  const altWHint = document.createElement('span');
  altWHint.style.cssText = 'color:#666;font-family:var(--sans);font-size:9px;font-weight:600;letter-spacing:.03em;align-self:center;margin-right:4px;order:-1';
  altWHint.textContent = 'Alt+W';
  addRow.appendChild(altWHint);
  list.appendChild(addRow);
  list.ondragover = evt => {
    if (!manualMode || !WATCHLIST_DRAG_ID) return;
    evt.preventDefault();
  };
  list.ondrop = evt => {
    if (!manualMode || !WATCHLIST_DRAG_ID) return;
    evt.preventDefault();
    const manualItems = watchlistEnsureItems(wl);
    const lastItem = manualItems[manualItems.length-1];
    const lastId = watchlistItemId(lastItem);
    const moved = lastId ? watchlistMoveItem(wl, WATCHLIST_DRAG_ID, lastId, true) : false;
    watchlistHandleDragEnd();
    if (moved) {
      saveWatchlists();
      renderWatchlist();
    }
  };
  const dd = document.getElementById('watchlistDropdown');
  if (dd) {
    dd.innerHTML = WATCHLISTS.map((w,i)=>`<option value="${i}"${i===ACTIVE_WATCHLIST?' selected':''}>${w.name}</option>`).join('')
      + `<option disabled>----------</option>`
      + `<option value="${WATCHLIST_SETTINGS_VALUE}">Settings...</option>`;
    dd.onchange = e => {
      const val = String(e.target.value||'');
      if (val === WATCHLIST_SETTINGS_VALUE) {
        dd.value = String(ACTIVE_WATCHLIST);
        toggleWlSettings();
        return;
      }
      ACTIVE_WATCHLIST = Number(val)||0;
      saveWatchlistPrefs();
      // Persist active index to server so it survives a full reload
      _syncPrefsToServer(WATCHLIST_KEY, {watchlists:WATCHLISTS, active:ACTIVE_WATCHLIST}, {immediate:true, keepalive:true});
      renderWatchlist();
      if (_blLiveQuoteCache && Object.keys(_blLiveQuoteCache).length) {
        blApplyLiveQuotes(_blLiveQuoteCache);
      }
      _prefetchWatchlistOHLCV();
      if(_blAutoRefreshSecs>0) blLivePollOnce(true).catch(()=>{});
    };
  }
  wlSyncColHeads(watchlistCurrentSort(wl));
  syncWatchlistPanelButton();
}
function _savePanelStates(){
  try{ localStorage.setItem('gekko_panel_states',JSON.stringify({
    watchlist: document.body.classList.contains('watchlist-open'),
    left: document.body.classList.contains('panel-open')
  })); }catch(_e){}
}
function toggleWatchlistPanel(forceOpen){
  const nextState = typeof forceOpen === 'boolean' ? forceOpen : !document.body.classList.contains('watchlist-open');
  document.body.classList.toggle('watchlist-open', nextState);
  syncWatchlistPanelButton();
  _savePanelStates();
  if (nextState) {
    setTimeout(watchlistFocusList, 0);
    blQueueImmediateLivePoll();
  }
}
let _blLeftPanelUserClosed = false;
function toggleLeftPanel(forceOpen){
  const nextState = typeof forceOpen === 'boolean' ? forceOpen : !document.body.classList.contains('panel-open');
  _blLeftPanelUserClosed = !nextState;
  document.body.classList.toggle('panel-open', nextState);
  _savePanelStates();
}
function toggleWlSettings(){
  const menu=document.getElementById('wlSettingsMenu');
  if(!menu) return;
  menu.classList.toggle('open');
}
function wlToggleSort(col){
  const wl=WATCHLISTS[ACTIVE_WATCHLIST];
  if(!wl) return;
  const cur=watchlistCurrentSort(wl);
  if(cur===col) wl.sort=col+'-desc';
  else if(cur===col+'-desc') wl.sort='manual';
  else wl.sort=col;
  saveWatchlists();
  renderWatchlist();
}
const _WL_HEAD_LABELS={wlHeadSym:'Symbol',wlHeadPrice:'Last',wlHeadPct:'Chg%'};
const _WL_HEAD_SORT={wlHeadSym:'alpha',wlHeadPrice:'price',wlHeadPct:'pct'};
function wlSyncColHeads(sort){
  Object.keys(_WL_HEAD_LABELS).forEach(id=>{
    const el=document.getElementById(id);
    if(!el) return;
    const base=_WL_HEAD_SORT[id];
    const isAsc=sort===base;
    const isDesc=sort===base+'-desc';
    el.classList.toggle('active',isAsc||isDesc);
    el.textContent=_WL_HEAD_LABELS[id]+(isAsc?' \u2191':isDesc?' \u2193':'');
  });
}
function _closeWlSettings(){
  const btn=document.getElementById('wlSettingsToggle');
  const menu=document.getElementById('wlSettingsMenu');
  if(menu) menu.classList.remove('open');
  if(btn) btn.classList.remove('open');
}
function addWatchlist(){
  _closeWlSettings();
  const name = prompt('New watchlist name?', 'Owned');
  if (!name) return;
  WATCHLISTS.push({ name: watchlistSafeName(name, `List ${WATCHLISTS.length+1}`), sort:'manual', items: [] });
  ACTIVE_WATCHLIST = WATCHLISTS.length-1;
  saveWatchlists();
  renderWatchlist();
}
function renameWatchlist(){
  _closeWlSettings();
  const wl = WATCHLISTS[ACTIVE_WATCHLIST];
  if (!wl) return;
  const currentName = wl.name || `List ${ACTIVE_WATCHLIST+1}`;
  const name = prompt('Rename watchlist:', currentName);
  if (name == null) return;
  wl.name = watchlistSafeName(name, currentName);
  saveWatchlists();
  renderWatchlist();
}
function moveWatchlist(step){
  _closeWlSettings();
  const from = Number(ACTIVE_WATCHLIST) || 0;
  const to = from + (Number(step) || 0);
  if (to < 0 || to >= WATCHLISTS.length || to === from) return;
  const moved = WATCHLISTS.splice(from, 1)[0];
  if (!moved) return;
  WATCHLISTS.splice(to, 0, moved);
  ACTIVE_WATCHLIST = to;
  saveWatchlists();
  renderWatchlist();
}
function deleteWatchlist(){
  _closeWlSettings();
  if (WATCHLISTS.length<=1) return alert('Cannot delete last watchlist.');
  if (!confirm('Delete this watchlist?')) return;
  WATCHLISTS.splice(ACTIVE_WATCHLIST,1);
  ACTIVE_WATCHLIST = Math.max(0,ACTIVE_WATCHLIST-1);
  saveWatchlists();
  renderWatchlist();
}

function normInsiderKey(v){
  return String(v||'').trim().toLowerCase();
}
function normManagerKey(v){
  return String(v||'').trim().toLowerCase();
}
function makeInsiderColor(i){
  const hue=((i*137.508)%360+360)%360;
  const sat=(i%2===0)?82:70;
  const light=(i%3===0)?58:(i%3===1?50:42);
  return `hsl(${hue.toFixed(1)}, ${sat}%, ${light}%)`;
}
function makeManagerColor(i){
  const hue=((i*137.508+26)%360+360)%360;
  const sat=(i%2===0)?74:66;
  const light=(i%3===0)?60:(i%3===1?52:44);
  return `hsl(${hue.toFixed(1)}, ${sat}%, ${light}%)`;
}
function buildInsiderColorMap(){
  const keys=[...new Set(INSIDERS.map(r=>normInsiderKey(r&&r.insider)).filter(Boolean))].sort();
  keys.forEach((k,i)=>{INSIDER_COLOR_MAP[k]=makeInsiderColor(i);});
}
function buildManagerColorMap(){
  const keys=[...new Set(HOLDINGS.map(r=>normManagerKey(r&&r.manager)).filter(Boolean))].sort();
  keys.forEach((k,i)=>{MANAGER_COLOR_MAP[k]=makeManagerColor(i);});
}
function insiderColor(name){
  const key=normInsiderKey(name);
  if(!key) return 'var(--muted)';
  if(!INSIDER_COLOR_MAP[key]) INSIDER_COLOR_MAP[key]=makeInsiderColor(Object.keys(INSIDER_COLOR_MAP).length);
  return INSIDER_COLOR_MAP[key];
}
function managerColor(name){
  const key=normManagerKey(name);
  if(!key) return 'var(--muted)';
  if(!MANAGER_COLOR_MAP[key]) MANAGER_COLOR_MAP[key]=makeManagerColor(Object.keys(MANAGER_COLOR_MAP).length);
  return MANAGER_COLOR_MAP[key];
}
function insiderColorIfKnown(name){
  const key=normInsiderKey(name);
  return (key&&INSIDER_COLOR_MAP[key])?INSIDER_COLOR_MAP[key]:'';
}
function managerColorIfKnown(name){
  const key=normManagerKey(name);
  return (key&&MANAGER_COLOR_MAP[key])?MANAGER_COLOR_MAP[key]:'';
}
buildInsiderColorMap();
buildManagerColorMap();
function countDistinctInsiderBuys(ticker,cutoffMs){
  const rows=INSIDER_BUY_INDEX[ticker]||[];
  if(!rows.length) return 0;
  const seen=new Set();
  rows.forEach(r=>{
    if(cutoffMs){
      const ts=r.d?new Date(r.d).getTime():NaN;
      if(!Number.isFinite(ts)||ts<cutoffMs) return;
    }
    seen.add(r.k);
  });
  return seen.size;
}


function sendRotationMode(mode){
  const frame=document.getElementById('rotationFrame');
  try{ if(frame && frame.contentWindow) frame.contentWindow.postMessage({type:'rotation-mode',mode}, '*'); }catch(_e){}
}
function _findTabButton(name){
  const buttons=[...document.querySelectorAll('.tab-btn')];
  return buttons.find(b=>{
    const oc=String(b.getAttribute('onclick')||'');
    return oc.includes("'"+name+"'");
  }) || null;
}
function _isTabAvailable(name){
  const pane=document.getElementById('tab-'+name);
  if(!pane) return false;
  const btn=_findTabButton(name);
  if(!btn) return false;
  const style=window.getComputedStyle(btn);
  if(style.display==='none' || style.visibility==='hidden') return false;
  return true;
}
function _loadSavedTab(){
  try{
    const v=String(localStorage.getItem(TAB_UI_KEY)||'').trim();
    return v||'';
  }catch(_e){ return ''; }
}
function _saveCurrentTab(name){
  try{ localStorage.setItem('_activeTab', name); }catch(_e){}
}
function _getSavedTab(){
  try{ return localStorage.getItem('_activeTab')||'buylevels'; }catch(_e){ return 'buylevels'; }
}
function rotSetModeOuter(mode,btn){
  document.querySelectorAll('#tab-rotation .rot-mode-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  sendRotationMode(mode);
}
function loadRotationFrame(){
  const frame=document.getElementById('rotationFrame');
  const msg=document.getElementById('rotationFrameMsg');
  if(!frame) return;
  if(frame.dataset.loaded==='1'){if(msg)msg.style.display='none';return;}
  frame.dataset.loaded='1';
  if(msg){msg.textContent='Loading rotation...';msg.style.display='flex';}
  frame.src=ROTATION_FRAME_SRC;
  frame.addEventListener('load',function(){
    if(msg)msg.style.display='none';
    // Set timestamp on first-ever load; after browser F5 the localStorage value is already restored
    if(!_tabRefreshTs['rotation']) _updateRefreshTs('rotation');
    sendRotationMode(document.getElementById('rotModeCross2')?.classList.contains('active')?'crossAsset':'sectors');
  },{once:true});
  frame.addEventListener('error',function(){
    frame.dataset.loaded='';
    if(msg){msg.textContent='Rotation failed to load.';msg.style.display='flex';}
  },{once:true});
}
function ensureTabReady(name){
  if(name==='buylevels'){
    const firstOpen = !TAB_INIT.buylevels;
    TAB_INIT.buylevels = 1;
    _renderRefreshTs('buylevels');
    const rerender = (selectDefault=false) => {
      blRefreshTickers(selectDefault);
      renderBuyLevels();
    };
    if (!Object.keys(BUY_META || {}).length && (firstOpen || _buyMetaFetchPromise || _insidersFetchPromise)) {
      const empty=document.getElementById('blEmpty');
      const section=document.getElementById('blChartSection');
      if (empty) {
        empty.style.display='block';
        empty.innerHTML='<div class="muted">Loading chart data...</div>';
      }
      if (section) section.style.display='none';
    }
    ensureBuyMetaData(false)
      .then(() => { rerender(firstOpen); })
      .catch(() => { rerender(firstOpen); });
    return;
  }
  if(name==='managers'){
    TAB_INIT.managers = 1;
    _renderRefreshTs('managers');
    function _doMgrRender(){
      _mgrInitManagerDropdown();
      mgrSt.filtered=[...HOLDINGS]; mgrFilter();
    }
    const body=document.getElementById('mgrBody');
    const hasData=HOLDINGS.length>0;
    if(hasData){
      _doMgrRender();
    } else {
      if(body) body.innerHTML='<tr><td colspan="9" class="muted" style="text-align:center;padding:16px">Loading…</td></tr>';
      Promise.all([
        ensureHoldingsData(false).catch(()=>{}),
        ensureConvictionData(false).catch(()=>{})
      ]).then(()=>{
        if(document.getElementById('tab-managers')?.classList.contains('active')) _doMgrRender();
      }).catch(()=>{
        if(body) body.innerHTML='<tr><td colspan="9" class="muted" style="text-align:center;padding:16px">Click ↻ Refresh to load manager data.</td></tr>';
      });
    }
    // Load conviction in background if not already loaded
    if(!CONV.length) ensureConvictionData(false).then(()=>{ if(document.getElementById('tab-managers')?.classList.contains('active')) renderMgr(); }).catch(()=>{});
    return;
  }
  if(name==='zreturns'){
    if(TAB_INIT.zreturns) return;
    TAB_INIT.zreturns=1;
    _renderRefreshTs('zreturns');
    zrFilter();
    return;
  }
  if(name==='reversals'){
    TAB_INIT.reversals = 1;
    _renderRefreshTs('reversals');
    if (_hasReversalsData()) {
      rvFilter();
    } else {
      _renderReversalsLoading('Loading…');
      ensureReversalsData(false).then(()=>{
        if(document.getElementById('tab-reversals')?.classList.contains('active')) rvInit();
      }).catch(()=>{
        _renderReversalsLoading('Click ↻ Refresh to load reversals data.');
      });
    }
    return;
  }
  if(name==='holdings'){ switchTab('managers',btn); return; }
  if(name==='insider'){
    const firstOpen = !TAB_INIT.insider;
    TAB_INIT.insider = 1;
    _renderRefreshTs('insider');
    if (firstOpen) {
      initInsiderTitleFilter();
      iApplyLookbackFromMovedControl();
      iApplySortFromMovedControl();
    }
    // Load CONV for manager badges; re-render once it arrives if tab still active
    if(!CONV.length){
      ensureConvictionData(false).then(()=>{
        if(document.getElementById('tab-insider')?.classList.contains('active')) renderI();
      }).catch(()=>{});
    } else {
      ensureConvictionData(false).catch(()=>{});
    }
    if (INSIDERS.length) {
      iFilter();
    } else {
      _renderInsidersLoading('Loading…');
      ensureInsidersData(false).then(()=>{
        if(document.getElementById('tab-insider')?.classList.contains('active')) iFilter();
      }).catch(()=>{
        _renderInsidersLoading('Click ↻ Refresh to load insider trades.');
      });
    }
    return;
  }
  if(name==='themes'){
    TAB_INIT.themes = 1;
    if (THEMES_DATA.length > 0) {
      thFilter();
    } else {
      // Show a lightweight loading message and fetch from server cache (not a full refresh)
      _renderThemesLoading('Loading themes...');
      ensureThemesData(false, {background:false}).then(()=>{
        if(document.getElementById('tab-themes')?.classList.contains('active')) thFilter();
      }).catch(()=>{
        _renderThemesLoading('Click ↻ Refresh to load themes data.');
      });
    }
    return;
  }
  if(name==='heatmap'){
    if(!TAB_INIT.heatmap){
      TAB_INIT.heatmap=1;
      hmPopulateCats();
    }
    if (_hmView==='sp500') {
      if (!SP500_DATA.length) {
        _renderHeatmapLoading('Loading S&P 500 heatmap...');
        ensureSp500Data(false).then(()=>{
          if(document.getElementById('tab-heatmap')?.classList.contains('active')) renderHeatmap();
        }).catch(()=>{ _renderHeatmapLoading('Click ↻ Refresh to load S&P 500 heatmap.'); });
      } else {
        renderHeatmap();
      }
    } else {
      if (!THEMES_DATA.length) {
        _renderHeatmapLoading('Loading themes heatmap...');
        ensureThemesData(false, {background:false}).then(()=>{
          hmPopulateCats();
          if(document.getElementById('tab-heatmap')?.classList.contains('active')) renderHeatmap();
        }).catch(()=>{ _renderHeatmapLoading('Click ↻ Refresh to load themes heatmap.'); });
      } else {
        hmPopulateCats();
        renderHeatmap();
      }
    }
    return;
  }
  if(name==='bubble'){
    TAB_INIT.bubble=1;
    _renderRefreshTs('bubble');
    mountBubbleChartV2();
    if(CONV.length){
      updateBubbleChartDataset();
    } else {
      _bubbleShowOverlay('Loading…');
      Promise.all([
        ensureConvictionData(false).catch(()=>{}),
        ensureInsidersData(false).catch(()=>{}),
        ensureBubbleSizeData(false).catch(()=>{})
      ]).then(()=>{
        if(document.getElementById('tab-bubble')?.classList.contains('active')){
          if(CONV.length){ _bubbleHideOverlay(); updateBubbleChartDataset(); }
          else _bubbleShowOverlay('Click ↻ Refresh to load bubble chart data.');
        }
      });
    }
    return;
  }
  if(name==='rotation'){
    if(TAB_INIT.rotation) return;
    TAB_INIT.rotation=1;
    loadRotationFrame();
  }
}
function switchTab(name,btn){
  try{
    if(!_isTabAvailable(name)) name='buylevels';
    document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    const pane=document.getElementById('tab-'+name);
    if(!pane) throw new Error('Missing tab pane: '+name);
    pane.classList.add('active');
    if(btn)btn.classList.add('active');
    else document.querySelectorAll('.tab-btn').forEach(b=>{if(b.textContent.trim()&&b.getAttribute('onclick')&&b.getAttribute('onclick').includes("'"+name+"'"))b.classList.add('active');});
    if(name==='buylevels'){
      if(!_blLeftPanelUserClosed) document.body.classList.add('panel-open');
      blQueueImmediateLivePoll();
    } else {
      document.body.classList.remove('panel-open');
    }
    _saveCurrentTab(name);
    ensureTabReady(name);
  }catch(err){
    showJsError('switchTab('+name+') failed', err);
    console.error(err);
  }
}
function goChart(ticker){
  const q=String(ticker||'').trim().toUpperCase();
  if(!q) return;
  switchTab('buylevels',null);
  blOpenTicker(q);
  try{ renderWatchlist(); }catch(_e){}
}

function giBadge(score,tier){
  if(score===null||score===undefined) return '<span style="color:var(--muted)">-</span>';
  const col=GIC[tier]||'#7a8fa8';
  const pct=Math.min(100,Math.max(0,Math.round(score)));
  const r=parseInt(col.slice(1,3),16)||0;
  const g=parseInt(col.slice(3,5),16)||0;
  const b=parseInt(col.slice(5,7),16)||0;
  const fade=`rgba(${r},${g},${b},0.28)`;
  const glow=`rgba(${r},${g},${b},0.55)`;
  // inline-flex keeps the badge tight to its content; <td text-align:right floats it right
  return `<span style="display:inline-flex;align-items:center;gap:6px;vertical-align:middle">`
    +`<span style="color:${col};font-weight:700;font-family:var(--mono);font-size:13px;min-width:22px;text-align:right;letter-spacing:-.01em">${score.toFixed(0)}</span>`
    +`<span style="display:inline-block;width:56px;height:8px;background:rgba(255,255,255,.055);border-radius:4px;overflow:hidden;flex-shrink:0;box-shadow:inset 0 1px 3px rgba(0,0,0,.6)">`
      +`<span style="display:block;width:${pct}%;height:100%;background:linear-gradient(90deg,${fade} 0%,${col} 100%);border-radius:4px;box-shadow:0 1px 5px 0 ${glow}"></span>`
    +`</span>`
    +`</span>`;
}
function chgBadge(ct,pct){
  if(ct==='NEW')  return '<span class="badge b-new">NEW</span>';
  if(ct==='SOLD') return '<span class="badge b-sold">SOLD</span>';
  if(ct==='INCREASED'){const s=pct!=null?`^ ${pct>0?'+':''}${pct.toFixed(1)}%`:'^';return `<span class="badge b-inc">${s}</span>`;}
  if(ct==='DECREASED'){const s=pct!=null?`v ${pct.toFixed(1)}%`:'v';return `<span class="badge b-dec">${s}</span>`;}
  return '<span style="color:var(--muted);font-size:10px">-</span>';
}
function txBadge(r){
  if(r.is_buy) return `<span class="badge b-buy">${r.tx_label}</span>`;
  if(r.tx_type==='S'||r.tx_type==='S+') return `<span class="badge b-sell">${r.tx_label}</span>`;
  return `<span style="color:var(--muted)">${r.tx_label}</span>`;
}
function holdingsChgBadge(types){
  if(!Array.isArray(types)) return '<span style="color:var(--muted);font-size:10px">-</span>';
  const badges=types.filter(t=>t&&t.ct&&t.ct!=='UNCHANGED').map(t=>{
    const ct=t.ct, pct=t.pct;
    if(ct==='NEW')  return '<span class="badge b-new">NEW</span>';
    if(ct==='SOLD') return '<span class="badge b-sold">SOLD</span>';
    if(ct==='INCREASED'){const s=pct!=null?`&#9650; ${Math.abs(pct).toFixed(1)}%`:'&#9650;';return `<span class="badge b-inc">${s}</span>`;}
    if(ct==='DECREASED'){const s=pct!=null?`&#9660; ${Math.abs(pct).toFixed(1)}%`:'&#9660;';return `<span class="badge b-dec">${s}</span>`;}
    return '';
  }).filter(Boolean);
  return badges.length?'<span style="display:flex;gap:3px;flex-wrap:wrap">'+badges.join('')+'</span>':'<span style="color:var(--muted);font-size:10px">-</span>';
}
function escAttr(v){
  return String(v??'')
    .replace(/&/g,'&amp;')
    .replace(/"/g,'&quot;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/\n/g,'&#10;');
}
function escHtml(v){
  return String(v??'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}
function renderHoverTipHtml(raw,kind){
  if(kind==='heatmap'){
    let data=null;
    try{data=JSON.parse(String(raw||'{}'));}catch(_err){data=null;}
    if(!data||typeof data!=='object') return '';
    const ticker=String(data.ticker||'').trim()||'-';
    const name=String(data.name||'').trim();
    const giNum=Number(data.gi);
    const hasGi=Number.isFinite(giNum);
    const zoneKey=String(data.zoneKey||'').trim()||(hasGi?scoreToZone(giNum):'');
    const zoneLabel=String(data.zoneLabel||'').trim()||(zoneKey?(HM_ZONE_TIP_LABELS[zoneKey]||GISP_ZL[zoneKey]||zoneKey):'-');
    const zoneColor=zoneKey?(GISP_ZC[zoneKey]||'var(--text)'):'rgba(255,255,255,.62)';
    const giText=hasGi?giNum.toFixed(1):'-';
    const giColor=hasGi?giColorForValue(giNum):'rgba(255,255,255,.62)';
    const capNum=Number(data.marketCap);
    const capText=Number.isFinite(capNum)&&capNum>0?fmt_money_short_js(capNum):'-';
    const metricKey=String(data.metric||'').trim();
    const metricLabel=String(data.metricLabel||'').trim()||hmMetricLabel(metricKey||'r1d');
    const metricNum=Number(data.metricValue);
    const metricIsGi=(metricKey==='gi');
    const hasMetric=Number.isFinite(metricNum);
    const metricText=hasMetric?hmFmt(metricNum, metricIsGi?'gi':metricKey||'r1d'):'-';
    const metricColor=!hasMetric?'rgba(255,255,255,.62)':(metricIsGi?giColorForValue(metricNum):(metricNum>0?'#67e08e':metricNum<0?'#ff8d66':'#f3f4f6'));
    return `<div class="tip-heatmap">
      <div class="tip-hm-ticker">${escHtml(ticker)}</div>
      <div class="tip-hm-name">${escHtml(name||' ')}</div>
      <div class="tip-hm-grid">
        <div class="tip-hm-k">GI</div>
        <div class="tip-hm-k">Zone</div>
        <div class="tip-hm-k">Mkt Cap</div>
        <div class="tip-hm-k tip-hm-k-metric">${escHtml(metricLabel.replace('%','').trim())}</div>
        <div class="tip-hm-v" style="color:${giColor}">${escHtml(giText)}</div>
        <div class="tip-hm-v" style="color:${zoneColor}">${escHtml(zoneLabel)}</div>
        <div class="tip-hm-v${capText==='-'?' muted':''}">${escHtml(capText)}</div>
        <div class="tip-hm-v tip-hm-v-metric" style="color:${metricColor}">${escHtml(metricText)}</div>
      </div>
    </div>`;
  }
  const lines=String(raw||'').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
  if(!lines.length) return '';
  function parts(line){return line.split(/\s{2,}/).map(s=>s.trim()).filter(Boolean);}
  function plain(line){
    const mgr=managerColorIfKnown(line);
    const ins=insiderColorIfKnown(line);
    const known=mgr||ins;
    if(known) return `<div class="tip-line"><span class="tip-name" style="color:${known}">${escHtml(line)}</span></div>`;
    return `<div class="tip-line"><span class="tip-meta">${escHtml(line)}</span></div>`;
  }
  const isMgrKind=kind==='mgr'||kind==='new'||kind==='inc'||kind==='dec'||kind==='mgrdet';
  const isInsKind=kind==='ins';
  const isRichKind=isMgrKind||isInsKind;
  if(!kind) return lines.map(plain).join('');
  // Rich kinds (new/inc/dec/ins/mgr): lines formatted as "Name  |  Value  |  Pct  |  Date"
  if(isRichKind){
    return lines.map(line=>{
      const segs=line.split(/\s*\|\s*/).map(s=>s.trim()).filter(Boolean);
      if(!segs.length) return plain(line);
      const name=segs[0];
      const rest=segs.slice(1);
      const nColor=isInsKind?insiderColor(name):managerColor(name);
      let html=`<div class="tip-line">`;
      if(nColor) html+=`<span class="tip-name" style="color:${nColor}">${escHtml(name)}</span>`;
      else       html+=`<span class="tip-name">${escHtml(name)}</span>`;
      rest.forEach(seg=>{
        // Detect date (YYYY-MM-DD or like "Jan '25")
        const isDate=/^\d{4}-\d{2}-\d{2}$/.test(seg)||/^[A-Za-z]{3}\s+'?\d{2,4}$/.test(seg);
        // Detect money ($... or ends with K/M/B)
        const isMoney=/^\$|[KMB]$/.test(seg);
        // Detect pct change
        const isPct=/^[+\-]?\d+(\.\d+)?%$/.test(seg);
        if(isDate)        html+=` <span class="tip-date">${escHtml(fmtDateShort(seg)||seg)}</span>`;
        else if(isMoney)  html+=` <span style="color:#86efac">${escHtml(seg)}</span>`;
        else if(isPct)    html+=` <span class="tip-metric">${escHtml(seg)}</span>`;
        else              html+=` <span class="tip-meta">${escHtml(seg)}</span>`;
      });
      html+='</div>';
      return html;
    }).join('');
  }
  return lines.map(line=>{
    const p=parts(line);
    if(!p.length) return plain(line);
    const date=fmtDateShort(p[0]||'');
    const metric=p[1]||'';
    const name=p[2]||'';
    const tail=p.slice(3).join('  ');
    let html=`<div class="tip-line"><span class="tip-date">${escHtml(date)}</span>`;
    if(metric)html+=`  <span class="tip-metric">${escHtml(metric)}</span>`;
    if(name){
      html+=`  <span class="tip-name">${escHtml(name)}</span>`;
    }
    if(tail){
      const segs=tail.split('|').map(s=>s.trim()).filter(Boolean);
      const tailTxt=segs.length?segs.join(' | '):tail;
      let rich=escHtml(tailTxt)
        .replace(/(\d+(?:\.\d+)?% of portfolio)/g,'<span style="color:#c084fc">$1</span>')
        .replace(/([+\-]?[\d,.]+(?:K|M|B)? shares)/g,'<span style="color:#93c5fd">$1</span>');
      html+=`  <span class="tip-meta">${rich}</span>`;
    }
    html+='</div>';
    return html;
  }).join('');
}
function hoverCount(v,color,tip,kind=''){
  const count=v||0;
  if(!tip) return `<span style="color:${color}">${count}</span>`;
  const k=kind?` data-tip-kind="${kind}"`:'';
  return `<span class="hover-stat" data-tip="${escAttr(tip)}"${k} style="color:${color}">${count}</span>`;
}
function managerRowTip(r){
  const dt=r&&r.report_date?fmtDateShort(r.report_date):'';
  const val=r&&r.value_fmt?String(r.value_fmt):'n/a';
  const name=r&&r.manager?String(r.manager):'';
  const src=r&&r.source?String(r.source):'';
  const ct=r&&r.change_type?String(r.change_type):'';
  const noChgPct=!ct||ct==='NEW'||ct==='SOLD'||ct==='UNKNOWN';
  const cp=noChgPct?null:(r&&r.share_chg_pct!=null&&Number.isFinite(Number(r.share_chg_pct)))
    ?`${Number(r.share_chg_pct)>0?'+':''}${Number(r.share_chg_pct).toFixed(1)}%`:null;
  const chgStr=ct?(cp?`${ct} ${cp}`:ct):'';
  const trail=[src,chgStr,(r&&r.pct!=null&&Number.isFinite(Number(r.pct)))?`${Number(r.pct).toFixed(2)}% portfolio`:'' ].filter(Boolean).join(' | ');
  return `${dt||'n/a'}  ${val}  ${name||'n/a'}${trail?'  '+trail:''}`;
}
function managerCell(r){
  const name=String((r&&r.manager)||'').trim();
  if(!name) return '<span class="muted">-</span>';
  const clr=managerColor(name);
  const tip=managerRowTip(r);
  return `<span class="hover-stat" data-tip="${escAttr(tip)}" data-tip-kind="mgrdet" style="color:${clr};font-weight:600">${escHtml(name)}</span>`;
}
function tickerLinkCell(ticker, row=null){
  const txt=String(ticker||'').trim();
  if(!txt||txt==='-') return '<span class="muted">-</span>';
  const exRaw=row&&typeof row==='object'
    ? (row.exchange ?? row.exch ?? row.market ?? row.market_exchange ?? '')
    : '';
  const ex=String(exRaw||'').trim();
  const exAttr=ex?` data-exchange="${escAttr(ex)}"`:'';
  return `<button type="button" class="sym-link" data-ticker="${escAttr(txt)}"${exAttr}><span class="sym-link-text" onclick="event.stopPropagation();goChart(this.closest('.sym-link').dataset.ticker)">${escHtml(txt)}</span></button>`;
}

// -- Generic table state --
const hoverTipEl=document.createElement('div');
hoverTipEl.className='hover-tip';
document.body.appendChild(hoverTipEl);
let activeTipTarget=null,_hideTipTimer=null;
function hideHoverTip(){
  clearTimeout(_hideTipTimer);
  activeTipTarget=null;
  hoverTipEl.classList.remove('show');
  hoverTipEl.removeAttribute('data-kind');
}
function scheduleHide(delay){
  clearTimeout(_hideTipTimer);
  _hideTipTimer=setTimeout(hideHoverTip,delay||80);
}
function cancelHide(){clearTimeout(_hideTipTimer);}
function moveHoverTip(e){
  if(!hoverTipEl.classList.contains('show')) return;
  const pad=12;
  const rect=hoverTipEl.getBoundingClientRect();
  let x=e.clientX+18;
  let y=e.clientY+18;
  if(x+rect.width>window.innerWidth-pad) x=window.innerWidth-rect.width-pad;
  if(y+rect.height>window.innerHeight-pad) y=Math.max(pad,e.clientY-rect.height-18);
  hoverTipEl.style.left=`${x}px`;
  hoverTipEl.style.top=`${y}px`;
}
hoverTipEl.addEventListener('mouseenter',cancelHide);
hoverTipEl.addEventListener('mouseleave',()=>scheduleHide(80));
// Hide immediately when mouse leaves a [data-tip] element
document.addEventListener('mouseout',e=>{
  const el=e.target&&e.target.closest?e.target.closest('[data-tip]'):null;
  if(!el) return;
  const to=e.relatedTarget;
  if(to&&el.contains(to)) return;           // moved into a child — still inside
  if(to&&(hoverTipEl===to||hoverTipEl.contains(to))) return; // moved onto tooltip
  hideHoverTip();
});
document.addEventListener('mousemove',e=>{
  const onTip=hoverTipEl===e.target||hoverTipEl.contains(e.target);
  if(onTip){cancelHide();return;}
  const el=e.target&&e.target.closest?e.target.closest('[data-tip]'):null;
  if(!el){
    if(activeTipTarget) hideHoverTip();
    return;
  }
  cancelHide();
  if(el!==activeTipTarget){
    activeTipTarget=el;
    const raw=el.getAttribute('data-tip')||'';
    const kind=el.getAttribute('data-tip-kind')||'';
    if(kind) hoverTipEl.setAttribute('data-kind',kind);
    else hoverTipEl.removeAttribute('data-kind');
    hoverTipEl.innerHTML=renderHoverTipHtml(raw,kind);
    hoverTipEl.classList.add('show');
  }
  moveHoverTip(e);
});
document.addEventListener('scroll',e=>{
  if(hoverTipEl.contains(e.target)||e.target===hoverTipEl) return;
  hideHoverTip();
},true);

// TradingView mini chart on symbol hover (ported from ape_wisdom behavior)
const symChartTipEl=document.createElement('div');
symChartTipEl.className='sym-chart-popup';
document.body.appendChild(symChartTipEl);
let _symChartHideTimer=null,_symChartLoadTimer=null,_symChartTicker='',_symChartAnchor=null,_symChartMouseEvt=null;
function _symChartCancelHide(){ clearTimeout(_symChartHideTimer); _symChartHideTimer=null; }
function _symChartScheduleHide(){ hideSymbolMiniChart(); }
function getFinalSymbol(symbol, yfExchange){
  const ex=String(yfExchange||'').toUpperCase();
  const s=String(symbol||'').toUpperCase().replace('-', '.');
  const manualOverrides={
    'SPY':'AMEX:SPY','VOO':'AMEX:VOO','IVV':'AMEX:IVV',
    'TQQQ':'NASDAQ:TQQQ','SQQQ':'NASDAQ:SQQQ','VPN':'NASDAQ:VPN',
    'AM':'NYSE:AM','DIA':'AMEX:DIA','IWM':'AMEX:IWM','DTE':'NYSE:DTE'
  };
  if(manualOverrides[s]) return manualOverrides[s];
  if(ex.includes('NMS')||ex.includes('NGM')||ex.includes('NCM')||ex.includes('NASDAQ')) return 'NASDAQ:'+s;
  if(ex.includes('NYQ')||ex.includes('NYSE')) return 'NYSE:'+s;
  if(ex.includes('ASE')||ex.includes('AMEX')||ex.includes('PCX')||ex.includes('ARCA')) return 'AMEX:'+s;
  if(ex.includes('BATS')||ex.includes('BZX')) return 'BATS:'+s;
  if(ex.includes('LSE')) return 'LSE:'+s;
  return s;
}
function _symChartPosition(container, evt){
  const e=evt||_symChartMouseEvt;
  if(!e) return;
  const screenPadding=12;
  const mouseX=Number(e.clientX)||0;
  const mouseY=Number(e.clientY)||0;
  const rect=container.getBoundingClientRect();
  const screenW=window.innerWidth||1200;
  const screenH=window.innerHeight||800;
  let leftPos=mouseX+16;
  let topPos=Math.max(screenPadding,Math.min(mouseY+16,screenH-rect.height-screenPadding));
  if(leftPos+rect.width>screenW-screenPadding) leftPos=Math.max(screenPadding,mouseX-rect.width-16);
  if(leftPos<screenPadding) leftPos=screenPadding;
  if(leftPos+rect.width>screenW-screenPadding) leftPos=screenW-rect.width-screenPadding;
  container.style.left=leftPos+'px';
  container.style.top=topPos+'px';
}
function hideSymbolMiniChart(){
  _symChartCancelHide();
  clearTimeout(_symChartLoadTimer);
  _symChartLoadTimer=null;
  _symChartTicker='';
  _symChartAnchor=null;
  symChartTipEl.classList.remove('show','large-chart');
  symChartTipEl.innerHTML='';
}
function loadMiniChart(symbol, yfExchange, event){
  if(!symbol) return;
  _symChartMouseEvt=event||_symChartMouseEvt;
  _symChartCancelHide();
  if(_symChartTicker===symbol && symChartTipEl.classList.contains('show')){
    _symChartPosition(symChartTipEl, event||_symChartMouseEvt);
    return;
  }
  _symChartTicker=symbol;
  symChartTipEl.innerHTML='';
  symChartTipEl.style.width='';
  symChartTipEl.classList.add('large-chart');
  const mouseX=((event||_symChartMouseEvt)||{}).clientX||0;
  const screenW=window.innerWidth||1200;
  const spaceOnRight=screenW-mouseX-40;
  const idealWidth=screenW*0.85;
  const minWidth=620;
  if(idealWidth>spaceOnRight && spaceOnRight>minWidth) symChartTipEl.style.width=spaceOnRight+'px';
  _symChartPosition(symChartTipEl, event||_symChartMouseEvt);
  const finalSymbol=getFinalSymbol(symbol, yfExchange||'');
  const widgetContainer=document.createElement('div');
  widgetContainer.className='tradingview-widget-container';
  const widgetDiv=document.createElement('div');
  widgetDiv.className='tradingview-widget-container__widget';
  widgetContainer.appendChild(widgetDiv);
  const script=document.createElement('script');
  script.type='text/javascript';
  script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
  script.async=true;
  script.innerHTML=JSON.stringify({
    autosize:true,symbol:finalSymbol,interval:'D',timezone:'Etc/UTC',theme:'dark',style:'1',
    locale:'en',enable_publishing:false,allow_symbol_change:true,calendar:false,details:true,
    hotlist:false,hide_side_toolbar:true,hide_top_toolbar:true,hide_legend:false,hide_volume:false,
    withdateranges:true,range:'12M',save_image:false,backgroundColor:'#0F0F0F',
    gridColor:'rgba(242, 242, 242, 0.06)',watchlist:[],compareSymbols:[],studies:[]
  });
  widgetContainer.appendChild(script);
  symChartTipEl.appendChild(widgetContainer);
  symChartTipEl.classList.add('show');
  _symChartPosition(symChartTipEl, event||_symChartMouseEvt);
}
document.addEventListener('mouseover',e=>{
  // Only trigger when mouse is directly over the ticker text span, not the cell padding
  if(!e.target||!e.target.classList||!e.target.classList.contains('sym-link-text')) return;
  const el=e.target.closest('.sym-link[data-ticker]');
  if(!el) return;
  _symChartCancelHide();
  const sym=String(el.dataset.ticker||'').trim().toUpperCase();
  const ex=String(el.dataset.exchange||'').trim();
  if(!sym) return;
  _symChartAnchor=el;
  _symChartMouseEvt=e;
  clearTimeout(_symChartLoadTimer);
  _symChartLoadTimer=setTimeout(()=>loadMiniChart(sym,ex,_symChartMouseEvt),120);
});
document.addEventListener('mouseout',e=>{
  // Only hide when mouse leaves the ticker text span itself
  if(!e.target||!e.target.classList||!e.target.classList.contains('sym-link-text')) return;
  const el=e.target.closest('.sym-link[data-ticker]');
  if(!el) return;
  const to=e.relatedTarget;
  if(to && symChartTipEl.contains(to)) return;
  _symChartScheduleHide();
});
document.addEventListener('mousemove',e=>{
  _symChartMouseEvt=e;
  if(symChartTipEl.classList.contains('show')) _symChartPosition(symChartTipEl,e);
});
document.addEventListener('scroll',()=>{ if(symChartTipEl.classList.contains('show')) hideSymbolMiniChart(); },true);

// Heatmap cell TradingView mini chart popup
const hmMiniPopEl=document.createElement('div');
hmMiniPopEl.className='hm-mini-popup';
document.body.appendChild(hmMiniPopEl);
let _hmMiniTicker='';
function _hmMiniPosition(e){
  const pad=12;
  const mX=Number(e.clientX)||0, mY=Number(e.clientY)||0;
  const w=hmMiniPopEl.offsetWidth||380, h=hmMiniPopEl.offsetHeight||220;
  const sW=window.innerWidth||1200, sH=window.innerHeight||800;
  let left=mX+16, top=mY+16;
  if(left+w>sW-pad) left=mX-w-16;
  if(top+h>sH-pad) top=mY-h-16;
  left=Math.max(pad,left); top=Math.max(pad,top);
  hmMiniPopEl.style.left=left+'px';
  hmMiniPopEl.style.top=top+'px';
}
function showHmMiniChart(ticker,exchange,e){
  const sym=getFinalSymbol(ticker,exchange||'');
  if(_hmMiniTicker===sym && hmMiniPopEl.classList.contains('show')){
    _hmMiniPosition(e); return;
  }
  _hmMiniTicker=sym;
  hmMiniPopEl.innerHTML='';
  const mc=document.createElement('tv-mini-chart');
  mc.setAttribute('symbol',sym);
  mc.setAttribute('time-frame','7D');
  mc.setAttribute('line-chart-type','Baseline');
  mc.setAttribute('show-time-scale','');
  mc.setAttribute('theme','dark');
  /* Make the widget taller than the container so overflow:hidden clips the
     "price by TradingView" footer (≈28px) at the bottom of the iframe. */
  mc.style.cssText='width:100%;height:252px;display:block;margin-top:-2px;';
  hmMiniPopEl.appendChild(mc);
  hmMiniPopEl.classList.add('show');
  _hmMiniPosition(e);
}
function hideHmMiniChart(){
  _hmMiniTicker='';
  hmMiniPopEl.classList.remove('show');
  hmMiniPopEl.innerHTML='';
}
document.addEventListener('mouseover',e=>{
  const el=e.target&&e.target.closest?e.target.closest('.hm-cell[data-ticker],.hm-sp-cell[data-ticker]'):null;
  if(!el) return;
  const ticker=String(el.dataset.ticker||'').trim().toUpperCase();
  if(!ticker) return;
  showHmMiniChart(ticker,'',e);
});
document.addEventListener('mouseout',e=>{
  const el=e.target&&e.target.closest?e.target.closest('.hm-cell[data-ticker],.hm-sp-cell[data-ticker]'):null;
  if(!el) return;
  const to=e.relatedTarget;
  if(to&&to.closest&&to.closest('.hm-cell[data-ticker],.hm-sp-cell[data-ticker]')) return;
  hideHmMiniChart();
});
document.addEventListener('mousemove',e=>{
  if(hmMiniPopEl.classList.contains('show')){
    const el=e.target&&e.target.closest?e.target.closest('.hm-cell[data-ticker],.hm-sp-cell[data-ticker]'):null;
    if(el) _hmMiniPosition(e);
  }
});
document.addEventListener('scroll',()=>{ if(hmMiniPopEl.classList.contains('show')) hideHmMiniChart(); },true);
function mkState(data,sc,sd){return{all:data,filtered:[...data],sc:sc||'rank',sd:sd||1,pg:1,ps:100};}
const TABLE_SORT_KEY='gekko_table_sort_v1';
let _tableSortSaveTimer=null;
// Registered sort-state slots: {key, stFn} — stFn returns the live state object.
const _tableSortSlots=[];
function _regSortSlot(key,stFn){ _tableSortSlots.push({key,stFn}); }
function _saveTableSorts(){
  if(_tableSortSaveTimer) clearTimeout(_tableSortSaveTimer);
  _tableSortSaveTimer=setTimeout(()=>{
    _tableSortSaveTimer=null;
    try{
      const out={};
      _tableSortSlots.forEach(({key,stFn})=>{
        try{const st=stFn();if(st)out[key]={sc:st.sc,sd:st.sd,ps:st.ps};}catch(_e){}
      });
      localStorage.setItem(TABLE_SORT_KEY,JSON.stringify(out));
    }catch(_e){}
  },400);
}
function _restoreTableSorts(){
  try{
    const raw=localStorage.getItem(TABLE_SORT_KEY);
    if(!raw) return;
    const saved=JSON.parse(raw);
    _tableSortSlots.forEach(({key,stFn})=>{
      const s=saved[key];
      if(!s) return;
      try{
        const st=stFn();
        if(!st) return;
        if(s.sc) st.sc=s.sc;
        if(typeof s.sd==='number') st.sd=s.sd;
        if(typeof s.ps==='number'&&s.ps>0) st.ps=s.ps;
      }catch(_e){}
    });
  }catch(_e){}
}
function doSort(st){
  const c=st.sc,d=st.sd;
  st.filtered.sort((a,b)=>{
    let av=a[c],bv=b[c];
    if(av==null) av=d===1?Infinity:-Infinity;
    if(bv==null) bv=d===1?Infinity:-Infinity;
    return typeof av==='string'?av.localeCompare(bv)*d:(av-bv)*d;
  });
  _saveTableSorts(); // persist sort state on every change
}
function syncSortSelect(selectId,col){
  const sel=document.getElementById(selectId);
  if(!sel) return;
  const has=Array.from(sel.options||[]).some(o=>o.value===col);
  if(has) sel.value=col;
}
// Global Enter-key commit: pressing Enter in any ctrl-input fires change + blurs the field
document.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const el = e.target;
  if (!el || !el.classList.contains('ctrl-input')) return;
  e.preventDefault();
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.blur();
}, true);

function initNumberSteppers(){
  const fitInputWidth=inp=>{
    if(!inp) return;
    const layout=String(inp.dataset.stepperLayout||'').toLowerCase();
    if(layout==='vsplit'){
      inp.style.minWidth='0';
      inp.style.width='100%';
      return;
    }
    const baseWidth=String(inp.dataset.baseWidth||inp.style.width||'').trim();
    if(baseWidth) inp.dataset.baseWidth=baseWidth;
    const samples=[inp.value,inp.placeholder,inp.min,inp.max]
      .map(v=>String(v??'').trim())
      .filter(Boolean);
    let chars=3;
    samples.forEach(v=>{chars=Math.max(chars,v.length);});
    const minCh=parseInt(inp.dataset.minCh||'',10);
    if(Number.isFinite(minCh) && minCh>0) chars=Math.max(chars,minCh);
    const stepStr=String(inp.step||'').trim();
    if(stepStr.includes('.')){
      const dp=(stepStr.split('.')[1]||'').length;
      const base=(String(inp.value||inp.min||'0').split('.')[0]||'').length;
      chars=Math.max(chars,base+dp+1);
    }
    chars=Math.min(8,chars);
    const autoWidth=`calc(${chars}ch + 8px)`;
    if(baseWidth){
      inp.style.minWidth=baseWidth;
      inp.style.width=`max(${baseWidth}, ${autoWidth})`;
    }else{
      inp.style.width=autoWidth;
    }
  };
  document.querySelectorAll('.ctrl-input[type="number"]').forEach(inp=>{
    if(inp.dataset.stepperInit==='1') return;
    inp.dataset.stepperInit='1';
    const parent=inp.parentNode;
    if(!parent) return;
    const layout=String(inp.dataset.stepperLayout||'').toLowerCase();
    const wrap=document.createElement('span');
    wrap.className='num-stepper'+(layout==='vsplit'?' vsplit':'');
    const dec=document.createElement('button');
    dec.type='button';
    dec.className='num-step-btn step-dec';
    dec.textContent='-';
    dec.title='Decrease';
    const inc=document.createElement('button');
    inc.type='button';
    inc.className='num-step-btn step-inc';
    inc.textContent='+';
    inc.title='Increase';
    parent.insertBefore(wrap,inp);
    if(layout==='vsplit'){
      const stack=document.createElement('span');
      stack.className='num-stepper-stack';
      wrap.appendChild(inp);
      wrap.appendChild(stack);
      stack.appendChild(inc);
      stack.appendChild(dec);
    }else{
      wrap.appendChild(dec);
      wrap.appendChild(inp);
      wrap.appendChild(inc);
    }
    const asNum=v=>{
      const n=parseFloat(v);
      return Number.isFinite(n)?n:null;
    };
    const stepBy=delta=>{
      const step=asNum(inp.step)||1;
      const min=asNum(inp.min);
      const max=asNum(inp.max);
      let cur=asNum(inp.value);
      if(cur===null){
        // If field is empty and has an auto-seed function, start from the computed auto price
        const seedFn=inp.dataset.autoSeed&&window[inp.dataset.autoSeed];
        const seed=typeof seedFn==='function'?seedFn():null;
        cur=(seed!==null&&Number.isFinite(seed))?seed:(min!==null?min:0);
      }
      let next=cur+delta*step;
      if(min!==null&&next<min) next=min;
      if(max!==null&&next>max) next=max;
      const dp=(String(step).split('.')[1]||'').length;
      inp.value=dp>0?next.toFixed(dp):String(Math.round(next));
      inp.dispatchEvent(new Event('input',{bubbles:true}));
      inp.dispatchEvent(new Event('change',{bubbles:true}));
    };
    // Click-and-hold: first step immediately, then repeat after 400ms, then every 80ms
    let _stepTimer=null;
    const _startRepeat=(delta)=>{
      stepBy(delta);
      _stepTimer=setTimeout(()=>{
        _stepTimer=setInterval(()=>stepBy(delta),80);
      },400);
    };
    const _stopRepeat=()=>{
      if(_stepTimer!==null){clearTimeout(_stepTimer);clearInterval(_stepTimer);_stepTimer=null;}
    };
    const _bindHold=(btn,delta)=>{
      btn.addEventListener('mousedown',e=>{if(e.button!==0) return;e.preventDefault();_startRepeat(delta);});
      btn.addEventListener('mouseup',_stopRepeat);
      btn.addEventListener('mouseleave',_stopRepeat);
      // still handle plain keyboard activation (Enter/Space) via click
      btn.addEventListener('click',e=>{e.preventDefault();});
    };
    _bindHold(dec,-1);
    _bindHold(inc,1);
    inp.addEventListener('input',()=>fitInputWidth(inp));
    fitInputWidth(inp);
  });
}
function mkPag(st,pgId,renderFn){
  const tot=Math.ceil(st.filtered.length/st.ps);
  const el=document.getElementById(pgId);
  if(tot<=1){el.innerHTML='';return;}
  const p=st.pg;
  let b=`<button onclick="${renderFn}Page(1)" ${p===1?'disabled':''}><<</button>
         <button onclick="${renderFn}Page(${p-1})" ${p===1?'disabled':''}><</button>`;
  for(let i=Math.max(1,p-2);i<=Math.min(tot,p+2);i++)
    b+=`<button onclick="${renderFn}Page(${i})" ${i===p?'style="border-color:var(--green);color:var(--green)"':''}>${i}</button>`;
  b+=`<button onclick="${renderFn}Page(${p+1})" ${p===tot?'disabled':''}>></button>
      <button onclick="${renderFn}Page(${tot})" ${p===tot?'disabled':''}>>></button>
      <span class="page-info">Page ${p} / ${tot}</span>`;
  el.innerHTML=b;
}
function goPage(st,p,renderFn){
  const tot=Math.ceil(st.filtered.length/st.ps);
  st.pg=Math.max(1,Math.min(tot,p));
  renderFn(); window.scrollTo(0,0);
}

// -- TAB 1: CONVICTION --
// -- TAB 1: MANAGERS (merged Conviction + Holdings) --
const mgrSt=Object.assign(mkState(HOLDINGS,'value',-1),{ps:25});
_regSortSlot('managers',()=>mgrSt);
let mgrGroups=[];

function _mgrInitManagerDropdown(){
  const sel=document.getElementById('mgrMgr');
  if(!sel) return;
  const existing=new Set(Array.from(sel.options).map(o=>o.value).filter(Boolean));
  const names=[...new Set(HOLDINGS.map(r=>r.manager).filter(Boolean))].sort();
  names.forEach(n=>{ if(!existing.has(n)){ const o=document.createElement('option'); o.value=n; o.textContent=n; sel.appendChild(o); }});
}

function mgrFilter(){
  const q=document.getElementById('mgrS').value.trim().toLowerCase();
  const mgr=document.getElementById('mgrMgr').value;
  const ch=document.getElementById('mgrCh').value;
  const gi=document.getElementById('mgrGI').value;
  const mm=parseInt(document.getElementById('mgrMM').value)||1;
  const minIns=parseInt(document.getElementById('mgrMinIns')?.value)||0;
  const ibDays=parseInt(document.getElementById('mgrIBPeriod')?.value)||0;
  const ibCutoffMs=ibDays>0?(Date.now()-ibDays*86400000):0;
  mgrSt.filtered=HOLDINGS.filter(r=>{
    if(mgr&&r.manager!==mgr) return false;
    if(q&&!r.ticker.toLowerCase().includes(q)&&!(r.company||'').toLowerCase().includes(q)) return false;
    if(ch&&r.change_type!==ch) return false;
    if(gi&&r.gi_tier!==gi) return false;
    return true;
  });
  doSort(mgrSt); mgrSt.pg=1;
  // After filtering individuals, re-group and apply group-level filters
  const wasOpen={};
  mgrGroups.forEach(g=>{if(g._open)wasOpen[g.ticker]=true;});
  mgrGroups=groupHoldings(mgrSt.filtered);
  mgrGroups.forEach(g=>{if(wasOpen[g.ticker])g._open=true;});
  // Build conviction lookup for enrichment
  const convMap={};
  CONV.forEach(c=>{if(c.ticker) convMap[c.ticker]=c;});
  // Apply group-level filters (min managers, min insiders, buy period) using live BUY_META + CONV
  mgrGroups=mgrGroups.filter(g=>{
    if(g.managerCount<mm) return false;
    // Insider filters: use countDistinctInsiderBuys (deduped by insider key)
    if(minIns>0||ibCutoffMs>0){
      const distinctIns=countDistinctInsiderBuys(g.ticker, ibCutoffMs);
      const fallbackIns=(()=>{
        if(distinctIns>0) return distinctIns;
        // Fallback to CONV count if BUY_META not loaded yet
        const cv=convMap[g.ticker];
        return (cv&&cv.insider_buys>0)?cv.insider_buys:0;
      })();
      if(minIns>0&&fallbackIns<minIns) return false;
      if(minIns===0&&ibCutoffMs>0&&distinctIns<1) return false;
    }
    return true;
  });
  sortHoldingGroups(mgrGroups);
  renderMgr();
}

function mgrSort(col){
  if(mgrSt.sc===col) mgrSt.sd*=-1; else{mgrSt.sc=col;mgrSt.sd=col==='rank'?1:-1;}
  document.querySelectorAll('#tab-managers thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add(mgrSt.sd===1?'sort-asc':'sort-desc');});
  mgrGroups.sort((a,b)=>{
    const av=a[col]??a.totalVal; const bv=b[col]??b.totalVal;
    const an=Number(av),bn=Number(bv);
    if(Number.isFinite(an)&&Number.isFinite(bn)&&an!==bn) return (an-bn)*mgrSt.sd;
    return String(a.ticker||'').localeCompare(String(b.ticker||''));
  });
  mgrSt.pg=1; renderMgr();
}

function mgrPSChange(){mgrSt.ps=parseInt(document.getElementById('mgrPS')?.value)||25;mgrSt.pg=1;renderMgr();}
function renderMgrPage(p){mgrSt.pg=p;renderMgr();}

function toggleMgrGroup(idx){
  const g=mgrGroups[Math.floor(idx)];
  if(g) g._open=!g._open;
  renderMgr();
}

function _mgrRichTip(rows, types){
  const filtered=rows.filter(r=>types.includes((r.change_type||'').toUpperCase()));
  if(!filtered.length) return '';
  return filtered.map(r=>{
    const name=r.manager||'?';
    const val=r.value_fmt||'n/a';
    const dt=r.report_date?fmtDateShort(r.report_date):'';
    const ct=(r.change_type||'').toUpperCase();
    const noChgPct=ct==='NEW'||ct==='SOLD'||ct==='UNKNOWN';
    const pct=(r.share_chg_pct!=null&&Number.isFinite(Number(r.share_chg_pct))&&!noChgPct)
      ?`${Number(r.share_chg_pct)>0?'+':''}${Number(r.share_chg_pct).toFixed(1)}%`:'';
    const parts=[name,val,pct,dt].filter(Boolean);
    return parts.join('  |  ');
  }).join('\n');
}

function renderMgr(){
  const s=mgrSt;
  const convMap={};
  CONV.forEach(c=>{if(c.ticker) convMap[c.ticker]=c;});
  const start=(s.pg-1)*s.ps, page=mgrGroups.slice(start,start+s.ps);
  let html='';
  page.forEach((g,idx)=>{
    const gi=start+idx;
    const cv=convMap[g.ticker]||{};
    const rows=g._rows||[];
    const newRows=rows.filter(r=>r.change_type==='NEW');
    const incRows=rows.filter(r=>r.change_type==='INCREASED');
    const decRows=rows.filter(r=>r.change_type==='DECREASED');
    const newCount=newRows.length||cv.new_count||0;
    const incCount=incRows.length||cv.inc_count||0;
    const decCount=decRows.length;
    const newTip=_mgrRichTip(newRows,['NEW'])||cv.new_detail||'';
    const incTip=_mgrRichTip(incRows,['INCREASED'])||cv.inc_detail||'';
    const decTip=_mgrRichTip(decRows,['DECREASED']);
    // Build insider tooltip from live BUY_META (has dates + values), fall back to CONV
    const ibDaysRender=parseInt(document.getElementById('mgrIBPeriod')?.value)||0;
    const ibCutoffRender=ibDaysRender>0?(Date.now()-ibDaysRender*86400000):0;
    const rawBuys=(BUY_META[g.ticker]||[]).filter(b=>{
      if(!b.insider) return false;
      if(ibCutoffRender>0){const ts=new Date(blBuyTradeDate(b)).getTime();if(!Number.isFinite(ts)||ts<ibCutoffRender) return false;}
      return true;
    });
    // Deduplicate by insider name — keep the most recent transaction per insider
    const insiderMap=new Map();
    rawBuys.forEach(b=>{
      const key=(b.insider||'').trim().toLowerCase();
      if(!key) return;
      const existing=insiderMap.get(key);
      if(!existing){insiderMap.set(key,b);return;}
      const tsNew=new Date(blBuyTradeDate(b)||blBuyFiledDate(b)||'').getTime()||0;
      const tsOld=new Date(blBuyTradeDate(existing)||blBuyFiledDate(existing)||'').getTime()||0;
      if(tsNew>tsOld) insiderMap.set(key,b);
    });
    const dedupedBuys=Array.from(insiderMap.values());
    const insiderBuysCount=dedupedBuys.length||countDistinctInsiderBuys(g.ticker,ibCutoffRender)||cv.insider_buys||0;
    const insTip=dedupedBuys.length
      ? dedupedBuys.map(b=>{
          const name=b.insider||'?';
          const val=b.value_fmt||(b.value!=null?'$'+Number(b.value).toLocaleString():'');
          const dt=fmtDateShort(blBuyTradeDate(b)||blBuyFiledDate(b)||'');
          return [name,val,dt].filter(Boolean).join('  |  ');
        }).join('\n')
      : (cv.insider_detail||'');
    html+=`<tr class="grp-hdr${g._open?' open':''}" onclick="toggleMgrGroup(${gi})">
      <td class="sym-cell">${tickerLinkCell(g.ticker,g)}</td>
      <td class="muted" style="max-width:160px;overflow:hidden;text-overflow:ellipsis" title="${g.company||''}">${g.company||'-'}</td>
      <td style="color:var(--green)">${g.value_fmt}</td>
      <td>${hoverCount(g.managerCount,'var(--green)',g.mgrTip||g.mgrs,'mgr')}</td>
      <td style="text-align:center">${giBadge(g.gi_score,g.gi_tier)}</td>
      <td>${newCount>0?hoverCount(newCount,'#86efac',newTip,'new'):'-'}</td>
      <td>${incCount>0?hoverCount(incCount,'#60a5fa',incTip,'inc'):'-'}</td>
      <td>${decCount>0?hoverCount(decCount,'#f87171',decTip,'dec'):'-'}</td>
      <td>${insiderBuysCount>0?hoverCount(insiderBuysCount,'#fbbf24',insTip,'ins'):'-'}</td>
    </tr>`;
    if(g._open){
      g._rows.forEach(r=>{
        html+=`<tr class="grp-child">
          <td class="muted" style="font-size:10px;padding-left:14px" colspan="2">${managerCell(r)}</td>
          <td style="color:var(--green)">${r.value_fmt}</td>
          <td class="muted">${r.pct!=null?r.pct.toFixed(2)+'%<div class="pct-bar"><div class="pct-bar-fill" style="width:'+Math.min(r.pct,100).toFixed(1)+'%"></div></div>':'-'}</td>
          <td style="text-align:center">${giBadge(r.gi_score,r.gi_tier)}</td>
          <td colspan="4" style="text-align:left;padding-left:8px">${holdingsChgBadge([{ct:r.change_type,pct:r.share_chg_pct}],[])}</td>
        </tr>`;
      });
    }
  });
  document.getElementById('mgrBody').innerHTML=html;
  document.querySelectorAll('#tab-managers .grp-child').forEach(tr=>{tr.style.display='table-row';});
  mkPag({filtered:mgrGroups,ps:s.ps,pg:s.pg},'mgrPag','renderMgrPage');
  setCountMeta('mgrCnt',
    `${mgrGroups.length.toLocaleString()} tickers (${mgrSt.filtered.length.toLocaleString()} positions)`,
    0, !!(typeof _holdingsFetchPromise!=='undefined'&&_holdingsFetchPromise)||!!(typeof _convictionFetchPromise!=='undefined'&&_convictionFetchPromise));
}

// Keep legacy stubs so any surviving refs don't break
function cFilter(){mgrFilter();}
function renderC(){renderMgr();}
const cSt=mgrSt;

// -- TAB 2: BUBBLE CHART --
let bChart=null;
let _bubbleSizeMode='held';
const _BUBBLE_PREFS_KEY='gekko_bubble_prefs';
function bubbleSavePrefs(){
  try{
    localStorage.setItem(_BUBBLE_PREFS_KEY,JSON.stringify({
      sizeMode:_bubbleSizeMode,
      mm:document.getElementById('bMM')?.value||'1',
      minNew:document.getElementById('bMinNew')?.value||'2',
      gi:document.getElementById('bGI')?.value||'',
      ib:document.getElementById('bIB')?.value||'',
      ibPeriod:document.getElementById('bIBPeriod')?.value||'',
      minIb:document.getElementById('bMinIB')?.value||'1',
    }));
  }catch(_e){}
}
function bubbleLoadPrefs(){
  try{
    const raw=localStorage.getItem(_BUBBLE_PREFS_KEY);
    if(!raw) return;
    const p=JSON.parse(raw);
    if(p.sizeMode&&['held','market','buys'].includes(p.sizeMode)) _bubbleSizeMode=p.sizeMode;
    const set=(id,val)=>{ const el=document.getElementById(id); if(el&&val!=null) el.value=val; };
    set('bMM',p.mm); set('bMinNew',p.minNew); set('bGI',p.gi);
    set('bIB',p.ib); set('bIBPeriod',p.ibPeriod); set('bMinIB',p.minIb);
  }catch(_e){}
}
const BUBBLE_SIZE_LABELS={
  held:'Held Value',
  market:'Market Cap / ETF Assets',
  buys:'New Position',
};
function withAlpha(hex, alpha){
  try{
    const h=String(hex||'').replace('#','');
    if(h.length!==6) return hex;
    const n=parseInt(h,16);
    const r=(n>>16)&255,g=(n>>8)&255,b=n&255;
    return `rgba(${r},${g},${b},${alpha})`;
  }catch(_e){ return hex; }
}
function bubbleUpdateSizeUI(){
  document.querySelectorAll('#tab-bubble .th-cat-btn[id^="bSize"]').forEach(b=>b.classList.remove('active'));
  const activeId=_bubbleSizeMode==='market'?'bSizeMarket':(_bubbleSizeMode==='buys'?'bSizeBuys':'bSizeHeld');
  const activeBtn=document.getElementById(activeId);
  if(activeBtn) activeBtn.classList.add('active');
  const title=document.getElementById('bSizeTitle');
  if(title) title.textContent=BUBBLE_SIZE_LABELS[_bubbleSizeMode]||BUBBLE_SIZE_LABELS.held;
}
function bubbleSetSizeMode(mode,btn){
  _bubbleSizeMode=(mode==='market'||mode==='buys')?mode:'held';
  bubbleUpdateSizeUI();
  renderBubble();
  bubbleSavePrefs();
}
function bubbleMarketSizeRef(ticker){
  const row=BUBBLE_SIZE_DATA[String(ticker||'').trim().toUpperCase()]||{};
  const marketCap=Number(row.market_cap);
  if(Number.isFinite(marketCap)&&marketCap>0){
    return {raw:marketCap,missing:false,label:'Market Cap',fmt:fmt_money_js(marketCap)};
  }
  const netAssets=Number(row.net_assets);
  if(Number.isFinite(netAssets)&&netAssets>0){
    return {raw:netAssets,missing:false,label:'Net Assets',fmt:fmt_money_js(netAssets)};
  }
  return {raw:null,missing:true,label:'Mkt Cap / Assets',fmt:'n/a'};
}
function sumInsiderBuyValue(ticker,cutoffMs){
  const rows=INSIDER_BUY_INDEX[String(ticker||'').trim().toUpperCase()]||[];
  if(!rows.length) return 0;
  let total=0;
  rows.forEach(r=>{
    if(cutoffMs){
      const ts=r.d?new Date(r.d).getTime():NaN;
      if(!Number.isFinite(ts)||ts<cutoffMs) return;
    }
    const v=Number(r.v);
    if(Number.isFinite(v)&&v>0) total+=v;
  });
  return total;
}
function bubbleSizeMetricForRow(row,cutoffMs){
  if(_bubbleSizeMode==='market') return bubbleMarketSizeRef(row?.ticker);
  if(_bubbleSizeMode==='buys'){
    // Manager new positions: $ value of holdings first appearing in latest 13F filing
    // (change_type === "NEW" from trailblazer/billionaire managers — not company insider trades)
    const nv=Math.max(0,Number(row?.new_value)||0);
    const fmt=String(row?.new_value_fmt||fmt_money_js(nv));
    return {raw:nv,missing:nv===0,label:'New Position',fmt};
  }
  const held=Math.max(0,Number(row?.total_value)||0);
  return {raw:held,missing:false,label:'Held Value',fmt:String(row?.total_value_fmt||fmt_money_js(held))};
}
function _bubbleShowOverlay(msg){
  const o=document.getElementById('bubbleOverlay');
  const m=document.getElementById('bubbleOverlayMsg');
  if(o){ o.style.display='flex'; if(m) m.textContent=msg||''; }
}
function _bubbleHideOverlay(){
  const o=document.getElementById('bubbleOverlay');
  if(o) o.style.display='none';
}
function renderBubble(){
  _bubbleHideOverlay();
  bubbleUpdateSizeUI();
  const mm=parseInt(document.getElementById('bMM').value)||1;
  const minNew=parseInt(document.getElementById('bMinNew').value)||2;
  const gi=document.getElementById('bGI').value;
  const ib=document.getElementById('bIB').value;
  const minIb=parseInt(document.getElementById('bMinIB').value)||0;
  const ibDays=parseInt(document.getElementById('bIBPeriod').value)||0;
  const cutoffMs=ibDays>0?(Date.now()-ibDays*86400000):0;
  const data=CONV.map(r=>Object.assign({},r,{_ib_distinct:countDistinctInsiderBuys(r.ticker,cutoffMs)})).filter(r=>{
    if(gi&&r.gi_tier!==gi)return false;
    if(r.gi_score==null)return false;
    if(ib==='yes'&&r._ib_distinct<1)return false;
    if(r._ib_distinct<minIb)return false;
    if(r.manager_count<mm)return false;
    // new position mode: require min managers with a new position
    if(_bubbleSizeMode==='buys'&&(r.new_count||0)<minNew)return false;
    return true;
  });
  const sizeMetrics=data.map(r=>bubbleSizeMetricForRow(r,cutoffMs));
  const rawSizeVals=sizeMetrics
    .map(m=>Number(m?.raw))
    .filter(v=>Number.isFinite(v))
    .map(v=>Math.max(0,v));
  // For buys mode scale from 0 so bubble size is proportional to absolute buy value
  const minHeld=_bubbleSizeMode==='buys'?0:(rawSizeVals.length?Math.min(...rawSizeVals):0);
  const maxHeld=rawSizeVals.length?Math.max(...rawSizeVals):0;
  const minR=4,maxRCap=24;
  const rootMin=Math.sqrt(minHeld);
  const rootSpan=Math.sqrt(maxHeld)-rootMin;
  function radiusFor(v){
    const vv=Math.max(0,Number(v)||0);
    if(maxHeld<=0) return minR;
    if(rootSpan<=0) return (minR+maxRCap)/2;
    const n=(Math.sqrt(vv)-rootMin)/rootSpan;
    return Math.max(minR,Math.min(maxRCap,minR+n*(maxRCap-minR)));
  }
  const fallbackRadius=(minR+maxRCap)/2;
  const pts=data.map((r,idx)=>{
    const sizeMeta=sizeMetrics[idx]||{raw:0,missing:false,label:'Held Value',fmt:'n/a'};
    return {x:r.manager_count,y:r.gi_score,r:sizeMeta.missing?fallbackRadius:radiusFor(sizeMeta.raw),
      _t:r.ticker,_c:r.company,_m:r.manager_count,_ib:r._ib_distinct,_v:r.total_value_fmt,
      _ml:r.mgr_list,_tier:r.gi_tier,_gi:r.gi_score,_sizeLabel:sizeMeta.label,_sizeFmt:sizeMeta.fmt,
      _md:r.manager_detail||'',_nc:r.new_count||0,_nv:r.new_value_fmt||'',_nd:r.new_detail||''};
  });
  const xVals=pts.map(p=>p.x);
  const yVals=pts.map(p=>p.y);
  const maxR=pts.length?Math.max(...pts.map(p=>p.r)):12;
  const chartPad=Math.ceil(maxR)+6;
  const bottomPad=Math.max(4,Math.ceil(maxR*0.22));
  const xSpread=pts.length?Math.max(1,Math.max(...xVals)-Math.min(...xVals)):1;
  const ySpread=pts.length?Math.max(10,Math.max(...yVals)-Math.min(...yVals)):10;
  const xPad=pts.length?Math.max(1,Math.ceil(xSpread*0.10),Math.ceil(maxR/20)):1;
  const yPad=pts.length?Math.max(2,Math.ceil(ySpread*0.08),Math.ceil(maxR/7)):3;
  const xMin=pts.length?Math.max(0,Math.floor(Math.min(...xVals)-xPad)):0;
  const xMax=pts.length?Math.ceil(Math.max(...xVals)+xPad):10;
  const yMin=pts.length?Math.max(0,Math.floor(Math.min(...yVals)-yPad)):0;
  const yMax=pts.length?Math.min(100,Math.ceil(Math.max(...yVals)+yPad)):100;
  const ctx=document.getElementById('bubbleChart').getContext('2d');
  if(bChart)bChart.destroy();
  bChart=new Chart(ctx,{
    type:'bubble',
    data:{datasets:[{
      label:'Tickers',
      data:pts,
      backgroundColor:pts.map(p=>withAlpha(p._gi!=null?giColorForValue(p._gi):UI.muted,0.55)),
      borderColor:pts.map(p=>p._gi!=null?giColorForValue(p._gi):UI.muted),
      borderWidth:pts.map(p=>p._ib>0?2.5:1.4),
      clip:false,
    }]},
    options:{
      responsive:true,maintainAspectRatio:false,
      layout:{padding:{top:chartPad,bottom:bottomPad,left:chartPad,right:chartPad}},
      plugins:{
        legend:{display:false},
        zoom:{
          zoom:{wheel:{enabled:true},drag:{enabled:false},mode:'xy'},
          pan:{enabled:true,mode:'xy'},
        },
        tooltip:{enabled:false},
      },
      scales:{
        x:{title:{display:true,text:'Number of Managers Holding',color:UI.muted,font:{family:'JetBrains Mono',size:11}},
           grid:{color:'rgba(255,255,255,0.03)'},ticks:{color:UI.muted,font:{family:'JetBrains Mono'}},min:xMin,max:xMax},
        y:{title:{display:true,text:'GI Score',color:UI.muted,font:{family:'JetBrains Mono',size:11}},
           grid:{color:'rgba(255,255,255,0.03)'},ticks:{color:UI.muted,font:{family:'JetBrains Mono'}},min:yMin,max:yMax},
      },
    },
  });
  bubbleSavePrefs();
}

// ---- Bubble Chart v2 globals ----
window.SECTOR_COLORS={
  'Technology':'#7AA2F7','Financial':'#E0AF68','Healthcare':'#9ECE6A',
  'Consumer':'#F7768E','Energy':'#FF9E64','Industrials':'#BB9AF7',
  'Communication':'#7DCFFF','Utilities':'#73DACA','Real Estate':'#B4B4B4','Materials':'#C0CAF5'
};
window.fmtMoney=function(v){
  if(v==null||!isFinite(v))return'—';
  if(v>=1e12)return'$'+(v/1e12).toFixed(2)+'T';
  if(v>=1e9)return'$'+(v/1e9).toFixed(2)+'B';
  if(v>=1e6)return'$'+(v/1e6).toFixed(1)+'M';
  if(v>=1e3)return'$'+(v/1e3).toFixed(0)+'K';
  return'$'+Math.round(v);
};
window.fmtPct=function(v){
  if(v==null||!isFinite(v))return'—';
  return(v>0?'+':'')+v.toFixed(1)+'%';
};
window.giColor=function(v){
  if(v==null)return'#777';
  if(v>=75)return'#22c55e';
  if(v>=60)return'#86efac';
  if(v>=45)return'#facc15';
  if(v>=33)return'#f97316';
  return'#ef4444';
};
function _bcGiTier(gi){
  if(gi>=75)return'dark-green';
  if(gi>=60)return'green';
  if(gi>=45)return'yellow';
  if(gi>=33)return'orange';
  return'red';
}
window.DATASET=[];
function buildBubbleDataset(){
  const rows=CONV.map(r=>{
    const bsd=BUBBLE_SIZE_DATA[String(r.ticker||'').toUpperCase()]||{};
    const ibDistinct=countDistinctInsiderBuys(r.ticker,0);
    const ibValue=sumInsiderBuyValue(r.ticker,0);
    const sector=bsd.sector||r.sector||'';
    return{
      ticker:r.ticker,
      company:r.company||BL_TICKER_INFO[r.ticker]||'',
      sector,
      gi_score:r.gi_score!=null?+r.gi_score:null,
      gi_tier:r.gi_tier||_bcGiTier(r.gi_score||0),
      manager_count:r.manager_count||0,
      new_count:r.new_count||0,
      total_value:Math.max(0,Number(r.total_value)||0),
      new_value:Math.max(0,Number(r.new_value)||0),
      insider_buys_distinct:ibDistinct,
      insider_buys_value:ibValue,
      chg_30d:null,
      chg_90d:null,
    };
  }).filter(r=>r.gi_score!=null);
  return rows;
}
let _bcRoot=null;
let _bcScriptsLoaded=false;
let _bcScriptsPromise=null;
function _bcLoadScript(src){
  return new Promise((resolve,reject)=>{
    const s=document.createElement('script');
    s.src=src; s.crossOrigin='anonymous';
    s.onload=resolve;
    s.onerror=()=>reject(new Error('Failed: '+src));
    document.head.appendChild(s);
  });
}
function _ensureBcScripts(){
  if(_bcScriptsLoaded)return Promise.resolve();
  if(_bcScriptsPromise)return _bcScriptsPromise;
  _bcScriptsPromise=_bcLoadScript('https://unpkg.com/react@18.3.1/umd/react.production.min.js')
    .then(()=>_bcLoadScript('https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js'))
    .then(()=>_bcLoadScript('https://unpkg.com/@babel/standalone@7.29.0/babel.min.js'))
    .then(()=>new Promise(r=>setTimeout(r,80))) // let Babel transform type="text/babel" scripts
    .then(()=>{_bcScriptsLoaded=true;});
  return _bcScriptsPromise;
}
let _bcMounting=false;
function mountBubbleChartV2(){
  if(_bcRoot)return;
  if(_bcMounting)return;
  _bcMounting=true;
  _bubbleShowOverlay('Loading chart…');
  _ensureBcScripts().then(()=>{
    const canvas=document.getElementById('chart');
    if(!canvas||!window.BubbleChartApp){console.warn('bc: chart element or component missing');return;}
    const host=canvas.parentElement;
    canvas.remove();
    const mount=document.createElement('div');
    mount.id='bcReactRoot';
    mount.style.cssText='position:absolute;inset:0';
    host.appendChild(mount);
    _bcRoot=ReactDOM.createRoot(mount);
    _bcRoot.render(React.createElement(window.BubbleChartApp,{rows:window.DATASET}));
    _bubbleHideOverlay();
  }).catch(err=>{
    console.error('bc: script load failed',err);
    _bubbleShowOverlay('Chart failed to load. Check connection.');
    _bcMounting=false;
  });
}
function updateBubbleChartDataset(){
  const rows=buildBubbleDataset();
  window.DATASET=rows;
  if(_bcRoot){
    _bcRoot.render(React.createElement(window.BubbleChartApp,{rows}));
  }
  _bubbleHideOverlay();
}
// -- Bubble chart custom tooltip --
const _bubbleTipEl=(()=>{const d=document.createElement('div');d.className='bubble-tip';document.body.appendChild(d);return d;})();
let _bubbleTipTicker='';
function _bubbleTipGiColor(score){
  if(score==null) return '#8b8fa8';
  if(score>=75) return '#22c55e';
  if(score>=55) return '#86efac';
  if(score>=40) return '#facc15';
  if(score>=25) return '#f97316';
  return '#ef4444';
}
function _bubbleTipGiLabel(tier){
  const m={
    'dark-green':'Strong Accum','green':'Accumulation',
    'yellow':'Neutral','orange':'Distribution','red':'Heavy Dist'
  };
  return m[tier]||tier||'—';
}
function _bubbleTipChgColor(ct){
  if(ct==='NEW')       return '#86efac';
  if(ct==='INCREASED') return '#4ade80';
  if(ct==='DECREASED') return '#f97316';
  if(ct==='SOLD')      return '#ef4444';
  if(ct==='UNKNOWN')   return '#6b7080';
  return '#8b8fa8';
}
function _bubbleTipChgLabel(ct, pct){
  if(ct==='NEW')       return '★ New';
  if(ct==='SOLD')      return '✕ Sold';
  if(ct==='INCREASED') return pct!=null?`▲ +${pct.toFixed(1)}%`:'▲ Increased';
  if(ct==='DECREASED') return pct!=null?`▼ ${pct.toFixed(1)}%`:'▼ Decreased';
  if(ct==='UNKNOWN')   return '? No prior data';
  return '— Unchanged';
}
function showBubbleTip(d, evt){
  if(_bubbleTipTicker===d._t && _bubbleTipEl.classList.contains('show')){
    _positionBubbleTip(evt); return;
  }
  _bubbleTipTicker=d._t;
  const giColor=_bubbleTipGiColor(d._gi);
  // Build per-manager rows from HOLDINGS (exclude SOLD)
  const hRows=(HOLDINGS||[]).filter(h=>h.ticker===d._t&&h.change_type!=='SOLD');
  const mgrRowsHtml=hRows.length?hRows.map(h=>{
    const ct=h.change_type||'UNCHANGED';
    const chgColor=_bubbleTipChgColor(ct);
    const chgLabel=_bubbleTipChgLabel(ct,h.share_chg_pct!=null?Number(h.share_chg_pct):null);
    return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-top:1px solid rgba(255,255,255,.05)">
      <span style="font-size:10px;color:#cbd5e1;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(h.manager||'')}">${escHtml(h.manager||'—')}</span>
      <span style="font-size:10px;color:#4ade80;margin:0 8px;white-space:nowrap">${h.value_fmt||'—'}</span>
      <span style="font-size:10px;color:${chgColor};white-space:nowrap">${chgLabel}</span>
    </div>`;
  }).join(''):'';
  _bubbleTipEl.innerHTML=`
    <div class="bubble-tip-tv"><tv-mini-chart symbol="${getFinalSymbol(d._t,'')}" time-frame="3M" line-chart-type="Baseline" theme="dark" style="width:100%;height:208px;display:block;margin-top:-2px"></tv-mini-chart></div>
    <div class="bubble-tip-body">
      <div class="bubble-tip-header">
        <span class="bubble-tip-ticker">${d._t}</span>
        <span class="bubble-tip-company" title="${d._c||''}">${d._c||''}</span>
      </div>
      <div class="bubble-tip-row">
        <span class="bubble-tip-lbl">GI Score</span>
        <span class="bubble-tip-val" style="color:${giColor}">${d._gi!=null?d._gi.toFixed(1):'—'} <span style="font-size:10px;color:${giColor};opacity:.8">${_bubbleTipGiLabel(d._tier)}</span></span>
      </div>
      <div class="bubble-tip-row">
        <span class="bubble-tip-lbl">Total Held Value</span>
        <span class="bubble-tip-val" style="color:#4ade80">${d._v||'—'}</span>
      </div>
      ${d._ib>0?`<div class="bubble-tip-row"><span class="bubble-tip-lbl">Insider Buys</span><span class="bubble-tip-val" style="color:#fbbf24">${d._ib} distinct</span></div>`:''}
      ${mgrRowsHtml?`<div style="margin-top:6px;padding-top:2px;border-top:1px solid rgba(255,255,255,.08)"><div style="font-size:9px;color:#4a5568;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Managers (${hRows.length})</div>${mgrRowsHtml}</div>`:''}
      <div class="bubble-tip-click">CLICK TO OPEN CHART →</div>
    </div>`;
  _bubbleTipEl.classList.add('show');
  _positionBubbleTip(evt);
}
function _positionBubbleTip(evt){
  const pad=14, w=_bubbleTipEl.offsetWidth||320, h=_bubbleTipEl.offsetHeight||400;
  const mX=Number(evt.clientX)||0, mY=Number(evt.clientY)||0;
  const sW=window.innerWidth||1200, sH=window.innerHeight||800;
  let left=mX+20, top=mY-h/2;
  if(left+w>sW-pad) left=mX-w-20;
  top=Math.max(pad,Math.min(top,sH-h-pad));
  _bubbleTipEl.style.left=left+'px';
  _bubbleTipEl.style.top=top+'px';
}
function hideBubbleTip(){
  _bubbleTipTicker='';
  _bubbleTipEl.classList.remove('show');
  _bubbleTipEl.innerHTML='';
}
_bubbleTipEl.addEventListener('click',()=>{
  if(_bubbleTipTicker){ goChart(_bubbleTipTicker); hideBubbleTip(); }
});
// Wire hover + click onto the bubble canvas
document.addEventListener('mousemove',evt=>{
  const canvas=document.getElementById('bubbleChart');
  if(!canvas||!bChart) return;
  const rect=canvas.getBoundingClientRect();
  if(evt.clientX<rect.left||evt.clientX>rect.right||evt.clientY<rect.top||evt.clientY>rect.bottom){
    if(_bubbleTipEl.classList.contains('show')) hideBubbleTip();
    return;
  }
  const elements=bChart.getElementsAtEventForMode(evt,'nearest',{intersect:true},false);
  if(elements.length){
    const d=bChart.data.datasets[elements[0].datasetIndex].data[elements[0].index];
    showBubbleTip(d,evt);
    canvas.style.cursor='pointer';
  } else {
    hideBubbleTip();
    canvas.style.cursor='default';
  }
});
document.getElementById('bubbleChart')?.addEventListener('click',evt=>{
  if(!bChart) return;
  const elements=bChart.getElementsAtEventForMode(evt,'nearest',{intersect:true},false);
  if(elements.length){
    const d=bChart.data.datasets[elements[0].datasetIndex].data[elements[0].index];
    goChart(d._t);
  }
});

// -- TAB 3: BUY LEVELS --
let blChart=null,giHistChart=null,_crosshairRatio=null,_crosshairXVal=null,_crosshairY=null,_crosshairSource='';
var _blPeriod=365,_blChartType='hollow',_blShowGI=true,_blGIPos='lower',
    _blShowEarnings=true,_blShowReversals=true,_blShowInsiders=true;
var _blShowVwap=false,_blShowValueChart=false,_blShowMA50=false,_blShowMA200=false,
    _blShowProfile=true,_blShowVSA=true,_blShowDataTooltip=false,_blShowCrosshair=true;
var _blShowTargetLines=true,_blShowStopLine=true,_blShowLookbackBar=true;
let _blProjLookback=0;  // 0 = current bar; N = use close price N bars ago as entry anchor
function _syncLookbackBarPos(chart){
  const bar=document.getElementById('blLookbackBar');
  if(!bar) return;
  const c=chart||blChart;
  if(!c||!c.scales||!c.scales.x||!c.canvas) return;
  const lastIdx=(_blOhlcv||[]).length-1;
  if(lastIdx<0) return;
  // Anchor to lastIdx + right padding so buttons sit at the chart's right edge in default view
  const anchorX=lastIdx+(_blRightBars||0)+12.0;
  const px=c.scales.x.getPixelForValue(anchorX);
  const canvas=c.canvas;
  const wrap=canvas.offsetParent;
  const canvasLeft=(canvas.offsetLeft||0)+(wrap?wrap.offsetLeft||0:0);
  bar.style.left=(canvasLeft+px+8)+'px';
  bar.style.right='auto';
  // Dynamic bottom: 34px above the volume area, plus GI lower section height when visible
  const giSection=document.getElementById('blGISection');
  const giH=(giSection&&_blGIPos==='lower')?(giSection.offsetHeight||88):0;
  bar.style.bottom=(giH+34)+'px';
}
const blLookbackSyncPlugin={id:'blLookbackSync',afterDraw(chart){_syncLookbackBarPos(chart);}};
function blSetLookback(n){
  _blProjLookback=n;
  const ids=[0,5,10,20,30,50];
  ids.forEach(d=>{
    const btn=document.getElementById('blLb'+d);
    if(!btn) return;
    btn.classList.toggle('active',d===n);
    btn.classList.toggle('lb-past',d===n&&n>0);
  });
  // Recalculate projection lines from historical anchor price
  gispCalc();
  if(blChart) blChart.update('none');
}
var _blMarginTopPct=3,_blMarginBotPct=30,_blRightBars=0,_blVolumeScale=1;
var _blVcConsistentGaps=true,_blVcWidthScale=1,_blVcFilled=false;
var _blShowGIReturns=true,_blShowGIBacktest=true,_blShowGISizer=true;
var _blNeutralColor='#CCCCCC';
var _blUpColor='#33AA00';
var _blDownColor='#CC3300';
var _blVolUpColor='#33AA00';
var _blVolDownColor='#CC3300';
var _blInsiderDotColor='#facc15';
var _blVCColor='#f97316';
var _blVwapColor='#facc15';
var _blMA50Color='#3b82f6';
var _blMA200Color='#ef4444';
function blHexToRgba(hex,alpha){
  try{
    const h=String(hex||'').replace('#','');
    if(h.length!==6) return hex;
    const n=parseInt(h,16);
    return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${alpha})`;
  }catch(_e){return hex;}
}
var _blChartColorMode='neutral';
let _blOhlcv=[];
let _blVsaCache=null, _blIndCache=null;
let _blBuys=[];
let _blBuysIdxReady=false; // true only after _blBuys._idx values have been mapped
let _blRenderedTicker='';
let _blSavedZoom=null; // {span:number,rightGap:number}
let _blForceDefaultRange=false;
let _blDeferredOpacityRestore=false;
let _giPts=[];
let _blGIRenderRetryToken=0;
function clampNum(v,lo,hi){
  if(!Number.isFinite(v)) return lo;
  return Math.max(lo,Math.min(hi,v));
}
function blCaptureZoomState(){
  if(!blChart||!blChart.scales||!blChart.scales.x||!_blOhlcv.length) return;
  const sx=blChart.scales.x;
  const span=Number(sx.max)-Number(sx.min);
  const rightGap=Number(sx.max)-(_blOhlcv.length-1);
  if(!Number.isFinite(span)||span<=0) return;
  _blSavedZoom={
    span,
    rightGap:Number.isFinite(rightGap)?rightGap:(_blRightBars+2.5)
  };
}
function blRangeFromSavedZoom(ohlcv){
  const saved=_blSavedZoom;
  const n=(ohlcv||[]).length;
  if(!saved||!n) return null;
  const savedSpan=Number(saved.span);
  if(!Number.isFinite(savedSpan)||savedSpan<=0) return null;
  const maxIdx=n-1;
  const minRightGap=_blRightBars+2.5;
  const rightGapRaw=Number(saved.rightGap);
  const rightGap=Number.isFinite(rightGapRaw)?Math.max(minRightGap,rightGapRaw):minRightGap;
  const xMax=maxIdx+rightGap;
  const maxSpan=(maxIdx+rightGap)+1;
  const span=Math.max(10,Math.min(savedSpan,maxSpan));
  return {min:Math.max(0,xMax-span),max:xMax};
}
function setRangeIfChanged(scaleOpts,minVal,maxVal){
  const prevMin=scaleOpts.min;
  const prevMax=scaleOpts.max;
  scaleOpts.min=minVal;
  scaleOpts.max=maxVal;
  return prevMin!==minVal||prevMax!==maxVal;
}
function giColorForValue(v){
  if(v>=70)return GIC['dark-green'];
  if(v>=60)return GIC.green;
  if(v>=45)return GIC.yellow;
  if(v>=33)return GIC.orange;
  return GIC.red;
}
function giLineGradient(chart,yScale){
  if(!chart.chartArea) return giColorForValue((yScale.min+yScale.max)/2);
  const minV=yScale.min,maxV=yScale.max;
  const span=maxV-minV;
  if(!Number.isFinite(span)||span<=0) return giColorForValue(minV);
  const grad=chart.ctx.createLinearGradient(0,chart.chartArea.bottom,0,chart.chartArea.top);
  const marks=[minV,33,45,60,70,maxV].filter(v=>v>=minV&&v<=maxV).sort((a,b)=>a-b);
  const uniq=[...new Set(marks)];
  if(!uniq.length){
    grad.addColorStop(0,giColorForValue(minV));
    grad.addColorStop(1,giColorForValue(maxV));
    return grad;
  }
  uniq.forEach(v=>grad.addColorStop((v-minV)/span,giColorForValue(v)));
  return grad;
}
function blBottomPricePadRatio(){
  if(blShowVolume()) return (_blShowGI&&_blGIPos==='overlay') ? 0.33 : 0.30;
  if(_blShowGI&&_blGIPos==='overlay') return 0.20;
  return 0.06;
}
function blVisibleProjectionPrices(rawMin, rawMax){
  if(!_projLines.length||!_blOhlcv.length) return [];
  const lastIdx=_blOhlcv.length-1;
  return _projLines
    .filter(p=>{
      const price=Number(p?.price);
      if(!Number.isFinite(price)) return false;
      const days=Number.isFinite(Number(p?.days)) ? Number(p.days) : 0;
      let xMin=lastIdx, xMax=lastIdx;
      if(days===0){
        if(p.label==='Entry') return false;
        if(!_blShowStopLine) return false;
        xMax=Infinity;
      }else if(p.label==='Stop'){
        if(!_blShowStopLine) return false;
        xMax=lastIdx+days;
      }else{
        if(!_blShowTargetLines) return false;
        const targetIdx=lastIdx+days;
        xMin=targetIdx-1;
        xMax=targetIdx+1;
      }
      return xMax>=rawMin&&xMin<=rawMax;
    })
    .map(p=>Number(p.price));
}

function syncGIToBuyRange(){
  if(!blChart||!_blOhlcv.length) return;
  const sx=blChart.scales&&blChart.scales.x;
  if(!sx) return;
  const rawMin=Number.isFinite(sx.min)?sx.min:0;
  const rawMax=Number.isFinite(sx.max)?sx.max:(_blOhlcv.length-1);
  if(rawMax<rawMin) return;
  const lo=Math.max(0,Math.floor(rawMin));
  const hi=Math.min(_blOhlcv.length-1,Math.ceil(rawMax));
  const vis=(hi>=lo)?_blOhlcv.slice(lo,hi+1):[];

  const lows=vis.map(d=>d.l).filter(Number.isFinite);
  const highs=vis.map(d=>d.h).filter(Number.isFinite);
  const projPrices=blVisibleProjectionPrices(rawMin, rawMax);
  let buyChanged=false,giChanged=false;
  const priceVals=[...lows,...highs,...projPrices].filter(Number.isFinite);
  if(priceVals.length){
    let loP=Math.min(...priceVals),hiP=Math.max(...priceVals);
    if(!(hiP>loP)){
      const flatPad=Math.max(0.25, Math.abs(hiP||loP||1)*0.02);
      loP-=flatPad;
      hiP+=flatPad;
    }
    const span=Math.max(0.01,hiP-loP);
    const padTop=Math.max(0.01,span*(_blMarginTopPct/100));
    // Preserve extra lower room for the overlaid volume panel.
    const padBottom=Math.max(0.01,span*(_blMarginBotPct/100));
    const yMin=Math.max(0,loP-padBottom),yMax=hiP+padTop;
    if(blChart.options&&blChart.options.scales&&blChart.options.scales.y){
      buyChanged=setRangeIfChanged(blChart.options.scales.y,yMin,yMax);
    }
  }

  if(giHistChart&&giHistChart.options&&giHistChart.options.scales){
    const gx=giHistChart.options.scales.x;
    if(gx){
      giChanged=setRangeIfChanged(gx,rawMin,rawMax)||giChanged;
    }
    const gy=giHistChart.options.scales.y;
    if(gy&&_giPts.length){
      // Always use the full dataset for y-axis so the line never clips when zoomed in or switching symbols
      const src=_giPts.map(p=>p.v).filter(Number.isFinite);
      if(src.length){
        let gMin=Math.min(...src),gMax=Math.max(...src);
        if(gMax<=gMin){gMin-=0.5;gMax+=0.5;}
        const _gyPad=Math.max((gMax-gMin)*0.10,2);
        gMin=Math.max(0,gMin-_gyPad); gMax=Math.min(100,gMax+_gyPad);
        giChanged=setRangeIfChanged(gy,gMin,gMax)||giChanged;
      }
    }
  }
  if(buyChanged)blChart.update('none');
  // Sync giHistChart left padding to blChart.chartArea.left so crosshairs align pixel-perfectly
  if(giHistChart&&blChart?.chartArea){
    const targetLeft=blChart.chartArea.left||0;
    const padObj=giHistChart.options?.layout?.padding;
    if(padObj&&Math.abs((padObj.left||0)-targetLeft)>0.5){
      padObj.left=targetLeft;
      giChanged=true;
    }
  }
  if(giChanged&&giHistChart)giHistChart.update('none');
}
function relayoutBuyCharts(){
  // When ticker changes, sibling panel visibility can alter flex heights.
  // Force a post-layout resize so Chart.js uses the final container size.
  requestAnimationFrame(()=>{
    requestAnimationFrame(()=>{
      if(blChart){blChart.resize();blChart.update('none');}
      if(giHistChart){giHistChart.resize();giHistChart.update('none');}
      syncGIToBuyRange();
      // Restore main chart visibility only AFTER resize/update complete,
      // so the resize jitter is never visible.
      if(_blDeferredOpacityRestore){
        _blDeferredOpacityRestore=false;
        const w=document.getElementById('blChartWrap');
        if(w){w.style.transition='opacity 0.07s ease';w.style.opacity='1';}
      }
    });
  });
}
function blScheduleLowerGIRenderRetries(ticker){
  const expected=ticker||'';
  const token=++_blGIRenderRetryToken;
  if(_blGIPos!=='lower'||!expected) return;
  [150, 500, 1200, 2500].forEach(ms=>{
    setTimeout(()=>{
      if(token!==_blGIRenderRetryToken) return;
      if(_blGIPos!=='lower') return;
      if(!document.getElementById('tab-buylevels')?.classList.contains('active')) return;
      const cur=blCurrentTicker();
      if(cur!==expected) return;
      // Skip if chart already rendered with real data
      if(giHistChart&&_giPts.length>0) return;
      // If GI data is now available, do a full re-render (same path as manual refresh)
      const hasData=GI_HISTORY&&GI_HISTORY[expected]&&GI_HISTORY[expected].length>0;
      if(hasData){
        renderBuyLevels().catch(()=>{});
      } else {
        // Data still loading — just try renderGIChart in case it arrives soon
        renderGIChart(expected);
      }
    }, ms);
  });
}
window.addEventListener('resize',()=>{
  if(blChart||giHistChart) relayoutBuyCharts();
});
window.addEventListener('load',()=>{
  const cur=blCurrentTicker();
  if(cur) blScheduleLowerGIRenderRetries(cur);
  // Strip all browser-native tooltips from the chart tab controls and dropdowns
  const blTab=document.getElementById('tab-buylevels');
  if(blTab) blTab.querySelectorAll('[title]').forEach(el=>el.removeAttribute('title'));
});
document.fonts?.ready?.then?.(()=>{
  const cur=blCurrentTicker();
  if(cur) blScheduleLowerGIRenderRetries(cur);
});
document.getElementById('mainArea')?.addEventListener('transitionend',evt=>{
  if(evt.propertyName!=='margin-left') return;
  if(!document.getElementById('tab-buylevels')?.classList.contains('active')) return;
  relayoutBuyCharts();
});
function blCloseChartTypeMenu(){
  const menu=document.getElementById('blChartTypeMenu');
  const btn=document.getElementById('blBtnChartType');
  if(menu) menu.style.display='none';
  if(btn) btn.classList.remove('open');
}
function blToggleIndicatorsMenu(evt){
  evt?.stopPropagation?.();
  blCloseChartTypeMenu();
  const menu=document.getElementById('blIndicatorsMenu');
  const btn=document.getElementById('blBtnIndicators');
  const isOpen=menu&&(menu.style.display!=='none'&&menu.style.display!=='');
  if(menu) menu.style.display=isOpen?'none':'block';
  if(btn) btn.classList.toggle('open',!isOpen);
}
function blToggleChartTypeMenu(evt){
  evt?.stopPropagation?.();
  const indMenu=document.getElementById('blIndicatorsMenu');
  const indBtn=document.getElementById('blBtnIndicators');
  if(indMenu) indMenu.style.display='none';
  if(indBtn) indBtn.classList.remove('open');
  const menu=document.getElementById('blChartTypeMenu');
  const btn=document.getElementById('blBtnChartType');
  const isOpen=menu&&(menu.style.display!=='none'&&menu.style.display!=='');
  if(menu) menu.style.display=isOpen?'none':'block';
  if(btn) btn.classList.toggle('open',!isOpen);
}
document.addEventListener('click', evt=>{
  const closeMenu=(menuId, btnId)=>{
    const menu=document.getElementById(menuId);
    const btn=document.getElementById(btnId);
    if(menu && btn && !menu.contains(evt.target) && evt.target!==btn && !btn.contains(evt.target)){
      menu.style.display='none';
      btn.classList.remove('open');
    }
  };
  closeMenu('blIndicatorsMenu','blBtnIndicators');
  closeMenu('blChartTypeMenu','blBtnChartType');
});
function blChartTypeLabel(mode){
  return BL_CHART_TYPE_LABELS[String(mode||'').toLowerCase()] || BL_CHART_TYPE_LABELS.hollow;
}
function blSyncChartTypeUI(){
  const set=(id,on)=>{ const el=document.getElementById(id); if(el) el.innerHTML=on?'&#10003;':''; };
  set('blChartTypeHollowChk', _blChartType==='hollow');
  set('blChartTypeCandleChk', _blChartType==='candle');
  set('blChartTypeLineChk', _blChartType==='line');
  set('blChartTypeOhlcChk', _blChartType==='ohlc');
  set('blChartTypeHlcChk', _blChartType==='hlc');
  set('blChartTypeVolcndleChk', _blChartType==='volcndle');
  set('blChartColorOpenChk', _blChartColorMode==='open');
  set('blChartColorChangeChk', _blChartColorMode==='change');
  set('blChartColorNeutralChk', _blChartColorMode==='neutral');
  const _mti=document.getElementById('blMarginTopInput'); if(_mti) _mti.value=_blMarginTopPct;
  const _mbi=document.getElementById('blMarginBotInput'); if(_mbi) _mbi.value=_blMarginBotPct;
  const _mri=document.getElementById('blMarginRightInput'); if(_mri) _mri.value=_blRightBars;
  blSyncVolumeScaleUI();
  blSyncVcWidthScaleUI();
  _blSyncVcFilledUI();
  const _sw=document.getElementById('blNeutralColorSwatch'); if(_sw) _sw.style.background=_blNeutralColor;
  const _ci=document.getElementById('blNeutralColorCustom'); if(_ci) _ci.value=_blNeutralColor;
  const _ups=document.getElementById('blUpColorSwatch'); if(_ups) _ups.style.background=_blUpColor;
  const _upc=document.getElementById('blUpColorCustom'); if(_upc) _upc.value=_blUpColor;
  const _dns=document.getElementById('blDownColorSwatch'); if(_dns) _dns.style.background=_blDownColor;
  const _dnc=document.getElementById('blDownColorCustom'); if(_dnc) _dnc.value=_blDownColor;
  const _vus=document.getElementById('blVolUpColorSwatch'); if(_vus) _vus.style.background=_blVolUpColor;
  const _vuc=document.getElementById('blVolUpColorCustom'); if(_vuc) _vuc.value=_blVolUpColor;
  const _vds=document.getElementById('blVolDownColorSwatch'); if(_vds) _vds.style.background=_blVolDownColor;
  const _vdc=document.getElementById('blVolDownColorCustom'); if(_vdc) _vdc.value=_blVolDownColor;
  const _ids=document.getElementById('blInsiderDotSwatch'); if(_ids) _ids.style.background=_blInsiderDotColor;
  const _idc=document.getElementById('blInsiderDotColorCustom'); if(_idc) _idc.value=_blInsiderDotColor;
  const _vcs=document.getElementById('blVCSwatch'); if(_vcs) _vcs.style.background=_blVCColor;
  const _vwaps=document.getElementById('blVwapSwatch'); if(_vwaps) _vwaps.style.background=_blVwapColor;
  const _ma50s=document.getElementById('blMA50Swatch'); if(_ma50s) _ma50s.style.background=_blMA50Color;
  const _ma200s=document.getElementById('blMA200Swatch'); if(_ma200s) _ma200s.style.background=_blMA200Color;
}
function blSetChartType(mode){
  const next=String(mode||'').toLowerCase();
  if(!Object.prototype.hasOwnProperty.call(BL_CHART_TYPE_LABELS, next)) return;
  const changed=next!==_blChartType;
  _blChartType=next;
  blCloseChartTypeMenu();
  blSyncIndicatorChecks();
  saveBuyLevelsPrefs();
  if(changed) renderBuyLevels();
}
function blToggleVcGaps(){
  _blVcConsistentGaps=!_blVcConsistentGaps;
  _blSyncVcGapsUI();
  saveBuyLevelsPrefs();
  if(blChart) blChart.update('none');
}
function _blSyncVcGapsUI(){
  const lbl=document.getElementById('blVcGapsToggleLabel');
  const wrap=document.getElementById('blVcGapsToggleWrap');
  if(lbl) lbl.textContent=_blVcConsistentGaps?'= gaps':'~ gaps';
  if(wrap){
    wrap.style.color=_blVcConsistentGaps?'#93c5fd':'#aaa';
    wrap.style.borderColor=_blVcConsistentGaps?'#4b8ad4':'#444';
  }
}
function blToggleVcFilled(){
  _blVcFilled=!_blVcFilled;
  _blSyncVcFilledUI();
  saveBuyLevelsPrefs();
  if(blChart) blChart.update('none');
}
function _blSyncVcFilledUI(){
  const lbl=document.getElementById('blVcFilledToggleLabel');
  const wrap=document.getElementById('blVcFilledToggleWrap');
  if(lbl) lbl.textContent=_blVcFilled?'filled':'hollow';
  if(wrap){
    wrap.style.color=_blVcFilled?'#93c5fd':'#aaa';
    wrap.style.borderColor=_blVcFilled?'#4b8ad4':'#444';
  }
}
function blTriggerCustomColor(inputId, triggerEl, evt){
  evt?.stopPropagation?.();
  const inp=document.getElementById(inputId);
  if(!inp) return;
  const rect=triggerEl.getBoundingClientRect();
  inp.style.position='fixed';
  inp.style.left=Math.round(rect.left)+'px';
  inp.style.top=Math.round(rect.bottom)+'px';
  inp.style.width='0';
  inp.style.height='0';
  inp.style.opacity='0';
  inp.style.pointerEvents='none';
  inp.style.display='block';
  inp.click();
}
function blToggleInsiderColorPicker(evt){
  evt?.stopPropagation?.();
  const p=document.getElementById('blInsiderColorPickerPanel');
  if(!p) return;
  p.style.display=p.style.display==='none'?'block':'none';
  const ci=document.getElementById('blInsiderDotColorCustom'); if(ci) ci.value=_blInsiderDotColor;
}
function blToggleIndColorPicker(panelId, inputId, currentColor){
  const allPanels=['blUpColorPanel','blDownColorPanel','blVCColorPanel','blVwapColorPanel','blMA50ColorPanel','blMA200ColorPanel'];
  allPanels.forEach(id=>{
    if(id!==panelId){const p=document.getElementById(id);if(p)p.style.display='none';}
  });
  const p=document.getElementById(panelId);
  if(!p) return;
  p.style.display=p.style.display==='none'?'block':'none';
  const ci=document.getElementById(inputId); if(ci&&currentColor) ci.value=currentColor;
}
function blSetInsiderDotColor(hex){
  if(!hex) return;
  _blInsiderDotColor=hex;
  const sw=document.getElementById('blInsiderDotSwatch'); if(sw) sw.style.background=hex;
  const ci=document.getElementById('blInsiderDotColorCustom'); if(ci) ci.value=hex;
  saveBuyLevelsPrefs();
  if(blChart) blChart.update('none');
}
function blToggleColorPicker(evt){
  evt?.stopPropagation?.();
  const p=document.getElementById('blColorPickerPanel');
  if(!p) return;
  p.style.display=p.style.display==='none'?'block':'none';
  const ci=document.getElementById('blNeutralColorCustom'); if(ci) ci.value=_blNeutralColor;
}
function blSetNeutralColor(hex){
  if(!hex) return;
  _blNeutralColor=hex;
  const sw=document.getElementById('blNeutralColorSwatch'); if(sw) sw.style.background=hex;
  const ci=document.getElementById('blNeutralColorCustom'); if(ci) ci.value=hex;
  blSetChartColorMode('neutral');
}
function blSetUpColor(hex){
  if(!hex||!/^#[0-9a-fA-F]{6}$/.test(hex)) return;
  _blUpColor=hex;
  const sw=document.getElementById('blUpColorSwatch'); if(sw) sw.style.background=hex;
  const ci=document.getElementById('blUpColorCustom'); if(ci) ci.value=hex;
  saveBuyLevelsPrefs(); renderBuyLevels();
}
function blSetDownColor(hex){
  if(!hex||!/^#[0-9a-fA-F]{6}$/.test(hex)) return;
  _blDownColor=hex;
  const sw=document.getElementById('blDownColorSwatch'); if(sw) sw.style.background=hex;
  const ci=document.getElementById('blDownColorCustom'); if(ci) ci.value=hex;
  saveBuyLevelsPrefs(); renderBuyLevels();
}
function blSetVolUpColor(hex){
  if(!hex||!/^#[0-9a-fA-F]{6}$/.test(hex)) return;
  _blVolUpColor=hex;
  const sw=document.getElementById('blVolUpColorSwatch'); if(sw) sw.style.background=hex;
  const ci=document.getElementById('blVolUpColorCustom'); if(ci) ci.value=hex;
  saveBuyLevelsPrefs(); if(blChart) blChart.update('none');
}
function blSetVolDownColor(hex){
  if(!hex||!/^#[0-9a-fA-F]{6}$/.test(hex)) return;
  _blVolDownColor=hex;
  const sw=document.getElementById('blVolDownColorSwatch'); if(sw) sw.style.background=hex;
  const ci=document.getElementById('blVolDownColorCustom'); if(ci) ci.value=hex;
  saveBuyLevelsPrefs(); if(blChart) blChart.update('none');
}
function blMakeColorSetter(varRef, swatchId, inputId, update){
  return function(hex){
    if(!hex) return;
    varRef.set(hex);
    const sw=document.getElementById(swatchId); if(sw) sw.style.background=hex;
    const ci=document.getElementById(inputId); if(ci) ci.value=hex;
    saveBuyLevelsPrefs();
    if(update&&blChart) blChart.update('none');
  };
}
function blSetVCColor(hex){ if(!hex)return; _blVCColor=hex; const sw=document.getElementById('blVCSwatch'); if(sw)sw.style.background=hex; const ci=document.getElementById('blVCColorCustom'); if(ci)ci.value=hex; saveBuyLevelsPrefs(); if(blChart)blChart.update('none'); }
function blSetVwapColor(hex){ if(!hex)return; _blVwapColor=hex; const sw=document.getElementById('blVwapSwatch'); if(sw)sw.style.background=hex; const ci=document.getElementById('blVwapColorCustom'); if(ci)ci.value=hex; saveBuyLevelsPrefs(); if(blChart)blChart.update(); }
function blSetMA50Color(hex){ if(!hex)return; _blMA50Color=hex; const sw=document.getElementById('blMA50Swatch'); if(sw)sw.style.background=hex; const ci=document.getElementById('blMA50ColorCustom'); if(ci)ci.value=hex; saveBuyLevelsPrefs(); if(blChart)blChart.update(); }
function blSetMA200Color(hex){ if(!hex)return; _blMA200Color=hex; const sw=document.getElementById('blMA200Swatch'); if(sw)sw.style.background=hex; const ci=document.getElementById('blMA200ColorCustom'); if(ci)ci.value=hex; saveBuyLevelsPrefs(); if(blChart)blChart.update(); }
function blSyncVolumeScaleUI(){
  if(!Number.isFinite(_blVolumeScale)||_blVolumeScale<=0) _blVolumeScale=1;
  _blVolumeScale=clampNum(_blVolumeScale,0.25,2.5);
  const _vsi=document.getElementById('blVolumeScaleInput'); if(_vsi) _vsi.value=_blVolumeScale.toFixed(2);
  const _vsv=document.getElementById('blVolumeScaleValue'); if(_vsv) _vsv.textContent=_blVolumeScale.toFixed(2)+'x';
}
function blSetVolumeScale(val){
  const raw=parseFloat(val);
  if(!Number.isFinite(raw)) return;
  const next=clampNum(raw,0.25,2.5);
  const changed=Math.abs(next-_blVolumeScale)>0.0001;
  _blVolumeScale=next;
  blSyncVolumeScaleUI();
  saveBuyLevelsPrefs();
  if(changed&&blChart) blChart.update('none');
}
function blSyncVcWidthScaleUI(){
  if(!Number.isFinite(_blVcWidthScale)||_blVcWidthScale<=0) _blVcWidthScale=1;
  _blVcWidthScale=clampNum(_blVcWidthScale,0.25,3.0);
  const inp=document.getElementById('blVcWidthScaleInput'); if(inp) inp.value=_blVcWidthScale.toFixed(2);
  const lbl=document.getElementById('blVcWidthScaleValue'); if(lbl) lbl.textContent=_blVcWidthScale.toFixed(2)+'x';
  const row=document.getElementById('blVcWidthScaleRow');
  if(row) row.style.display=(_blChartType==='volcndle')?'':'none';
}
function blSetVcWidthScale(val){
  const raw=parseFloat(val);
  if(!Number.isFinite(raw)) return;
  const next=clampNum(raw,0.25,3.0);
  const changed=Math.abs(next-_blVcWidthScale)>0.0001;
  _blVcWidthScale=next;
  blSyncVcWidthScaleUI();
  saveBuyLevelsPrefs();
  if(changed&&blChart) blChart.update('none');
}
function blSetMarginTop(val){
  const v=Math.round(Number(val));
  if(Number.isFinite(v)&&v>=0){_blMarginTopPct=v;saveBuyLevelsPrefs();renderBuyLevels();}
}
function blSetMarginBot(val){
  const v=Math.round(Number(val));
  if(Number.isFinite(v)&&v>=0){_blMarginBotPct=v;saveBuyLevelsPrefs();renderBuyLevels();}
}
function blSetMarginRight(val){
  const v=parseInt(val);
  if(Number.isFinite(v)&&v>=0){_blRightBars=v;saveBuyLevelsPrefs();_blForceDefaultRange=true;renderBuyLevels();}
}
function blSetChartColorMode(mode){
  const next=String(mode||'').toLowerCase();
  if(!Object.prototype.hasOwnProperty.call(BL_CHART_COLOR_LABELS, next)) return;
  const changed=next!==_blChartColorMode;
  _blChartColorMode=next;
  blSyncIndicatorChecks();
  saveBuyLevelsPrefs();
  if(changed&&blChart) blChart.update();
}
function blSyncIndicatorChecks(){
  const set=(id,on)=>{ const el=document.getElementById(id); if(el) el.innerHTML=on?'&#10003;':''; };
  set('blIndEarningsChk',_blShowEarnings);
  set('blIndReversalsChk',_blShowReversals);
  set('blIndInsidersChk',_blShowInsiders);
  set('blIndVCChk',_blShowValueChart);
  set('blIndVwapChk',_blShowVwap);
  set('blIndMA50Chk',_blShowMA50);
  set('blIndMA200Chk',_blShowMA200);
  set('blIndVSAChk',_blShowVSA);
  set('blIndTargetLinesChk',_blShowTargetLines);
  set('blIndStopLineChk',_blShowStopLine);
  set('blIndProfileChk',_blShowProfile);
  set('blIndLookbackBarChk',_blShowLookbackBar);
  set('blIndGIReturnsChk',_blShowGIReturns);
  set('blIndGIBacktestChk',_blShowGIBacktest);
  set('blIndGISizerChk',_blShowGISizer);
  const lbBar=document.getElementById('blLookbackBar');
  if(lbBar) lbBar.style.display=_blShowLookbackBar?'flex':'none';
  const giLbl=document.getElementById('blGIBtnLbl');
  if(giLbl) giLbl.textContent=_blGIPos==='overlay'?'Overlay':_blGIPos==='off'?'Off':'Lower';
  set('blIndGIChk', _blGIPos!=='off');
  set('blIndCrosshairChk', _blShowCrosshair);
  set('blIndTooltipChk', _blShowDataTooltip);
  blSyncChartTypeUI();
  _blSyncVcGapsUI();
}
function blToggleEarnings(){ _blShowEarnings=!_blShowEarnings; blSyncIndicatorChecks(); saveBuyLevelsPrefs(); renderBuyLevels(); }
function blToggleReversals(){ _blShowReversals=!_blShowReversals; blSyncIndicatorChecks(); saveBuyLevelsPrefs(); renderBuyLevels(); }
function blToggleInsiders(){ _blShowInsiders=!_blShowInsiders; if(blChart) blChart.update(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleVSA(){ _blShowVSA=!_blShowVSA; _blVsaCache=null; blSyncIndicatorChecks(); saveBuyLevelsPrefs(); if(blChart) blChart.update('none'); }
function blToggleTargetLines(){ _blShowTargetLines=!_blShowTargetLines; blSyncIndicatorChecks(); saveBuyLevelsPrefs(); syncGIToBuyRange(); if(blChart) blChart.update('none'); }
function blToggleStopLine(){ _blShowStopLine=!_blShowStopLine; blSyncIndicatorChecks(); saveBuyLevelsPrefs(); syncGIToBuyRange(); if(blChart) blChart.update('none'); }
function blToggleValueChart(){ _blShowValueChart=!_blShowValueChart; if(blChart) blChart.update(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleVwap(){ _blShowVwap=!_blShowVwap; if(blChart) blChart.update(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleMA50(){ _blShowMA50=!_blShowMA50; if(blChart) blChart.update(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleMA200(){ _blShowMA200=!_blShowMA200; if(blChart) blChart.update(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleDataTooltip(){
  _blShowDataTooltip=!_blShowDataTooltip;
  if(!_blShowDataTooltip){
    const tip=document.getElementById('blTooltip');
    if(tip) tip.style.display='none';
  }
  blSyncIndicatorChecks();
  saveBuyLevelsPrefs();
}
function blToggleCrosshair(){
  _blShowCrosshair=!_blShowCrosshair;
  if(!_blShowCrosshair){
    _crosshairRatio=null;
    _crosshairXVal=null;
    _crosshairY=null;
    _crosshairSource='';
  }
  blSyncIndicatorChecks();
  saveBuyLevelsPrefs();
  if(blChart) blChart.draw();
  if(giHistChart) giHistChart.draw();
}
function blToggleGIPos(){ blCycleGIPos(); }
function blCycleGIPos(){
  const order=['lower','overlay','off'];
  _blGIPos=order[(order.indexOf(_blGIPos)+1)%order.length];
  blSyncIndicatorChecks();
  saveBuyLevelsPrefs();
  const _t=blCurrentTicker();
  const _pos=_blGIPos;
  // Defer so DOM can lay out before chart creation (same as startup)
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    if(_blGIPos!==_pos)return; // user clicked again, ignore stale render
    try{
      if(blChart&&blChart.options?.scales?.x){
        const showAxis=(_pos!=='lower');
        blChart.options.scales.x.display=showAxis;
        if(blChart.options.scales.x.ticks) blChart.options.scales.x.ticks.display=showAxis;
        blChart.update('none');
      }
    }catch(_e){}
    renderGIChart(_t);
    if(blChart) blChart.draw();
    _syncLookbackBarPos(blChart);
  }));
}
function blToggleProfile(){ _blShowProfile=!_blShowProfile; blRenderProfile(blCurrentTicker()); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleLookbackBar(){ _blShowLookbackBar=!_blShowLookbackBar; if(!_blShowLookbackBar) blSetLookback(0); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleGIReturns(){ _blShowGIReturns=!_blShowGIReturns; _blSyncGIPanelVis(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleGIBacktest(){ _blShowGIBacktest=!_blShowGIBacktest; _blSyncGIPanelVis(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function blToggleGISizer(){ _blShowGISizer=!_blShowGISizer; _blSyncGIPanelVis(); blSyncIndicatorChecks(); saveBuyLevelsPrefs(); }
function _blSyncGIPanelVis(){
  const rc=document.getElementById('gisp-returns-card');
  const bc=document.getElementById('gisp-backtest-card');
  const sc=document.getElementById('gisp-sizer-card');
  if(rc) rc.style.display=_blShowGIReturns?'':'none';
  if(bc) bc.style.display=_blShowGIBacktest?'':'none';
  if(sc) sc.style.display=_blShowGISizer?'':'none';
}
function blValueChartEnabled(){
  return !!_blShowValueChart && String(_blChartType||'').toLowerCase()!=='line';
}
function blShowIndicators(){
  return _blShowVwap || _blShowMA50 || _blShowMA200 || blValueChartEnabled();
}
function blShowVolume(){
  return true;
}
function blShowVSA(){
  return !!_blShowVSA;
}
function blRenderProfile(ticker){
  const el=document.getElementById('blProfileBadge');
  if(!el)return;
  if(!ticker||!_blShowProfile){el.innerHTML='';el.style.display='none';return;}
  const sym=String(ticker||'').trim().toUpperCase();
  const row=(ZR_DATA||[]).find(r=>r.ticker===sym)||{};
  const meta=BL_PROFILE_META[sym]||{};
  const name=meta.name||row.company||BL_TICKER_INFO[sym]||sym;
  const sector=meta.sector||row.sector||'';
  const industry=meta.industry||row.industry||'';
  const info=[sector,industry].filter(Boolean).join(' | ');
  el.innerHTML=`<span style="background:transparent;color:#fff;padding:2px 10px;font-weight:700;border-radius:6px 0 0 6px;max-width:320px;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 4px rgba(0,0,0,0.75)">${name}</span>`+
    (info?`<span style="background:transparent;color:#9ca3af;padding:2px 10px;border-radius:0 4px 4px 0;max-width:420px;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 4px rgba(0,0,0,0.75)">${info}</span>`:'');
  el.style.display='flex';
  const hasMeta = !!(meta.name || meta.sector || meta.industry);
  if (_profileMetaStale(sym) || (!hasMeta && !_blProfileMetaFetchedAt[sym])) {
    blEnsureProfileMeta(sym, false).then(() => {
      if (blCurrentTicker() === sym && _blShowProfile) blRenderProfile(sym);
    }).catch(() => {});
  }
}
function blSMA(values, period){
  const out=new Array(values.length).fill(null);
  if(!Array.isArray(values)||period<=0) return out;
  let sum=0;
  for(let i=0;i<values.length;i++){
    const v=Number(values[i]);
    sum += Number.isFinite(v) ? v : 0;
    if(i>=period){
      const prev=Number(values[i-period]);
      sum -= Number.isFinite(prev) ? prev : 0;
    }
    if(i>=period-1) out[i]=sum/period;
  }
  return out;
}
function blEMA(values, period){
  const out=new Array(values.length).fill(null);
  if(!Array.isArray(values)||!values.length||period<=0) return out;
  const k=2/(period+1);
  let ema=null;
  values.forEach((raw,i)=>{
    const v=Number(raw);
    if(!Number.isFinite(v)) return;
    ema=ema==null?v:(v*k+ema*(1-k));
    if(i>=period-1) out[i]=ema;
  });
  return out;
}
function blVolumeMA(period){
  return blSMA((_blOhlcv||[]).map(d=>Number(d.v)||0), period);
}
function blRollingVWAP(period){
  const out=new Array((_blOhlcv||[]).length).fill(null);
  let pv=0, vv=0;
  for(let i=0;i<(_blOhlcv||[]).length;i++){
    const d=_blOhlcv[i]||{};
    const tp=(Number(d.h)+Number(d.l)+Number(d.c))/3;
    const vol=Math.max(0, Number(d.v)||0);
    if(Number.isFinite(tp) && vol>0){ pv += tp*vol; vv += vol; }
    if(i>=period){
      const p=_blOhlcv[i-period]||{};
      const ptp=(Number(p.h)+Number(p.l)+Number(p.c))/3;
      const pvol=Math.max(0, Number(p.v)||0);
      if(Number.isFinite(ptp) && pvol>0){ pv -= ptp*pvol; vv -= pvol; }
    }
    if(i>=period-1 && vv>0) out[i]=pv/vv;
  }
  return out;
}
function blIndicatorSeries(){
  if(_blIndCache) return _blIndCache;
  const close=(_blOhlcv||[]).map(d=>Number(d.c));
  _blIndCache={
    vwap20: blRollingVWAP(20),
    sma50: blSMA(close,50),
    sma200: blSMA(close,200),
    vol20: blVolumeMA(20),
  };
  return _blIndCache;
}
function blVolumeStats(){
  if(_blVsaCache) return _blVsaCache;
  const vsaLen=20,vsaThresh=1.5,vsaSpreadLow=0.8;
  _blVsaCache=(_blOhlcv||[]).map((d,i)=>{
    const v=Number(d.v)||0;
    let signal='';
    let color='rgba(67,70,81,0.85)';
    let avgVol=null, avgRange=null, relVol=null, spreadRel=null;
    const spread=Math.max((Number(d.h)-Number(d.l))||0,0.0001);
    if(i>=vsaLen+2){
      let sumVol=0,sumRange=0;
      for(let j=0;j<vsaLen;j++){ sumVol += Number(_blOhlcv[i-j]?.v)||0; sumRange += Math.max((Number(_blOhlcv[i-j]?.h)-Number(_blOhlcv[i-j]?.l))||0,0); }
      avgVol=sumVol/vsaLen; avgRange=sumRange/vsaLen;
      relVol=avgVol>0 ? v/avgVol : null;
      spreadRel=avgRange>0 ? spread/avgRange : null;
      const isHighVol=v>(avgVol*vsaThresh);
      const isLowSpread=spread<(avgRange*vsaSpreadLow);
      const isWideSpread=spread>avgRange;
      const isLowVolSeq=v<(Number(_blOhlcv[i-1]?.v)||0) && v<(Number(_blOhlcv[i-2]?.v)||0);
      const isNarrow=spread<avgRange;
      if(isHighVol&&isLowSpread){ signal='Squat'; color='#fbc02d'; }
      else if(isHighVol&&isWideSpread){ signal='Climax'; color='#7e57c2'; }
      else if(Number(d.c)>Number(d.o)&&isLowVolSeq&&isNarrow){ signal='No Demand'; color='#ef5350'; }
      else if(Number(d.c)<Number(d.o)&&isLowVolSeq&&isNarrow){ signal='No Supply'; color='#26a69a'; }
    }
    return {vol:v, avgVol, relVol, spread, avgRange, spreadRel, signal, color};
  });
  return _blVsaCache;
}

function blGetBarSpacing(x, visibleCount){
  const step=(Number.isFinite(x.max)?Math.ceil(x.max):1)>0 ? Math.abs(x.getPixelForValue(1)-x.getPixelForValue(0)) : 0;
  return Math.max(1, step || ((x.right-x.left)/Math.max(1,visibleCount||_blOhlcv.length||1)));
}
function blBaseCandleWidth(x, visibleCount){
  const barSpacing=blGetBarSpacing(x, visibleCount);
  return Math.max(1, Math.round(barSpacing - blCandleGapPx(barSpacing)));
}
function blCandleGapPx(barSpacing){
  // Fixed gap per zoom level
  if(barSpacing<=8) return 2;
  if(barSpacing<=20) return 3;
  return Math.min(4, Math.max(2, Math.round(barSpacing * 0.04)));
}
function blMaxCandleBodyWidth(barSpacing){
  // No hard pixel cap - bars grow proportionally when zoomed in
  return Math.max(1, barSpacing - blCandleGapPx(barSpacing));
}
function blOhlcStrokeWidth(x, visibleCount){
  const barSpacing=blGetBarSpacing(x, visibleCount);
  return Math.max(1, Number((barSpacing*0.14).toFixed(2)));
}
function blValueOverlayStrokeWidth(chartType, x, visibleCount){
  if(chartType==='ohlc' || chartType==='hlc'){
    return blOhlcStrokeWidth(x, visibleCount);
  }
  return 2.1;
}
function blOhlcBarGeometry(px, d, chart, y, cw, chartType, alignWidth){
  const wickX=blAlignCanvasPx(px, chart, alignWidth);
  const wickTop=blAlignCanvasPx(y.getPixelForValue(d.h), chart, alignWidth);
  const wickBot=blAlignCanvasPx(y.getPixelForValue(d.l), chart, alignWidth);
  const openY=blAlignCanvasPx(y.getPixelForValue(d.o), chart, alignWidth);
  const closeY=blAlignCanvasPx(y.getPixelForValue(d.c), chart, alignWidth);
  const tickLen=chartType==='hollow' ? 0 : Math.max(4, Math.round(cw*0.48));
  const leftTick=blAlignCanvasPx(px-tickLen, chart, alignWidth);
  const rightTick=blAlignCanvasPx(px+tickLen, chart, alignWidth);
  return {wickX, wickTop, wickBot, openY, closeY, leftTick, rightTick, tickLen};
}
function blBarStrokeColor(i, d, chartType){
  if(chartType==='line') return UI.hollowCandle;
  if(_blChartColorMode==='neutral') return _blNeutralColor;
  if(_blChartColorMode==='open'){
    const open=Number(d?.o);
    const close=Number(d?.c);
    if(!Number.isFinite(open) || !Number.isFinite(close)) return UI.hollowCandle;
    if(close>open) return _blUpColor;
    if(close<open) return _blDownColor;
    return UI.hollowCandle;
  }
  if(_blChartColorMode!=='change') return UI.hollowCandle;
  const cur=Number(_blOhlcv?.[i]?.c);
  const prev=Number(_blOhlcv?.[i-1]?.c);
  if(!Number.isFinite(cur) || !Number.isFinite(prev)) return UI.hollowCandle;
  if(cur>prev) return _blUpColor;
  if(cur<prev) return _blDownColor;
  return UI.hollowCandle;
}
function blFormatPriceAxis(v){
  const n=Number(v);
  if(!Number.isFinite(n)) return '';
  return '$'+n.toFixed(2);
}
function blFormatSignedMoney(v){
  const raw=Number(v);
  if(!Number.isFinite(raw)) return '';
  const n=Math.abs(raw)<1e-9?0:raw;
  const sign=n>0?'+':n<0?'-':'';
  return `${sign}$${Math.abs(n).toFixed(2)}`;
}
function blFormatSignedPct(v,decimals=1){
  const raw=Number(v);
  if(!Number.isFinite(raw)) return '';
  const n=Math.abs(raw)<1e-9?0:raw;
  const sign=n>0?'+':n<0?'-':'';
  return `${sign}${Math.abs(n).toFixed(decimals)}%`;
}
function blTodayChangeSnapshot(){
  const sym=blCurrentTicker();
  if(!sym) return null;
  const bars=(Array.isArray(_blOhlcv)&&_blOhlcv.length)?_blOhlcv:(CANDLE_DATA[sym]||[]);
  const snap=blSymbolChangeSnapshot(sym,bars);
  if(!snap) return null;
  const delta=Number(snap.delta);
  const pct=Number(snap.pct);
  if(!Number.isFinite(delta)||!Number.isFinite(pct)) return null;
  return {delta,pct};
}
function blCrosshairSourceChart(){
  return _crosshairSource==='gi' ? giHistChart : blChart;
}
function blCrosshairClampedRatio(){
  return clampNum(_crosshairRatio==null?0:_crosshairRatio,0,1);
}
function blFmtIsoDateLocal(dt){
  const y=dt.getFullYear();
  const m=String(dt.getMonth()+1).padStart(2,'0');
  const d=String(dt.getDate()).padStart(2,'0');
  return `${y}-${m}-${d}`;
}
function blShiftTradingDate(dateStr, offset){
  const base=new Date(`${dateStr}T12:00:00`);
  if(!Number.isFinite(base.getTime())) return dateStr||'';
  const dir=offset>=0?1:-1;
  let rem=Math.abs(Math.round(offset));
  while(rem>0){
    base.setDate(base.getDate()+dir);
    const day=base.getDay();
    if(day!==0 && day!==6) rem--;
  }
  return blFmtIsoDateLocal(base);
}
function blCrosshairXValue(){
  if(Number.isFinite(_crosshairXVal)) return _crosshairXVal;
  if(_crosshairRatio===null||!_blOhlcv.length) return null;
  const chart=blChart||giHistChart;
  const x=chart?.scales?.x;
  const area=chart?.chartArea;
  if(!x||!area) return null;
  const px=area.left + blCrosshairClampedRatio()*(area.right-area.left);
  const v=x.getValueForPixel(px);
  return Number.isFinite(v)?v:null;
}
function blCrosshairXPixel(chart){
  if(!chart||_crosshairRatio===null) return null;
  const area=chart.chartArea;
  if(!area) return null;
  // Use ratio (fractional position within the plot area) rather than a
  // per-chart getPixelForValue() call.  Both charts share the same ratio
  // so the line always lands at the same proportional position regardless
  // of differing chartArea.left values caused by y-axis label width differences.
  const px=area.left + clampNum(_crosshairRatio,0,1)*(area.right-area.left);
  return Number.isFinite(px)?blAlignCanvasPx(px, chart, 1):null;
}
function blCrosshairDateIdx(){
  const xVal=blCrosshairXValue();
  if(xVal==null||!_blOhlcv.length) return null;
  return clampNum(Math.round(xVal),0,_blOhlcv.length-1);
}
function blFormatCrosshairDate(isoStr){
  if(!isoStr) return '';
  const mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const t=String(isoStr).slice(0,10);
  const y=t.slice(0,4), m=parseInt(t.slice(5,7),10)-1, d=parseInt(t.slice(8,10),10);
  return mo[m]+' '+d+', '+y;
}
function blCrosshairDateText(){
  const xVal=blCrosshairXValue();
  if(xVal==null||!_blOhlcv.length) return '';
  const idx=Math.round(xVal);
  if(idx>=0 && idx<_blOhlcv.length) return blFormatCrosshairDate(_blOhlcv[idx]?.t||'');
  if(idx>=_blOhlcv.length) return blFormatCrosshairDate(blShiftTradingDate(_blOhlcv[_blOhlcv.length-1]?.t||'', idx-(_blOhlcv.length-1)));
  return blFormatCrosshairDate(blShiftTradingDate(_blOhlcv[0]?.t||'', idx));
}
function blCrosshairYText(chart){
  if(_crosshairY===null||!chart) return '';
  if(chart===blChart && _crosshairSource==='buy'){
    return blFormatPriceAxis(chart.scales.y.getValueForPixel(_crosshairY));
  }
  if(chart===giHistChart && _crosshairSource==='gi'){
    const v=chart.scales.y.getValueForPixel(_crosshairY);
    return Number.isFinite(v)?('GI '+v.toFixed(1)):'';
  }
  return '';
}
function blCrosshairYColor(chart){
  if(chart===giHistChart && _crosshairSource==='gi' && _crosshairY!==null){
    const v=chart.scales.y.getValueForPixel(_crosshairY);
    return Number.isFinite(v)?giColorForValue(v):'#f3f4f6';
  }
  return '#f3f4f6';
}
function blCrosshairShowsXAxis(chart){
  return chart===giHistChart ? _blGIPos==='lower' : _blGIPos!=='lower';
}
function blDrawCrosshairTag(chart, x, y, text, opts={}){
  if(!chart||!text) return;
  const ctx=chart.ctx;
  const padX=opts.padX||7;
  const padY=opts.padY||4;
  const radius=opts.radius!=null?opts.radius:6;
  const font=opts.font||'600 10px JetBrains Mono,monospace';
  ctx.save();
  ctx.font=font;
  const tm=ctx.measureText(text);
  const textH=Math.max(10,(tm.actualBoundingBoxAscent||7)+(tm.actualBoundingBoxDescent||3));
  const w=Math.ceil(tm.width)+padX*2;
  const h=Math.ceil(textH)+padY*2;
  let left=x;
  let top=y;
  if(opts.align==='center') left-=w/2;
  else if(opts.align==='right') left-=w;
  if(opts.valign==='middle') top-=h/2;
  else if(opts.valign==='bottom') top-=h;
  left=Math.max(2,Math.min(chart.width-w-2,left));
  top=Math.max(2,Math.min(chart.height-h-2,top));
  ctx.beginPath();
  if(typeof ctx.roundRect==='function') ctx.roundRect(left,top,w,h,radius);
  else {
    ctx.moveTo(left+radius,top);
    ctx.lineTo(left+w-radius,top);
    ctx.quadraticCurveTo(left+w,top,left+w,top+radius);
    ctx.lineTo(left+w,top+h-radius);
    ctx.quadraticCurveTo(left+w,top+h,left+w-radius,top+h);
    ctx.lineTo(left+radius,top+h);
    ctx.quadraticCurveTo(left,top+h,left,top+h-radius);
    ctx.lineTo(left,top+radius);
    ctx.quadraticCurveTo(left,top,left+radius,top);
  }
  ctx.fillStyle=opts.fill||'rgba(8,10,14,0.96)';
  ctx.strokeStyle=opts.stroke||'rgba(148,163,184,0.28)';
  ctx.lineWidth=1;
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle=opts.color||'#f3f4f6';
  ctx.textAlign='left';
  ctx.textBaseline='middle';
  ctx.fillText(text,left+padX,top+h/2+0.5);
  ctx.restore();
}
function blVolumeWidthAt(i, x, visibleCount){
  // Same gap formula as candles so volume bars stay in sync at all zoom levels
  const barSpacing = blGetBarSpacing(x, visibleCount);
  return Math.max(1, Math.round(barSpacing - blCandleGapPx(barSpacing)));
}
function blCandleWidthAt(i, x, visibleCount){
  return blBaseCandleWidth(x, visibleCount);
}
function blAlignCanvasPx(v, chart, lineWidth=1){
  const dpr=Math.max(1, chart?.currentDevicePixelRatio || window.devicePixelRatio || 1);
  const scaledLine=Math.max(1, Math.round(lineWidth*dpr));
  return (Math.round(v*dpr) + (scaledLine % 2 ? 0.5 : 0)) / dpr;
}
function blStrokeBodyOutlineSegment(ctx, chart, px, cw, yTop, yBot, edge){
  const dpr=Math.max(1, chart?.currentDevicePixelRatio || window.devicePixelRatio || 1);
  const lineWidth=ctx.lineWidth||1;
  const top=blAlignCanvasPx(Math.min(yTop,yBot), chart, lineWidth);
  const bot=Math.max(top + 1/dpr, blAlignCanvasPx(Math.max(yTop,yBot), chart, lineWidth));
  if(!(bot>top)) return;
  const left=blAlignCanvasPx(px-cw/2, chart, lineWidth);
  const right=left+Math.max(1, Math.round(cw));
  ctx.beginPath();
  ctx.moveTo(left,top); ctx.lineTo(left,bot);
  ctx.moveTo(right,top); ctx.lineTo(right,bot);
  if(edge==='top'){ ctx.moveTo(left,top); ctx.lineTo(right,top); }
  else if(edge==='bottom'){ ctx.moveTo(left,bot); ctx.lineTo(right,bot); }
  else if(edge==='full'){ ctx.moveTo(left,top); ctx.lineTo(right,top); ctx.moveTo(left,bot); ctx.lineTo(right,bot); }
  // 'sides' = left+right only, no horizontal lines
  ctx.stroke();
}
function blDrawLineOverlaySegment(ctx, chart, ax, ay, bx, by, lineWidth=2){
  ctx.save();
  const area=chart?.chartArea;
  if(area){
    ctx.beginPath();
    ctx.rect(area.left, area.top, area.right-area.left, area.bottom-area.top);
    ctx.clip();
  }
  ctx.lineWidth=lineWidth;
  ctx.lineCap='round';
  ctx.lineJoin='round';
  ctx.beginPath();
  ctx.moveTo(blAlignCanvasPx(ax, chart, lineWidth), blAlignCanvasPx(ay, chart, lineWidth));
  ctx.lineTo(blAlignCanvasPx(bx, chart, lineWidth), blAlignCanvasPx(by, chart, lineWidth));
  ctx.stroke();
  ctx.restore();
}

const yAxisBackgroundPlugin={
  id:'yAxisBackground',
  beforeDraw(chart){
    const {ctx,chartArea,scales}=chart;
    if(!chartArea||!scales.y) return;
    const y=scales.y;
    // Fill the Y-axis strip with the chart background so candles are clipped behind it
    ctx.save();
    ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()||'#000000';
    ctx.fillRect(chartArea.right, chartArea.top, chart.width-chartArea.right, chartArea.bottom-chartArea.top);
    ctx.restore();
  }
};
// Returns a Map of barIndex → {cx, w} for volcndle consistent-gap layout.
// Bars are placed left-to-right with a fixed gap between them; widths are
// sqrt-scaled relative to the median visible volume.
function _buildVcLayout(chart){
  // Lay bars out left-to-right with a FIXED gap between every adjacent pair.
  // Widths are sqrt-scaled relative to median visible volume, then proportionally
  // scaled so that (sum of all widths) + (n-1)*fixedGap = total available pixels.
  // This gives truly consistent spacing regardless of bar width.
  const x=chart?.scales?.x;
  if(!x||!_blOhlcv.length) return null;
  const visLo=Math.max(0,Math.floor(Number.isFinite(x.min)?x.min:0));
  const visHi=Math.min(_blOhlcv.length-1,Math.ceil(Number.isFinite(x.max)?x.max:_blOhlcv.length-1));
  const n=visHi-visLo+1;
  if(n<=0) return null;
  // Total pixel span for the visible bars (slot edges)
  const pxLeft=x.getPixelForValue(visLo-0.5);
  const pxRight=x.getPixelForValue(visHi+0.5);
  const totalW=pxRight-pxLeft;
  if(totalW<=2) return null;
  // Per-slot width → use as basis for gap size
  const slotW=totalW/n;
  const fixedGap=Math.max(1, Math.round(slotW*0.18));
  // Volumes and median
  const volArr=[];
  for(let i=visLo;i<=visHi;i++){
    const v=Number(_blOhlcv[i]?.v);
    volArr.push(Number.isFinite(v)&&v>0?v:null);
  }
  const validVols=volArr.filter(v=>v!==null).sort((a,b)=>a-b);
  if(!validVols.length) return null;
  const medVol=validVols[Math.floor(validVols.length/2)];
  // Raw widths: sqrt-scaled, exponent driven by _blVcWidthScale
  // scale=1 → sqrt; scale>1 → more contrast; scale<1 → flatter
  const vcExp=Math.max(0.1, (_blVcWidthScale||1)*0.5);
  const rawW=volArr.map(v=>{
    const ratio=v!=null?(v/medVol):1;
    return Math.max(1, slotW*Math.pow(ratio, vcExp));
  });
  // Scale raw widths so they fit: sum(rawW)*scale + fixedGap*(n-1) = totalW
  const sumRaw=rawW.reduce((a,b)=>a+b,0);
  const availForBars=Math.max(n, totalW-fixedGap*(n-1));
  const scale=availForBars/sumRaw;
  const widths=rawW.map(w=>Math.max(1,Math.round(w*scale)));
  // Sequential layout: place each bar left-to-right with fixedGap between them
  const map=new Map();
  let cursor=pxLeft;
  for(let i=0;i<n;i++){
    const w=widths[i];
    const cx=cursor+w/2;
    map.set(visLo+i,{cx,w});
    cursor+=w+fixedGap;
  }
  return map;
}
const wickPlugin={
  id:'wickPlugin',
  afterDatasetsDraw(chart){
    if(!_blOhlcv.length)return;
    const {ctx,scales:{x,y},chartArea}=chart;
    const visibleCount=Math.max(1, Math.abs((Number.isFinite(x.max)?x.max:_blOhlcv.length-1) - (Number.isFinite(x.min)?x.min:0)) + 1);
    ctx.save();
    ctx.beginPath();
    ctx.rect(chartArea.left, chartArea.top, chartArea.right-chartArea.left, chartArea.bottom-chartArea.top);
    ctx.clip();
    // Pre-compute value chart bands (drawn AFTER candles so they overlay on top)
    let vcBands=null;
    if(blValueChartEnabled()&&_blOhlcv.length>5){
      const vcLen=5,vcExt=8;
      vcBands=[];
      for(let i=vcLen-1;i<_blOhlcv.length;i++){
        let sumBasis=0,sumRange=0;
        for(let j=0;j<vcLen;j++){ const b=_blOhlcv[i-j]; sumBasis+=((Number(b.h)+Number(b.l))/2); sumRange+=Math.max((Number(b.h)-Number(b.l))||0,0); }
        const basis=sumBasis/vcLen, rangeAvg=sumRange/vcLen, volUnit=rangeAvg*0.2;
        vcBands[i]={top:basis+vcExt*volUnit,bot:basis-vcExt*volUnit};
      }
    }
    const chartType=String(_blChartType||'hollow').toLowerCase();
    if(chartType==='volcndle'){
      const visLo=Math.max(0,Math.floor(Number.isFinite(x.min)?x.min:0));
      const visHi=Math.min(_blOhlcv.length-1,Math.ceil(Number.isFinite(x.max)?x.max:_blOhlcv.length-1));
      const vols=[];
      for(let vi=visLo;vi<=visHi;vi++){ const v=Number(_blOhlcv[vi]?.v); if(Number.isFinite(v)&&v>0) vols.push(v); }
      vols.sort((a,b)=>a-b);
      const medianVol=vols.length?vols[Math.floor(vols.length/2)]:1;
      const barSpacing=blGetBarSpacing(x,visibleCount);
      const normWidth=Math.max(3, barSpacing*0.55);
      const maxBodyW=Math.max(4, barSpacing*0.92);
      const minBodyW=Math.max(2, Math.round(barSpacing*0.10));
      const _vcLayout=_blVcConsistentGaps?_buildVcLayout(chart):null;
      _blOhlcv.forEach((d,i)=>{
        const _vcBar=_vcLayout?_vcLayout.get(i):null;
        const px=_vcBar?_vcBar.cx:x.getPixelForValue(i);
        if(px<x.left-maxBodyW||px>x.right+maxBodyW) return;
        const vol=Number(d?.v);
        const cw=_vcBar?_vcBar.w:Math.max(minBodyW, Math.min(maxBodyW, Math.round(normWidth*(Number.isFinite(vol)&&vol>0?(vol/medianVol):1))));
        const openY=y.getPixelForValue(d.o), closeY=y.getPixelForValue(d.c);
        const highY=y.getPixelForValue(d.h), lowY=y.getPixelForValue(d.l);
        const isUp=Number(d.c)>=Number(d.o);
        const bodyTop=Math.min(openY,closeY), bodyBot=Math.max(openY,closeY);
        const vcStyle=_blVcFilled?'candle':'hollow';
        const color=blBarStrokeColor(i,d,vcStyle);
        const alignW=1;
        const apx=blAlignCanvasPx(px,chart,alignW);
        const atop=blAlignCanvasPx(bodyTop,chart,alignW);
        const abot=Math.max(atop+1,blAlignCanvasPx(bodyBot,chart,alignW));
        const aleft=blAlignCanvasPx(px-cw/2,chart,alignW);
        const abodyW=Math.max(1,Math.round(cw));
        ctx.fillStyle=color;
        ctx.strokeStyle=color;
        ctx.lineWidth=1;
        if(_blVcFilled){
          ctx.fillRect(aleft,atop,abodyW,abot-atop);
        } else {
          if(isUp){ ctx.strokeRect(aleft,atop,abodyW,abot-atop); }
          else{ ctx.fillRect(aleft,atop,abodyW,abot-atop); }
        }
        ctx.beginPath();
        ctx.moveTo(apx,blAlignCanvasPx(highY,chart,alignW));
        ctx.lineTo(apx,atop);
        ctx.moveTo(apx,abot);
        ctx.lineTo(apx,blAlignCanvasPx(lowY,chart,alignW));
        ctx.stroke();
      });
    }
    if(chartType==='candle' || chartType==='hollow' || chartType==='ohlc' || chartType==='hlc'){
      _blOhlcv.forEach((d,i)=>{
        const dpr=Math.max(1, chart?.currentDevicePixelRatio || window.devicePixelRatio || 1);
        const cw=Math.max(2, Math.round(blCandleWidthAt(i, x, visibleCount)));
        const px=x.getPixelForValue(i);
        if(px<x.left-cw||px>x.right+cw)return;
        const lineWidth=(chartType==='hollow'||chartType==='candle') ? 1 : blOhlcStrokeWidth(x, visibleCount);
        const geom=blOhlcBarGeometry(px, d, chart, y, cw, chartType, lineWidth);
        const color=blBarStrokeColor(i, d, chartType);
        ctx.strokeStyle=color;
        ctx.lineWidth=lineWidth;
        if(chartType==='candle' || chartType==='hollow'){
          const oY=y.getPixelForValue(d.o),cY=y.getPixelForValue(d.c);
          const bodyTop=blAlignCanvasPx(Math.min(oY,cY), chart, lineWidth);
          const bodyBot=Math.max(bodyTop + 1/dpr, blAlignCanvasPx(Math.max(oY,cY), chart, lineWidth));
          const bodyLeft=blAlignCanvasPx(px-cw/2, chart, lineWidth);
          const bodyW=Math.max(1, Math.round(cw));
          // hollow: down vs prev close = solid; up vs prev close = hollow
          // candle: always solid filled
          const prevClose=i>0?Number(_blOhlcv[i-1]?.c):NaN;
          const downVsPrev=Number.isFinite(prevClose)&&Number(d.c)<prevClose;
          const fillBody=chartType==='candle'||downVsPrev;
          ctx.beginPath();
          ctx.moveTo(geom.wickX,geom.wickTop);ctx.lineTo(geom.wickX,bodyTop);
          ctx.moveTo(geom.wickX,bodyBot);ctx.lineTo(geom.wickX,geom.wickBot);
          ctx.stroke();
          if(fillBody){
            ctx.fillStyle=color;
            ctx.fillRect(bodyLeft,bodyTop,bodyW,bodyBot-bodyTop);
          }else{
            ctx.strokeRect(bodyLeft,bodyTop,bodyW,bodyBot-bodyTop);
          }
        }else{
          ctx.beginPath();
          ctx.moveTo(geom.wickX,geom.wickTop);ctx.lineTo(geom.wickX,geom.wickBot);
          if(chartType==='ohlc'){ ctx.moveTo(geom.leftTick,geom.openY);ctx.lineTo(geom.wickX,geom.openY); }
          ctx.moveTo(geom.wickX,geom.closeY);ctx.lineTo(geom.rightTick,geom.closeY);
          ctx.stroke();
        }
      });
    }
    // Draw value chart extensions ON TOP of candles
    // Wick portions get a thin 1.5px line; body-overlap portions stay outline-only
    if(vcBands){
      ctx.strokeStyle=blHexToRgba(_blVCColor,0.90);
      if(chartType==='line'){
        const lineWidth=2.1;
        for(let i=1;i<_blOhlcv.length;i++){
          const prev=_blOhlcv[i-1];
          const cur=_blOhlcv[i];
          const prevBand=vcBands[i-1];
          const curBand=vcBands[i];
          if(!prevBand||!curBand) continue;
          const x1=x.getPixelForValue(i-1), x2=x.getPixelForValue(i);
          if((x1<x.left&&x2<x.left)||(x1>x.right&&x2>x.right)) continue;
          const c1=Number(prev.c), c2=Number(cur.c);
          if(!(Number.isFinite(c1)&&Number.isFinite(c2))) continue;
          const y1=y.getPixelForValue(c1), y2=y.getPixelForValue(c2);
          const top1=Number(prevBand.top), top2=Number(curBand.top);
          const bot1=Number(prevBand.bot), bot2=Number(curBand.bot);
          if(Number.isFinite(top1)&&Number.isFinite(top2)){
            const s1=c1-top1, s2=c2-top2;
            if(s1>0 || s2>0){
              let ax=x1, ay=y1, bx=x2, by=y2;
              if(!(s1>0)){
                const t=(0-s1)/Math.max(1e-9,(s2-s1));
                ax=x1+(x2-x1)*t; ay=y1+(y2-y1)*t;
              }
              if(!(s2>0)){
                const t=(0-s1)/Math.max(1e-9,(s2-s1));
                bx=x1+(x2-x1)*t; by=y1+(y2-y1)*t;
              }
              blDrawLineOverlaySegment(ctx, chart, ax, ay, bx, by, lineWidth);
            }
          }
          if(Number.isFinite(bot1)&&Number.isFinite(bot2)){
            const s1=c1-bot1, s2=c2-bot2;
            if(s1<0 || s2<0){
              let ax=x1, ay=y1, bx=x2, by=y2;
              if(!(s1<0)){
                const t=(0-s1)/Math.max(1e-9,(s2-s1));
                ax=x1+(x2-x1)*t; ay=y1+(y2-y1)*t;
              }
              if(!(s2<0)){
                const t=(0-s1)/Math.max(1e-9,(s2-s1));
                bx=x1+(x2-x1)*t; by=y1+(y2-y1)*t;
              }
              blDrawLineOverlaySegment(ctx, chart, ax, ay, bx, by, lineWidth);
            }
          }
        }
        ctx.restore();
        return;
      }
      // Pre-compute volcndle width params so the overlay matches the bars exactly
      let _vcVolMeta=null;
      let _vcOverlayLayout=null;
      if(chartType==='volcndle'){
        if(_blVcConsistentGaps){
          _vcOverlayLayout=_buildVcLayout(chart);
        } else {
          const visLo=Math.max(0,Math.floor(Number.isFinite(x.min)?x.min:0));
          const visHi=Math.min(_blOhlcv.length-1,Math.ceil(Number.isFinite(x.max)?x.max:_blOhlcv.length-1));
          const vvols=[];
          for(let vi=visLo;vi<=visHi;vi++){const v=Number(_blOhlcv[vi]?.v);if(Number.isFinite(v)&&v>0)vvols.push(v);}
          vvols.sort((a,b)=>a-b);
          const medVol=vvols.length?vvols[Math.floor(vvols.length/2)]:1;
          const bspc=blGetBarSpacing(x,visibleCount);
          _vcVolMeta={medVol,norm:Math.max(3,bspc*0.55),maxW:Math.max(4,bspc*0.92),minW:Math.max(2,Math.round(bspc*0.10))};
        }
      }
      _blOhlcv.forEach((d,i)=>{
        const band=vcBands[i]; if(!band) return;
        const _vcBar=_vcOverlayLayout?_vcOverlayLayout.get(i):null;
        const px=_vcBar?_vcBar.cx:x.getPixelForValue(i);
        // Use volume-proportional width for volcndle, standard width otherwise
        const cw=_vcBar?_vcBar.w:_vcVolMeta
          ? Math.max(_vcVolMeta.minW, Math.min(_vcVolMeta.maxW, Math.round(_vcVolMeta.norm*((Number(d.v)>0?Number(d.v):_vcVolMeta.medVol)/_vcVolMeta.medVol))))
          : Math.max(2, Math.round(blCandleWidthAt(i, x, visibleCount)));
        if(px<x.left-cw||px>x.right+cw) return;
        if(chartType==='ohlc'||chartType==='hlc'){
          const alignWidth=blOhlcStrokeWidth(x, visibleCount);
          const lineWidth=blValueOverlayStrokeWidth(chartType, x, visibleCount);
          const geom=blOhlcBarGeometry(px, d, chart, y, cw, chartType, alignWidth);
          if(Number(d.h)>band.top){
            const extTop=geom.wickTop;
            const extBot=blAlignCanvasPx(y.getPixelForValue(band.top), chart, alignWidth);
            if(extTop<extBot){
              ctx.beginPath();ctx.lineWidth=lineWidth;
              ctx.moveTo(geom.wickX,extTop);ctx.lineTo(geom.wickX,extBot);ctx.stroke();
            }
            if(chartType==='ohlc' && Number(d.o)>band.top){
              ctx.beginPath();ctx.lineWidth=lineWidth;
              ctx.moveTo(geom.leftTick,geom.openY);ctx.lineTo(geom.wickX,geom.openY);ctx.stroke();
            }
            if(Number(d.c)>band.top){
              ctx.beginPath();ctx.lineWidth=lineWidth;
              ctx.moveTo(geom.wickX,geom.closeY);ctx.lineTo(geom.rightTick,geom.closeY);ctx.stroke();
            }
          }
          if(Number(d.l)<band.bot){
            const extTop=blAlignCanvasPx(y.getPixelForValue(band.bot), chart, alignWidth);
            const extBot=geom.wickBot;
            if(extBot>extTop){
              ctx.beginPath();ctx.lineWidth=lineWidth;
              ctx.moveTo(geom.wickX,extTop);ctx.lineTo(geom.wickX,extBot);ctx.stroke();
            }
            if(chartType==='ohlc' && Number(d.o)<band.bot){
              ctx.beginPath();ctx.lineWidth=lineWidth;
              ctx.moveTo(geom.leftTick,geom.openY);ctx.lineTo(geom.wickX,geom.openY);ctx.stroke();
            }
            if(Number(d.c)<band.bot){
              ctx.beginPath();ctx.lineWidth=lineWidth;
              ctx.moveTo(geom.wickX,geom.closeY);ctx.lineTo(geom.rightTick,geom.closeY);ctx.stroke();
            }
          }
          return;
        }
        // hollow and candle (and volcndle): use lineWidth=1 geometry
        const alignW1=1;
        const geomType=(chartType==='volcndle')?(_blVcFilled?'candle':'hollow'):chartType;
        const geom=blOhlcBarGeometry(px, d, chart, y, cw, geomType, alignW1);
        const bodyTop=Math.min(blAlignCanvasPx(y.getPixelForValue(d.o),chart,alignW1), blAlignCanvasPx(y.getPixelForValue(d.c),chart,alignW1));
        const bodyBot=Math.max(blAlignCanvasPx(y.getPixelForValue(d.o),chart,alignW1), blAlignCanvasPx(y.getPixelForValue(d.c),chart,alignW1));
        const bodyLeft=blAlignCanvasPx(px-cw/2, chart, alignW1);
        const bodyW=Math.max(1, Math.round(cw));
        // Per-bar: detect whether this individual bar is solid-filled or hollow.
        // In hollow mode: down vs prev close = solid fill; up vs prev close = hollow outline.
        const prevClose=i>0?Number(_blOhlcv[i-1]?.c):NaN;
        const isBarSolid=(chartType==='candle')||(chartType==='volcndle'&&_blVcFilled)||((chartType==='hollow'||(chartType==='volcndle'&&!_blVcFilled))&&Number.isFinite(prevClose)&&Number(d.c)<prevClose);
        // Body overlap rendering:
        //   solid bar  ? fill overlap region + horizontal cross at band boundary (clearly visible)
        //   hollow bar ? vertical sides only; NO fill, NO horizontal inside the hollow area
        const vcBodyOverlay=(yTop,yBot,bandLinePx)=>{
          if(!(yBot>yTop)) return;
          if(isBarSolid){
            ctx.fillStyle=blHexToRgba(_blVCColor,0.90);
            ctx.fillRect(bodyLeft,yTop,bodyW,yBot-yTop);
          }else{
            // Hollow bar: only side verticals - no horizontal inside the hollow area
            ctx.lineWidth=1.5;
            blStrokeBodyOutlineSegment(ctx,chart,geom.wickX,cw,yTop,yBot,'sides');
          }
        };
        // Top extension: candle high exceeds value chart ceiling
        if(Number(d.h)>band.top){
          const extTop=geom.wickTop;
          const extBot=blAlignCanvasPx(y.getPixelForValue(band.top), chart, alignW1);
          const wickBot=Math.min(extBot, bodyTop);
          // Wick portion (above body): vertical orange line
          if(extTop<wickBot){
            ctx.beginPath();ctx.lineWidth=1.5;
            ctx.moveTo(geom.wickX,extTop);ctx.lineTo(geom.wickX,wickBot);ctx.stroke();
          }
          // Hollow bar: horizontal cap at body-top where the wick orange meets the body
          if(!isBarSolid&&extBot>=bodyTop){
            ctx.beginPath();ctx.lineWidth=1.5;
            ctx.moveTo(bodyLeft,bodyTop);ctx.lineTo(bodyLeft+bodyW,bodyTop);ctx.stroke();
          }
          // Body overlap
          if(extBot>bodyTop){
            vcBodyOverlay(Math.max(extTop,bodyTop), Math.min(extBot,bodyBot), extBot);
          }
        }
        // Bottom extension: candle low falls below value chart floor
        if(Number(d.l)<band.bot){
          const extTop=blAlignCanvasPx(y.getPixelForValue(band.bot), chart, alignW1);
          const extBot=geom.wickBot;
          const wickTop=Math.max(extTop, bodyBot);
          // Body overlap
          if(extTop<bodyBot){
            vcBodyOverlay(Math.max(extTop,bodyTop), Math.min(extBot,bodyBot), extTop);
          }
          // Hollow bar: horizontal cap at body-bottom where the wick orange meets the body
          if(!isBarSolid&&extTop<=bodyBot){
            ctx.beginPath();ctx.lineWidth=1.5;
            ctx.moveTo(bodyLeft,bodyBot);ctx.lineTo(bodyLeft+bodyW,bodyBot);ctx.stroke();
          }
          // Wick portion (below body): vertical orange line
          if(extBot>wickTop){
            ctx.beginPath();ctx.lineWidth=1.5;
            ctx.moveTo(geom.wickX,wickTop);ctx.lineTo(geom.wickX,extBot);ctx.stroke();
          }
        }
      });
    }
    ctx.restore();
  }
};

const buyLinePlugin={
  id:'buyLinePlugin',
  afterDatasetsDraw(chart){
    if(!_blShowInsiders||!_blBuys.length)return;
    const {ctx,scales:{x,y}}=chart;
    const vcLayout=(String(_blChartType||'').toLowerCase()==='volcndle'&&_blVcConsistentGaps)
      ?_buildVcLayout(chart):null;
    ctx.save();
    _blBuys.forEach(b=>{
      const vcBar=vcLayout?vcLayout.get(b._idx):null;
      const xPx=vcBar?vcBar.cx:x.getPixelForValue(b._idx);
      if(xPx<x.left||xPx>x.right)return;
      const yPx=y.getPixelForValue(b.price);
      ctx.beginPath();
      ctx.arc(xPx,yPx,5.0,0,Math.PI*2);
      ctx.fillStyle=_blInsiderDotColor;
      ctx.fill();
      ctx.strokeStyle='rgba(0,0,0,0.5)';
      ctx.lineWidth=0.8;
      ctx.stroke();
    });
    ctx.restore();
  }
};

const priceLabelPlugin={
  id:'priceLabelPlugin',
  afterDraw(chart){
    if(chart!==blChart) return;
    if(!_blOhlcv.length) return;
    const {ctx,chartArea:{left,right},scales}=chart;
    const y=scales?.y;
    if(!y) return;
    const last=_blOhlcv[_blOhlcv.length-1];
    const price=Number(last?.c);
    if(!Number.isFinite(price)) return;
    const py=y.getPixelForValue(price);
    if(py<y.top||py>y.bottom) return;
    // Color by direction vs previous close
    const prev=_blOhlcv.length>1?Number(_blOhlcv[_blOhlcv.length-2]?.c):price;
    const isUp=price>=prev;
    const lineCol=isUp?'rgba(67,160,71,0.55)':'rgba(229,57,53,0.55)';
    const markerFill=isUp?'#2E7D32':'#C62828';
    // Draw horizontal dotted line across full chart width
    ctx.save();
    ctx.strokeStyle=lineCol;
    ctx.lineWidth=1;
    ctx.setLineDash([2,2]);
    ctx.beginPath();
    ctx.moveTo(left,py);
    ctx.lineTo(right,py);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
    const txt=blFormatPriceAxis(price);
    blDrawCrosshairTag(chart,right+6,py,txt,{align:'left',valign:'middle',color:'#ffffff',fill:markerFill,stroke:markerFill,padX:4,radius:0});
  }
};
const todayChangePlugin={
  id:'todayChangePlugin',
  afterDraw(chart){
    if(chart!==blChart) return;
    const snap=blTodayChangeSnapshot();
    if(!snap) return;
    const delta=Number(snap.delta);
    const pct=Number(snap.pct);
    if(!Number.isFinite(delta)||!Number.isFinite(pct)) return;
    const chgTxt=`${blFormatSignedMoney(delta)} (${blFormatSignedPct(pct,2)})`;
    if(!chgTxt) return;
    const area=chart.chartArea;
    if(!area) return;
    const last=_blOhlcv.length ? _blOhlcv[_blOhlcv.length-1] : null;
    const openPx=Number(last?.o), highPx=Number(last?.h), lowPx=Number(last?.l), closePx=Number(last?.c);
    const fmtPx=v=>Number.isFinite(v)?blFormatPriceAxis(v):'--';
    const ohlcTxt=`O:${fmtPx(openPx)} H:${fmtPx(highPx)} L:${fmtPx(lowPx)} C:${fmtPx(closePx)}`;
    const ohlcFont='400 10px JetBrains Mono,monospace';
    const chgFont='700 10px JetBrains Mono,monospace';
    const lineY=2;
    let chgX=2;
    try{
      const ctx=chart.ctx;
      ctx.save();
      ctx.font=ohlcFont;
      chgX=2+Math.ceil(ctx.measureText(ohlcTxt).width)+5;
      ctx.restore();
    }catch(_e){}
    const txtColor=delta>0?(_blUpColor||'#33AA00'):delta<0?(_blDownColor||'#CC3300'):'#d1d5db';
    blDrawCrosshairTag(chart,2,lineY,ohlcTxt,{
      align:'left',valign:'top',color:'#ffffff',
      fill:'rgba(0,0,0,0)',stroke:'rgba(0,0,0,0)',
      font:ohlcFont,padX:0,padY:0,radius:0
    });
    blDrawCrosshairTag(chart,chgX,lineY,chgTxt,{
      align:'left',valign:'top',color:txtColor,
      fill:'rgba(0,0,0,0)',stroke:'rgba(0,0,0,0)',
      font:chgFont,padX:0,padY:0,radius:0
    });
  }
};
const extendedHoursPlugin={
  id:'extendedHoursPlugin',
  afterDraw(chart){
    if(chart!==blChart) return;
    const sym=blCurrentTicker();
    if(!sym) return;
    const extPx=_blExtendedPrice[sym];
    if(!Number.isFinite(extPx)) return;
    const {ctx,chartArea:{left,right},scales}=chart;
    const y=scales?.y;
    if(!y) return;
    const py=y.getPixelForValue(extPx);
    if(py<y.top||py>y.bottom) return;
    // Golden dotted line across full chart width - no label
    ctx.save();
    ctx.strokeStyle='rgba(201,162,39,0.65)';
    ctx.lineWidth=1;
    ctx.setLineDash([2,2]);
    ctx.beginPath();
    ctx.moveTo(left,py);
    ctx.lineTo(right,py);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }
};
const crosshairPlugin={
  id:'crosshair',
  afterDraw(chart){
    if(!_blShowCrosshair) return;
    if(_crosshairRatio===null)return;
    const {ctx,chartArea:{top,bottom,left,right},scales}=chart;
    if(!scales?.x)return;
    const px=blCrosshairXPixel(chart);
    if(px==null)return;
    if(px<left-1||px>right+1)return;
    const yPx=_crosshairY===null?null:blAlignCanvasPx(_crosshairY, chart, 1);
    ctx.save();
    ctx.strokeStyle='rgba(156,176,196,0.5)';ctx.lineWidth=1;
    ctx.beginPath();
    ctx.moveTo(px,top);ctx.lineTo(px,bottom);ctx.stroke();
    const showHorizontal=yPx!==null&&chart===blCrosshairSourceChart();
    if(showHorizontal){
      ctx.beginPath();
      ctx.moveTo(left,yPx);ctx.lineTo(right,yPx);ctx.stroke();
    }
    ctx.restore();
    if(blCrosshairShowsXAxis(chart)){
      const dateTxt=blCrosshairDateText();
      if(dateTxt) blDrawCrosshairTag(chart,px,bottom+6,dateTxt,{align:'center',valign:'top',color:'#f3f4f6'});
    }
    if(showHorizontal){
      const yTxt=blCrosshairYText(chart);
      if(yTxt) blDrawCrosshairTag(chart,right+6,yPx,yTxt,{align:'left',valign:'middle',color:blCrosshairYColor(chart),stroke:'rgba(148,163,184,0.34)'});
    }
  }
};

let _blReversals=[];
let _blEarnings=[];
const _candleHollow=true;
// Signal type visual config: color + size multiplier
const _sigStyles={
  gi_rev:    {color:'#34e38a', sz:7.5, off:14},   // bright green — GI Reversal
  cust_cont: {color:'#38bdf8', sz:6.5, off:13},   // sky blue    — Continuation
};
const reversalPlugin={
  id:'reversalPlugin',
  afterDatasetsDraw(chart){
    if(!_blShowReversals||!_blReversals.length||!_blOhlcv.length)return;
    const {ctx,scales:{x,y},chartArea}=chart;
    ctx.save();
    _blReversals.forEach(r=>{
      const xPx=x.getPixelForValue(r._idx);
      const style=_sigStyles[r.t]||_sigStyles.gi_rev;
      const {color,sz,off}=style;
      if(xPx<x.left-sz||xPx>x.right+sz)return;
      // All signals are buy-side — upward triangle below the candle low
      const ohlcv=_blOhlcv[r._idx];
      const lowPrice=ohlcv?Number(ohlcv.l):NaN;
      const baseY=Number.isFinite(lowPrice)?y.getPixelForValue(lowPrice):y.getPixelForValue(r.p||0);
      const yPx=baseY+off;
      ctx.beginPath();
      ctx.moveTo(xPx,yPx-sz);
      ctx.lineTo(xPx+sz*0.75,yPx+sz*0.5);
      ctx.lineTo(xPx-sz*0.75,yPx+sz*0.5);
      ctx.closePath();
      ctx.fillStyle=color;
      ctx.fill();
    });
    ctx.restore();
  }
};
function fmtRevenue(v){
  if(v==null) return '--';
  if(Math.abs(v)>=1e12) return '$'+(v/1e12).toFixed(2)+'T';
  if(Math.abs(v)>=1e9)  return '$'+(v/1e9).toFixed(2)+'B';
  if(Math.abs(v)>=1e6)  return '$'+(v/1e6).toFixed(2)+'M';
  return '$'+v.toLocaleString();
}

function fmtBeatPct(actual,estimate){
  if(actual==null||estimate==null||!Number.isFinite(Number(actual))||!Number.isFinite(Number(estimate))||Number(estimate)===0) return '';
  const pct=((Number(actual)-Number(estimate))/Math.abs(Number(estimate))*100);
  const sign=pct>=0?'+':'';
  const col=pct>=0?UI.greenBright:UI.redBright;
  const word=pct>=0?'Beat':'Miss';
  return `<span style="color:${col};font-weight:700">${word} ${sign}${pct.toFixed(1)}%</span>`;
}
function fmtEPS(v){return v==null?'--':'$'+Number(v).toFixed(2);}
function fmtSentiment(s){
  if(s==null) return {label:'N/A',color:'#555'};
  if(s>=0.5)  return {label:'Strongly Positive',color:UI.greenBright};
  if(s>=0.2)  return {label:'Positive',color:UI.greenSoft};
  if(s>=-0.2) return {label:'Neutral',color:'#888'};
  if(s>=-0.5) return {label:'Negative',color:UI.orange};
  return {label:'Strongly Negative',color:UI.redBright};
}
function showInsiderBuyPopup(b, clientX, clientY){
  let pop=document.getElementById('insiderBuyPopup');
  if(!pop){
    pop=document.createElement('div');
    pop.id='insiderBuyPopup';
    pop.style.cssText='position:fixed;z-index:9999;max-width:300px;display:none;flex-direction:column;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.01)),#0f0f0f;border:1px solid #2f2f2f;border-radius:10px;padding:8px 12px;font-family:JetBrains Mono,monospace;font-size:11px;color:#eaeaea;box-shadow:0 18px 45px rgba(0,0,0,.55);pointer-events:none;';
    document.body.appendChild(pop);
  }
  const insiders=b.insiders&&b.insiders.length?b.insiders:[{insider:b.insider,title:b.title,value:b.value,value_fmt:b.value_fmt}];
  const multiInsider=insiders.length>1;
  const insiderRows=insiders.map(ins=>`
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px${multiInsider?';padding-top:4px;border-top:1px solid #1e1e1e':''}">
      <div>
        <div style="font-size:12px;font-weight:700;color:#fff">${escHtml(ins.insider||'')}</div>
        ${ins.title?'<div style="color:#facc15;font-size:9px;text-transform:uppercase;letter-spacing:.06em;margin-top:2px">'+escHtml(ins.title)+'</div>':''}
      </div>
      ${ins.value_fmt&&ins.value_fmt!=='$0'?'<div style="color:#aaa;font-size:10px;white-space:nowrap">'+escHtml(ins.value_fmt)+'</div>':''}
    </div>
  `).join('');
  const totalRow=multiInsider&&b.value_fmt&&b.value_fmt!=='$0'
    ?`<div style="padding-top:4px;border-top:1px solid #2f2f2f;color:#aaa">Total: <span style="color:#fff;font-weight:600">${escHtml(b.value_fmt)}</span></div>`:'';
  pop.innerHTML=`
    <div style="display:flex;flex-direction:column;gap:3px;line-height:1.3">
      ${insiderRows}
      ${totalRow}
    </div>
  `;
  const margin=12;
  pop.style.display='flex';
  pop.style.left='-10000px';
  pop.style.top='0px';
  const rect=pop.getBoundingClientRect();
  let lx=clientX+margin, ty=clientY-20;
  if(lx+rect.width+margin>window.innerWidth) lx=clientX-rect.width-margin;
  if(ty+rect.height+margin>window.innerHeight) ty=window.innerHeight-rect.height-margin;
  if(ty<margin) ty=margin;
  if(lx<margin) lx=margin;
  pop.style.left=Math.round(lx)+'px';
  pop.style.top=Math.round(ty)+'px';
}
function earningsPopupSection(label, text){
  const clean=String(text??'').trim();
  if(!clean) return '';
  return `
    <div style="display:flex;flex-direction:column;gap:4px">
      <div style="color:#767676;font-size:9px;text-transform:uppercase;letter-spacing:.08em">${label}</div>
      <div style="color:#d7d7d7;white-space:pre-wrap;word-break:break-word;line-height:1.45">${escHtml(clean)}</div>
    </div>
  `;
}
function showEarningsPopup(e, clientX, clientY){
  let pop=document.getElementById('earningsPopup');
  if(!pop){
    pop=document.createElement('div');
    pop.id='earningsPopup';
    pop.style.cssText='position:fixed;z-index:9999;max-width:340px;max-height:82vh;display:none;flex-direction:column;overflow:hidden;background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01)), #0f0f0f;border:1px solid #2f2f2f;border-radius:10px;padding:8px 12px;font-family:JetBrains Mono,monospace;font-size:11px;color:#eaeaea;box-shadow:0 18px 45px rgba(0,0,0,.55);pointer-events:auto;';
    pop.addEventListener('click',ev=>ev.stopPropagation());
    pop.addEventListener('mousedown',ev=>ev.stopPropagation());
    pop.addEventListener('wheel',ev=>ev.stopPropagation(),{passive:true});
    document.body.appendChild(pop);
    document.addEventListener('mousedown',evt=>{
      if(!pop||pop.style.display==='none') return;
      if(pop.contains(evt.target)) return;
      pop.style.display='none';
    });
  }
  const sent=fmtSentiment(e.s);
  const timing=e.et?e.et.replace(/_/g,' '):'';
  pop.innerHTML=`
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px;flex:0 0 auto">
      <div>
        <div style="font-size:13px;font-weight:700;color:#fff">Earnings - ${fmtDateShort(e.d)}</div>
        ${timing?'<div style="color:#7a7a7a;font-size:9px;text-transform:uppercase;letter-spacing:.08em;margin-top:2px">'+timing+'</div>':''}
      </div>
      <span style="cursor:pointer;color:#888;font-size:15px;padding:0 4px" onclick="document.getElementById('earningsPopup').style.display='none'">?</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:8px;line-height:1.35;min-height:0;overflow-y:auto;overflow-x:hidden;padding-right:4px;max-height:calc(82vh - 58px);overscroll-behavior:contain">
      <div>EPS: <span style="color:#fff">${fmtEPS(e.ae)}</span> vs <span style="color:#c8c8c8">${fmtEPS(e.ee)}</span> - ${fmtBeatPct(e.ae,e.ee)}</div>
      <div>Rev: <span style="color:#fff">${fmtRevenue(e.ar)}</span> vs <span style="color:#c8c8c8">${fmtRevenue(e.er)}</span> - ${fmtBeatPct(e.ar,e.er)}</div>
      <div>Sentiment: <span style="color:${sent.color}">${e.s!=null?Number(e.s).toFixed(2):'n/a'}</span> <span style="color:#9b9b9b">(${sent.label})</span></div>
      ${earningsPopupSection('Summary', e.su)}
      ${earningsPopupSection('Guidance', e.gu)}
      ${earningsPopupSection('Risk Factors', e.rf)}
    </div>
  `;
  const margin=12;
  // Render first to measure actual size, then clamp within viewport.
  pop.style.display='flex';
  pop.style.left='-10000px';
  pop.style.top='0px';
  const rect=pop.getBoundingClientRect();

  let lx=clientX+margin;
  let ty=clientY-20;

  if(lx+rect.width+margin>window.innerWidth) lx=clientX-rect.width-margin;
  if(ty+rect.height+margin>window.innerHeight) ty=window.innerHeight-rect.height-margin;
  if(ty<margin) ty=margin;
  if(lx<margin) lx=margin;

  pop.style.left=Math.round(lx)+'px';
  pop.style.top=Math.round(ty)+'px';
}
const projectionPlugin={
  id:'projectionPlugin',
  afterDatasetsDraw(chart){
    if(!_projLines.length)return;
    const {ctx,scales:{x,y},chartArea}=chart;
    const lastIdx=_blOhlcv.length?_blOhlcv.length-1:0;
    const anchorOffset=Math.min(Math.max(0,_blProjLookback||0),Math.max(0,lastIdx));
    const anchorIdx=Math.max(0,lastIdx-anchorOffset);
    const isPast=anchorOffset>0;
    ctx.save();
    ctx.font='600 9.5px JetBrains Mono,monospace';
    ctx.textBaseline='middle';
    _projLines.forEach(p=>{
      if(p.label==='Entry')return;
      const yPx=y.getPixelForValue(p.price);
      if(yPx<y.top-2||yPx>y.bottom+2)return;
      const days=Number.isFinite(Number(p.days))?Number(p.days):0;
      let hx0,hx1,lbl;
      if(days===0&&p.label==='Target'){
        // Sizer target — drawn at anchor, gated by stop-line toggle (same as Stop)
        if(!_blShowStopLine)return;
        hx0=x.getPixelForValue(anchorIdx-1);
        hx1=x.getPixelForValue(anchorIdx+1);
        lbl='Target $'+p.price.toFixed(2);
      }else if(days===0){
        // PT Stop line — drawn at anchor
        if(!_blShowStopLine)return;
        hx0=x.getPixelForValue(anchorIdx-1);
        hx1=x.getPixelForValue(anchorIdx+1);
        lbl='Stop $'+p.price.toFixed(2);
      }else{
        // Target: hash centered on anchorIdx+days
        if(!_blShowTargetLines)return;
        const tIdx=anchorIdx+days;
        hx0=x.getPixelForValue(tIdx-1);
        hx1=x.getPixelForValue(tIdx+1);
        lbl=p.label;
      }
      // Clamp to chart area
      hx0=Math.max(chartArea.left,hx0);
      hx1=Math.min(chartArea.right,hx1);
      if(hx1<hx0)return;
      // Horizontal hash line
      ctx.beginPath();
      ctx.setLineDash([]);
      ctx.strokeStyle=p.color||'#fff';
      ctx.lineWidth=1.5;
      ctx.moveTo(hx0,yPx);
      ctx.lineTo(hx1,yPx);
      ctx.stroke();
      // Vertical tick on right end
      const tx=hx1;
      ctx.beginPath();
      ctx.moveTo(tx,yPx-4);
      ctx.lineTo(tx,yPx+4);
      ctx.lineWidth=2;
      ctx.stroke();
      // Label inside chart area only (never bleeds into y-axis space)
      const tw=ctx.measureText(lbl).width;
      const lx=tx+4;
      if(lx+tw+4<=chartArea.right){
        ctx.fillStyle='rgba(6,6,6,0.85)';
        ctx.fillRect(lx-2,yPx-7,tw+4,14);
        ctx.fillStyle=p.color||'#fff';
        ctx.fillText(lbl,lx,yPx);
      }
    });
    ctx.restore();
  }
};
const earningsPlugin={
  id:'earningsPlugin',
  afterDatasetsDraw(chart){
    if(!_blShowEarnings||!_blEarnings.length||!_blOhlcv.length)return;
    const {ctx,scales:{x},chartArea:{bottom}}=chart;
    const sz=9,pad=4;
    ctx.save();
    ctx.textAlign='center';
    ctx.textBaseline='middle';
    _blEarnings.forEach(e=>{
      const xPx=x.getPixelForValue(e._idx);
      const hw=sz*0.75,hh=sz*0.7;
      if(xPx<x.left-hw||xPx>x.right+hw)return;
      const yPx=bottom-hh-pad;
      const ae=Number(e.ae), ee=Number(e.ee);
      let col='#666';
      if(Number.isFinite(ae) && Number.isFinite(ee)) col=ae>=ee?UI.greenBright:UI.redBright;
      else if(e.s!=null) col=Number(e.s)>=0.3?UI.greenBright:Number(e.s)<=-0.3?UI.redBright:'#888';
      ctx.fillStyle=col;
      ctx.fillRect(xPx-hw,yPx-hh,hw*2,hh*2);
      ctx.font=`bold ${Math.round(hh*1.5)}px JetBrains Mono`;
      ctx.fillStyle='#000';
      ctx.fillText('E',xPx,yPx);
    });
    ctx.restore();
  }
};
const giOverlayPlugin={
  id:'giOverlayPlugin',
  afterDatasetsDraw(chart){
    if(!_blShowGI||_blGIPos!=='overlay'||!_giPts.length||!_blOhlcv.length) return;
    const {ctx,scales:{x,y},chartArea}=chart;
    const vis=_giPts.filter(p=>Number.isFinite(p.x)&&p.x>=x.min&&p.x<=x.max&&Number.isFinite(p.v));
    const src=vis.length?vis:_giPts.filter(p=>Number.isFinite(p.v));
    if(!src.length) return;
    let giMin=Math.min(...src.map(p=>p.v)), giMax=Math.max(...src.map(p=>p.v));
    if(!(giMax>giMin)){ giMin-=0.5; giMax+=0.5; }
    // Respect the actual volume panel height so the GI line stays above it
    const _chartH=Math.max(1,chartArea.bottom-chartArea.top);
    const _volPanelH=blShowVolume()
      ? Math.max(24,Math.min(_chartH*0.58,Math.max(64,Math.min(152,_chartH*0.31))*clampNum(Number(_blVolumeScale)||1,0.25,2.5)))
      : 0;
    const fullTop=chartArea.top+12;
    const fullBottom=_volPanelH>0
      ? chartArea.bottom-_volPanelH-8
      : chartArea.bottom-24;
    const availH=Math.max(48, fullBottom-fullTop);
    const overlayH=Math.max(42, availH*0.52);
    const inset=(availH-overlayH)/2;
    const top=fullTop+inset;
    const bottom=fullBottom-inset;
    const yForGI=v=>{
      const t=(v-giMin)/Math.max(0.0001,giMax-giMin);
      return bottom - t*(bottom-top);
    };
    ctx.save();
    ctx.lineWidth=Math.max(1.8,1.5);
    ctx.lineJoin='round';
    ctx.lineCap='round';
    // Draw segment-by-segment so each segment is colored by its GI value
    const visPts=_giPts.filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.v)&&p.x>=x.min-1&&p.x<=x.max+1);
    for(let i=0;i<visPts.length-1;i++){
      const a=visPts[i], b=visPts[i+1];
      const ax=x.getPixelForValue(a.x), ay=yForGI(a.v);
      const bx=x.getPixelForValue(b.x), by=yForGI(b.v);
      ctx.beginPath();
      ctx.strokeStyle=giColorForValue((a.v+b.v)/2);
      ctx.moveTo(ax,ay); ctx.lineTo(bx,by); ctx.stroke();
    }
    ctx.restore();
  }
};

const volumePlugin={
  id:'volumePlugin',
  afterDatasetsDraw(chart){
    if(!blShowVolume()||!_blOhlcv.length)return;
    const {ctx,scales:{x,y},chartArea}=chart;
    const vols=_blOhlcv.map(d=>Number(d.v)||0);
    const visMin=Math.max(0,Math.floor(Number.isFinite(x.min)?x.min:0));
    const visMax=Math.min(vols.length-1,Math.ceil(Number.isFinite(x.max)?x.max:vols.length-1));
    const visVols=vols.slice(visMin,visMax+1);
    const maxVol=Math.max(...(visVols.length?visVols:vols),0);
    const isVolCndle=String(_blChartType||'').toLowerCase()==='volcndle';
    const visibleCount2=Math.max(1, Math.abs((Number.isFinite(x.max)?x.max:_blOhlcv.length-1)-(Number.isFinite(x.min)?x.min:0))+1);
    const _vcBarSpacing=blGetBarSpacing(x,visibleCount2);
    const _vcSorted=[...visVols].filter(v=>v>0).sort((a,b)=>a-b);
    const _vcMedian=_vcSorted.length?_vcSorted[Math.floor(_vcSorted.length/2)]:1;
    const _vcNorm=Math.max(3,_vcBarSpacing*0.55);
    const _vcMax=Math.max(4,_vcBarSpacing*0.92);
    const _vcMin=Math.max(2,Math.round(_vcBarSpacing*0.10));
    const _vcVolLayout=(isVolCndle&&_blVcConsistentGaps)?_buildVcLayout(chart):null;
    if(!(maxVol>0)) return;
    const volMargin=0;
    const chartH=Math.max(1, chartArea.bottom-chartArea.top);
    const volScale=clampNum(Number(_blVolumeScale)||1,0.25,2.5);
    const basePanelH=Math.max(64, Math.min(152, chartH*0.31));
    const panelH=Math.max(24, Math.min(chartH*0.58, basePanelH*volScale));
    // When x-axis is visible (overlay/off GI mode), cap bars at chartArea.bottom so they
    // don't paint over date labels. When x-axis is hidden (lower GI mode), extend to the
    // full canvas height so there's no visible gap between the chart and the GI panel below.
    const _xAxisVisible=!!(blChart?.options?.scales?.x?.display);
    const baseY=Math.ceil(_xAxisVisible ? chartArea.bottom : (chart.canvas.clientHeight||chartArea.bottom));
    const visibleCount=Math.max(1, Math.abs((Number.isFinite(x.max)?x.max:_blOhlcv.length-1) - (Number.isFinite(x.min)?x.min:0)) + 1);
    const vsaStats=blVolumeStats();
    ctx.save();
    ctx.beginPath();
    ctx.rect(chartArea.left, chartArea.top, chartArea.right-chartArea.left, baseY-chartArea.top);
    ctx.clip();
    _blOhlcv.forEach((d,i)=>{
      const _vcBar=_vcVolLayout?_vcVolLayout.get(i):null;
      const width=_vcBar?_vcBar.w:isVolCndle
        ? Math.max(_vcMin,Math.min(_vcMax,Math.round(_vcNorm*((vols[i]>0?vols[i]:_vcMedian)/_vcMedian))))
        : blVolumeWidthAt(i, x, visibleCount);
      const barW=Math.max(2, Math.round(width));
      const px=_vcBar?_vcBar.cx:x.getPixelForValue(i);
      if(px<x.left-barW||px>x.right+barW)return;
      const vol=vols[i];
      if(!(vol>0)) return;
      const h=Math.max(1, Math.ceil((vol/maxVol)*(panelH-volMargin)));
      const y0=baseY-h;
      const up=Number(d.c)>=Number(d.o);
      const vs=vsaStats[i]||{};
      const vsaColor=_blShowVSA ? (vs.signal ? vs.color : '#434651') : null;
      ctx.fillStyle=vsaColor || (up?blHexToRgba(_blVolUpColor,0.52):blHexToRgba(_blVolDownColor,0.52));
      ctx.fillRect(px-barW/2,y0,barW,h);
    });
    ctx.restore();
  }
};
const indicatorPlugin={
  id:'indicatorPlugin',
  afterDatasetsDraw(chart){
    if(!blShowIndicators()||!_blOhlcv.length)return;
    const {ctx,scales:{x,y}}=chart;
    const ind=blIndicatorSeries();
    const series=[];
    if(_blShowVwap) series.push({data:ind.vwap20,color:blHexToRgba(_blVwapColor,0.95),width:1.2});
    if(_blShowMA50) series.push({data:ind.sma50,color:blHexToRgba(_blMA50Color,0.92),width:1.15});
    if(_blShowMA200) series.push({data:ind.sma200,color:blHexToRgba(_blMA200Color,0.90),width:1.2});
    ctx.save();
    series.forEach(s=>{
      ctx.beginPath();
      let started=false;
      ctx.strokeStyle=s.color;
      ctx.lineWidth=s.width;
      s.data.forEach((v,i)=>{
        if(!Number.isFinite(v)){started=false;return;}
        const px=x.getPixelForValue(i);
        const py=y.getPixelForValue(v);
        if(!started){ctx.moveTo(px,py);started=true;} else ctx.lineTo(px,py);
      });
      ctx.stroke();
    });
    ctx.restore();
  }
};
const vsaPlugin={
  id:'vsaPlugin',
  afterDatasetsDraw(chart){
    if(!blShowVSA()||!_blOhlcv.length)return;
    const {ctx,scales:{x,y}}=chart;
    const stats=blVolumeStats();
    ctx.save();
    ctx.font='bold 8px JetBrains Mono,monospace';
    ctx.textAlign='center';
    ctx.textBaseline='middle';
    stats.forEach((s,i)=>{
      if(!s.signal) return;
      const px=x.getPixelForValue(i);
      if(px<x.left-12||px>x.right+12) return;
      const lowSide=(s.signal==='No Supply'||s.signal==='Squat');
      const py=lowSide ? y.getPixelForValue(_blOhlcv[i].l)-11 : y.getPixelForValue(_blOhlcv[i].h)+11;
      ctx.fillStyle=s.color||'rgba(67,70,81,0.92)';
      ctx.beginPath();
      ctx.arc(px,py,7,0,Math.PI*2);
      ctx.fill();
      ctx.fillStyle='#fff';
      const lbl=s.signal==='No Supply'?'NS':s.signal==='No Demand'?'ND':s.signal==='Climax'?'C':'S';
      ctx.fillText(lbl,px,py+0.5);
    });
    ctx.restore();
  }
};

let _blTickerMenuItems=[];
let _blTickerMenuIndex=-1;

function blTickerCompany(ticker){
  return BL_TICKER_INFO[String(ticker||'').trim().toUpperCase()]||'';
}

function blCurrentTicker(){
  const el=document.getElementById('blTicker');
  return String(el?.dataset.current||el?.value||'').trim().toUpperCase();
}

function blSyncTickerCurrent(){
  const cur=blCurrentTicker();
  const inp=document.getElementById('blTF');
  if(inp && cur && document.activeElement!==inp) inp.value=cur;
  return cur;
}

function blSetCurrentTicker(ticker){
  const q=String(ticker||'').trim().toUpperCase();
  const el=document.getElementById('blTicker');
  const inp=document.getElementById('blTF');
  if(el){
    el.dataset.current=q;
    el.value=q;
  }
  if(inp) inp.value=q;
  _blTypeAhead=q;
  blSyncTickerCurrent();
  saveBuyLevelsPrefs();
  return q;
}

function blTickerMatchRank(ticker, query){
  const sym=String(ticker||'').trim().toUpperCase();
  const q=String(query||'').trim().toUpperCase();
  if(!sym || !q) return Number.POSITIVE_INFINITY;
  const company=blTickerCompany(sym).toUpperCase();
  if(sym===q) return 0;
  if(sym.startsWith(q)) return 1;
  if(company.startsWith(q)) return 2;
  if(sym.includes(q)) return 3;
  if(company.includes(q)) return 4;
  return Number.POSITIVE_INFINITY;
}

function blTickerMatchesQuery(ticker, query){
  return Number.isFinite(blTickerMatchRank(ticker, query));
}

function blHideTickerMenu(){
  const menu=document.getElementById('blTickerMenu');
  if(menu){ menu.classList.remove('show'); menu.innerHTML=''; }
  _blTickerMenuItems=[];
  _blTickerMenuIndex=-1;
}

function blActiveTickerSuggestion(){
  return (_blTickerMenuIndex>=0&&_blTickerMenuIndex<_blTickerMenuItems.length)?_blTickerMenuItems[_blTickerMenuIndex]:'';
}

function blUpdateTickerMenuActive(){
  const menu=document.getElementById('blTickerMenu');
  if(!menu) return;
  const items=menu.querySelectorAll('.bl-ticker-item');
  items.forEach((el,i)=>{
    const active=i===_blTickerMenuIndex;
    el.classList.toggle('active', active);
    if(active) el.scrollIntoView({block:'nearest'});
  });
}

function blSetTickerMenuIndex(idx){
  if(idx<0 || idx>=_blTickerMenuItems.length) return;
  _blTickerMenuIndex=idx;
  blUpdateTickerMenuActive();
}

function blRenderTickerMenu(tickers, query){
  const menu=document.getElementById('blTickerMenu');
  const inp=document.getElementById('blTF');
  const q=String(query||'').trim().toUpperCase();
  if(!menu){ _blTickerMenuItems=[]; _blTickerMenuIndex=-1; return; }
  if(!inp || document.activeElement!==inp){ blHideTickerMenu(); return; }
  if(!q){ blHideTickerMenu(); return; }
  const visible=(tickers||[]).slice(0,12);
  if(!visible.length){
    _blTickerMenuItems=[];
    _blTickerMenuIndex=-1;
    menu.innerHTML='<div class="bl-ticker-empty">No matches</div>';
    menu.classList.add('show');
    return;
  }
  const prev=blActiveTickerSuggestion();
  _blTickerMenuItems=visible;
  if(prev && visible.includes(prev)) _blTickerMenuIndex=visible.indexOf(prev);
  else {
    const exactIdx=visible.indexOf(q);
    _blTickerMenuIndex=exactIdx>=0?exactIdx:0;
  }
  menu.innerHTML=visible.map((t,i)=>{
    const name=blTickerCompany(t);
    return `<button type="button" class="bl-ticker-item${i===_blTickerMenuIndex?' active':''}" data-ticker="${escAttr(t)}" onmousedown="event.preventDefault()" onmouseenter="blSetTickerMenuIndex(${i})" onclick="blOpenTickerSuggestion(this.dataset.ticker)"><span class="bl-ticker-symbol">${escHtml(t)}</span><span class="bl-ticker-name">${escHtml(name||'No company name')}</span></button>`;
  }).join('');
  menu.classList.add('show');
  blUpdateTickerMenuActive();
}

function blMoveTickerMenu(step){
  if(!_blTickerMenuItems.length) return false;
  const size=_blTickerMenuItems.length;
  if(!size) return false;
  if(_blTickerMenuIndex<0 || _blTickerMenuIndex>=size) _blTickerMenuIndex=0;
  else _blTickerMenuIndex=(_blTickerMenuIndex+step+size)%size;
  blUpdateTickerMenuActive();
  return true;
}

function blHandleFilterInput(){
  const inp=document.getElementById('blTF');
  if(!inp) return;
  const upper=String(inp.value||'').toUpperCase();
  if(inp.value!==upper){
    const start=inp.selectionStart;
    const end=inp.selectionEnd;
    inp.value=upper;
    try{ inp.setSelectionRange(start==null?upper.length:start,end==null?upper.length:end); }catch(_e){}
  }
  _blTypeAhead=String(inp.value||'').trim().toUpperCase();
  _blTypeAheadAt=Date.now();
  blRefreshTickers(false);
}

function blHandleFilterFocus(){
  const q=String(document.getElementById('blTF')?.value||'').trim();
  if(q) blRefreshTickers(false);
}

function blHandleFilterBlur(){
  setTimeout(()=>{
    const wrap=document.getElementById('blTickerSearchWrap');
    if(wrap && !wrap.contains(document.activeElement)) blHideTickerMenu();
  },0);
}

function blOpenTickerSuggestion(ticker){
  const sym=String(ticker||'').trim().toUpperCase();
  if(!sym) return false;
  const inp=document.getElementById('blTF');
  if(inp) inp.value=sym;
  _blTypeAhead=sym;
  _blTypeAheadAt=Date.now();
  blHideTickerMenu();
  return blOpenTicker(sym);
}

function blHandleFilterKeydown(event){
  const key=String(event?.key||'');
  if(key==='ArrowDown' || key==='ArrowUp'){
    if(blMoveTickerMenu(key==='ArrowDown'?1:-1)){
      event.preventDefault();
      return false;
    }
    return true;
  }
  if(key==='Enter'){
    event.preventDefault();
    blForceOpen();
    return false;
  }
  if(key==='Escape'){
    const inp=document.getElementById('blTF');
    if(inp && inp.value){
      inp.value='';
      _blTypeAhead='';
      _blTypeAheadAt=0;
      blRefreshTickers(false);
    }else blHideTickerMenu();
    event.preventDefault();
    return false;
  }
  return true;
}

function blRefreshTickers(selectDefault){
  const q=(document.getElementById('blTF').value||'').trim().toUpperCase();
  const sortBy=String(document.getElementById('blSortBy')?.value||_blSortBy||'recent');
  const cur=blCurrentTicker();
  const cutoff=Date.now()-blLookbackDays()*86400000;
  const candleData=getCandleData();
  const visibleBuysByTicker={};
  let tickers=Array.from(new Set([].concat(Object.keys(candleData||{}), Object.keys(BUY_META||{})))).filter(t=>{
    const buys=(BUY_META[t]||[]).filter(b=>b.price!=null&&new Date(blBuyTradeDate(b)).getTime()>=cutoff);
    visibleBuysByTicker[t]=buys;
    return buys.length>0 || !!(candleData[t]&&candleData[t].length);
  });
  const curExists=!!(cur && tickers.includes(cur));
  const alphaCompare=(a,b)=>a.localeCompare(b);
  tickers.sort((a,b)=>{
    const aBuys=visibleBuysByTicker[a]||[];
    const bBuys=visibleBuysByTicker[b]||[];
    const aHasBuys=aBuys.length>0;
    const bHasBuys=bBuys.length>0;
    if(sortBy!=='alpha' && aHasBuys!==bHasBuys) return (bHasBuys?1:0)-(aHasBuys?1:0);
    if(sortBy==='amount'){
      const diff=bBuys.reduce((s,x)=>s+(x.value||0),0)-aBuys.reduce((s,x)=>s+(x.value||0),0);
      if(diff) return diff;
    }else if(sortBy==='recent'){
      const da=aBuys.reduce((m,x)=>{const d=blBuyTradeDate(x);return d>m?d:m;},'');
      const db=bBuys.reduce((m,x)=>{const d=blBuyTradeDate(x);return d>m?d:m;},'');
      const diff=db.localeCompare(da);
      if(diff) return diff;
    }else if(sortBy==='count'){
      const diff=bBuys.length-aBuys.length;
      if(diff) return diff;
    }
    return alphaCompare(a,b);
  });
  const sortOrder=new Map(tickers.map((t,i)=>[t,i]));
  if(q && !(selectDefault && cur && !curExists)){
    tickers=tickers.filter(t=>blTickerMatchesQuery(t,q));
    const loaded=new Set(tickers);
    Object.keys(BL_SEARCH_UNIVERSE||{}).forEach(t=>{
      if(!loaded.has(t)&&blTickerMatchesQuery(t,q)) tickers.push(t);
    });
    tickers.sort((a,b)=>{
      const rankDiff=blTickerMatchRank(a,q)-blTickerMatchRank(b,q);
      if(rankDiff) return rankDiff;
      return (sortOrder.get(a)||0)-(sortOrder.get(b)||0);
    });
  }
  const curValid=!!(cur && tickers.includes(cur));
  if(selectDefault && !curValid && tickers.length) blSetCurrentTicker(tickers[0]);
  else blSyncTickerCurrent();
  blRenderTickerMenu(tickers, q);
}

function blLookbackDays(){
  const v=parseInt(document.getElementById('blLookback')?.value);
  _blLookbackDays=Number.isFinite(v)?v:_blLookbackDays;
  return Number.isFinite(_blLookbackDays)?_blLookbackDays:365;
}

function blBuyTradeDate(b){
  return b?.trans_date||b?.date||b?.filing_date||'';
}

function blBuyFiledDate(b){
  return b?.date||b?.filing_date||b?.trans_date||'';
}

function blForceOpen(){
  const q=(document.getElementById('blTF').value||'').trim().toUpperCase();
  let ticker='';
  const candleData=getCandleData();
  if(q){
    const hasBuys=!!BUY_META[q];
    const hasChart=!!(candleData[q]&&candleData[q].length);
    if(hasBuys||hasChart) ticker=q;
  }
  if(!ticker) ticker=blActiveTickerSuggestion()||_blTickerMenuItems[0]||'';
  if(!ticker) return;
  const inp=document.getElementById('blTF');
  if(inp) inp.value=ticker;
  _blTypeAhead=ticker;
  _blTypeAheadAt=Date.now();
  blHideTickerMenu();
  blOpenTicker(ticker);
}

function blOpenTicker(ticker){
  const q=String(ticker||'').trim().toUpperCase();
  if(!q) return false;
  const inp=document.getElementById('blTF');
  if(inp) inp.value=q;
  // Save current chart zoom before switching tickers.
  if(q!==_blRenderedTicker) blCaptureZoomState();
  blSetCurrentTicker(q);
  blHideTickerMenu();
  renderBuyLevels();
  blFetchLiveQuoteOnce(q);  // always fetch current price when opening a ticker
  if(inp){
    try{ inp.setSelectionRange(inp.value.length, inp.value.length); }catch(_e){}
    if(document.activeElement===inp){
      try{ inp.blur(); }catch(_e){}
    }
  }
  return true;
}

let _blTypeAhead='';
let _blTypeAheadAt=0;
function blChartTabActive(){
  return !!document.getElementById('tab-buylevels')?.classList.contains('active');
}
function blActiveTypingTarget(el){
  if(!el) return false;
  const tag=String(el.tagName||'').toUpperCase();
  return el.isContentEditable || tag==='INPUT' || tag==='TEXTAREA' || tag==='SELECT';
}
function blFocusFilterInput(){
  const inp=document.getElementById('blTF');
  if(!inp) return null;
  try{ inp.focus({preventScroll:true}); }catch(_e){ try{ inp.focus(); }catch(_e2){} }
  return inp;
}
function blPrimeLookupTyping(seed){
  const inp=blFocusFilterInput();
  if(!inp) return false;
  const current=blCurrentTicker();
  const shown=String(inp.value||'').trim().toUpperCase();
  const base=(shown && shown!==current) ? shown : '';
  const next=(base + String(seed||'')).toUpperCase();
  _blTypeAhead=next;
  _blTypeAheadAt=Date.now();
  blSetFilterText(next);
  try{ inp.setSelectionRange(next.length,next.length); }catch(_e){}
  return true;
}
function blSetFilterText(val){
  const inp=document.getElementById('blTF');
  if(!inp) return;
  inp.value=String(val||'').toUpperCase();
  blRefreshTickers(false);
}
function blShowToast(msg){
  let t=document.getElementById('blToastMsg');
  if(!t){
    t=document.createElement('div');
    t.id='blToastMsg';
    t.style.cssText='position:fixed;bottom:28px;right:24px;z-index:99999;background:#1a1a1a;border:1px solid #333;color:#eaeaea;font-family:var(--mono);font-size:11px;padding:6px 14px;border-radius:8px;box-shadow:0 4px 18px rgba(0,0,0,.5);pointer-events:none;transition:opacity .25s ease';
    document.body.appendChild(t);
  }
  t.textContent=msg;
  t.style.opacity='1';
  clearTimeout(t._tid);
  t._tid=setTimeout(()=>{t.style.opacity='0';},2000);
}
document.addEventListener('keydown',function(e){
  if(!blChartTabActive()) return;
  if(e.altKey&&!e.ctrlKey&&!e.metaKey&&(e.key==='w'||e.key==='W')){
    e.preventDefault();
    const sym=blCurrentTicker();
    if(!sym) return;
    const wl=WATCHLISTS[ACTIVE_WATCHLIST];
    if(!wl) return;
    const items=wl.items||[];
    if(items.some(it=>it&&it.type==='symbol'&&it.sym===sym)){
      blShowToast(sym+' already in watchlist');
      return;
    }
    if(!wl.items) wl.items=[];
    wl.items.push({type:'symbol',sym});
    saveWatchlists();
    renderWatchlist();
    blShowToast(sym+' added to watchlist');
    // Fetch OHLCV if not already loaded, then re-render with price
    if(CANDLE_DATA[sym]==null){
      blEnsureTickerOHLCV(sym).then(()=>renderWatchlist()).catch(()=>{});
    }
    return;
  }
  if(e.altKey||e.ctrlKey||e.metaKey) return;
  if(blActiveTypingTarget(e.target)) return;
  const key=String(e.key||'');
  const inp=document.getElementById('blTF');
  if((key==='ArrowDown' || key==='ArrowUp') && inp && String(inp.value||'').trim()){
    if(blMoveTickerMenu(key==='ArrowDown' ? 1 : -1)){
      e.preventDefault();
      return;
    }
  }
  if(document.body.classList.contains('watchlist-open')){
    if(key==='ArrowDown' || key==='ArrowUp'){
      if(watchlistStepSelection(key==='ArrowDown' ? 1 : -1)){
        e.preventDefault();
        return;
      }
    }
  }
  const now=Date.now();
  if(!inp) return;
  if(key.length===1 && /^[A-Za-z0-9.-]$/.test(key)){
    if(document.activeElement!==inp){
      if(blPrimeLookupTyping(key)){ e.preventDefault(); return; }
    }
    _blTypeAheadAt=now;
    _blTypeAhead+=key.toUpperCase();
    blSetFilterText(_blTypeAhead);
    e.preventDefault();
    return;
  }
  if(key==='Backspace'){
    const cur=String(inp.value||'').trim().toUpperCase();
    if(!cur) return;
    _blTypeAhead=cur.slice(0,-1);
    _blTypeAheadAt=now;
    blSetFilterText(_blTypeAhead);
    e.preventDefault();
    return;
  }
  if(key==='Escape'){
    if(!inp.value && !_blTypeAhead) return;
    _blTypeAhead='';
    _blTypeAheadAt=0;
    blSetFilterText('');
    e.preventDefault();
    return;
  }
  if(key==='Enter'){
    const q=String(inp.value||_blTypeAhead||'').trim().toUpperCase();
    if(!q) return;
    _blTypeAhead=q;
    _blTypeAheadAt=now;
    blForceOpen();
    e.preventDefault();
  }
});

document.addEventListener('mousedown',function(e){
  const wrap=document.getElementById('blTickerSearchWrap');
  if(wrap && !wrap.contains(e.target)) blHideTickerMenu();
});

function blChartPeriodDays(){
  const v=parseInt(document.getElementById('blChartPeriod')?.value);
  _blPeriod=Number.isFinite(v)?v:_blPeriod;
  return Number.isFinite(_blPeriod)?_blPeriod:365;
}
function blChartPeriodChange(){
  _blPeriod=blChartPeriodDays();
  _blForceDefaultRange=true;
  _blSavedZoom=null;
  saveBuyLevelsPrefs();
  renderBuyLevels();
}

function blResetChartZoom(){
  if(!blChart||!_blOhlcv.length) return;
  const range=blDefaultXRange(_blOhlcv);
  blChart.options.scales.x.min=range.min;
  blChart.options.scales.x.max=range.max;
  _blSavedZoom=null;
  blChart.update('none');
  syncGIToBuyRange();
  _syncLookbackBarPos(blChart);
}
function blDefaultXRange(ohlcv){
  const n=ohlcv.length;
  if(!n) return {min:0,max:0};
  const maxIdx=n-1;
  const days=blChartPeriodDays();
  // Always add 0.5 so the last bar center sits fully inside the chart area at 0 right bars
  const rightPad=_blRightBars+2.5;
  if(!Number.isFinite(days)||days<=0) return {min:0,max:maxIdx+rightPad};
  const endTs=new Date(ohlcv[maxIdx].t).getTime();
  if(!Number.isFinite(endTs)) return {min:Math.max(0,maxIdx-252),max:maxIdx+rightPad};
  const cutoff=endTs-days*86400000;
  let minIdx=0;
  for(let i=0;i<n;i++){
    const ts=new Date(ohlcv[i].t).getTime();
    if(Number.isFinite(ts)&&ts>=cutoff){minIdx=i;break;}
  }
  return {min:minIdx,max:maxIdx+rightPad};
}

function blClosestIdxForDate(dateStr){
  if(!_blOhlcv.length) return 0;
  const ts=new Date(dateStr).getTime();
  if(!Number.isFinite(ts)) return 0;
  let best=0,bestDiff=Infinity;
  _blOhlcv.forEach((d,i)=>{
    const diff=Math.abs(new Date(d.t).getTime()-ts);
    if(diff<bestDiff){bestDiff=diff;best=i;}
  });
  return best;
}

function blAlignedGIChartPoints(rawPts){
  const pts=(rawPts||[])
    .map(d=>({t:String(d?.t||''),v:Number(d?.v)}))
    .filter(d=>d.t&&Number.isFinite(d.v))
    .sort((a,b)=>a.t.localeCompare(b.t));
  if(!pts.length) return [];
  if(!_blOhlcv.length){
    return pts.map((d,i)=>Object.assign({},d,{x:i}));
  }
  const out=[];
  let histIdx=0;
  let latest=null;
  _blOhlcv.forEach((bar,i)=>{
    const barDate=String(bar?.t||'');
    if(!barDate) return;
    while(histIdx<pts.length && pts[histIdx].t<=barDate){
      latest=pts[histIdx];
      histIdx++;
    }
    if(latest) out.push({t:barDate,src_t:latest.t,v:latest.v,x:i});
  });
  return out.length ? out : pts.map((d,i)=>Object.assign({},d,{x:blClosestIdxForDate(d.t)}));
}

function blVisibleBuys(ticker){
  // Use the chart period (not the "Buys Within" watchlist filter) so dots always
  // appear for any buy that falls within the visible chart date range.
  const chartDays=Math.max(blChartPeriodDays(), blLookbackDays());
  const cutoff=Date.now()-chartDays*86400000;
  return (BUY_META[ticker]||[])
    .filter(b=>b.price!=null&&new Date(blBuyTradeDate(b)).getTime()>=cutoff);
}

function iUpdateHeaderSort(col,dir){
  document.querySelectorAll('#tab-insider thead th').forEach(t=>{
    t.classList.remove('sort-asc','sort-desc');
    if(t.dataset.col===col) t.classList.add(dir===1?'sort-asc':'sort-desc');
  });
}

function iSortValueFromMovedControl(){
  const sortBy=String(document.getElementById('blSortBy')?.value||'recent');
  if(sortBy==='amount') return {col:'total_value',dir:-1};
  if(sortBy==='count') return {col:'trade_count',dir:-1};
  if(sortBy==='alpha') return {col:'ticker',dir:1};
  return {col:'filing_date',dir:-1};
}

function iSyncMovedSortControl(){
  const sel=document.getElementById('blSortBy');
  if(!sel) return;
  let value='';
  if(iSt.sc==='total_value') value='amount';
  else if(iSt.sc==='filing_date') value='recent';
  else if(iSt.sc==='trade_count') value='count';
  else if(iSt.sc==='ticker' && iSt.sd===1) value='alpha';
  if(value) sel.value=value;
}

function iApplySortFromMovedControl(){
  const cfg=iSortValueFromMovedControl();
  iSt.sc=cfg.col;
  iSt.sd=cfg.dir;
  iUpdateHeaderSort(iSt.sc,iSt.sd);
}

function iWinDaysFromSelect(){
  const sel=document.getElementById('iWinDaysSelect');
  const hidden=document.getElementById('iWinDays');
  if(sel&&hidden) hidden.value=sel.value;
}
function iApplyLookbackFromMovedControl(){
  const lookbackEl=document.getElementById('blLookback');
  const hiddenEl=document.getElementById('iWinDays');
  const selEl=document.getElementById('iWinDaysSelect');
  if(!lookbackEl) return;
  const days=parseInt(lookbackEl.value)||365;
  if(hiddenEl) hiddenEl.value=String(days);
  // Sync the dropdown if the value matches one of its options
  if(selEl){
    const opt=Array.from(selEl.options).find(o=>parseInt(o.value)===days);
    if(opt) selEl.value=String(days);
  }
}

function blSortChange(){
  blPullSavedControlState();
  saveBuyLevelsPrefs();
  blRefreshTickers();
  iApplySortFromMovedControl();
  if(!TAB_INIT.insider) return;
  iSt.pg=1;
  renderI();
}

function blLookbackChange(){
  blPullSavedControlState();
  saveBuyLevelsPrefs();
  iApplyLookbackFromMovedControl();
  blRefreshTickers();
  if(TAB_INIT.insider) iFilter();
  renderBuyLevels();
}

async function renderBuyLevels(){
  try{
  const _renderToken=++_blRenderToken;
  const ticker=blCurrentTicker();
  await blEnsureTickerOHLCV(ticker);
  if(_renderToken!==_blRenderToken||ticker!==blCurrentTicker()) return;
  blSyncTickerCurrent();
  try{ renderWatchlist(); }catch(_e){}
  const empty=document.getElementById('blEmpty');
  const section=document.getElementById('blChartSection');
  if(!empty||!section) throw new Error('Buy Levels DOM missing');
  const candleData=getCandleData();
  const hasData=!!(BUY_META[ticker]||(candleData[ticker]&&candleData[ticker].length));
  if(!ticker||!hasData){
    empty.style.display='block';section.style.display='none';
    if(blChart){blChart.destroy();blChart=null;}_blOhlcv=[];_blReversals=[];_blEarnings=[];_projLines=[]; blRenderProfile('');
    if(giHistChart){giHistChart.destroy();giHistChart=null;}
    document.getElementById('blGISection').style.display='none';
    document.getElementById('blTooltip').style.display='none';
    blSyncIndicatorChecks();
    renderGISignalPanel(null);
    _blRenderedTicker='';
    return;
  }
  const allOhlcv=candleData[ticker]||[];
  if(!allOhlcv.length){
    // Show section so GI panel is visible; hide chart area, show message
    empty.style.display='none';section.style.display='flex';
    document.getElementById('blNoData').textContent='No chart data for '+ticker;
    document.getElementById('blNoData').style.display='block';
    document.getElementById('blChartWrap').style.display='none';
    if(blChart){blChart.destroy();blChart=null;}_blOhlcv=[]; blRenderProfile('');
    if(giHistChart){giHistChart.destroy();giHistChart=null;}
    document.getElementById('blGISection').style.display='none';
    document.getElementById('blTooltip').style.display='none';
    blSyncIndicatorChecks();
    renderGISignalPanel(ticker);
    renderGIChart(ticker);
    _blRenderedTicker='';
    return;
  }
  document.getElementById('blNoData').style.display='none';
  document.getElementById('blChartWrap').style.display='';
  _blBuys=blVisibleBuys(ticker);
  _blBuysIdxReady=false; // _idx not mapped yet — block chart updates until after mapping
  empty.style.display='none';section.style.display='flex';
  renderGISignalPanel(ticker);
  const ohlcv=allOhlcv; // EOD data from backend is always trusted - no filtering
  if(!ohlcv.length)return;
  _blOhlcv=ohlcv; _blVsaCache=null; _blIndCache=null;
  // Apply any cached live quote now that CANDLE_DATA is loaded.
  // Fixes the race where the first Schwab poll fires before data arrives.
  const _lq=_blLiveQuoteCache[ticker];
  if(_lq) _blLivePatchCandleData(ticker,_lq);
  blSyncIndicatorChecks();
  blRenderProfile(ticker);
  // Build date->index map for uniform candle spacing (no weekend gaps)
  const dateToIdx={};
  ohlcv.forEach((d,i)=>{dateToIdx[d.t]=i;});
  function closestIdx(dateStr){
    if(dateToIdx[dateStr]!==undefined)return dateToIdx[dateStr];
    return blClosestIdxForDate(dateStr);
  }
  _blBuys=_blBuys.map(b=>Object.assign({},b,{_idx:closestIdx(blBuyTradeDate(b))}));
  // Step 1: collapse same-insider + same trading-day into one dot (dollar-weighted avg price)
  (function(){
    const agg={};
    _blBuys.forEach(b=>{
      const k=(b.insider||'?')+'|'+b._idx;
      if(!agg[k])agg[k]={
        insider:b.insider||'?',title:b.title||'',_idx:b._idx,
        sumVal:0,sumShares:0,sumP:0,n:0,date:blBuyFiledDate(b),trans_date:blBuyTradeDate(b)
      };
      const g=agg[k],v=b.value||0,p=b.price||0;
      if(!g.title&&b.title)g.title=b.title;
      const filedDate=blBuyFiledDate(b);
      if(filedDate>g.date)g.date=filedDate;
      const transDate=blBuyTradeDate(b);
      if(transDate>g.trans_date)g.trans_date=transDate;
      if(v>0)g.sumVal+=v;
      if(v>0&&p>0)g.sumShares+=v/p;
      else if(p>0){g.sumP+=p;g.n++;}
    });
    _blBuys=Object.values(agg).map(g=>{
      const p=g.sumShares>0?g.sumVal/g.sumShares:g.n>0?g.sumP/g.n:0;
      return{
        insider:g.insider,title:g.title,_idx:g._idx,price:Math.round(p*100)/100,
        value:g.sumVal,value_fmt:fmt_money_js(g.sumVal),date:g.date,trans_date:g.trans_date
      };
    }).filter(b=>b.price>0);
  })();
  // Step 2: collapse different insiders buying on the same day at the same price into one dot
  (function(){
    const agg={};
    _blBuys.forEach(b=>{
      const k=b._idx+'|'+b.price;
      if(!agg[k])agg[k]={
        insiders:[],_idx:b._idx,price:b.price,
        sumVal:0,date:b.date,trans_date:b.trans_date
      };
      const g=agg[k];
      g.insiders.push({insider:b.insider,title:b.title,value:b.value,value_fmt:b.value_fmt});
      g.sumVal+=b.value||0;
      if(b.date>g.date)g.date=b.date;
      if(b.trans_date>g.trans_date)g.trans_date=b.trans_date;
    });
    _blBuys=Object.values(agg).map(g=>{
      const first=g.insiders[0]||{};
      return{
        insider:g.insiders.map(x=>x.insider||'?').join(', '),
        insiders:g.insiders,
        title:first.title||'',
        _idx:g._idx,price:g.price,
        value:g.sumVal,value_fmt:fmt_money_js(g.sumVal),
        date:g.date,trans_date:g.trans_date
      };
    });
  })();
  _blBuysIdxReady=true; // _idx mapping complete — chart updates are now safe
  // Load reversal + earnings signals (closestIdx is now ready)
  (function(){
    const rawRev=(REVERSALS_DATA[ticker]||[]);
    _blReversals=rawRev.map(r=>{const idx=closestIdx(r.d);return{...r,_idx:idx,t:r.t||'gi_rev'};});
    const rawEarn=(EARNINGS_DATA[ticker]||[]);
    _blEarnings=rawEarn.map(e=>Object.assign({},e,{_idx:closestIdx(e.d)}));
  })();
  const yLo=Math.min(...ohlcv.map(d=>d.l));
  const yHi=Math.max(...ohlcv.map(d=>d.h));
  const ind=blIndicatorSeries();
  const overlayVals=[];
  if(blShowIndicators()){
    [ind.vwap20, ind.sma50, ind.sma200].forEach(arr=>arr.forEach(v=>{if(Number.isFinite(v)) overlayVals.push(v);}));
  }
  const allY=overlayVals.length?[yLo,yHi,...overlayVals]:[yLo,yHi];
  const yLoAll=Math.min(...allY);
  const yHiAll=Math.max(...allY);
  const span=(yHiAll-yLoAll||1);
  const padTop=Math.max(0.01,span*(_blMarginTopPct/100));
  const padBottom=Math.max(0.01,span*(_blMarginBotPct/100));
  const yMin=Math.max(0,yLoAll-padBottom),yMax=yHiAll+padTop;
  const tickerChanged=ticker!==_blRenderedTicker;
  // Reset lookback to "Now" whenever the user switches to a different ticker
  if(tickerChanged && _blProjLookback!==0){ blSetLookback(0); }
  let xRange=null;
  // Keep the current viewport when re-rendering the same ticker,
  // unless a period change explicitly requested a fresh default range.
  if(!tickerChanged&&!_blForceDefaultRange&&blChart&&blChart.scales&&blChart.scales.x){
    const sxPrev=blChart.scales.x;
    const prevMin=Number(sxPrev.min), prevMax=Number(sxPrev.max);
    if(Number.isFinite(prevMin)&&Number.isFinite(prevMax)&&prevMax>prevMin){
      xRange={min:Math.max(0,prevMin),max:Math.max(prevMin+1,prevMax)};
    }
  }
  _blForceDefaultRange=false;
  // When switching symbols, carry over the prior zoom span.
  if(!xRange&&tickerChanged) xRange=blRangeFromSavedZoom(ohlcv);
  if(!xRange) xRange=blDefaultXRange(ohlcv);
  if(tickerChanged) _blSavedZoom=null;
  _blRenderedTicker=ticker;
  const buyPts=_blBuys.map(b=>{return{x:b._idx,y:b.price,_b:b};});
  const isLineChart=_blChartType==='line';
  const closePts=ohlcv.map((d,i)=>({x:i,y:Number(d.c)}));
  // Hide chart wrap during destroy/recreate to prevent ghost flash.
  const _blWrap=document.getElementById('blChartWrap');
  if(_blWrap) _blWrap.style.opacity='0';
  if(blChart)blChart.destroy();
  const canvas=document.getElementById('buyLevelChart');
  if(!canvas) throw new Error('buyLevelChart canvas missing');
  const ctx=canvas.getContext('2d');
  if(!ctx) throw new Error('buyLevelChart context unavailable');
  blChart=new Chart(ctx,{
    type:'scatter',
    data:{datasets:[
      {data:[{x:0,y:(yMin+yMax)/2},{x:ohlcv.length-1,y:(yMin+yMax)/2}],pointRadius:0,hoverRadius:0},
      {type:'line',label:'Close',data:closePts,
        hidden:!isLineChart,
        borderColor:'rgba(216,220,228,0.95)',
        backgroundColor:'transparent',
        fill:false,
        borderWidth:1.7,pointRadius:0,tension:0,
        order:10},
      {type:'scatter',label:'Insider Buys',data:buyPts,
        pointRadius:0,pointHitRadius:0,pointHoverRadius:0},
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      onHover(evt){
        const canvas=evt?.native?.target||evt?.chart?.canvas||document.getElementById('buyLevelChart');
        if(!blChart||!canvas) return;
        const scales=blChart.scales;
        const xPx=evt.x, yPx=evt.y;
        const nativeEvt=evt.native||evt;
        const cx=nativeEvt.clientX||0, cy=nativeEvt.clientY||0;
        let hit=false;
        // Insider buy dot hover — show popup instantly
        if(_blShowInsiders&&_blBuys.length){
          const _hoverVcLayout=(String(_blChartType||'').toLowerCase()==='volcndle'&&_blVcConsistentGaps)
            ?_buildVcLayout(blChart):null;
          let hitBuy=null;
          _blBuys.forEach(b=>{
            const _hvcBar=_hoverVcLayout?_hoverVcLayout.get(b._idx):null;
            const bxPx=_hvcBar?_hvcBar.cx:scales.x.getPixelForValue(b._idx);
            const byPx=scales.y.getPixelForValue(b.price);
            if(Math.abs(xPx-bxPx)<=9&&Math.abs(yPx-byPx)<=9) hitBuy=b;
          });
          if(hitBuy){ hit=true; showInsiderBuyPopup(hitBuy,cx,cy); }
          else{ const pop=document.getElementById('insiderBuyPopup'); if(pop) pop.style.display='none'; }
        }
        if(!hit&&_blShowEarnings&&_blEarnings.length){
          const {bottom}=blChart.chartArea;
          const bh=14,bw=16,pad=4;
          const hitY=bottom-bh/2-pad;
          if(Math.abs(yPx-hitY)<=bh+2){
            _blEarnings.forEach(e=>{
              const ex=scales.x.getPixelForValue(e._idx);
              if(Math.abs(xPx-ex)<=bw/2+4) hit=true;
            });
          }
        }
        canvas.style.cursor=hit?'pointer':'crosshair';
      },
      onClick(evt){
        if(!blChart) return;
        const nativeEvt=evt.native||evt;
        const cx=nativeEvt.clientX||0, cy=nativeEvt.clientY||0;
        const scales=blChart.scales;
        const xPx=evt.x, yPx=evt.y;
        if(!_blShowEarnings||!_blEarnings.length) return;
        const {bottom}=blChart.chartArea;
        const bh=14,bw=16,pad=4;
        const hitY=bottom-bh/2-pad;
        if(Math.abs(yPx-hitY)>bh+4) return;
        let hit=null;
        _blEarnings.forEach(e=>{
          const ex=scales.x.getPixelForValue(e._idx);
          if(Math.abs(xPx-ex)<=bw/2+6) hit=e;
        });
        if(!hit) return;
        showEarningsPopup(hit, cx, cy);
      },
      plugins:{
        legend:{display:false},
        zoom:{
          zoom:{wheel:{enabled:false},pinch:{enabled:true},mode:'x',onZoom:()=>syncGIToBuyRange(),onZoomComplete:()=>syncGIToBuyRange()},
          pan:{enabled:true,mode:'x',
            onPan({chart}){
              const sx=chart.scales?.x;
              if(sx&&sx.min<0){
                const span=sx.max-sx.min;
                chart.options.scales.x.min=0;
                chart.options.scales.x.max=span;
                chart.update('none');
              }
              syncGIToBuyRange();
              _syncLookbackBarPos(chart);
            },
            onPanComplete({chart}){
              const sx=chart.scales?.x;
              if(sx&&sx.min<0){
                const span=sx.max-sx.min;
                chart.options.scales.x.min=0;
                chart.options.scales.x.max=span;
                chart.update('none');
              }
              syncGIToBuyRange();
              _syncLookbackBarPos(chart);
            }},
        },
        tooltip:{enabled:false},
      },
      scales:{
        x:{type:'linear',display:_blGIPos!=='lower',min:xRange.min,max:xRange.max,
          grid:{display:false},
          border:{display:false},
          ticks:{
            display:_blGIPos!=='lower',
            maxTicksLimit:10,
            color:'#888',
            font:{family:'JetBrains Mono',size:11,weight:'400'},
            maxRotation:0,
            padding:6,
            callback:v=>{
              const idx=Math.round(v);
              const d=ohlcv[idx];
              if(!d||idx>=ohlcv.length) return '';
              const t=d.t.slice(0,10);
              const mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
              const m=parseInt(t.slice(5,7),10)-1;
              const day=parseInt(t.slice(8,10),10);
              // Show year at Jan, month otherwise, day when zoomed in tight
              const span=Math.abs((Number.isFinite(xRange.max)?xRange.max:ohlcv.length)-(Number.isFinite(xRange.min)?xRange.min:0));
              if(span<=60) return mo[m]+' '+day;
              if(m===0) return t.slice(0,4);
              return mo[m];
            }
          }},
        y:{position:'right',min:yMin,max:yMax,
          grid:{display:false},
          border:{display:false},
          afterFit(scale){scale.paddingLeft=4;},
          ticks:{
            color:'#888',
            font:{family:'JetBrains Mono',size:11,weight:'400'},
            maxTicksLimit:10,
            includeBounds:false,
            padding:4,
            callback:v=>v.toFixed(2)
          }},
      },
    },
    plugins:[yAxisBackgroundPlugin,volumePlugin,indicatorPlugin,wickPlugin,buyLinePlugin,priceLabelPlugin,todayChangePlugin,extendedHoursPlugin,crosshairPlugin,reversalPlugin,earningsPlugin,projectionPlugin,giOverlayPlugin,blLookbackSyncPlugin],
  });
  if(!canvas._blDblClickBound){ canvas.addEventListener('dblclick', blResetChartZoom); canvas._blDblClickBound=true; }
  if(!canvas._blWheelBound){
    canvas.addEventListener('wheel',function(e){
      if(!blChart||!_blOhlcv.length) return;
      e.preventDefault();
      const sx=blChart.scales?.x;
      if(!sx) return;
      const curMin=sx.min, curMax=sx.max;
      const span=curMax-curMin;
      // scroll up (deltaY<0) = zoom in (fewer bars); scroll down = zoom out (more bars)
      const factor=e.deltaY>0?1.15:1/1.15;
      const newSpan=Math.max(10,Math.min(span*factor,(_blOhlcv.length-1)+_blRightBars+1));
      const lastIdx=_blOhlcv.length-1;
      // Right edge: keep at least 2.5 bars of clear space after the last candle
      const newMax=Math.max(curMax, lastIdx+2.5);
      blChart.options.scales.x.max=newMax;
      blChart.options.scales.x.min=Math.max(0,newMax-newSpan);
      blChart.update('none');
      syncGIToBuyRange();
    },{passive:false});
    canvas._blWheelBound=true;
  }
  // Keep chart hidden until relayoutBuyCharts finishes its resize pass,
  // so the resize jitter is never visible. relayoutBuyCharts will restore opacity.
  _blDeferredOpacityRestore=true;
  // Safety fallback: always reveal within 600 ms even if relayout never fires.
  setTimeout(()=>{
    if(_blDeferredOpacityRestore){
      _blDeferredOpacityRestore=false;
      const w=document.getElementById('blChartWrap');
      if(w){w.style.transition='opacity 0.07s ease';w.style.opacity='1';}
    }
  },600);
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    if(_renderToken!==_blRenderToken||ticker!==blCurrentTicker()) return;
    renderGIChart(ticker);
  }));
  blScheduleLowerGIRenderRetries(ticker);
  }catch(err){
    showJsError('renderBuyLevels failed', err);
    console.error(err);
    if(blChart){ try{ blChart.destroy(); }catch(_e){} blChart=null; }
    const _blWrapErr=document.getElementById('blChartWrap');
    if(_blWrapErr) _blWrapErr.style.opacity='1';
  }
}

function renderGIChart(ticker){
  const giHistory=getGIHistory();
  const raw=giHistory[ticker]||[];
  const pts=raw.map(d=>({t:d.t,v:Number(d.v)})).filter(d=>d.t&&Number.isFinite(d.v)).sort((a,b)=>a.t.localeCompare(b.t));
  const alignedPts=blAlignedGIChartPoints(pts);
  const el=document.getElementById('blGISection');
  // If the GI chart is already rendered with data and the canvas is properly sized,
  // just sync the x-range instead of destroying and recreating the whole chart.
  const giCanvas=document.getElementById('giHistChart');
  const canvasReady=giCanvas&&giCanvas.clientWidth>=10&&giCanvas.clientHeight>=5;
  if(giHistChart&&canvasReady&&alignedPts.length&&_blGIPos==='lower'){
    _giPts=alignedPts;
    syncGIToBuyRange();
    // Resolve any deferred opacity restore (no relayoutBuyCharts needed here).
    if(_blDeferredOpacityRestore){
      _blDeferredOpacityRestore=false;
      const w=document.getElementById('blChartWrap');
      if(w){w.style.transition='opacity 0.07s ease';w.style.opacity='1';}
    }
    return;
  }
  // Full destroy/recreate path — hide GI section during the swap.
  el.style.opacity='0';
  if(giHistChart){giHistChart.destroy();giHistChart=null;}
  if(!alignedPts.length||_blGIPos==='off'){
    _giPts=[];el.style.display='none';el.style.opacity='1';
    // GI section hidden → main chart x-axis must be visible (no lower panel to show dates)
    try{if(blChart&&blChart.options?.scales?.x){blChart.options.scales.x.display=true;if(blChart.options.scales.x.ticks)blChart.options.scales.x.ticks.display=true;blChart.update('none');}}catch(_e){}
    relayoutBuyCharts();return;
  }
  if(_blGIPos==='overlay'){
    el.style.display='none';el.style.opacity='1';_giPts=alignedPts;
    // Overlay: no lower panel, main chart needs its x-axis visible
    try{if(blChart&&blChart.options?.scales?.x){blChart.options.scales.x.display=true;if(blChart.options.scales.x.ticks)blChart.options.scales.x.ticks.display=true;blChart.update('none');}}catch(_e){}
    if(blChart)blChart.draw();relayoutBuyCharts();return;
  }
  el.style.display='block';
  // Lower panel is showing → main chart hides its x-axis (dates are in the GI panel)
  try{if(blChart&&blChart.options?.scales?.x){blChart.options.scales.x.display=false;if(blChart.options.scales.x.ticks)blChart.options.scales.x.ticks.display=false;blChart.update('none');}}catch(_e){}
  // If the canvas has no layout dimensions yet (first load), defer and retry
  if(giCanvas&&(giCanvas.clientWidth<10||giCanvas.clientHeight<5)){
    el.style.opacity='1';
    requestAnimationFrame(()=>setTimeout(()=>renderGIChart(ticker),60));
    return;
  }
  _giPts=alignedPts;
  const ctx2=document.getElementById('giHistChart').getContext('2d');
  const vals=_giPts.map(d=>d.v);
  let yMin=Math.min(...vals),yMax=Math.max(...vals);
  if(yMax<=yMin){yMin-=0.5;yMax+=0.5;}
  const xMin=blChart&&blChart.scales&&Number.isFinite(blChart.scales.x.min)?blChart.scales.x.min:0;
  const xMax=blChart&&blChart.scales&&Number.isFinite(blChart.scales.x.max)?blChart.scales.x.max:Math.max(0,_blOhlcv.length?_blOhlcv.length-1:_giPts.length-1);
  giHistChart=new Chart(ctx2,{
    type:'line',
    plugins:[crosshairPlugin],
    data:{
      datasets:[{
        data:_giPts.map(d=>({x:d.x,y:d.v})),
        borderColor:ctx=>giLineGradient(ctx.chart,ctx.chart.scales.y),
        borderWidth:Math.max(2.2,1.5),pointRadius:0,fill:false,tension:0,
        borderCapStyle:'round',borderJoinStyle:'round'
      }]
    },
    options:{
      animation:false,responsive:true,maintainAspectRatio:false,
      layout:{autoPadding:false,padding:{top:2,bottom:2,left:0,right:0}},
      plugins:{legend:{display:false},
        tooltip:{
          callbacks:{
            label:c=>{
              const col=giColorForValue(c.parsed.y);
              return`GI: ${c.parsed.y.toFixed(1)}  ${GISP_ZL[scoreToZone(c.parsed.y)]||''}`;
            },
            labelColor:c=>{const col=giColorForValue(c.parsed.y);return{backgroundColor:col,borderColor:col};}
          },
          font:{family:'JetBrains Mono',size:12},padding:8,displayColors:true
        }},
      scales:{
        x:{type:'linear',min:xMin,max:xMax,
           grid:{display:false},
           border:{display:true,color:'#2a2a2a',width:1},
           ticks:{color:'#888',font:{family:'JetBrains Mono',size:11,weight:'400'},maxRotation:0,maxTicksLimit:10,padding:6,
             callback:v=>{
               const d=_blOhlcv[Math.round(v)];
               if(!d) return '';
               const t=d.t.slice(0,10);
               const mo=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
               const m=parseInt(t.slice(5,7),10)-1;
               return m===0?t.slice(0,4):mo[m];
             }}},
        y:{min:yMin,max:yMax,position:'right',
           afterFit:axis=>{
             const ref=blChart&&blChart.scales&&blChart.scales.y;
             if(ref&&Number.isFinite(ref.width)&&ref.width>0) axis.width=ref.width;
           },
           grid:{display:false},
           ticks:{display:false}}
      }
    }
  });
  el.style.opacity='1';
  syncGIToBuyRange();
  relayoutBuyCharts();
}

// -- GI SIGNAL PANEL --
const GISP_ZONES=['buying','accumulation','neutral','distribution','selling'];
const GISP_ZC={buying:'#22c55e',accumulation:'#86efac',neutral:'#facc15',distribution:'#fb923c',selling:'#ef4444'};
const GISP_ZL={buying:'Buying',accumulation:'Accumulation',neutral:'Neutral',distribution:'Distribution',selling:'Selling'};
const GISP_ZL_S={buying:'Buy',accumulation:'Accum',neutral:'Neutral',distribution:'Dist.',selling:'Sell'};
let _gispZone=null;
let _gispScore=null;
let _projLines=[];  // [{price,label,color,dash}]
const _gispBacktestCache=new Map();
const _gispOptimalStopCache=new Map();
const _gispOptimalStopAnyCache=new Map();

function gispInvalidateTickerCaches(ticker){
  const key=gispNormTicker(ticker);
  if(!key) return;
  const prefix=`${key}|`;
  [..._gispBacktestCache.keys()].forEach(k=>{ if(String(k).startsWith(prefix)) _gispBacktestCache.delete(k); });
  [..._gispOptimalStopCache.keys()].forEach(k=>{ if(String(k).startsWith(prefix)) _gispOptimalStopCache.delete(k); });
  _gispOptimalStopAnyCache.delete(key);
}

function scoreToZone(s){
  if(s==null)return null;
  if(s>=70)return'buying';if(s>=60)return'accumulation';if(s>=45)return'neutral';if(s>=33)return'distribution';
  return'selling';
}

function renderGISPUnifiedMatrix(ticker,zone,allZ){
  const el=document.getElementById('gisp-unified');
  if(!el) return;
  const curZr=allZ[zone]||null;
  const scoreNum=Number.isFinite(Number(_gispScore))?Number(_gispScore):null;
  const scoreColor=scoreNum!=null?giColorForValue(scoreNum):'var(--muted)';
  const zoneColor=GISP_ZC[zone]||'var(--text)';
  const zoneLabel=GISP_ZL[zone]||'';
  const ZL3={buying:'Buy',accumulation:'Acc',neutral:'Ntr',distribution:'Dst',selling:'Sel'};
  const periods=[
    {label:'5D', key:'avg_5d'},
    {label:'10D',key:'avg_10d'},
    {label:'20D',key:'avg_20d'},
    {label:'30D',key:'avg_30d'},
    {label:'50D',key:'avg_50d'},
  ];
  const pColor=v=>{
    const num=Number(v);
    return !Number.isFinite(num)?'var(--muted)':(num>0?'var(--green)':num<0?'var(--red)':'var(--muted)');
  };
  const zFmt=v=>{
    const num=Number(v);
    return Number.isFinite(num)?((num>=0?'+':'')+num.toFixed(1)+'%'):'<span class="gm-loading">...</span>';
  };

  // Header: Period | Buy | Acc | Ntr | Dst | Sel
  let rows=`
    <div class="gm-hdr gm-period"></div>`;
  GISP_ZONES.forEach(z=>{
    const isAct=z===zone;
    rows+=`<div class="gm-hdr${isAct?' gm-act-col':''}" style="color:${GISP_ZC[z]}">${ZL3[z]}</div>`;
  });

  // Data rows - one per period
  periods.forEach(({label,key})=>{
    rows+=`
      <div class="gm-cell gm-period">${label}</div>`;
    GISP_ZONES.forEach(z=>{
      const zr=allZ[z]||null;
      const zv=zr?zr[key]:null;
      const zc=pColor(zv);
      const isAct=z===zone;
      rows+=`<div class="gm-cell gm-zone-col${isAct?' gm-act-col':''}" style="color:${zc}">${zFmt(zv)}</div>`;
    });
  });

  el.innerHTML=`
    <div class="gm-unified-head">
      <span id="gisp-gi-badge" style="font-family:var(--mono);font-size:11px;font-weight:700;color:${scoreColor};margin-left:auto">${scoreNum!=null?'GI '+scoreNum.toFixed(1):''}</span>
    </div>
    <div class="gisp-matrix">${rows}</div>`;
}

function priceLookupSeries(ohlcv){
  return (ohlcv||[])
    .map(d=>({t:d.t,o:Number(d.o),h:Number(d.h),l:Number(d.l),c:Number(d.c)}))
    .filter(d=>d.t&&Number.isFinite(d.c)&&Number.isFinite(d.l)&&Number.isFinite(d.h))
    .sort((a,b)=>a.t.localeCompare(b.t));
}
function priceOnOrAfter(series,dateStr){
  for(let i=0;i<series.length;i++) if(series[i].t>=dateStr) return series[i];
  return null;
}
function priceOnOrBefore(series,dateStr){
  for(let i=series.length-1;i>=0;i--) if(series[i].t<=dateStr) return series[i];
  return null;
}
function firstStopHitLong(series,entryDate,exitDate,stopPx){
  if(!(stopPx>0)) return null;
  for(let i=0;i<series.length;i++){
    const b=series[i];
    if(b.t<entryDate) continue;
    if(b.t>exitDate) break;
    if(Number.isFinite(b.l)&&b.l<=stopPx) return b;
  }
  return null;
}
function computeBacktest(ticker,zone,stopPct=null){
  const cacheKey=`${gispNormTicker(ticker)}|${String(zone||'')}|${Number.isFinite(Number(stopPct)) ? Number(stopPct) : 'na'}`;
  if(_gispBacktestCache.has(cacheKey)) return _gispBacktestCache.get(cacheKey);
  const giHist=(getGIHistory()[ticker]||[]).map(d=>({t:d.t,v:Number(d.v)})).filter(d=>d.t&&Number.isFinite(d.v)).sort((a,b)=>a.t.localeCompare(b.t));
  const priceSeries=priceLookupSeries(getCandleData()[ticker]||[]);
  if(!giHist.length||!priceSeries.length||!zone){ _gispBacktestCache.set(cacheKey,null); return null; }
  const stop=Number(stopPct);
  const useStop=Number.isFinite(stop)&&stop>0;
  const trades=[];
  let currentZone=null, entryBar=null, entryZoneDate=null;
  for(let i=0;i<giHist.length;i++){
    const row=giHist[i];
    const z=scoreToZone(row.v);
    if(currentZone!==zone && z===zone){
      entryBar=priceOnOrAfter(priceSeries,row.t);
      entryZoneDate=row.t;
    }
    if(currentZone===zone && z!==zone && entryBar){
      const exitBar=priceOnOrAfter(priceSeries,row.t) || priceOnOrBefore(priceSeries,row.t);
      if(exitBar && entryBar.c>0){
        let finalExit=exitBar;
        let exitPx=exitBar.c;
        let stopped=false;
        if(useStop){
          const stopPx=entryBar.c*(1-stop/100);
          const hit=firstStopHitLong(priceSeries,entryBar.t,exitBar.t,stopPx);
          if(hit){
            finalExit=hit;
            exitPx=stopPx;
            stopped=true;
          }
        }
        const ret=(exitPx-entryBar.c)/entryBar.c*100;
        const days=Math.max(0,Math.round((new Date(finalExit.t)-new Date(entryBar.t))/86400000));
        trades.push({
          entryDate:entryBar.t, exitDate:finalExit.t, zoneDate:entryZoneDate,
          ret, days, win:ret>0, stopped
        });
      }
      entryBar=null;
      entryZoneDate=null;
    }
    currentZone=z;
  }
  if(entryBar){
    const lastBar=priceSeries[priceSeries.length-1];
    if(lastBar && entryBar.c>0 && lastBar.t>=entryBar.t){
      let finalExit=lastBar;
      let exitPx=lastBar.c;
      let stopped=false;
      if(useStop){
        const stopPx=entryBar.c*(1-stop/100);
        const hit=firstStopHitLong(priceSeries,entryBar.t,lastBar.t,stopPx);
        if(hit){
          finalExit=hit;
          exitPx=stopPx;
          stopped=true;
        }
      }
      const ret=(exitPx-entryBar.c)/entryBar.c*100;
      const days=Math.max(0,Math.round((new Date(finalExit.t)-new Date(entryBar.t))/86400000));
      trades.push({
        entryDate:entryBar.t, exitDate:finalExit.t, zoneDate:entryZoneDate,
        ret, days, win:ret>0, open:!stopped, stopped
      });
    }
  }
  if(!trades.length){ _gispBacktestCache.set(cacheKey,null); return null; }
  const closed=trades.filter(t=>!t.open);
  const sample=closed.length?closed:trades;
  const wins=sample.filter(t=>t.win), losses=sample.filter(t=>!t.win);
  const stoppedCount=sample.filter(t=>t.stopped).length;
  const compound=sample.reduce((acc,t)=>acc*(1+t.ret/100),1);
  const result={
    trades: sample.length,
    totalTrades: trades.length,
    openTrades: trades.length-sample.length,
    winRate: sample.length ? wins.length/sample.length*100 : 0,
    wins:wins.length,
    losses:losses.length,
    avgWin:wins.length ? wins.reduce((a,b)=>a+b.ret,0)/wins.length : 0,
    avgLoss:losses.length ? losses.reduce((a,b)=>a+b.ret,0)/losses.length : 0,
    avgDays:sample.length ? sample.reduce((a,b)=>a+b.days,0)/sample.length : 0,
    totalPnL:sample.reduce((a,b)=>a+b.ret,0),
    compoundPnL:(compound-1)*100,
    stoppedCount
  };
  _gispBacktestCache.set(cacheKey,result);
  return result;
}

function computeOptimalBacktest(ticker,stopPct=null){
  let best=null;
  GISP_ZONES.forEach(z=>{
    const bt=computeBacktest(ticker,z,stopPct);
    if(!bt||!bt.trades) return;
    const score=(Number.isFinite(bt.compoundPnL)?bt.compoundPnL:bt.totalPnL);
    if(!best || score>best.score || (score===best.score && bt.trades>best.bt.trades)) best={zone:z,bt,score};
  });
  return best;
}

function btFmtMoney(v){
  return Number.isFinite(v)?`$${v.toFixed(2)}`:'--';
}

function btFmtSignedPct(v){
  if(!Number.isFinite(v)) return '--';
  return `${v>0?'+':''}${v.toFixed(2)}%`;
}
function gispPlainNum(v, decimals=2){
  const n=Number(v);
  if(!Number.isFinite(n)) return '';
  return n.toFixed(decimals).replace(/\.0+$/,'').replace(/(\.\d*?)0+$/,'$1');
}
function gispCalcATR(n=14){
  const ticker=blCurrentTicker();
  const ohlcv=(ticker&&getCandleData()[ticker])||_blOhlcv||[];
  if(ohlcv.length<n+1) return NaN;
  const slice=ohlcv.slice(-(n+1));
  let trSum=0;
  for(let i=1;i<=n;i++){
    const bar=slice[i],prev=slice[i-1];
    const h=Number(bar?.h),l=Number(bar?.l),pc=Number(prev?.c);
    if(!Number.isFinite(h)||!Number.isFinite(l)||!Number.isFinite(pc)) return NaN;
    trSum+=Math.max(h-l,Math.abs(h-pc),Math.abs(l-pc));
  }
  return trSum/n;
}
function gispSetAtrStop(mult){
  const entryPrice=gispLastClose(blCurrentTicker());
  if(!Number.isFinite(entryPrice)||entryPrice<=0) return;
  const atr=gispCalcATR(14);
  if(!Number.isFinite(atr)||atr<=0) return;
  const stopPrice=Math.round((entryPrice-atr*mult)*100)/100;
  if(stopPrice<=0||stopPrice>=entryPrice) return;
  _blSizerAtrMult=mult;
  _blSizerManualStop=stopPrice;
  const stopEl=document.getElementById('gispManualStop');
  if(stopEl) stopEl.value=String(stopPrice);
  gispSyncAtrButtons();
  gispSyncStopLine();
  saveBuyLevelsPrefs();
  renderGISPPositionSizer(blCurrentTicker(),_gispZone);
}
function gispAtrClearOnManual(){
  if(_blSizerAtrMult!==null){_blSizerAtrMult=null;gispSyncAtrButtons();}
}
function gispSyncAtrButtons(){
  const idMap={0.5:'gispAtr05',1.0:'gispAtr10',1.5:'gispAtr15',2.0:'gispAtr20',2.5:'gispAtr25',3.0:'gispAtr30'};
  Object.entries(idMap).forEach(([m,id])=>{
    const btn=document.getElementById(id);
    if(btn) btn.classList.toggle('active',_blSizerAtrMult===Number(m));
  });
}
function gispGetAutoStopPrice(){ return Number.isFinite(_blSizerLastAutoStop)?_blSizerLastAutoStop:null; }
function gispGetAutoTargetPrice(){ return Number.isFinite(_blSizerLastAutoTarget)?_blSizerLastAutoTarget:null; }
function gispSyncStopLine(explicitPrice){
  const price=explicitPrice!=null?explicitPrice:_blSizerManualStop;
  if(!(price>0)){
    // Remove stale stop line
    const i=_projLines.findIndex(p=>p.label==='Stop');
    if(i>=0){_projLines.splice(i,1);if(blChart&&_blBuysIdxReady) blChart.update('none');}
    return;
  }
  const idx=_projLines.findIndex(p=>p.label==='Stop');
  if(idx>=0){_projLines[idx].price=price;_projLines[idx].color='#ff4d4d';}
  else _projLines.push({price,label:'Stop',color:'#ff4d4d',dash:[6,3],days:0});
  if(blChart&&_blBuysIdxReady) blChart.update('none');
}
function gispSetRMult(mult){
  const entryPrice=gispLastClose(blCurrentTicker());
  if(!Number.isFinite(entryPrice)||entryPrice<=0) return;
  // Use manual stop if set, otherwise fall back to the auto-resolved stop price
  const stopPrice=(_blSizerManualStop>0)?_blSizerManualStop
    :(Number.isFinite(_blSizerLastAutoStop)&&_blSizerLastAutoStop>0?_blSizerLastAutoStop:0);
  if(!(stopPrice>0)||stopPrice>=entryPrice) return;
  const riskPerShare=entryPrice-stopPrice;
  const targetPrice=Math.round((entryPrice+mult*riskPerShare)*100)/100;
  _blSizerRMult=mult;
  _blSizerManualTarget=targetPrice;
  const tEl=document.getElementById('gispManualTarget');
  if(tEl) tEl.value=String(targetPrice);
  gispSyncRMultButtons();
  gispSyncTargetLine();
  saveBuyLevelsPrefs();
  renderGISPPositionSizer(blCurrentTicker(),_gispZone);
}
function gispTargetClearOnManual(){
  if(_blSizerRMult!==null){_blSizerRMult=null;gispSyncRMultButtons();}
}
function gispSyncRMultButtons(){
  const idMap={1.0:'gispRMult10',1.5:'gispRMult15',2.0:'gispRMult20',2.5:'gispRMult25',3.0:'gispRMult30',3.5:'gispRMult35'};
  Object.entries(idMap).forEach(([m,id])=>{
    const btn=document.getElementById(id);
    if(btn) btn.classList.toggle('active',_blSizerRMult===Number(m));
  });
}
function gispSyncTargetLine(explicitPrice){
  const price=explicitPrice!=null?explicitPrice:_blSizerManualTarget;
  if(!(price>0)){
    // Remove stale target line
    const i=_projLines.findIndex(p=>p.label==='Target');
    if(i>=0){_projLines.splice(i,1);if(blChart&&_blBuysIdxReady) blChart.update('none');}
    return;
  }
  const idx=_projLines.findIndex(p=>p.label==='Target');
  if(idx>=0){_projLines[idx].price=price;_projLines[idx].color='#26c26a';}
  else _projLines.push({price,label:'Target',color:'#26c26a',dash:[4,3],days:0});
  if(blChart&&_blBuysIdxReady) blChart.update('none');
}
function gispFmtK(v){
  if(!Number.isFinite(v)) return '--';
  if(Math.abs(v)>=1000) return '$'+(v/1000).toFixed(1)+'K';
  return '$'+v.toFixed(0);
}
function gispSyncPositionSizerInputs(){
  const acctEl=document.getElementById('gispAcctValue');
  const riskCashEl=document.getElementById('gispRiskCash');
  const riskPctEl=document.getElementById('gispRiskPct');
  const maxRiskPctEl=document.getElementById('gispMaxRiskPct');
  const manualStopEl=document.getElementById('gispManualStop');
  if(acctEl && document.activeElement!==acctEl) acctEl.value=gispPlainNum(_blSizerAccountValue,0)||'100000';
  if(riskCashEl && document.activeElement!==riskCashEl) riskCashEl.value=gispPlainNum(_blSizerRiskCash, 2)||'500';
  if(riskPctEl && document.activeElement!==riskPctEl) riskPctEl.value=gispPlainNum(_blSizerRiskPct, 2)||'0.5';
  if(maxRiskPctEl && document.activeElement!==maxRiskPctEl) maxRiskPctEl.value=gispPlainNum(_blSizerMaxRiskPct, 2)||'100';
  if(manualStopEl && document.activeElement!==manualStopEl) manualStopEl.value=_blSizerManualStop>0?gispPlainNum(_blSizerManualStop,2):'';
  const manualTargetEl=document.getElementById('gispManualTarget');
  if(manualTargetEl&&document.activeElement!==manualTargetEl) manualTargetEl.value=_blSizerManualTarget>0?gispPlainNum(_blSizerManualTarget,2):'';
  gispSyncRMultButtons();
  const isPct=_blSizerRiskMode==='pct';
  const mf=document.getElementById('gispModeFixed'); if(mf) mf.classList.toggle('active',!isPct);
  const mp=document.getElementById('gispModePct');   if(mp) mp.classList.toggle('active', isPct);
  const fr=document.getElementById('gispRiskFixedRow'); if(fr) fr.style.display=isPct?'none':'';
  const pr=document.getElementById('gispRiskPctRow');   if(pr) pr.style.display=isPct?'':'none';
  gispSyncAtrButtons();
}
function gispPullPositionSizerInputs(){
  const acct=Number(document.getElementById('gispAcctValue')?.value);
  const riskCash=Number(document.getElementById('gispRiskCash')?.value);
  const riskPct=Number(document.getElementById('gispRiskPct')?.value);
  const maxRiskPct=Number(document.getElementById('gispMaxRiskPct')?.value);
  const manualStopRaw=document.getElementById('gispManualStop')?.value;
  const manualStop=manualStopRaw===''||manualStopRaw==null ? 0 : Number(manualStopRaw);
  _blSizerAccountValue=Number.isFinite(acct)&&acct>=0 ? acct : _blSizerAccountValue;
  _blSizerRiskCash=Number.isFinite(riskCash)&&riskCash>=0 ? riskCash : _blSizerRiskCash;
  _blSizerRiskPct=Number.isFinite(riskPct)&&riskPct>=0 ? riskPct : _blSizerRiskPct;
  _blSizerMaxRiskPct=Number.isFinite(maxRiskPct)&&maxRiskPct>=0 ? maxRiskPct : _blSizerMaxRiskPct;
  _blSizerManualStop=Number.isFinite(manualStop)&&manualStop>0 ? manualStop : 0;
  const manualTargetRaw=document.getElementById('gispManualTarget')?.value;
  const manualTarget=(manualTargetRaw===''||manualTargetRaw==null)?0:Number(manualTargetRaw);
  _blSizerManualTarget=Number.isFinite(manualTarget)&&manualTarget>0?manualTarget:0;
}
function gispSetRiskMode(mode){
  _blSizerRiskMode=mode==='pct'?'pct':'fixed';
  gispSyncPositionSizerInputs();
  saveBuyLevelsPrefs();
  renderGISPPositionSizer(blCurrentTicker(), _gispZone);
}
function gispPositionSizerChanged(){
  gispPullPositionSizerInputs();
  saveBuyLevelsPrefs();
  // renderGISPPositionSizer syncs stop/target lines with resolved prices at the end
  renderGISPPositionSizer(blCurrentTicker(), _gispZone);
}

function gispNormTicker(ticker){
  return String(ticker||'').trim().toUpperCase();
}

function gispLatestGIReading(ticker){
  const key=gispNormTicker(ticker);
  if(!key) return null;
  const giHist=(getGIHistory()[key]||[])
    .map(d=>({t:String(d?.t||''),v:Number(d?.v)}))
    .filter(d=>d.t&&Number.isFinite(d.v))
    .sort((a,b)=>a.t.localeCompare(b.t));
  return giHist.length ? giHist[giHist.length-1] : null;
}

function gispGIReadingForDate(ticker,dateStr){
  const key=gispNormTicker(ticker);
  if(!key||!dateStr) return null;
  const giHist=getGIHistory()[key]||[];
  for(let i=giHist.length-1;i>=0;i--){
    const row=giHist[i]||{};
    const t=String(row.t||'');
    const v=Number(row.v);
    if(!t||!Number.isFinite(v)) continue;
    if(t<=dateStr) return {t,v};
  }
  return null;
}

function gispLastClose(ticker){
  const key=gispNormTicker(ticker);
  if(!key) return NaN;
  const cached=getCandleData()[key]||[];
  if(cached.length){
    const last=Number(cached[cached.length-1]?.c);
    if(Number.isFinite(last)) return last;
  }
  if(blCurrentTicker()===key && Array.isArray(_blOhlcv) && _blOhlcv.length){
    const live=Number(_blOhlcv[_blOhlcv.length-1]?.c);
    if(Number.isFinite(live)) return live;
  }
  return NaN;
}

function ensureFairValueData(ticker){
  const key=gispNormTicker(ticker);
  if(!key) return Promise.resolve(null);
  const cached=FAIR_VALUE_DATA[key];
  const cachedVal=Number(cached?.fair_value);
  if(Number.isFinite(cachedVal) && cachedVal>0) return Promise.resolve(cached);
  if(FAIR_VALUE_PENDING[key]) return FAIR_VALUE_PENDING[key];
  // Route through local server (which proxies dashboard.gekko.app using stored session cookie)
  FAIR_VALUE_PENDING[key]=fetch(`/api/fair-value/${encodeURIComponent(key)}`)
    .then(resp=>resp.ok ? resp.json() : null)
    .then(payload=>{
      const fairValue=Number(payload?.fair_value);
      if(Number.isFinite(fairValue) && fairValue>0){
        FAIR_VALUE_DATA[key]=payload;
        return FAIR_VALUE_DATA[key];
      }
      return null;
    })
    .catch(()=>null)
    .finally(()=>{ delete FAIR_VALUE_PENDING[key]; });
  return FAIR_VALUE_PENDING[key];
}

function renderGISPFairValue(ticker){
  // Fair value disabled — no Gekko account
  const fvEl=document.getElementById('gisp-fairvalue');
  if(fvEl){fvEl.style.display='none';fvEl.innerHTML='';}
  return;
  const key=gispNormTicker(ticker);
  if(!key){fvEl.style.display='none';fvEl.innerHTML='';return;}
  const row=FAIR_VALUE_DATA[key]||null;
  const fairValue=Number(row?.fair_value);
  const lastClose=gispLastClose(key);
  if(!Number.isFinite(fairValue)||fairValue<=0||!Number.isFinite(lastClose)||lastClose<=0){
    if((!Number.isFinite(fairValue)||fairValue<=0) && !FAIR_VALUE_PENDING[key]){
      ensureFairValueData(key).then(found=>{
        if(found && blCurrentTicker()===key) renderGISPFairValue(key);
      });
    }
    fvEl.style.display='none';
    fvEl.innerHTML='';
    return;
  }
  const gapPct=(lastClose/fairValue-1)*100;
  let stateLabel='Near Fair Value';
  let stateColor='var(--amber)';
  if(gapPct<=-1){
    stateLabel='Undervalued';
    stateColor='var(--green)';
  }else if(gapPct>=1){
    stateLabel='Overvalued';
    stateColor='var(--red)';
  }
  // Left = undervalued (negative gapPct), right = overvalued (positive gapPct)
  const markerPct=clampNum(((gapPct+25)/50)*100,2,98);
  const gapTxt=`${gapPct>0?'+':''}${gapPct.toFixed(1)}%`;
  fvEl.style.display='flex';
  fvEl.innerHTML=`
    <div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:4px">
      <span class="gisp-fv-label">Fair Value</span>
      <span style="display:flex;align-items:baseline;gap:5px">
        <span class="gisp-fv-value" style="color:${stateColor}">${btFmtMoney(fairValue)}</span>
        <span style="font-size:9px;font-weight:700;color:${stateColor}">${gapTxt}</span>
      </span>
    </div>
    <div class="gisp-fv-track">
      <div class="gisp-fv-mid"></div>
      <div class="gisp-fv-dot" style="left:${markerPct}%"></div>
    </div>`;
}

function computeOptimalZoneStop(ticker,zone){
  const cacheKey=`${gispNormTicker(ticker)}|${String(zone||'')}`;
  if(_gispOptimalStopCache.has(cacheKey)) return _gispOptimalStopCache.get(cacheKey);
  const candidates=[2,3,4,5,6,7,8,10,12,15,18,20,25];
  let best=null;
  candidates.forEach(stopPct=>{
    const bt=computeBacktest(ticker,zone,stopPct);
    if(!bt||!bt.trades) return;
    const score=Number.isFinite(bt.compoundPnL)?bt.compoundPnL:bt.totalPnL;
    if(!best || score>best.score || (score===best.score && bt.winRate>best.bt.winRate) || (score===best.score && bt.winRate===best.bt.winRate && stopPct<best.stopPct)){
      best={stopPct,bt,score};
    }
  });
  _gispOptimalStopCache.set(cacheKey,best);
  return best;
}

function computeOptimalTickerStop(ticker){
  const key=gispNormTicker(ticker);
  if(!key) return null;
  if(_gispOptimalStopAnyCache.has(key)) return _gispOptimalStopAnyCache.get(key);
  const candidates=[2,3,4,5,6,7,8,10,12,15,18,20,25];
  let best=null;
  GISP_ZONES.forEach(z=>{
    candidates.forEach(stopPct=>{
      const bt=computeBacktest(key,z,stopPct);
      if(!bt||!bt.trades) return;
      const score=Number.isFinite(bt.compoundPnL)?bt.compoundPnL:bt.totalPnL;
      if(!best || score>best.score || (score===best.score && bt.winRate>best.bt.winRate) || (score===best.score && bt.winRate===best.bt.winRate && stopPct<best.stopPct)){
        best={stopPct,bt,score,zone:z,fallback:true};
      }
    });
  });
  _gispOptimalStopAnyCache.set(key,best);
  return best;
}

function gispFixedTargetCandidates(ticker,zone){
  const zr=(ZR_ALL[ticker]||{})[zone]||null;
  return [['5D',zr?.avg_5d,5],['10D',zr?.avg_10d,10],['20D',zr?.avg_20d,20],['30D',zr?.avg_30d,30],['50D',zr?.avg_50d,50]]
    .map(([label,ret,days])=>({label,ret:Number(ret),days}))
    .filter(c=>Number.isFinite(c.ret)&&c.ret>0);
}
function gispTargetReturnTolerance(bestRet){
  const n=Math.abs(Number(bestRet)||0);
  return Math.max(0.20, Math.min(0.75, n*0.08));
}
function gispPickEfficientTarget(candidates){
  if(!Array.isArray(candidates)||!candidates.length) return null;
  const bestRet=Math.max(...candidates.map(c=>Number(c.ret)).filter(Number.isFinite));
  if(!Number.isFinite(bestRet)) return null;
  const tol=gispTargetReturnTolerance(bestRet);
  const comparable=candidates.filter(c=>Number.isFinite(c.ret)&&c.ret>0&&c.ret>=bestRet-tol);
  if(!comparable.length) return null;
  comparable.sort((a,b)=>(a.days??999)-(b.days??999)||(b.ret-a.ret));
  return Object.assign({}, comparable[0], {bestRet, tolerance:tol});
}
function computeOptimalZoneTarget(ticker,zone,bt=null){
  const fixedTargets=gispFixedTargetCandidates(ticker,zone);
  const efficient=gispPickEfficientTarget(fixedTargets);
  if(efficient) return efficient;
  if(bt&&Number.isFinite(bt.avgWin)&&bt.avgWin>0){
    return {label:'Zone Exit',ret:bt.avgWin,days:Number.isFinite(bt.avgDays)?bt.avgDays:null};
  }
  return null;
}
function renderGISPPositionSizer(ticker,zone){
  const out=document.getElementById('gispSizerOut');
  if(!out) return;
  const key=gispNormTicker(ticker);
  if(!key){
    out.innerHTML='<div class="gisp-sizer-note">Select a ticker to size from the current chart stop.</div>';
    return;
  }
  const entryPrice=gispLastClose(key);
  const atr=gispCalcATR(14);
  const atrStopPrice=(Number.isFinite(entryPrice)&&entryPrice>0&&Number.isFinite(atr)&&atr>0)
    ? Math.round((entryPrice-atr*1.0)*100)/100 : NaN;

  // On ticker change: clear fields → Auto mode, reset button states
  if(key!==_blSizerAutoFilledKey){
    _blSizerAutoFilledKey=key;
    _blSizerAutoFilledTargetKey=key;
    _blSizerManualStop=0;
    _blSizerManualTarget=0;
    _blSizerAtrMult=null;
    _blSizerRMult=null;
    const stopEl=document.getElementById('gispManualStop');
    const tEl=document.getElementById('gispManualTarget');
    if(stopEl) stopEl.value='';
    if(tEl) tEl.value='';
    gispSyncAtrButtons();
    gispSyncRMultButtons();
    saveBuyLevelsPrefs();
    // Note: do NOT call blChart.update() here — _blBuys._idx may not be mapped yet
    // and would corrupt the insider dot positions. The sync calls at the end of this
    // function (gispSyncStopLine/Target) handle the chart update correctly.
  }

  // Stale-check: if saved stop/target are clearly wrong for this ticker's price, clear them
  const _stopFieldFocused=document.activeElement===document.getElementById('gispManualStop');
  const _targetFieldFocused=document.activeElement===document.getElementById('gispManualTarget');
  if(!_stopFieldFocused&&Number.isFinite(entryPrice)&&entryPrice>0&&_blSizerManualStop>0&&
     (_blSizerManualStop>=entryPrice||_blSizerManualStop<entryPrice*0.5)){
    _blSizerManualStop=0; _blSizerAtrMult=null;
    const stopEl=document.getElementById('gispManualStop'); if(stopEl) stopEl.value='';
    gispSyncAtrButtons();
  }
  if(!_targetFieldFocused&&Number.isFinite(entryPrice)&&entryPrice>0&&_blSizerManualTarget>0&&
     (_blSizerManualTarget<=entryPrice||_blSizerManualTarget>entryPrice*2.5)){
    _blSizerManualTarget=0; _blSizerRMult=null;
    const tEl=document.getElementById('gispManualTarget'); if(tEl) tEl.value='';
    gispSyncRMultButtons();
  }

  // Resolve stop: manual value if set, else backtest zone stop, else ATR stop
  const manualStop=Number(_blSizerManualStop)||0;
  const usingManualStop=manualStop>0&&Number.isFinite(entryPrice)&&manualStop<entryPrice;
  let autoStopPrice=atrStopPrice;
  let autoStopSrc='ATRx1';
  if(!usingManualStop){
    const btStop=computeOptimalZoneStop(key,zone)||computeOptimalTickerStop(key);
    if(btStop&&Number.isFinite(entryPrice)&&entryPrice>0){
      const bsPrice=Math.round(entryPrice*(1-btStop.stopPct/100)*100)/100;
      if(bsPrice>0&&bsPrice<entryPrice){ autoStopPrice=bsPrice; autoStopSrc=`BT ${btStop.stopPct}%${btStop.fallback?' (any zone)':''}`; }
    }
  }
  const stopPrice=usingManualStop ? manualStop : autoStopPrice;
  const riskPerShare=(Number.isFinite(entryPrice)&&Number.isFinite(stopPrice))?(entryPrice-stopPrice):NaN;
  const accountValue=Math.max(0,Number(_blSizerAccountValue)||0);
  const maxAllocPct=Math.max(0,Number(_blSizerMaxRiskPct)||0);
  if(!Number.isFinite(entryPrice)||entryPrice<=0){
    out.innerHTML='<div class="gisp-sizer-note">No price available for this ticker.</div>';
    return;
  }
  if(!Number.isFinite(stopPrice)||stopPrice<=0||!Number.isFinite(riskPerShare)||riskPerShare<=0){
    out.innerHTML='<div class="gisp-sizer-note">'+(manualStop>0&&manualStop>=entryPrice?'Stop price must be below entry price.':'No stop available for this zone yet — enter a stop level to calculate.')+'</div>';
    return;
  }
  if(!(accountValue>0)){
    out.innerHTML='<div class="gisp-sizer-note">Enter an account value above $0 to calculate shares.</div>';
    return;
  }
  // Allocated capital = account × max port % (or full account if no cap set)
  const maxAllocDollars=maxAllocPct>0?accountValue*(maxAllocPct/100):accountValue;
  let riskDollars, riskSub;
  if(_blSizerRiskMode==='pct'){
    const rp=Math.max(0,Number(_blSizerRiskPct)||0);
    // Risk % applies to allocated capital, not total account
    riskDollars=maxAllocDollars*(rp/100);
    riskSub=`${rp.toFixed(2)}% of alloc`;
  }else{
    const fixedRisk=Math.max(0,Number(_blSizerRiskCash)||0);
    // Cap fixed risk so it can't imply more shares than maxAllocDollars allows
    const maxRiskFromAlloc=maxAllocDollars*(riskPerShare/entryPrice);
    riskDollars=Number.isFinite(maxRiskFromAlloc)&&maxRiskFromAlloc>0?Math.min(fixedRisk,maxRiskFromAlloc):fixedRisk;
    riskSub=`Fixed ${btFmtMoney(riskDollars)}`;
  }
  if(!(riskDollars>0)){
    out.innerHTML='<div class="gisp-sizer-note">Enter a risk amount above $0 to calculate shares.</div>';
    return;
  }
  const sharesFromRisk=Math.floor(riskDollars/riskPerShare);
  // Position size always capped at allocated capital
  const sharesFromAlloc=Math.floor(maxAllocDollars/entryPrice);
  const shares=Math.max(0,Math.min(sharesFromRisk,sharesFromAlloc));
  const positionValue=shares*entryPrice;
  const actualRisk=shares*riskPerShare;
  const stopPctActual=((entryPrice-stopPrice)/entryPrice*100);
  const isCapped=sharesFromAlloc<sharesFromRisk;
  const stopSrc=_blSizerAtrMult!==null?`ATRx${_blSizerAtrMult}`:(usingManualStop?'Manual':autoStopSrc);
  const riskPctOfAcct=accountValue>0?(actualRisk/accountValue*100):0;
  const positionPct=accountValue>0?(positionValue/accountValue*100):0;
  const sharesClass=isCapped?'gisp-value-neu':'gisp-value-pos';
  // Resolve target: manual → backtest zone → 2R from stop → nothing
  const btForTarget=computeBacktest(key,zone);
  const targetChoice=computeOptimalZoneTarget(key,zone,btForTarget||null);
  const btTargetPrice=(Number.isFinite(entryPrice)&&targetChoice)?Math.round(entryPrice*(1+targetChoice.ret/100)*100)/100:NaN;
  let autoTargetPrice=btTargetPrice;
  let autoTargetSrc=targetChoice?targetChoice.label:'';
  if(!Number.isFinite(autoTargetPrice)&&riskPerShare>0){
    // Fall back to 2R when no backtest data available
    autoTargetPrice=Math.round((entryPrice+2*riskPerShare)*100)/100;
    autoTargetSrc='2R';
  }
  const usingManualTarget=_blSizerManualTarget>0&&_blSizerManualTarget>entryPrice;
  const resolvedTargetPrice=usingManualTarget?_blSizerManualTarget:(Number.isFinite(autoTargetPrice)&&autoTargetPrice>entryPrice?autoTargetPrice:NaN);
  const rewardPerShare=Number.isFinite(resolvedTargetPrice)?(resolvedTargetPrice-entryPrice):NaN;
  const rewardRisk=(Number.isFinite(rewardPerShare)&&rewardPerShare>0&&riskPerShare>0)?(rewardPerShare/riskPerShare):NaN;
  const potentialProfit=(Number.isFinite(rewardPerShare)&&rewardPerShare>0)?(shares*rewardPerShare):NaN;
  const targetPct=(Number.isFinite(resolvedTargetPrice)&&entryPrice>0)?((resolvedTargetPrice-entryPrice)/entryPrice*100):NaN;
  const targetSrc=_blSizerRMult!==null?`${_blSizerRMult}R`:(usingManualTarget?'Manual':autoTargetSrc);
  // ---- v2 rendering ----
  const rrClass = Number.isFinite(rewardRisk) ? (rewardRisk>=2?'rr-good':rewardRisk>=1?'rr-ok':'rr-bad') : 'rr-ok';
  const rrVerdictClass = Number.isFinite(rewardRisk) ? (rewardRisk>=2?'good':rewardRisk>=1?'warn':'bad') : 'warn';
  const rrVerdict = Number.isFinite(rewardRisk) ? (rewardRisk>=2?'Good':rewardRisk>=1?'Marginal':'Poor') : '—';

  // RR bar geometry: stop ... entry ... target positioned proportionally
  let rrBarHtml = '';
  if (Number.isFinite(resolvedTargetPrice) && riskPerShare>0 && rewardPerShare>0) {
    const totalRange = riskPerShare + rewardPerShare;
    const entryPctPos = (riskPerShare/totalRange) * 100;
    rrBarHtml = `
      <div class="gsz-rr" title="Stop $${stopPrice.toFixed(2)} → Entry $${entryPrice.toFixed(2)} → Target $${resolvedTargetPrice.toFixed(2)}">
        <div class="gsz-rr-fill-risk" style="left:0;width:${entryPctPos}%"></div>
        <div class="gsz-rr-fill-reward" style="left:${entryPctPos}%;right:0"></div>
        <div class="gsz-rr-entry" style="left:${entryPctPos}%"></div>
        <div class="gsz-rr-pct left" style="color:#ff8a8a">-${stopPctActual.toFixed(1)}%</div>
        <div class="gsz-rr-pct right" style="color:#6be2a4">+${targetPct.toFixed(1)}%</div>
      </div>`;
  }

  const cappedBadge = isCapped
    ? ` <span class="gsz-badge warn" title="Share count capped by Max Port %">CAPPED</span>`
    : '';

  const profitHtml = Number.isFinite(potentialProfit)
    ? `<span class="gsz-split-dollar reward">${gispFmtK(potentialProfit)}</span><span class="gsz-split-pct">${((v=>(v%1===0?v.toFixed(0):v.toFixed(2)))(potentialProfit/accountValue*100))}% acct</span>`
    : `<span class="gsz-split-dollar" style="color:var(--muted)">—</span>`;

  const targetPriceHtml = Number.isFinite(resolvedTargetPrice)
    ? `<span class="gsz-split-price reward">$${resolvedTargetPrice.toFixed(2)}</span>`
    : `<span class="gsz-split-price" style="color:var(--muted)">—</span>`;

  const targetDelta = Number.isFinite(targetPct)
    ? `<span class="gsz-split-delta" style="color:#6be2a4">+${targetPct.toFixed(1)}%</span>`
    : '';

  out.innerHTML = `
    <div class="gsz-results">
      <div class="gsz-hero">
        <div class="gsz-hero-cell">
          <div class="gsz-hero-label">
            <span>Shares</span>
            ${cappedBadge}
            <button class="gsz-copy-btn" onclick="gispCopyShares(${shares},this)" title="Copy share count">COPY</button>
          </div>
          <div class="gsz-hero-val ${isCapped?'capped':''}">${shares.toLocaleString()}</div>
          <div class="gsz-hero-sub">${gispFmtK(positionValue)}</div>
          <div class="gsz-hero-sub">${positionPct%1===0?positionPct.toFixed(0):positionPct.toFixed(1)}% of acct</div>
        </div>
        <div class="gsz-hero-cell right">
          <div class="gsz-hero-label"><span>Risk / Reward</span> <span class="gsz-badge ${rrVerdictClass}">${rrVerdict}</span></div>
          <div class="gsz-hero-val ${rrClass}">${Number.isFinite(rewardRisk)?rewardRisk.toFixed(2)+'x':'—'}</div>
          <div class="gsz-hero-sub">${Number.isFinite(resolvedTargetPrice)?`${gispFmtK(actualRisk)} risked → ${Number.isFinite(potentialProfit)?gispFmtK(potentialProfit):'—'} potential`:'Set a target to see reward'}</div>
        </div>
      </div>

      ${rrBarHtml}

      <div class="gsz-split">
        <div class="gsz-split-cell risk">
          <div class="gsz-split-head">
            <span class="gsz-split-title">Downside · Stop</span>
            <span class="gsz-split-src">${stopSrc||''}</span>
          </div>
          <div><span class="gsz-split-price risk">$${stopPrice.toFixed(2)}</span></div>
          <div><span class="gsz-split-dollar risk">−${gispFmtK(actualRisk)}</span><span class="gsz-split-pct">${riskPctOfAcct%1===0?riskPctOfAcct.toFixed(0):riskPctOfAcct.toFixed(2)}% acct</span></div>
        </div>
        <div class="gsz-split-cell reward">
          <div class="gsz-split-head">
            <span class="gsz-split-title">Upside · Target</span>
            <span class="gsz-split-src">${targetSrc||''}</span>
          </div>
          <div>${targetPriceHtml}</div>
          <div>${profitHtml}</div>
        </div>
      </div>

      <div class="gsz-meta" style="flex-direction:column;gap:3px">
        <span class="gsz-meta-item"><span class="k">Entry</span><span class="v">$${entryPrice.toFixed(2)}</span></span>
        <span class="gsz-meta-item"><span class="k">Per share</span><span class="v">−$${riskPerShare.toFixed(2)}${Number.isFinite(rewardPerShare)&&rewardPerShare>0?' / +$'+rewardPerShare.toFixed(2):''}</span></span>
        <span class="gsz-meta-item"><span class="k">Position</span><span class="v">$${Math.round(positionValue).toLocaleString()}</span></span>
      </div>
    </div>`;
  // Cache resolved auto prices so steppers can seed from them when fields are empty
  if(!(_blSizerManualStop>0)) _blSizerLastAutoStop=Number.isFinite(stopPrice)?stopPrice:NaN;
  if(!(_blSizerManualTarget>0)) _blSizerLastAutoTarget=Number.isFinite(resolvedTargetPrice)?resolvedTargetPrice:NaN;
  // Always sync chart lines with resolved prices (works for both manual and auto mode)
  gispSyncStopLine(stopPrice);
  gispSyncTargetLine(Number.isFinite(resolvedTargetPrice)?resolvedTargetPrice:null);
}

// Copy share count to clipboard and flash the button
function gispCopyShares(shares, btn){
  try {
    navigator.clipboard.writeText(String(shares));
    if (btn) {
      const original = btn.textContent;
      btn.textContent = 'COPIED';
      btn.classList.add('copied');
      setTimeout(()=>{ btn.textContent = original; btn.classList.remove('copied'); }, 1200);
    }
  } catch(e) { /* no-op */ }
}

function renderGISPBacktest(ticker,zone){
  const btEl=document.getElementById('gisp-backtest');
  // If OHLCV not loaded yet, fetch it then re-render
  if(ticker&&(!getCandleData()[ticker]||!getCandleData()[ticker].length)){
    btEl.innerHTML='<div style="color:var(--muted);font-size:9px">Loading price history...</div>';
    blEnsureTickerOHLCV(ticker).then(()=>renderGISPBacktest(ticker,zone)).catch(()=>{});
    return;
  }
  const bt=computeBacktest(ticker,zone);
  if(bt){
    const wc=bt.winRate>=50?'var(--green)':'var(--red)';
    const ohlcv=getCandleData()[ticker]||[];
    const lastClose=ohlcv.length?ohlcv[ohlcv.length-1].c:null;
    const stopChoice=computeOptimalZoneStop(ticker,zone) || computeOptimalTickerStop(ticker);
    const targetChoice=computeOptimalZoneTarget(ticker,zone,bt);
    const targetPrice=(lastClose&&targetChoice)?lastClose*(1+targetChoice.ret/100):null;
    const stopPrice=(lastClose&&stopChoice)?lastClose*(1-stopChoice.stopPct/100):null;
    const rewardRisk=(Number.isFinite(targetPrice)&&Number.isFinite(stopPrice)&&targetPrice>lastClose&&stopPrice<lastClose)
      ? (targetPrice-lastClose)/(lastClose-stopPrice)
      : null;
    const stopPctTxt=stopChoice?`${stopChoice.stopPct.toFixed(stopChoice.stopPct%1?1:0)}%`:'';
    const zoneLabel=GISP_ZL[zone]||'Unknown';
    const zoneColor=GISP_ZC[zone]||'var(--text)';
    const scoreNum=Number.isFinite(Number(_gispScore)) ? Number(_gispScore) : null;
    const scoreColor=scoreNum!=null ? giColorForValue(scoreNum) : 'var(--muted)';
    // Update GI badge in unified matrix if it's there
    const giBadge=document.getElementById('gisp-gi-badge');
    if(giBadge){giBadge.textContent=scoreNum!=null?`GI ${scoreNum.toFixed(1)}`:'';giBadge.style.color=scoreNum!=null?scoreColor:'';}
    const bv=(main,sub='')=>`<span class="bt-main">${main}</span>${sub?`<span class="bt-sub">${sub}</span>`:''}`;
    // 2x3 grid: [Win Rate | Wins/Losses] [Target | Stop] [Reward/Risk | Avg Hold]
    const cells=[
      ['Win Rate', bv(`<span style="color:${wc}">${bt.winRate.toFixed(1)}%</span>`)],
      ['Wins / Losses', bv(`${bt.wins} / ${bt.losses}`)],
      ['Target', targetChoice&&Number.isFinite(targetPrice)
        ? bv(`<span style="color:var(--green)">${btFmtMoney(targetPrice)}</span>`,`${btFmtSignedPct(targetChoice.ret)} | ${targetChoice.label}`)
        : bv(`<span style="color:var(--muted)">No data</span>`)],
      ['Stop', stopChoice&&Number.isFinite(stopPrice)
        ? bv(`<span style="color:var(--red)">${btFmtMoney(stopPrice)}</span>`,`-${stopPctTxt} | ${stopChoice.bt.stoppedCount||0} stopped`)
        : bv(`<span style="color:var(--muted)">No data</span>`)],
      ['Reward / Risk', Number.isFinite(rewardRisk)
        ? bv(`${rewardRisk.toFixed(2)}x`)
        : bv(`<span style="color:var(--muted)">--</span>`)],
      ['Avg Hold', bv(`${bt.avgDays.toFixed(1)} days`)],
    ];
    btEl.innerHTML=`<div class="bt-grid">${
      cells.map(([k,v])=>`<div class="bt-metric"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('')
    }</div>`;
  }else{
    btEl.innerHTML='<div style="color:var(--muted);font-size:9px">Not enough matching GI and price history for backtest.</div>';
  }
}

function gispCalc(){
  const ticker=blCurrentTicker();
  if(!ticker) return;
  // Fetch OHLCV if not yet loaded, then recalc
  if(!getCandleData()[ticker]||!getCandleData()[ticker].length){
    blEnsureTickerOHLCV(ticker).then(()=>gispCalc()).catch(()=>{});
    return;
  }
  // Reset sizer stop/target when ticker changes so stale prices aren't drawn
  // before renderGISPPositionSizer() has a chance to auto-fill the new ticker's values.
  // Also clear the DOM inputs so gispPullPositionSizerInputs() can't pull back stale values.
  if(ticker!==_blSizerAutoFilledKey||ticker!==_blSizerAutoFilledTargetKey){
    _blSizerManualStop=0;
    _blSizerManualTarget=0;
    _blSizerAutoFilledKey='';
    _blSizerAutoFilledTargetKey='';
    const _se=document.getElementById('gispManualStop'); if(_se) _se.value='';
    const _te=document.getElementById('gispManualTarget'); if(_te) _te.value='';
  }
  // Get entry reference for projection lines — supports historical lookback
  const ohlcv=getCandleData()[ticker]||[];
  const lastIdx=ohlcv.length-1;
  const anchorOffset=Math.min(Math.max(0,_blProjLookback||0),Math.max(0,lastIdx));
  const anchorIdx=Math.max(0,lastIdx-anchorOffset);
  const entry=ohlcv.length?ohlcv[anchorIdx].c:null;
  _projLines=[];
  // Determine which GI zone to use for projections.
  // In historical lookback mode, look up what zone the ticker was actually in
  // on that date from GI_HISTORY, so the stop/target percentages reflect
  // what the system would have predicted at that moment — not today's zone.
  let effectiveZone=_gispZone;
  let effectiveScore=_gispScore;
  if(_blProjLookback>0 && anchorIdx>=0){
    const anchorDate=String(ohlcv[anchorIdx]?.t||'');
    if(anchorDate){
      const giHist=(getGIHistory()[ticker]||[]).slice().sort((a,b)=>a.t.localeCompare(b.t));
      // Walk backwards to find the most recent GI reading at or before anchor date
      for(let i=giHist.length-1;i>=0;i--){
        if(giHist[i].t<=anchorDate){
          effectiveScore=giHist[i].v;
          effectiveZone=scoreToZone(effectiveScore);
          break;
        }
      }
    }
  }
  if(entry&&effectiveZone){
    _projLines.push({price:entry,label:'Entry',color:'#94a3b8',dash:[4,4],days:0});
    // Target projection hash marks (5D/10D/20D/30D/50D)
    const zrTgt=(ZR_ALL[ticker]||{})[effectiveZone]||null;
    if(zrTgt){
      const tgts=[
        ['5D', zrTgt.avg_5d,  5, '#a78bfa'],
        ['10D',zrTgt.avg_10d,10, '#60a5fa'],
        ['20D',zrTgt.avg_20d,20, '#34d399'],
        ['30D',zrTgt.avg_30d,30, '#2dd4bf'],
        ['50D',zrTgt.avg_50d,50, '#c084fc'],
      ];
      tgts.forEach(([lbl,ret,days,col])=>{
        if(ret!=null&&Number.isFinite(Number(ret))){
          _projLines.push({price:entry*(1+Number(ret)/100),label:lbl,color:col,dash:[],days});
        }
      });
    }
    // Optimal stop loss from historical stop scan for that zone
    const stopChoice=computeOptimalZoneStop(ticker,effectiveZone) || computeOptimalTickerStop(ticker);
    if(stopChoice&&stopChoice.stopPct>0){
      const stopPrice=entry*(1-stopChoice.stopPct/100);
      _projLines.push({price:stopPrice,label:'Stop',color:'#ef4444',dash:[6,3],days:0});
    }
  }
  if(blChart){
    syncGIToBuyRange();
    // Only update chart if _blBuys._idx has been mapped; otherwise dots render at NaN positions.
    // renderBuyLevels() will do the full redraw once _idx mapping is complete.
    if(_blBuysIdxReady) blChart.update('none');
  }
  if(ticker&&_gispZone){
    renderGISPBacktest(ticker,_gispZone);
    // renderGISPPositionSizer will sync stop/target lines with resolved prices (incl. auto mode)
    renderGISPPositionSizer(ticker,_gispZone);
  }
}

function renderGISignalPanel(ticker){
  const content=document.getElementById('gisp-content');
  const empty=document.getElementById('gisp-empty');
  if(!ticker){_gispScore=null;_gispZone=null;renderGISPFairValue(null);renderGISPPositionSizer(null,null);content.style.display='none';empty.style.display='block';return;}
  // Keep the left panel synced with the GI chart by preferring the latest GI history point.
  let score=null,tier=null;
  const latestGI=gispLatestGIReading(ticker);
  if(latestGI) score=latestGI.v;
  if(score==null){const hold=(HOLDINGS||[]).find(h=>h.ticker===ticker);if(hold){score=hold.gi_score;tier=hold.gi_tier;}}
  if(score==null){const zrR=ZR_DATA.find(r=>r.ticker===ticker);if(zrR){score=zrR.gi_score;tier=zrR.gi_tier;}}
  if(score==null){
    const giHist=(getGIHistory()[ticker]||[]).map(d=>Number(d.v)).filter(Number.isFinite);
    if(giHist.length) score=giHist[giHist.length-1];
  }
  const zone=scoreToZone(score);
  _gispZone=zone;
  const scoreNum=Number.isFinite(Number(score))?Number(score):null;
  _gispScore=scoreNum;
  // All zone returns for this ticker
  const allZ=ZR_ALL[ticker]||{};
  const curZr=allZ[zone]||null;
  renderGISPUnifiedMatrix(ticker,zone,allZ);
  renderGISPFairValue(ticker);
  gispCalc();
  renderGISPBacktest(ticker,zone);
  renderGISPPositionSizer(ticker,zone);
  content.style.display='flex';empty.style.display='none';
}

// -- TAB 6: GI ZONE RETURNS --
// retCell returns a full <td> with gradient background (same style as Themes tab)
function retCell(v,scale){
  if(v==null||!Number.isFinite(v)) return '<td><span class="muted">-</span></td>';
  const bg=thRetBg(v,scale||12);
  const sign=v>=0?'+':'';
  const fw=Math.abs(v)>=5?'700':'400';
  const inner=`<span style="color:#f0f0f0;font-family:var(--mono);font-size:12px;font-weight:${fw}">${sign}${v.toFixed(2)}%</span>`;
  return bg?`<td style="background:${bg};padding:0 8px">${inner}</td>`:`<td>${inner}</td>`;
}
const zrSt=Object.assign(mkState(ZR_DATA,'avg_20d',-1),{ps:25});
_regSortSlot('zr',()=>zrSt);
function zrFilter(){
  const q=document.getElementById('zrS').value.trim().toLowerCase();
  const zone=document.getElementById('zrZone').value;
  const minN=parseInt(document.getElementById('zrMinN').value)||0;
  const ibPeriod=parseInt(document.getElementById('zrIBPeriod').value)||0;
  const cutoff=ibPeriod?Date.now()-ibPeriod*86400000:null;
  zrSt.filtered=ZR_DATA.filter(r=>{
    if(zone&&r.zone!==zone)return false;
    if(r.n<minN)return false;
    if(q&&!r.ticker.toLowerCase().includes(q)&&!(r.company||'').toLowerCase().includes(q))return false;
    if(cutoff){
      const recent=((INSIDER_BUY_INDEX[r.ticker]||[]).filter(x=>new Date(x.d).getTime()>=cutoff).map(x=>x.k).filter(Boolean).filter((v,i,a)=>a.indexOf(v)===i).length);
      if(recent<1) return false;
    }
    return true;
  });
  doSort(zrSt);zrSt.pg=1;renderZR();
}
function zrSort(){
  const col=document.getElementById('zrSortCol').value;
  zrSt.sc=col;zrSt.sd=-1;
  document.querySelectorAll('#tab-zreturns thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add('sort-desc');});
  doSort(zrSt);zrSt.pg=1;renderZR();
}
function zrSortBy(col){
  if(zrSt.sc===col)zrSt.sd*=-1;else{zrSt.sc=col;zrSt.sd=-1;}
  syncSortSelect('zrSortCol',col);
  document.querySelectorAll('#tab-zreturns thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add(zrSt.sd===1?'sort-asc':'sort-desc');});
  doSort(zrSt);zrSt.pg=1;renderZR();
}
function zrPSChange(){zrSt.ps=parseInt(document.getElementById('zrPS').value);zrSt.pg=1;renderZR();}
function renderZRPage(p){goPage(zrSt,p,renderZR);}
function renderZR(){
  const s=zrSt,start=(s.pg-1)*s.ps,page=s.filtered.slice(start,start+s.ps);
  document.getElementById('zrBody').innerHTML=page.map((r,i)=>`
    <tr>
      <td class="sym-cell">${tickerLinkCell(r.ticker, r)}</td>
      <td class="muted" style="max-width:160px;overflow:hidden;text-overflow:ellipsis" title="${r.company||BL_TICKER_INFO[r.ticker]||''}">${r.company||BL_TICKER_INFO[r.ticker]||'-'}</td>
      <td class="label-cell" style="max-width:130px;overflow:hidden;text-overflow:ellipsis">${r.sector||'-'}</td>
      <td>${hoverCount(r.insider_buys,'var(--green)',r.insider_detail,'ins')}</td>
      <td>${hoverCount(r.manager_count,'var(--green)',r.manager_detail,'mgr')}</td>
      ${retCell(r.avg_5d,  5)}
      ${retCell(r.avg_10d, 8)}
      ${retCell(r.avg_20d,12)}
      ${retCell(r.avg_30d,18)}
      ${retCell(r.avg_50d,25)}
      <td class="muted" style="font-size:10px">${r.n}</td>
      <td style="text-align:center">${giBadge(r.gi_score,r.gi_tier)}</td>
    </tr>`).join('');
  mkPag(s,'zrPag','renderZR');
  setCountMeta('zrCnt', `${s.filtered.length.toLocaleString()} rows`, 0, false);
}

// -- TAB: SIGNALS --
// Format helpers matching gekko_backtest.html style
function rvFmtScore(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  const c=n>=70?'var(--green)':n>=50?'var(--amber)':n>=30?'var(--orange)':'var(--red)';
  const bar=Math.round(n/10);
  const filled='█'.repeat(bar)+'░'.repeat(10-bar);
  return `<span style="color:${c};font-family:var(--mono);font-size:11px">${n.toFixed(1)}</span>`
        +`<span style="color:${c};font-family:var(--mono);font-size:9px;opacity:0.6;margin-left:4px">${filled}</span>`;
}
function rvFmtRobust(v){
  const n=Number(v);
  if(!Number.isFinite(n)) return '<span style="color:var(--muted)">—</span>';
  const c=n>=8?'var(--green)':n>=5?'var(--amber)':'var(--red)';
  const lbl=n>=9?'confirmed':n>=7?'strong':n>=5?'moderate':n>=3?'weak':'isolated';
  return `<span style="color:${c};font-family:var(--mono)">${n}/10</span>`
        +`<span style="color:${c};font-size:9px;margin-left:4px;opacity:0.7">${lbl}</span>`;
}
function rvGiBadge(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  let cls,bg,fg;
  if(n>=70){bg='rgba(34,197,94,0.18)';fg='var(--green)';}
  else if(n>=60){bg='rgba(34,197,94,0.11)';fg='#86efac';}
  else if(n>=45){bg='rgba(147,161,181,0.12)';fg='var(--muted)';}
  else if(n>=33){bg='rgba(249,115,22,0.14)';fg='var(--orange)';}
  else{bg='rgba(239,68,68,0.14)';fg='var(--red)';}
  return `<span style="display:inline-block;padding:1px 7px;border-radius:999px;background:${bg};color:${fg};font-family:var(--mono);font-size:11px;font-weight:700">${n.toFixed(0)}</span>`;
}
function rvSourceBadge(src,mode){
  const isGI=(String(src||'GI').toUpperCase()!=='CUSTOM');
  const bg=isGI?'rgba(96,165,250,0.14)':'rgba(245,158,11,0.14)';
  const bd=isGI?'rgba(96,165,250,0.28)':'rgba(245,158,11,0.28)';
  const fg=isGI?'var(--blue)':'var(--amber)';
  const label=isGI?'GI':'Custom';
  const sm=String(mode||'').toLowerCase();
  const modeLabel=isGI?'reversal':sm==='gi_style'?'gi-style':sm==='reversal'?'reversal':sm==='mechanics_reversal'?'mech-rev':sm==='mechanics_continuation'?'mech-cont':sm==='native_relaxed'?'relaxed':'native';
  return `<div style="display:flex;flex-direction:column;gap:2px;min-width:60px">`
        +`<span style="display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid ${bd};background:${bg};color:${fg};font-size:10px;font-weight:700;text-align:center">${label}</span>`
        +`<span style="font-size:9px;color:var(--muted);text-align:center">${modeLabel}</span>`
        +`</div>`;
}
function rvModeBadge(src,mode){
  const isGI=(String(src||'GI').toUpperCase()!=='CUSTOM');
  const sm=String(mode||'').toLowerCase();
  const bg=isGI?'rgba(34,197,94,0.14)':'rgba(59,130,246,0.14)';
  const bd=isGI?'rgba(34,197,94,0.28)':'rgba(59,130,246,0.28)';
  const fg=isGI?'var(--green)':'var(--blue)';
  const labels={'gi':'GI','native_legacy':'Native','native_relaxed':'Relaxed','mechanics_continuation':'Mech Cont','mechanics_reversal':'Mech Rev','gi_style':'GI-Style','reversal':'Reversal'};
  const label=isGI?'GI':(labels[sm]||sm||'—');
  return `<span style="display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid ${bd};background:${bg};color:${fg};font-size:10px;font-weight:700">${escHtml(label)}</span>`;
}
function rvFamilyBadge(fam){
  const f=String(fam||'').toLowerCase();
  const isRev=(f==='reversal');
  const bg=isRev?'rgba(245,158,11,0.14)':'rgba(167,139,250,0.14)';
  const bd=isRev?'rgba(245,158,11,0.28)':'rgba(167,139,250,0.28)';
  const fg=isRev?'var(--amber)':'#c4b5fd';
  const label=isRev?'Reversal':f.includes('continuation')?'Continuation':'Other';
  return `<span style="display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid ${bd};background:${bg};color:${fg};font-size:10px;font-weight:700">${label}</span>`;
}
function rvFmtThresh(r){
  if(!r) return '<span style="color:var(--muted)">—</span>';
  const mode=String(r.threshold_mode||'fixed_global');
  if(mode==='fixed_global') return r.thresh==null?'<span style="color:var(--muted)">—</span>':`<span style="font-family:var(--mono)">${r.thresh}</span>`;
  const lbl=escHtml(r.threshold_label||'Dynamic');
  const eff=r.effective_threshold;
  const effHtml=(eff!=null&&Number.isFinite(Number(eff)))?`<div style="font-size:10px;color:var(--muted)">Eff ${Number(eff).toFixed(1)}</div>`:'';
  return `<div style="color:var(--amber);line-height:1.3">${lbl}${effHtml}</div>`;
}
function rvFmtTgt(t){
  if(t==null) return '—';
  if(typeof t==='string'&&t.startsWith('atr_')) return `<span style="color:var(--green);font-family:var(--mono)">ATR ${t.slice(4)}:1</span>`;
  const n=Number(t);
  return Number.isFinite(n)?`<span style="color:var(--green);font-family:var(--mono)">+${(n*100).toFixed(0)}%</span>`:'—';
}
function rvFmtPct(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  const c=n>=0?'var(--green)':'var(--red)';
  return `<span style="color:${c};font-family:var(--mono)">${n>=0?'+':''}${n.toFixed(2)}%</span>`;
}
function rvFmtTail(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  const c=n>=-2?'var(--green)':n>=-4?'var(--amber)':'var(--red)';
  return `<span style="color:${c};font-family:var(--mono)">${n.toFixed(2)}%</span>`;
}
function rvFmtR(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  const c=n>=1?'var(--green)':n>=0.5?'var(--amber)':'var(--red)';
  return `<span style="color:${c};font-family:var(--mono)">${n>=0?'+':''}${n.toFixed(2)}R</span>`;
}
function rvFmtSharpe(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  const c=n>=1.5?'var(--green)':n>=0.5?'var(--amber)':'var(--red)';
  return `<span style="color:${c};font-family:var(--mono)">${n.toFixed(3)}</span>`;
}
function rvFmtWR(v){
  if(v==null||!Number.isFinite(Number(v))) return '<span style="color:var(--muted)">—</span>';
  const n=Number(v);
  const c=n>=60?'var(--green)':n>=50?'var(--amber)':'var(--red)';
  return `<span style="color:${c};font-family:var(--mono)">${n.toFixed(1)}%</span>`;
}
function rvNormSource(v){ return String(v||'GI').toUpperCase()==='CUSTOM'?'CUSTOM':'GI'; }
const rvSt=Object.assign(mkState([], 'signal_date', -1),{ps:50});
_regSortSlot('reversals',()=>rvSt);
const _RV_PREFS_KEY='gekko_rv_filters';
function rvSavePrefs(){
  try{
    const p={
      strategy: document.getElementById('rvStrategy')?.value||'',
      source:   document.getElementById('rvSource')?.value||'BOTH',
      family:   document.getElementById('rvFamily')?.value||'',
      mode:     document.getElementById('rvMode')?.value||'',
      tgt:      document.getElementById('rvTgt')?.value||'',
      atrm:     document.getElementById('rvAtrM')?.value||'',
      today:    !!(document.getElementById('rvToday')?.checked),
      sc:       rvSt.sc,
      sd:       rvSt.sd,
    };
    localStorage.setItem(_RV_PREFS_KEY, JSON.stringify(p));
  }catch(_e){}
}
function rvLoadPrefs(){
  try{
    const raw=localStorage.getItem(_RV_PREFS_KEY);
    if(!raw) return;
    const p=JSON.parse(raw);
    const set=(id,val)=>{ const el=document.getElementById(id); if(el&&val!=null) el.value=val; };
    set('rvStrategy', p.strategy);
    set('rvSource',   p.source);
    set('rvFamily',   p.family);
    set('rvMode',     p.mode);
    set('rvTgt',      p.tgt);
    set('rvAtrM',     p.atrm);
    const todayEl=document.getElementById('rvToday');
    if(todayEl) todayEl.checked=!!p.today;
    if(p.sc) rvSt.sc=p.sc;
    if(p.sd) rvSt.sd=p.sd;
  }catch(_e){}
}
function rvInit(){
  rvSt.all=REVERSAL_ROWS;
  rvSt.filtered=[...REVERSAL_ROWS];
  rvSt.sc='signal_date'; rvSt.sd=-1; rvSt.pg=1; rvSt.ps=50;
  rvLoadPrefs();
  document.querySelectorAll('#tab-reversals thead th').forEach(t=>{
    t.classList.remove('sort-asc','sort-desc');
    if(t.dataset.col===rvSt.sc) t.classList.add(rvSt.sd===1?'sort-asc':'sort-desc');
  });
  ensureSignalsData();
}
function rvStrategyFilter(pool, key){
  if(!key) return pool;
  // Score threshold (e.g. score_90)
  const sm=key.match(/score_(\d+)/);
  if(sm){ const ms=parseInt(sm[1]); pool=pool.filter(r=>(r.score||0)>=ms); }
  // Entry filters (boolean fields)
  if(key.indexOf('_conf3')!==-1)   pool=pool.filter(r=>(r.confirm_count||0)>=3);
  else if(key.indexOf('_conf2')!==-1) pool=pool.filter(r=>(r.confirm_count||0)>=2);
  else if(key.indexOf('_momrev')!==-1) pool=pool.filter(r=>r.above_prev_high&&r.gi_reversal);
  else if(key.indexOf('_mom')!==-1)  pool=pool.filter(r=>r.above_prev_high);
  else if(key.indexOf('_rev')!==-1)  pool=pool.filter(r=>r.gi_reversal);
  else if(key.indexOf('_vol')!==-1)  pool=pool.filter(r=>r.vol_confirm);
  else if(key.indexOf('_giacc')!==-1) pool=pool.filter(r=>r.gi_accel);
  else if(key.indexOf('_atrok')!==-1) pool=pool.filter(r=>r.atr_regime_ok);
  else if(key.indexOf('_clstr')!==-1) pool=pool.filter(r=>r.close_strength);
  else if(key.indexOf('_gitrend')!==-1) pool=pool.filter(r=>r.gi_trend_up);
  return pool;
}
function rvComputeRanks(pool){
  const byDay={};
  pool.forEach(r=>{ const k=r.days_ago; if(!byDay[k]) byDay[k]=[]; byDay[k].push(r); });
  Object.values(byDay).forEach(day=>{
    day.sort((a,b)=>(b.sharpe||0)-(a.sharpe||0));
    day.forEach((r,i)=>{ r._rv_rank=i+1; r.pos_rank=i+1; });
  });
}
function rvFilter(){
  const q=(document.getElementById('rvS')?.value||'').trim().toUpperCase();
  const strat=(document.getElementById('rvStrategy')?.value||'');
  const src=(document.getElementById('rvSource')?.value||'BOTH').toUpperCase();
  const family=(document.getElementById('rvFamily')?.value||'').toLowerCase();
  const mode=(document.getElementById('rvMode')?.value||'').toLowerCase();
  const tgt=(document.getElementById('rvTgt')?.value||'');
  const atrM=(document.getElementById('rvAtrM')?.value||'');
  const todayOnly=document.getElementById('rvToday')?.checked;
  // Apply strategy variant filter first, then compute per-day ranks
  let pool=rvStrategyFilter(REVERSAL_ROWS.slice(), strat);
  rvComputeRanks(pool);
  // Apply position limit (Top N/day) from strategy key prefix
  const nMatch=strat?strat.match(/^(\d+)_/):null;
  if(nMatch){ const nLim=parseInt(nMatch[1]); pool=pool.filter(r=>(r._rv_rank||999)<=nLim); }
  rvSt.filtered=pool.filter(r=>{
    if(src!=='BOTH'&&rvNormSource(r.signal_source)!==src) return false;
    if(family){
      const f=String(r.signal_family||'').toLowerCase();
      if(f!==family&&!(family==='continuation'&&f.includes('continuation'))) return false;
    }
    if(mode&&String(r.signal_mode||'').toLowerCase()!==mode) return false;
    if(tgt){ const rt=r.target==null?'':String(r.target); if(rt!==tgt) return false; }
    if(atrM&&String(r.atr_mult||'')!==atrM) return false;
    if(todayOnly&&Number(r.days_ago)!==1) return false;
    if(q&&!String(r.ticker||'').toUpperCase().includes(q)) return false;
    return true;
  });
  doSort(rvSt); rvSt.pg=1; renderRV(); rvSavePrefs();
}
function rvSortBy(col){
  const textCols=new Set(['ticker','signal_date','signal_source','signal_family','signal_mode','target']);
  if(rvSt.sc===col) rvSt.sd*=-1;
  else{rvSt.sc=col;rvSt.sd=textCols.has(col)?1:-1;}
  document.querySelectorAll('#tab-reversals thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add(rvSt.sd===1?'sort-asc':'sort-desc');});
  doSort(rvSt); rvSt.pg=1; renderRV(); rvSavePrefs();
}
function renderRVPage(p){goPage(rvSt,p,renderRV);}
function renderRV(){
  const s=rvSt, start=(s.pg-1)*s.ps, page=s.filtered.slice(start,start+s.ps);
  const num='text-align:right';
  document.getElementById('rvBody').innerHTML=page.map(r=>{
    const daysAgo=Number(r.days_ago);
    const daysLabel=daysAgo===1?'Today':(Number.isFinite(daysAgo)?daysAgo+'d':'—');
    const daysColor=daysAgo===1?'var(--green)':'var(--muted)';
    const posColor=r.pos_rank===1?'var(--green)':r.pos_rank<=3?'var(--amber)':'var(--muted)';
    return `<tr>
      <td style="font-weight:600;color:${posColor};${num};font-family:var(--mono)">${r.pos_rank!=null?r.pos_rank:'—'}</td>
      <td class="sym-cell">${tickerLinkCell(r.ticker,r)}</td>
      <td>${rvSourceBadge(r.signal_source,r.signal_mode)}</td>
      <td>${rvModeBadge(r.signal_source,r.signal_mode)}</td>
      <td>${rvFamilyBadge(r.signal_family)}</td>
      <td style="min-width:90px">${rvFmtScore(r.score)}</td>
      <td style="min-width:80px">${rvFmtRobust(r.robust_total)}</td>
      <td style="color:var(--muted);font-family:var(--mono);font-size:11px">${r.signal_date||'—'}</td>
      <td style="color:${daysColor};font-family:var(--mono);${num}">${daysLabel}</td>
      <td>${rvGiBadge(r.current_gi)}</td>
      <td style="${num}">${rvFmtThresh(r)}</td>
      <td style="${num}">${r.avg_atr_pct!=null&&Number.isFinite(Number(r.avg_atr_pct))?`<span style="color:var(--red);font-family:var(--mono)">-${Number(r.avg_atr_pct).toFixed(1)}%</span>`:'—'}</td>
      <td style="${num};font-family:var(--mono)">${r.atr_mult!=null?r.atr_mult+'x':'—'}</td>
      <td style="${num}">${rvFmtTgt(r.target)}</td>
      <td style="${num};font-family:var(--mono)">${r.hold!=null?r.hold+'d':'—'}</td>
      <td style="${num};font-family:var(--mono);color:var(--muted)">${r.ts_days!=null&&r.ts_days>0?r.ts_days+'d':'—'}</td>
      <td style="${num}">${rvFmtWR(r.win_rate)}</td>
      <td style="${num}">${rvFmtPct(r.avg_ret)}</td>
      <td style="${num}">${rvFmtPct(r.expected_ret_3d)}</td>
      <td style="${num}">${rvFmtPct(r.expected_ret_5d)}</td>
      <td style="${num}">${rvFmtPct(r.expected_ret_10d)}</td>
      <td style="${num}">${rvFmtTail(r.downside_tail_10d)}</td>
      <td style="${num}">${rvFmtR(r.expected_r_multiple)}</td>
      <td style="${num}">${rvFmtSharpe(r.sharpe)}</td>
      <td style="${num};font-family:var(--mono);color:var(--muted)">${r.n!=null?r.n:'—'}</td>
    </tr>`;
  }).join('');
  mkPag(s,'rvPag','renderRV');
  setCountMeta('rvCnt',`${s.filtered.length.toLocaleString()} signals`,0,!!_reversalsFetchPromise);
}

// -- Shared helper --
function fmt_money_js(v){
  if(v==null||v==='')return'-';
  const n=Number(v);
  if(!Number.isFinite(n))return'-';
  if(Math.abs(n)<0.0005)return'$0';
  const sign=n<0?'-':'';
  const a=Math.abs(n);
  if(a>=1e9)return sign+'$'+(a/1e9).toFixed(2)+'B';
  if(a>=1e6)return sign+'$'+(a/1e6).toFixed(2)+'M';
  if(a>=1e3)return sign+'$'+(a/1e3).toFixed(0)+'K';
  return sign+'$'+a.toFixed(0);
}
function fmt_money_short_js(v){
  if(v==null||v==='')return'-';
  const n=Number(v);
  if(!Number.isFinite(n))return'-';
  if(Math.abs(n)<0.0005)return'$0';
  const sign=n<0?'-':'';
  const a=Math.abs(n);
  const compact=(value,suffix)=>{
    const decimals=value>=100?0:value>=10?1:2;
    return sign+'$'+value.toFixed(decimals)+suffix;
  };
  if(a>=1e12)return compact(a/1e12,'T');
  if(a>=1e9)return compact(a/1e9,'B');
  if(a>=1e6)return compact(a/1e6,'M');
  if(a>=1e3)return compact(a/1e3,'K');
  return sign+'$'+(a>=100?a.toFixed(0):a>=10?a.toFixed(1):a.toFixed(2));
}
function fmt_shares_js(v){
  const n=Number(v);
  if(!Number.isFinite(n)) return '-';
  const a=Math.abs(n);
  if(a>=1e9) return (n/1e9).toFixed(2)+'B';
  if(a>=1e6) return (n/1e6).toFixed(2)+'M';
  if(a>=1e3) return (n/1e3).toFixed(1)+'K';
  return n.toLocaleString(undefined,{maximumFractionDigits:0});
}
function insiderRowDate(r){
  return String(r?.trans_date||r?.filing_date||'');
}
function insiderDateLabel(items){
  const dates=[...new Set((items||[]).map(insiderRowDate).filter(Boolean))].sort();
  if(!dates.length) return '';
  if(dates.length===1) return fmtDateShort(dates[0]);
  return `${fmtDateShort(dates[dates.length-1])} .. ${fmtDateShort(dates[0])}`;
}
function insiderDisplayRows(items){
  const grouped={};
  (items||[]).forEach(r=>{
    const date=insiderRowDate(r);
    const key=[
      r?.insider||'',
      r?.title||'',
      date,
      r?.tx_type||'',
      r?.tx_label||'',
      r?.is_buy?'1':'0'
    ].join('|');
    if(!grouped[key]){
      grouped[key]={...r,display_date:date,shares:0,total_value:0,_weightedPrice:0,_weightedShares:0,_fills:0};
    }
    const g=grouped[key];
    const shares=Number(r?.shares);
    const total=Number(r?.total_value);
    const price=Number(r?.price);
    if(Number.isFinite(shares)) g.shares+=shares;
    if(Number.isFinite(total)) g.total_value+=total;
    if(Number.isFinite(price)&&Number.isFinite(shares)&&shares>0){
      g._weightedPrice+=price*shares;
      g._weightedShares+=shares;
    }
    g._fills+=1;
  });
  return Object.values(grouped).map(r=>{
    const shares=Number(r.shares)||0;
    const price=r._weightedShares>0 ? (r._weightedPrice/r._weightedShares) : (Number.isFinite(Number(r.price)) ? Number(r.price) : null);
    return {
      ...r,
      shares,
      shares_fmt:fmt_shares_js(shares),
      price,
      total_value:r.total_value,
      value_fmt:fmt_money_js(r.total_value),
      display_date:r.display_date||insiderRowDate(r)
    };
  }).sort((a,b)=>{
    const ad=String(a.display_date||'');
    const bd=String(b.display_date||'');
    const dcmp=bd.localeCompare(ad);
    if(dcmp) return dcmp;
    return String(a.insider||'').localeCompare(String(b.insider||''), undefined, {numeric:true,sensitivity:'base'});
  });
}

// -- TAB 4: HOLDINGS (grouped by ticker) --
const hSt=Object.assign(mkState(HOLDINGS,'value',-1),{ps:25});
_regSortSlot('holdings',()=>hSt);
let hGroups=[];
function groupHoldings(rows){
  const map={};
  rows.forEach(r=>{(map[r.ticker]=map[r.ticker]||[]).push(r);});
  return Object.entries(map).map(([ticker,items])=>{
    // Keep only the latest entry per manager (data has multiple quarters)
    const mgrMap={};
    items.forEach(r=>{if(!mgrMap[r.manager]||r.report_date>mgrMap[r.manager].report_date)mgrMap[r.manager]=r;});
    const deduped=Object.values(mgrMap);
    const totalVal=deduped.reduce((s,r)=>s+(r.value||0),0);
    const mgrList=deduped.map(r=>String(r.manager||'').trim()).filter(Boolean);
    const mgrs=mgrList.join(', ');
    const mgrTip=mgrList.join('\n');
    const latestDate=deduped.map(r=>r.report_date).filter(Boolean).sort().reverse()[0]||'';
    const types_present=new Set(deduped.map(r=>r.change_type));
    // Compute net share change across all managers
    let netShares=0, netPrevShares=0, hasShareData=false;
    const specialTypes=[];
    deduped.forEach(r=>{
      if(r.change_type==='NEW')  specialTypes.push({ct:'NEW',pct:null});
      else if(r.change_type==='SOLD') specialTypes.push({ct:'SOLD',pct:null});
      else {
        const cur=r.shares||0;
        const scp=r.share_chg_pct;
        const prev=(scp!=null&&scp!==-100)?cur/(1+scp/100):cur;
        netShares+=cur;
        netPrevShares+=prev;
        hasShareData=true;
      }
    });
    // Build chgTypes: unique special badges + one net change badge
    const chgTypes=[];
    const seenSpecial=new Set();
    specialTypes.forEach(s=>{if(!seenSpecial.has(s.ct)){seenSpecial.add(s.ct);chgTypes.push(s);}});
    if(hasShareData&&netPrevShares>0){
      const netPct=((netShares-netPrevShares)/netPrevShares)*100;
      if(Math.abs(netPct)>=0.05){
        chgTypes.push({ct:netPct>0?'INCREASED':'DECREASED',pct:netPct});
      }
    }
    if(!chgTypes.length) chgTypes.push({ct:'UNCHANGED',pct:null});
    const chg=chgTypes[0].ct;
    const chgPct=chgTypes[0].pct;
    const groupRank=Math.min(...items.map(r=>Number(r.rank)||Infinity));
    return{ticker,company:deduped[0].company,totalVal,rank:groupRank,
      value_fmt:fmt_money_js(totalVal),mgrs,mgrTip,latestDate,
      gi_score:deduped[0].gi_score,gi_tier:deduped[0].gi_tier,gi_label:deduped[0].gi_label,
      change_type:chg,change_pct:chgPct,chgTypes,managerCount:deduped.length,_rows:deduped,_open:false};
  });
}
function toggleHGroup(idx){
  hGroups[idx]._open=!hGroups[idx]._open;
  renderH();
}
function hFilter(){
  const mgr=document.getElementById('hMgr').value;
  const q=document.getElementById('hS').value.trim().toLowerCase();
  const ch=document.getElementById('hCh').value;
  const gi=document.getElementById('hGI').value;
  hSt.filtered=HOLDINGS.filter(r=>{
    if(mgr&&r.manager!==mgr) return false;
    if(q&&!r.ticker.toLowerCase().includes(q)&&!r.company.toLowerCase().includes(q)) return false;
    if(ch&&r.change_type!==ch) return false;
    if(gi&&r.gi_tier!==gi) return false;
    return true;
  });
  doSort(hSt); hSt.pg=1; renderH();
}
function hSort(col){
  if(hSt.sc===col) hSt.sd*=-1; else{hSt.sc=col;hSt.sd=col==='rank'?1:-1;}
  document.querySelectorAll('#tab-holdings thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add(hSt.sd===1?'sort-asc':'sort-desc');});
  doSort(hSt); hSt.pg=1; renderH();
}
function hGroupSortValue(g,col){
  if(col==='value') return g.totalVal;
  if(col==='managerCount') return g.managerCount;
  return g[col];
}
function sortHoldingGroups(groups){
  const col=hSt.sc||'rank';
  const dir=hSt.sd||1;
  groups.sort((a,b)=>{
    let av=hGroupSortValue(a,col);
    let bv=hGroupSortValue(b,col);
    const aNum=(typeof av==='number') ? av : Number(av);
    const bNum=(typeof bv==='number') ? bv : Number(bv);
    if(Number.isFinite(aNum) && Number.isFinite(bNum)){
      if(aNum!==bNum) return (aNum-bNum)*dir;
    } else {
      av=String(av??'');
      bv=String(bv??'');
      const cmp=av.localeCompare(bv, undefined, {numeric:true,sensitivity:'base'});
      if(cmp) return cmp*dir;
    }
    return String(a.ticker||'').localeCompare(String(b.ticker||''), undefined, {numeric:true,sensitivity:'base'});
  });
}
function hPSChange(){hSt.ps=parseInt(document.getElementById('hPS').value);hSt.pg=1;renderH();}
function renderHPage(p){goPage(hSt,p,renderH);}
function renderH(){
  const s=hSt;
  // Preserve open state across re-renders
  const wasOpen={};
  hGroups.forEach(g=>{if(g._open)wasOpen[g.ticker]=true;});
  hGroups=groupHoldings(s.filtered);
  hGroups.forEach(g=>{if(wasOpen[g.ticker])g._open=true;});
  sortHoldingGroups(hGroups);
  const start=(s.pg-1)*s.ps,page=hGroups.slice(start,start+s.ps);
  let html='';
  page.forEach((g,idx)=>{
    const gi=start+idx;
    html+=`<tr class="grp-hdr${g._open?' open':''}" onclick="toggleHGroup(${gi})">
      <td class="sym-cell">${tickerLinkCell(g.ticker, g)}</td>
      <td class="muted" style="max-width:160px;overflow:hidden;text-overflow:ellipsis" title="${g.company}">${g.company||'-'}</td>
      <td style="color:var(--green)">${g.value_fmt}</td>
      <td>${hoverCount(g.managerCount,'var(--green)',g.mgrTip||g.mgrs,'mgr')}</td>
      <td style="text-align:center">${giBadge(g.gi_score,g.gi_tier)}</td>
      <td>${holdingsChgBadge(g.chgTypes,[])}</td>
    </tr>`;
    if(g._open){
      g._rows.forEach(r=>{
        html+=`<tr class="grp-child">
          <td class="muted" style="font-size:10px;padding-left:14px" colspan="2">${managerCell(r)}</td>
          <td style="color:var(--green)">${r.value_fmt}</td>
          <td class="muted">${r.pct!=null?r.pct.toFixed(2)+'%<div class="pct-bar"><div class="pct-bar-fill" style="width:'+Math.min(r.pct,100).toFixed(1)+'%"></div></div>':'-'}</td>
          <td style="text-align:center">${giBadge(r.gi_score,r.gi_tier)}</td>
          <td>${holdingsChgBadge([{ct:r.change_type,pct:r.share_chg_pct}],[])}</td>
        </tr>`;
      });
    }
  });
  document.getElementById('hBody').innerHTML=html;
  document.querySelectorAll('.grp-child').forEach(tr=>{tr.style.display='table-row';});
  mkPag({filtered:hGroups,ps:s.ps,pg:s.pg},'hPag','renderH');
  setCountMeta(
    'hCnt',
    `${hGroups.length.toLocaleString()} tickers (${s.filtered.length.toLocaleString()} positions)`,
    0,
    !!_holdingsFetchPromise
  );
}

// -- TAB 5: INSIDER TRADES (grouped by ticker) --
const iSt=Object.assign(mkState(INSIDERS,'filing_date',-1),{ps:25});
_regSortSlot('insiders',()=>iSt);
let iGroups=[];
function groupInsiders(rows){
  const map={};
  rows.forEach(r=>{(map[r.ticker]=map[r.ticker]||[]).push(r);});
  return Object.entries(map).map(([ticker,items])=>{
    items.sort((a,b)=>insiderRowDate(b).localeCompare(insiderRowDate(a))||String(b.filing_date||'').localeCompare(String(a.filing_date||'')));
    const newest=items[0];
    const totalVal=items.reduce((s,r)=>s+(r.total_value||0),0);
    const detailRows=insiderDisplayRows(items);
    return{ticker,company:newest.company,newest_date:insiderRowDate(newest),
      date_label:insiderDateLabel(items),
      trade_count:items.length,insider_count:new Set(items.map(r=>r.insider).filter(Boolean)).size,total_value:totalVal,value_fmt:fmt_money_js(totalVal),
      gi_score:newest.gi_score,gi_tier:newest.gi_tier,gi_label:newest.gi_label,
      _rows:detailRows,_open:false};
  }).sort((a,b)=>b.newest_date.localeCompare(a.newest_date));
}
function toggleIGroup(idx){
  iGroups[idx]._open=!iGroups[idx]._open;
  renderI();
}
function iFilter(){
  // Always keep iWinDays in sync with blLookback (blApplySavedControlState sets blLookback
  // programmatically without firing onchange, so iWinDays can drift out of sync)
  iApplyLookbackFromMovedControl();
  const q=document.getElementById('iS').value.trim().toLowerCase();
  const tit=document.getElementById('iTit').value;
  const winDays=parseInt(document.getElementById('iWinDays').value)||30;
  const cutoff=new Date(Date.now()-winDays*86400000);
  iSt.filtered=INSIDERS.filter(r=>{
    if(q&&!r.ticker.toLowerCase().includes(q)&&!(r.company||'').toLowerCase().includes(q)&&!(r.insider||'').toLowerCase().includes(q)) return false;
    if(tit&&r.title!==tit) return false;
    const rowDate=insiderRowDate(r);
    if(rowDate&&new Date(rowDate)<cutoff) return false;
    return true;
  });
  iSt.pg=1; renderI();
}
function iSort(col){
  if(iSt.sc===col) iSt.sd*=-1; else{iSt.sc=col;iSt.sd=-1;}
  iUpdateHeaderSort(col,iSt.sd);
  iSyncMovedSortControl();
  iSt.pg=1; renderI();
}
function iGroupSortValue(g,col){
  if(col==='filing_date') return g.newest_date||'';
  return g[col];
}
function sortInsiderGroups(groups){
  const col=iSt.sc||'filing_date';
  const dir=iSt.sd||-1;
  groups.sort((a,b)=>{
    let av=iGroupSortValue(a,col);
    let bv=iGroupSortValue(b,col);
    const aNum=(typeof av==='number') ? av : Number(av);
    const bNum=(typeof bv==='number') ? bv : Number(bv);
    if(Number.isFinite(aNum) && Number.isFinite(bNum)){
      if(aNum!==bNum) return (aNum-bNum)*dir;
    } else {
      av=String(av??'');
      bv=String(bv??'');
      const cmp=av.localeCompare(bv, undefined, {numeric:true,sensitivity:'base'});
      if(cmp) return cmp*dir;
    }
    return String(a.ticker||'').localeCompare(String(b.ticker||''), undefined, {numeric:true,sensitivity:'base'});
  });
}
function iPSChange(){iSt.ps=parseInt(document.getElementById('iPS').value);iSt.pg=1;renderI();}
function renderIPage(p){goPage(iSt,p,renderI);}
function renderI(){
  const s=iSt;
  const _convMap={};
  CONV.forEach(c=>{ if(c.ticker) _convMap[c.ticker]=c; });
  const wasOpen={};
  iGroups.forEach(g=>{if(g._open)wasOpen[g.ticker]=true;});
  iGroups=groupInsiders(s.filtered);
  iGroups.forEach(g=>{if(wasOpen[g.ticker])g._open=true;});
  const minIns=parseInt(document.getElementById('iMinIns').value)||1;
  if(minIns>1){
    iGroups=iGroups.filter(g=>{
      const buyers=new Set(g._rows.filter(r=>r.is_buy).map(r=>r.insider));
      return buyers.size>=minIns;
    });
  }
  sortInsiderGroups(iGroups);
  const start=(s.pg-1)*s.ps,page=iGroups.slice(start,start+s.ps);
  let html='';
  page.forEach((g,idx)=>{
    const gi=start+idx;
    html+=`<tr class="grp-hdr${g._open?' open':''}" onclick="toggleIGroup(${gi})">
      <td class="sym-cell">${tickerLinkCell(g.ticker||'-', g)}</td>
      <td class="muted" style="max-width:160px;overflow:hidden;text-overflow:ellipsis" title="${g.company}">${g.company||'-'}</td>
      <td><span class="trade-count badge-trades">${g.trade_count} trade${g.trade_count!==1?'s':''}</span><span class="trade-count badge-insiders">${g.insider_count} insider${g.insider_count!==1?'s':''}</span>${(()=>{const cv=_convMap[g.ticker];const mc=cv&&cv.manager_count>0?cv.manager_count:0;if(!mc) return '';const tip=(cv.manager_detail||'').split('\n').filter(Boolean).join('&#10;');return `<span class="trade-count badge-managers" title="${tip}">${mc} manager${mc!==1?'s':''}</span>`;})()}</td>
      <td style="color:var(--green)">${g.value_fmt}</td>
      <td style="text-align:center">${giBadge(g.gi_score,g.gi_tier)}</td>
      <td class="muted" title="${g.date_label||fmtDateShort(g.newest_date)}">${fmtDateShort(g.newest_date)}</td>
    </tr>`;
    if(g._open){
      g._rows.forEach(r=>{
        html+=`<tr class="grp-child">
          <td class="muted" style="padding-left:14px;font-size:10px;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r.insider}">${r.insider||'-'}</td>
          <td class="muted" style="max-width:140px;overflow:hidden;text-overflow:ellipsis;font-size:10px" title="${r.title}">${r.title||'-'}</td>
          <td class="muted" style="font-size:10px">${r.shares_fmt}${r.price!=null?' @ $'+r.price.toFixed(2):''}</td>
          <td style="color:var(--green)">${r.value_fmt}</td>
          <td style="text-align:center">${giBadge(r.gi_score,r.gi_tier)}</td>
          <td class="muted">${fmtDateShort(r.display_date||insiderRowDate(r))}</td>
        </tr>`;
      });
    }
  });
  document.getElementById('iBody').innerHTML=html;
  document.querySelectorAll('#tab-insider .grp-child').forEach(tr=>{
    tr.style.display='table-row';
    const insiderCell=tr.children[0];
    const titleCell=tr.children[1];
    const sharesCell=tr.children[2];
    if(insiderCell){insiderCell.style.paddingLeft='14px';insiderCell.style.fontSize='10px';}
    if(titleCell)titleCell.style.fontSize='10px';
    if(sharesCell)sharesCell.style.fontSize='10px';
    const insiderName=(insiderCell&&insiderCell.textContent?insiderCell.textContent:'').trim();
    if(/[A-Za-z0-9]/.test(insiderName)){
      const clr=insiderColor(insiderName);
      if(insiderCell){insiderCell.style.color=clr;insiderCell.style.fontWeight='600';}
      if(titleCell&&/[A-Za-z0-9]/.test((titleCell.textContent||'').trim()))titleCell.style.color=clr;
    }
  });
  mkPag({filtered:iGroups,ps:s.ps,pg:s.pg},'iPag','renderI');
  setCountMeta(
    'iCnt',
    `${iGroups.length.toLocaleString()} tickers (${s.filtered.length.toLocaleString()} trades)`,
    0,
    !!_insidersFetchPromise
  );
}
function initInsiderTitleFilter(){
  if(initInsiderTitleFilter.done) return;
  initInsiderTitleFilter.done=true;
  const titles=[...new Set(INSIDERS.map(r=>r.title).filter(Boolean))].sort();
  const sel=document.getElementById('iTit');
  titles.forEach(t=>{const o=document.createElement('option');o.value=o.textContent=t;sel.appendChild(o);});
}
initNumberSteppers();

// -- TAB: THEMES --
const thSt={filtered:[...THEMES_DATA],sc:'r1d',sd:-1,pg:1,ps:100};
_regSortSlot('themes',()=>thSt);
// Restore all table sort states now that every state object exists
_restoreTableSorts();
let _thCat='';
function thSetCat(cat,btn){
  _thCat=cat;
  document.querySelectorAll('#tab-themes .th-cat-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  thFilter();
}
function thFilter(){
  const q=(document.getElementById('thS').value||'').trim().toLowerCase();
  thSt.filtered=THEMES_DATA.filter(r=>{
    const group=String((r&&(r.theme||r.cat))||'');
    if(_thCat&&group!==_thCat) return false;
    if(q&&!r.ticker.toLowerCase().includes(q)&&!r.name.toLowerCase().includes(q)) return false;
    return true;
  });
  thSt.pg=1; renderTh();
}
function thSort(col){
  if(thSt.sc===col) thSt.sd*=-1; else{thSt.sc=col;thSt.sd=-1;}
  syncSortSelect('thSortSel',col);
  document.querySelectorAll('#tab-themes thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add(thSt.sd===1?'sort-asc':'sort-desc');});
  renderTh();
}
function thSortChange(){
  const col=document.getElementById('thSortSel').value;
  thSt.sc=col;thSt.sd=-1;
  document.querySelectorAll('#tab-themes thead th').forEach(t=>{t.classList.remove('sort-asc','sort-desc');if(t.dataset.col===col)t.classList.add('sort-desc');});
  renderTh();
}
// Gradient background for a return cell.
// `scale` = the % value that maps to ~full saturation (varies per column).
function thRetBg(v, scale){
  if(v==null||!Number.isFinite(v)||v===0) return null;
  // Ease curve: small moves stay subtle, large moves saturate quickly.
  const t=Math.pow(Math.min(Math.abs(v)/scale, 1), 0.65);
  // Interpolate from near-black base toward the target colour.
  const base=16;
  let r,g,b;
  if(v>0){
    // Target: rich forest green  rgb(20,100,50)
    r=Math.round(base+t*(20 -base));
    g=Math.round(base+t*(100-base));
    b=Math.round(base+t*(50 -base));
  } else {
    // Target: deep crimson  rgb(130,25,25)
    r=Math.round(base+t*(130-base));
    g=Math.round(base+t*(25 -base));
    b=Math.round(base+t*(25 -base));
  }
  return `rgb(${r},${g},${b})`;
}
// Full <td> for a return column — applies gradient bg, white text.
function thRetCell(v, scale){
  if(v==null||!Number.isFinite(v)){
    return `<td><span class="muted">-</span></td>`;
  }
  const bg=thRetBg(v, scale);
  const sign=v>=0?'+':'';
  const cell=`<span style="color:#f0f0f0;font-family:var(--mono)">${sign}${v.toFixed(2)}%</span>`;
  return bg
    ? `<td style="background:${bg};padding:0 10px">${cell}</td>`
    : `<td>${cell}</td>`;
}
function thPct(v){
  if(v==null||!Number.isFinite(v)) return '<span class="muted">-</span>';
  const c=v>=0?'var(--green)':'var(--red)';
  const s=v>=0?'+':'';
  return `<span style="color:${c};font-family:var(--mono)">${s}${v.toFixed(2)}%</span>`;
}
function renderThPage(p){goPage(thSt,p,renderTh);}
function renderTh(){
  const s=thSt;
  const arr=[...s.filtered];
  arr.sort((a,b)=>{
    let av=a[s.sc],bv=b[s.sc];
    if(av==null)av=s.sd===1?Infinity:-Infinity;
    if(bv==null)bv=s.sd===1?Infinity:-Infinity;
    return typeof av==='string'?av.localeCompare(bv)*s.sd:(av-bv)*s.sd;
  });
  const start=(s.pg-1)*s.ps,page=arr.slice(start,start+s.ps);
  let html='';
  page.forEach((r,i)=>{
    html+=`<tr>
      <td class="sym-cell">${tickerLinkCell(r.ticker, r)}</td>
      <td class="muted">${r.name}</td>
      <td style="text-align:center">${giBadge(r.gi,r.gi_tier)}</td>
      ${thRetCell(r.r1d,  4)}
      ${thRetCell(r.r2d,  4)}
      ${thRetCell(r.r3d,  5)}
      ${thRetCell(r.r4d,  6)}
      ${thRetCell(r.r1w,  7)}
      ${thRetCell(r.r1m,  14)}
      ${thRetCell(r.r3m,  20)}
      ${thRetCell(r.r6m,  28)}
      ${thRetCell(r.rytd, 28)}
      ${thRetCell(r.r1y,  40)}
      ${thRetCell(r.r2y,  55)}
    </tr>`;
  });
  if(!page.length){
    const msg=_themesServerRefreshing ? 'Updating themes... this can take a minute' : 'No themes found';
    html=`<tr><td colspan="14" class="muted" style="text-align:center;padding:16px">${msg}</td></tr>`;
  }
  document.getElementById('thBody').innerHTML=html;
  mkPag({filtered:arr,ps:s.ps,pg:s.pg},'thPag','renderTh');
  setCountMeta('thCnt', `${s.filtered.length.toLocaleString()} themes`, 0, !!_themesFetchPromise || !!_themesServerRefreshing);
}

// -- Buy-levels chart tooltip --
(function(){
  const canvas=document.getElementById('buyLevelChart');
  const tip=document.getElementById('blTooltip');
  let _tipRaf=null, _tipLastX=-1;
  canvas.addEventListener('mousemove',function(e){
    if(Math.abs(e.clientX-_tipLastX)<2) return; // skip sub-pixel moves
    _tipLastX=e.clientX;
    if(_tipRaf) return;
    _tipRaf=requestAnimationFrame(()=>{
      _tipRaf=null;
      if(!_blShowDataTooltip){tip.style.display='none';return;}
      if(!blChart||!_blOhlcv.length){tip.style.display='none';return;}
      const rect=canvas.getBoundingClientRect();
      const ca=blChart.chartArea;
      const sx=blChart.scales.x;
      // FIX: scale CSS-pixel mouse coords into Chart.js logical pixel space
      const _sx=rect.width?(blChart.width/rect.width):1;
      const mx=(e.clientX-rect.left)*_sx;
      if(mx<ca.left||mx>ca.right){tip.style.display='none';return;}
      const idx=Math.round(sx.getValueForPixel(mx));
      const d=_blOhlcv[Math.max(0,Math.min(idx,_blOhlcv.length-1))];
      if(!d){tip.style.display='none';return;}
      const ticker=blCurrentTicker();
      const giRow=gispGIReadingForDate(ticker,d.t);
      const chg=d.o>0?((d.c/d.o-1)*100):0;
      const chgColor=chg>=0?UI.greenBright:UI.redBright;
      let html=`<div style="color:#94a3b8;margin-bottom:1px;font-weight:600">${d.t}</div>`;
      html+=`<div>O $${Number(d.o).toFixed(2)}  H $${Number(d.h).toFixed(2)}  L $${Number(d.l).toFixed(2)}  C $${Number(d.c).toFixed(2)}</div>`;
      html+=`<div>Chg <span style="color:${chgColor}">${chg>=0?'+':''}${chg.toFixed(2)}%</span></div>`;
      if(giRow&&Number.isFinite(giRow.v))html+=`<div>GI <span style="color:${giColorForValue(giRow.v)}">${giRow.v.toFixed(1)}</span></div>`;
      tip.innerHTML=html;
      tip.style.display='block';
      const pad=10;
      let tx=e.clientX+18,ty=e.clientY-10;
      if(tx+tip.offsetWidth>window.innerWidth-pad)tx=e.clientX-tip.offsetWidth-18;
      if(ty+tip.offsetHeight>window.innerHeight-pad)ty=window.innerHeight-tip.offsetHeight-pad;
      if(tx<pad) tx=pad;
      if(ty<pad) ty=pad;
      tip.style.left=tx+'px';tip.style.top=ty+'px';
    });
  });
  canvas.addEventListener('mouseleave',function(){
    if(_tipRaf){cancelAnimationFrame(_tipRaf);_tipRaf=null;}
    if(tip)tip.style.display='none';
  });
  canvas.addEventListener('dblclick',function(){if(blChart){blChart.resetZoom();requestAnimationFrame(syncGIToBuyRange);}});
  document.getElementById('bubbleChart').addEventListener('dblclick',function(){if(bChart)bChart.resetZoom();});
})();

// -- Crosshair: sync vertical line across candle + GI charts --
(function(){
  let _xhairRaf=null;
  function onMove(e){
    if(_xhairRaf) return;
    _xhairRaf=requestAnimationFrame(()=>{
      _xhairRaf=null;
      if(!_blShowCrosshair){
        if(_crosshairRatio!==null||_crosshairXVal!==null||_crosshairY!==null||_crosshairSource){
          _crosshairRatio=null;
          _crosshairXVal=null;
          _crosshairY=null;
          _crosshairSource='';
          if(blChart)blChart.draw();
          if(giHistChart)giHistChart.draw();
        }
        return;
      }
      const srcChart=(e.target.id==='buyLevelChart')?blChart:giHistChart;
      if(!srcChart)return;
      const rect=e.target.getBoundingClientRect();
      const {left,right,top,bottom}=srcChart.chartArea;
      const xScale=srcChart.scales?.x;
      if(!xScale)return;
      // Mouse coords in CSS pixels — same space as Chart.js chartArea/scales.
      const mx=e.clientX-rect.left;
      const my=e.clientY-rect.top;
      _crosshairSource=(e.target.id==='buyLevelChart')?'buy':'gi';
      _crosshairRatio=(mx-left)/(right-left);
      const xVal=xScale.getValueForPixel(mx);
      _crosshairXVal=Number.isFinite(xVal)?xVal:null;
      _crosshairY=(my>=top&&my<=bottom)?my:null;
      if(blChart)blChart.draw();
      if(giHistChart)giHistChart.draw();
    });
  }
  function onLeave(){
    if(_xhairRaf){cancelAnimationFrame(_xhairRaf);_xhairRaf=null;}
    _crosshairRatio=null;
    _crosshairXVal=null;
    _crosshairY=null;
    _crosshairSource='';
    if(blChart)blChart.draw();
    if(giHistChart)giHistChart.draw();
  }
  ['buyLevelChart','giHistChart'].forEach(id=>{
    const el=document.getElementById(id);
    el.addEventListener('mousemove',onMove);
    el.addEventListener('mouseleave',onLeave);
  });
})();

// -- TAB: HEATMAP --
let _hmView='themes',_hmMetric='r1d';
let _hmRefreshPollTimer=null;
async function hmRefreshAll(btn){
  if(btn){btn.disabled=true;btn.textContent='↻ Syncing…';}
  try{
    const r=await fetch('/api/sync',{method:'POST'});
    const j=await r.json().catch(()=>({}));
    if(j.status==='already_running'){
      if(btn){btn.textContent='↻ Running…';}
    }
  }catch(e){
    console.warn('[hmRefreshAll] POST /api/sync failed',e);
    if(btn){btn.disabled=false;btn.textContent='↻ Refresh All';}
    return;
  }
  // Poll /api/status until sync_running goes false, then reload data
  clearInterval(_hmRefreshPollTimer);
  let pollCount=0;
  _hmRefreshPollTimer=setInterval(async()=>{
    pollCount++;
    if(pollCount>120){ clearInterval(_hmRefreshPollTimer); if(btn){btn.disabled=false;btn.textContent='↻ Refresh All';} return; }
    try{
      const s=await fetch('/api/status').then(r=>r.json());
      if(!s.sync_running){
        clearInterval(_hmRefreshPollTimer);
        if(btn){btn.disabled=false;btn.textContent='↻ Refresh All';}
        // Force reload all heatmap data then redraw
        _themesLastLoadedAt=0; _sp500LastLoadedAt=0;
        THEMES_DATA.length=0; SP500_DATA.length=0;
        if(_hmView==='sp500'){
          ensureSp500Data(true).then(()=>renderHeatmap()).catch(()=>{});
        } else {
          ensureThemesData(true).then(()=>{ hmPopulateCats(); renderHeatmap(); }).catch(()=>{});
        }
        // Also force-reload active tab data
        _forceReloadActiveTabAfterSync();
      }
    }catch(_e){}
  },2000);
}
function _forceReloadActiveTabAfterSync(){
  // Reset staleness timestamps so all ensures do a fresh fetch
  _convictionLastLoadedAt=0; _holdingsLastLoadedAt=0; _insidersLastLoadedAt=0;
  _reversalsLastLoadedAt=0; _themesLastLoadedAt=0; _sp500LastLoadedAt=0;
  if(_isTabActive('managers'))  { Promise.all([ensureConvictionData(true,{background:false}),ensureHoldingsData(true,{background:false})]).then(()=>{ _mgrInitManagerDropdown();mgrSt.filtered=[...HOLDINGS];mgrFilter(); }).catch(()=>{}); }
  if(_isTabActive('insider'))   { ensureInsidersData(true,{background:false}).then(()=>{ iFilter(); }).catch(()=>{}); }
  if(_isTabActive('themes'))    { ensureThemesData(true,{background:false}).then(()=>{ thFilter(); }).catch(()=>{}); }
  if(_isTabActive('reversals')) { ensureReversalsData(true,{background:false}).then(()=>{ rvInit(); }).catch(()=>{}); }
  // OHLCV refresh for the active chart ticker
  const activeTicker=getActiveWatchTicker();
  if(activeTicker) fetch(`/api/ohlcv/${activeTicker}?refresh=1`).then(r=>r.json()).then(bars=>{
    if(bars&&bars.length){ _blOhlcv=bars; if(typeof blSilentUpdateChart==='function') blSilentUpdateChart(); }
  }).catch(()=>{});
}
const HM_MAJORS=['SPY','DIA','QQQ','MDY','IWM','USO','GLD','SLV','CPER','IBIT','ETHA','TLT','HYG','VEU'];
const HM_METRIC_LABELS={gi:'GI Score',r1d:'1D %',r1w:'1W %',r1m:'1M %',r3m:'3M %',r6m:'6M %',rytd:'YTD %',r1y:'1Y %'};
const HM_ZONE_TIP_LABELS={buying:'BUY',accumulation:'ACCUM',neutral:'NEUTR',distribution:'DIST',selling:'SELL'};
const HM_SP500_SECTOR_ORDER=['TECHNOLOGY','COMMUNICATION SERVICES','FINANCIAL SERVICES','HEALTHCARE','CONSUMER DEFENSIVE','CONSUMER CYCLICAL','INDUSTRIALS','ENERGY','REAL ESTATE','BASIC MATERIALS','UTILITIES','OTHER'];
let _hmLayoutRaf=0, _hmLayoutRetryTimer=0;
function hmEsc(s){
  return String(s??'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}
function hmMetricLabel(metric){
  return HM_METRIC_LABELS[metric]||String(metric||'').toUpperCase();
}
function hmLegendText(){
  return '';
}
function hmSyncControls(){
  const wrap=document.getElementById('hmCatWrap');
  if(wrap) wrap.style.display=_hmView==='themes'?'flex':'none';
}
function hmSetView(v,btn){
  _hmView=v;
  document.querySelectorAll('#tab-heatmap .th-cat-btn[id^="hmView"]').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  // rebuild category dropdown
  hmPopulateCats();
  let loadingTriggered = false;
  if (_hmView==='sp500' && !SP500_DATA.length) {
    _renderHeatmapLoading('Loading S&P 500 heatmap...');
    loadingTriggered = true;
    ensureSp500Data(false).then(() => {
      if (document.getElementById('tab-heatmap')?.classList.contains('active')) renderHeatmap();
    }).catch(() => {});
  }
  if (_hmView==='themes' && !THEMES_DATA.length) {
    _renderHeatmapLoading('Loading themes heatmap...');
    loadingTriggered = true;
    ensureThemesData(false).then(() => {
      hmPopulateCats();
      if (document.getElementById('tab-heatmap')?.classList.contains('active')) renderHeatmap();
    }).catch(() => {});
  }
  if (loadingTriggered) return;
  renderHeatmap();
}
function hmSetMetric(m,btn){
  _hmMetric=m;
  document.querySelectorAll('#tab-heatmap .th-cat-btn[id^="hmM"]').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  renderHeatmap();
}
function hmPopulateCats(){
  const sel=document.getElementById('hmCat');
  sel.innerHTML='<option value="">All</option>';
  if(_hmView==='themes'){
    const cats=[...new Set(THEMES_DATA.map(r=>String((r&&(r.theme||r.cat))||'')).filter(Boolean))]
      .filter(c=>!c.startsWith('_')).sort();
    cats.forEach(c=>{const o=document.createElement('option');o.value=o.textContent=c;sel.appendChild(o);});
  }
  sel.value='';
  hmSyncControls();
}
function hmPctColor(v){
  if(v==null)return'#1a1a1a';
  const abs=Math.abs(v);
  const intensity=Math.min(1,abs/8);
  if(v>0)return`rgba(${Math.round(22+34*intensity)},${Math.round(163-63*intensity)},${Math.round(74-54*intensity)},${0.55+intensity*0.45})`;
  return`rgba(${Math.round(155+84*intensity)},${Math.round(28)},${Math.round(28)},${0.55+intensity*0.45})`;
}
function hmGiColor(v){
  if(v==null)return'#1a1a1a';
  // Keep top two green zones intentionally far apart for easier visual scan.
  if(v>=70)return'rgba(7,95,64,0.92)';
  if(v>=60)return'rgba(132,204,22,0.88)';
  if(v>=45)return'rgba(234,179,8,0.65)';
  if(v>=33)return'rgba(249,115,22,0.65)';
  return'rgba(185,28,28,0.70)';
}
function hmFmt(v,metric){
  if(v==null)return'-';
  if(metric==='gi')return v.toFixed(1);
  return(v>=0?'+':'')+v.toFixed(2)+'%';
}
function hmTooltipPayload(row,metric){
  const tipMetric=metric==='gi'?'r1d':metric;
  const giNum=Number(row&&row.gi);
  const zoneKey=Number.isFinite(giNum)?scoreToZone(giNum):'';
  const metricValue=row?(tipMetric==='gi'?row.gi:row[tipMetric]):null;
  return escAttr(JSON.stringify({
    ticker:String((row&&row.ticker)||''),
    name:String((row&&row.name)||''),
    gi:Number.isFinite(giNum)?giNum:null,
    zoneKey:zoneKey||'',
    zoneLabel:zoneKey?(GISP_ZL[zoneKey]||zoneKey):'',
    marketCap:(row&&Number.isFinite(Number(row.market_cap))&&Number(row.market_cap)>0)?Number(row.market_cap):null,
    metric:tipMetric,
    metricLabel:hmMetricLabel(tipMetric),
    metricValue:Number.isFinite(Number(metricValue))?Number(metricValue):null
  }));
}
function hmScheduleLayout(){
  if(_hmView==='sp500') return;
  if(_hmLayoutRaf) cancelAnimationFrame(_hmLayoutRaf);
  if(_hmLayoutRetryTimer) clearTimeout(_hmLayoutRetryTimer);
  _hmLayoutRaf=requestAnimationFrame(()=>{
    _hmLayoutRaf=0;
    const ok=hmApplyLayout();
    // If dimensions weren't ready yet (first paint), retry after 60ms and 200ms
    if(!ok){
      _hmLayoutRetryTimer=setTimeout(()=>{
        _hmLayoutRetryTimer=0;
        if(!hmApplyLayout()){
          setTimeout(()=>{
            if(!hmApplyLayout()){
              // Last resort — reveal grid anyway so it's not stuck invisible
              const g=document.getElementById('hmGrid');
              if(g) g.style.opacity='';
            }
          }, 200);
        }
      }, 60);
    }
  });
}
function hmApplyLayout(){
  const tab=document.getElementById('tab-heatmap');
  const grid=document.getElementById('hmGrid');
  if(!tab||!grid||!grid.children.length||!tab.classList.contains('active')||_hmView==='sp500') return false;
  const legend=document.getElementById('hmLegend');
  const controls=tab.querySelector('.hm-controls');
  const count=grid.children.length;
  // getBoundingClientRect returns real pixel size even immediately after display change
  const gridRect=grid.getBoundingClientRect();
  const tabRect=tab.getBoundingClientRect();
  const width=Math.max(0, gridRect.width||grid.clientWidth||tab.clientWidth||0);
  let height=Math.max(0, gridRect.height||grid.clientHeight||0);
  if(!height){
    const usedH=(controls?controls.getBoundingClientRect().height:0)+(legend&&legend.style.display!=='none'?legend.getBoundingClientRect().height:0)+8;
    height=Math.max(0, tabRect.height-usedH);
  }
  // If still no real dimensions, signal caller to retry
  if(width<60||height<60) return false;
  height=Math.max(180,height);
  const gap=count>180?2:(count>84?3:4);
  const pad=count>180?2:4;
  let best={ cols:1, size:24 };
  for(let cols=1; cols<=count; cols++) {
    const rows=Math.ceil(count/cols);
    const sizeW=(width - (pad*2) - (gap*(cols-1)))/cols;
    const sizeH=(height - (pad*2) - (gap*(rows-1)))/rows;
    const size=Math.floor(Math.min(sizeW,sizeH));
    if(size>best.size) best={ cols, size };
  }
  const maxCell=_hmView==='majors'?118:96;
  const cell=Math.max(24, Math.min(maxCell, best.size));
  grid.style.setProperty('--hm-cols', String(Math.max(1,best.cols)));
  grid.style.setProperty('--hm-cell', `${cell}px`);
  grid.style.setProperty('--hm-gap', `${gap}px`);
  grid.style.setProperty('--hm-pad', `${pad}px`);
  grid.classList.toggle('hm-tight', cell < 44);
  grid.style.opacity='';  // reveal after layout is correctly applied
  return true;
}
function hmViewRows(){
  const catFilter=document.getElementById('hmCat').value;
  if(_hmView==='themes') return THEMES_DATA.filter(r=>{
    const group=String((r&&(r.theme||r.cat))||'');
    if(group.startsWith('_')) return false; // hidden categories (e.g. _majors_only)
    return !catFilter||group===catFilter;
  });
  if(_hmView==='sp500') return SP500_DATA.slice();
  // Majors view — build lookup from all THEMES_DATA (including _majors_only hidden entries)
  const byTicker={};
  THEMES_DATA.forEach(r=>{byTicker[r.ticker]=r;});
  return HM_MAJORS.map(t=>byTicker[t]||{ticker:t,name:t,cat:'Majors',gi:null,gi_tier:'none',r1d:null,r1w:null,r1m:null,r3m:null,r6m:null,rytd:null,r1y:null});
}
function hmWorst(row, shortSide, scale){
  if(!row.length||shortSide<=0||scale<=0) return Number.POSITIVE_INFINITY;
  const areas=row.map(it=>it.weight*scale);
  const sum=areas.reduce((a,b)=>a+b,0);
  const max=Math.max(...areas);
  const min=Math.max(1e-9, Math.min(...areas));
  const s2=sum*sum;
  const side2=shortSide*shortSide;
  return Math.max((side2*max)/s2, s2/(side2*min));
}
function hmLayoutRow(row, rects, x, y, w, h, scale){
  const rowArea=row.reduce((sum,it)=>sum+it.weight,0)*scale;
  if(w>=h){
    const rowW=rowArea/Math.max(h,1);
    let cy=y;
    row.forEach(it=>{
      const area=it.weight*scale;
      const itemH=area/Math.max(rowW,1);
      rects.push({item:it,x,y:cy,w:rowW,h:itemH});
      cy+=itemH;
    });
    return {x:x+rowW,y,w:w-rowW,h};
  }
  const rowH=rowArea/Math.max(w,1);
  let cx=x;
  row.forEach(it=>{
    const area=it.weight*scale;
    const itemW=area/Math.max(rowH,1);
    rects.push({item:it,x:cx,y,w:itemW,h:rowH});
    cx+=itemW;
  });
  return {x,y:y+rowH,w,h:h-rowH};
}
function hmSquarify(items, x, y, w, h){
  const data=(items||[])
    .filter(it=>Number(it.weight)>0)
    .sort((a,b)=>(Number(b.weight)||0)-(Number(a.weight)||0));
  if(!data.length||w<=0||h<=0) return [];
  const total=data.reduce((sum,it)=>sum+Number(it.weight),0);
  if(total<=0) return [];
  const scale=(w*h)/total;
  const pending=data.slice();
  const rects=[];
  let row=[];
  let box={x,y,w,h};
  while(pending.length){
    const next=pending[0];
    const side=Math.min(box.w, box.h);
    if(!row.length || hmWorst(row.concat([next]), side, scale) <= hmWorst(row, side, scale)){
      row.push(next);
      pending.shift();
    } else {
      box=hmLayoutRow(row, rects, box.x, box.y, box.w, box.h, scale);
      row=[];
    }
  }
  if(row.length) hmLayoutRow(row, rects, box.x, box.y, box.w, box.h, scale);
  return rects;
}
function hmRenderSP500(rows, grid){
  const width=Math.max(320, (grid.clientWidth||0)-8);
  const height=Math.max(220, (grid.clientHeight||0)-8);
  if(width<80||height<80){
    requestAnimationFrame(()=>renderHeatmap());
    return;
  }
  const groups=new Map();
  rows.forEach(r=>{
    const sector=String(r.sector||'OTHER').trim().toUpperCase()||'OTHER';
    if(!groups.has(sector)) groups.set(sector, []);
    groups.get(sector).push(r);
  });
  const sectors=Array.from(groups.entries()).map(([sector, items])=>({
    sector,
    items:items
      .filter(r=>Number(r.market_cap)>0)
      .sort((a,b)=>(Number(b.market_cap)||0)-(Number(a.market_cap)||0)),
    weight:items.reduce((sum,r)=>sum+(Number(r.market_cap)||0),0),
  })).filter(s=>s.weight>0&&s.items.length);
  sectors.sort((a,b)=>{
    const weightDiff=(Number(b.weight)||0)-(Number(a.weight)||0);
    if(weightDiff) return weightDiff;
    const ai=HM_SP500_SECTOR_ORDER.indexOf(a.sector);
    const bi=HM_SP500_SECTOR_ORDER.indexOf(b.sector);
    if(ai!==bi) return (ai<0?999:ai)-(bi<0?999:bi);
    return String(a.sector||'').localeCompare(String(b.sector||''));
  });
  const sectorRects=hmSquarify(sectors.map(s=>({weight:s.weight,data:s})),0,0,width,height);
  if(!sectorRects.length){
    grid.innerHTML='<div class="hm-sp-empty">No S&amp;P 500 heatmap data</div>';
    return;
  }
  const metricLabel=hmMetricLabel(_hmMetric);
  grid.innerHTML=sectorRects.map(rect=>{
    const sector=rect.item.data;
    const bodyW=Math.max(0, rect.w-4);
    const bodyH=Math.max(0, rect.h-20);
    const companyRects=hmSquarify(
      sector.items.map(item=>({weight:Number(item.market_cap)||0,data:item})),
      0,0,bodyW,bodyH
    );
    const cellHtml=companyRects.map(cell=>{
      const item=cell.item.data;
      const val=item[_hmMetric==='gi'?'gi':_hmMetric];
      const area=cell.w*cell.h;
      const minSide=Math.min(cell.w, cell.h);
      const fmtVal=hmFmt(val,_hmMetric);
      const bg=_hmMetric==='gi'?hmGiColor(val):hmPctColor(val);
      let label='';
      if(area>185 && minSide>16){
        const tickerSize=Math.max(9, Math.min(19, Math.min(cell.w*0.17, cell.h*0.34)));
        const valueSize=Math.max(8, Math.min(15, tickerSize-1));
        const showValue=area>520 && minSide>26;
        label=`<div class="hm-sp-label"><div class="hm-sp-ticker" style="font-size:${tickerSize.toFixed(1)}px">${hmEsc(item.ticker)}</div>${showValue?`<div class="hm-sp-ret" style="font-size:${valueSize.toFixed(1)}px">${hmEsc(fmtVal)}</div>`:''}</div>`;
      }
      return `<div class="hm-sp-cell" data-ticker="${hmEsc(item.ticker)}" onclick="goChart(this.dataset.ticker)" style="left:${cell.x.toFixed(1)}px;top:${cell.y.toFixed(1)}px;width:${Math.max(0,cell.w).toFixed(1)}px;height:${Math.max(0,cell.h).toFixed(1)}px;background:${bg}">${label}</div>`;
    }).join('');
    return `<div class="hm-sp-sector" style="left:${rect.x.toFixed(1)}px;top:${rect.y.toFixed(1)}px;width:${Math.max(0,rect.w).toFixed(1)}px;height:${Math.max(0,rect.h).toFixed(1)}px">
      <div class="hm-sp-sector-title">${hmEsc(sector.sector)}</div>
      <div class="hm-sp-sector-body">${cellHtml}</div>
    </div>`;
  }).join('');
}
function renderHeatmap(){
  const grid=document.getElementById('hmGrid');
  const legend=document.getElementById('hmLegend');
  let rows=hmViewRows();
  const legendText=hmLegendText();
  if(legend){
    legend.textContent=legendText;
    legend.style.display=legendText ? '' : 'none';
  }
  grid.classList.toggle('hm-sp500', _hmView==='sp500');
  if(!rows.length){
    grid.innerHTML=`<div class="hm-sp-empty">${_hmView==='sp500'?'No S&P 500 data loaded':'No heatmap data loaded'}</div>`;
    grid.classList.remove('hm-tight');
    return;
  }
  if(_hmView==='sp500'){
    hmRenderSP500(rows, grid);
    return;
  }
  if(_hmMetric==='gi') rows=[...rows].sort((a,b)=>(b.gi||0)-(a.gi||0));
  else rows=[...rows].sort((a,b)=>(b[_hmMetric]||0)-(a[_hmMetric]||0));
  const metricLabel=hmMetricLabel(_hmMetric);
  // Hide grid while layout calculates to prevent flash of wrong-sized cells
  grid.style.opacity='0';
  grid.innerHTML=rows.map(r=>{
    const val=r[_hmMetric==='gi'?'gi':_hmMetric];
    const bg=_hmMetric==='gi'?hmGiColor(val):hmPctColor(val);
    const fmtVal=hmFmt(val,_hmMetric);
    return`<div class="hm-cell" data-ticker="${hmEsc(r.ticker)}" onclick="goChart(this.dataset.ticker)" style="background:${bg}">
      <div class="hm-ticker">${r.ticker}</div>
      <div class="hm-name">${r.name||''}</div>
      <div class="hm-val">${fmtVal}</div>
    </div>`;
  }).join('');
  hmScheduleLayout();
}
window.addEventListener('resize', ()=>{
  if(_hmView==='sp500') renderHeatmap();
  else hmScheduleLayout();
});
// ResizeObserver on the grid — fires when the container gets real dimensions
// (catches the initial-paint case where clientWidth was 0 during first render)
(()=>{
  if(typeof ResizeObserver==='undefined') return;
  const obs=new ResizeObserver(()=>{
    if(_hmView!=='sp500' && document.getElementById('hmGrid')?.children.length){
      hmScheduleLayout();
    }
  });
  const grid=document.getElementById('hmGrid');
  if(grid) obs.observe(grid);
})();
// -- LIVE DATA POLLING (Schwab) ---------------------------------------------
let _blLiveEnabled=false;
let _blLiveMarketOpen=false;
let _blLiveRegularSession=false;
let _blSchwabNeedsAuth=false;
let _blSchwabAuthInProgress=false;
let _blLivePollTimer=null;
const _blLiveQuoteCache={};
let _blLiveImmediatePollTimer=null;
const BL_LIVE_POLL_INTERVAL_MS=60*1000;
let _blLiveLastPollAt=0;
let _blLivePollInFlight=false;

function blStopLivePollTimer(){
  if(_blLivePollTimer){
    clearInterval(_blLivePollTimer);
    _blLivePollTimer=null;
  }
}
function blEnsureLivePollTimer(){
  // Stop if market closed/live disabled OR if the auto-refresh timer is Off
  if(!(_blLiveEnabled&&_blLiveMarketOpen) || _blAutoRefreshSecs===0){
    blStopLivePollTimer();
    if(_blLiveImmediatePollTimer){
      clearTimeout(_blLiveImmediatePollTimer);
      _blLiveImmediatePollTimer=null;
    }
    return;
  }
  // Use the user's timer interval when set, otherwise fall back to 60s
  const intervalMs = _blAutoRefreshSecs>0
    ? Math.min(_blAutoRefreshSecs*1000, BL_LIVE_POLL_INTERVAL_MS)
    : BL_LIVE_POLL_INTERVAL_MS;
  // Restart if interval changed
  if(_blLivePollTimer) clearInterval(_blLivePollTimer);
  _blLivePollTimer=setInterval(()=>{blLivePollOnce(true);}, intervalMs);
}
function blQueueImmediateLivePoll(){
  if(!(_blLiveEnabled&&_blLiveMarketOpen)) return;
  if(_blAutoRefreshSecs===0) return;  // timer is Off — don't poll
  const now=Date.now();
  const wait=Math.max(0, BL_LIVE_POLL_INTERVAL_MS-(now-_blLiveLastPollAt));
  if(_blLiveImmediatePollTimer) clearTimeout(_blLiveImmediatePollTimer);
  _blLiveImmediatePollTimer=setTimeout(()=>{
    _blLiveImmediatePollTimer=null;
    blLivePollOnce(true);
  }, wait);
}
// One-shot poll regardless of timer setting — used when user explicitly opens a ticker
// or on initial startup load. Never starts a repeating loop.
// Pass a specific ticker to fetch only that symbol; omit to fetch the whole watchlist.
function blFetchLiveQuoteOnce(sym){
  if(!(_blLiveEnabled&&_blLiveMarketOpen)) return;
  if(sym){
    const key=String(sym).trim().toUpperCase();
    if(!key) return;
    fetch('/api/live/quotes?tickers='+encodeURIComponent(key))
      .then(r=>r.ok?r.json():null)
      .then(quotes=>{ if(quotes){ Object.assign(_blLiveQuoteCache,quotes); blApplyLiveQuotes(quotes); } })
      .catch(()=>{});
  } else {
    blLivePollOnce(true).catch(()=>{});
  }
}
const _blExtendedPrice={}; // ticker ? after-hours/pre-market mark price

function blLiveEtPhase(){
  try{
    const parts=new Intl.DateTimeFormat('en-US',{
      timeZone:'America/New_York',
      weekday:'short',
      hour:'2-digit',
      minute:'2-digit',
      hour12:false
    }).formatToParts(new Date());
    let wd='',hour=0,minute=0;
    parts.forEach(p=>{
      if(p.type==='weekday') wd=String(p.value||'').slice(0,3).toLowerCase();
      else if(p.type==='hour') hour=parseInt(p.value,10)||0;
      else if(p.type==='minute') minute=parseInt(p.value,10)||0;
    });
    if(wd==='sat'||wd==='sun') return 'closed';
    const mins=hour*60+minute;
    if(mins>=570&&mins<960) return 'regular';    // 09:30-16:00 ET
    if(mins>=240&&mins<570) return 'premarket';  // 04:00-09:30 ET
    if(mins>=960&&mins<1200) return 'postmarket';// 16:00-20:00 ET
    return 'closed';
  }catch(_e){
    if(_blLiveRegularSession) return 'regular';
    if(_blLiveMarketOpen) return 'postmarket';
    return 'closed';
  }
}
function blCanUseFallbackDailyBar(){
  return blLiveEtPhase()==='postmarket';
}
function blTradingDayGap(startDate, endDate){
  const s=String(startDate||'').slice(0,10);
  const e=String(endDate||'').slice(0,10);
  if(!s||!e) return null;
  const sd=new Date(`${s}T12:00:00`);
  const ed=new Date(`${e}T12:00:00`);
  if(!Number.isFinite(sd.getTime())||!Number.isFinite(ed.getTime())) return null;
  if(sd>=ed) return 0;
  let gap=0;
  const cur=new Date(sd.getTime());
  while(cur<ed){
    cur.setDate(cur.getDate()+1);
    const day=cur.getDay();
    if(day!==0&&day!==6) gap++;
    if(gap>10) break;
  }
  return gap;
}
function blCanBackfillTodayFromLive(lastDate, today){
  return blTradingDayGap(lastDate, today)===1;
}
let _blCountdownTimer=null;
function _blFormatCountdown(secsUntil){
  if(secsUntil<=0) return '';
  const h=Math.floor(secsUntil/3600);
  const m=Math.floor((secsUntil%3600)/60);
  const s=secsUntil%60;
  if(h>0) return `${h}h ${String(m).padStart(2,'0')}m`;
  if(m>0) return `${m}m ${String(s).padStart(2,'0')}s`;
  return `${s}s`;
}
function _blSecsUntilNext(targetHour, targetMin){
  // Seconds until the next occurrence of targetHour:targetMin ET, skipping weekends
  try{
    const now=new Date();
    const fmt=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',
      weekday:'short',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
    const parts={};
    fmt.formatToParts(now).forEach(p=>parts[p.type]=p.value);
    const nowSecs=parseInt(parts.hour)*3600+parseInt(parts.minute)*60+parseInt(parts.second);
    const targetSecs=targetHour*3600+targetMin*60;
    let diff=targetSecs-nowSecs;
    if(diff<=0) diff+=86400; // push to tomorrow if already past
    // Check what day of week the candidate time falls on
    for(let i=0;i<7;i++){
      const candidateMs=now.getTime()+diff*1000;
      const wd=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short'})
        .format(new Date(candidateMs)).slice(0,3).toLowerCase();
      if(wd!=='sat'&&wd!=='sun') break;
      diff+=86400; // skip one more day
    }
    return diff;
  }catch(_e){ return 0; }
}
function _blStartCountdown(targetHour, targetMin, label, color){
  if(_blCountdownTimer) clearInterval(_blCountdownTimer);
  const cd=document.getElementById('blLiveCountdown');
  const lbl=document.getElementById('blLiveBadgeLabel');
  const dot=document.getElementById('blLiveDot');
  const badge=document.getElementById('blLiveBadge');
  const tick=()=>{
    const secs=_blSecsUntilNext(targetHour, targetMin);
    if(secs<=1){ clearInterval(_blCountdownTimer); _blCountdownTimer=null; blLiveUpdateBadge(); return; }
    if(cd){ cd.style.display='inline'; cd.textContent=_blFormatCountdown(secs); }
    if(lbl) lbl.textContent=label;
    if(dot){ dot.style.background=color; }
    if(badge){ badge.style.color=color; }
  };
  tick();
  _blCountdownTimer=setInterval(tick,1000);
}
function blLiveUpdateBadge(){
  const badge=document.getElementById('blLiveBadge');
  if(!badge) return;
  const lbl=document.getElementById('blLiveBadgeLabel');
  const dot=document.getElementById('blLiveDot');
  const cd=document.getElementById('blLiveCountdown');
  if(_blSchwabNeedsAuth||_blSchwabAuthInProgress){
    if(_blCountdownTimer){ clearInterval(_blCountdownTimer); _blCountdownTimer=null; }
    if(cd) cd.style.display='none';
    badge.style.display='inline-flex';
    badge.style.color='#f59e0b';
    badge.style.opacity='1';
    badge.style.cursor=_blSchwabAuthInProgress?'default':'pointer';
    badge.title=_blSchwabAuthInProgress?'Schwab sign-in in progress...':'Click to sign in to Schwab';
    if(dot) dot.style.background='#f59e0b';
    if(lbl) lbl.textContent=_blSchwabAuthInProgress?'Signing in...':'Sign in';
    badge.onclick=_blSchwabAuthInProgress?null:blSchwabSignIn;
    return;
  }
  badge.onclick=null;
  badge.style.cursor='default';
  badge.title='';
  badge.style.display='inline-flex';
  badge.style.opacity='0.95';
  const phase=blLiveEtPhase();
  if(phase==='regular'){
    // Market Open — green, countdown to 4:00 PM close
    if(_blCountdownTimer){ clearInterval(_blCountdownTimer); _blCountdownTimer=null; }
    _blStartCountdown(16,0,'Market Open','#22c55e');
  } else if(phase==='premarket'){
    // Pre-Market — blue, countdown to 9:30 AM open
    if(_blCountdownTimer){ clearInterval(_blCountdownTimer); _blCountdownTimer=null; }
    _blStartCountdown(9,30,'Pre-Market','#60a5fa');
  } else if(phase==='postmarket'){
    // After Hours — amber, countdown to 8:00 PM session end
    if(_blCountdownTimer){ clearInterval(_blCountdownTimer); _blCountdownTimer=null; }
    _blStartCountdown(20,0,'After Hours','#f59e0b');
  } else {
    // Closed / overnight — no countdown, just static label
    if(_blCountdownTimer){ clearInterval(_blCountdownTimer); _blCountdownTimer=null; }
    if(cd){ cd.style.display='none'; cd.textContent=''; }
    if(lbl) lbl.textContent='Market Closed';
    if(dot) dot.style.background='#6b7280';
    badge.style.color='#6b7280';
  }
}

async function blSchwabSignIn(){
  _blSchwabAuthInProgress=true;
  blLiveUpdateBadge();
  try{
    const r=await fetch('/api/live/auth',{method:'POST'});
    if(!r.ok) throw new Error('failed');
    // Poll status every 3 s until auth completes (or 3 min timeout)
    let attempts=0;
    const poll=setInterval(async()=>{
      attempts++;
      try{
        const sr=await fetch('/api/live/status');
        if(!sr.ok) return;
        const ss=await sr.json();
        const wasEnabled=_blLiveEnabled;
        const wasRegular=_blLiveRegularSession;
        _blLiveEnabled=!!ss.enabled;
        _blLiveMarketOpen=!!ss.market_open;
        _blLiveRegularSession=!!ss.regular_session;
        _blSchwabNeedsAuth=!!ss.needs_auth;
        _blSchwabAuthInProgress=!!ss.auth_in_progress;
        blLiveUpdateBadge();
        blEnsureLivePollTimer();
        if(_blLiveEnabled&&_blLiveRegularSession&&(!wasEnabled||!wasRegular)) blQueueImmediateLivePoll();
        if(!_blSchwabAuthInProgress){
          clearInterval(poll);
          if(_blLiveEnabled&&_blLiveRegularSession) blQueueImmediateLivePoll();
        }
      }catch(_e){}
      if(attempts>60) clearInterval(poll);
    },3000);
  }catch(_e){
    _blSchwabAuthInProgress=false;
    _blSchwabNeedsAuth=true;
    blLiveUpdateBadge();
  }
}

function _blLiveSanityCheck(val, ref){
  // Reject a live value if it's more than 60% away from the reference price
  const v=Number(val), r=Number(ref);
  if(!Number.isFinite(v)||v<=0) return false;
  if(!Number.isFinite(r)||r<=0) return true;
  return v>=r*0.40 && v<=r*2.50;
}
function _blLivePatchCandleData(sym, q){
  const _ld=new Date();const today=`${_ld.getFullYear()}-${String(_ld.getMonth()+1).padStart(2,'0')}-${String(_ld.getDate()).padStart(2,'0')}`;
  if(!CANDLE_DATA[sym]||!CANDLE_DATA[sym].length) return;
  const bars=CANDLE_DATA[sym];
  const last=bars[bars.length-1];
  const lastDate=String(last.t||'').slice(0,10);
  const ref=Number(last.c)||Number(q.price)||1;
  // Determine if we are in the regular NYSE session (from server flag on each quote)
  const inRegularSession=q.regular_session===true;
  if(!inRegularSession){
    // Extended hours (pre-market or after-hours): freeze the candle, store mark as extended price
    if(q.price!=null&&_blLiveSanityCheck(q.price,ref)){
      _blExtendedPrice[sym]=Number(q.price);
    }
    // Fallback only in post-market when EOD file is still on yesterday.
    if(lastDate!==today&&q.price!=null&&blCanUseFallbackDailyBar()&&blCanBackfillTodayFromLive(lastDate,today)){
      const cRaw=Number(q.price);
      const oRaw=Number(q.open),hRaw=Number(q.high),lRaw=Number(q.low),vRaw=Number(q.volume);
      const hasDayStats=Number.isFinite(oRaw)&&Number.isFinite(hRaw)&&Number.isFinite(lRaw);
      const prevClose=Number(last.c),prevVol=Number(last.v);
      const looksLikeFreshSession=hasDayStats&&(cRaw!==prevClose||(Number.isFinite(vRaw)&&vRaw!==prevVol));
      if(Number.isFinite(cRaw)&&looksLikeFreshSession&&_blLiveSanityCheck(cRaw,ref)){
        const o=_blLiveSanityCheck(oRaw,ref)?oRaw:cRaw;
        const h=_blLiveSanityCheck(hRaw,ref)?hRaw:Math.max(o,cRaw);
        const l=_blLiveSanityCheck(lRaw,ref)?lRaw:Math.min(o,cRaw);
        bars.push({t:today,o,h:Math.max(o,h,cRaw),l:Math.min(o,l,cRaw),c:cRaw,v:Number.isFinite(vRaw)?vRaw:Number(last.v||0)});
        return;
      }
    }
    // If today's bar already exists (from file or prior fallback), keep it unchanged after-hours.
    return;
  }
  // Regular session: patch candle normally and clear any stale extended price
  delete _blExtendedPrice[sym];
  if(lastDate!==today&&q.price!=null&&blCanBackfillTodayFromLive(lastDate,today)){
    // q.open may be null outside market hours - fall back to current price
    const o=Number(q.open||q.price),h=Number(q.high||q.price),l=Number(q.low||q.price),c=Number(q.price);
    if(_blLiveSanityCheck(c,ref)&&_blLiveSanityCheck(l,ref))
      bars.push({t:today,o,h:Math.max(o,h,c),l:Math.min(o,l,c),c,v:Number(q.volume||0)});
  }else{
    if(q.price !=null&&_blLiveSanityCheck(q.price,ref)) last.c=Number(q.price);
    if(q.open  !=null&&_blLiveSanityCheck(q.open,ref))  last.o=Number(q.open);
    if(q.high  !=null&&_blLiveSanityCheck(q.high,ref)&&Number(q.high)>Number(last.h)) last.h=Number(q.high);
    if(q.low   !=null&&_blLiveSanityCheck(q.low,ref) &&Number(q.low) <Number(last.l)) last.l=Number(q.low);
    if(q.volume!=null) last.v=Number(q.volume);
  }
}

function blApplyLiveQuotes(quotes){
  const _ld=new Date();const today=`${_ld.getFullYear()}-${String(_ld.getMonth()+1).padStart(2,'0')}-${String(_ld.getDate()).padStart(2,'0')}`;
  let wlChanged=false;
  Object.entries(quotes).forEach(([sym,q])=>{
    if(!q||q.price==null) return;
    _blLivePatchCandleData(sym,q);
    wlChanged=true;  // render watchlist for any session (pre/regular/post market)
  });
  if(wlChanged) renderWatchlist();
  const ticker=blCurrentTicker();
  const q=quotes[ticker];
  if(q&&Array.isArray(_blOhlcv)&&_blOhlcv.length){
    const last=_blOhlcv[_blOhlcv.length-1];
    const lastDate=String(last.t||'').slice(0,10);
    const ref=Number(last.c)||Number(q.price)||1;
    const inRegular=q.regular_session===true;
    if(!inRegular){
      // Extended hours: freeze candle, update extended price line and redraw plugin
      if(q.price!=null&&_blLiveSanityCheck(q.price,ref)) _blExtendedPrice[ticker]=Number(q.price);
      if(lastDate!==today&&q.price!=null&&blCanUseFallbackDailyBar()&&blCanBackfillTodayFromLive(lastDate,today)){
        const cRaw=Number(q.price);
        const oRaw=Number(q.open),hRaw=Number(q.high),lRaw=Number(q.low),vRaw=Number(q.volume);
        const hasDayStats=Number.isFinite(oRaw)&&Number.isFinite(hRaw)&&Number.isFinite(lRaw);
        const prevClose=Number(last.c),prevVol=Number(last.v);
        const looksLikeFreshSession=hasDayStats&&(cRaw!==prevClose||(Number.isFinite(vRaw)&&vRaw!==prevVol));
        if(Number.isFinite(cRaw)&&looksLikeFreshSession&&_blLiveSanityCheck(cRaw,ref)){
          const o=_blLiveSanityCheck(oRaw,ref)?oRaw:cRaw;
          const h=_blLiveSanityCheck(hRaw,ref)?hRaw:Math.max(o,cRaw);
          const l=_blLiveSanityCheck(lRaw,ref)?lRaw:Math.min(o,cRaw);
          const newBar={t:today,o,h:Math.max(o,h,cRaw),l:Math.min(o,l,cRaw),c:cRaw,v:Number.isFinite(vRaw)?vRaw:Number(last.v||0)};
          _blOhlcv.push(newBar);
          if(blChart){
            try{
              const newIdx=_blOhlcv.length-1;
              const ds=blChart.data.datasets[1];
              if(ds&&ds.data) ds.data.push({x:newIdx,y:Number(cRaw)});
              blChart.update('none');
            }catch(_e){}
          }
          return;
        }
      }
      if(blChart) try{blChart.update('none');}catch(_e){}
    }else{
      delete _blExtendedPrice[ticker];
      if(lastDate!==today&&q.price!=null&&blCanBackfillTodayFromLive(lastDate,today)&&_blLiveSanityCheck(q.price,ref)&&_blLiveSanityCheck(q.low||q.price,ref)){
        const o=Number(q.open||q.price),h=Number(q.high||q.price),l=Number(q.low||q.price),c=Number(q.price);
        const newBar={t:today,o,h:Math.max(o,h,c),l:Math.min(o,l,c),c,v:Number(q.volume||0)};
        _blOhlcv.push(newBar);
        if(blChart){
          try{
            const newIdx=_blOhlcv.length-1;
            const ds=blChart.data.datasets[1];
            if(ds&&ds.data) ds.data.push({x:newIdx,y:Number(c)});
            blChart.update('none');
          }catch(_e){}
        }
      }else{
        let changed=false;
        if(q.price !=null&&_blLiveSanityCheck(q.price,ref)&&Number(q.price)!==Number(last.c)){last.c=Number(q.price);changed=true;}
        if(q.open  !=null&&_blLiveSanityCheck(q.open,ref) &&Number(q.open) !==Number(last.o)){last.o=Number(q.open); changed=true;}
        if(q.high  !=null&&_blLiveSanityCheck(q.high,ref) &&Number(q.high) >Number(last.h))  {last.h=Number(q.high); changed=true;}
        if(q.low   !=null&&_blLiveSanityCheck(q.low,ref)  &&Number(q.low)  <Number(last.l))  {last.l=Number(q.low);  changed=true;}
        if(q.volume!=null&&Number(q.volume)!==Number(last.v)){last.v=Number(q.volume);changed=true;}
        if(changed&&blChart){
          try{
            // Update close-line dataset (index 1) for line-chart display mode.
            // Plugins (wickPlugin, volumePlugin, etc.) read _blOhlcv directly,
            // so blChart.update('none') already redraws candles/wicks/volume.
            const ds=blChart.data.datasets[1];
            if(ds&&ds.data&&ds.data.length){
              const pt=ds.data[ds.data.length-1];
              if(pt&&typeof pt==='object') pt.y=Number(last.c);
            }
            blChart.update('none');
          }catch(_e){}
        }
      }
    }
  }
}

async function blLivePollOnce(force=false){
  // Poll during regular session AND extended hours (pre/post market).
  if(!(_blLiveEnabled&&_blLiveMarketOpen)) return;
  const now=Date.now();
  if(_blLivePollInFlight) return;
  if(!force && _blLiveLastPollAt && (now-_blLiveLastPollAt)<BL_LIVE_POLL_INTERVAL_MS) return;
  _blLivePollInFlight=true;
  _blLiveLastPollAt=now;
  try{
    const tickers=[...new Set([blCurrentTicker(),...watchlistVisibleSymbols()].filter(Boolean))];
    if(!tickers.length) return;
    const resp=await fetch('/api/live/quotes?tickers='+tickers.join(','));
    if(resp.status===401){
      // Token expired - flip to needs-auth state immediately without waiting for status poll
      _blLiveEnabled=false;
      _blSchwabNeedsAuth=true;
      _blSchwabAuthInProgress=false;
      blLiveUpdateBadge();
      blEnsureLivePollTimer();
      return;
    }
    if(!resp.ok) return;
    const quotes=await resp.json();
    Object.assign(_blLiveQuoteCache,quotes);
    blApplyLiveQuotes(quotes);
  }catch(_e){}
  finally {
    _blLivePollInFlight=false;
  }
}

async function blStartLivePoll(){
  try{
    const r=await fetch('/api/live/status');
    if(!r.ok) return;
    const s=await r.json();
    _blLiveEnabled=!!s.enabled;
    _blLiveMarketOpen=!!s.market_open;
    _blLiveRegularSession=!!s.regular_session;
    _blSchwabNeedsAuth=!!s.needs_auth;
    _blSchwabAuthInProgress=!!s.auth_in_progress;
    blLiveUpdateBadge();
    blEnsureLivePollTimer();
    // Always do one initial quote fetch on startup regardless of timer setting
    if(_blLiveEnabled&&_blLiveMarketOpen) blFetchLiveQuoteOnce();
    else if(_blAutoRefreshSecs>0) blQueueImmediateLivePoll();
    // Status refresh every 60 s - picks up session transitions (badge update only, no data fetch when timer is Off).
    setInterval(async()=>{
      try{
        const sr=await fetch('/api/live/status');if(!sr.ok)return;
        const ss=await sr.json();
        const wasEnabled=_blLiveEnabled;
        const wasOpen=_blLiveMarketOpen;
        _blLiveEnabled=!!ss.enabled;
        _blLiveMarketOpen=!!ss.market_open;
        _blLiveRegularSession=!!ss.regular_session;
        _blSchwabNeedsAuth=!!ss.needs_auth;
        _blSchwabAuthInProgress=!!ss.auth_in_progress;
        blLiveUpdateBadge();
        blEnsureLivePollTimer();
        // Only trigger a quote poll if the timer is on and session just opened
        if(_blAutoRefreshSecs>0&&_blLiveEnabled&&_blLiveMarketOpen&&(!wasEnabled||!wasOpen)) blQueueImmediateLivePoll();
      }catch(_e){}
    },60000);
  }catch(_e){}
}
// -----------------------------------------------------------------------------

function initUI(){
  try{
    try{
      const ps=JSON.parse(localStorage.getItem('gekko_panel_states')||'{}');
      const watchlistOpen = ps.watchlist!==false;
      const leftOpen = ps.left!==false;
      document.body.classList.toggle('watchlist-open', watchlistOpen);
      document.body.classList.toggle('panel-open', leftOpen);
      _blLeftPanelUserClosed = !leftOpen;
    }catch(_e){
      document.body.classList.add('panel-open');
      document.body.classList.add('watchlist-open');
    }
    loadWatchlists();
    loadBuyLevelsPrefs();
    watchlistInitBackup().catch(() => watchlistSetBackupStatus('Local browser storage only'));
    renderWatchlist();
    blCheckOhlcvVersion();
    setInterval(blCheckOhlcvVersion, 120000);
    blStartLivePoll();
    syncWatchlistPanelButton();
    switchTab(_getSavedTab(), null);
    setTimeout(()=>{
      relayoutBuyCharts();
      const cur=blCurrentTicker();
      if(cur && _blGIPos==='lower') renderGIChart(cur);
    }, 250);
    setTimeout(()=>{
      const cur=blCurrentTicker();
      if(cur && _blGIPos==='lower' && !giHistChart) renderGIChart(cur);
    }, 800);
  }catch(err){ showJsError('Initial load failed', err); console.error(err); }
}
async function loadAppData(){
  const overlay=document.getElementById('app-loading-overlay');
  const msg=document.getElementById('app-loading-msg');
  const bar=document.getElementById('app-loading-bar');
  let done=0;
  if(msg) msg.textContent='Loading core data...';
  if(bar) bar.style.width='8%';
  const endpoints=[
    ['/api/buy-meta',          'Buy levels'],
    ['/api/zone-returns',      'Zone returns'],
    ['/api/zone-returns-all',  'Zone detail'],
  ];
  const total=endpoints.length;
  try{
    const results=await Promise.all(endpoints.map(async([url,label])=>{
      const ctrl=new AbortController();
      const tid=setTimeout(()=>ctrl.abort(),30000); // 30s timeout per request
      let resp;
      try{ resp=await fetch(url,{signal:ctrl.signal}); }
      finally{ clearTimeout(tid); }
      if(!resp.ok) throw new Error(label+' '+resp.status);
      const sourceUpdatedAt = resp.headers.get('X-Gekko-Source-Updated-At') || '';
      const data=await resp.json();
      done++;
      if(msg) msg.textContent='Loaded: '+label;
      if(bar)  bar.style.width=Math.round(done/total*100)+'%';
      return {data, sourceUpdatedAt};
    }));
    const [buyMeta,zrData,zrAll]=results.map(x=>x||{data:null,sourceUpdatedAt:''});
    GI_HISTORY={};
    _applyBuyMetaData((buyMeta.data && typeof buyMeta.data==='object') ? buyMeta.data : {});
    ZR_DATA.push(...((zrData&&zrData.data)||[]));
    Object.assign(ZR_ALL,           (zrAll&&zrAll.data)||{});
    ZR_DATA.forEach(r=>{ if(r&&!r.company) r.company=BL_TICKER_INFO[r.ticker]||''; blRememberTickerCompany(r?.ticker, r?.company); });
  }catch(err){
    console.error('loadAppData failed', err);
    const isTimeout=err.name==='AbortError';
    const hint=isTimeout?'Server took too long to respond (>30s)':err.message;
    if(overlay) overlay.innerHTML='<div style="text-align:center;color:#ef4444;font-family:JetBrains Mono,monospace;padding:40px;line-height:1.8">Failed to load data.<br><small style="color:#777">'+hint+'</small><br><br><small style="color:#555">Make sure gekko_server.py is running:<br>python gekko_server.py</small><br><br><button onclick="location.reload()" style="margin-top:8px;padding:6px 18px;background:#1a1a1a;border:1px solid #333;color:#ccc;border-radius:6px;cursor:pointer;font-family:inherit">↻ Retry</button></div>';
    return;
  }
  if(overlay) overlay.style.display='none';
  initUI();
  _prefetchWatchlistOHLCV();  // load last-close bars for active watchlist price display
  startAutoRefresh();
}
loadAppData();

</script>

<!-- ============================================================
     REFINED LAYER — additive, toggleable.
     Adds: timeframe pills, tweaks toggle, bottom status bar.
     ============================================================ -->
<style>
#refinedStatusBar {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 9500;
  height: 26px;
  display: none;
  align-items: center;
  padding: 0 14px;
  background: #0a0a0a;
  border-top: 1px solid #1f1f1f;
  color: #9a9a9a;
  font-family: var(--sans);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.01em;
  gap: 14px;
  user-select: none;
  line-height: 1;
  box-sizing: border-box;
  white-space: nowrap;
  overflow: hidden;
}
/* status bar hidden — market status shown in toolbar instead */
/* also lift any bottom-fixed toasts above us if needed */

#refinedStatusBar .sb-live {
  display: inline-flex; align-items: center; gap: 6px;
  color: #4ade80;
  font-weight: 700; letter-spacing: 0.12em;
  font-size: 10px;
  flex-shrink: 0;
}
#refinedStatusBar .sb-live .sb-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
  animation: sbPulse 2s infinite;
}
@keyframes sbPulse {
  0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.6); }
  70% { box-shadow: 0 0 0 5px rgba(74, 222, 128, 0); }
  100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
}
#refinedStatusBar .sb-sep {
  width: 1px; height: 12px; background: #262626;
  flex-shrink: 0;
}
#refinedStatusBar .sb-item { display: inline-flex; align-items: center; gap: 6px; flex-shrink: 0; }
#refinedStatusBar .sb-k { color: #6a6a6a; }
#refinedStatusBar .sb-v { color: #d0d0d0; font-variant-numeric: tabular-nums; }
#refinedStatusBar .sb-spacer { flex: 1 1 auto; }
#refinedStatusBar .sb-market-open { color: #4ade80; font-weight: 600; }
#refinedStatusBar .sb-market-closed { color: #f87171; font-weight: 600; }

/* Market status badge shown in toolbar */

/* Tweaks float button */
#refinedTweaksToggle {
  display: none !important;
}
</style>

<!-- Bottom status bar -->
<div id="refinedStatusBar">
  <span class="sb-live"><span class="sb-dot"></span>LIVE</span>
  <span class="sb-sep"></span>
  <span class="sb-item"><span class="sb-k">US Market</span><span class="sb-v" id="sbMarketStatus">· Open</span></span>
  <span class="sb-sep"></span>
  <span class="sb-item"><span class="sb-v">Gekko Engine v4.2.1</span></span>
  <span class="sb-spacer"></span>
  <span class="sb-item"><span class="sb-k">Cache</span><span class="sb-v" id="sbCache">98.4%</span></span>
  <span class="sb-sep"></span>
  <span class="sb-item"><span class="sb-v" id="sbLatency">216ms</span></span>
</div>

<!-- Tweaks panel -->
<button id="refinedTweaksToggle" type="button">Style</button>
<div id="refinedTweaks">
  <div class="rt-title">Style</div>
  <div class="rt-opts">
    <button class="rt-opt" data-mode="original" type="button">Original</button>
    <button class="rt-opt active" data-mode="refined" type="button">Refined</button>
  </div>
  <div class="rt-title" style="margin-top:4px">Status Bar</div>
  <div class="rt-opts">
    <button class="rt-opt" data-sb="off" type="button">Hide</button>
    <button class="rt-opt active" data-sb="on" type="button">Show</button>
  </div>
</div>

<script>
(function(){
  // Enable refined mode by default
  document.body.classList.add('refined');

  /* ---------- Watchlist gear button ---------- */
  function buildWlGear() {
    const topbar = document.querySelector('#watchlistPanel .watchlist-topbar');
    if (!topbar || document.getElementById('refinedWlGear')) return;

    const btn = document.createElement('button');
    btn.id = 'refinedWlGear';
    btn.type = 'button';
    btn.title = 'Watchlist settings';
    btn.setAttribute('aria-label', 'Watchlist settings');
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>';

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (typeof toggleWlSettings === 'function') {
        try { toggleWlSettings(); } catch (err) {}
      }
      const menu = document.getElementById('wlSettingsMenu');
      btn.classList.toggle('open', !!(menu && menu.classList.contains('open')));
    });

    // Close gear state when menu closes externally
    const menu = document.getElementById('wlSettingsMenu');
    if (menu) {
      const obs = new MutationObserver(() => {
        btn.classList.toggle('open', menu.classList.contains('open'));
      });
      obs.observe(menu, { attributes: true, attributeFilter: ['class'] });
    }

    // Append gear to the topbar (row layout sends it to the right of .watchlist-controls)
    topbar.appendChild(btn);

    // Strip the in-<select> "Settings" option and the "----------" divider the app injects,
    // since the gear button replaces them.
    const dd = document.getElementById('watchlistDropdown');
    if (dd) {
      const rm = () => {
        Array.from(dd.options).forEach(o => {
          const txt = (o.textContent || '').trim();
          const low = txt.toLowerCase();
          const isSettings = low.includes('settings') || low.includes('⚙');
          const isDivider = o.disabled || /^[-─—_\s]+$/.test(txt);
          if (isSettings || isDivider) o.remove();
        });
      };
      rm();
      const ddObs = new MutationObserver(rm);
      ddObs.observe(dd, { childList: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildWlGear);
  } else {
    buildWlGear();
  }
  // Also try after a tick in case the app re-renders the watchlist
  setTimeout(buildWlGear, 500);
  setTimeout(buildWlGear, 1500);

  /* ---------- Timeframe pills: inject next to the <select id=blChartPeriod> ---------- */
  function buildTfPills() {
    const sel = document.getElementById('blChartPeriod');
    if (!sel || document.getElementById('tfPills')) return;

    // Hide the "Chart" label right before the select (matches markup pattern)
    const prev = sel.previousElementSibling;
    if (prev && prev.classList && prev.classList.contains('ctrl-label')) {
      prev.classList.add('ctrl-label-chart-tf');
    }

    // Daily/weekly/monthly-friendly set
    const presets = [
      { label: '1M',  value: '30' },
      { label: '3M',  value: '90' },
      { label: '6M',  value: '180' },
      { label: 'YTD', value: 'ytd' },
      { label: '1Y',  value: '365' },
      { label: '2Y',  value: '730' },
      { label: 'All', value: '0' },
    ];

    // Compute YTD day count (days since Jan 1 of current year, min 1)
    function ytdDays() {
      const now = new Date();
      const jan1 = new Date(now.getFullYear(), 0, 1);
      const days = Math.max(1, Math.floor((now - jan1) / 86400000));
      return String(days);
    }

    // Ensure the YTD option exists on the <select> (value = dynamic day count)
    function ensureYtdOption() {
      const days = ytdDays();
      let opt = Array.from(sel.options).find(o => o.dataset.ytd === '1');
      if (!opt) {
        opt = document.createElement('option');
        opt.dataset.ytd = '1';
        opt.textContent = 'YTD';
        // insert after the 6-month option if present, else before 1-year
        const oneY = Array.from(sel.options).find(o => o.value === '365');
        sel.insertBefore(opt, oneY || null);
      }
      opt.value = days;
      return days;
    }

    const wrap = document.createElement('div');
    wrap.id = 'tfPills';
    wrap.className = 'tf-pills';
    wrap.setAttribute('role', 'tablist');
    presets.forEach(p => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'tf-pill';
      b.dataset.val = p.value;
      b.textContent = p.label;
      b.addEventListener('click', () => {
        let targetVal = p.value;
        if (p.value === 'ytd') {
          targetVal = ensureYtdOption();
        }
        sel.value = targetVal;
        if (sel.value !== targetVal) {
          const opt = Array.from(sel.options).find(o => o.value === targetVal);
          if (opt) sel.value = opt.value;
        }
        sel.dispatchEvent(new Event('change', { bubbles: true }));
        if (typeof blChartPeriodChange === 'function') {
          try { blChartPeriodChange(); } catch (e) {}
        }
        syncTfPills();
      });
      wrap.appendChild(b);
    });

    sel.insertAdjacentElement('afterend', wrap);
    syncTfPills();
  }

  function syncTfPills() {
    const sel = document.getElementById('blChartPeriod');
    const wrap = document.getElementById('tfPills');
    if (!sel || !wrap) return;
    const cur = String(sel.value);
    // Find the YTD option's current day-count so we can match it
    const ytdOpt = Array.from(sel.options).find(o => o.dataset && o.dataset.ytd === '1');
    const ytdVal = ytdOpt ? ytdOpt.value : null;
    wrap.querySelectorAll('.tf-pill').forEach(b => {
      let match = false;
      if (b.dataset.val === 'ytd') {
        match = (ytdVal !== null && cur === ytdVal);
      } else {
        match = (b.dataset.val === cur);
      }
      b.classList.toggle('active', match);
    });
  }

  // Build when DOM ready; also watch for tab switches that might re-render
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildTfPills);
  } else {
    buildTfPills();
  }
  // Keep pills in sync if something else changes the select
  document.addEventListener('change', (e) => {
    if (e.target && e.target.id === 'blChartPeriod') syncTfPills();
  });

  /* ---------- Tweaks panel ---------- */
  const toggleBtn = document.getElementById('refinedTweaksToggle');
  const panel = document.getElementById('refinedTweaks');
  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (!panel.contains(e.target) && e.target !== toggleBtn) panel.classList.remove('open');
  });

  panel.querySelectorAll('[data-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;
      document.body.classList.toggle('refined', mode === 'refined');
      panel.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('active', b === btn));
    });
  });
  panel.querySelectorAll('[data-sb]').forEach(btn => {
    btn.addEventListener('click', () => {
      const on = btn.dataset.sb === 'on';
      document.getElementById('refinedStatusBar').style.display = on ? '' : 'none';
      panel.querySelectorAll('[data-sb]').forEach(b => b.classList.toggle('active', b === btn));
    });
  });

  /* ---------- Market badge in toolbar ---------- */
  function refreshMarketBadge() {
    if (typeof blLiveUpdateBadge === 'function') blLiveUpdateBadge();
  }
  // Show badge once JS is ready, then keep it current
  setTimeout(refreshMarketBadge, 200);
  setInterval(refreshMarketBadge, 60000);
})();
</script>

<!-- Bubble Chart v2 — React component (Babel transpiled) -->
<script type="text/babel" data-presets="react">
(function(){
// useTweaks — lightweight localStorage-backed settings hook
window.TWEAK_DEFAULTS = {
  xAxis:'gi', yAxis:'managers', sizeAxis:'totalValue',
  showQuadrants:true, showLabels:true, viewMode:'default',
  minManagers:1, minGi:0, sector:'all',
  onlyInsiders:false, onlyPinned:false, labelDensity:20,
};
window.useTweaks = function(defaults){
  const [vals, setVals] = React.useState(()=>{
    try{ const s=JSON.parse(localStorage.getItem('gekko_bc_cfg')||'{}'); return{...defaults,...s}; }
    catch{ return{...defaults}; }
  });
  const setTweak = React.useCallback((k,v)=>{
    setVals(prev=>{
      const next={...prev,[k]:v};
      try{ localStorage.setItem('gekko_bc_cfg',JSON.stringify(next)); }catch{}
      return next;
    });
  },[]);
  return [vals, setTweak];
};

// ---------- axis definitions ----------
const AXES = {
  managers:{ label:'Managers Holding', short:'Mgrs', get:r=>r.manager_count, fmt:v=>String(v), min:0 },
  gi:{ label:'GI Score', short:'GI', get:r=>r.gi_score, fmt:v=>(v==null?'—':v.toFixed(1)), min:0, max:100 },
  chg30:{ label:'30d Change', short:'30d Δ', get:r=>r.chg_30d, fmt:v=>window.fmtPct(v) },
  chg90:{ label:'90d Change', short:'90d Δ', get:r=>r.chg_90d, fmt:v=>window.fmtPct(v) },
  newCount:{ label:'New Positions', short:'New', get:r=>r.new_count, fmt:v=>String(v), min:0 },
  insiderDist:{ label:'Insider Buys (distinct)', short:'Insiders', get:r=>r.insider_buys_distinct, fmt:v=>String(v), min:0 },
  totalValue:{ label:'Held Value', short:'Held $', get:r=>r.total_value, fmt:v=>window.fmtMoney(v), min:0, log:true },
  newValue:{ label:'New-Position $', short:'New $', get:r=>r.new_value, fmt:v=>window.fmtMoney(v), min:0, log:true },
  insiderValue:{ label:'Insider Buy $', short:'Insider $', get:r=>r.insider_buys_value, fmt:v=>window.fmtMoney(v), min:0 },
};

const ARCHETYPE = {
  mega:         { icon:'◆', text:'Mega-cap institutional favorite' },
  hidden_gem:   { icon:'✦', text:'Hidden gem — few holders, strong accumulation' },
  crowded_trap: { icon:'⚠', text:'Crowded trap — heavily held, distributing' },
  falling_knife:{ icon:'▼', text:'Falling knife — low GI, thin ownership' },
  neutral:      { icon:'·', text:'Neutral — mixed signals' },
};

const TIER_COLOR = {
  'dark-green':'#22c55e','green':'#86efac','yellow':'#facc15','orange':'#f97316','red':'#ef4444'
};

function niceStep(span){
  const p=Math.pow(10,Math.floor(Math.log10(Math.abs(span)||1)));
  const n=span/p;
  if(n<=1)return 0.2*p; if(n<=2)return 0.5*p; if(n<=5)return 1*p; return 2*p;
}

function axisRange(vals,axis){
  if(!vals.length)return[0,1];
  let min=Math.min(...vals), max=Math.max(...vals);
  if(axis.min!=null)min=axis.min;
  if(axis.max!=null)max=axis.max;
  const pad=(max-min)*0.06||1;
  return[Math.max(axis.min??-Infinity,min-pad),Math.min(axis.max??Infinity,max+pad)];
}

function placeLabels(points,ctx){
  const placed=[];
  ctx.font='500 10px "JetBrains Mono"';
  for(const p of points){
    if(!p._wantLabel)continue;
    const w=ctx.measureText(p.ticker).width+8, h=14;
    const cands=[
      {x:p.sx+p.r+4, y:p.sy-h/2},
      {x:p.sx-w/2,   y:p.sy-p.r-h-2},
      {x:p.sx-p.r-w-4, y:p.sy-h/2},
      {x:p.sx-w/2,   y:p.sy+p.r+2},
    ];
    let chosen=null;
    for(const c of cands){
      const box={x:c.x,y:c.y,w,h};
      const collides=placed.some(b=>!(box.x+box.w<b.x||box.x>b.x+b.w||box.y+box.h<b.y||box.y>b.y+b.h));
      if(!collides){chosen=box;break;}
    }
    if(chosen){placed.push(chosen);p._labelBox=chosen;}
  }
  return placed;
}

// ---------- main component ----------
function BubbleChartApp({ rows=[] }){
  const { useEffect, useRef, useState, useCallback, useMemo } = React;

  const canvasRef = useRef(null);
  const dataRef = useRef(rows);
  const [rowsVersion, setRowsVersion] = useState(0);

  useEffect(()=>{
    dataRef.current=rows;
    setRowsVersion(v=>v+1);
  },[rows]);

  const [tv, setTweak] = window.useTweaks(window.TWEAK_DEFAULTS);
  const t = { values:tv, set:(obj)=>{ for(const k in obj) setTweak(k,obj[k]); } };

  const [hotTiers, setHotTiers] = useState(new Set(['dark-green','green','yellow','orange','red']));
  const [hoverPt, setHoverPt] = useState(null);
  const [hoverPos, setHoverPos] = useState({x:0,y:0});
  const [selected, setSelected] = useState(new Set());
  const [pinned, setPinned] = useState(()=>{
    try{ return new Set(JSON.parse(localStorage.getItem('gekko_pinned')||'[]')); }
    catch{ return new Set(); }
  });
  const [search, setSearch] = useState('');
  const [view, setView] = useState({xMin:null,xMax:null,yMin:null,yMax:null});
  const [pulseTicker, setPulseTicker] = useState(null);
  const [axisMenu, setAxisMenu] = useState(null);
  const [lasso, setLasso] = useState(null);
  const [panning, setPanning] = useState(false);
  const [openChip, setOpenChip] = useState(null);
  const [popPos, setPopPos] = useState({x:0,y:0});
  const chipRefs = useRef({});

  useEffect(()=>{
    try{ localStorage.setItem('gekko_pinned',JSON.stringify([...pinned])); }catch{}
  },[pinned]);

  const filtered = useMemo(()=>{
    return dataRef.current.filter(r=>{
      if(!hotTiers.has(r.gi_tier))return false;
      if(r.manager_count<tv.minManagers)return false;
      if(r.gi_score<tv.minGi)return false;
      if(tv.sector!=='all'&&r.sector!==tv.sector)return false;
      if(tv.onlyInsiders&&r.insider_buys_distinct<1)return false;
      if(tv.onlyPinned&&!pinned.has(r.ticker))return false;
      return true;
    });
  },[hotTiers,tv.minManagers,tv.minGi,tv.sector,tv.onlyInsiders,tv.onlyPinned,pinned,rowsVersion]);

  const xA=AXES[tv.xAxis], yA=AXES[tv.yAxis], sA=AXES[tv.sizeAxis];
  const drawRef=useRef(()=>{});

  const draw=useCallback(()=>{
    const canvas=canvasRef.current;
    if(!canvas)return;
    const dpr=window.devicePixelRatio||1;
    const rect=canvas.parentElement.getBoundingClientRect();
    canvas.width=rect.width*dpr; canvas.height=rect.height*dpr;
    canvas.style.width=rect.width+'px'; canvas.style.height=rect.height+'px';
    const ctx=canvas.getContext('2d');
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,rect.width,rect.height);

    const W=rect.width, H=rect.height;
    const pad={l:56,r:16,t:16,b:36};
    const pw=W-pad.l-pad.r, ph=H-pad.t-pad.b;

    const xVals=filtered.map(r=>xA.get(r)).filter(v=>v!=null&&isFinite(v));
    const yVals=filtered.map(r=>yA.get(r)).filter(v=>v!=null&&isFinite(v));
    const sVals=filtered.map(r=>sA.get(r)).filter(v=>v!=null&&isFinite(v)&&v>=0);

    const emptyEl=document.getElementById('emptyState');
    if(!xVals.length||!yVals.length){
      if(emptyEl)emptyEl.style.display='flex';
      return;
    }
    if(emptyEl)emptyEl.style.display='none';

    let [xMin,xMax]=view.xMin!=null?[view.xMin,view.xMax]:axisRange(xVals,xA);
    let [yMin,yMax]=view.yMin!=null?[view.yMin,view.yMax]:axisRange(yVals,yA);

    const xScale=v=>pad.l+((v-xMin)/(xMax-xMin))*pw;
    const yScale=v=>pad.t+(1-(v-yMin)/(yMax-yMin))*ph;

    const sMin=Math.min(...sVals,0), sMax=Math.max(...sVals,1);
    const minR=4, maxR=26;
    const rScale=v=>{
      if(sMax<=0)return minR;
      const vv=Math.max(0,v||0);
      if(sA.log){
        const L=Math.log1p(vv),Lmin=Math.log1p(Math.max(0,sMin)),Lmax=Math.log1p(sMax);
        if(Lmax===Lmin)return(minR+maxR)/2;
        return minR+((L-Lmin)/(Lmax-Lmin))*(maxR-minR);
      }
      const n=(Math.sqrt(vv)-Math.sqrt(Math.max(0,sMin)))/(Math.sqrt(sMax)-Math.sqrt(Math.max(0,sMin))||1);
      return Math.max(minR,Math.min(maxR,minR+n*(maxR-minR)));
    };

    // quadrant dividers
    if(tv.showQuadrants&&tv.viewMode==='default'){
      const xMid=(xMin+xMax)/2;
      const yMid=yA===AXES.gi?50:(yMin+yMax)/2;
      ctx.strokeStyle='rgba(255,255,255,.05)'; ctx.lineWidth=1; ctx.setLineDash([3,4]);
      ctx.beginPath();
      ctx.moveTo(xScale(xMid),pad.t); ctx.lineTo(xScale(xMid),H-pad.b);
      ctx.moveTo(pad.l,yScale(yMid)); ctx.lineTo(W-pad.r,yScale(yMid));
      ctx.stroke(); ctx.setLineDash([]);
      updateQuadrantLabels(xA,yA);
    } else {
      ['q-tl','q-tr','q-bl','q-br'].forEach(id=>{const el=document.getElementById(id);if(el)el.classList.remove('on');});
    }

    // grid
    ctx.strokeStyle='rgba(255,255,255,.04)'; ctx.lineWidth=1;
    ctx.font='10px "JetBrains Mono"'; ctx.fillStyle='#555';
    const xStep=niceStep((xMax-xMin)/6);
    for(let v=Math.ceil(xMin/xStep)*xStep;v<=xMax;v+=xStep){
      const x=xScale(v);
      ctx.beginPath(); ctx.moveTo(x,pad.t); ctx.lineTo(x,H-pad.b); ctx.stroke();
      ctx.textAlign='center'; ctx.textBaseline='top';
      ctx.fillText(xA.fmt(v).replace('$',''),x,H-pad.b+6);
    }
    const yStep=niceStep((yMax-yMin)/6);
    for(let v=Math.ceil(yMin/yStep)*yStep;v<=yMax;v+=yStep){
      const y=yScale(v);
      ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(W-pad.r,y); ctx.stroke();
      ctx.textAlign='right'; ctx.textBaseline='middle';
      ctx.fillText(yA.fmt(v),pad.l-8,y);
    }

    // density heatmap
    if(tv.viewMode==='density'){
      const cells=24, cw=pw/cells, chh=ph/cells;
      const grid=Array.from({length:cells},()=>new Array(cells).fill(0));
      filtered.forEach(r=>{
        const x=xA.get(r),y=yA.get(r);
        if(x==null||y==null)return;
        const cx=Math.min(cells-1,Math.max(0,Math.floor((x-xMin)/(xMax-xMin)*cells)));
        const cy=Math.min(cells-1,Math.max(0,Math.floor((y-yMin)/(yMax-yMin)*cells)));
        grid[cy][cx]+=1+(r.gi_score/50);
      });
      const maxCell=Math.max(...grid.flat(),1);
      for(let cy=0;cy<cells;cy++)for(let cx=0;cx<cells;cx++){
        const v=grid[cy][cx]/maxCell;
        if(v<.02)continue;
        ctx.fillStyle=`rgba(34,197,94,${v*0.35})`;
        ctx.fillRect(pad.l+cx*cw, pad.t+(cells-1-cy)*chh, cw, chh);
      }
    }

    // bubbles
    const pts=filtered.map(r=>{
      const xv=xA.get(r),yv=yA.get(r),sv=sA.get(r);
      if(xv==null||yv==null)return null;
      return{r:rScale(sv||0),sx:xScale(xv),sy:yScale(yv),ticker:r.ticker,company:r.company,sector:r.sector,giScore:r.gi_score,giTier:r.gi_tier,row:r,pinned:pinned.has(r.ticker),selected:selected.has(r.ticker)};
    }).filter(Boolean);
    pts.sort((a,b)=>b.r-a.r);

    const colorFor=p=>{
      if(tv.viewMode==='sector')return(window.SECTOR_COLORS[p.sector]||'#999');
      return TIER_COLOR[p.giTier]||'#999';
    };

    for(const p of pts){
      const col=colorFor(p);
      const isSearched=pulseTicker&&p.ticker.toLowerCase().includes(pulseTicker.toLowerCase());
      const dimmed=pulseTicker&&!isSearched;
      const alpha=dimmed?0.12:(p.selected?1:0.75);
      ctx.globalAlpha=alpha*0.55; ctx.fillStyle=col;
      ctx.beginPath(); ctx.arc(p.sx,p.sy,p.r,0,Math.PI*2); ctx.fill();
      ctx.globalAlpha=alpha; ctx.strokeStyle=col;
      ctx.lineWidth=p.row.insider_buys_distinct>0?2.5:1.2;
      ctx.stroke();
      if(p.row.insider_buys_distinct>0){
        ctx.strokeStyle=`rgba(251,191,36,${alpha*0.7})`; ctx.lineWidth=1.5;
        ctx.beginPath(); ctx.arc(p.sx,p.sy,p.r+3,0,Math.PI*2); ctx.stroke();
      }
      if(p.pinned){
        ctx.fillStyle=`rgba(251,191,36,${alpha})`;
        ctx.beginPath(); ctx.arc(p.sx+p.r*0.7,p.sy-p.r*0.7,3,0,Math.PI*2); ctx.fill();
      }
      if(p.selected){
        ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.globalAlpha=1;
        ctx.beginPath(); ctx.arc(p.sx,p.sy,p.r+4,0,Math.PI*2); ctx.stroke();
      }
      ctx.globalAlpha=1;
    }

    if(pulseTicker){
      for(const p of pts){
        if(!p.ticker.toLowerCase().includes(pulseTicker.toLowerCase()))continue;
        const pulse=(Date.now()/600)%1;
        ctx.strokeStyle=`rgba(255,255,255,${1-pulse})`; ctx.lineWidth=2;
        ctx.beginPath(); ctx.arc(p.sx,p.sy,p.r+4+pulse*18,0,Math.PI*2); ctx.stroke();
      }
    }

    if(tv.showLabels){
      const sorted=[...pts].sort((a,b)=>{
        const sa=(a.pinned?1e9:0)+(a.selected?5e8:0)+a.r;
        const sb=(b.pinned?1e9:0)+(b.selected?5e8:0)+b.r;
        return sb-sa;
      });
      const budget=Math.max(4,Math.min(sorted.length,Math.round(tv.labelDensity)));
      sorted.slice(0,budget).forEach(p=>p._wantLabel=true);
      placeLabels(sorted,ctx);
      ctx.font='600 10px "JetBrains Mono"';
      sorted.forEach(p=>{
        if(!p._labelBox)return;
        const b=p._labelBox;
        ctx.fillStyle='rgba(0,0,0,.55)'; ctx.fillRect(b.x,b.y,b.w,b.h);
        ctx.fillStyle=p.selected?'#fff':'rgba(234,234,234,.92)';
        ctx.textAlign='left'; ctx.textBaseline='middle';
        ctx.fillText(p.ticker,b.x+4,b.y+b.h/2);
      });
    }

    if(lasso){
      const x=Math.min(lasso.x0,lasso.x1), y=Math.min(lasso.y0,lasso.y1);
      const w=Math.abs(lasso.x1-lasso.x0), h=Math.abs(lasso.y1-lasso.y0);
      ctx.strokeStyle='rgba(255,255,255,.5)'; ctx.fillStyle='rgba(255,255,255,.05)'; ctx.lineWidth=1;
      ctx.setLineDash([4,3]); ctx.fillRect(x,y,w,h); ctx.strokeRect(x,y,w,h); ctx.setLineDash([]);
    }

    canvas._pts=pts;
    canvas._scale={xScale,yScale,xMin,xMax,yMin,yMax,pad,W,H};
    const rcShown=document.getElementById('rcShown');
    const rcTotal=document.getElementById('rcTotal');
    if(rcShown)rcShown.textContent=filtered.length;
    if(rcTotal)rcTotal.textContent=dataRef.current.length;
  },[filtered,xA,yA,sA,tv.showQuadrants,tv.showLabels,tv.viewMode,tv.labelDensity,pinned,selected,pulseTicker,view,lasso]);

  drawRef.current=draw;

  function updateQuadrantLabels(xA,yA){
    const mapping={
      'managers-gi':{tl:'✦ Hidden Gems',tr:'★ Crowded Winners',bl:'▾ Forgotten',br:'⚠ Crowded Traps'},
      'managers-chg30':{tl:'✦ Contrarian Winners',tr:'★ Momentum Favorites',bl:'▾ Orphans',br:'⚠ Crowded & Fading'},
      'gi-managers':{tl:'▾ Thin Coverage',tr:'★ Crowded Winners',bl:'⚠ Forgotten',br:'✦ Hidden Gems'},
    };
    const xKey=Object.keys(AXES).find(k=>AXES[k]===xA)||'';
    const yKey=Object.keys(AXES).find(k=>AXES[k]===yA)||'';
    const key=`${xKey}-${yKey}`;
    const q=mapping[key];
    ['tl','tr','bl','br'].forEach((pos,i)=>{
      const el=document.getElementById(`q-${pos}`);
      if(!el)return;
      if(q&&q[pos]){
        el.textContent=q[pos]; el.classList.add('on');
        el.style.color=pos==='tr'?'#86efac':pos==='tl'?'#a5e077':pos==='br'?'#fca5a5':'#9ca3af';
      } else {
        el.classList.remove('on');
      }
    });
  }

  useEffect(()=>{draw();},[draw]);

  useEffect(()=>{
    const ro=new ResizeObserver(()=>draw());
    if(canvasRef.current)ro.observe(canvasRef.current.parentElement);
    return()=>ro.disconnect();
  },[draw]);

  useEffect(()=>{
    if(!pulseTicker)return;
    let raf;
    const tick=()=>{draw();raf=requestAnimationFrame(tick);};
    tick();
    return()=>cancelAnimationFrame(raf);
  },[pulseTicker,draw]);

  // hit test
  const hitTest=(mx,my)=>{
    const canvas=canvasRef.current;
    if(!canvas||!canvas._pts)return null;
    const rect=canvas.getBoundingClientRect();
    const x=mx-rect.left, y=my-rect.top;
    for(let i=canvas._pts.length-1;i>=0;i--){
      const p=canvas._pts[i];
      const dx=x-p.sx, dy=y-p.sy;
      if(dx*dx+dy*dy<=(p.r+2)*(p.r+2))return p;
    }
    return null;
  };

  const onMouseMove=e=>{
    if(panning){return;}
    if(lasso){
      const rect=canvasRef.current.getBoundingClientRect();
      setLasso(l=>({...l,x1:e.clientX-rect.left,y1:e.clientY-rect.top}));
      return;
    }
    const p=hitTest(e.clientX,e.clientY);
    if(p){setHoverPt(p);setHoverPos({x:e.clientX,y:e.clientY});}
    else setHoverPt(null);
  };
  const onMouseLeave=()=>setHoverPt(null);
  const onMouseDown=e=>{
    if(e.button!==0)return;
    const rect=canvasRef.current.getBoundingClientRect();
    const x=e.clientX-rect.left, y=e.clientY-rect.top;
    if(e.shiftKey){
      setPanning({startX:e.clientX,startY:e.clientY,view:{...view}});
    } else {
      const p=hitTest(e.clientX,e.clientY);
      if(p){
        setSelected(prev=>{
          const n=e.ctrlKey||e.metaKey?new Set(prev):new Set();
          if(n.has(p.ticker))n.delete(p.ticker);else n.add(p.ticker);
          return n;
        });
      } else {
        setLasso({x0:x,y0:y,x1:x,y1:y});
        if(!e.ctrlKey&&!e.metaKey)setSelected(new Set());
      }
    }
  };
  const onMouseUp=e=>{
    if(panning){setPanning(false);return;}
    if(lasso){
      const x0=Math.min(lasso.x0,lasso.x1), x1=Math.max(lasso.x0,lasso.x1);
      const y0=Math.min(lasso.y0,lasso.y1), y1=Math.max(lasso.y0,lasso.y1);
      if(Math.abs(x1-x0)>4&&Math.abs(y1-y0)>4){
        const pts=(canvasRef.current._pts||[]).filter(p=>p.sx>=x0&&p.sx<=x1&&p.sy>=y0&&p.sy<=y1);
        setSelected(new Set(pts.map(p=>p.ticker)));
      }
      setLasso(null);
    }
  };
  const onDoubleClick=()=>{setView({xMin:null,xMax:null,yMin:null,yMax:null});setSelected(new Set());};
  const onWheel=e=>{
    e.preventDefault();
    const canvas=canvasRef.current, sc=canvas?._scale;
    if(!sc)return;
    const rect=canvas.getBoundingClientRect();
    const mx=e.clientX-rect.left, my=e.clientY-rect.top;
    const{xMin,xMax,yMin,yMax,pad,W,H}=sc;
    const pw=W-pad.l-pad.r, ph=H-pad.t-pad.b;
    const xAtMouse=xMin+((mx-pad.l)/pw)*(xMax-xMin);
    const yAtMouse=yMin+(1-(my-pad.t)/ph)*(yMax-yMin);
    const factor=e.deltaY<0?0.85:1/0.85;
    setView({
      xMin:xAtMouse+(xMin-xAtMouse)*factor,
      xMax:xAtMouse+(xMax-xAtMouse)*factor,
      yMin:yAtMouse+(yMin-yAtMouse)*factor,
      yMax:yAtMouse+(yMax-yAtMouse)*factor,
    });
  };

  // pan
  useEffect(()=>{
    if(!panning)return;
    const onMove=e=>{
      const sc=canvasRef.current?._scale;if(!sc)return;
      const{pad,W,H}=sc;
      const pw=W-pad.l-pad.r, ph=H-pad.t-pad.b;
      const dx=(e.clientX-panning.startX)/pw, dy=(e.clientY-panning.startY)/ph;
      const v=panning.view;
      const xr=(v.xMax??1)-(v.xMin??0), yr=(v.yMax??1)-(v.yMin??0);
      setView({xMin:(v.xMin??0)-dx*xr,xMax:(v.xMax??1)-dx*xr,yMin:(v.yMin??0)+dy*yr,yMax:(v.yMax??1)+dy*yr});
    };
    const onUp=()=>setPanning(false);
    window.addEventListener('mousemove',onMove);
    window.addEventListener('mouseup',onUp);
    return()=>{window.removeEventListener('mousemove',onMove);window.removeEventListener('mouseup',onUp);};
  },[panning]);

  // escape key
  useEffect(()=>{
    const h=e=>{if(e.key==='Escape'){setOpenChip(null);setSelected(new Set());}};
    document.addEventListener('keydown',h);
    return()=>document.removeEventListener('keydown',h);
  },[]);

  // axis labels
  useEffect(()=>{
    ['xAxisLabel','yAxisLabel','sizeLabel'].forEach((id,i)=>{
      const el=document.getElementById(id);
      if(!el)return;
      const axis=[xA,yA,sA][i];
      el.textContent=axis.label;
      el.onclick=e=>{
        const r=el.getBoundingClientRect();
        setAxisMenu({kind:['x','y','s'][i],x:r.left,y:r.bottom+4});
      };
    });
  },[xA,yA,sA]);

  useEffect(()=>{
    if(!axisMenu)return;
    const close=()=>setAxisMenu(null);
    setTimeout(()=>document.addEventListener('click',close,{once:true}),0);
  },[axisMenu]);

  // GI tier toggle
  useEffect(()=>{
    const h=e=>{
      const seg=e.target.closest('.gi-seg');if(!seg)return;
      const tier=seg.dataset.tier;
      setHotTiers(prev=>{
        const n=new Set(prev);
        if(n.has(tier))n.delete(tier);else n.add(tier);
        return n.size===0?new Set(['dark-green','green','yellow','orange','red']):n;
      });
    };
    const el=document.getElementById('giScale');
    el?.addEventListener('click',h);
    return()=>el?.removeEventListener('click',h);
  },[]);

  useEffect(()=>{
    document.querySelectorAll('#giScale .gi-seg').forEach(seg=>{
      if(hotTiers.has(seg.dataset.tier))seg.classList.remove('dim');
      else seg.classList.add('dim');
    });
  },[hotTiers]);

  // view mode segmented control
  useEffect(()=>{
    const h=e=>{const btn=e.target.closest('.seg-btn');if(btn)t.set({viewMode:btn.dataset.mode});};
    const el=document.getElementById('viewModeSeg');
    el?.addEventListener('click',h);
    return()=>el?.removeEventListener('click',h);
  },[]);
  useEffect(()=>{
    document.querySelectorAll('#viewModeSeg .seg-btn').forEach(b=>b.classList.toggle('active',b.dataset.mode===tv.viewMode));
  },[tv.viewMode]);

  // search
  useEffect(()=>{
    const inp=document.getElementById('searchInput');if(!inp)return;
    const h=()=>{
      const v=inp.value.trim();
      setSearch(v);setPulseTicker(v||null);
      if(v){
        const matches=dataRef.current.filter(r=>r.ticker.toLowerCase().includes(v.toLowerCase())||r.company.toLowerCase().includes(v.toLowerCase()));
        setSelected(new Set(matches.slice(0,10).map(r=>r.ticker)));
      } else setSelected(new Set());
    };
    inp.addEventListener('input',h);
    return()=>inp.removeEventListener('input',h);
  },[]);

  // selection rail
  const selectedRows=useMemo(()=>dataRef.current.filter(r=>selected.has(r.ticker)),[selected,rowsVersion]);
  useEffect(()=>{
    const rail=document.getElementById('bc-rail');
    const inner=document.getElementById('bc-railInner');
    if(!rail||!inner)return;
    const open=selectedRows.length>0||pinned.size>0;
    rail.classList.toggle('open',open);
    if(!open){inner.innerHTML='';return;}
    const displayRows=selectedRows.length>0?selectedRows:dataRef.current.filter(r=>pinned.has(r.ticker));
    const avgGi=displayRows.reduce((s,r)=>s+r.gi_score,0)/displayRows.length;
    const totalV=displayRows.reduce((s,r)=>s+r.total_value,0);
    const insCount=displayRows.filter(r=>r.insider_buys_distinct>0).length;
    const rowsHtml=(rows,title)=>`
      <div class="rail-section-title">${title}</div>
      <div class="rail-list">
        ${rows.map(r=>`
          <div class="rail-row" data-tk="${r.ticker}">
            <span class="dot" style="background:${TIER_COLOR[r.gi_tier]}"></span>
            <span><div class="tk">${r.ticker}</div><div class="co">${r.company}</div></span>
            <span class="gi" style="color:${TIER_COLOR[r.gi_tier]}">${r.gi_score.toFixed(0)}</span>
            <button class="star ${pinned.has(r.ticker)?'on':''}" data-pin="${r.ticker}">${pinned.has(r.ticker)?'★':'☆'}</button>
          </div>`).join('')}
      </div>`;
    const pinnedRows=dataRef.current.filter(r=>pinned.has(r.ticker));
    const showSel=selectedRows.length>0;
    const showPin=pinned.size>0&&!selectedRows.some(r=>pinned.has(r.ticker));
    inner.innerHTML=`
      <div class="rail-head">
        <h3>${showSel?`Selection (${selectedRows.length})`:'Pinned'}</h3>
        <button class="close" id="bcRailClose">×</button>
      </div>
      <div class="rail-stats">
        <div class="rail-stat"><div class="rail-stat-lbl">Avg GI</div><div class="rail-stat-val" style="color:${window.giColor(avgGi)}">${avgGi.toFixed(1)}</div></div>
        <div class="rail-stat"><div class="rail-stat-lbl">Tickers</div><div class="rail-stat-val">${displayRows.length}</div></div>
        <div class="rail-stat"><div class="rail-stat-lbl">Total Held</div><div class="rail-stat-val" style="color:#86efac">${window.fmtMoney(totalV)}</div></div>
        <div class="rail-stat"><div class="rail-stat-lbl">Insiders</div><div class="rail-stat-val">${insCount}/${displayRows.length}</div></div>
      </div>
      ${showSel?rowsHtml(selectedRows.slice(0,60),`${selectedRows.length} selected`):''}
      ${showPin?rowsHtml(pinnedRows,`${pinnedRows.length} pinned`):''}
    `;
    document.getElementById('bcRailClose').onclick=()=>setSelected(new Set());
    inner.querySelectorAll('[data-pin]').forEach(btn=>{
      btn.onclick=e=>{
        e.stopPropagation();
        const tk=btn.dataset.pin;
        setPinned(prev=>{const n=new Set(prev);if(n.has(tk))n.delete(tk);else n.add(tk);return n;});
      };
    });
    inner.querySelectorAll('.rail-row').forEach(row=>{
      row.onclick=()=>setSelected(new Set([row.dataset.tk]));
    });
  },[selectedRows,pinned]);

  // tooltip
  useEffect(()=>{
    const tip=document.getElementById('bc-tip');if(!tip)return;
    if(!hoverPt){tip.classList.remove('show');return;}
    const p=hoverPt, row=p.row;
    const tierCol=TIER_COLOR[p.giTier];
    const sectorCol=(window.SECTOR_COLORS[p.sector]||'#888');
    const arch=ARCHETYPE[row.archetype]||ARCHETYPE.neutral;
    tip.innerHTML=`
      <div class="tip-head">
        <span class="tip-tk" style="color:${tierCol}">${p.ticker}</span>
        <span class="tip-co" title="${p.company}">${p.company}</span>
        <span class="tip-sector" style="color:${sectorCol}">${p.sector||'—'}</span>
      </div>
      <div class="tip-body">
        <div class="tip-row"><span class="lbl">GI Score</span><span class="val" style="color:${tierCol}">${p.giScore.toFixed(1)}</span></div>
        <div class="tip-row"><span class="lbl">Managers</span><span class="val">${row.manager_count}</span></div>
        <div class="tip-row"><span class="lbl">Held</span><span class="val" style="color:#86efac">${window.fmtMoney(row.total_value)}</span></div>
        <div class="tip-row"><span class="lbl">New positions</span><span class="val">${row.new_count} · ${window.fmtMoney(row.new_value)}</span></div>
        ${row.insider_buys_distinct>0?`<div class="tip-row"><span class="lbl">Insider buys</span><span class="val" style="color:#fbbf24">${row.insider_buys_distinct} · ${window.fmtMoney(row.insider_buys_value)}</span></div>`:''}
        <div class="tip-arch"><span class="arch-icon">${arch.icon}</span>${arch.text}</div>
      </div>
      <div class="tip-hint">click to select · ★ to pin · shift-drag to pan</div>
    `;
    tip.classList.add('show');
    const w=tip.offsetWidth||270, h=tip.offsetHeight||220;
    let left=hoverPos.x+18, top=hoverPos.y-h/2;
    if(left+w>window.innerWidth-12)left=hoverPos.x-w-18;
    top=Math.max(12,Math.min(top,window.innerHeight-h-12));
    tip.style.left=left+'px'; tip.style.top=top+'px';
  },[hoverPt,hoverPos]);

  // chip popovers
  const openPop=id=>{
    const el=chipRefs.current[id];if(!el)return;
    const r=el.getBoundingClientRect();
    setPopPos({x:r.left,y:r.bottom+6});setOpenChip(id);
  };
  const closePop=()=>setOpenChip(null);
  useEffect(()=>{
    if(!openChip)return;
    const h=e=>{if(!e.target.closest('.pop')&&!e.target.closest('[data-chip]'))closePop();};
    document.addEventListener('mousedown',h);
    return()=>document.removeEventListener('mousedown',h);
  },[openChip]);

  const AXIS_OPTS=Object.entries(AXES).map(([k,a])=>({value:k,label:a.label,sub:a.short}));
  const SECTOR_OPTS=[{value:'all',label:'All sectors'},...Object.keys(window.SECTOR_COLORS).map(s=>({value:s,label:s}))];
  const TIERS=[
    {k:'dark-green',label:'Strong Accum',color:TIER_COLOR['dark-green']},
    {k:'green',label:'Accumulation',color:TIER_COLOR['green']},
    {k:'yellow',label:'Neutral',color:TIER_COLOR['yellow']},
    {k:'orange',label:'Distribution',color:TIER_COLOR['orange']},
    {k:'red',label:'Heavy Dist',color:TIER_COLOR['red']},
  ];

  const chipDefs=[
    {id:'xAxis',label:'X',val:AXES[tv.xAxis].short,active:true,render:()=>(
      <div><div className="pop-title">X Axis</div>
        {AXIS_OPTS.map(o=><div key={o.value} className={'pop-item'+(tv.xAxis===o.value?' on':'')}
          onClick={()=>{t.set({xAxis:o.value});closePop();}}>
          <span className="check">✓</span><span>{o.label}</span><span className="sub">{o.sub}</span>
        </div>)}
      </div>
    )},
    {id:'yAxis',label:'Y',val:AXES[tv.yAxis].short,active:true,render:()=>(
      <div><div className="pop-title">Y Axis</div>
        {AXIS_OPTS.map(o=><div key={o.value} className={'pop-item'+(tv.yAxis===o.value?' on':'')}
          onClick={()=>{t.set({yAxis:o.value});closePop();}}>
          <span className="check">✓</span><span>{o.label}</span><span className="sub">{o.sub}</span>
        </div>)}
      </div>
    )},
    {id:'sizeAxis',label:'Size',val:AXES[tv.sizeAxis].short,active:true,render:()=>(
      <div><div className="pop-title">Bubble Size</div>
        {AXIS_OPTS.map(o=><div key={o.value} className={'pop-item'+(tv.sizeAxis===o.value?' on':'')}
          onClick={()=>{t.set({sizeAxis:o.value});closePop();}}>
          <span className="check">✓</span><span>{o.label}</span><span className="sub">{o.sub}</span>
        </div>)}
      </div>
    )},
    {id:'minMgrs',label:'Min Mgrs',val:tv.minManagers,active:tv.minManagers>1,render:()=>(
      <div><div className="pop-title">Min Managers Holding</div>
        <div className="pop-row">
          <input type="range" min="1" max="80" step="1" value={tv.minManagers} onChange={e=>t.set({minManagers:+e.target.value})}/>
          <div className="val">{tv.minManagers}</div>
        </div>
        <div className="pop-sep"></div>
        <button className="pop-btn" onClick={()=>t.set({minManagers:1})}>Reset</button>
      </div>
    )},
    {id:'minGi',label:'Min GI',val:tv.minGi,active:tv.minGi>0,render:()=>(
      <div><div className="pop-title">Min GI Score</div>
        <div className="pop-row">
          <input type="range" min="0" max="100" step="5" value={tv.minGi} onChange={e=>t.set({minGi:+e.target.value})}/>
          <div className="val">{tv.minGi}</div>
        </div>
        <div className="pop-sep"></div>
        <button className="pop-btn" onClick={()=>t.set({minGi:0})}>Reset</button>
      </div>
    )},
    {id:'sector',label:'Sector',val:tv.sector==='all'?'All':tv.sector,active:tv.sector!=='all',render:()=>(
      <div style={{maxHeight:280,overflowY:'auto'}}>
        <div className="pop-title">Sector</div>
        {SECTOR_OPTS.map(o=><div key={o.value} className={'pop-item'+(tv.sector===o.value?' on':'')}
          onClick={()=>{t.set({sector:o.value});closePop();}}>
          <span className="check">✓</span>
          {o.value!=='all'&&<span style={{width:8,height:8,borderRadius:'50%',background:window.SECTOR_COLORS[o.value],display:'inline-block'}}></span>}
          <span>{o.label}</span>
        </div>)}
      </div>
    )},
    {id:'tiers',label:'GI Tiers',val:hotTiers.size===5?'All':`${hotTiers.size}/5`,active:hotTiers.size<5,render:()=>(
      <div><div className="pop-title">GI Tiers</div>
        {TIERS.map(ti=>{
          const on=hotTiers.has(ti.k);
          return(<div key={ti.k} className={'pop-toggle'+(on?' on':'')}
            onClick={()=>setHotTiers(prev=>{const n=new Set(prev);if(n.has(ti.k))n.delete(ti.k);else n.add(ti.k);return n.size===0?new Set(['dark-green','green','yellow','orange','red']):n;})}>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <span style={{width:10,height:10,borderRadius:'50%',background:ti.color,display:'inline-block'}}></span>
              <span className="label">{ti.label}</span>
            </div>
            <div className="pop-sw"></div>
          </div>);
        })}
        <div className="pop-sep"></div>
        <button className="pop-btn" onClick={()=>setHotTiers(new Set(['dark-green','green','yellow','orange','red']))}>All tiers</button>
      </div>
    )},
    {id:'insiders',label:'',val:'Insider buys only',active:tv.onlyInsiders,
      direct:()=>t.set({onlyInsiders:!tv.onlyInsiders})},
    {id:'pinnedOnly',label:'',val:`★ Pinned${pinned.size?` (${pinned.size})`:''}`,active:tv.onlyPinned,
      direct:()=>t.set({onlyPinned:!tv.onlyPinned})},
    {id:'display',label:'Display',val:[tv.showQuadrants&&'Q',tv.showLabels&&'Labels'].filter(Boolean).join('+'),active:true,render:()=>(
      <div><div className="pop-title">Display</div>
        <div className={'pop-toggle'+(tv.showQuadrants?' on':'')} onClick={()=>t.set({showQuadrants:!tv.showQuadrants})}>
          <span className="label">Quadrant dividers</span><div className="pop-sw"></div>
        </div>
        <div className={'pop-toggle'+(tv.showLabels?' on':'')} onClick={()=>t.set({showLabels:!tv.showLabels})}>
          <span className="label">Smart ticker labels</span><div className="pop-sw"></div>
        </div>
        <div className="pop-row">
          <label>Density</label>
          <input type="range" min="4" max="40" step="1" value={tv.labelDensity} onChange={e=>t.set({labelDensity:+e.target.value})}/>
          <div className="val">{tv.labelDensity}</div>
        </div>
      </div>
    )},
    {id:'actions',label:'',val:'Actions ▾',active:false,render:()=>(
      <div><div className="pop-title">Actions</div>
        <button className="pop-btn" style={{marginBottom:4}} onClick={()=>{setView({xMin:null,xMax:null,yMin:null,yMax:null});closePop();}}>
          Reset zoom{view.xMin!=null?' •':''}
        </button>
        <button className="pop-btn" style={{marginBottom:4}} onClick={()=>{setSelected(new Set());closePop();}}>
          Clear selection{selected.size?` (${selected.size})`:''}
        </button>
        <button className="pop-btn" style={{marginBottom:4}} onClick={()=>{setPinned(new Set());closePop();}}>
          Clear pins{pinned.size?` (${pinned.size})`:''}
        </button>
        <div className="pop-sep"></div>
        <button className="pop-btn danger" onClick={()=>{
          t.set({minManagers:1,minGi:0,sector:'all',onlyInsiders:false,onlyPinned:false});
          setHotTiers(new Set(['dark-green','green','yellow','orange','red']));
          setSearch('');setPulseTicker(null);
          const inp=document.getElementById('searchInput');if(inp)inp.value='';
          closePop();
        }}>Reset all filters</button>
      </div>
    )},
  ];

  const chipsHost=document.getElementById('chipsWrap');
  const activeDef=chipDefs.find(c=>c.id===openChip);

  return (<>
    {axisMenu&&ReactDOM.createPortal(
      <div className="bc-menu" style={{left:axisMenu.x,top:axisMenu.y}} onClick={e=>e.stopPropagation()}>
        <div className="bc-menu-title">{axisMenu.kind==='x'?'X Axis':axisMenu.kind==='y'?'Y Axis':'Bubble Size'}</div>
        {Object.entries(AXES).map(([k,a])=>{
          const cur=axisMenu.kind==='x'?tv.xAxis:axisMenu.kind==='y'?tv.yAxis:tv.sizeAxis;
          return(<div key={k} className={'bc-menu-item'+(cur===k?' on':'')} onClick={()=>{
            if(axisMenu.kind==='x')t.set({xAxis:k});
            if(axisMenu.kind==='y')t.set({yAxis:k});
            if(axisMenu.kind==='s')t.set({sizeAxis:k});
            setAxisMenu(null);
          }}><span className="check">✓</span><span>{a.label}</span><span className="sub">{a.short}</span></div>);
        })}
      </div>, document.body
    )}

    <canvas ref={canvasRef} id="bcChartCanvas"
      onMouseMove={onMouseMove} onMouseLeave={onMouseLeave}
      onMouseDown={onMouseDown} onMouseUp={onMouseUp}
      onDoubleClick={onDoubleClick} onWheel={onWheel}
      style={{display:'block'}}
    />

    {chipsHost&&ReactDOM.createPortal(
      <>
        {chipDefs.map(c=>(
          <div key={c.id} ref={el=>chipRefs.current[c.id]=el} data-chip={c.id}
            className={'chip control'+(c.active?' active':'')+(c.id==='actions'?' action':'')}
            onClick={()=>{if(c.direct){c.direct();return;}if(openChip===c.id)closePop();else openPop(c.id);}}>
            {c.label&&<span className="chip-label">{c.label}</span>}
            <span className="chip-val">{c.val}</span>
            {c.render&&<span className="chip-caret">▾</span>}
          </div>
        ))}
      </>, chipsHost
    )}

    {activeDef&&activeDef.render&&ReactDOM.createPortal(
      <div className="pop" style={{left:popPos.x,top:popPos.y}} onClick={e=>e.stopPropagation()}>
        {activeDef.render()}
      </div>, document.body
    )}
  </>);
}
// Mount is controlled by mountBubbleChartV2() called from switchTab
window.BubbleChartApp = BubbleChartApp;
})();
</script>

</body>
</html>"""


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
