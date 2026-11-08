"""Draft 10 stage 2b: underdog gifts, the Conquest leader penalty, borehole operators."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


# ---------- rules ----------
rep("function hitPulse(id,att,win){", r"""/* ---------- underdog gifts ----------
   Every 5 turns from turn 15, with 3+ players alive: strength = 0.35 army + 0.25 land + 0.15 resources + 0.15 jopium + 0.10 cores,
   each part compared with the best alive player. The weakest player is the underdog when their strength is at most 60% of
   everyone else's average; they get ceil((0.6·avg − S)/0.1) gifts (1–3) on their own empty asteroids / planet sections.
   A gift lasts 5 turns, is seen only by players who see its tile, and goes to whoever reaches it first (see claimGifts). */
const GIFT_SPACE=['frigate','siege','boomerang','catapult'],GIFT_ROVER=['tank','stomper','ballista'];
function strengthParts(pid){
  const p=P(pid);
  return {army:G.fleets.filter(f=>f.owner===pid&&DR[f.cls].dmg>0).reduce((a,f)=>a+f.count*(DR[f.cls].hp+DR[f.cls].dmg),0),
    land:G.nodes.filter(n=>n.owner===pid).length,res:RES.reduce((a,r)=>a+p.res[r],0),gold:p.gold,
    cores:1+G.nodes.filter(n=>n.type==='captured'&&n.owner===pid).length};
}
function strengths(){
  const alive=G.players.filter(p=>p.alive),parts=new Map(alive.map(p=>[p.id,strengthParts(p.id)]));
  const W={army:.35,land:.25,res:.15,gold:.15,cores:.10},best={};
  for(const k in W)best[k]=Math.max(0,...[...parts.values()].map(x=>x[k]));
  const out=new Map();for(const [pid,x] of parts){let v=0;for(const k in W)v+=W[k]*(best[k]>0?x[k]/best[k]:1);out.set(pid,v);}
  return out;
}
const giftSpot=(pid,n)=>n.owner===pid&&(n.type==='empty'||(n.planet!=null&&!n.center))&&!n.stations.length&&
  !G.fleets.some(f=>f.node===n.id)&&!G.workers.some(w=>w.node===n.id)&&!(G.gifts||[]).some(g=>g.node===n.id);
