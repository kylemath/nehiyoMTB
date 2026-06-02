import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

/* =====================================================================
   Icon Extruder
   PNG/SVG  ->  posterize to K tones  ->  connected-region segments
   ->  assign filament colour + layer height per region  ->  extruded
   manifold STL (heightmap-of-columns mesher).
   ===================================================================== */

const $ = id => document.getElementById(id);
const statusEl = $('status');
function status(m){ statusEl.textContent = m; }

/* ---------------- state ---------------- */
const S = {
  srcCanvas: document.createElement('canvas'),
  W:0, H:0,            // working grid size
  level: null,         // Uint8Array length W*H, 0..K-1 (0 = lightest)
  label: null,         // Int32Array, segment id per cell, -1 = void
  segs: [],            // [{id, level, color, name, heightMm, px, sample}]
  K:3,
  palette: [
    {color:'#1a1a1a', name:'Black'},
    {color:'#ffffff', name:'White'},
    {color:'#c0392b', name:'Red'},
    {color:'#e0b04a', name:'Yellow'},
    {color:'#2c6fb0', name:'Blue'},
    {color:'#3a8a3a', name:'Green'},
    {color:'#888888', name:'Grey'}
  ],
  selSwatch:0,
  selSeg:-1
};

/* ---------------- image loading ---------------- */
function drawSourceFromImage(img, w, h){
  const c = S.srcCanvas;
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#fff'; ctx.fillRect(0,0,w,h);
  ctx.drawImage(img, 0,0, w,h);
  const sc = $('srcCanvas');
  sc.style.display='block'; sc.width=w; sc.height=h;
  sc.getContext('2d').drawImage(c,0,0);
  status('Image loaded ('+w+'×'+h+'). Adjust tones, then press “Process”.');
}

function loadImageElement(srcUrl){
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = ()=>{
    const maxIn = 700;
    let w=img.naturalWidth||img.width, h=img.naturalHeight||img.height;
    const s = Math.min(1, maxIn/Math.max(w,h));
    drawSourceFromImage(img, Math.max(1,Math.round(w*s)), Math.max(1,Math.round(h*s)));
  };
  img.onerror = ()=>status('Could not load image (CORS or bad URL). Try downloading then uploading the file.');
  img.src = srcUrl;
}

function loadFile(file){
  if(!file) return;
  if(file.type==='image/svg+xml' || /\.svg$/i.test(file.name)){
    const r=new FileReader();
    r.onload=()=>{ const blob=new Blob([r.result],{type:'image/svg+xml'}); loadImageElement(URL.createObjectURL(blob)); };
    r.readAsText(file);
  } else {
    loadImageElement(URL.createObjectURL(file));
  }
}

$('fileInput').addEventListener('change', e=>loadFile(e.target.files[0]));
$('loadUrl').addEventListener('click', ()=>{ const u=$('urlInput').value.trim(); if(u) loadImageElement(u); });
window.addEventListener('paste', e=>{
  for(const it of (e.clipboardData?.items||[])){ if(it.type.startsWith('image/')){ loadFile(it.getAsFile()); } }
});

/* ---------------- sliders ---------------- */
function bindRange(id, valId, fn){ const r=$(id); const v=$(valId);
  const upd=()=>{ if(v) v.textContent=r.value; if(fn) fn(); };
  r.addEventListener('input',upd); upd();
}
bindRange('kRange','kVal');
bindRange('resRange','resVal');
bindRange('minRange','minVal');
bindRange('wRange','wVal', ()=>{ if(S.W) buildAndShow(); });

/* ---------------- processing ---------------- */
function lum(r,g,b){ return 0.299*r+0.587*g+0.114*b; }

