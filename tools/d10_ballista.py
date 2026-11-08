"""Draft 10 stage 2a: the new ballista (crystal chain lightning), artillery always fires, hit pulses."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


# ---------- stats ----------
rep("""rd:'Стреляет по соседней клетке, даже в космосе, как катапульта: каждый выстрел тратит 1 железо. В бою на своей клетке железо не нужно.',cost:{iron:4,copper:3,silicon:1},hp:4,dmg:2,spd:1,up:1,ground:true,d:'Fires at a neighbouring tile, even one in space, like a catapult: each shot uses 1 Iron. Needs no Iron to fight on its own tile.',ud:null},""",
    """rd:'Бьёт молнией по соседней клетке за кристаллы: 1 кристалл = удар 0,5. Зарядите до 5 кристаллов: молния перескакивает на соседние клетки с врагами, удваивая урон (0,5, 1, 2, 4, 8). Каждая лишняя баллиста в эскадрилье может добавить +0,5 к последнему удару за +1 кристалл.',cost:{iron:4,copper:3,silicon:1},hp:2,dmg:2,spd:1,up:1,ground:true,d:'Shoots lightning at a neighbouring tile for crystals: 1 crystal is a 0.5 hit. Charge up to 5 and the bolt jumps on to neighbouring enemy tiles, doubling each time (0.5, 1, 2, 4, 8). Each extra ballista in the squadron can add +0.5 to the last hit for +1 crystal.',ud:null},""")

# ---------- helpers ----------
rep("const ARTY=c=>c==='catapult'||c==='ballista';",
    """const ARTY=c=>c==='catapult'||c==='ballista';
