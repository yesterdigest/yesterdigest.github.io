// 배너 WebP 만들기 — 헤드리스 크롬 캔버스(libwebp)로 인코딩한다 (이 기계의 ffmpeg 에는 webp 인코더가 없다).
// 사용: 사이트 폴더에서  node tools/make-banner-webp.mjs [원본.png]      (Q=0.8 기본)
// 원본 = 유튜브 채널 배너 2560×1440 한 장 → strip-*.webp (제호 아래 사진 띠)
// 🔴 원본은 이 공개 저장소에 두지 않는다 — 작업 저장소(~/projects/yesterdigest/assets/brand-2026-09/_banner/)에 있다
// 포트 9334 · 임시 프로필만 쓴다 (9222·유진님 프로필 금지)
import { spawn } from 'node:child_process'; import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'ydwebp-'));
const ch = spawn('google-chrome', ['--headless=new','--disable-gpu','--remote-debugging-port=9334','--user-data-dir='+prof,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
for(let i=0;i<50;i++){try{await fetch('http://127.0.0.1:9334/json/version');break}catch{await sleep(200)}}
const t=(await (await fetch('http://127.0.0.1:9334/json/list')).json()).find(x=>x.type==='page');
const ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise(r=>ws.addEventListener('open',r));
let id=0;const P=new Map();ws.addEventListener('message',m=>{const d=JSON.parse(m.data);if(P.has(d.id)){P.get(d.id)(d);P.delete(d.id)}});
const send=(method,params={})=>new Promise(r=>{const i=++id;P.set(i,r);ws.send(JSON.stringify({id:i,method,params}))});
const SRC=process.argv[2]||path.join(os.homedir(),'projects/yesterdigest/assets/brand-2026-09/_banner/youtube-banner-2026-09-24-2560x1440.png');
const src='data:image/png;base64,'+fs.readFileSync(SRC).toString('base64');
await send('Runtime.evaluate',{expression:`(async()=>{const im=new Image();im.src=${JSON.stringify(src)};await im.decode();window.__im=im;return 1})()`,awaitPromise:true});
const Q=parseFloat(process.env.Q||'0.8');
const jobs=[
            // 제호 아래 사진 띠 — 배너 «아랫줄»(신문·서울·거리)만. 가운데 옛 로고 줄은 쓰지 않는다
            ['strip-1280',0,1015,2560,425,1280],['strip-1920',0,1015,2560,425,1920],['strip-2560',0,1015,2560,425,2560],
            ['strip-m-720',800,1015,1190,425,720],['strip-m-1080',800,1015,1190,425,1080]];
for(const [n,sx,sy,sw,sh,w] of jobs){
  const h=Math.round(sh*w/sw/2)*2;
  const r=await send('Runtime.evaluate',{expression:`(async()=>{const im=window.__im;const c=document.createElement('canvas');c.width=${w};c.height=${h};const x=c.getContext('2d');x.imageSmoothingQuality='high';x.drawImage(im,${sx},${sy},${sw},${sh},0,0,${w},${h});return c.toDataURL('image/webp',${Q});})()`,awaitPromise:true,returnByValue:true});
  const b=Buffer.from(r.result.result.value.split(',')[1],'base64');
  fs.writeFileSync(`assets/brand/${n}.webp`,b); console.log(n,w+'x'+h,b.length);
}
ws.close(); ch.kill('SIGTERM'); await sleep(600); try{fs.rmSync(prof,{recursive:true,force:true})}catch{}