function process(){
  if(!S.srcCanvas.width){ status('Load an image first.'); return; }
  const K = S.K = parseInt($('kRange').value,10);
  const maxRes = parseInt($('resRange').value,10);
  const invert = $('invert').checked;
  const voidBg = $('voidBg').checked;
  const minPx = parseInt($('minRange').value,10);

  // resample to working grid
  const sw=S.srcCanvas.width, sh=S.srcCanvas.height;
  const s = Math.min(1, maxRes/Math.max(sw,sh));
  const W = S.W = Math.max(2, Math.round(sw*s));
  const H = S.H = Math.max(2, Math.round(sh*s));
  const tmp = document.createElement('canvas'); tmp.width=W; tmp.height=H;
  const tctx = tmp.getContext('2d');
  tctx.fillStyle='#fff'; tctx.fillRect(0,0,W,H);
  tctx.drawImage(S.srcCanvas, 0,0, W,H);
  const img = tctx.getImageData(0,0,W,H).data;
  S.rgb = img;

  // posterize to levels (0 = lightest -> background candidate, K-1 = darkest)
  const level = S.level = new Uint8Array(W*H);
  for(let i=0;i<W*H;i++){
    let L = lum(img[i*4],img[i*4+1],img[i*4+2]);
    if(invert) L = 255-L;
    let lightBin = Math.min(K-1, Math.floor(L*K/256));   // 0 dark .. K-1 light
    level[i] = (K-1) - lightBin;                          // 0 light .. K-1 dark
  }

  labelSegments(voidBg);
  if(minPx>0) despeckle(minPx, voidBg);
  finalizeSegments(voidBg);
  applyDefaultHeights();
  renderPalette(); renderSegList(); drawSegCanvas(); buildAndShow();
  status(S.segs.length+' regions found. Click a region to assign a filament & height.');
}

function labelSegments(voidBg){
  const {W,H,level} = S;
  const label = S.label = new Int32Array(W*H).fill(-1);
  let next=0;
  const stack=[];
  for(let start=0;start<W*H;start++){
    if(label[start]!==-1) continue;
    const lv = level[start];
    if(voidBg && lv===0){ label[start]=-1; continue; } // background void
    const id=next++;
    stack.length=0; stack.push(start); label[start]=id;
    while(stack.length){
      const p=stack.pop(); const x=p%W, y=(p/W)|0;
      const nb=[];
      if(x>0)nb.push(p-1); if(x<W-1)nb.push(p+1);
      if(y>0)nb.push(p-W); if(y<H-1)nb.push(p+W);
      for(const q of nb){ if(label[q]===-1 && level[q]===lv && !(voidBg&&level[q]===0)){ label[q]=id; stack.push(q);} }
    }
  }
  S.nLabels=next;
}

function despeckle(minPx, voidBg){
  const {W,H,label,level} = S;
  // count pixels per label
  const counts={};
  for(let i=0;i<W*H;i++){ const l=label[i]; if(l>=0) counts[l]=(counts[l]||0)+1; }
  // for each small label, reassign cells' level to dominant neighbour level (or background)
  let changed=false;
  for(let i=0;i<W*H;i++){
    const l=label[i]; if(l<0) continue;
    if(counts[l]>=minPx) continue;
    const x=i%W, y=(i/W)|0; const tally={};
    const nb=[];
    if(x>0)nb.push(i-1); if(x<W-1)nb.push(i+1); if(y>0)nb.push(i-W); if(y<H-1)nb.push(i+W);
    for(const q of nb){ const lq=label[q]; if(lq>=0 && lq!==l && counts[lq]>=minPx){ tally[level[q]]=(tally[level[q]]||0)+1; } }
    let best=-1,bc=0; for(const lev in tally){ if(tally[lev]>bc){bc=tally[lev];best=+lev;} }
    if(best>=0){ level[i]=best; } else if(voidBg){ level[i]=0; }
    changed=true;
  }
  if(changed) labelSegments(voidBg);
}

function nearestPalette(r,g,b){
  let bi=0,bd=1e9;
  S.palette.forEach((p,idx)=>{
    const c=hex2rgb(p.color); const d=(c[0]-r)**2+(c[1]-g)**2+(c[2]-b)**2;
    if(d<bd){bd=d;bi=idx;}
  });
  return bi;
}

function finalizeSegments(voidBg){
  const {W,H,label,level,rgb} = S;
  const acc={};
  for(let i=0;i<W*H;i++){ const l=label[i]; if(l<0)continue;
    const a=acc[l]||(acc[l]={px:0,r:0,g:0,b:0,lev:level[i]});
    a.px++; a.r+=rgb[i*4]; a.g+=rgb[i*4+1]; a.b+=rgb[i*4+2];
  }
  // remap labels to compact ids and build segments
  const ids=Object.keys(acc).map(Number).sort((p,q)=>acc[p].lev-acc[q].lev || acc[q].px-acc[p].px);
  const remap={}; const segs=[];
  ids.forEach((old,ni)=>{
    const a=acc[old]; remap[old]=ni;
    const r=Math.round(a.r/a.px),g=Math.round(a.g/a.px),b=Math.round(a.b/a.px);
    const pal=nearestPalette(r,g,b);
    segs.push({id:ni, level:a.lev, px:a.px, sample:[r,g,b],
               color:S.palette[pal].color, name:S.palette[pal].name, heightMm:0});
  });
  for(let i=0;i<W*H;i++){ if(label[i]>=0) label[i]=remap[label[i]]; }
  S.segs=segs;
}

