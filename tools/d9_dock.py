"""Draft 9: docking one drone at a time, launch lists, upgrade station rework, chargers, infinite queues, boreholes, barrier switch."""
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


# ---------------------------------------------------------------- helpers
rep("// keep one battery entry per drone after the drone count changes", """// one charger per tile; everything else up to the fleet size limit
const capFor=(pid,cls)=>cls==='charger'?1:tileCap(pid);
// what each station takes in: barrack = drones (not chargers), rover barrack = rovers, upgrade station = both
const dockKinds=st=>st.type==='kazarm'?SPACE.filter(c=>c!=='charger'):st.type==='rbarracks'?ROVERS:st.type==='upgrade'?[...SPACE,...ROVERS].filter(c=>c!=='charger'):[];
const leviHere=(pid,node)=>G.fleets.some(g=>g.owner===pid&&g.node===node&&g.cls==='leviathan');
const stationBusy=st=>st.queue.length>0||CLS.some(c=>(st.hangar[c]||[]).some(d=>d.upg));
// take one drone out of a fleet, with its share of the fleet's health and its own battery
function takeDrone(f){const hp=f.hp/f.count,en=f.en.length?f.en.pop():BATT;f.hp-=hp;f.count--;if(f.count<=0)G.fleets=G.fleets.filter(g=>g!==f);return {hp,en,up:!!f.up};}
// docked drones go back on the map, joining a fleet of the same kind standing there
function launchDrones(pid,c,node,drones){
  for(const d of drones){
    let f=G.fleets.find(g=>g.owner===pid&&g.node===node&&g.cls===c&&g.up===!!d.up&&!g.path.length&&!g.settled);
    if(!f){f=newFleet(pid,c,0,node,!!d.up);f.hp=0;G.fleets.push(f);}
    f.count++;f.hp+=d.hp;f.en.push(d.en);
  }
}
// keep one battery entry per drone after the drone count changes""")

