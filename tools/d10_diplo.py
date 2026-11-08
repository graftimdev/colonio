"""Draft 10 stage 3: diplomacy (peace treaties), rules side."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


# ---------- tech ----------
rep("  {id:'rates',b:0,at:[2,14],req:'trade',br:'Trade',rbr:'Торговля',n:'Better rates',r:'Выгодный курс',c:3,d:'Trades take 4 and give 3.',rd:'Обмен 4 на 3.'},",
    "  {id:'rates',b:0,at:[2,14],req:'trade',br:'Trade',rbr:'Торговля',n:'Better rates',r:'Выгодный курс',c:3,d:'Trades take 4 and give 3 (crystal trades stay 2 for 1).',rd:'Обмен 4 на 3 (обмен кристаллов остаётся 2 на 1).'},\n"
    "  {id:'diplomacy',b:0,at:[3,14],req:'rates',br:'Trade',rbr:'Торговля',n:'Diplomacy',r:'Дипломатия',c:3,d:'Lets you send peace treaties to rivals you have met (Empire → Rivals). A worker at your core prepares them.',rd:'Можно отправлять мирные договоры встреченным соперникам (Империя → Соперники). Готовит их рабочий в ядре.'},")

# ---------- who counts as an enemy ----------
rep("const warFleetsAt=(pid,id)=>G.fleets.filter(f=>f.node===id&&f.owner!==pid&&f.cls!=='spy');",
    "const warFleetsAt=(pid,id)=>G.fleets.filter(f=>f.node===id&&isFoe(pid,f.owner)&&f.cls!=='spy');")
rep("function hostileAt(pid,id){const n=G.nodes[id];return warFleetsAt(pid,id).length>0||(n.owner!=null&&n.owner!==pid&&armed(n));}",
    "function hostileAt(pid,id){const n=G.nodes[id];return warFleetsAt(pid,id).length>0||(isFoe(pid,n.owner)&&armed(n));}")
rep("const enemyXray=(pid,id)=>{const n=G.nodes[id];return n.owner!=null&&n.owner!==pid&&live(n,'xray').some(s=>s.hp>0);};",
    "const enemyXray=(pid,id)=>{const n=G.nodes[id];return isFoe(pid,n.owner)&&live(n,'xray').some(s=>s.hp>0);};")
# isFoe/atPeace must exist before these lines run (they are arrow functions, so order of definition only matters at call time)

# battles
rep("  if(n&&owner!=null&&[...sides.keys()].some(p=>p!==owner)){", "  if(n&&owner!=null&&[...sides.keys()].some(p=>isFoe(p,owner))){")
rep("    const act=[...sides.values()].filter(alive);\n    if(act.length<2)break;",
    "    const act=[...sides.values()].filter(alive);\n    if(!act.some(a=>act.some(b=>isFoe(a.pid,b.pid))))break;")
rep("      const enemies=act.filter(o=>o!==s);", "      const enemies=act.filter(o=>isFoe(s.pid,o.pid));")
rep("    const vsOwner=n.owner!=null&&fl.some(f=>f.owner!==n.owner)&&(liveTurrets(n).length||n.type==='core');\n    if(owners.size<2&&!vsOwner)continue;",
    "    const vsOwner=n.owner!=null&&fl.some(f=>isFoe(f.owner,n.owner))&&(liveTurrets(n).length||n.type==='core');\n    if(![...owners].some(a=>[...owners].some(b=>isFoe(a,b)))&&!vsOwner)continue;")
rep("    if(!G.fleets.some(f=>f.node===n.id&&f.owner!==w.owner&&DR[f.cls].dmg>0))return true;",
    "    if(!G.fleets.some(f=>f.node===n.id&&isFoe(f.owner,w.owner)&&DR[f.cls].dmg>0))return true;")
rep("    if(n.owner==null||n.owner===w.owner||!(coreGuns||liveTurrets(n).some(t=>t.type!=='death')))return true;",
    "    if(!isFoe(n.owner,w.owner)||!(coreGuns||liveTurrets(n).some(t=>t.type!=='death')))return true;")
rep("for(const n of G.nodes)if(n.type==='core'&&!G.fleets.some(f=>f.node===n.id&&f.owner!==n.owner&&f.cls!=='spy'))",
    "for(const n of G.nodes)if(n.type==='core'&&!G.fleets.some(f=>f.node===n.id&&isFoe(f.owner,n.owner)&&f.cls!=='spy'))")
rep("    const spyK=G.fleets.filter(f=>f.node===t.id&&f.cls==='spy'&&f.owner!==n.owner).reduce((a,f)=>a+f.count,0);",
    "    const spyK=G.fleets.filter(f=>f.node===t.id&&f.cls==='spy'&&isFoe(f.owner,n.owner)).reduce((a,f)=>a+f.count,0);")
# workers can't claim a partner's tiles
rep("    if(n.owner===w.owner||n.type==='core'||n.type==='wreck')continue;",
    "    if(n.owner===w.owner||n.type==='core'||n.type==='wreck')continue;\n    if(n.owner!=null&&atPeace(n.owner,w.owner)){log(L(`${w.name} can't claim ${lc(nodeName(n))}: you are at peace with ${pShort(P(n.owner))}.`,`${w.name} не может захватить ${lc(nodeName(n))}: у вас мир с ${pShort(P(n.owner))}.`),'warn',n.id,[w.owner]);continue;}")
rep("      const rivals=[...new Set(G.workers.filter(x=>x.node===n.id&&x.owner!==w.owner&&",
    "      const rivals=[...new Set(G.workers.filter(x=>x.node===n.id&&x.owner!==w.owner&&")

# ---------- power: partners' networks link where they touch ----------
rep("const fleetOnGrid=f=>f.cls==='spy'||(G.conn[f.owner]&&G.conn[f.owner].has(f.node));",
    """// at peace, two players' networks link where their tiles are one hop apart, so squadrons on a partner's network stay powered