function applyDefaultHeights(){
  const base=parseFloat($('baseH').value)||0, step=parseFloat($('stepH').value)||0.6;
  S.segs.forEach(s=>{ s.heightMm = +(base + s.level*step).toFixed(3); });
}
$('reheightBtn').addEventListener('click',()=>{ if(S.segs.length){ applyDefaultHeights(); renderSegList(); buildAndShow(); }});
$('processBtn').addEventListener('click', process);

/* ---------------- palette UI ---------------- */
function hex2rgb(h){ h=h.replace('#',''); return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]; }

function renderPalette(){
  const wrap=$('swatches'); wrap.innerHTML='';
  S.palette.forEach((p,idx)=>{
    const d=document.createElement('div'); d.className='sw'+(idx===S.selSwatch?' sel':'');
    d.style.background=p.color; d.title=p.name;
    d.innerHTML='<span class="x">×</span>';
    d.addEventListener('click',e=>{
      if(e.target.classList.contains('x')){ S.palette.splice(idx,1); if(S.selSwatch>=S.palette.length)S.selSwatch=0; renderPalette(); return; }
      S.selSwatch=idx; renderPalette();
    });
    wrap.appendChild(d);
  });
}
$('addSw').addEventListener('click',()=>{
  S.palette.push({color:$('newColor').value, name:$('newName').value.trim()||$('newColor').value});
  $('newName').value=''; renderPalette();
});

/* ---------------- region list UI ---------------- */
function renderSegList(){
  const wrap=$('segList');
  if(!S.segs.length){ wrap.innerHTML='<div class="hint">No regions yet.</div>'; return; }
  wrap.innerHTML='';
  S.segs.forEach(s=>{
    const row=document.createElement('div'); row.className='segrow'+(s.id===S.selSeg?' sel':'');
    row.innerHTML=`<span class="chip" style="background:${s.color}"></span>
      <span class="lbl">tone ${s.level} · <span class="px">${s.px}px</span></span>
      <input type="number" step="0.1" min="0" value="${s.heightMm}" title="height (mm)">`;
    row.querySelector('.lbl').addEventListener('click',()=>{ S.selSeg=s.id; renderSegList(); drawSegCanvas(); highlight3D(); });
    row.querySelector('.chip').addEventListener('click',()=>{ s.color=S.palette[S.selSwatch].color; s.name=S.palette[S.selSwatch].name; renderSegList(); drawSegCanvas(); buildAndShow(); });
    row.querySelector('input').addEventListener('change',e=>{ s.heightMm=parseFloat(e.target.value)||0; buildAndShow(); });
    wrap.appendChild(row);
  });
}

/* ---------------- 2D segment canvas ---------------- */
function drawSegCanvas(){
  const {W,H,label} = S; if(!W) return;
  const cv=$('segCanvas');
  const disp=Math.max(1, Math.floor(420/Math.max(W,H)));
  cv.width=W*disp; cv.height=H*disp;
  const ctx=cv.getContext('2d'); ctx.imageSmoothingEnabled=false;
  const colorOf={}; S.segs.forEach(s=>colorOf[s.id]=s.color);
  // fill cells
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){
    const l=label[y*W+x];
    ctx.fillStyle = l<0 ? '#ffffff' : colorOf[l];
    ctx.fillRect(x*disp,y*disp,disp,disp);
  }
  // region borders
  ctx.fillStyle='rgba(0,0,0,0.55)';
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){
    const l=label[y*W+x];
    if(x<W-1 && label[y*W+x+1]!==l) ctx.fillRect((x+1)*disp-1,y*disp,1,disp);
    if(y<H-1 && label[(y+1)*W+x]!==l) ctx.fillRect(x*disp,(y+1)*disp-1,disp,1);
  }
  // highlight selected
  if(S.selSeg>=0){
    ctx.fillStyle='rgba(163,193,74,0.45)';
    for(let i=0;i<W*H;i++){ if(label[i]===S.selSeg){ const x=i%W,y=(i/W)|0; ctx.fillRect(x*disp,y*disp,disp,disp);} }
  }
  cv._disp=disp;
}
$('segCanvas').addEventListener('click',e=>{
  if(!S.W) return;
  const cv=e.target, r=cv.getBoundingClientRect(), disp=cv._disp;
  const x=Math.floor((e.clientX-r.left)*cv.width/r.width/disp);
  const y=Math.floor((e.clientY-r.top)*cv.height/r.height/disp);
  if(x<0||y<0||x>=S.W||y>=S.H) return;
  const l=S.label[y*S.W+x];
  if(l<0){ status('That is background (void).'); return; }
  S.selSeg=l;
  const seg=S.segs.find(s=>s.id===l);
  // paint with current swatch
  seg.color=S.palette[S.selSwatch].color; seg.name=S.palette[S.selSwatch].name;
  renderSegList(); drawSegCanvas(); buildAndShow();
  status(`Region (tone ${seg.level}, ${seg.px}px) → ${seg.name}, height ${seg.heightMm}mm.`);
});