# ---------------------------------------------------------------- orders
cut("    case 'dock':{", "    case 'disf':{", "")
rep("    case 'upg':{const f=F(c.f);return f?upgradeOne(f):false;}\n", "")
cut("    case 'launch':{", "    case 'resign':", """    case 'launch':{
      // c.s = station uid, or c.ch = settled charger; c.c = type; c.i = which docked drone, or -1 for all of that type
      let list,node;
      if(c.ch!=null){const ch=F(c.ch);if(!ch||ch.cls!=='charger')return false;list=(ch.dock||[]).filter(d=>d.c===c.c);node=ch.node;}
      else{const f=S(c.s);if(!f||!DR[c.c]||f.s.state!=='done')return false;list=f.s.hangar[c.c]||[];node=f.n.id;}
      if(leviHere(pid,node))return deny(L('Nothing can launch while your leviathan stands on this tile.','Нельзя выпускать, пока на этой клетке стоит ваш левиафан.'));
      let pick=(+c.i<0?list:[list[+c.i]]).filter(d=>d&&!d.upg);
      const room=capFor(pid,c.c)-tileCount(pid,node,c.c);
      if(!pick.length)return false;
      if(room<=0)return deny(L(`This tile already holds ${capFor(pid,c.c)} of your ${dCount(2,c.c).replace(/^\\d+ /,'')}. Move them out first.`,`На этой клетке уже ${dCount(capFor(pid,c.c),c.c)}. Сначала уведите их.`));
      pick=pick.slice(0,room);
      if(c.ch!=null){const ch=F(c.ch);ch.dock=ch.dock.filter(d=>!pick.includes(d));}
      else{const f=S(c.s);f.s.hangar[c.c]=f.s.hangar[c.c].filter(d=>!pick.includes(d));}
      launchDrones(pid,c.c,node,pick);
      toast(L(`${dCount(pick.length,c.c)} launched.`,`Выпущено: ${dCount(pick.length,c.c)}.`));return true;}
    case 'dockone':{
      const f=F(c.f);if(!f||f.cls==='leviathan'||f.settled)return false;
      if(c.ch!=null){const ch=F(c.ch);if(!ch||ch.cls!=='charger'||!ch.settled||ch.node!==f.node||f.cls==='charger')return false;(ch.dock=ch.dock||[]).push({c:f.cls,...takeDrone(f)});return true;}
      const st=S(c.s);if(!st||st.s.state!=='done'||st.n.id!==f.node||!dockKinds(st.s).includes(f.cls))return false;
      st.s.hangar[f.cls].push(takeDrone(f));return true;}
    case 'upgrade':{
      const st=S(c.s);if(!st||st.s.type!=='upgrade'||st.s.state!=='done'||!DR[c.c]||!dU(c.c))return false;
      const d=st.s.hangar[c.c].find(d=>!d.up&&!d.upg);if(!d)return deny(L('Dock a drone of this type here first.','Сначала пристыкуйте сюда дрона этого типа.'));
      if(!canPayAt(pid,st.n.id,DR[c.c].cost))return deny(L('Not enough resources for the upgrade.','Не хватает ресурсов на улучшение.'));
      payAt(pid,st.n.id,DR[c.c].cost);d.upg=true;st.s.last=c.c;return true;}
    case 'loopq':p.loopQ=!!c.v;return true;
    case 'barrier':{const st=S(c.s);if(!st||st.s.type!=='barrier')return false;st.s.off=!c.on;return true;}
    case 'settle':{
      const f=F(c.f);if(!f||f.cls!=='charger')return false;
      if(c.v){if(f.settled)return false;f.settled=true;f.settledAt=G.turn;f.path=[];f.mergeInto=null;f.dock=f.dock||[];return true;}
      if(!f.settled)return false;
      if(G.turn<=f.settledAt)return deny(L('A charger that has just settled stays for at least a turn.','Только что севший зарядчик должен простоять хотя бы ход.'));
      if(G.fleets.some(g=>g.cls==='leviathan'&&g.owner===pid&&g.node===f.node))return deny(L("The charger can't stand up while your leviathan is on its tile.",'Зарядчик не может встать, пока на его клетке ваш левиафан.'));
      if((f.dock||[]).length)return deny(L('Launch the drones docked in it first.','Сначала выпустите пристыкованные дроны.'));
      f.settled=false;return true;}
    case 'selfdestruct':{
      const f=F(c.f);if(!f)return false;const k=emptyDrones(f);if(!k)return false;
      const per=f.hp/f.count;f.en=f.en.filter(e=>e>0);f.count-=k;f.hp-=per*k;if(f.count<=0)G.fleets=G.fleets.filter(g=>g!==f);
      toast(L(`${dCount(k,f.cls)} blew themselves up.`,`Взорвались: ${dCount(k,f.cls)}.`));return true;}
""")
# fleets with empty drones, or a settled charger, can't take orders
rep("    case 'fmove':{const f=F(c.f);return f?orderFleetMove(f,+c.to):false;}",
    "    case 'fmove':{const f=F(c.f);if(!f)return false;if(f.settled)return deny(L('The charger is settled. Stand it up first.','Зарядчик сидит. Сначала поднимите его.'));if(stuck(f))return deny(L(`${plural(emptyDrones(f),'drone')} in this fleet ${emptyDrones(f)>1?'have':'has'} no energy, so the fleet can't move. Bring it back to your network, or blow up the empty drones.`,`В этом флоте без энергии: ${cnt(emptyDrones(f),'drone')}. Флот не может двигаться. Верните его в сеть или взорвите пустые дроны.`));return orderFleetMove(f,+c.to);}")
rep("    case 'bomb':{const f=F(c.f);if(!f||!ARTY(f.cls))return false;",
    "    case 'bomb':{const f=F(c.f);if(!f||!ARTY(f.cls))return false;if(stuck(f))return deny(L(\"Drones in this fleet have no energy, so it can't fire.\",'В этом флоте есть дроны без энергии, он не может стрелять.'));")