const peaceLinked=(a,b)=>atPeace(a,b)&&G.conn[a]&&G.conn[b]&&[...G.conn[a]].some(id=>G.nodes[id].nbr.some(x=>G.conn[b].has(x)));
const fleetOnGrid=f=>f.cls==='spy'||(G.conn[f.owner]&&G.conn[f.owner].has(f.node))||(G.peace||[]).some(x=>{const q=x.a===f.owner?x.b:x.b===f.owner?x.a:null;return q!=null&&G.conn[q]&&G.conn[q].has(f.node)&&peaceLinked(f.owner,q);});""")

# ---------- sight: partners see each other's cores and spies ----------
rep("function vis(pid){if(pid===ME&&G.spectate)return new Set(G.nodes.map(n=>n.id));const p=P(pid);const s=new Set(p.explored);p.explored.forEach(id=>G.nodes[id].nbr.forEach(x=>s.add(x)));fleetSight(pid).forEach(id=>s.add(id));return s;}",
    "function vis(pid){if(pid===ME&&G.spectate)return new Set(G.nodes.map(n=>n.id));const p=P(pid);const s=new Set(p.explored);p.explored.forEach(id=>G.nodes[id].nbr.forEach(x=>s.add(x)));fleetSight(pid).forEach(id=>s.add(id));\n  for(const q of G.players)if(q.alive&&atPeace(pid,q.id)){s.add(q.core);G.nodes[q.core].nbr.forEach(x=>s.add(x));}\n  return s;}")
rep("  if(u.cls==='spy')return G.nodes[u.node].owner===ME&&live(G.nodes[u.node],'xray').length>0;",
    "  if(u.cls==='spy')return atPeace(ME,u.owner)||(G.nodes[u.node].owner===ME&&live(G.nodes[u.node],'xray').length>0);")

# ---------- treaties: prepared by a worker at the core, delivered at the end of the turn ----------
rep("function hitPulse(id,att,win,kind){", r"""/* ---------- diplomacy ----------
   G.peace: [{a,b}] pairs at peace (a<b). G.treaties: [{from,to,t}] waiting for an answer.
   A worker at the core prepares treaties (w.task 'diplo', w.diplo = [{to,brk}]): at the end of the turn they are sent,
   and breaks take effect. Answers ('peaceans') take effect at the end of the turn they are given. */
function metOf(pid){return new Set(P(pid).met||[]);}
// you meet a rival once you have seen their territory or drones
function updateMet(){
  for(const p of G.players){if(!p.alive)continue;const V=vis(p.id),m=new Set(p.met||[]);
    for(const id of V){const n=G.nodes[id];if(n.owner!=null&&n.owner!==p.id)m.add(n.owner);}
    for(const f of G.fleets)if(f.owner!==p.id&&V.has(f.node)&&(f.cls!=='spy'||atPeace(p.id,f.owner)))m.add(f.owner);
    for(const w of G.workers)if(w.owner!==p.id&&V.has(w.node))m.add(w.owner);
    p.met=[...m].sort((a,b)=>a-b);}
}
function makePeace(a,b){if(atPeace(a,b))return;(G.peace=G.peace||[]).push({a:Math.min(a,b),b:Math.max(a,b)});G.treaties=(G.treaties||[]).filter(t=>!((t.from===a&&t.to===b)||(t.from===b&&t.to===a)));
  log(L(`${pShort(P(a))} and ${pShort(P(b))} made peace. They can't attack each other, see each other's cores and spies, and their networks link where they touch.`,`${pShort(P(a))} и ${pShort(P(b))} заключили мир: они не нападают друг на друга, видят ядра и шпионов друг друга, а их сети соединяются там, где соприкасаются.`),'info',null,[a,b]);}
