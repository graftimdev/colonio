"""Draft 11 stages 4-5: tutorial engine rebuilt (hand-made maps, one calm pointer, hints only when needed),
the starter tutorial on the Draft 11 layout, and the tutorial menu with small tutorials."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


# ---------- newGame can take a hand-made map and a worker count ----------
rep("const np=on?on.seats.length:opts.bots+1,mode=opts.mode==='conquest'?'conquest':'warfare';const {nodes,cores,planets}=genMap(np,opts.per,mode);",
    "const np=on?on.seats.length:opts.bots+1,mode=opts.mode==='conquest'?'conquest':'warfare';const {nodes,cores,planets}=opts.map?opts.map():genMap(np,opts.per,mode);")
rep("  for(let i=0;i<np;i++)for(let w=0;w<5;w++)G.workers.push(newWorker(i,cores[i]));",
    "  for(let i=0;i<np;i++)for(let w=0;w<(opts.workers!=null?opts.workers:5);w++)G.workers.push(newWorker(i,cores[i]));")
rep("  if(!on)try{localStorage.setItem('jopium-setup',JSON.stringify(opts));}catch(e){}",
    "  if(!on&&!opts.map)try{localStorage.setItem('jopium-setup',JSON.stringify(opts));}catch(e){}")

# ---------- replace the whole Draft 10 tutorial block ----------
i = s.index("/* ---------- tutorial ----------")
j = s.index("function tutSkip(){G.popup={type:'tutskip'};G.popupAt=performance.now();renderPopup();}")
j = s.index("\n", j) + 1
TUT = r"""/* ---------- tutorials ----------
   One engine for the starter tutorial and the small ones. Each tutorial builds a hand-made map (tutMap),
   then walks through steps. The only pointer is a slow, turning yellow outline around what to press; a bubble
   appears only when there is something worth explaining. When a menu is in the way of a map target, the pointer
   goes to that menu's ✕ first. A correct press gives a short yellow shine. */