# one charger per tile, everywhere tile limits are checked
rep("if(tileCount(u.owner,nx,u.cls,u)+u.count>tileCap(u.owner)){", "if(tileCount(u.owner,nx,u.cls,u)+u.count>capFor(u.owner,u.cls)){")
rep("if(id!==f.node&&tileCount(pid,id,f.cls,f)+f.count>tileCap(pid))", "if(id!==f.node&&tileCount(pid,id,f.cls,f)+f.count>capFor(pid,f.cls))")

# ---------------------------------------------------------------- boreholes: one per planet centre, x1..x5 price, at most five
cut("function stCost(pid,type){", "const fitsHere=", """function stCost(pid,type){
  const base=ST[type].cost;if(type!=='borehole')return base;
  return Object.fromEntries(Object.entries(base).map(([r,v])=>[r,v*(boreholes(pid)+1)]));
}
const boreholes=pid=>G.nodes.reduce((a,n)=>a+(n.owner===pid?n.stations.filter(s=>s.type==='borehole'&&s.state!=='destroyed').length:0),0);
""")
rep("  if(n.stations.length>=SLOTS)return L('All 4 build slots are used','Все 4 места для станций заняты');",
    "  if(type==='borehole'&&n.stations.some(x=>x.type==='borehole'))return L('Only one borehole per planet centre','Только одна скважина на центр планеты');\n  if(type==='borehole'&&boreholes(pid)>=5)return L('You already have 5 boreholes','У вас уже 5 скважин');\n  if(n.stations.length>=SLOTS)return L('All 4 build slots are used','Все 4 места для станций заняты');")
rep("    if(!fitsHere(n,k))continue;\n", "    if(!fitsHere(n,k))continue;\n    if(k==='borehole'&&n.stations.some(x=>x.type==='borehole'))continue;\n")

# ---------------------------------------------------------------- charger docks recharge, enemy fleets wipe them
rep("  // docked drones recharge: +1 a turn in a barrack or upgrade station",
    "  // drones docked in a settled charger recharge 0.5 a turn (1 when an upgraded charger links to your network)\n  for(const f of G.fleets)if(f.owner===pid&&f.cls==='charger'&&f.settled)for(const d of f.dock||[])d.en=Math.min(BATT,d.en+(f.up&&G.conn[pid].has(f.node)?1:.5));\n  // docked drones recharge: +1 a turn in a barrack or upgrade station")
rep("  // spies caught by enemy war drones or X-ray turrets",
    "  // drones docked in a charger are lost when enemy war drones are on its tile\n  for(const f of G.fleets)if(f.cls==='charger'&&f.settled&&(f.dock||[]).length&&warFleetsAt(f.owner,f.node).length){log(L(`${plural(f.dock.length,'drone')} docked in ${whose(f.owner).toLowerCase()} charger at ${lc(nodeName(G.nodes[f.node]))} were destroyed by enemy fleets.`,`Пристыкованные к зарядчику (${f.owner===ME?'ваш':pShort(P(f.owner))}) дроны на ${lc(nodeName(G.nodes[f.node]))} уничтожены: ${cnt(f.dock.length,'drone')}.`),'battle',f.node,[f.owner]);f.dock=[];}\n  // spies caught by enemy war drones or X-ray turrets")

