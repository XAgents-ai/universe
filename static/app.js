'use strict';
const spec = {S:['#667a8a','structural'], C:['#3181b8','conductor'], G:['#835eab','gate'], A:['#ce713a','mover'], W:['#b48f28','welder'], B:['#2f956e','store'], P:['#b95684','sensor'], K:['#b64c4c','control'], R:['#6e85aa','rotator']};
const arrow = {N:'↑', E:'→', S:'↓', W:'←'};
const $ = id => document.getElementById(id);
const svgNS = 'http://www.w3.org/2000/svg';
function restoredToken(){try{return sessionStorage.getItem('universe-v03-participant-token')}catch{return null}}
let role='audit', sid=null, current=null, liveToken=restoredToken(), sawLiveObserver=false;
function node(name,attrs={},text=null){const e=document.createElementNS(svgNS,name);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text!==null)e.textContent=text;return e;}
async function req(url,opts={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opts});let d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||r.statusText);return d;}
function showError(e){$('eventLog').textContent='ERROR: '+(e?.message||String(e));}
function addLegend(){const l=$('speciesLegend');for(const [s,[color,desc]] of Object.entries(spec)){const span=document.createElement('span');span.className='legendTag';span.title=desc;const b=document.createElement('b');b.style.background=color;b.textContent=s;span.append(b,document.createTextNode(' '+s));l.append(span);}}
function draw(frame, fog=false, observations=[]){const svg=$('universe');svg.replaceChildren();let w=frame.width,h=frame.height,cell=42,pad=30;
  svg.setAttribute('viewBox',`0 0 ${w*cell+pad*2} ${h*cell+pad*2}`);
  svg.append(node('rect',{x:pad,y:pad,width:w*cell,height:h*cell,rx:5,fill:'#fcfdfd',stroke:'#d9e1e6','stroke-width':1}));
  for(let x=0;x<=w;x++)svg.append(node('line',{x1:pad+x*cell,y1:pad,x2:pad+x*cell,y2:pad+h*cell,stroke:'#e9eff2'}));
  for(let y=0;y<=h;y++)svg.append(node('line',{x1:pad,y1:pad+y*cell,x2:pad+w*cell,y2:pad+y*cell,stroke:'#e9eff2'}));
  for(let x=0;x<w;x++)svg.append(node('text',{x:pad+(x+.5)*cell,y:pad-10,'text-anchor':'middle',fill:'#a0adb8','font-size':11},String(x)));
  for(let y=0;y<h;y++)svg.append(node('text',{x:pad-13,y:pad+(y+.55)*cell,'text-anchor':'middle',fill:'#a0adb8','font-size':11},String(y)));
  if(fog){
    svg.append(node('rect',{x:pad,y:pad,width:w*cell,height:h*cell,fill:'#e3e9ee','fill-opacity':'.78'}));
    for(const o of observations){for(let x=Math.max(0,o.site[0]-o.radius);x<=Math.min(w-1,o.site[0]+o.radius);x++)for(let y=Math.max(0,o.site[1]-o.radius);y<=Math.min(h-1,o.site[1]+o.radius);y++){
      svg.append(node('rect',{x:pad+x*cell+1,y:pad+y*cell+1,width:cell-2,height:cell-2,fill:'#f8fbfc'}));}}
    // Earlier observations are frozen measurements, not a promise of current physical state.
  }
  if(!fog && $('heatToggle').checked)for(const p of frame.heat||[]){const strength=Math.min(.72,.09+p.quanta*.09);svg.append(node('rect',{x:pad+p.x*cell+1,y:pad+p.y*cell+1,width:cell-2,height:cell-2,fill:`rgba(240,115,46,${strength})`,rx:2}));if(p.quanta)svg.append(node('text',{x:pad+(p.x+.88)*cell,y:pad+(p.y+.23)*cell,'text-anchor':'end','font-size':9,fill:'#7a431b'},p.quanta));}
  if(!fog)for(const s of frame.sources||[]){let x=pad+(s.x+.5)*cell,y=pad+(s.y+.5)*cell;svg.append(node('circle',{cx:x,cy:y,r:cell*.36,fill:'#fff3d8',stroke:'#e4be71','stroke-width':1.4}));svg.append(node('text',{x,y:y+4,'text-anchor':'middle','font-size':13,fill:'#855d25'},'☼'));svg.append(node('text',{x:x+cell*.29,y:y-cell*.28,'text-anchor':'middle','font-size':10,fill:'#855d25'},arrow[s.direction]));}
  if(!fog && $('bondsToggle').checked)for(const [a,b] of frame.bonds||[])svg.append(node('line',{x1:pad+(a[0]+.5)*cell,y1:pad+(a[1]+.5)*cell,x2:pad+(b[0]+.5)*cell,y2:pad+(b[1]+.5)*cell,stroke:'#151e27','stroke-width':11,'stroke-opacity':'.55','stroke-linecap':'round'}));
  let particles = fog ? observations.flatMap(o=>o.particles) : frame.particles||[];
  let byPos=new Map();for(const p of particles)byPos.set(`${p.x},${p.y}`,p);
  for(const p of byPos.values()){
    const x=pad+p.x*cell+3,y=pad+p.y*cell+3,co=spec[p.species]?.[0]||'#666';
    svg.append(node('rect',{x,y,width:cell-6,height:cell-6,rx:6,fill:co,stroke:'#fff','stroke-width':1.6}));
    svg.append(node('text',{x:x+13,y:y+23,'text-anchor':'middle',fill:'#fff','font-size':16,'font-weight':750},p.species));
    svg.append(node('text',{x:x+cell-17,y:y+13,'text-anchor':'middle',fill:'#fff','font-size':12},arrow[p.direction]||'·'));
    if($('quantaToggle').checked){const q=p.charge||0,exc=p.excitation||0;if(q||exc)svg.append(node('text',{x:x+cell-15,y:y+cell-10,'text-anchor':'end','font-size':10,fill:'#fff','font-weight':'bold'}, q?`q${q}`:`x${exc}`));}
    if(!fog && p.control)svg.append(node('circle',{cx:x+5,cy:y+5,r:3,fill:'#fff4a4'}));
  }
  svg.onclick=e=>{const rect=svg.getBoundingClientRect();const vb=svg.viewBox.baseVal;const sx=(e.clientX-rect.left)*vb.width/rect.width,sy=(e.clientY-rect.top)*vb.height/rect.height;const x=Math.floor((sx-pad)/cell),y=Math.floor((sy-pad)/cell);if(x>=0&&x<w&&y>=0&&y<h&&!['audit','livewatch'].includes(role)){$('x').value=x;$('y').value=y;}};
}
function metrics(frame){const el=$('metrics');el.replaceChildren();if(role==='agent'||role==='liveagent'){el.innerHTML='<div class="muted small" style="grid-column:span 2">Not exposed to inhabitants. Energy stored in individual particles appears only in paid local observations.</div>';return;}
  for(const [name,key] of [['Stored','Eq'],['Excitation','Ex'],['Bond energy','Eb'],['Heat','ET'],['Boundary in','Ein'],['Boundary out','Eout'],['Invariant total','total']]){const div=document.createElement('div');div.className='metric'+(key==='total'?' wide':'');const label=document.createElement('span');label.textContent=name;const val=document.createElement('strong');val.textContent=frame.energy[key];div.append(label,val);el.append(div);}}
