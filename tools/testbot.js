// Test bot for online sync checks. Paste into a browser tab that is in an online match (via dev tools).
// Every turn it gives random orders through order(), exactly like a player, then ends the turn.
// window.HS collects the match fingerprint after every turn; compare it between tabs.
(()=>{
window.HS=[];window.ORD=0;window.OK=0;
const _ot=onlineTurn;onlineTurn=function(m){_ot(m);HS.push(G.turn+':'+stateHash());};
const R=()=>Math.random(),pick=a=>a[Math.floor(R()*a.length)];
const _ord=order;order=function(c){ORD++;const r=_ord(c);if(r)OK++;return r;};
window.botOrders=function(){
  const me=P(ME);if(!me.alive)return;
  const ws=G.workers.filter(w=>w.owner===ME),K=[...known(ME)];
  // early on, research hard so the late-game orders get exercised too
  if(me.techs.size<TECHS.length&&G.turn<120){for(const w of ws){if(w.node===me.core){const t=TECHS.find(t=>techOpen(me,t)&&researchersOn(ME,t.id)<techLeft(me,t.id));if(t)order({t:'research',w:w.id,tech:t.id});}else if(R()<.6)order({t:'wmove',w:w.id,to:me.core});}order({t:'hire'});}
  else for(const w of ws){const r=R();
    if(r<.15)order({t:'wmove',w:w.id,to:pick(K)});
    else if(r<.22){const to=pick(K),p=findPath(w.node,to,known(ME));if(p&&p.length)order({t:'wmove',w:w.id,to,path:p});}
    else if(r<.4)order({t:'task',w:w.id,task:'claim'});
    else if(r<.6)order({t:'task',w:w.id,task:'mine'});
    else if(r<.72){const t=TECHS.find(t=>techOpen(me,t));if(t)order({t:'research',w:w.id,tech:t.id});}
    else order({t:'build',n:w.node,type:pick(['kazarm','kazarm','generator','storage','turret','upgrade','barrier','estorage','rbarracks','borehole','levi','chain'])});
  }
  if(R()<.5)order({t:'hire'});
  if(R()<.05)order({t:'loopq',v:R()<.5});
  for(const n of G.nodes)if(n.owner===ME)for(const s of n.stations){
    if(s.state==='build'){const w=ws.find(w=>w.node===n.id&&!w.path.length);if(w)order({t:'task',w:w.id,task:'build',ref:s.uid});}
    if(s.state!=='done')continue;
    if(s.type==='kazarm'||s.type==='rbarracks'){order({t:'queue',s:s.uid,c:pick(s.type==='kazarm'?SPACE:ROVERS)});for(const c of CLS)if(s.hangar[c].length)order({t:'launch',s:s.uid,c,i:R()<.5?-1:0});}
    if(s.type==='upgrade'){for(const c of CLS)if(s.hangar[c].length){order({t:'upgrade',s:s.uid,c});if(R()<.5)order({t:'launch',s:s.uid,c,i:-1});}}
    if(['kazarm','rbarracks','upgrade'].includes(s.type))for(const f of G.fleets.filter(f=>f.owner===ME&&f.node===n.id))if(R()<.3)order({t:'dockone',f:f.id,s:s.uid});
    if(s.type==='barrier'&&R()<.1)order({t:'barrier',s:s.uid,on:R()<.7});
    if(s.state==='destroyed'&&R()<.3)order({t:'stdis',s:s.uid});
  }
  const mine=G.fleets.filter(f=>f.owner===ME);
  for(const f of mine){
    if(!G.fleets.includes(f))continue;
    const r=R();
    if(stuck(f)){order({t:'selfdestruct',f:f.id});continue;}
    if(f.cls==='charger'){if(!f.settled&&r<.4)order({t:'settle',f:f.id,v:true});else if(f.settled&&r<.15)order({t:'settle',f:f.id,v:false});
      if(f.settled){const g=mine.find(g=>g!==f&&g.node===f.node&&G.fleets.includes(g)&&g.cls!=='leviathan'&&g.cls!=='charger');if(g)order({t:'dockone',f:g.id,ch:f.id});for(const d of (f.dock||[]).slice(0,1))order({t:'launch',ch:f.id,c:d.c,i:-1});}
      if(f.settled)continue;}
    if(ARTY(f.cls)&&r<.4)order({t:'bomb',f:f.id,to:pick(G.nodes[f.node].nbr),keep:R()<.5});
    else if(r<.08&&f.count>1)order({t:'split',f:f.id,k:1});
    else if(r<.14){const g=mine.find(g=>g!==f&&g.cls===f.cls&&G.fleets.includes(g));if(g)order({t:'merge',src:f.id,tgt:g.id});}
    else if(r<.2){const to=pick(K),p=findPath(f.node,to,routeSet(f,ME));if(p&&p.length)order({t:'fmove',f:f.id,to,path:p});}
    else{const ec=G.players.find(q=>q.id!==ME).core;const tgt=R()<.6?K.filter(id=>G.nodes[id].owner!=null&&G.nodes[id].owner!==ME).sort((a,b)=>hexDist(G.nodes[a],G.nodes[ec])-hexDist(G.nodes[b],G.nodes[ec]))[0]??pick(K):pick(K);order({t:'fmove',f:f.id,to:tgt});}
  }
  const alive=mine.filter(f=>G.fleets.includes(f)&&!f.settled);
  if(alive.length>=2&&R()<.15)order({t:'squad',ids:[alive[0].id,alive[1].id]});
  for(const q of me.squads||[])if(R()<.3)order({t:'squadmove',q:q.id,to:pick(K)});
  if(R()<.05&&(me.squads||[]).length)order({t:'squaddel',q:me.squads[0].id});
  if(R()<.3)order({t:'trade',give:pick(RES),get:pick(RES)});
};
window.BOT=setInterval(()=>{if(!G||!G.online||G.waiting||!P(ME).alive)return;try{botOrders();}catch(e){console.error('bot',e);window.BOTERR=String(e.stack);}endTurn(true);},60);
})();