# ---------------------------------------------------------------- fleet menu
cut("function fleetRow(f,n){", "// the task buttons a worker can use", r"""function fleetRow(f,n){
  const D=DR[f.cls],mine=n.owner===ME;
  const kaz=mine&&live(n,D.ground?'rbarracks':'kazarm').length;
  const btn=(a,l,cls)=>`<button class="btn small ${cls||''}" type="button" data-a="${a}" data-f="${f.id}">${l}</button>`;
  const b=[];
  if(f.cls==='charger'&&f.settled)b.push(btn('fsettle0',L('Stand up','Встать')));
  else{b.push(btn('fmove',L('Move','Лететь')));if(f.cls==='charger')b.push(btn('fsettle1',L('Settle','Сесть')));}
  if(ARTY(f.cls))b.push(btn('fbomb',L('Bombard','Обстрел')));
  if(f.path.length||f.bombard!=null)b.push(btn('fstop',L('Stop','Стоп'),'quiet'));
  if(f.count>1)b.push(btn('fsplit',L('Split','Разделить')));
  if(kaz&&f.cls!=='leviathan')b.push(btn('fdis',L('Disassemble','Разобрать'),'quiet'));
  if(stuck(f))b.push(btn('fboom',L('Self-destruct','Взорваться'),'danger'));
  let status=`${HEART} ${Math.round(f.hp)}/${fleetMax(f)}`;
  if(f.cls!=='leviathan')status+=` · ${BOLT}${avgEn(f)}/${BATT}`;
  if(f.cls!=='spy'&&f.cls!=='leviathan'&&!fleetOnGrid(f))status+=' · <span class="warn">'+L('cut off','отрезан')+'</span>';
  if(f.settled)status+=' · '+L('settled','сидит');
  if(f.path.length)status+=' · '+(f.mergeInto?L('flying to merge','летит на объединение'):L(`moving, ${plural(f.path.length,'hop')} left`,`в пути, осталось ${cnt(f.path.length,'hop')}`));
  if(f.bombard!=null)status+=' · '+L('bombarding ','обстреливает: ')+lc(nodeName(G.nodes[f.bombard]));
  let h=`<div class="row"><div class="grow"><b>${dN(f.cls)}${f.up?' ↑':''}</b> ×${f.count}<br><span class="sub">${status}</span></div><div class="acts">${b.join('')}</div>`;
  if(f.cls!=='leviathan')h+=`<div class="full mono sub" title="${L('Energy of each drone','Энергия каждого дрона')}">${BOLT} ${f.en.map(e=>`<span class="${e<=0?'bad':e<2?'warn':''}">${e}</span>`).join(' · ')}</div>`;
  if(G.splitOpen===f.id){const half=Math.floor(f.count/2);h+=`<div class="full"><input type="range" id="splitN" min="1" max="${f.count-1}" value="${half}" aria-label="${L('Drones to split off','Сколько отделить')}"><span class="mono" id="splitLbl" style="white-space:nowrap">${f.count-half} | ${half}</span><button class="btn small primary" type="button" data-a="fsplitgo" data-f="${f.id}">${L('Split','Разделить')}</button></div>`;}
  return h+`</div>`;
}
// the "Fleets nearby" list on top of a barrack, upgrade station or settled charger: dock drones one at a time
function nearbyHtml(n,kinds,attr){
  const fl=G.fleets.filter(f=>f.owner===ME&&f.node===n.id&&kinds.includes(f.cls)&&!f.settled);
  return `<div class="sec"><h3>${L('Fleets nearby','Флоты рядом')}</h3>${fl.length?fl.map(f=>`<div class="row"><div class="grow"><b>${dN(f.cls)}${f.up?' ↑':''}</b> ×${f.count} <span class="sub">${HEART}${Math.round(f.hp)} · ${BOLT}${avgEn(f)}</span></div><button class="btn small" type="button" data-a="dockone" data-f="${f.id}" ${attr}>${L('Dock one','Пристыковать одного')}</button></div>`).join(''):`<p class="sub" style="margin:0">${L('No fleets of yours that can dock here.','Здесь нет ваших флотов, которые могут пристыковаться.')}</p>`}</div>`;
}
// docked drones, by type, with a Launch button that opens the list of each one
function dockedHtml(list,attr){
  const by={};for(const d of list)(by[d.c]=by[d.c]||[]).push(d);
  const types=Object.keys(by);
  return `<div class="sec"><h3>${L('Docked','Пристыковано')}</h3>${types.length?types.map(c=>`<div class="row"><div class="grow"><b>${dN(c)}</b> ×${by[c].length}</div><button class="btn small primary" type="button" data-a="hangar" data-c="${c}" ${attr}>${L('Launch','Выпустить')} ${by[c].length}</button></div>`).join(''):`<p class="sub" style="margin:0">${L('Nothing docked.','Ничего не пристыковано.')}</p>`}</div>`;
}
""")
rep("""  if(mine)h+=`<div class="sec">${fleetRow(f,n)}</div>`;""",
    """  if(mine)h+=`<div class="sec">${fleetRow(f,n)}</div>`;
  if(mine&&f.cls==='charger'&&f.settled){h+=nearbyHtml(n,[...SPACE,...ROVERS].filter(c=>c!=='charger'),`data-ch="${f.id}"`);h+=dockedHtml(f.dock||[],`data-ch="${f.id}"`);}""")

