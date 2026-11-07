"""Draft 9: full damage order (turrets and workers inside it), boomerangs, leviathan pilots, charger links, battle preview."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:80]}')
    s = s.replace(a, b)


def cut(start, end, new):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + new + s[b:]


cut("function fight(n,fleets,where){", "const REV_PRI=", r"""// Draft 9 damage order, first hit first. Turrets, workers and the core take their place in it.
const HIT_ORDER=['leviathan','stomper','tank','ballista','frigate','catapult','bomber','interceptor','siege','t:chain','t:turret','t:xray','t:death','boomerang','spy','repair','charger','worker','core'];
// the free tile next to n closest to pid's core, where a boomerang sends a rescued unit
function rescueTile(pid,n){
  const d=distMap(P(pid).core);let best=null,bd=Infinity;
  for(const id of n.nbr){if(hostileAt(pid,id))continue;const x=d.get(id)??99;if(x<bd){bd=x;best=id;}}
  return best;
}
function fight(n,fleets,where){
  // sides: each player present with war drones, plus the tile owner's turrets and core
  const sides=new Map();
  const side=pid=>{if(!sides.has(pid))sides.set(pid,{pid,fleets:[],turrets:[],core:null,workers:[],boom:0,rescued:false,saved:[]});return sides.get(pid);};
  for(const f of fleets)if(f.cls!=='spy')side(f.owner).fleets.push(f);
  const owner=n?n.owner:null;
  if(n&&owner!=null&&[...sides.keys()].some(p=>p!==owner)){
    const t=liveTurrets(n);const core=n.type==='core'&&n.coreHp>0?n:null;
    if(t.length||core){const s=side(owner);s.turrets=t;s.core=core;
      // each turret uses 1 energy per battle; without it, it can't fire
      for(const x of t)x.pw=x.type!=='death'&&payEnergy(owner,n.id,1);}
  }
  if(sides.size<2)return false;
  // workers on the tile take part for their side: 1 health, no damage
  if(n)for(const w of G.workers)if(w.node===n.id&&sides.has(w.owner))side(w.owner).workers.push({w,hp:1});
  for(const s of sides.values())s.boom=s.fleets.filter(f=>f.cls==='boomerang').reduce((a,f)=>a+f.count,0);
  const before=[...sides.values()].map(s=>({pid:s.pid,f:s.fleets.map(f=>[f,f.count]),t:s.turrets.map(t=>t),core:s.core?s.core.coreHp:null}));
  // barrier (first round only), minus barriers switched off by upgraded siege drones
  let barrier=0,off=0;
  if(n&&owner!=null&&sides.has(owner)){
    const b=live(n,'barrier').filter(x=>x.pw).length;
    const up=fleets.filter(f=>f.owner!==owner&&f.cls==='siege'&&f.up).reduce((a,f)=>a+f.count,0);
    off=Math.min(b,up);barrier=10*(b-off);
  }
  // upgraded frigates that held their ground this turn get extra health
  for(const s of sides.values())for(const f of s.fleets)if(f.cls==='frigate'&&f.up&&(!f.trail||f.trail.length<=1))f.buf=f.count;
  const alive=s=>s.fleets.some(f=>f.hp>0)||s.turrets.some(t=>t.hp>0)||(s.core&&s.core.coreHp>0);
  // a boomerang side that has lost every boomerang sends one unit per fallen boomerang to safety
  const rescue=s=>{
    const dest=rescueTile(s.pid,n);if(dest==null)return;
    for(let i=0;i<s.boom;i++){
      let ok=false;
      for(const c of ['charger','repair']){const f=s.fleets.find(f=>f.cls===c&&f.hp>0&&f.count>0);if(f){const d=takeDrone(f);if(f.count<=0)f.hp=0;launchDrones(s.pid,c,dest,[d]);s.saved.push(dN(c));ok=true;break;}}
      if(!ok){const w=s.workers.find(x=>x.hp>0);if(w){w.hp=0;w.saved=true;w.w.node=dest;w.w.path=[];w.w.task='idle';w.w.then=null;s.saved.push(w.w.name);ok=true;}}
      if(!ok){const f=G.fleets.find(f=>f.owner===s.pid&&f.node===n.id&&f.cls==='spy'&&f.count>0);if(f){const d=takeDrone(f);launchDrones(s.pid,'spy',dest,[d]);s.saved.push(dN('spy'));ok=true;}}
      if(!ok)break;
    }
  };
  let rounds=0;
  for(;rounds<60;rounds++){
    const act=[...sides.values()].filter(alive);
    if(act.length<2)break;
    const inc=new Map(act.map(s=>[s.pid,{gen:0,str:0,chain:0}]));
    let any=false;
    for(const s of act){
      const enemies=act.filter(o=>o!==s);
      const maxEnemy=Math.max(0,...enemies.flatMap(o=>o.fleets.filter(f=>f.hp>0).map(f=>f.count)));
      let gen=0,str=0,chain=0;
      for(const f of s.fleets){if(f.hp<=0)continue;const D=DR[f.cls];let d=D.dmg;if(f.cls==='bomber'&&maxEnemy>0&&f.count>maxEnemy)d=3;if(f.cls==='boomerang'&&f.up&&f.viaFree)d+=2;const k=poweredDrones(f);gen+=d*k;if(f.cls==='siege')str+=(D.sdmg-D.dmg)*k;}
      for(const t of s.turrets){if(t.hp<=0||!t.pw)continue;gen+=ST[t.type].dmg||0;if(t.type==='chain')chain++;}
      if(s.core&&s.core.coreHp>0)gen+=2;
      if(gen+str+chain>0)any=true;
      for(const o of enemies){const x=inc.get(o.pid);x.gen+=gen/enemies.length;x.str+=str/enemies.length;x.chain+=chain;}
    }
    if(!any)break;
    for(const s of act){
      const x=inc.get(s.pid);let gen=x.gen,str=x.str;
      if(rounds===0&&s.pid===owner&&barrier>0){const a=Math.min(barrier,gen);gen-=a;const b=Math.min(barrier-a,str);str-=b;}
      // chain turrets: 1 damage to each enemy fleet per chain turret
      if(x.chain)for(const f of s.fleets)if(f.hp>0){const d=Math.min(f.buf,x.chain);f.buf-=d;f.hp-=x.chain-d;}
      // everything on this side, in the order it takes damage; siege bonus damage only lands on turrets and the core
      const tg=[];
      for(const f of s.fleets)if(f.hp>0)tg.push({k:HIT_ORDER.indexOf(f.cls),f});
      for(const t of s.turrets)if(t.hp>0)tg.push({k:HIT_ORDER.indexOf('t:'+t.type),t});
      for(const w of s.workers)if(w.hp>0)tg.push({k:HIT_ORDER.indexOf('worker'),w});
      if(s.core&&s.core.coreHp>0)tg.push({k:HIT_ORDER.length-1,c:s.core});
      tg.sort((a,b)=>a.k-b.k);
      for(const t of tg){
        if(gen<=1e-9&&str<=1e-9)break;
        if(t.f){const f=t.f;if(gen<=0)continue;if(f.buf>0){const d=Math.min(f.buf,gen);f.buf-=d;gen-=d;}const d=Math.min(f.hp,gen);f.hp-=d;gen-=d;}
        else if(t.w){if(gen<=0)continue;const d=Math.min(t.w.hp,gen);t.w.hp-=d;gen-=d;}
        else{const o=t.t||t.c,hp=t.t?o.hp:o.coreHp,a=Math.min(hp,str);str-=a;const b=Math.min(hp-a,gen);gen-=b;if(t.t)o.hp-=a+b;else o.coreHp-=a+b;}
      }
      s.fleets.forEach(syncFleet);
      // repair drones patch the front-line fleet each round
      const rep=s.fleets.filter(f=>f.cls==='repair'&&f.hp>0).reduce((a,f)=>a+f.count,0);
      if(rep){const front=s.fleets.filter(f=>f.hp>0).sort((a,b)=>DRONE_PRI.indexOf(a.cls)-DRONE_PRI.indexOf(b.cls))[0];if(front)front.hp=Math.min(fleetMax(front),front.hp+rep);}
      if(s.boom>0&&!s.rescued&&!s.fleets.some(f=>f.cls==='boomerang'&&f.hp>0)){s.rescued=true;if(n)rescue(s);}
    }
  }
  for(const s of sides.values())for(const f of s.fleets)f.buf=0;
  // workers who fell in the battle
  const deadW=new Set();for(const s of sides.values())for(const w of s.workers)if(w.hp<=0&&!w.saved)deadW.add(w.w);
  // report
  const parts=before.map(b=>{
    const lost=[],sd=sides.get(b.pid);
    for(const [f,c] of b.f){const k=f.hp<=0?c:c-f.count;if(k>0)lost.push(dCount(k,f.cls));if(f.cls==='leviathan'&&f.hp<=0&&f.pilot)lost.push(L(`pilot ${f.pilot}`,`пилот ${f.pilot}`));}
    for(const t of b.t)if(t.hp<=0)lost.push(lc(sN(t.type)));
    const wl=sd.workers.filter(w=>deadW.has(w.w)).map(w=>w.w.name);if(wl.length)lost.push(L(`worker${wl.length>1?'s':''} ${wl.join(', ')}`,`рабоч${wl.length>1?'ие':'ий'} ${wl.join(', ')}`));
    if(b.core!=null){const c=sd.core;if(c&&c.coreHp<b.core)lost.push(L(`${Math.round(b.core-Math.max(0,c.coreHp))} core health`,`${Math.round(b.core-Math.max(0,c.coreHp))} здоровья ядра`));}
    const sv=sd.saved.length?L(`; boomerangs saved ${sd.saved.join(', ')}`,`; бумеранги спасли: ${sd.saved.join(', ')}`):'';
    return L(`${pShort(P(b.pid))} lost ${lost.length?lost.join(', '):'nothing'}`,`${pShort(P(b.pid))}: ${lost.length?'потери — '+lost.join(', '):'без потерь'}`)+sv;
  });
  const winner=[...sides.values()].filter(alive);
  // a short summary for the battle preview
  G.lastFight={win:winner.map(s=>s.pid),sides:[...sides.values()].map(s=>({pid:s.pid,fleets:s.fleets.filter(f=>f.hp>0).map(f=>[f.cls,f.count]),workers:s.workers.filter(w=>w.hp>0).length,turrets:s.turrets.filter(t=>t.hp>0).map(t=>t.type),core:s.core?Math.max(0,Math.round(s.core.coreHp)):null,saved:s.saved}))};
  const verdict=winner.length===1?L(`${pShort(P(winner[0].pid))} won`,`Победа: ${pShort(P(winner[0].pid))}`):winner.length===0?L('Both sides were wiped out','Обе стороны уничтожены'):L('No side could finish the fight','Никто не смог завершить бой');
  log(L(`Battle ${where}: ${verdict} after ${plural(Math.max(1,rounds),'round')}. ${parts.join('; ')}.${off?` Upgraded siege drones switched off ${plural(off,'electric barrier')}.`:''}`,`Бой — ${where}. ${verdict} (${cnt(Math.max(1,rounds),'round')}). ${parts.join('; ')}.${off?` Улучшенные осады отключили: ${cnt(off,'electric barrier')}.`:''}`),'battle',n?n.id:null,[...sides.keys()]);
  G.fleets=G.fleets.filter(f=>f.hp>0);
  if(deadW.size)G.workers=G.workers.filter(w=>!deadW.has(w));
  if(n){n.stations=n.stations.filter(s=>!(isTurret(s.type)&&s.state==='done'&&s.hp<=0));G.flash.add(n.id);(G.battleAt=G.battleAt||new Set()).add(n.id);if(n.type==='core'&&n.coreHp<=0)coreFall(n);}
  return true;
}
""")

# ---------------------------------------------------------------- boomerangs: free hop next turn, return home after a win
rep("  const wBefore=G.workers.map(w=>[w.id,w.owner]);",
    "  const wBefore=G.workers.map(w=>[w.id,w.owner]);\n  G.battleAt=new Set();\n  for(const f of G.fleets){f.viaFree=false;f.hopFree=f.freeHop;f.freeHop=null;}")
rep("    if(f.up&&f.cls==='interceptor'&&G.nodes[f.node].owner===f.owner)steps=3;",
    "    if(f.up&&f.cls==='interceptor'&&G.nodes[f.node].owner===f.owner)steps=3;\n    // a boomerang passing back through the tile it attacked last turn gets that hop for free\n    if(f.cls==='boomerang'&&f.hopFree!=null&&f.path.includes(f.hopFree)){steps++;f.viaFree=true;}")
rep("  // spies caught by enemy war drones or X-ray turrets",
    """  // boomerangs that won a battle fly back to the tile they attacked from; next turn that battle tile is a free hop
  for(const f of G.fleets)if(f.cls==='boomerang'&&f.trail&&f.trail.length>1&&G.battleAt.has(f.node)&&!hostileAt(f.owner,f.node)){
    const back=f.trail[f.trail.length-2];f.freeHop=f.node;f.node=back;f.trail.push(back);f.path=[];
  }
  // spies caught by enemy war drones or X-ray turrets""")