function render(data){current=data;
 if(role==='audit'){
   const f=data.frame;draw(f);metrics(f);$('tickLabel').textContent='TICK '+f.tick;$('canvasNote').textContent='Full recorded state · '+f.hash+' · immutable audit replay';
   $('eventLog').textContent=f.event?JSON.stringify(f.event,null,2):'Initial snapshot: loose P and A, charged seed manipulators, no claimed construction.';
   $('timeline').max=data.length-1;$('timeline').value=data.cursor;$('frameLabel').textContent=`${data.cursor}/${data.length-1}`;
 }else if(role==='agent'||role==='liveagent'){
   draw({width:data.width,height:data.height},true,data.observed);metrics({});$('tickLabel').textContent=role==='liveagent'?'LIVE ACTOR · LOCAL':'LOCAL OBSERVATION';
   $('canvasNote').textContent='Fog = unobserved · colored cells = last paid observation, possibly stale'+(role==='liveagent'?' · SHARED WORLD':'');
   $('eventLog').textContent=data.actions.length?JSON.stringify(data.actions.slice(-8),null,2):'No control-site operation has been submitted.';
   const sites=$('siteList');sites.replaceChildren();const label=document.createElement('span');label.textContent='Your authorized K sites: ';sites.append(label);
   for(const p of data.authorized){const b=document.createElement('button');b.textContent=p.join(',');b.onclick=()=>{$('x').value=p[0];$('y').value=p[1];};sites.append(b);}
 }else if(role==='livewatch'){
   const f=data.frame;draw(f);metrics(f);$('tickLabel').textContent='LIVE TICK '+f.tick;
   $('canvasNote').textContent='Read-only live global state · '+f.hash+' · humans and AI inhabit the same world';
   $('eventLog').textContent=data.event?JSON.stringify(data.event,null,2):'No registered participant operations yet.';
 }else{
   const f=data.frame;draw(f);metrics(f);$('tickLabel').textContent='CLONE TICK '+f.tick;$('canvasNote').textContent='Research clone · environmental interventions logged · '+f.hash;
   $('eventLog').textContent=data.events.length?JSON.stringify(data.events.slice(-3),null,2):'No boundary interventions submitted in this clone.';
 }
}
async function switchMode(next){role=next;document.querySelectorAll('.modes button').forEach(b=>b.classList.toggle('active',b.dataset.role===role));
 $('refreshBtn').hidden=!['livewatch','liveagent'].includes(role); $('timelinePanel').hidden=role!=='audit';$('controls').hidden=['audit','livewatch'].includes(role);$('envFields').hidden=role!=='experiment';$('siteList').hidden=!['agent','liveagent'].includes(role);$('heatToggle').disabled=['agent','liveagent'].includes(role);$('bondsToggle').disabled=['agent','liveagent'].includes(role);
 $('metricsTitle').textContent=['agent','liveagent'].includes(role)?'LOCAL ENERGY VISIBILITY':'ENERGY LEDGER';$('logTitle').textContent=['agent','liveagent'].includes(role)?'YOUR ACTION OUTCOMES':'RECORDED EVENT';
 const config={audit:['Recorded physical state','Read-only: raw P/A → bonded responder → stimulus without controller','No physical operations permitted in audit replay.'],livewatch:['Persistent live universe · observer','Read-only global audit view; no ability to change the world.','This is an audit instrument. Prior access to live global information should be disclosed in controlled trials.'],liveagent:['Shared world · human participant','Same physical interface as API-connected model and program controllers.','Join once, then use charged control-site actions. Observations are local and may become stale.'],agent:['Solo research sandbox','Only paid observations and charged control-site operations. No boundary access.','Select an authorized K site. Observe costs energy; set and claim are charged. Wait advances the world.'],experiment:['Experimenter · isolated clone','Full physical inspection; boundary interventions are recorded and counted.','Apply logged drop/remove/replace or wait. No charged agent control here.']}[role];
 $('viewTitle').textContent=config[0];$('viewDesc').textContent=config[1];$('actionInfo').textContent=config[2];$('actionButtons').replaceChildren();
 const ops=['agent','liveagent'].includes(role)?['observe','set','claim','wait']:role==='experiment'?['drop','remove','replace','wait']:[];
 for(const op of ops){const b=document.createElement('button');b.textContent=op==='wait'?'Advance 1 tick':op.toUpperCase();if(op==='wait')b.className='secondary';b.onclick=()=>act(op);$('actionButtons').append(b);}
 try{
    if(role==='livewatch'){sawLiveObserver=true;sid=null;render(await req('/api/live/observer'));return;}
    if(role==='liveagent'){
      sid=null;
      if(!liveToken){const d=await req('/api/live/join',{method:'POST',body:JSON.stringify({controller:'human',global_exposure_declared:sawLiveObserver})});liveToken=d.token;try{sessionStorage.setItem('universe-v03-participant-token',liveToken)}catch{}render(d);}
      else render(await req('/api/live/actor',{headers:{Authorization:'Bearer '+liveToken}}));
      return;
    }
    const d=await req('/api/session',{method:'POST',body:JSON.stringify({role})});sid=d.session;render(d);
  }catch(e){showError(e);}
}
async function act(kind){if(!sid && role!=='liveagent')return;const payload={kind,x:Number($('x').value),y:Number($('y').value),species:$('species').value,direction:$('direction').value};
 try{
    if(role==='liveagent')render(await req('/api/live/act',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+liveToken},body:JSON.stringify(payload)}));
    else render(await req(`/api/session/${sid}/act`,{method:'POST',body:JSON.stringify(payload)}));
  }catch(e){showError(e);}}