# ---------------------------------------------------------------- station menus
rep("  if((s.type==='kazarm'||s.type==='rbarracks')&&mine)h+=kazarmHtml(n,s);",
    "  if((s.type==='kazarm'||s.type==='rbarracks'||s.type==='upgrade')&&mine)h+=nearbyHtml(n,dockKinds(s),`data-s=\"${s.uid}\"`);\n  if((s.type==='kazarm'||s.type==='rbarracks')&&mine)h+=kazarmHtml(n,s);")
cut("  if(s.type==='upgrade'&&mine){", "  if(s.type==='storage'){", """  if(s.type==='upgrade'&&mine)h+=upgradeHtml(n,s);
""")
rep("  if(s.type==='barrier')h+=box(L('Absorbs 10 damage per battle on this asteroid.','Поглощает 10 урона в каждом бою на этом астероиде.'));",
    "  if(s.type==='barrier')h+=`<div class=\"sec\"><div class=\"row\"><div class=\"grow\">${L('Absorbs 10 damage in the first round of every battle here, and 10 of every artillery volley. Uses 1 energy a turn while on.','Поглощает 10 урона в первом раунде каждого боя здесь и 10 урона каждого залпа артиллерии. Тратит 1 энергию за ход, пока включён.')}<br><span class=\"sub\">${s.off?L('Switched off','Выключен'):s.pw===false?L('No power last turn','В прошлый ход не хватило энергии'):L('On','Включён')}</span></div>${mine?`<button class=\"btn small\" type=\"button\" data-a=\"bar\" data-s=\"${s.uid}\" data-v=\"${s.off?1:0}\">${s.off?L('Switch on','Включить'):L('Switch off','Выключить')}</button>`:''}</div></div>`;")
rep("${s.hangar[c]?' '+s.hangar[c]:''}</button>", "${s.hangar[c].length?' '+s.hangar[c].length:''}</button>")
rep("const D=DR[c],room=Math.max(0,cap-tileCount(ME,n.id,c)),k=Math.min(s.hangar[c],room);", "const D=DR[c],k=s.hangar[c].length;")
rep("data-a=\"kasm\" data-s=\"${s.uid}\" data-c=\"${c}\" ${k?'':'disabled'}>", "data-a=\"hangar\" data-s=\"${s.uid}\" data-c=\"${c}\" ${k?'':'disabled'}>")
rep("${i===0?` <span class=\"sub\">· ${L('ready next turn','будет готов в следующем ходу')}</span>`:''}",
    "${i===0?` <span class=\"sub\">· ${(DR[c].build||1)-(s.qprog||0)>1?L(`ready in ${(DR[c].build||1)-(s.qprog||0)} turns`,`будет готов через ${cnt((DR[c].build||1)-(s.qprog||0),'turn')}`):L('ready next turn','будет готов в следующем ходу')}</span>`:''}")