let TUT=null,TUT_SAVE=null;
const tutEl=()=>$('#tut');
// a map from axial cells: {cells:[[q,r,type,res]...], planet:{c:[q,r],secs:[[q,r]...]}, cores:[[q,r],[q,r]]}
function tutMap(spec){
  const nodes=[],idx=new Map(),key2=(q,r)=>q+','+r;
  const add=(q,r,type,res)=>{const n={id:nodes.length,q,r,x:R*(q+r/2),y:R*(SQ3/2)*r,nbr:[],type:type||'empty',res:res||null,owner:null,coreOf:null,coreHp:0,stations:[],store:{},estore:0,cut:0,planet:null,center:false};n.shape=Array.from({length:7},()=>.75+rnd()*.45);idx.set(key2(q,r),n.id);nodes.push(n);return n;};
  for(const [q,r,t,res] of spec.cells)add(q,r,t,res);
  const planets=[];
  if(spec.planet){const pl=spec.planet,c=add(pl.c[0],pl.c[1],'planet');c.planet=0;c.center=true;
    const ids=[c.id];for(const [q,r] of pl.secs){const n=add(q,r,'planet');n.planet=0;ids.push(n.id);}
    planets.push({...PLANETS[pl.look||0],center:c.id,ids,look:planetLook(PLANETS[pl.look||0].kind)});}
  const cores=spec.cores.map(([q,r])=>{let id=idx.get(key2(q,r));if(id==null)id=add(q,r,'core').id;return id;});
  for(const n of nodes)for(const [a,b] of DIRS){const k=key2(n.q+a,n.r+b);if(idx.has(k))n.nbr.push(idx.get(k));}
  cores.forEach((c,pid)=>{const n=nodes[c];n.type='core';n.coreOf=pid;n.owner=pid;n.coreHp=CORE_HP;});
  const at=(q,r)=>idx.get(key2(q,r));
  return {nodes,cores,planets,at};
}
// start a tutorial: a fresh match on its map, sleeping rival, tutorial rules on
function beginTutorial(key){
  const T=TUTS[key]||TUTS.starter;closeOverlay();
  let M=null;
  newGame({per:12,bots:1,timer:0,mode:'warfare',diff:'easy',seed:7,workers:T.workers??1,map:()=>(M=tutMap(T.map),M)});
  G.tut=true;G.turnTime=0;G.timeLeft=0;G.sel=null;
  TUT_SAVE={tb:TECH.barrack.c,kt:ST.kazarm.t,lt:ST.levi.t,tt:TECH.trade.c};
  const p=P(ME);p.explored=new Set(G.nodes.map(n=>n.id));P(1).explored=new Set(G.nodes.map(n=>n.id));
  for(const r of RES)p.res[r]=0;
  T.setup(M.at,p);
  G.conn=G.players.map(q=>connSet(q.id));
  TUT={key,T,i:0,at:M.at,ids:T.ids?T.ids(M.at):{},t0:performance.now(),fx:null};
  centerOn(G.nodes[p.core],true);
  if(T.center)centerOn(G.nodes[T.center(M.at)],false);
  refresh();takeSnapshot();
  const st=tutStep();if(st&&st.enter)st.enter();
  tutLoop();
}
// ---- where to point ----
const nodeOpen=id=>G.modal&&G.modal.type==='node'&&G.modal.id===id&&!$('#modal').hidden;
const unitOpen=f=>f&&G.modal&&G.modal.type==='unit'&&G.modal.f===f.id&&!$('#modal').hidden;
const stOpen=uid=>G.modal&&G.modal.type==='station'&&G.modal.uid===uid&&!$('#modal').hidden;
const q$=sel=>{const el=document.querySelector(sel);return el&&el.offsetParent!==null&&!el.disabled?el:null;};
const T_tile=id=>({tile:id}),T_dom=sel=>({dom:sel});
const myWorkers=()=>G.workers.filter(w=>w.owner===ME);
const workerTo=id=>myWorkers().some(w=>(w.path.length?w.path.at(-1):w.node)===id);
const workerAt=id=>myWorkers().some(w=>w.node===id&&!w.path.length);
const myFleets=c=>G.fleets.filter(f=>f.owner===ME&&(!c||f.cls===c));
const T2=(en,ru)=>L(en,ru);
// open tile `from`, press Move on a worker there, then tap tile `to`
function tMove(from,to){if(G.moveMode)return T_tile(to);if(nodeOpen(from)&&q$('[data-a="wmove"]'))return T_dom('[data-a="wmove"]');return T_tile(from);}
function tTask(id,task){if(nodeOpen(id)&&q$(`[data-a="wtask"][data-t="${task}"]`))return T_dom(`[data-a="wtask"][data-t="${task}"]`);return T_tile(id);}
// open a tile's "Build a station here" list, then press Start on `type`
function tBuild(id,type){if(!nodeOpen(id))return T_tile(id);if(q$(`[data-a="start"][data-t="${type}"]`))return T_dom(`[data-a="start"][data-t="${type}"]`);return T_dom('#modal details > summary');}
// a squadron order: tap the squadron, press the button, tap the tile (and confirm the battle preview)
function tFleet(f,act,to){if(!f)return null;if(G.popup&&G.popup.type==='preview')return T_dom('[data-a="pmove"]');if(G.popup&&G.popup.type==='charge')return null;if(G.moveMode)return T_tile(to);if(unitOpen(f)&&q$(`[data-a="${act}"][data-f="${f.id}"]`))return T_dom(`[data-a="${act}"][data-f="${f.id}"]`);return {unit:f};}
// a station's button
function tStation(n,s,sel){if(stOpen(s.uid)&&q$(sel))return T_dom(sel);if(nodeOpen(n)&&q$(`[data-a="openst"][data-s="${s.uid}"]`))return T_dom(`[data-a="openst"][data-s="${s.uid}"]`);return {station:s.uid,tile:n};}
const stepDone=()=>TUT&&TUT.T.steps[TUT.i];
const tutStep=stepDone;
const tutAllowsEnd=()=>!TUT||!!(tutStep()&&tutStep().end);
// a map target can't be pressed while a menu covers it: point at the menu's ✕ first
function tutResolve(t){
  if(!t)return null;
  const mapT=t.tile!=null||t.unit||t.station!=null||t.hold;
  if(mapT&&!t.dom){
    if(G.popup&&!$('#popup').hidden&&q$('#popup .x'))return {dom:'#popup .x',close:true};
    if(!$('#techscr').hidden&&q$('#techscr .tcore'))return {dom:'#techscr .tcore',close:true};
    if(!$('#modal').hidden&&q$('#modal .x'))return {dom:'#modal .x',close:true};
  }
  return t;
}
function tutRect(t){
  if(!t)return null;
  if(t.dom){const el=q$(t.dom);if(!el)return null;const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width+12,h:r.height+12,round:false};}
  const cr=cv.getBoundingClientRect();
  if(t.unit||t.hold){const u=t.unit||t.hold;const h=G.hits.find(h=>h.kind==='fleet'&&h.u===u);if(h)return {x:cr.left+h.x,y:cr.top+h.y,w:h.r*2.6,h:h.r*2.6,round:true};const n=G.nodes[u.node];const [x,y]=toScreen(n.x,n.y);const d=R*cam.z*1.2;return {x:cr.left+x,y:cr.top+y,w:d,h:d,round:true};}
  if(t.station!=null){const h=G.hits.find(h=>h.kind==='station'&&h.s.uid===t.station);if(h)return {x:cr.left+h.x,y:cr.top+h.y,w:h.r*2.8,h:h.r*2.8,round:true};}
  const id=t.tile;if(id==null)return null;const n=G.nodes[id];const [x,y]=toScreen(n.x,n.y);const d=27*Math.max(.55,Math.min(1.4,cam.z))*2+16;return {x:cr.left+x,y:cr.top+y,w:d,h:d,round:true};
}
function tutAdvance(){
  const r=TUT.lastRect;if(r)TUT.fx={x:r.x,y:r.y,t:performance.now()};
  TUT.i++;TUT.t0=performance.now();sfxTurn();
  const nx=tutStep();
  if(!nx){tutFinish();return;}
  if(nx.enter)nx.enter();
  if(nx.end&&nx.at&&(nx.at()||{}).dom==='#endturn'){closeModal();refresh();}
}
function tutLoop(){
  if(!TUT||!G||!G.tut){const el=tutEl();if(el)el.hidden=true;return;}
  const el=tutEl(),st=tutStep();
  if(!st){el.hidden=true;return;}
  if(st.fix)st.fix();
  if(st.done&&st.done()){tutAdvance();requestAnimationFrame(tutLoop);return;}
  el.hidden=false;
  const t=tutResolve(st.at?st.at():null),r=tutRect(t);if(r)TUT.lastRect=r;
  const out=$('#tutout'),bub=$('#tutbub'),fx=$('#tutfx');
  out.hidden=!r;
  if(r){out.style.left=(r.x-r.w/2-4)+'px';out.style.top=(r.y-r.h/2-4)+'px';out.setAttribute('width',r.w+8);out.setAttribute('height',r.h+8);
    const rc=out.querySelector('rect');rc.setAttribute('width',r.w+4);rc.setAttribute('height',r.h+4);rc.setAttribute('rx',r.round?(r.w+4)/2:10);}
  // the bubble: only when this step has something to explain (closing a menu needs no words)
  const txt=t&&t.close?null:st.say?st.say():null;
  const key=TUT.i+'|'+(txt||'');
  if(bub.dataset.k!==key){bub.dataset.k=key;bub.hidden=!txt&&!st.next;bub.querySelector('.tt').textContent=txt||'';const nb=bub.querySelector('.tutnext');nb.hidden=!st.next;nb.textContent=L('Next','Далее');bub.classList.remove('pop');void bub.offsetWidth;bub.classList.add('pop');}
  if(!bub.hidden){
    const bw=bub.offsetWidth,bh=bub.offsetHeight,vw=innerWidth,vh=innerHeight;let bx,by;
    if(r){const right=r.x+r.w/2+16+bw<vw-8;bx=right?r.x+r.w/2+16:r.x-r.w/2-16-bw;by=r.y-bh/2;if(bx<8){bx=Math.max(8,Math.min(vw-bw-8,r.x-bw/2));by=r.y+r.h/2+14;if(by+bh>vh-8)by=r.y-r.h/2-bh-14;}}
    else{bx=(vw-bw)/2;by=vh-bh-90;}
    bub.style.left=Math.max(8,Math.min(vw-bw-8,bx))+'px';bub.style.top=Math.max(8,Math.min(vh-bh-8,by))+'px';
  }
  // a correct press: a short yellow shine with a few sparks
  if(TUT.fx){const k=(performance.now()-TUT.fx.t)/1100;if(k>1){TUT.fx=null;fx.hidden=true;}else{fx.hidden=false;fx.style.left=TUT.fx.x+'px';fx.style.top=TUT.fx.y+'px';fx.style.setProperty('--k',k);}}
  requestAnimationFrame(tutLoop);
}
// FINISH HIM: big letters for 2 s and a deep synthesized voice; the music dips while it speaks
function finishHim(){
  const b=$('#tutbig');b.textContent=L('FINISH HIM','ДОБЕЙ ЕГО');b.hidden=false;b.classList.remove('go');void b.offsetWidth;b.classList.add('go');setTimeout(()=>{b.hidden=true;},2200);
  duck=.2;const back=()=>{duck=1;};
  try{if(window.speechSynthesis&&settings.sfx>0){const u=new SpeechSynthesisUtterance(L('Finish him!','Добей его!'));u.lang=RU()?'ru-RU':'en-US';u.pitch=.1;u.rate=.75;u.volume=Math.min(1,settings.sfx*1.4);u.onend=back;speechSynthesis.cancel();speechSynthesis.speak(u);setTimeout(back,3500);}else setTimeout(back,1500);}catch(e){back();}
}
function tutFinish(){
  restoreTutRules();
  const el=tutEl();if(el)el.hidden=true;
  const k=TUT?TUT.key:'starter',T=TUTS[k];TUT=null;
  profile.tuts=Object.assign({},profile.tuts||{},{[k]:true});saveProfile();
  if(k==='starter')Acc.tutDone();
  if(Acc.state==='in')Acc.saveTuts();
  if(G){G.tut=false;G.over=true;}
  ov.hidden=false;ov.className='dim';ov.dataset.view='tutdone';
  ov.innerHTML=`<div class="card"><h1>${k==='starter'?L('Tutorial complete','Обучение пройдено'):L(`${T.n} tutorial completed`,`Обучение «${T.r}» пройдено`)}</h1>${k==='starter'?`<p>${L('More short tutorials are in Settings → Tutorials.','Другие короткие уроки — в Настройках → «Обучение».')}</p>`:''}<div class="opts"><button class="btn primary" type="button" data-a="tut-menu">${L('To the main menu','В главное меню')}</button>${k!=='starter'?`<button class="btn" type="button" data-a="tut-list">${L('More tutorials','Другие уроки')}</button>`:''}</div></div>`;
}
function restoreTutRules(){if(TUT_SAVE){TECH.barrack.c=TUT_SAVE.tb;ST.kazarm.t=TUT_SAVE.kt;ST.levi.t=TUT_SAVE.lt;TECH.trade.c=TUT_SAVE.tt;TUT_SAVE=null;}}
// leaving a tutorial early: ask first
function tutSkip(){G.popup={type:'tutskip'};G.popupAt=performance.now();renderPopup();}
// first visit: language first, then the starter tutorial; from Settings: the list of tutorials
function startTutorial(){showMenu('tutlang');}
function tutMenuHtml(){
  const done=profile.tuts||{},row=k=>{const T=TUTS[k];return `<button class="btn tutrow" type="button" data-a="tut-go" data-v="${k}"><span>${L(T.n,T.r)}</span>${done[k]||(k==='starter'&&profile.tut)?'<span class="good">✓</span>':''}</button>`;};
  return `<div class="card"><button class="x" type="button" data-a="m-settings" aria-label="${L('Close','Закрыть')}">✕</button><h1>${L('Tutorials','Обучение')}</h1>
    <div class="mbtns">${row('starter')}</div>
    <h3 class="sub" style="margin:4px 0 0">${L('Economy','Экономика')}</h3><div class="mbtns">${row('trade')}</div>
    <h3 class="sub" style="margin:4px 0 0">${L('War drones','Боевые дроны')}</h3><div class="mbtns tutgrid">${['interceptor','bomber','frigate','siege','catapult','boomerang','tank','stomper','ballista'].map(row).join('')}</div></div>`;
}
"""
s = s[:i] + TUT + s[j:]

# ---------- the tutorials themselves ----------
TUTS = r"""
/* ---------- the tutorials ---------- */
const enemyFleet=(cls,k,node,up)=>{const f=newFleet(1,cls,k,node,up);G.fleets.push(f);return f;};
const myFleet=(cls,k,node,up)=>{const f=newFleet(ME,cls,k,node,up);G.fleets.push(f);return f;};
const TUTS={
  // the starter: core with iron, empty and silicon asteroids; iron and silicon meet in one planet section; the enemy core sits by another
  starter:{n:'Starter tutorial',r:'Основное обучение',workers:1,
    map:{cells:[[1,0,'res','iron'],[-1,0,'empty'],[1,-1,'res','silicon'],[6,-1,'res','copper'],[5,0,'empty'],[6,-2,'res','iron'],[5,-2,'res','silicon'],[-2,0,'res','copper'],[-2,1,'empty']],
         planet:{c:[3,-1],secs:[[2,-1],[4,-1],[3,0],[3,-2],[4,-2]],look:1},cores:[[0,0],[5,-1]]},
    ids:at=>({A:at(1,0),E:at(-1,0),Si:at(1,-1),S:at(2,-1),S2:at(4,-1),P:at(3,-1),ec:at(5,-1)}),
    setup:(at,p)=>{for(const r of RES)p.res[r]=25;p.gold=99;TECH.barrack.c=1;ST.kazarm.t=1;ST.levi.t=1;},
    steps:[
      {say:()=>T2('This is your core: everything starts here. Tap it.','Это ваше ядро, с него начинается всё. Нажмите на него.'),at:()=>T_tile(P(ME).core),done:()=>G.sel===P(ME).core||nodeOpen(P(ME).core)},
      {say:()=>T2('Tap it again to open it.','Нажмите ещё раз, чтобы открыть его.'),at:()=>T_tile(P(ME).core),done:()=>nodeOpen(P(ME).core)},
      {say:()=>G.moveMode?T2('Send it to the iron asteroid.','Отправьте его на железный астероид.'):T2('Workers claim and mine asteroids. Send yours out.','Рабочие захватывают астероиды и добывают ресурсы. Отправьте своего.'),at:()=>tMove(P(ME).core,TUT.ids.A),done:()=>workerTo(TUT.ids.A)},
      {say:()=>T2('Orders play out when you end the turn.','Приказы выполняются, когда вы завершаете ход.'),at:()=>T_dom('#endturn'),end:true,done:()=>workerAt(TUT.ids.A)},
      {say:()=>T2('Claim the asteroid to make it yours.','Захватите астероид, чтобы он стал вашим.'),at:()=>tTask(TUT.ids.A,'claim'),done:()=>myWorkers().some(w=>w.node===TUT.ids.A&&w.task==='claim')||G.nodes[TUT.ids.A].owner===ME},
      {at:()=>T_dom('#endturn'),end:true,done:()=>G.nodes[TUT.ids.A].owner===ME},
      {say:()=>T2('Mine it: a worker on your asteroid brings 2 of its resource every turn, for 1 energy. Iron pays for workers and drones.','Добывайте: рабочий на вашем астероиде приносит 2 единицы ресурса каждый ход за 1 энергию. Железо нужно для рабочих и дронов.'),at:()=>tTask(TUT.ids.A,'mine'),done:()=>myWorkers().some(w=>w.node===TUT.ids.A&&w.task==='mine')},
      {say:()=>T2('Build a second worker at your core. It appears next turn.','Создайте в ядре второго рабочего. Он появится в следующем ходу.'),at:()=>nodeOpen(P(ME).core)?T_dom('[data-a="hire"]'):T_tile(P(ME).core),done:()=>P(ME).workerQueue>0},
      {at:()=>T_dom('#endturn'),end:true,done:()=>myWorkers().length>=2},
      {say:()=>T2('Research the Barrack with the worker at your core.','Исследуйте Казарму рабочим, стоящим в ядре.'),
        at:()=>!$('#techscr').hidden?(G.popup&&G.popup.type==='tech'&&G.popup.t==='barrack'?T_dom('[data-a="tset"]'):T_dom('[data-a="techpop"][data-t="barrack"]')):nodeOpen(P(ME).core)?T_dom('[data-a="open"][data-m="tech"]'):T_tile(P(ME).core),
        done:()=>myWorkers().some(w=>w.task==='research'&&w.tech==='barrack')||has(ME,'barrack')},
      {at:()=>T_dom('#endturn'),end:true,done:()=>has(ME,'barrack')},
      {say:()=>T2('Build a Barrack at your core.','Постройте Казарму в ядре.'),at:()=>tBuild(P(ME).core,'kazarm'),done:()=>G.nodes[P(ME).core].stations.some(s=>s.type==='kazarm')},
      {at:()=>T_dom('#endturn'),end:true,done:()=>live(G.nodes[P(ME).core],'kazarm').length>0},
      {say:()=>T2('Order two different war drones.','Закажите двух разных боевых дронов.'),
        at:()=>{const k=live(G.nodes[P(ME).core],'kazarm')[0];if(!k)return null;return tStation(P(ME).core,k,k.queue.includes('interceptor')?'[data-a="kbuild"][data-c="bomber"]':'[data-a="kbuild"][data-c="interceptor"]');},
        done:()=>{const k=live(G.nodes[P(ME).core],'kazarm')[0];return !!k&&new Set([...k.queue,...CLS.filter(c=>k.hangar[c].length)]).size>=2;}},
      {at:()=>T_dom('#endturn'),end:true,done:()=>{const k=live(G.nodes[P(ME).core],'kazarm')[0];return !!k&&k.hangar.interceptor.length>0&&k.hangar.bomber.length>0;}},
      {at:()=>{if(G.popup&&G.popup.type==='hangar')return T_dom('[data-a="hlaunch"][data-i="-1"]');const k=live(G.nodes[P(ME).core],'kazarm')[0];return k?tStation(P(ME).core,k,`[data-a="hangar"][data-c="${k.hangar.interceptor.length?'interceptor':'bomber'}"]`):null;},
        done:()=>myFleets().length>=2},
      {say:()=>G.popup&&G.popup.type==='squad'?null:T2('Press and hold here for a second, then drag across both squadrons to group them into a fleet.','Нажмите здесь и держите секунду, затем протяните рамку через обе эскадрильи, чтобы собрать их во флот.'),
        at:()=>G.popup&&G.popup.type==='squad'?T_dom('[data-a="sqmake"]'):{hold:myFleets()[0]},done:()=>(P(ME).squads||[]).length>0},
      {enter:()=>{enemyFleet('interceptor',1,TUT.ids.E);hitPulse(TUT.ids.E,[],[],'gift');G.pulseT0=performance.now();refresh();},
        say:()=>G.popup&&G.popup.type==='preview'||G.moveMode?null:T2('An enemy drone landed next to your core! Attack it with your fleet.','Вражеский дрон сел рядом с ядром! Атакуйте его флотом.'),
        at:()=>G.popup&&G.popup.type==='preview'?T_dom('[data-a="pmove"]'):G.moveMode?T_tile(TUT.ids.E):G.modal&&G.modal.type==='empire'&&!$('#modal').hidden?T_dom('[data-a="sqmove"]'):T_dom('#empireBtn'),
        done:()=>myFleets().some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.E)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1)},
      {say:()=>G.moveMode?null:T2('Planet centres hold jopium. Send your new worker to the planet centre.','В центрах планет есть жопиум. Отправьте нового рабочего в центр планеты.'),at:()=>tMove(P(ME).core,TUT.ids.P),done:()=>workerTo(TUT.ids.P),
        // the worker takes the silicon asteroid and the planet section straight to the centre
        fix:()=>{const w=myWorkers().find(w=>w.path.length&&w.path.at(-1)===TUT.ids.P&&w.path[0]!==TUT.ids.Si&&w.node===P(ME).core);if(w)w.path=[TUT.ids.Si,TUT.ids.S,TUT.ids.P];}},
      {say:()=>T2('End turns until it arrives.','Завершайте ходы, пока он не долетит.'),at:()=>T_dom('#endturn'),end:true,done:()=>workerAt(TUT.ids.P)},
      {at:()=>tTask(TUT.ids.P,'claim'),done:()=>myWorkers().some(w=>w.node===TUT.ids.P&&w.task==='claim')||G.nodes[TUT.ids.P].owner===ME},
      {at:()=>T_dom('#endturn'),end:true,done:()=>G.nodes[TUT.ids.P].owner===ME},
      {say:()=>T2('Press Mine now: from the turn the centre connects to your core, it gives 1 jopium a turn, that very turn included.','Нажмите «Добывать»: с того хода, когда центр соединится с ядром, он даёт 1 жопиум за ход, включая этот ход.'),at:()=>tTask(TUT.ids.P,'mine'),done:()=>myWorkers().some(w=>w.node===TUT.ids.P&&w.task==='mine')},
      {say:()=>T2('The red cross means the centre is cut off: the planet section between it and your iron asteroid is unclaimed.','Красный крестик значит, что центр отрезан: участок планеты между ним и вашим железным астероидом ничей.'),at:()=>T_tile(TUT.ids.P),next:true},
      {say:()=>{const g=TUT.ids.S;if(workerAt(g)&&!myWorkers().some(w=>w.node===g&&w.task==='claim'))return null;if(myWorkers().some(w=>w.node===g&&w.task==='claim')||workerTo(g))return null;return T2('Move the iron miner one hop onto that section and claim it.','Переместите шахтёра с железа на этот участок и захватите его.');},
        at:()=>{const g=TUT.ids.S;if(myWorkers().some(w=>w.node===g&&!w.path.length&&w.task==='claim'))return T_dom('#endturn');if(workerAt(g))return tTask(g,'claim');if(workerTo(g))return T_dom('#endturn');return tMove(TUT.ids.A,g);},end:true,
        done:()=>G.nodes[TUT.ids.S].owner===ME&&G.conn[ME].has(TUT.ids.P)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>P(ME).gold>=100},
      {say:()=>T2('100 jopium: build a leviathan on the planet centre.','100 жопиума: постройте левиафана в центре планеты.'),at:()=>tBuild(TUT.ids.P,'levi'),done:()=>G.nodes[TUT.ids.P].stations.some(s=>s.type==='levi')||myFleets('leviathan').length>0},
      {at:()=>T_dom('#endturn'),end:true,done:()=>myFleets('leviathan').length>0},
      {say:()=>G.moveMode||G.popup?null:T2('Send it to the enemy core.','Отправьте его к вражескому ядру.'),at:()=>tFleet(myFleets('leviathan')[0],'fmove',TUT.ids.ec),done:()=>myFleets('leviathan').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.ec)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>myFleets('leviathan').some(f=>f.node===TUT.ids.S2)},
      {enter:()=>finishHim(),at:()=>T_dom('#endturn'),end:true,done:()=>!P(1).alive},
    ]},

  trade:{n:'Trade',r:'Торговля',workers:2,
    map:{cells:[[1,0,'res','iron'],[-1,0,'res','copper'],[0,1,'empty'],[4,-2,'empty']],cores:[[0,0],[5,-2]]},
    setup:(at,p)=>{p.res.iron=30;p.res.silicon=10;p.techs.add('generator');TECH.trade.c=1;p.workersBuilt=0;},
    steps:[
      {say:()=>T2('You need copper for a new worker, and you have none. Research Trade with your workers.','Для нового рабочего нужна медь, а её нет. Исследуйте Торговлю своими рабочими.'),
        at:()=>!$('#techscr').hidden?(G.popup&&G.popup.type==='tech'&&G.popup.t==='trade'?T_dom('[data-a="tset"]'):T_dom('[data-a="techpop"][data-t="trade"]')):nodeOpen(P(ME).core)?T_dom('[data-a="open"][data-m="tech"]'):T_tile(P(ME).core),
        done:()=>myWorkers().some(w=>w.task==='research'&&w.tech==='trade')},
      {at:()=>T_dom('#endturn'),end:true,done:()=>has(ME,'trade')},
      {say:()=>G.modal&&G.modal.type==='empire'&&!$('#modal').hidden?T2('Give iron, get copper, and trade until you have 4 copper.','Отдайте железо, получите медь и меняйте, пока не будет 4 меди.'):T2('Trading is in the Empire menu.','Торговля — в меню «Империя».'),
        at:()=>{if(!(G.modal&&G.modal.type==='empire'&&!$('#modal').hidden))return T_dom('#empireBtn');if(G.trade.give!=='iron')return T_dom('[data-a="tgive"][data-r="iron"]');if(G.trade.get!=='copper')return T_dom('[data-a="tget"][data-r="copper"]');return T_dom('[data-a="trade"]');},
        done:()=>P(ME).res.copper>=workerCost(P(ME)).copper},
      {say:()=>T2('Now build the worker at your core.','Теперь создайте рабочего в ядре.'),at:()=>nodeOpen(P(ME).core)?T_dom('[data-a="hire"]'):T_tile(P(ME).core),done:()=>P(ME).workerQueue>0},
    ]},

  // a lone ballista at the edge of a planet; four enemy tiles in a line, the last an enemy core at 1 health
  ballista:{n:'Ballista',r:'Баллиста',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty'],[3,0,'empty'],[-3,2,'empty']],planet:{c:[-1,0],secs:[[0,0],[-2,0],[-1,1],[-1,-1],[0,-1],[-2,1]],look:2},cores:[[-3,1],[4,0]]},
    ids:at=>({B:at(0,0),t1:at(1,0),t2:at(2,0),t3:at(3,0),ec:at(4,0)}),center:at=>at(1,0),
    setup:(at,p)=>{p.res.xeno=10;p.techs.add('rovers');p.techs.add('planetmove');myFleet('ballista',1,at(0,0));enemyFleet('interceptor',1,at(1,0));enemyFleet('interceptor',1,at(2,0));enemyFleet('frigate',1,at(3,0));G.nodes[at(4,0)].coreHp=1;},
    steps:[
      {say:()=>G.popup&&G.popup.type==='charge'?T2('Charge all 5 crystals: the bolt jumps along the line, doubling each time, and the 4th hit lands on the core.','Зарядите все 5 кристаллов: молния прыгает по линии, удваиваясь, и 4-й удар придётся в ядро.'):G.moveMode?null:T2('Your ballista can fire lightning along that line of enemies.','Ваша баллиста может ударить молнией по этой линии врагов.'),
        at:()=>{if(G.popup&&G.popup.type==='charge')return G.popup.cr<5?T_dom('[data-a="chg"][data-k="5"]'):T_dom('[data-a="chgfire"]');return tFleet(myFleets('ballista')[0],'fbomb',TUT.ids.t1);},
        done:()=>myFleets('ballista').some(f=>f.bombard===TUT.ids.t1&&f.charge===5)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!P(1).alive},
    ]},

  interceptor:{n:'Interceptor',r:'Перехватчик',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty'],[3,0,'res','iron'],[4,0,'empty']],cores:[[0,0],[6,-1]]},
    ids:at=>({X:at(3,0)}),center:at=>at(2,0),
    setup:(at,p)=>{p.techs.add('barrack');myFleet('interceptor',2,at(1,0));G.workers.push(newWorker(1,at(3,0)));G.workers.at(-1).task='claim';G.nodes[at(4,0)].owner=null;},
    steps:[
      {say:()=>G.moveMode||G.popup?null:T2('Interceptors fly 2 hops a turn. An enemy worker is claiming the iron asteroid 2 hops away: get there this turn.','Перехватчики пролетают 2 прыжка за ход. Вражеский рабочий захватывает железный астероид в 2 прыжках: успейте туда за этот ход.'),
        at:()=>tFleet(myFleets('interceptor')[0],'fmove',TUT.ids.X),done:()=>myFleets('interceptor').some(f=>f.path.at(-1)===TUT.ids.X)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!G.workers.some(w=>w.owner===1&&w.node===TUT.ids.X)},
    ]},

  bomber:{n:'Bomber',r:'Бомбер',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty']],cores:[[0,0],[4,-1]]},
    ids:at=>({X:at(1,0)}),center:at=>at(1,0),
    setup:(at,p)=>{p.techs.add('barrack');const c=G.nodes[p.core];const k=newStation(c,'kazarm',{state:'done'});k.work=0;c.stations.push(k);k.hangar.bomber.push(newDrone('bomber'));myFleet('bomber',5,p.core);enemyFleet('frigate',5,at(1,0));},
    steps:[
      {say:()=>T2('Bombers deal 3 instead of 2 while their squadron outnumbers every enemy squadron. You have 5, the enemy has 5. Launch the bomber waiting in your Barrack.','Бомберы наносят 3 вместо 2, пока их эскадрилья больше любой вражеской. У вас 5, у врага 5. Выпустите бомбер из Казармы.'),
        at:()=>{if(G.popup&&G.popup.type==='hangar')return T_dom('[data-a="hlaunch"][data-i="-1"]');const k=live(G.nodes[P(ME).core],'kazarm')[0];return tStation(P(ME).core,k,'[data-a="hangar"][data-c="bomber"]');},
        done:()=>myFleets('bomber').some(f=>f.count>=6)},
      {say:()=>G.moveMode||G.popup?null:T2('6 against 5: now attack the frigates.','6 против 5: теперь атакуйте фрегаты.'),at:()=>tFleet(myFleets('bomber')[0],'fmove',TUT.ids.X),done:()=>myFleets('bomber').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.X)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1)},
    ]},

  frigate:{n:'Frigate',r:'Фрегат',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty'],[1,-1,'empty']],cores:[[0,0],[4,-1]]},
    ids:at=>({X:at(1,0),Y:at(1,-1),Z:at(2,0)}),center:at=>at(1,0),
    setup:(at,p)=>{p.techs.add('barrack');myFleet('catapult',2,at(1,0));myFleet('frigate',3,at(1,-1));enemyFleet('interceptor',3,at(2,0));},
    steps:[
      {say:()=>G.moveMode||G.popup?null:T2('Enemy interceptors will hit your catapults next turn. Frigates take damage first: move them onto the catapults\' tile to shield them.','Вражеские перехватчики ударят по катапультам в следующем ходу. Фрегаты принимают урон первыми: переместите их к катапультам, чтобы прикрыть.'),
        at:()=>tFleet(myFleets('frigate')[0],'fmove',TUT.ids.X),done:()=>myFleets('frigate').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.X)},
      {enter:()=>{const e=G.fleets.find(f=>f.owner===1);if(e)e.path=[TUT.ids.X];},at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1)},
      {say:()=>myFleets('catapult').length?T2('The frigates took the hits, and every catapult survived.','Фрегаты приняли удар, и все катапульты уцелели.'):T2('The battle is over.','Бой окончен.'),at:()=>T_tile(TUT.ids.X),next:true},
    ]},

  siege:{n:'Siege',r:'Осада',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty']],cores:[[0,0],[3,0]]},
    ids:at=>({ec:at(3,0),X:at(2,0)}),center:at=>at(2,0),
    setup:(at,p)=>{p.techs.add('barrack');myFleet('siege',6,at(2,0));const e=G.nodes[at(3,0)];const t=newStation(e,'turret',{state:'done'});t.hp=t.maxHp||ST.turret.hp||6;e.stations.push(t);},
    steps:[
      {say:()=>G.moveMode||G.popup?null:T2('Siege drones deal only 1 to drones but 5 to turrets and cores. Attack the enemy core.','Осадные дроны наносят дронам всего 1, но турелям и ядрам — 5. Атакуйте вражеское ядро.'),
        at:()=>tFleet(myFleets('siege')[0],'fmove',TUT.ids.ec),done:()=>myFleets('siege').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.ec)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!P(1).alive},
    ]},

  catapult:{n:'Catapult',r:'Катапульта',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty'],[3,-1,'empty']],cores:[[0,0],[4,-1]]},
    ids:at=>({T:at(2,0),X:at(1,0)}),center:at=>at(2,0),
    setup:(at,p)=>{p.techs.add('barrack');p.res.iron=20;myFleet('catapult',3,at(1,0));const n=G.nodes[at(2,0)];n.owner=1;const t=newStation(n,'turret',{state:'done'});t.hp=t.maxHp||ST.turret.hp||6;n.stations.push(t);},
    steps:[
      {say:()=>G.moveMode?null:T2('A turret guards that asteroid. Catapults bombard the next tile from safety: 2 damage per catapult, 1 iron a shot.','Этот астероид охраняет турель. Катапульты обстреливают соседнюю клетку издалека: 2 урона с каждой, 1 железо за выстрел.'),
        at:()=>tFleet(myFleets('catapult')[0],'fbomb',TUT.ids.T),done:()=>myFleets('catapult').some(f=>f.bombard===TUT.ids.T)},
      {say:()=>T2('End turns until the turret falls.','Завершайте ходы, пока турель не падёт.'),at:()=>T_dom('#endturn'),end:true,fix:()=>{const f=myFleets('catapult')[0];if(f&&f.bombard==null&&liveTurrets(G.nodes[TUT.ids.T]).length)f.bombard=TUT.ids.T;},done:()=>!liveTurrets(G.nodes[TUT.ids.T]).length},
    ]},

  boomerang:{n:'Boomerang',r:'Бумеранг',workers:0,
    map:{cells:[[1,0,'empty'],[2,0,'empty'],[3,0,'empty']],cores:[[0,0],[5,-1]]},
    ids:at=>({A:at(2,0),B:at(3,0),H:at(1,0)}),center:at=>at(2,0),
    setup:(at,p)=>{p.techs.add('barrack');myFleet('boomerang',4,at(1,0));enemyFleet('interceptor',1,at(2,0));enemyFleet('interceptor',1,at(3,0));},
    steps:[
      {say:()=>G.moveMode||G.popup?null:T2('Attack the closer enemy drone.','Атакуйте ближайший вражеский дрон.'),at:()=>tFleet(myFleets('boomerang')[0],'fmove',TUT.ids.A),done:()=>myFleets('boomerang').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.A)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1&&f.node===TUT.ids.A)},
      {say:()=>G.moveMode||G.popup?null:T2('After a win, boomerangs fly back home. Next turn the tile they attacked costs no hop: reach the far drone, 2 hops away, in one turn.','После победы бумеранги возвращаются. В следующем ходу атакованная клетка не тратит прыжок: долетите до дальнего дрона в 2 прыжках за один ход.'),
        at:()=>tFleet(myFleets('boomerang')[0],'fmove',TUT.ids.B),done:()=>myFleets('boomerang').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.B)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1)},
    ]},

  tank:{n:'Tank',r:'Танк',workers:0,
    map:{cells:[[-3,1,'empty']],planet:{c:[0,0],secs:[[1,0],[-1,0],[0,1],[0,-1],[1,-1],[-1,1]],look:3},cores:[[-2,1],[3,-1]]},
    ids:at=>({P:at(0,0),T:at(-1,1)}),center:at=>at(0,0),
    setup:(at,p)=>{p.techs.add('rovers');p.techs.add('planetmove');myFleet('tank',2,at(-1,1));G.workers.push(newWorker(1,at(0,0)));G.workers.at(-1).task='claim';},
    steps:[
      {say:()=>G.moveMode||G.popup?null:T2('Tanks are rovers: they only drive on their planet. An enemy worker is claiming the centre: drive there.','Танки — роверы: они ездят только по своей планете. Вражеский рабочий захватывает центр: езжайте туда.'),
        at:()=>tFleet(myFleets('tank')[0],'fmove',TUT.ids.P),done:()=>myFleets('tank').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.P)},
      {at:()=>T_dom('#endturn'),end:true,done:()=>!G.workers.some(w=>w.owner===1)},
    ]},

  stomper:{n:'Stomper',r:'Топтун',workers:0,
    map:{cells:[[-3,1,'empty']],planet:{c:[0,0],secs:[[1,0],[-1,0],[0,1],[0,-1],[1,-1],[-1,1]],look:4},cores:[[-2,1],[3,-1]]},
    ids:at=>({B:at(-1,0),S:at(0,-1),E:at(0,0)}),center:at=>at(0,0),
    setup:(at,p)=>{p.techs.add('rovers');p.techs.add('planetmove');myFleet('ballista',2,at(-1,0));myFleet('stomper',2,at(0,-1));enemyFleet('tank',3,at(0,0));},
    steps:[
      {say:()=>G.moveMode||G.popup?null:T2('Enemy tanks will hit your ballistas next turn. Stompers are bulky and take damage first: move yours next to the ballistas.','Вражеские танки ударят по баллистам в следующем ходу. Топтуны крепкие и принимают урон первыми: подведите своего к баллистам.'),
        at:()=>tFleet(myFleets('stomper')[0],'fmove',TUT.ids.B),done:()=>myFleets('stomper').some(f=>(f.path.length?f.path.at(-1):f.node)===TUT.ids.B)},
      {enter:()=>{const e=G.fleets.find(f=>f.owner===1);if(e)e.path=[TUT.ids.B];},at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1)||G.turn>=6},
      {say:()=>T2('The stomper soaked up the tank fire while the ballistas fought.','Топтун принял огонь танков, пока баллисты сражались.'),at:()=>T_tile(TUT.ids.B),next:true},
    ]},
};
"""
rep("function renderTop(){", TUTS + "\nfunction renderTop(){")

# ---------- overlay: only the outline, the bubble, the shine, the big banner ----------
i = s.index('<div id="tut" hidden aria-live="polite">')
j = s.index('<div class="mapctl" id="mapctl"', i)
s = s[:i] + """<div id="tut" hidden aria-live="polite">
      <svg id="tutout" aria-hidden="true"><rect x="2" y="2" pathLength="100"/></svg>
      <div id="tutbub" role="status"><span class="tt"></span><button class="btn small tutnext" type="button" data-a="tut-next">Next</button></div>
      <div id="tutfx"><b></b><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
      <div id="tutbig" hidden></div>
    </div>
    """ + s[j:]
rep("#tutout{position:absolute;overflow:visible}#tutout rect{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:4 4;stroke-dashoffset:100;animation:tuttrace 2s linear infinite;width:calc(100% - 4px);height:calc(100% - 4px)}",
    "#tutout{position:absolute;overflow:visible}#tutout rect{fill:none;stroke:var(--volt);stroke-width:2.2;stroke-dasharray:2.2 2.8;stroke-linecap:round;animation:tutspin 9s linear infinite}\n@keyframes tutspin{to{stroke-dashoffset:-100}}\n#tutbig{position:fixed;left:0;right:0;top:38%;text-align:center;font:900 clamp(40px,9vw,96px)/1 var(--f-display,Impact,sans-serif);color:#ff3b3b;letter-spacing:.06em;text-shadow:0 0 18px rgba(255,40,40,.7),0 4px 0 #400}\n#tutbig.go{animation:tutbig 2.2s ease-out}@keyframes tutbig{0%{transform:scale(2.2);opacity:0}12%{transform:scale(1);opacity:1}80%{opacity:1}100%{opacity:0}}\n.tutrow{display:flex;justify-content:space-between;align-items:center}.tutgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:6px}")
rep("#tutfx{position:absolute;width:0;height:0}#tutfx b{position:absolute;left:-30px;top:-30px;width:60px;height:60px;border-radius:50%;background:#fff;opacity:calc(.9 - var(--k,0)*2)}",
    "#tutfx{position:absolute;width:0;height:0}#tutfx b{position:absolute;left:-34px;top:-34px;width:68px;height:68px;border-radius:50%;background:radial-gradient(circle,rgba(255,216,77,.55),rgba(255,216,77,0) 70%);opacity:calc(1 - var(--k,0))}")

# ---------- menus and actions ----------
rep("    case 'tut-lang':settings.lang=d.v;saveSettings();beginTutorial();break;",
    "    case 'tut-lang':settings.lang=d.v;saveSettings();beginTutorial('starter');break;\n    case 'tut-go':beginTutorial(d.v);break;\n    case 'tut-list':leaveGame();showMenu('tutmenu');break;")
rep("  if(/^([msehjlk]-|acc-|set-|tut-lang|tut-menu)/.test(a))return menuAct(a,d);",
    "  if(/^([msehjlk]-|acc-|set-|tut-lang|tut-menu|tut-go|tut-list)/.test(a))return menuAct(a,d);")
rep("    case 's-tut':startTutorial();break;", "    case 's-tut':showMenu('tutmenu');break;")
rep("  if(view==='signing'){", "  if(view==='tutmenu'){\n    ov.innerHTML=tutMenuHtml();\n  }else if(view==='signing'){")
rep("""<button class="btn" type="button" data-a="s-tut">${L('Replay tutorial','Пройти обучение заново')}</button>""",
    """<button class="btn" type="button" data-a="s-tut">${L('Tutorials','Обучение')}</button>""")
rep("    case 'tut-next':if(TUT&&tutStep()&&tutStep().next)tutAdvance();return;",
    "    case 'tut-next':if(TUT&&tutStep()&&tutStep().next)tutAdvance();return;")
rep("  if(G&&G.tut){if(result==='won'&&TUT){TUT.i=TSTEPS.length;tutFinish();}return;}",
    "  if(G&&G.tut){if(result==='won'&&TUT){tutFinish();}return;}")
# the account remembers which tutorials you finished
rep("  async saveAch(){", "  async saveTuts(){if(this.state!=='in')return;const {doc,updateDoc}=this.m;try{await updateDoc(doc(this.db,'users',this.user.uid),{tuts:profile.tuts||{}});}catch(e){}},\n  async saveAch(){")
rep("profile.ach=Object.assign({},profile.ach||{},d.ach||{});", "profile.ach=Object.assign({},profile.ach||{},d.ach||{});profile.tuts=Object.assign({},profile.tuts||{},d.tuts||{});")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