async function seek(index){if(!sid)return;try{render(await req(`/api/session/${sid}/frame/${index}`,{method:'POST'}));}catch(e){showError(e);}}
async function exportVisible(){if(!sid&&!['livewatch','liveagent'].includes(role))return;try{const d=role==='livewatch'?await req('/api/live/events'):role==='liveagent'?await req('/api/live/actor',{headers:{Authorization:'Bearer '+liveToken}}):await req(`/api/session/${sid}/export`);const blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`universe-r03-${role}-record.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}catch(e){showError(e);}}
for(const s of Object.keys(spec)){const o=document.createElement('option');o.textContent=s;$('species').append(o);}
addLegend();document.querySelectorAll('.modes button').forEach(b=>b.onclick=()=>switchMode(b.dataset.role));$('prevBtn').onclick=()=>seek(Math.max(0,current.cursor-1));$('nextBtn').onclick=()=>seek(Math.min(current.length-1,current.cursor+1));$('timeline').oninput=e=>seek(Number(e.target.value));$('exportBtn').onclick=exportVisible; $('refreshBtn').onclick=async()=>{try{if(role==='livewatch')render(await req('/api/live/observer'));else if(role==='liveagent'&&liveToken)render(await req('/api/live/actor',{headers:{Authorization:'Bearer '+liveToken}}));}catch(e){showError(e);}};
for(const id of ['heatToggle','bondsToggle','quantaToggle'])$(id).onchange=()=>current&&render(current);
switchMode('audit');
