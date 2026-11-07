"""Draft 9 AI: new rules (energy, docking, upgrades, planet movement, leviathans) and basic battle sense."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:80]}')
    s = s.replace(a, b)


a = s.index("  // upgrade one parked drone per turn when resources are comfortable")
b = s.index("  const targeted=new Set(ws.filter", a)
s = s[:a] + r"""  // upgrade stations: dock a drone and upgrade it (ready next turn), and launch the ones that are done
  for(const n of G.nodes){if(n.owner!==pid)continue;for(const st of live(n,'upgrade')){
    for(const c of CLS){const ready=st.hangar[c].filter(d=>!d.upg);if(ready.length&&!leviHere(pid,n.id)){const k=Math.min(ready.length,capFor(pid,c)-tileCount(pid,n.id,c));if(k>0){const go=ready.slice(0,k);st.hangar[c]=st.hangar[c].filter(d=>!go.includes(d));launchDrones(pid,c,n.id,go);}}}
    if(!DF.upgrade)continue;
    const f=G.fleets.find(f=>f.owner===pid&&f.node===n.id&&!f.up&&!f.path.length&&dU(f.cls)&&dockKinds(st).includes(f.cls));
    if(f&&p.res.iron>=30&&RES.every(r=>p.res[r]>=(DR[f.cls].cost[r]||0)+8)){payAt(pid,n.id,DR[f.cls].cost);const d=takeDrone(f);d.upg=true;st.hangar[f.cls].push(d);}
  }}
  // death turrets fire at a neighbour full of enemies, never at their own units (each shot needs 10 Xenocrystal and 5 energy)
  for(const n of G.nodes){if(n.owner!==pid||p.res.xeno<10||p.energy<5)continue;for(const s of n.stations){
    if(s.type!=='death'||s.state!=='done'||s.charge>0||s.aim!=null)continue;
    let best=null,bs=3;
    for(const id of n.nbr){const t=G.nodes[id];
      if(t.owner===pid||G.fleets.some(f=>f.node===id&&f.owner===pid)||G.workers.some(w=>w.node===id&&w.owner===pid))continue;
      const sc=G.fleets.filter(f=>f.node===id&&f.cls!=='spy').reduce((a,f)=>a+f.count,0)+G.workers.filter(w=>w.node===id).length+(t.owner!=null?2*t.stations.filter(x=>x.state!=='destroyed').length:0);
      if(sc>bs){bs=sc;best=id;}}
    if(best!=null)s.aim=best;
  }}
  const V=vis(pid);
  // spies fly towards the nearest enemy core and watch it
  for(const f of G.fleets.filter(f=>f.owner===pid&&f.cls==='spy'&&!f.path.length)){
    const RS=routeSet(f,pid),d=distMap(f.node,RS);let tgt=null,bd=Infinity;
    for(const q of G.players)if(q.alive&&q.id!==pid&&RS.has(q.core)){const c=d.get(q.core);if(c!=null&&c<bd){bd=c;tgt=q.core;}}
    if(tgt==null){for(const [id,dd] of d)if(!p.explored.has(id)&&dd>0&&dd<bd){bd=dd+1;tgt=id;}}
    if(tgt!=null&&bd>1){const path=findPath(f.node,tgt,RS);if(path)f.path=path.slice(0,-1);}
  }
  const mine=G.fleets.filter(f=>f.owner===pid);
  for(const f of mine)for(const g of mine){if(f===g||f.hp<=0||g.hp<=0||f.cls!==g.cls||f.up!==g.up||f.node!==g.node||f.path.length||g.path.length||f.cls==='charger'||f.cls==='leviathan')continue;if(f.count+g.count>capFor(pid,f.cls))continue;mergeFleets(f,g);g.hp=0;}
  // drones with empty batteries blow up so the rest of their fleet can move again
  for(const f of G.fleets.filter(f=>f.owner===pid&&stuck(f)&&f.count>emptyDrones(f))){const k=emptyDrones(f),per=f.hp/f.count;f.en=f.en.filter(e=>e>0);f.count-=k;f.hp-=per*k;}
  const myF=G.fleets.filter(f=>f.owner===pid);
  const total=myF.filter(f=>DR[f.cls].dmg>0).reduce((a,f)=>a+f.count,0);
  const threat=DF.react&&G.fleets.find(f=>f.owner!==pid&&f.cls!=='spy'&&V.has(f.node)&&(f.node===p.core||core.nbr.includes(f.node)));
  // fighting strength, roughly damage times health; for a tile, everything hostile to us that we can see there
  const pw=(dmg,hp)=>dmg*hp;
  const ownPower=id=>{let d=0,h=0;for(const f of G.fleets)if(f.owner===pid&&f.node===id&&f.cls!=='spy'){d+=DR[f.cls].dmg*poweredDrones(f);h+=f.hp;}return pw(d,h);};
  const enemyPower=id=>{let d=0,h=0;const n=G.nodes[id];
    for(const f of G.fleets)if(f.owner!==pid&&f.node===id&&f.cls!=='spy'&&V.has(id)){d+=DR[f.cls].dmg*poweredDrones(f);h+=f.hp;}
    if(n.owner!=null&&n.owner!==pid){for(const t of liveTurrets(n)){d+=ST[t.type].dmg||(t.type==='chain'?2:0);h+=t.hp;}if(n.type==='core'&&n.coreHp>0){d+=2;h+=n.coreHp;}}
    return pw(d,h);};
  const homeOf=f=>{const RS=routeSet(f,pid);const d=distMap(f.node,RS);let best=null,bd=Infinity;for(const [id,dd] of d)if(G.conn[pid].has(id)&&dd<bd&&!leviBlocks(f,id)){bd=dd;best=id;}return best;};
  // enough battery to get there, fight and come back (0.5 a turn each way, plus a margin)
  const canReach=(f,path)=>{if(f.cls==='leviathan'||!path)return !!path;const turns=Math.ceil(path.length/Math.max(1,DR[f.cls].spd));return Math.min(...f.en)>=turns+1;};
  const nearestEnemy=(f,needTurret)=>{const RS=routeSet(f,pid),d=distMap(f.node,RS);let best=null,bd=Infinity;for(const [id,dd] of d){const m=G.nodes[id];if(m.owner!=null&&m.owner!==pid&&(!needTurret||liveTurrets(m).length)&&dd<bd){best=id;bd=dd;}}return best;};
  for(const f of myF){
    if(f.path.length||f.cls==='spy'||f.settled||stuck(f))continue;
    const n=G.nodes[f.node],RS=routeSet(f,pid);
    if(DR[f.cls].ground){aiRover(f,pid);continue;}
    // low batteries off the network: head home to recharge
    if(f.cls!=='leviathan'&&!fleetOnGrid(f)&&Math.min(...f.en)<=2){const h=homeOf(f);if(h!=null){f.path=findPath(f.node,h,RS)||[];f.bombard=null;}continue;}
    // a stronger enemy next door: fall back towards the core
    const danger=n.nbr.filter(id=>enemyPower(id)>ownPower(f.node)*1.2);
    if(danger.length&&f.node!==p.core&&f.cls!=='leviathan'){f.path=findPath(f.node,p.core,RS)||[];f.bombard=null;continue;}
    if(f.cls==='repair'){const lead=myF.filter(g=>g.cls!=='repair'&&g.cls!=='charger').sort((a,b)=>b.count-a.count)[0];if(lead&&lead.node!==f.node)f.path=findPath(f.node,lead.node,RS)||[];continue;}
    if(f.cls==='charger')continue;
    if(threat&&f.node!==p.core){f.path=findPath(f.node,p.core,RS)||[];f.bombard=null;continue;}
    if(f.cls==='catapult'){
      const t=nearestEnemy(f,true);if(t==null)continue;
      if(n.nbr.includes(t)){f.bombard=t;continue;}
      const path=findPath(f.node,t,RS);if(path&&path.length>1&&canReach(f,path))f.path=path.slice(0,-1);
      continue;
    }
    if(n.owner!=null&&n.owner!==pid)continue;
    if(threat||total<DF.attackAt)continue;
    // attack the nearest enemy tile we expect to beat; otherwise explore
    const d=distMap(f.node,RS);let t=null,bd=Infinity;
    for(const [id,dd] of d){const m=G.nodes[id];if(dd===0||dd>=bd)continue;
      const hostile=(m.owner!=null&&m.owner!==pid)||G.fleets.some(g=>g.owner!==pid&&g.node===id&&g.cls!=='spy'&&V.has(id));
      if(!hostile)continue;
      if(enemyPower(id)*1.4>=pw(myF.filter(g=>g.node===f.node&&g.cls!=='spy').reduce((a,g)=>a+DR[g.cls].dmg*poweredDrones(g),0),myF.filter(g=>g.node===f.node).reduce((a,g)=>a+g.hp,0)))continue;
      bd=dd;t=id;}
    if(t==null){for(const [id,dd] of d)if(!p.explored.has(id)&&dd>0&&dd<bd&&tileCount(pid,id,f.cls,f)+f.count<=capFor(pid,f.cls)){bd=dd;t=id;}}
    if(t!=null){const path=findPath(f.node,t,RS);if(canReach(f,path))f.path=path;}
  }
  // workers keep away from enemy war fleets: on or next to one without an escort or a turret, they pull back
  const dangerW=new Set();for(const f of G.fleets)if(f.owner!==pid&&f.cls!=='spy'&&DR[f.cls].dmg>0&&V.has(f.node)){dangerW.add(f.node);for(const x of G.nodes[f.node].nbr)dangerW.add(x);}
  const guardedW=id=>G.fleets.some(f=>f.owner===pid&&f.node===id&&DR[f.cls].dmg>0)||(G.nodes[id].owner===pid&&armed(G.nodes[id]));
  for(const w of ws){
    const at=w.path.length?w.path[w.path.length-1]:w.node;
    if(!dangerW.has(at)||guardedW(at)||(w.task==='research'&&w.node===p.core))continue;
    const d=distMap(w.node,K);let best=null,bd=Infinity;
    for(const [id,dd] of d)if(!dangerW.has(id)&&G.conn[pid].has(id)&&dd<bd){bd=dd;best=id;}
    if(best==null)best=p.core;
    const path=best===w.node?[]:findPath(w.node,best,K);
    if(path){w.path=path;w.task='idle';w.then=null;w.ref=null;w.tech=null;}
  }
