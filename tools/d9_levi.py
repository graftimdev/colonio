"""Draft 9: planets in Warfare, the leviathan."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:80]}')
    s = s.replace(a, b)


# planets in both modes
rep("  const nPl=mode==='conquest'?Math.min(5,np-1):0,target=per*np+np;", "  const nPl=Math.min(5,np-1),target=per*np+np;")
rep("  const gold=$('#gold');gold.hidden=G.mode!=='conquest';", "  const gold=$('#gold');gold.hidden=!(G.planets&&G.planets.length);")
rep("if(G.mode==='conquest')gold.innerHTML=`${STARGOLD}<b>${p.gold}</b>/${GOLD_WIN}`;",
    "if(!gold.hidden)gold.innerHTML=G.mode==='conquest'?`${STARGOLD}<b>${p.gold}</b>/${GOLD_WIN}`:`${STARGOLD}<b>${p.gold}</b>`;")

# the leviathan is built like a station on a planet centre, but takes no slot and costs 100 stargold
i = s.index("\n  borehole:{n:'Borehole'")
j = s.index("\n", i + 1)
s = s[:j] + """
  levi:{n:'Leviathan',r:'Левиафан',rd:'Гигантский боевой дрон (50 здоровья, 20 урона, 1 прыжок за ход), которым управляет построивший его рабочий. Не тратит энергию и не занимает место станции. Только в «Сражении».',cost:{},gold:100,t:2,where:'centre',noSlot:true,d:'A giant war drone (50 health, 20 damage, 1 hop a turn) piloted by the worker who builds it. Uses no energy and takes no station slot. Warfare only.'},""" + s[j:]
rep("  if(n.stations.length>=SLOTS)return L('All 4 build slots are used','Все 4 места для станций заняты');",
    """  if(type==='levi'){
    if(G.mode==='conquest')return L('No leviathans in Conquest','В «Завоевании» левиафанов нет');
    if(P(pid).gold<ST.levi.gold)return L('Needs 100 stargold','Нужно 100 звёздного золота');
    if(n.stations.some(x=>x.type==='levi'))return L('A leviathan is already being built here','Здесь уже строится левиафан');
  }
  if(!ST[type].noSlot&&n.stations.filter(x=>!ST[x.type].noSlot).length>=SLOTS)return L('All 4 build slots are used','Все 4 места для станций заняты');""")
rep("const pc=stCost(pid,type);payAt(pid,nid,pc);const s=newStation(n,type,{paid:pc});n.stations.push(s);",
    "const pc=stCost(pid,type);payAt(pid,nid,pc);if(ST[type].gold)P(pid).gold-=ST[type].gold;const s=newStation(n,type,{paid:pc,gold:ST[type].gold||0});n.stations.push(s);")
rep("case 'stcancel':{const f=S(c.s);if(!f||f.s.state!=='build')return false;refundAt(pid,f.n.id,f.s.paid||ST[f.s.type].cost);",
    "case 'stcancel':{const f=S(c.s);if(!f||f.s.state!=='build')return false;refundAt(pid,f.n.id,f.s.paid||ST[f.s.type].cost);p.gold+=f.s.gold||0;")
# finishing the build: the builder climbs in and becomes the pilot
rep("    if(f.s.work<=0){f.s.state='done';",
    """    if(f.s.work<=0&&f.s.type==='levi'){
      f.n.stations=f.n.stations.filter(x=>x!==f.s);
      const crew=ws.filter(x=>x.task==='build'&&x.ref===f.s.uid);crew.forEach(x=>{x.task='idle';x.ref=null;});
      if(G.fleets.some(g=>g.owner===pid&&g.node===f.n.id&&!(g.cls==='charger'&&g.settled))){p.gold+=f.s.gold||0;log(L(`The leviathan at ${lc(nodeName(f.n))} could not be finished: your fleets were in the way. 100 stargold returned.`,`Левиафан на ${lc(nodeName(f.n))} не достроен: мешали ваши флоты. 100 звёздного золота возвращено.`),'warn',f.n.id,[pid]);continue;}
      const pilot=crew.find(x=>x===w)||crew[0]||w;G.workers=G.workers.filter(x=>x!==pilot);
      const lv=newFleet(pid,'leviathan',1,f.n.id);lv.pilot=pilot.name;G.fleets.push(lv);
      log(L(`A leviathan rose at ${lc(nodeName(f.n))}, piloted by ${pilot.name}.`,`На ${lc(nodeName(f.n))} поднялся левиафан. Пилот: ${pilot.name}.`),'good',f.n.id,[pid]);
      continue;
    }
    if(f.s.work<=0){f.s.state='done';""")
# leviathans and your other fleets never share a tile (a settled charger is the exception)
rep("      if(!planetOk(u.owner,u.cls,nx)){u.path=[];u.mergeInto=null;continue;}",
    "      if(!planetOk(u.owner,u.cls,nx)){u.path=[];u.mergeInto=null;continue;}\n      if(leviBlocks(u,nx)){u.path=[];u.mergeInto=null;continue;}")
rep("const leviHere=(pid,node)=>", """// a leviathan can't enter a tile with your fleets (a settled charger is fine), and your fleets can't enter a leviathan's tile
const leviBlocks=(f,id)=>f.cls==='leviathan'?G.fleets.some(g=>g!==f&&g.owner===f.owner&&g.node===id&&!(g.cls==='charger'&&g.settled)):G.fleets.some(g=>g.owner===f.owner&&g.node===id&&g.cls==='leviathan');
const leviHere=(pid,node)=>""")
rep("  if(id!==f.node&&tileCount(pid,id,f.cls,f)+f.count>capFor(pid,f.cls))",
    "  if(id!==f.node&&leviBlocks(f,id))return deny(f.cls==='leviathan'?L(\"Your leviathan can't share a tile with your other fleets.\",'Левиафан не может стоять на одной клетке с вашими флотами.'):L(\"Your fleets can't share a tile with your leviathan.\",'Ваши флоты не могут стоять на одной клетке с левиафаном.'));\n  if(id!==f.node&&tileCount(pid,id,f.cls,f)+f.count>capFor(pid,f.cls))")
rep("const capFor=(pid,cls)=>cls==='charger'?1:tileCap(pid);", "const capFor=(pid,cls)=>cls==='charger'||cls==='leviathan'?1:tileCap(pid);")
# a leviathan under construction is drawn as its icon, faded
rep("function stationIcon(c,s,x,y,sz,color){", "function stationIcon(c,s,x,y,sz,color){\n  if(s.type==='levi'){c.save();c.globalAlpha=.6;drawLeviathan(c,x,y,10*sz,color,.15);c.restore();return;}")
rep("<br>${costHtml(stCost(ME,k),w)}</div><button class=\"btn small\" type=\"button\" data-a=\"start\"",
    "<br>${s.gold?`<span class=\"cost\"><span class=\"${P(ME).gold<s.gold?'bad':''}\">${STARGOLD}${s.gold}</span></span>`:costHtml(stCost(ME,k),w)}</div><button class=\"btn small\" type=\"button\" data-a=\"start\"")
rep("    if(k==='borehole'&&n.stations.some(x=>x.type==='borehole'))continue;\n",
    "    if(k==='borehole'&&n.stations.some(x=>x.type==='borehole'))continue;\n    if(k==='levi'&&G.mode==='conquest')continue;\n")
rep("<details class=\"sec\"${n.stations.length<SLOTS?'':' hidden'}>", "<details class=\"sec\"${n.stations.filter(x=>!ST[x.type].noSlot).length<SLOTS||n.center?'':' hidden'}>")

# ending a turn: a leviathan finishing on a tile your fleets will be on is not allowed
rep("  if(G.online){submitTurn();return;}\n  G.moveMode=null;G.hoverPath=null;G.splitOpen=null;",
    """  const clash=leviClashes(ME);
  if(clash.length){
    if(!auto){sfxError();G.notice=L(`You can't end the turn like this: a leviathan would be finished at ${clash.map(n=>lc(nodeName(n))).join(', ')}, where your fleets are or are heading. Move the fleets elsewhere, or stop the build.`,`Нельзя так завершить ход: левиафан достроится на ${clash.map(n=>lc(nodeName(n))).join(', ')}, где стоят или куда летят ваши флоты. Уведите флоты или остановите стройку.`);openModal({type:'report'});return;}
    // the timer ran out: the build is cancelled and the stargold comes back
    for(const n of clash)for(const st of n.stations.filter(x=>x.type==='levi'))order({t:'stcancel',s:st.uid});
  }
  if(G.online){submitTurn();return;}
  G.moveMode=null;G.hoverPath=null;G.splitOpen=null;""")
rep("function afterResolve(){", """// planet centres where your leviathan would be finished this turn while your fleets stand there or are flying there
function leviClashes(pid){
  const out=[];
  for(const n of G.nodes)for(const st of n.stations){
    if(st.type!=='levi'||n.owner!==pid||st.state!=='build')continue;
    if(buildersOn(st.uid)<st.work)continue;
    if(G.fleets.some(f=>f.owner===pid&&!(f.cls==='charger'&&f.settled)&&(f.node===n.id&&!f.path.length||f.path[f.path.length-1]===n.id)))out.push(n);
  }
  return out;
}
function afterResolve(){""")
# the Warfare setup line mentions planets now
rep("L('Be the last AI left in the belt.','Останьтесь последним в поясе.')",
    "L('Be the last one left in the belt. Dwarf planets give stargold: 100 of it builds a leviathan.','Останьтесь последним в поясе. Карликовые планеты дают звёздное золото: за 100 можно построить левиафана.')")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