# ---------------------------------------------------------------- leviathan pilots die with it (the pilot is not a free worker)
# ---------------------------------------------------------------- upgraded chargers link their unclaimed tile to the network
rep("function bfsOwned(pid,start){const s=new Set([start]);const q=[start];while(q.length){const id=q.shift();for(const nb of G.nodes[id].nbr)if(!s.has(nb)&&G.nodes[nb].owner===pid){s.add(nb);q.push(nb);}}return s;}",
    "// a settled, upgraded charger on an unclaimed tile links that tile into its owner's network\nconst chargerLink=(pid,id)=>G.nodes[id].owner==null&&G.fleets.some(f=>f.owner===pid&&f.cls==='charger'&&f.up&&f.settled&&f.node===id);\nfunction bfsOwned(pid,start){const s=new Set([start]);const q=[start];while(q.length){const id=q.shift();for(const nb of G.nodes[id].nbr)if(!s.has(nb)&&(G.nodes[nb].owner===pid||chargerLink(pid,nb))){s.add(nb);q.push(nb);}}return s;}")
rep("function clusterOf(pid,id){return [...bfsOwned(pid,id)].map(x=>G.nodes[x]);}",
    "function clusterOf(pid,id){return [...bfsOwned(pid,id)].map(x=>G.nodes[x]).filter(x=>x.owner===pid);}")