rep("L(`Up to ${cap} of one type per tile. Launched units cost ${BOLT} upkeep each turn.`,`До ${cap} одного типа на клетку. Выпущенные единицы требуют ${BOLT} содержания каждый ход.`)",
    "L(`Up to ${cap} of one type per tile, one charger. Launched units use ${BOLT}0.5 a turn (1 for war drones on a planet). Docked ones use none and recharge 1 a turn.`,`До ${cap} одного типа на клетку, один зарядчик. Выпущенные тратят ${BOLT}0,5 за ход (боевые дроны на планете — 1). Пристыкованные не тратят и заряжаются на 1 за ход.`)")
rep("// small pop-up layer on top of menus: a drone's blueprint, or a tech", r"""// upgrade station: like a barrack, a card per type with Upgrade (a docked drone, done next turn) and Launch
function upgradeHtml(n,s){
  const w=walletAt(ME,n.id),list=dockKinds(s).filter(c=>canMake(ME,c)&&dU(c)&&(!DR[c].ground||has(ME,'rovers')));
  let h=`<div class="sec"><h3>${L('Upgrades · each takes one turn','Улучшения · каждое за один ход')}</h3><div class="dgrid">`;
  for(const c of list){
    const docked=s.hangar[c],ready=docked.filter(d=>!d.up&&!d.upg).length,busy=docked.filter(d=>d.upg).length;
    h+=`<div class="dcard"><button class="dname" type="button" data-a="dinfo" data-c="${c}">${dN(c)} <span aria-hidden="true">›</span></button>${costHtml(DR[c].cost,w)}<span class="sub">${dU(c)}</span>${busy?`<span class="sub warn">${L(`${busy} upgrading`,`улучшается: ${busy}`)}</span>`:''}<div class="dbtns"><button class="btn small" type="button" data-a="kupg" data-s="${s.uid}" data-c="${c}" ${ready&&canPayAt(ME,n.id,DR[c].cost)?'':'disabled'}>${L('Upgrade','Улучшить')}${ready?' '+ready:''}</button><button class="btn small primary" type="button" data-a="hangar" data-s="${s.uid}" data-c="${c}" ${docked.length?'':'disabled'}>${L('Launch','Выпустить')}${docked.length?' '+docked.length:''}</button></div></div>`;
  }
  return h+`</div><p class="sub" style="margin:0">${L('Dock drones here from Fleets nearby, upgrade them, then launch them.','Пристыкуйте дроны из «Флоты рядом», улучшите и выпустите.')}</p></div>`;
}
// small pop-up layer on top of menus: a drone's blueprint, a tech, or the list of docked drones of one type""")
rep("  if(m.type==='drone'){\n", r"""  if(m.type==='hangar'){
    let list,attr,title;
    if(m.ch!=null){const ch=G.fleets.find(f=>f.id===m.ch);list=ch?(ch.dock||[]).filter(d=>d.c===m.c):[];attr=`data-ch="${m.ch}"`;}
    else{const f=findStation(m.s);list=f?f.s.hangar[m.c]:[];attr=`data-s="${m.s}"`;}
    h+=`<h2>${dN(m.c)} · ${L('docked','пристыковано')} ${list.length}</h2>`;
    h+=list.length?`<div class="sec">${list.map((d,i)=>`<div class="row"><div class="grow mono">${HEART} ${Math.round(d.hp)}/${DR[m.c].hp} · ${BOLT} ${d.en}/${BATT}${d.up?' · ↑':''}${d.upg?` · <span class="warn">${L('upgrading','улучшается')}</span>`:''}</div><button class="btn small" type="button" data-a="hlaunch" data-c="${m.c}" data-i="${i}" ${attr} ${d.upg?'disabled':''}>${L('Launch','Выпустить')}</button></div>`).join('')}</div><div class="opts"><button class="btn primary" type="button" data-a="hlaunch" data-c="${m.c}" data-i="-1" ${attr}>${L('Launch all','Выпустить всех')}</button></div>`:`<p class="sub" style="margin:0">${L('Nothing docked.','Ничего не пристыковано.')}</p>`;
  }else if(m.type==='drone'){
""")

