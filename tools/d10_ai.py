"""Draft 10 stage 5: AI stops stalling and shuttling; it gathers an army and pushes for real targets."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


# 1. a half-built station nobody can reach no longer blocks every other build: after 6 turns with no builder it is cancelled
rep("""  const unfinished=[];G.nodes.forEach(n=>{if(n.owner===pid)n.stations.forEach(s=>{if(s.state==='build')unfinished.push({n,s});});});
  if(!unfinished.length&&rnd()>=DF.skip){""",
    """  let unfinished=[];G.nodes.forEach(n=>{if(n.owner===pid)n.stations.forEach(s=>{if(s.state==='build')unfinished.push({n,s});});});
  for(const {n,s:st} of unfinished){
    const on=ws.some(w=>(w.task==='build'&&w.ref===st.uid)||(w.then&&w.then.task==='build'&&w.then.ref===st.uid));
    st.stall=on?0:(st.stall||0)+1;
    if(st.stall>=6){refundAt(pid,n.id,st.paid||ST[st.type].cost);p.gold+=st.gold||0;n.stations=n.stations.filter(x=>x!==st);ws.forEach(w=>{if(w.ref===st.uid){w.task='idle';w.ref=null;}});}
  }
  // stalled builds (no builder for 3+ turns) don't hold up new ones
  unfinished=unfinished.filter(({n,s:st})=>n.stations.includes(st)&&(st.stall||0)<3);
  if(!unfinished.length&&rnd()>=DF.skip){""")

# 2. the barrack deadlock: docked drones waiting for a group of 3 used up the energy budget, so nothing more was queued
rep("    for(const c of SPACE){const need=c==='spy'?1:c==='repair'||c==='catapult'?2:3;",
    "    // when the energy budget is what stops new orders, launch whatever is docked instead of waiting for a full group\n    const starved=net-future<2||s.queue.length===0&&(s.wait=(s.wait||0)+1)>=4;if(!starved)s.wait=0;\n    for(const c of SPACE){const need=starved?1:c==='spy'?1:c==='repair'||c==='catapult'?2:3;")

# 3. squadrons: gather into one army, attack together, don't freeze on enemy tiles, and stop shuttling
rep("""  for(const f of myF){
    if(f.path.length||f.cls==='spy'||f.settled||stuck(f))continue;
    const n=G.nodes[f.node],RS=routeSet(f,pid);
    if(DR[f.cls].ground){aiRover(f,pid);continue;}""",
    r"""  // the army: every war squadron that can fight in space. Pick one target it can beat together, and a staging tile next to it
  const army=myF.filter(f=>!f.settled&&!stuck(f)&&f.cls!=='spy'&&f.cls!=='repair'&&f.cls!=='charger'&&f.cls!=='catapult'&&!DR[f.cls].ground&&DR[f.cls].dmg>0);
  const armyPow=pw(army.reduce((a,f)=>a+DR[f.cls].dmg*poweredDrones(f),0),army.reduce((a,f)=>a+f.hp,0));
  let goal=p.aiGoal!=null&&G.nodes[p.aiGoal]&&isFoe(pid,G.nodes[p.aiGoal].owner??G.nodes[p.aiGoal].coreOf)?p.aiGoal:null;
  if(goal!=null&&enemyPower(goal)*1.25>armyPow)goal=null;
  if(goal==null&&army.length&&!threat&&total>=DF.attackAt){
    const d=distMap(p.core,K);let best=null,bs=-Infinity;
    for(const [id,dd] of d){const m=G.nodes[id];if(!isFoe(pid,m.owner))continue;const ep=enemyPower(id);if(ep*1.25>armyPow)continue;
      // enemy cores first, then planet centres, then anything with turrets, then plain land; closer is better
      const v=(m.type==='core'?40:m.center?25:liveTurrets(m).length?12:6)-dd*2;if(v>bs){bs=v;best=id;}}
    goal=best;
  }
  p.aiGoal=goal;
  const goalPath=goal!=null?findPath(p.core,goal,K):null,stage=goalPath&&goalPath.length>1?goalPath[goalPath.length-2]:p.core;
  const atStage=army.filter(f=>f.node===stage);
  const stagePow=pw(atStage.reduce((a,f)=>a+DR[f.cls].dmg*poweredDrones(f),0),atStage.reduce((a,f)=>a+f.hp,0));
  const strike=goal!=null&&stagePow>=enemyPower(goal)*1.25;
  for(const f of myF){
    if(f.path.length||f.cls==='spy'||f.settled||stuck(f))continue;
    const n=G.nodes[f.node],RS=routeSet(f,pid);
    if(DR[f.cls].ground){aiRover(f,pid);continue;}
    // just pulled back from a stronger enemy: hold for a few turns instead of walking straight back in (no back-and-forth)
    if(f.cool&&G.turn<f.cool&&!threat)continue;""")
rep("    if(danger.length&&f.node!==p.core&&f.cls!=='leviathan'){f.path=findPath(f.node,p.core,RS)||[];f.bombard=null;continue;}",
    "    if(danger.length&&f.node!==p.core&&f.cls!=='leviathan'&&!(strike&&f.node===stage)){f.path=findPath(f.node,p.core,RS)||[];f.bombard=null;f.cool=G.turn+3;continue;}")
rep("""    if(n.owner!=null&&n.owner!==pid)continue;
    if(threat||total<DF.attackAt)continue;""",
    """    // on an enemy tile: wait there while one of our workers is on its way to claim it (at most 5 turns), otherwise move on
    if(isFoe(pid,n.owner)&&ws.some(w=>(w.path.at(-1)??w.node)===n.id)&&(f.hold=(f.hold||0)+1)<=5)continue;
    f.hold=0;
    if(threat)continue;
    // part of the army: gather at the staging tile, then strike together
    if(goal!=null&&army.includes(f)){
      const to=strike&&f.node===stage?goal:stage;
      if(f.node!==to){const path=findPath(f.node,to,RS);if(path&&canReach(f,path)&&(to===goal||tileCount(pid,to,f.cls,f)+f.count<=capFor(pid,f.cls))){f.path=path;continue;}}
      else continue;
    }
    if(total<DF.attackAt)continue;""")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