/* ---------------- mesher (heightmap of columns) ---------------- */
function buildMesh(filterColor){
  const {W,H,label,segs} = S;
  const hOf={}, cOf={}; segs.forEach(s=>{hOf[s.id]=s.heightMm; cOf[s.id]=s.color;});
  const cell = (parseFloat($('wRange').value)||60)/W;
  const active = (x,y)=>{ if(x<0||y<0||x>=W||y>=H) return null; const l=label[y*W+x];
    if(l<0) return null; if(filterColor && cOf[l]!==filterColor) return null; const h=hOf[l]; return h>0?{h,l}:null; };

  const pos=[], col=[];
  const c3=hex => { const [r,g,b]=hex2rgb(hex); return [r/255,g/255,b/255]; };
  function tri(ax,ay,az,bx,by,bz,cx,cy,cz,rgb){ pos.push(ax,ay,az,bx,by,bz,cx,cy,cz); for(let k=0;k<3;k++) col.push(rgb[0],rgb[1],rgb[2]); }
  function quad(a,b,c,d,rgb){ tri(a[0],a[1],a[2],b[0],b[1],b[2],c[0],c[1],c[2],rgb); tri(a[0],a[1],a[2],c[0],c[1],c[2],d[0],d[1],d[2],rgb); }

  for(let y=0;y<H;y++)for(let x=0;x<W;x++){
    const me=active(x,y); if(!me) continue;
    const h=me.h, rgb=c3(cOf[me.l]);
    const X0=x*cell, X1=(x+1)*cell;
    const Y0=(H-y-1)*cell, Y1=(H-y)*cell;
    // top (+z) and bottom (-z)
    quad([X0,Y0,h],[X1,Y0,h],[X1,Y1,h],[X0,Y1,h], rgb);
    quad([X0,Y0,0],[X0,Y1,0],[X1,Y1,0],[X1,Y0,0], rgb);
    // walls where neighbour is lower / void
    const R=active(x+1,y), L=active(x-1,y), D=active(x,y+1), U=active(x,y-1);
    const rh=R?R.h:0, lh=L?L.h:0, dh=D?D.h:0, uh=U?U.h:0;
    if(rh<h) quad([X1,Y0,rh],[X1,Y1,rh],[X1,Y1,h],[X1,Y0,h], rgb);            // +x
    if(lh<h) quad([X0,Y1,lh],[X0,Y0,lh],[X0,Y0,h],[X0,Y1,h], rgb);            // -x
    if(dh<h) quad([X0,Y0,dh],[X1,Y0,dh],[X1,Y0,h],[X0,Y0,h], rgb);            // -y (grid down)
    if(uh<h) quad([X1,Y1,uh],[X0,Y1,uh],[X0,Y1,h],[X1,Y1,h], rgb);            // +y (grid up)
  }
  return {pos:new Float32Array(pos), col:new Float32Array(col), cell, W, H};
}

/* ---------------- three.js preview ---------------- */
let renderer, scene, camera, controls, meshObj, gridObj;
function initThree(){
  const el=$('view'); const w=el.clientWidth||600, h=el.clientHeight||420;
  renderer=new THREE.WebGLRenderer({antialias:true}); renderer.setPixelRatio(devicePixelRatio);
  renderer.setSize(w,h); el.appendChild(renderer.domElement);
  scene=new THREE.Scene(); scene.background=new THREE.Color(0x0d100a);
  camera=new THREE.PerspectiveCamera(45,w/h,0.1,5000); camera.position.set(60,-70,80);
  camera.up.set(0,0,1);
  controls=new OrbitControls(camera,renderer.domElement);
  scene.add(new THREE.AmbientLight(0xffffff,0.55));
  const d1=new THREE.DirectionalLight(0xffffff,0.9); d1.position.set(40,-60,120); scene.add(d1);
  const d2=new THREE.DirectionalLight(0xffffff,0.4); d2.position.set(-60,40,40); scene.add(d2);
  window.addEventListener('resize',onResize);
  (function loop(){ requestAnimationFrame(loop); controls.update(); renderer.render(scene,camera); })();
}
function onResize(){ const el=$('view'); if(!renderer)return; const w=el.clientWidth,h=el.clientHeight; renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); }