# ---------------------------------------------------------------- interface actions
rep("    case 'kasm':order({t:'launch',s:+d.s,c:d.c});break;\n", """    case 'hangar':G.popup={type:'hangar',c:d.c,s:d.s!=null?+d.s:null,ch:d.ch!=null?+d.ch:null};G.popupAt=performance.now();break;
    case 'hlaunch':{order({t:'launch',c:d.c,i:+d.i,s:d.s!=null?+d.s:undefined,ch:d.ch!=null?+d.ch:undefined});if(+d.i<0)G.popup=null;break;}
    case 'dockone':order({t:'dockone',f:+d.f,s:d.s!=null?+d.s:undefined,ch:d.ch!=null?+d.ch:undefined});break;
    case 'kupg':order({t:'upgrade',s:+d.s,c:d.c});break;
    case 'bar':order({t:'barrier',s:+d.s,on:d.v==='1'});break;
    case 'fsettle1':order({t:'settle',f:+d.f,v:true});break;
    case 'fsettle0':order({t:'settle',f:+d.f,v:false});break;
    case 'fboom':order({t:'selfdestruct',f:+d.f});break;
""")

# stations with something in their queue get the yellow "busy" ring
rep("      stationIcon(ctx,s,sx,sy,sz,n.owner!=null?P(n.owner).color:'#8190ab');",
    "      stationIcon(ctx,s,sx,sy,sz,n.owner!=null?P(n.owner).color:'#8190ab');\n      if(n.owner===ME&&s.state==='done'&&stationBusy(s)){ctx.beginPath();ctx.arc(sx,sy,13.5*sz,0,Math.PI*2);ctx.strokeStyle=BUSY;ctx.lineWidth=1.8;ctx.stroke();}")

# ---------------------------------------------------------------- settings: infinite queues
rep("const settings={music:.5,sfx:.6,keepFire:false,", "const settings={music:.5,sfx:.6,keepFire:false,loopQ:false,")
i = s.index("<div class=\"opts\"><button class=\"btn primary\" type=\"button\" data-a=\"m-back\">")
s = s[:i] + """<div class="field"><div class="lab"><span>${L('Infinite queues','Бесконечные очереди')}</span><button type="button" class="switch ${settings.loopQ?'on':''}" role="switch" aria-checked="${settings.loopQ}" data-a="s-loop" aria-label="${L('Infinite queues','Бесконечные очереди')}"><i></i></button></div><p class="sub" style="margin:0">${L('Barracks and upgrade stations repeat the last drone, one a turn, whenever you can pay for it.','Казармы и станции улучшений повторяют последний дрон, по одному за ход, когда хватает ресурсов.')}</p></div>
      """ + s[i:]
rep("    case 's-fire':", "    case 's-loop':settings.loopQ=!settings.loopQ;saveSettings();showMenu('settings');if(G&&P(ME).alive)order({t:'loopq',v:settings.loopQ});break;\n    case 's-fire':")
rep("  G.conn=G.players.map(p=>connSet(p.id));\n  takeSnapshot();", "  G.conn=G.players.map(p=>connSet(p.id));\n  takeSnapshot();\n  if(settings.loopQ)order({t:'loopq',v:true});")

# ---------------------------------------------------------------- the AI and old code that counted docked drones as numbers
rep("future+=[...s.queue,...CLS.flatMap(c=>Array(s.hangar[c]).fill(c))]", "future+=[...s.queue,...CLS.flatMap(c=>s.hangar[c].map(()=>c))]")
rep("!s.hangar.spy&&", "!s.hangar.spy.length&&")
rep(".sort((a,b)=>s.hangar[b]-s.hangar[a])", ".sort((a,b)=>s.hangar[b].length-s.hangar[a].length)")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
