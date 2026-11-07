"""Draft 9 energy rework: drone batteries, new costs, 100 combined resources, docked drones as individual units."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:80]}')
    s = s.replace(a, b)


rep("const BASE_RES=60,BASE_ENERGY=30,CORE_HP=40,SLOTS=4;",
    "// BASE_RES: resources the core holds in total (all four together). BATT: energy each war drone or rover can carry.\nconst BASE_RES=100,BASE_ENERGY=30,CORE_HP=40,SLOTS=4,BATT=5;")
rep("alive:true,energy:20,", "alive:true,energy:30,")

# docked drones are now individual units: hangar[type] is a list of {hp,en,up,upg}
rep("Object.fromEntries(CLS.map(c=>[c,0]))", "emptyHangar()", 4)
rep("function newFleet(pid,cls,k,node,up){return {id:UID++,owner:pid,cls,count:k,hp:k*DR[cls].hp,node,",
    "const emptyHangar=()=>Object.fromEntries(CLS.map(c=>[c,[]]));\nconst newDrone=c=>({hp:DR[c].hp,en:BATT,up:false});\nfunction newFleet(pid,cls,k,node,up){return {id:UID++,owner:pid,cls,count:k,hp:k*DR[cls].hp,en:Array(k).fill(BATT),node,")

# ---------------------------------------------------------------- economy
a = s.index("function sharedCap(pid){")
b = s.index("const storeCap=n=>")
s = s[:a] + """// Draft 9: the core holds 100 resources in total; each storage adds 30 and a captured core adds 100
function sharedCap(pid){let k=0;for(const id of G.conn[pid]||[]){const n=G.nodes[id];k+=30*live(n,'storage').length+(n.type==='captured'?100:0);}return k;}
const resTotal=p=>RES.reduce((a,r)=>a+p.res[r],0);
const resCap=pid=>BASE_RES+sharedCap(pid);
const overflow=p=>Math.max(0,resTotal(p)-resCap(p.id));
function addRes(p,r,amt){const room=Math.max(0,resCap(p.id)-resTotal(p));const a=Math.max(0,Math.min(amt,room));p.res[r]+=a;return a;}
function clipRes(p){const lost={};let over=resTotal(p)-resCap(p.id);while(over>0){const r=RES.reduce((a,b)=>p.res[a]>=p.res[b]?a:b);p.res[r]--;lost[r]=(lost[r]||0)+1;over--;}return lost;}
function energyCap(pid){let c=BASE_ENERGY;for(const id of G.conn[pid]||[])c+=30*live(G.nodes[id],'estorage').length;return c;}
// the core makes 10, each generator 5 and each captured core 10
function energyProd(pid){if(!P(pid).alive)return 0;let e=10;for(const id of G.conn[pid]||[]){const n=G.nodes[id];e+=5*live(n,'generator').length+(n.type==='captured'?10:0);}return e;}
// energy one drone of this fleet uses a turn: 0.5, or 1 for a war drone on a planet tile; leviathans and settled chargers use none
const droneUse=f=>f.cls==='leviathan'||f.settled?0:(!DR[f.cls].ground&&G.nodes[f.node].planet!=null?1:.5);
// fleets on their owner's connected network are powered by the core; spies always are
const fleetOnGrid=f=>f.cls==='spy'||(G.conn[f.owner]&&G.conn[f.owner].has(f.node));
const emptyDrones=f=>(f.en||[]).filter(e=>e<=0).length;
const poweredDrones=f=>f.cls==='leviathan'?f.count:f.count-emptyDrones(f);
// a fleet with an empty drone can't move or fire until it is recharged, or the empty drones blow themselves up
const stuck=f=>f.cls!=='leviathan'&&emptyDrones(f)>0;
const avgEn=f=>f.en&&f.en.length?Math.round(f.en.reduce((a,e)=>a+e,0)/f.en.length*10)/10:0;
function energyUse(pid){
  let u=0;const conn=G.conn[pid];
  for(const f of G.fleets)if(f.owner===pid&&fleetOnGrid(f))u+=droneUse(f)*f.count;
  for(const w of G.workers){if(w.owner!==pid||w.path.length||!conn.has(w.node))continue;
    if(w.task==='build')u+=1;if(w.task==='mine')u+=has(pid,'drills')?.5:1;}
  for(const id of conn)for(const st of live(G.nodes[id],'barrier'))if(!st.off)u+=1;
  return u;
}
// pay energy for something standing on tile id: from the core's grid, or from a cut-off cluster's own batteries
function payEnergy(pid,id,amt){
  const p=P(pid);if(G.conn[pid].has(id)){if(p.energy<amt)return false;p.energy=Math.round((p.energy-amt)*10)/10;return true;}
  if(G.nodes[id].owner!==pid)return false;
  const cl=clusterOf(pid,id);if(cl.reduce((a,x)=>a+x.estore,0)<amt)return false;
  let need=amt;for(const x of cl){const t=Math.min(need,x.estore);x.estore-=t;need-=t;if(need<=0)break;}return true;
}
""" + s[b:]
rep("const storeCap=n=>30*live(n,'storage').length+(n.type==='captured'?60:0);", "const storeCap=n=>30*live(n,'storage').length+(n.type==='captured'?100:0);")
rep("function mergeFleets(t,s){t.count+=s.count;t.hp+=s.hp;G.fleets=G.fleets.filter(f=>f!==s);}",
    "function mergeFleets(t,s){t.count+=s.count;t.hp+=s.hp;t.en=(t.en||[]).concat(s.en||[]);G.fleets=G.fleets.filter(f=>f!==s);}\n// keep one battery entry per drone after the drone count changes\nfunction fixEn(f){f.en=f.en||[];while(f.en.length>f.count)f.en.pop();while(f.en.length<f.count)f.en.push(BATT);}")
rep("function syncFleet(f){if(f.hp>0)f.count=Math.ceil(f.hp/DR[f.cls].hp-1e-6);}", "function syncFleet(f){if(f.hp>0){f.count=Math.ceil(f.hp/DR[f.cls].hp-1e-6);fixEn(f);}}")

# combat: empty drones deal nothing, turrets need 1 energy per battle, no planet penalty any more
rep("gen+=d*f.count;if(f.cls==='siege')str+=(D.sdmg-D.dmg)*f.count;}", "const k=poweredDrones(f);gen+=d*k;if(f.cls==='siege')str+=(D.sdmg-D.dmg)*k;}")
rep("if(onPlanet&&!D.ground)d=Math.max(0,d-1);", "")
rep("if(d>0&&onPlanet&&!DR[f.cls].ground&&DR[f.cls].dmg<=1)f.hp-=1;", "")
rep("for(const t of s.turrets){if(t.hp<=0)continue;gen+=ST[t.type].dmg||0;if(t.type==='chain')chain++;}",
    "for(const t of s.turrets){if(t.hp<=0||!t.pw)continue;gen+=ST[t.type].dmg||0;if(t.type==='chain')chain++;}")
rep("    if(t.length||core){const s=side(owner);s.turrets=t;s.core=core;}",
    "    if(t.length||core){const s=side(owner);s.turrets=t;s.core=core;\n      // each turret uses 1 energy per battle; without it, it can't fire\n      for(const x of t)x.pw=x.type!=='death'&&payEnergy(owner,n.id,1);}")
rep("    const perShot=DR[f.cls].dmg-(G.nodes[f.node].planet!=null&&!DR[f.cls].ground?1:0);", "    const perShot=DR[f.cls].dmg;")
rep("    const shots=Math.min(f.count,Math.floor(p.res.iron/per));", "    const shots=Math.min(poweredDrones(f),Math.floor(p.res.iron/per));")

# barriers: only a powered barrier that is switched on absorbs damage
rep("const b=live(n,'barrier').length;", "const b=live(n,'barrier').filter(x=>x.pw).length;")
rep("const barrier=foe(tn.owner)?10*live(tn,'barrier').length:0;", "const barrier=foe(tn.owner)?10*live(tn,'barrier').filter(x=>x.pw).length:0;")

# death turret: 5 energy and 10 crystals per shot
rep("    const t=G.nodes[s.aim];s.aim=null;s.charge=5;",
    "    const t=G.nodes[s.aim];s.aim=null;\n    if(!canPayAt(n.owner,n.id,{xeno:10})||!payEnergy(n.owner,n.id,5)){log(L(`The death turret at ${lc(nodeName(n))} could not fire: it needs 5 energy and 10 Xenocrystal.`,`Турель смерти на ${lc(nodeName(n))} не выстрелила: нужно 5 энергии и 10 кристаллов.`),'warn',n.id,[n.owner]);continue;}\n    payAt(n.owner,n.id,{xeno:10});s.charge=5;")

# movement: a fleet with an empty drone stays put
rep("  for(const f of G.fleets)if(f.path.length){\n    let steps=DR[f.cls].spd;",
    "  for(const f of G.fleets)if(f.path.length&&!stuck(f)&&!f.settled){\n    let steps=DR[f.cls].spd;")

# ---------------------------------------------------------------- production
a = s.index("  // drone upkeep is paid last: a shortage damages fleets instead of halting the economy")
b = s.index("  // every worker queued this turn leaves the core together", a)
s = s[:a] + """  // drones: on the grid the core pays; otherwise, or when the grid runs short, each drone uses its own battery
  for(const f of G.fleets.filter(f=>f.owner===pid)){
    if(f.settled){f.en=f.en.map(e=>Math.min(BATT,e+.5));continue;}
    const u=droneUse(f);if(!u)continue;fixEn(f);
    const grid=fleetOnGrid(f),onCl=!grid&&clusters.get(f.node);
    const before=emptyDrones(f);
    for(let i=0;i<f.count;i++){
      if(grid&&avail>=u){avail-=u;continue;}
      if(onCl&&onCl.energy>=u){onCl.energy-=u;continue;}
      f.en[i]=Math.max(0,Math.round((f.en[i]-u)*10)/10);
    }
    if(f.cls!=='spy'&&!grid&&!f.cut)log(L(`Your ${dN(f.cls).toLowerCase()} fleet at ${lc(nodeName(G.nodes[f.node]))} is cut off from your network and runs on its batteries.`,`Флот «${dN(f.cls)}» на ${lc(nodeName(G.nodes[f.node]))} отрезан от сети и тратит свои батареи.`),'warn',f.node,[pid]);
    f.cut=!grid;
    if(emptyDrones(f)>before)log(L(`${plural(emptyDrones(f),'drone')} of your ${dN(f.cls).toLowerCase()} fleet at ${lc(nodeName(G.nodes[f.node]))} ran out of energy: the fleet can't move or fire.`,`Флот «${dN(f.cls)}» на ${lc(nodeName(G.nodes[f.node]))}: без энергии ${cnt(emptyDrones(f),'drone')}. Флот не может двигаться и стрелять.`),'warn',f.node,[pid]);
  }
  // barrack production: one drone a turn (a charger takes 2 turns); infinite queues repeat the last drone when they can pay
  for(const n of G.nodes){if(n.owner!==pid)continue;for(const st of [...live(n,'kazarm'),...live(n,'rbarracks')]){
    if(st.queue.length){const c=st.queue[0];st.qprog=(st.qprog||0)+1;if(st.qprog>=(DR[c].build||1)){st.queue.shift();st.qprog=0;st.hangar[c].push(newDrone(c));st.last=c;}}
    if(p.loopQ&&!st.queue.length&&st.last&&canMake(pid,st.last)&&canPayAt(pid,n.id,DR[st.last].cost)){payAt(pid,n.id,DR[st.last].cost);st.queue.push(st.last);}
  }}
  // upgrades finish after one turn; infinite queues start the next one of the same type
  for(const n of G.nodes){if(n.owner!==pid)continue;for(const st of live(n,'upgrade')){
    for(const c of CLS)for(const d of st.hangar[c])if(d.upg){d.upg=false;d.up=true;}
    if(p.loopQ&&st.last){const d=st.hangar[st.last].find(d=>!d.up&&!d.upg);if(d&&canPayAt(pid,n.id,DR[st.last].cost)){payAt(pid,n.id,DR[st.last].cost);d.upg=true;}}
  }}
  // docked drones recharge: +1 a turn in a barrack or upgrade station
  for(const n of G.nodes){if(n.owner!==pid)continue;for(const st of n.stations)if(st.state==='done')for(const c of CLS)for(const d of st.hangar[c])d.en=Math.min(BATT,d.en+1);}
  // spare grid energy tops up the batteries of drones on the grid, half a point at a time, at random
  {const spare=()=>Math.max(0,avail-p.energy);const want=[];
    for(const f of G.fleets)if(f.owner===pid&&fleetOnGrid(f)&&f.cls!=='leviathan')for(let i=0;i<f.count;i++)if(f.en[i]<BATT)want.push([f,i]);
    while(want.length&&spare()>=.5){const k=Math.floor(rnd()*want.length),[f,i]=want[k];f.en[i]=Math.min(BATT,f.en[i]+.5);avail-=.5;if(f.en[i]>=BATT)want.splice(k,1);}
    // a cut-off cluster with spare energy charges the drones inside it first
    for(const cl of new Set(clusters.values())){const ids=new Set(cl.ids.map(x=>x.id));const w2=[];
      for(const f of G.fleets)if(f.owner===pid&&!fleetOnGrid(f)&&ids.has(f.node))for(let i=0;i<f.count;i++)if(f.en[i]<BATT)w2.push([f,i]);
      while(w2.length&&cl.energy>=.5){const k=Math.floor(rnd()*w2.length),[f,i]=w2[k];f.en[i]=Math.min(BATT,f.en[i]+.5);cl.energy-=.5;if(f.en[i]>=BATT)w2.splice(k,1);}}
  }