""" + s[b:]
# workers are never sent into danger
rep("  const send=(w,id,task,ref,tech)=>{", "  const send=(w,id,task,ref,tech)=>{if(dangerW.has(id)&&!guardedW(id))return false;")
# the AI builds the odd boomerang, and a leviathan whenever it has the stargold (Warfare)
rep("if(DF.catapult&&turretsSeen&&rnd()<.2)extra.push('catapult');", "if(DF.catapult&&turretsSeen&&rnd()<.2)extra.push('catapult');if(rnd()<.15)extra.push('boomerang');")
rep("    if(DF.death&&has(pid,'death')&&count('death')<1)wants.push('death');",
    "    if(DF.death&&has(pid,'death')&&count('death')<1)wants.push('death');\n    if(G.mode!=='conquest'&&p.gold>=ST.levi.gold)wants.unshift('levi');")
rep("const poolFor=want=>want==='borehole'?myPlanet.filter(n=>n.center):", "const poolFor=want=>want==='borehole'||want==='levi'?myPlanet.filter(n=>n.center):")
rep("      if(site){const pc=stCost(pid,want);payAt(pid,site.id,pc);const s=newStation(site,want,{paid:pc});",
    "      if(site){const pc=stCost(pid,want);payAt(pid,site.id,pc);if(ST[want].gold)p.gold-=ST[want].gold;const s=newStation(site,want,{paid:pc,gold:ST[want].gold||0});")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