// players at peace never hurt each other (diplomacy fills G.peace in)
const atPeace=(a,b)=>!!(G.peace&&G.peace.some(x=>x.a===Math.min(a,b)&&x.b===Math.max(a,b)));
const isFoe=(a,b)=>a!=null&&b!=null&&a!==b&&!atPeace(a,b);
// ballista: the most crystals one shot can use (5 for the chain, +1 per extra ballista for the last hit)
const maxCharge=f=>5+Math.max(0,f.count-1);
const CHAIN=[.5,1,2,4,8];""")

# ---------- order ----------
rep("      f.bombard=+c.to;f.keep=!!c.keep;f.path=[];f.mergeInto=null;return true;}",
    """      if(f.cls==='ballista'){const cr=Math.floor(+c.cr||0);if(!(cr>=1&&cr<=maxCharge(f)))return deny(L('Pick how many crystals to charge.','Выберите, сколько кристаллов зарядить.'));
        if(p.res.xeno<cr)return deny(L(`You need ${cr} crystals for that shot.`,`Для этого выстрела нужно кристаллов: ${cr}.`));f.charge=cr;}
      f.bombard=+c.to;f.keep=!!c.keep;f.path=[];f.mergeInto=null;return true;}""")

# ---------- catapults always fire, ballistas fire lightning ----------
rep("""function bombardAll(){
  for(const f of G.fleets.filter(f=>ARTY(f.cls)&&f.bombard!=null)){
    if(!G.fleets.includes(f))continue;
    const tn=G.nodes[f.bombard];
    if(!G.nodes[f.node].nbr.includes(tn.id)){f.bombard=null;continue;}""",
    """function bombardAll(){
  for(const f of G.fleets.filter(f=>ARTY(f.cls)&&f.bombard!=null)){
    if(!G.fleets.includes(f))continue;
    const tn=G.nodes[f.bombard];
    if(!G.nodes[f.node].nbr.includes(tn.id)){f.bombard=null;continue;}
    if(f.cls==='ballista'){ballistaFire(f,tn);continue;}""")
# the old "held fire" line: artillery now always fires, even at an empty tile
i = s.index("    if(!turrets.length&&!drones.length&&!workers.length&&!core){if(f.owner===ME)log(")
j = s.index("\n", i)
s = s[:i] + "    // artillery always fires, even when nobody is there" + s[j:]
rep("""    }else{
      const d=Math.min(tn.coreHp,dmg);tn.coreHp-=d;if(d>0)lost.push(L(`${d} core health`,`${d} здоровья ядра`));
    }""", """    }else if(core){
      const d=Math.min(tn.coreHp,dmg);tn.coreHp-=d;if(d>0)lost.push(L(`${d} core health`,`${d} здоровья ядра`));
    }""")
rep("""    (G.rockets=G.rockets||[]).push({from:f.node,to:tn.id,n:Math.min(shots,6),owner:f.owner,fid:f.id});
    G.flash.add(tn.id);""", """    (G.rockets=G.rockets||[]).push({from:f.node,to:tn.id,n:Math.min(shots,6),owner:f.owner,fid:f.id});
    G.flash.add(tn.id);hitPulse(tn.id,[f.owner],[]);""")

rep("function fireDeathTurrets(){", r"""// a tile was hit: it pulses twice at the start of the next turn (red, or blue for a tile you attacked and won)
function hitPulse(id,att,win){(G.pulses=G.pulses||[]).push({node:id,att,win});}
// does tile id hold anything of an enemy of pid that a ballista bolt can hurt?
function boltTargets(pid,id){
  const n=G.nodes[id],tg=[];
  for(const g of G.fleets)if(g.node===id&&g.hp>0&&isFoe(pid,g.owner))tg.push({k:HIT_ORDER.indexOf(g.cls),f:g});
  if(isFoe(pid,n.owner))for(const t of liveTurrets(n))tg.push({k:HIT_ORDER.indexOf('t:'+t.type),t});
  for(const w of G.workers)if(w.node===id&&isFoe(pid,w.owner))tg.push({k:HIT_ORDER.indexOf('worker'),w});
  if(n.type==='core'&&n.coreHp>0&&isFoe(pid,n.coreOf))tg.push({k:HIT_ORDER.length-1,c:n});
  return tg.sort((a,b)=>a.k-b.k);
}
// the bolt's route after the first hit: as many different enemy tiles as it can reach in up to `left` jumps;
// ties go to the jump closer to an enemy core, then at random
function boltRoute(pid,from,seen,left){
  if(left<=0)return [];
  const opts=G.nodes[from].nbr.filter(id=>!seen.has(id)&&boltTargets(pid,id).length);
  if(!opts.length)return [];
  const cores=G.players.filter(q=>q.alive&&isFoe(pid,q.id)).map(q=>G.nodes[q.core]);
  const coreD=id=>cores.length?Math.min(...cores.map(c=>hexDist(G.nodes[id],c))):0;
  let best=null;
  for(const id of opts){const s2=new Set(seen);s2.add(id);const r=[id,...boltRoute(pid,id,s2,left-1)];
    if(!best||r.length>best[0].length)best=[r];else if(r.length===best[0].length)best.push(r);}
  const dmin=Math.min(...best.map(r=>coreD(r[0])));best=best.filter(r=>coreD(r[0])===dmin);
  return best[Math.floor(rnd()*best.length)];
}
// one hit of the bolt on a tile, in the usual damage order; a powered enemy barrier soaks 10 of it
function boltHit(f,id,dmg,lost){
  const n=G.nodes[id];
  const bar=isFoe(f.owner,n.owner)?10*live(n,'barrier').filter(x=>x.pw).length:0;
  let d=Math.max(0,dmg-bar);const soaked=dmg-d;
  for(const t of boltTargets(f.owner,id)){
    if(d<=1e-9)break;
    if(t.f){const g=t.f,before=g.count;const a=Math.min(g.hp,d);g.hp-=a;d-=a;syncFleet(g);const k=g.hp<=0?before:before-g.count;
      if(k>0)lost.push(L(`${k} ${pShort(P(g.owner))} ${dCount(k,g.cls).replace(/^\d+ /,'')}`,`${dCount(k,g.cls)} (${pShort(P(g.owner))})`));
      if(g.cls==='leviathan'&&g.hp<=0&&g.pilot)lost.push(L(`pilot ${g.pilot}`,`пилот ${g.pilot}`));}
    else if(t.t){const a=Math.min(t.t.hp,d);t.t.hp-=a;d-=a;if(t.t.hp<=0)lost.push(lc(sN(t.t.type)));}
    else if(t.w){d-=1;G.workers=G.workers.filter(w=>w!==t.w);lost.push(L(`worker ${t.w.name}`,`рабочий ${t.w.name}`));}
    else{const a=Math.min(t.c.coreHp,d);t.c.coreHp-=a;d-=a;if(a>0)lost.push(L(`${Math.round(a*10)/10} core health`,`${Math.round(a*10)/10} здоровья ядра`));}
  }
  G.fleets=G.fleets.filter(g=>g.hp>0);
  n.stations=n.stations.filter(s=>!(isTurret(s.type)&&s.state==='done'&&s.hp<=0));
  G.flash.add(id);hitPulse(id,[f.owner],[]);
  if(n.type==='core'&&n.coreHp<=0)coreFall(n);
  return soaked;
}
// a ballista squadron fires one bolt: charged crystals decide how far it jumps (0.5, 1, 2, 4, 8),
// crystals past the 5th add +0.5 each to the last hit (one per extra ballista)
function ballistaFire(f,tn){
  const p=P(f.owner),who=RU()?'Баллисты ('+(f.owner===ME?'ваши':pShort(p))+')':(f.owner===ME?'Your':pShort(p))+' ballistas';
  const want=Math.min(f.charge||1,maxCharge(f)),cr=Math.min(want,Math.floor(p.res.xeno),poweredDrones(f)>0?maxCharge(f):0);
  if(cr<1){log(L(`${who} had no crystals to fire at ${lc(nodeName(tn))}.`,`${who}: нет кристаллов для выстрела по: ${lc(nodeName(tn))}.`),'warn',f.node,[f.owner]);if(!f.keep)f.bombard=null;return;}
  p.res.xeno-=cr;
  const hops=Math.min(cr,5),extra=Math.max(0,cr-5);
  // the first hit always lands on the chosen tile; the bolt only jumps on from a tile that had an enemy
  const route=[tn.id];
  if(hops>1&&boltTargets(f.owner,tn.id).length)route.push(...boltRoute(f.owner,tn.id,new Set([f.node,tn.id]),hops-1));
  const lines=[],pids=new Set([f.owner]);
  route.forEach((id,i)=>{
    const dmg=CHAIN[i]+(i===route.length-1?.5*extra:0),lost=[];
    if(G.nodes[id].owner!=null)pids.add(G.nodes[id].owner);
    for(const g of G.fleets)if(g.node===id)pids.add(g.owner);
    const soaked=boltHit(f,id,dmg,lost);
    lines.push(L(`${lc(nodeName(G.nodes[id]))} ${dmg}${soaked?` (${soaked} soaked by a barrier)`:''}${lost.length?': '+lost.join(', '):''}`,`${lc(nodeName(G.nodes[id]))} ${dmg}${soaked?` (барьер поглотил ${soaked})`:''}${lost.length?': '+lost.join(', '):''}`));
  });
  const wasted=hops-route.length;
  log(L(`${who} fired a ${cr}-crystal bolt: ${lines.join(' → ')}${wasted>0?`. No more enemy tiles to jump to: ${wasted} crystal${wasted>1?'s':''} wasted`:''}.`,
        `${who} выпустили молнию (${cr} крист.): ${lines.join(' → ')}${wasted>0?`. Дальше прыгать некуда, потеряно кристаллов: ${wasted}`:''}.`),'warn',tn.id,[...pids]);
  (G.shocks=G.shocks||[]).push({path:[f.node,...route],owner:f.owner,fid:f.id});
  if(!f.keep)f.bombard=null;
}
function fireDeathTurrets(){""")

# death turret shots pulse too
rep("function fireDeathTurrets(){\n", "function fireDeathTurrets(){\n  // (each tile a death turret hits pulses red next turn)\n")

# battles pulse: blue for a tile you attacked and won
rep("  if(n){n.stations=n.stations.filter(s=>!(isTurret(s.type)&&s.state==='done'&&s.hp<=0));G.flash.add(n.id);",
    "  if(n){const att=[...sides.keys()].filter(pid=>fleets.some(f=>f.owner===pid&&f.trail&&f.trail.length>1));hitPulse(n.id,att.length?att:[...sides.keys()].filter(pid=>pid!==owner),winner.map(s=>s.pid));\n    n.stations=n.stations.filter(s=>!(isTurret(s.type)&&s.state==='done'&&s.hp<=0));G.flash.add(n.id);")

# resolve resets, local keys
rep("  G.log=[];G.flash=new Set();G.notice=null;G.rockets=[];G.coreFell=false;",
    "  G.log=[];G.flash=new Set();G.notice=null;G.rockets=[];G.shocks=[];G.pulses=[];G.coreFell=false;")
rep("'techFor','rockets',", "'techFor','rockets','shocks','pulses','pulseT0',")

# AI: ballistas charge what they can afford
rep("  if(f.cls==='ballista'){const t=n.nbr.find(foe);if(t!=null&&!foe(f.node)){f.bombard=t;return;}}",
    "  if(f.cls==='ballista'){const t=n.nbr.find(foe);const cr=Math.min(maxCharge(f),Math.floor(P(f.owner).res.xeno/2));if(t!=null&&!foe(f.node)&&cr>=1){f.bombard=t;f.charge=cr;return;}}")
rep("      if(n.nbr.includes(t)){f.bombard=t;continue;}",
    "      if(n.nbr.includes(t)){if(f.cls==='ballista'){const cr=Math.min(maxCharge(f),Math.floor(p.res.xeno/2));if(cr<1)continue;f.charge=cr;}f.bombard=t;continue;}")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
