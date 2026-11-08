"""Draft 10 stage 7: the tutorial (forced on a new account, replayable from Settings)."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


TUT_JS = r"""
/* ---------- tutorial ----------
   A fixed little Warfare match against a sleeping rival. Each step points at what to press:
   a double ripple on the target (1A), a bobbing arrow (2A), a dotted outline drawn around it (3B),
   a speech bubble next to it (4B), and a flash with sparks when the step is done (5B).
   Research, the Barrack, drones and the leviathan are sped up so it all fits in a few minutes. */
let TUT=null,TUT_SAVE=null;
const tutEl=()=>$('#tut');
// find a map with: core → iron asteroid A → free asteroid Gp → our planet section S → planet centre P, and a free tile X next to the core
function tutLayout(){
  for(let seed=1;seed<3000;seed++){
    newGame({per:12,bots:1,timer:0,mode:'warfare',diff:'easy',seed});
    const core=G.nodes[P(0).core],ec=P(1).core,d=distMap(core.id,null),pl=G.planets[0];if(!pl)continue;
    const Pn=G.nodes[pl.center];if(d.get(Pn.id)!==4||(d.get(ec)||0)<4)continue;
    for(const a of core.nbr){const A=G.nodes[a];if(A.planet!=null||A.type==='core')continue;
      for(const g of A.nbr){const Gn=G.nodes[g];if(Gn.planet!=null||Gn.type==='core'||d.get(g)!==2)continue;
        const S=Gn.nbr.find(x=>G.nodes[x].planet!=null&&!G.nodes[x].center&&G.nodes[x].nbr.includes(Pn.id));if(S==null)continue;
        const X=core.nbr.find(x=>x!==a&&G.nodes[x].planet==null&&G.nodes[x].type!=='core'&&!G.nodes[x].nbr.includes(g));if(X==null)continue;
        return {seed,A:a,Gp:g,S,P:Pn.id,X,ec};}}
  }
  return null;
}
function startTutorial(){showMenu('tutlang');}
function beginTutorial(){
  closeOverlay();
  const L0=tutLayout();if(!L0){showMenu('main');return;}
  G.tut=true;G.turnTime=0;G.timeLeft=0;
  // sped-up rules for the tutorial only (put back when it ends)
  TUT_SAVE={tb:TECH.barrack.c,kt:ST.kazarm.t,lt:ST.levi.t,ls:DR.leviathan.spd};
  TECH.barrack.c=1;ST.kazarm.t=1;ST.levi.t=1;DR.leviathan.spd=30;
  const p=P(ME);for(const r of RES)p.res[r]=25;p.gold=99;
  const A=G.nodes[L0.A];A.type='res';A.res='iron';
  G.nodes[L0.Gp].type='empty';G.nodes[L0.Gp].res=null;
  G.nodes[L0.S].owner=ME;
  G.nodes[L0.ec].coreHp=15;
  p.explored=new Set(G.nodes.map(n=>n.id));
  G.conn=G.players.map(q=>connSet(q.id));
  TUT={i:0,ids:L0,t0:performance.now(),fx:null};
  centerOn(G.nodes[p.core],true);G.sel=p.core;refresh();
  tutLoop();
}
// ---- what to point at ----
const nodeOpen=id=>G.modal&&G.modal.type==='node'&&G.modal.id===id&&!$('#modal').hidden;
const q$=sel=>{const el=document.querySelector(sel);return el&&el.offsetParent!==null?el:null;};
const T_tile=id=>({tile:id}),T_dom=sel=>({dom:sel});
// open tile `from`, press Move on a worker there, then tap tile `to`
function tMove(from,to){if(G.moveMode)return T_tile(to);if(nodeOpen(from)&&q$('[data-a="wmove"]'))return T_dom('[data-a="wmove"]');return T_tile(from);}
function tTask(id,task){if(nodeOpen(id)&&q$(`[data-a="wtask"][data-t="${task}"]`))return T_dom(`[data-a="wtask"][data-t="${task}"]`);return T_tile(id);}
const myWorkers=()=>G.workers.filter(w=>w.owner===ME);
const workerTo=id=>myWorkers().some(w=>(w.path.length?w.path.at(-1):w.node)===id);
const workerAt=id=>myWorkers().some(w=>w.node===id&&!w.path.length);
const T=(en,ru)=>L(en,ru);
const TSTEPS=[
  {say:()=>T('This is your core. Everything you build starts here. Let\'s take a tour.','Это ваше ядро. С него начинается всё, что вы строите. Давайте осмотримся.'),at:()=>T_tile(P(ME).core),next:true},
  {say:()=>G.moveMode?T('Now tap this asteroid to send the worker there.','Теперь нажмите на этот астероид, чтобы отправить туда рабочего.'):nodeOpen(P(ME).core)?T('Press Move next to your worker.','Нажмите «Лететь» рядом с рабочим.'):T('Tap your core twice to open it.','Нажмите на ядро дважды, чтобы открыть его.'),
    at:()=>tMove(P(ME).core,TUT.ids.A),done:()=>workerTo(TUT.ids.A)},
  {say:()=>T('End the turn: everything you ordered happens at once.','Завершите ход: всё, что вы приказали, происходит одновременно.'),at:()=>T_dom('#endturn'),end:true,done:()=>workerAt(TUT.ids.A)},
  {say:()=>nodeOpen(P(ME).core)?T('Build a worker. It appears at the core next turn.','Создайте рабочего. Он появится в ядре в следующем ходу.'):T('Open your core again.','Снова откройте ядро.'),
    at:()=>nodeOpen(P(ME).core)?T_dom('[data-a="hire"]'):T_tile(P(ME).core),done:()=>P(ME).workerQueue>0},
  {say:()=>nodeOpen(TUT.ids.A)?T('Press Claim: the asteroid becomes yours at the end of the turn.','Нажмите «Захватить»: астероид станет вашим в конце хода.'):T('Open the asteroid your worker reached.','Откройте астероид, до которого долетел рабочий.'),
    at:()=>tTask(TUT.ids.A,'claim'),done:()=>myWorkers().some(w=>w.node===TUT.ids.A&&w.task==='claim')||G.nodes[TUT.ids.A].owner===ME},
  {say:()=>T('End the turn to claim it.','Завершите ход, чтобы захватить его.'),at:()=>T_dom('#endturn'),end:true,done:()=>G.nodes[TUT.ids.A].owner===ME},
  {say:()=>nodeOpen(TUT.ids.A)?T('Press Mine: the worker brings in iron every turn.','Нажмите «Добывать»: рабочий будет приносить железо каждый ход.'):T('Open the asteroid again.','Снова откройте астероид.'),
    at:()=>tTask(TUT.ids.A,'mine'),done:()=>myWorkers().some(w=>w.node===TUT.ids.A&&w.task==='mine')},
  {say:()=>!$('#techscr').hidden?(G.popup&&G.popup.type==='tech'&&G.popup.t==='barrack'?T('Assign the worker standing at your core.','Назначьте рабочего, стоящего в ядре.'):T('Pick Barrack in the tech tree.','Выберите «Казарму» в дереве технологий.')):T('Open the tech tree (the F key, or the research row in your core menu).','Откройте дерево технологий (клавиша F или строка исследований в меню ядра).'),
    at:()=>!$('#techscr').hidden?(G.popup&&G.popup.type==='tech'&&G.popup.t==='barrack'?T_dom('[data-a="tset"]'):T_dom('[data-a="techpop"][data-t="barrack"]')):nodeOpen(P(ME).core)?T_dom('[data-a="open"][data-m="tech"]'):T_tile(P(ME).core),
    done:()=>myWorkers().some(w=>w.task==='research'&&w.tech==='barrack')||has(ME,'barrack')},
  {say:()=>T('End the turn. (Research is sped up in the tutorial.)','Завершите ход. (В обучении исследования ускорены.)'),at:()=>T_dom('#endturn'),end:true,done:()=>has(ME,'barrack')},
  {say:()=>nodeOpen(P(ME).core)?T('Start a Barrack here.','Начните строить здесь Казарму.'):T('Open your core.','Откройте ядро.'),
    at:()=>nodeOpen(P(ME).core)?T_dom('[data-a="start"][data-t="kazarm"]'):T_tile(P(ME).core),done:()=>G.nodes[P(ME).core].stations.some(s=>s.type==='kazarm')},
  {say:()=>T('End the turn to finish the Barrack.','Завершите ход, чтобы достроить Казарму.'),at:()=>T_dom('#endturn'),end:true,done:()=>live(G.nodes[P(ME).core],'kazarm').length>0},
  {say:()=>{const m=G.modal;return m&&m.type==='station'?T('Queue an interceptor and a bomber.','Поставьте в очередь перехватчик и бомбер.'):T('Open the Barrack (tap its icon next to the core).','Откройте Казарму (нажмите на её значок у ядра).');},
    at:()=>{const k=live(G.nodes[P(ME).core],'kazarm')[0];const m=G.modal;if(m&&m.type==='station'&&k&&m.uid===k.uid){const q=k.queue;return T_dom(q.includes('interceptor')?'[data-a="kbuild"][data-c="bomber"]':'[data-a="kbuild"][data-c="interceptor"]');}return k?{station:k.uid}:T_tile(P(ME).core);},
    done:()=>{const k=live(G.nodes[P(ME).core],'kazarm')[0];return !!k&&new Set([...k.queue,...CLS.filter(c=>k.hangar[c].length)]).size>=2;}},
  {say:()=>T('End the turn: both drones are built at once here.','Завершите ход: здесь оба дрона строятся сразу.'),at:()=>T_dom('#endturn'),end:true,done:()=>{const k=live(G.nodes[P(ME).core],'kazarm')[0];return !!k&&k.hangar.interceptor.length>0&&k.hangar.bomber.length>0;}},
  {say:()=>G.popup&&G.popup.type==='hangar'?T('Launch them.','Выпустите их.'):T('Press Launch on each drone in the Barrack.','Нажмите «Выпустить» у каждого дрона в Казарме.'),
    at:()=>{if(G.popup&&G.popup.type==='hangar')return T_dom('[data-a="hlaunch"][data-i="-1"]');const k=live(G.nodes[P(ME).core],'kazarm')[0];const m=G.modal;if(m&&m.type==='station'&&k&&m.uid===k.uid)return T_dom(`[data-a="hangar"][data-c="${k.hangar.interceptor.length?'interceptor':'bomber'}"]`);return k?{station:k.uid}:T_tile(P(ME).core);},
    done:()=>G.fleets.filter(f=>f.owner===ME&&f.cls!=='spy').length>=2},
  {say:()=>G.popup&&G.popup.type==='squad'?T('Make them one fleet: fleets move together.','Объедините их во флот: флот движется вместе.'):T('Press and hold the map for a second, then drag a box over both squadrons.','Нажмите на карту и держите секунду, затем протяните рамку через обе эскадрильи.'),
    at:()=>G.popup&&G.popup.type==='squad'?T_dom('[data-a="sqmake"]'):{unit:G.fleets.find(f=>f.owner===ME&&f.cls!=='spy')},done:()=>(P(ME).squads||[]).length>0},
  {enter:()=>{const e=newFleet(1,'interceptor',1,TUT.ids.X,false);G.fleets.push(e);G.flash.add(TUT.ids.X);hitPulse(TUT.ids.X,[],[],'gift');G.pulseT0=performance.now();refresh();},
    say:()=>G.popup&&G.popup.type==='preview'?T('The preview says you would win. Press Move.','Прогноз говорит, что вы победите. Нажмите «Лететь».'):G.moveMode?T('Tap the enemy drone\'s tile.','Нажмите на клетку вражеского дрона.'):G.modal&&G.modal.type==='empire'?T('Press Move on your fleet.','Нажмите «Лететь» у вашего флота.'):T('An enemy drone landed next to your Barrack! Open the Empire menu (the crown).','Вражеский дрон сел рядом с вашей Казармой! Откройте меню «Империя» (корона).'),
    at:()=>G.popup&&G.popup.type==='preview'?T_dom('[data-a="pmove"]'):G.moveMode?T_tile(TUT.ids.X):G.modal&&G.modal.type==='empire'?T_dom('[data-a="sqmove"]'):T_dom('#empireBtn'),
    done:()=>G.fleets.some(f=>f.owner===ME&&f.cls!=='spy'&&(f.path.length?f.path.at(-1):f.node)===TUT.ids.X)},
  {say:()=>T('End the turn to attack.','Завершите ход, чтобы атаковать.'),at:()=>T_dom('#endturn'),end:true,done:()=>!G.fleets.some(f=>f.owner===1)},
  {say:()=>G.moveMode?T('Tap the planet centre.','Нажмите на центр планеты.'):T('Planets hold jopium. Send your new worker to the planet centre: open the core, press Move.','На планетах есть жопиум. Отправьте нового рабочего в центр планеты: откройте ядро, нажмите «Лететь».'),
    at:()=>workerTo(TUT.ids.P)?null:tMove(P(ME).core,TUT.ids.P),done:()=>workerTo(TUT.ids.P)},
  {say:()=>T('End turns until the worker arrives.','Завершайте ходы, пока рабочий не долетит.'),at:()=>T_dom('#endturn'),end:true,done:()=>workerAt(TUT.ids.P)},
  {say:()=>nodeOpen(TUT.ids.P)?T('Claim the planet centre.','Захватите центр планеты.'):T('Open the planet centre.','Откройте центр планеты.'),at:()=>tTask(TUT.ids.P,'claim'),done:()=>myWorkers().some(w=>w.node===TUT.ids.P&&w.task==='claim')||G.nodes[TUT.ids.P].owner===ME},
  {say:()=>T('End the turn to claim it.','Завершите ход, чтобы захватить его.'),at:()=>T_dom('#endturn'),end:true,done:()=>G.nodes[TUT.ids.P].owner===ME},
  {say:()=>T('See the red cross? The centre is cut off: one free asteroid separates it from your network, so its jopium can\'t reach your core.','Видите красный крестик? Центр отрезан: между ним и вашей сетью есть свободный астероид, поэтому жопиум не доходит до ядра.'),at:()=>T_tile(TUT.ids.P),next:true},
  {say:()=>{const g=TUT.ids.Gp;if(workerAt(g))return nodeOpen(g)?T('Claim it.','Захватите его.'):T('Open this asteroid and claim it.','Откройте этот астероид и захватите его.');return G.moveMode?T('Tap the gap asteroid.','Нажмите на астероид-разрыв.'):T('Send the miner from your iron asteroid to the gap: open the iron asteroid, press Move.','Отправьте шахтёра с железного астероида в разрыв: откройте железный астероид, нажмите «Лететь».');},
    at:()=>{const g=TUT.ids.Gp;if(workerAt(g))return tTask(g,'claim');if(workerTo(g))return T_dom('#endturn');return tMove(TUT.ids.A,g);},end:true,done:()=>G.nodes[TUT.ids.Gp].owner===ME&&G.conn[ME].has(TUT.ids.P)},
  {say:()=>nodeOpen(TUT.ids.P)?T('Mine jopium. You have 99: one more makes 100, enough for a leviathan.','Добывайте жопиум. У вас 99: ещё один — и будет 100, хватит на левиафана.'):T('Open the planet centre.','Откройте центр планеты.'),
    at:()=>tTask(TUT.ids.P,'mine'),done:()=>myWorkers().some(w=>w.node===TUT.ids.P&&w.task==='mine')||P(ME).gold>=100},
  {say:()=>T('End the turn.','Завершите ход.'),at:()=>T_dom('#endturn'),end:true,done:()=>P(ME).gold>=100},
  {say:()=>nodeOpen(TUT.ids.P)?T('Build a Leviathan. The worker who finishes it becomes its pilot.','Постройте Левиафана. Рабочий, который его достроит, станет пилотом.'):T('Open the planet centre.','Откройте центр планеты.'),
    at:()=>nodeOpen(TUT.ids.P)?T_dom('[data-a="start"][data-t="levi"]'):T_tile(TUT.ids.P),done:()=>G.nodes[TUT.ids.P].stations.some(s=>s.type==='levi')||G.fleets.some(f=>f.owner===ME&&f.cls==='leviathan')},
  {say:()=>T('End the turn. (It builds in one turn here.)','Завершите ход. (Здесь он строится за один ход.)'),at:()=>T_dom('#endturn'),end:true,done:()=>G.fleets.some(f=>f.owner===ME&&f.cls==='leviathan')},
  {say:()=>G.popup&&G.popup.type==='preview'?T('Press Move.','Нажмите «Лететь».'):G.moveMode?T('Tap the enemy core.','Нажмите на вражеское ядро.'):G.modal&&G.modal.type==='unit'?T('Press Move.','Нажмите «Лететь».'):T('Tap your leviathan.','Нажмите на своего левиафана.'),
    at:()=>{const lv=G.fleets.find(f=>f.owner===ME&&f.cls==='leviathan');if(G.popup&&G.popup.type==='preview')return T_dom('[data-a="pmove"]');if(G.moveMode)return T_tile(TUT.ids.ec);if(G.modal&&G.modal.type==='unit')return T_dom('[data-a="fmove"]');return {unit:lv};},
    done:()=>G.fleets.some(f=>f.owner===ME&&f.cls==='leviathan'&&(f.path.length?f.path.at(-1):f.node)===TUT.ids.ec)},
  {say:()=>T('End the turn and destroy the enemy core.','Завершите ход и уничтожьте вражеское ядро.'),at:()=>T_dom('#endturn'),end:true,done:()=>!P(1).alive},
];
const tutStep=()=>TUT&&TSTEPS[TUT.i];
const tutAllowsEnd=()=>!TUT||!!(tutStep()&&tutStep().end);
// where the current target is on screen: {x,y,w,h} in page pixels
function tutRect(t){
  if(!t)return null;
  if(t.dom){const el=q$(t.dom);if(!el)return null;const r=el.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width+10,h:r.height+10,round:false};}
  const cr=cv.getBoundingClientRect();
  if(t.tile!=null){const n=G.nodes[t.tile];const [x,y]=toScreen(n.x,n.y);const d=R*cam.z*1.25;return {x:cr.left+x,y:cr.top+y,w:d,h:d,round:true};}
  if(t.unit){const h=G.hits.find(h=>h.kind==='fleet'&&h.u===t.unit);if(!h)return null;return {x:cr.left+h.x,y:cr.top+h.y,w:h.r*2.4,h:h.r*2.4,round:true};}
  if(t.station!=null){const h=G.hits.find(h=>h.kind==='station'&&h.s.uid===t.station);if(!h)return null;return {x:cr.left+h.x,y:cr.top+h.y,w:h.r*2.6,h:h.r*2.6,round:true};}
  return null;
}
function tutAdvance(){
  const st=tutStep();const r=TUT.lastRect;if(r)TUT.fx={x:r.x,y:r.y,t:performance.now()};
  TUT.i++;TUT.t0=performance.now();sfxTurn();
  const nx=tutStep();if(nx&&nx.enter)nx.enter();
  if(!nx)tutFinish();
}
function tutLoop(){
  if(!TUT||!G||!G.tut){const el=tutEl();if(el)el.hidden=true;return;}
  const el=tutEl(),st=tutStep();
  if(!st){el.hidden=true;return;}
  if(st.done&&st.done()){tutAdvance();requestAnimationFrame(tutLoop);return;}
  el.hidden=false;
  const r=tutRect(st.at());TUT.lastRect=r||TUT.lastRect;
  const ring=$('#tutring'),arr=$('#tutarrow'),out=$('#tutout'),bub=$('#tutbub'),fx=$('#tutfx');
  for(const e of [ring,arr,out])e.hidden=!r;
  if(r){
    ring.style.left=r.x+'px';ring.style.top=r.y+'px';
    const up=r.y-r.h/2<90;arr.style.left=r.x+'px';arr.style.top=(up?r.y+r.h/2+8:r.y-r.h/2-40)+'px';arr.classList.toggle('up',up);
    out.style.left=(r.x-r.w/2-6)+'px';out.style.top=(r.y-r.h/2-6)+'px';out.style.width=(r.w+12)+'px';out.style.height=(r.h+12)+'px';out.querySelector('rect').setAttribute('rx',r.round?(r.w+12)/2:10);
  }
  // the speech bubble: next to the target, on whichever side has room
  const txt=st.say();if(bub.dataset.k!==TUT.i+'|'+txt){bub.dataset.k=TUT.i+'|'+txt;bub.querySelector('.tt').textContent=txt;bub.querySelector('.tn').hidden=!st.next;bub.classList.remove('pop');void bub.offsetWidth;bub.classList.add('pop');}
  const bw=bub.offsetWidth,bh=bub.offsetHeight,vw=innerWidth,vh=innerHeight;
  let bx,by;
  if(r){const right=r.x+r.w/2+16+bw<vw-8;bx=right?r.x+r.w/2+16:r.x-r.w/2-16-bw;by=r.y-bh/2;if(bx<8){bx=Math.max(8,Math.min(vw-bw-8,r.x-bw/2));by=r.y+r.h/2+44;if(by+bh>vh-8)by=r.y-r.h/2-bh-48;}bub.classList.toggle('left',!right);}
  else{bx=(vw-bw)/2;by=vh-bh-90;}
  bub.style.left=Math.max(8,Math.min(vw-bw-8,bx))+'px';bub.style.top=Math.max(8,Math.min(vh-bh-8,by))+'px';
  // step done: a white flash and sparks where the last target was
  if(TUT.fx){const k=(performance.now()-TUT.fx.t)/900;if(k>1){TUT.fx=null;fx.hidden=true;}else{fx.hidden=false;fx.style.left=TUT.fx.x+'px';fx.style.top=TUT.fx.y+'px';fx.style.setProperty('--k',k);}}
  requestAnimationFrame(tutLoop);
}
function tutFinish(){
  restoreTutRules();
  const el=tutEl();if(el)el.hidden=true;
  TUT=null;Acc.tutDone();
  if(G){G.tut=false;G.over=true;}
  ov.hidden=false;ov.className='dim';ov.dataset.view='tutdone';
  ov.innerHTML=`<div class="card"><h1>${L('Tutorial complete','Обучение пройдено')}</h1><p>${L('You moved, claimed, mined, researched, built a Barrack and drones, made a fleet, linked a planet and flew a leviathan into the enemy core. You can replay this any time from Settings.','Вы летали, захватывали, добывали, исследовали, построили Казарму и дронов, собрали флот, подключили планету и разбили вражеское ядро левиафаном. Пройти обучение заново можно в Настройках.')}</p><div class="opts"><button class="btn primary" type="button" data-a="tut-menu">${L('To the main menu','В главное меню')}</button></div></div>`;
}
function restoreTutRules(){if(TUT_SAVE){TECH.barrack.c=TUT_SAVE.tb;ST.kazarm.t=TUT_SAVE.kt;ST.levi.t=TUT_SAVE.lt;DR.leviathan.spd=TUT_SAVE.ls;TUT_SAVE=null;}}
// leaving the tutorial early: ask first
function tutSkip(){G.popup={type:'tutskip'};G.popupAt=performance.now();renderPopup();}
"""

rep("function renderTop(){", TUT_JS + "\nfunction renderTop(){")

# the overlay layer
rep("""    <div class="mapctl" id="mapctl" hidden>""",
    """    <div id="tut" hidden aria-live="polite">
      <div id="tutring"><i></i><i></i></div>
      <div id="tutarrow" aria-hidden="true"></div>
      <svg id="tutout" aria-hidden="true"><rect x="2" y="2" width="calc(100% - 4px)" height="calc(100% - 4px)" pathLength="100"/></svg>
      <div id="tutbub" role="status"><span class="tt"></span><button class="btn small tn" type="button" data-a="tut-next">Next</button></div>
      <div id="tutfx"><b></b><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
    </div>
    <div class="mapctl" id="mapctl" hidden>""")
rep(".gbtn{", r"""#tut{position:fixed;inset:0;pointer-events:none;z-index:60}
#tutring{position:absolute;width:0;height:0}#tutring i{position:absolute;left:-36px;top:-36px;width:72px;height:72px;border:2.5px solid var(--accent);border-radius:50%;animation:tutrip 1.5s ease-out infinite}#tutring i+i{animation-delay:.35s}
@keyframes tutrip{0%{transform:scale(.3);opacity:.9}100%{transform:scale(1.6);opacity:0}}
#tutarrow{position:absolute;width:0;height:0;margin-left:-12px;border-left:12px solid transparent;border-right:12px solid transparent;border-top:18px solid var(--volt);animation:tutbob .9s ease-in-out infinite}
#tutarrow::before{content:"";position:absolute;left:-5px;top:-34px;width:10px;height:17px;background:var(--volt)}
#tutarrow.up{transform:rotate(180deg);animation-name:tutbobu}
@keyframes tutbob{0%,100%{translate:0 0}50%{translate:0 10px}}@keyframes tutbobu{0%,100%{translate:0 0}50%{translate:0 -10px}}
#tutout{position:absolute;overflow:visible}#tutout rect{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:4 4;stroke-dashoffset:100;animation:tuttrace 2s linear infinite;width:calc(100% - 4px);height:calc(100% - 4px)}
@keyframes tuttrace{0%{stroke-dashoffset:100;opacity:1}70%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
#tutbub{position:absolute;max-width:min(320px,calc(100vw - 32px));background:var(--panel);border:1px solid var(--accent);border-radius:10px;padding:9px 12px;color:var(--fg);font-size:14px;line-height:1.4;pointer-events:auto;display:grid;gap:8px;box-shadow:0 8px 30px rgba(0,0,0,.5)}
#tutbub.pop{animation:tutpop .35s ease-out}@keyframes tutpop{0%{transform:scale(0);opacity:0}60%{transform:scale(1.08);opacity:1}100%{transform:scale(1)}}
#tutbub .tn{justify-self:end}
#tutfx{position:absolute;width:0;height:0}#tutfx b{position:absolute;left:-30px;top:-30px;width:60px;height:60px;border-radius:50%;background:#fff;opacity:calc(.9 - var(--k,0)*2)}
#tutfx i{position:absolute;width:6px;height:6px;margin:-3px;border-radius:50%;background:var(--volt);opacity:calc(1 - var(--k,0));translate:calc(cos(var(--a)) * var(--k,0) * 70px) calc(sin(var(--a)) * var(--k,0) * 56px)}
#tutfx i:nth-of-type(1){--a:0deg}#tutfx i:nth-of-type(2){--a:45deg}#tutfx i:nth-of-type(3){--a:90deg}#tutfx i:nth-of-type(4){--a:135deg}#tutfx i:nth-of-type(5){--a:180deg}#tutfx i:nth-of-type(6){--a:225deg}#tutfx i:nth-of-type(7){--a:270deg}#tutfx i:nth-of-type(8){--a:315deg}
.gbtn{""")

# language choice before it starts
rep("  if(view==='login'){", """  if(view==='tutlang'){
    ov.innerHTML=`<div class="card"><h1>${L('Tutorial','Обучение')}</h1><p style="text-align:center;margin:0">Choose your language · Выберите язык</p>
      <div class="mbtns"><button class="btn" type="button" data-a="tut-lang" data-v="en">English</button><button class="btn" type="button" data-a="tut-lang" data-v="ru">Русский</button></div></div>`;
  }else if(view==='login'){""")
rep("    case 'acc-in':Acc.signIn();break;",
    "    case 'acc-in':Acc.signIn();break;\n    case 'tut-lang':settings.lang=d.v;saveSettings();beginTutorial();break;\n    case 'tut-menu':leaveGame();showMenu('main');break;")
# Settings → General: replay the tutorial
rep("""      <div class="opts"><button class="btn primary" type="button" data-a="m-back">${menuFrom==='game'?L('Back to game','Вернуться в игру'):L('Back','Назад')}</button></div></div>`;
  }else if(view==='closed'){""",
    """      ${menuFrom==='game'?'':`<div class="field"><button class="btn" type="button" data-a="s-tut">${L('Replay tutorial','Пройти обучение заново')}</button></div>`}
      <div class="opts"><button class="btn primary" type="button" data-a="m-back">${menuFrom==='game'?L('Back to game','Вернуться в игру'):L('Back','Назад')}</button></div></div>`;
  }else if(view==='closed'){""")
rep("    case 'set-tab':", "    case 's-tut':startTutorial();break;\n    case 'set-tab':")
# in-game clicks: Next in the bubble, the skip confirmation
rep("    case 'chg':if(G.popup&&G.popup.type==='charge')G.popup.cr=+d.k;break;",
    """    case 'chg':if(G.popup&&G.popup.type==='charge')G.popup.cr=+d.k;break;
    case 'tut-next':if(TUT&&tutStep()&&tutStep().next)tutAdvance();return;
    case 'tut-skip':{G.popup=null;restoreTutRules();TUT=null;const el=tutEl();if(el)el.hidden=true;Acc.tutDone();leaveGame();showMenu('main');toast(L('Tutorial skipped. You can replay it from Settings.','Обучение пропущено. Его можно пройти заново в Настройках.'));return;}""")
rep("  }else if(m.type==='charge'){", """  }else if(m.type==='tutskip'){
    h+=`<h2>${L('Skip the tutorial?','Пропустить обучение?')}</h2><p class="sub" style="margin:0">${L('You can replay it any time: Settings → Replay tutorial.','Его всегда можно пройти заново: Настройки → «Пройти обучение заново».')}</p><div class="opts"><button class="btn danger" type="button" data-a="tut-skip">${L('Skip tutorial','Пропустить')}</button><button class="btn primary" type="button" data-a="pclose">${L('Keep learning','Продолжить')}</button></div>`;
  }else if(m.type==='charge'){""")
# the Resign button reads "Menu" in the tutorial
rep("  $('#resign').textContent=G.over?L('Game menu','Меню игры'):L('Resign','Сдаться');",
    "  $('#resign').textContent=G.tut?L('Menu','Меню'):G.over?L('Game menu','Меню игры'):L('Resign','Сдаться');")
rep("$('#resign').onclick=()=>{if(!G)return;", "$('#resign').onclick=()=>{if(!G)return;if(G.tut){tutSkip();return;}")
# End turn only when the step allows it
rep("function endTurn(auto){", "function endTurn(auto){\n  if(G&&G.tut&&!tutAllowsEnd()){if(!auto){sfxError();toast(L('Follow the highlighted step first.','Сначала выполните подсвеченный шаг.'),true);}return;}")
# the sleeping rival: no AI turns in the tutorial
rep("  G.players.filter(p=>p.ai&&p.alive).forEach(aiTurn);", "  if(!G.tut)G.players.filter(p=>p.ai&&p.alive).forEach(aiTurn);")
# Barrack builds everything queued in one turn in the tutorial
rep("    if(st.queue.length){const c=st.queue[0];st.qprog=(st.qprog||0)+1;if(st.qprog>=(DR[c].build||1)){st.queue.shift();st.qprog=0;st.hangar[c].push(newDrone(c));st.last=c;}}",
    "    for(let k=0;k<(G.tut?9:1)&&st.queue.length;k++){const c=st.queue[0];st.qprog=G.tut?99:(st.qprog||0)+1;if(st.qprog>=(DR[c].build||1)){st.queue.shift();st.qprog=0;st.hangar[c].push(newDrone(c));st.last=c;}}")
# winning the tutorial ends it with its own card
rep("function endGame(result){", "function endGame(result){\n  if(G&&G.tut){if(result==='won'&&TUT){TUT.i=TSTEPS.length;tutFinish();}return;}")
# guests (the claude.ai copy) also get the tutorial on their first visit
rep("resize();showMenu(Acc.state==='guest'?'main':'login');Acc.init();",
    "resize();showMenu(Acc.state==='guest'?(profile.tut?'main':'tutlang'):'login');Acc.init();")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