function buildAndShow(){
  if(!renderer) initThree();
  if(meshObj){ scene.remove(meshObj); meshObj.geometry.dispose(); meshObj.material.dispose(); meshObj=null; }
  if(gridObj){ scene.remove(gridObj); gridObj=null; }
  if(!S.segs.length) return;
  const m=buildMesh(null);
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.BufferAttribute(m.pos,3));
  geo.setAttribute('color',new THREE.BufferAttribute(m.col,3));
  geo.computeVertexNormals();
  const ext=m.cell*Math.max(m.W,m.H);
  geo.translate(-m.cell*m.W/2, -m.cell*m.H/2, 0);
  const mat=new THREE.MeshStandardMaterial({vertexColors:true, roughness:0.75, metalness:0.0, flatShading:false});
  meshObj=new THREE.Mesh(geo,mat); scene.add(meshObj);
  gridObj=new THREE.GridHelper(ext*1.4, 14, 0x39432c, 0x222a1b);
  gridObj.rotation.x=Math.PI/2; scene.add(gridObj);
  // frame camera
  const r=ext*0.9; camera.position.set(r*0.7,-r,r*0.9); controls.target.set(0,0,2); controls.update();
}
function highlight3D(){ /* selection is shown in 2D + list; 3D keeps true colours */ }

/* ---------------- STL export ---------------- */
function meshToBinarySTL(pos){
  const nTri=pos.length/9;
  const buf=new ArrayBuffer(84+nTri*50); const dv=new DataView(buf);
  for(let i=0;i<80;i++) dv.setUint8(i,0);
  dv.setUint32(80,nTri,true);
  let o=84;
  for(let t=0;t<nTri;t++){
    const i=t*9;
    const ax=pos[i],ay=pos[i+1],az=pos[i+2], bx=pos[i+3],by=pos[i+4],bz=pos[i+5], cx=pos[i+6],cy=pos[i+7],cz=pos[i+8];
    const ux=bx-ax,uy=by-ay,uz=bz-az, vx=cx-ax,vy=cy-ay,vz=cz-az;
    let nx=uy*vz-uz*vy, ny=uz*vx-ux*vz, nz=ux*vy-uy*vx;
    const ln=Math.hypot(nx,ny,nz)||1; nx/=ln;ny/=ln;nz/=ln;
    dv.setFloat32(o,nx,true);dv.setFloat32(o+4,ny,true);dv.setFloat32(o+8,nz,true);o+=12;
    dv.setFloat32(o,ax,true);dv.setFloat32(o+4,ay,true);dv.setFloat32(o+8,az,true);o+=12;
    dv.setFloat32(o,bx,true);dv.setFloat32(o+4,by,true);dv.setFloat32(o+8,bz,true);o+=12;
    dv.setFloat32(o,cx,true);dv.setFloat32(o+4,cy,true);dv.setFloat32(o+8,cz,true);o+=12;
    dv.setUint16(o,0,true);o+=2;
  }
  return buf;
}
function downloadBuf(buf,name){ const blob=new Blob([buf],{type:'application/octet-stream'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click(); }

$('exportBtn').addEventListener('click',()=>{
  if(!S.segs.length){ status('Process an image first.'); return; }
  const m=buildMesh(null);
  if(!m.pos.length){ status('Nothing to export (all regions height 0).'); return; }
  downloadBuf(meshToBinarySTL(m.pos), ($('fname').value.trim()||'icon')+'.stl');
  status('Exported combined STL ('+(m.pos.length/9|0)+' triangles).');
});
$('exportColorBtn').addEventListener('click',()=>{
  if(!S.segs.length){ status('Process an image first.'); return; }
  const colors=[...new Set(S.segs.map(s=>s.color))];
  let n=0;
  colors.forEach((c,idx)=>{
    const m=buildMesh(c); if(!m.pos.length) return;
    const nm=S.segs.find(s=>s.color===c)?.name || ('colour'+idx);
    downloadBuf(meshToBinarySTL(m.pos), ($('fname').value.trim()||'icon')+'_'+nm.replace(/[^a-z0-9]+/gi,'')+'.stl'); n++;
  });
  status('Exported '+n+' per-colour STL file(s).');
});

renderPalette();
status('Load an image (upload, URL, or paste) and press “Process”.');