// the one who breaks the peace loses every squadron standing on the other's tiles
function breakPeace(by,other){
  if(!atPeace(by,other))return;
  G.peace=G.peace.filter(x=>!(x.a===Math.min(by,other)&&x.b===Math.max(by,other)));
  const lost=G.fleets.filter(f=>f.owner===by&&G.nodes[f.node].owner===other);
  G.fleets=G.fleets.filter(f=>!lost.includes(f));
  const k=lost.reduce((a,f)=>a+f.count,0);
  log(L(`${pShort(P(by))} broke the peace with ${pShort(P(other))}${k?` and lost ${plural(k,'drone')} on ${pShort(P(other))}'s tiles`:''}.`,`${pShort(P(by))} разорвал мир с ${pShort(P(other))}${k?` и потерял дронов на его клетках: ${k}`:''}.`),'battle',null,[by,other]);
}
function diploTurn(){
  // answers given this turn
  for(const t of [...(G.treaties||[])]){
    if(!P(t.to).alive||!P(t.from).alive){G.treaties=G.treaties.filter(x=>x!==t);continue;}
    // the computer never accepts
    if(P(t.to).ai){G.treaties=G.treaties.filter(x=>x!==t);log(L(`${pShort(P(t.to))} declined your peace treaty.`,`${pShort(P(t.to))} отклонил ваш мирный договор.`),'warn',null,[t.from]);continue;}
    if(t.ans==null)continue;
    G.treaties=G.treaties.filter(x=>x!==t);
    if(t.ans)makePeace(t.from,t.to);else log(L(`${pShort(P(t.to))} declined your peace treaty.`,`${pShort(P(t.to))} отклонил ваш мирный договор.`),'warn',null,[t.from]);
  }
  // workers that spent this turn at the core on diplomacy send their treaties and breaks
  for(const w of G.workers){if(w.task!=='diplo'||w.path.length)continue;const p=P(w.owner);
    if(w.node!==p.core){w.task='idle';w.diplo=null;continue;}
    for(const d of w.diplo||[]){
      if(d.brk)breakPeace(w.owner,d.to);
      else if(has(w.owner,'diplomacy')&&P(d.to).alive&&!atPeace(w.owner,d.to)&&metOf(w.owner).has(d.to)&&!(G.treaties||[]).some(t=>t.from===w.owner&&t.to===d.to)){
        (G.treaties=G.treaties||[]).push({from:w.owner,to:d.to,t:G.turn});
        log(L(`${w.name} sent a peace treaty to ${pShort(P(d.to))}.`,`${w.name} отправил мирный договор игроку ${pShort(P(d.to))}.`),'info',null,[w.owner]);
        log(L(`${pShort(P(w.owner))} wants to make peace with you.`,`${pShort(P(w.owner))} хочет заключить с вами мир.`),'info',null,[d.to]);}
    }
    w.task='idle';w.diplo=null;
  }
  // a fallen player's peace ends with them
  G.peace=(G.peace||[]).filter(x=>P(x.a).alive&&P(x.b).alive);
}
function hitPulse(id,att,win,kind){""")
rep("  G.turn++;G.timeLeft=G.turnTime;G.anim={t0:performance.now()};\n  updateGoldCap();updateGifts();\n",
    "  diploTurn();updateMet();\n  G.turn++;G.timeLeft=G.turnTime;G.anim={t0:performance.now()};\n  updateGoldCap();updateGifts();\n")

# ---------- orders ----------
rep("    case 'loopq':p.loopQ=!!c.v;return true;",
    """    case 'loopq':p.loopQ=!!c.v;return true;
    // diplomacy: a worker at the core prepares a treaty (or a break) for rival c.to; one worker can prepare several in the same turn
    case 'diplo':{const w=Wk(c.w),to=+c.to;if(!w||w.node!==p.core||w.path.length||!G.players[to]||to===pid||!P(to).alive)return false;
      const brk=!!c.brk;
      if(brk){if(!atPeace(pid,to))return false;}
      else{if(!has(pid,'diplomacy'))return deny(L('Research Diplomacy first.','Сначала изучите Дипломатию.'));if(atPeace(pid,to))return false;
        if(!metOf(pid).has(to))return deny(L("You haven't met this rival yet.",'Вы ещё не встречали этого соперника.'));}
      if(w.task!=='diplo'){setTask(w,'diplo');w.diplo=[];}
      w.diplo=w.diplo||[];if(!w.diplo.some(d=>d.to===to))w.diplo.push({to,brk});return true;}
    case 'peaceans':{const t=(G.treaties||[]).find(t=>t.from===+c.from&&t.to===pid);if(!t)return false;t.ans=!!c.yes;return true;}""")
rep("    case 'task':{const w=Wk(c.w);if(!w||!['idle','mine','claim','build','fix'].includes(c.task))return false;",
    "    case 'task':{const w=Wk(c.w);if(!w||!['idle','mine','claim','build','fix'].includes(c.task))return false;\n      if(w.task==='diplo')w.diplo=null;")

# sync fingerprint: who has met whom, and workers' diplomacy
rep("  for(const w of G.workers)parts.push(w.id,w.owner,w.node,w.task);",
    "  for(const w of G.workers)parts.push(w.id,w.owner,w.node,w.task,JSON.stringify(w.diplo||null));\n  for(const p of G.players)parts.push((p.met||[]).join(','));")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