""" + s[b:]
# cut-off clusters also get 10 from a captured core
rep("const cl={ids,energy:ids.reduce((a,x)=>a+x.estore+5*live(x,'generator').length,0)};",
    "const cl={ids,energy:ids.reduce((a,x)=>a+x.estore+5*live(x,'generator').length+(x.type==='captured'?10:0),0)};")
# barriers are paid first: they defend
rep("  // workers that arrived this turn start working next turn (same rule for people and AI)\n  const ws=G.workers.filter(w=>w.owner===pid&&!w.path.length&&!(w.trail&&w.trail.length>1));",
    "  // switched-on barriers are paid first; an unpaid barrier is down for the next turn\n  for(const n of G.nodes)if(n.owner===pid)for(const st of live(n,'barrier'))st.pw=!st.off&&spend(n.id,1);\n  // workers that arrived this turn start working next turn (same rule for people and AI)\n  const ws=G.workers.filter(w=>w.owner===pid&&!w.path.length&&!(w.trail&&w.trail.length>1));")
rep("  p.energy=Math.max(0,Math.min(energyCap(pid),Math.round(avail*10)/10));", "  p.energy=Math.max(0,Math.min(energyCap(pid),Math.round(avail*10)/10));")

# AI resource checks use the combined limit
rep("const full=RES.some(r=>p.res[r]>=BASE_RES-5);", "const full=resTotal(p)>=resCap(pid)-5;")
rep("for(const w of ws)if(w.task==='mine'&&p.res[G.nodes[w.node].res]>=BASE_RES&&sharedCap(pid)-overflow(p)<=0)w.task='idle';",
    "for(const w of ws)if(w.task==='mine'&&!G.nodes[w.node].center&&resTotal(p)>=resCap(pid))w.task='idle';")
rep("      const full=p.res[n.res]>=BASE_RES;", "      const full=resTotal(p)>=resCap(pid);")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