function updateGifts(){
  G.gifts=(G.gifts||[]).filter(g=>G.turn-g.t<5);
  if(G.gifts.length||G.turn<15||G.turn%5)return;
  const alive=G.players.filter(p=>p.alive);if(alive.length<3)return;
  const st=strengths(),ranked=[...st].sort((a,b)=>a[1]-b[1]),[uid,S]=ranked[0];
  const avg=ranked.slice(1).reduce((a,x)=>a+x[1],0)/(ranked.length-1);
  if(S>.6*avg)return;
  const k=Math.max(1,Math.min(3,Math.ceil((.6*avg-S)/.1-1e-9)));
  const spots=shuffle(G.nodes.filter(n=>giftSpot(uid,n))).slice(0,k);
  if(!spots.length)return;
  for(const n of spots){const rover=n.planet!=null,list=rover?GIFT_ROVER:GIFT_SPACE;
    G.gifts.push({node:n.id,cls:list[Math.floor(rnd()*list.length)],up:!rover,t:G.turn,for:uid});hitPulse(n.id,[],[],'gift');}
  log(L(`Supplies were dropped on ${spots.length} of your tile${spots.length>1?'s':''}. Reach them within 5 turns to collect them, before someone else does.`,
        `На ваших клетках появились припасы: ${spots.length}. Доберитесь до них за 5 ходов, пока их не забрал кто-то другой.`),'info',spots[0].id,[uid]);
}
// whoever reaches a gift takes it at once. Two players' workers together: only the underdog's can take it, otherwise nobody
// until one leaves; war squadrons settle it by battle first, so only the winner is left
function claimGifts(){
  for(const g of [...(G.gifts||[])]){
    const n=G.nodes[g.node];
    const owners=new Set([...G.workers.filter(w=>w.node===n.id).map(w=>w.owner),...G.fleets.filter(f=>f.node===n.id&&f.cls!=='spy').map(f=>f.owner)]);
    if(!owners.size)continue;
    const pid=owners.size===1?[...owners][0]:owners.has(g.for)?g.for:null;
    if(pid==null)continue;
    G.gifts=G.gifts.filter(x=>x!==g);
    const f=newFleet(pid,g.cls,1,n.id,g.up);G.fleets.push(f);
    const p=P(pid);for(const r of RES)addRes(p,r,2);
    log(L(`${pid===ME?'You':pShort(p)} collected the supplies at ${lc(nodeName(n))}: ${g.up?'an upgraded ':'a '}${dN(g.cls).toLowerCase()} and 2 of each resource.`,
          `${pid===ME?'Вы забрали':pShort(p)+' забрал'} припасы на ${lc(nodeName(n))}: ${dN(g.cls).toLowerCase()}${g.up?' (улучшенный)':''} и по 2 каждого ресурса.`),'info',n.id,[pid]);
  }
}
/* Conquest: a leader 50+ jopium ahead of second place mines less (boreholes 2, miners 1) until the gap has been 49 or less for 10 turns */
function updateGoldCap(){
  if(G.mode!=='conquest')return;
  const al=G.players.filter(p=>p.alive).sort((a,b)=>b.gold-a.gold);
  if(al.length<2){G.goldCap=null;return;}
  const gap=al[0].gold-al[1].gold;
  if(gap>=50){if(!G.goldCap||G.goldCap.pid!==al[0].id){G.goldCap={pid:al[0].id,calm:0};
      log(L(`${al[0].id===ME?'You are':pShort(al[0])+' is'} 50 jopium ahead: ${al[0].id===ME?'your':'their'} boreholes now give 2 jopium a turn until the others catch up.`,`${al[0].id===ME?'Вы опережаете':pShort(al[0])+' опережает'} всех на 50 жопиума: буры дают только 2 за ход, пока остальные не догонят.`),'warn',null,G.players.map(q=>q.id));}
    else G.goldCap.calm=0;}
  else if(G.goldCap){G.goldCap.calm++;if(G.goldCap.calm>=10){log(L('The jopium leader mines at the normal rate again.','Лидер по жопиуму снова добывает в обычном темпе.'),'info',null,G.players.map(q=>q.id));G.goldCap=null;}}
}
function hitPulse(id,att,win,kind){""")
rep("function hitPulse(id,att,win,kind){(G.pulses=G.pulses||[]).push({node:id,att,win});}",
    "function hitPulse(id,att,win,kind){(G.pulses=G.pulses||[]).push({node:id,att,win,kind});}")

# ---------- turn order ----------
rep("  // 4. captures\n  const movedNow=", "  claimGifts();\n  // 4. captures\n  const movedNow=")
rep("  G.turn++;G.timeLeft=G.turnTime;G.anim={t0:performance.now()};\n",
    "  G.turn++;G.timeLeft=G.turnTime;G.anim={t0:performance.now()};\n  updateGoldCap();updateGifts();\n")

# ---------- boreholes: the miner on a centre with a borehole operates it (1 energy a turn) ----------
rep("""      if(avail<mc){blocked++;continue;}avail-=mc;
      goldDone.add(n.id);const g=live(n,'borehole').length?5:1;p.gold+=g;continue;""",
    """      // with a borehole the worker sits at it as its operator: 1 energy a turn, 5 jopium (2 while the Conquest leader is capped)
      const bore=live(n,'borehole').length>0,cost=bore?1:mc;
      if(avail<cost){blocked++;continue;}avail-=cost;
      const capped=G.goldCap&&G.goldCap.pid===pid;
      goldDone.add(n.id);const g=bore?(capped?2:5):1;p.gold+=g;continue;""")

# ---------- sync ----------
rep("  for(const w of G.workers)parts.push(w.id,w.owner,w.node,w.task);",
    "  for(const w of G.workers)parts.push(w.id,w.owner,w.node,w.task);\n  parts.push(JSON.stringify(G.gifts||[]),JSON.stringify(G.goldCap||null),JSON.stringify(G.peace||[]),JSON.stringify(G.treaties||[]));")

# ---------- drawing: gifts on tiles you can see, yellow pulse when they appear ----------
rep("  // hit pulses: when the move animation ends,", r"""  // gifts: a yellow glow and a small box on the tile, only where you can see
  for(const g of G.gifts||[]){if(!V.has(g.node))continue;const n=G.nodes[g.node],[x,y]=toScreen(n.x,n.y),b=6*sz,yy=y-16*sz;
    ctx.beginPath();ctx.arc(x,y,R*cam.z*.62,0,Math.PI*2);ctx.fillStyle='rgba(255,216,77,.16)';ctx.fill();ctx.strokeStyle='rgba(255,216,77,.75)';ctx.lineWidth=1.5;ctx.stroke();
    ctx.fillStyle='#ffd84d';ctx.fillRect(x-b,yy-b*.6,b*2,b*1.4);ctx.strokeStyle='#0b1020';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(x,yy-b*.6);ctx.lineTo(x,yy+b*.8);ctx.moveTo(x-b,yy);ctx.lineTo(x+b,yy);ctx.stroke();}
  // hit pulses: when the move animation ends,""")
rep("      const won=pu.att.includes(ME)&&pu.win.length===1&&pu.win[0]===ME,col=won?'77,163,255':'255,93,108';",
    "      const won=pu.att.includes(ME)&&pu.win.length===1&&pu.win[0]===ME,col=pu.kind==='gift'?'255,216,77':won?'77,163,255':'255,93,108';")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