# the linked tile is drawn with a dotted ring
rep("  ctx.setLineDash([]);\n  // electric barriers replace",
    "  ctx.setLineDash([]);\n  for(const f of G.fleets)if(f.cls==='charger'&&f.up&&f.settled&&V.has(f.node)&&chargerLink(f.owner,f.node)){const n=G.nodes[f.node];const [x,y]=toScreen(n.x,n.y);ctx.beginPath();ctx.arc(x,y,R*z*.96,0,Math.PI*2);ctx.setLineDash([3,6]);ctx.strokeStyle=hexa(P(f.owner).color,.75);ctx.lineWidth=1.6;ctx.stroke();ctx.setLineDash([]);}\n  // electric barriers replace")

# ---------------------------------------------------------------- battle preview when ordering a fleet onto enemies
rep("else if(mm.u.cls)order({t:'fmove',f:mm.u.id,to:id});",
    "else if(mm.u.cls){if(mm.u.cls!=='spy'&&enemiesAt(id))openPreview(mm.u,id);else order({t:'fmove',f:mm.u.id,to:id});}")
rep("function openUnit(u){", r"""// is there something hostile you can see on tile id (fleets, turrets, a core or workers)?
function enemiesAt(id){
  const V=vis(ME),n=G.nodes[id];if(!V.has(id))return false;
  return G.fleets.some(f=>f.node===id&&f.owner!==ME&&f.cls!=='spy'&&unitVisible(f,V))||(n.owner!=null&&n.owner!==ME&&(liveTurrets(n).length||(n.type==='core'&&n.coreHp>0)))||G.workers.some(w=>w.node===id&&w.owner!==ME);
}
// fight the battle on a copy of the match, with only what you can see, to estimate the result
function previewBattle(f,to){
  const keep={G,UID,RNG},V=vis(ME);let res=null;
  const g2={};for(const k in G)if(!['hits','modal','popup','moveMode','hoverPath','anim','flash','log','seenTech','lastFight'].includes(k))g2[k]=G[k];
  try{
    REPLAY=true;G=Object.assign(structuredClone(g2),{log:[],flash:new Set(),hits:[],seenTech:new Set()});
    G.fleets=G.fleets.filter(x=>x.owner===ME||x.cls!=='spy'&&(x.node!==to||unitVisible(x,V)));
    const fc=G.fleets.find(x=>x.id===f.id);fc.node=to;fc.path=[];fc.trail=[f.node,to];
    const n=G.nodes[to],enemyW=G.workers.filter(w=>w.node===to&&w.owner!==ME).length;
    if(fight(n,G.fleets.filter(x=>x.node===to&&x.cls!=='spy'),'')){res=G.lastFight;}
    else res={win:[ME],sides:[{pid:ME,fleets:[[f.cls,f.count]],workers:0,turrets:[],core:null,saved:[]}],workersOnly:enemyW};
  }catch(e){console.warn('Jopium: preview failed',e);res=null;}
  finally{G=keep.G;UID=keep.UID;RNG=keep.RNG;REPLAY=false;}
  return res;
}
function openPreview(f,to){G.popup={type:'preview',f:f.id,to,res:previewBattle(f,to)};G.popupAt=performance.now();G.moveMode=null;G.hoverPath=null;refresh();}
const tileKind=n=>n.type==='core'||n.type==='deadcore'||n.type==='captured'?L('core','ядро'):n.planet!=null?(n.center?L('planet centre','центр планеты'):L('planet section','участок планеты')):L('asteroid','астероид');
function openUnit(u){""")
rep("  if(m.type==='hangar'){\n", r"""  if(m.type==='preview'){
    const r=m.res,n=G.nodes[m.to],win=r&&r.win.length===1&&r.win[0]===ME;
    const desc=sd=>{const a=[];for(const [c,k] of sd.fleets)a.push(dCount(k,c));if(sd.workers)a.push(L(`${plural(sd.workers,'worker')}`,cnt(sd.workers,'worker')));for(const t of sd.turrets)a.push(lc(sN(t)));if(sd.core!=null)a.push(L(`core at ${sd.core} health`,`ядро: ${sd.core} здоровья`));return a.length?a.join(', '):L('nothing','ничего');};
    h+=`<h2>${r?L(`If you move to this ${tileKind(n)}, you would ${win?'win':'lose'}`,`Если полететь на ${tileKind(n)}, вы ${win?'победите':'проиграете'}`):L('The result is hard to predict','Исход трудно предсказать')}</h2><p class="sub" style="margin:0">${L('An estimate from what you can see now, if nobody else moves.','Оценка по тому, что вы видите сейчас, если никто больше не сдвинется.')}</p>`;
    if(r){
      if(r.workersOnly)h+=`<div class="row"><div class="grow">${L(`The enemy has only workers there: ${plural(r.workersOnly,'worker')} would be destroyed.`,`Там только рабочие противника: будет уничтожено ${cnt(r.workersOnly,'worker')}.`)}</div></div>`;
      for(const sd of r.sides){const mine=sd.pid===ME,won=r.win.includes(sd.pid);if(!won&&!sd.saved.length)continue;
        h+=`<div class="row"><div class="grow"><b style="color:${P(sd.pid).color}">${mine?L('You','Вы'):esc(pShort(P(sd.pid)))}</b> ${won?L('would keep','сохраните'+(mine?'':'т')):''} ${won?desc(sd):''}${sd.saved.length?`<br><span class="sub">${L('Boomerangs would save','Бумеранги спасут')}: ${sd.saved.map(esc).join(', ')}</span>`:''}</div></div>`;}
    }
    h+=`<div class="opts"><button class="btn primary" type="button" data-a="pmove" data-f="${m.f}" data-n="${m.to}">${L('Move','Лететь')}</button><button class="btn" type="button" data-a="pclose">${L('Cancel','Отмена')}</button></div>`;
  }else if(m.type==='hangar'){
""")
rep("    case 'pclose':G.popup=null;break;", "    case 'pclose':G.popup=null;break;\n    case 'pmove':G.popup=null;order({t:'fmove',f:+d.f,to:+d.n});break;")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
