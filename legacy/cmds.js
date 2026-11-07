/* ---------- orders as messages (online play) ---------- */
// Every change a player makes to the match goes through order(). It is applied at once on this screen and,
// online, also recorded. When everyone has ended the turn, each screen rewinds to the start of the turn,
// replays every player's orders in seat order, then resolves. Same start + same orders + same seed = same match.
function applyCmd(pid,c){
  const p=P(pid);if(!p||!c||(!p.alive&&c.t!=='resign'))return false;
  const Wk=id=>G.workers.find(w=>w.id===+id&&w.owner===pid),F=id=>G.fleets.find(f=>f.id===+id&&f.owner===pid);
  const S=uid=>{const f=findStation(+uid);return f&&f.n.owner===pid?f:null;};
  switch(c.t){
    case 'research':{const w=Wk(c.w),t=c.tech;if(!w||!TECH[t]||!techOpen(p,TECH[t])||w.node!==p.core||w.path.length)return false;
      if(researchersOn(pid,t,w)>=techLeft(p,t))return deny(L('Enough workers are already researching this.','Это уже исследует достаточно рабочих.'));
      setTask(w,'research');w.tech=t;return true;}
    case 'task':{const w=Wk(c.w);if(!w||!['idle','mine','claim','build','fix'].includes(c.task))return false;
      if(c.task==='build'){const f=S(c.ref);if(!f)return false;if(buildersOn(f.s.uid,w)>=f.s.work)return deny(L('Enough workers are already building this.','Это уже строит достаточно рабочих.'));}
      setTask(w,c.task,c.task==='build'||c.task==='fix'?+c.ref:null);return true;}
    case 'wtech':{const w=Wk(c.w);if(!w)return false;w.tech=TECH[c.tech]?c.tech:null;return true;}
    case 'wmove':{const w=Wk(c.w);if(!w||!G.nodes[c.to])return false;const path=findPath(w.node,+c.to,known(pid));
      if(!path)return deny(L('No known route to that asteroid.','Нет известного пути к этому астероиду.'));
      w.path=path;w.task='idle';w.ref=null;w.then=null;w.tech=null;return true;}
    case 'freew':if(p.freeOffer&&!p.workerQueue){p.workerQueue++;p.freeQ++;p.freeOffer=false;return true;}return false;
    case 'hire':{const c2=workerCost(p);if(workerTotal(p)<12&&canPayAt(pid,p.core,c2)){payAt(pid,p.core,c2);p.workerQueue++;return true;}return false;}
    case 'trade':{
      if(!has(pid,'trade')||!RES.includes(c.give)||!RES.includes(c.get))return false;
      if((c.give==='xeno'||c.get==='xeno')&&!has(pid,'xtrade'))return false;
      const [give,get]=has(pid,'rates')?[4,3]:[3,2];
      if(c.give===c.get)return deny(L('Pick two different resources.','Выберите два разных ресурса.'));
      if(p.res[c.give]<give)return deny(L(`You need ${give} ${rN(c.give)} to trade.`,`Для обмена нужно ${give} ед. (${lc(rN(c.give))}).`));
      p.res[c.give]-=give;if(addRes(p,c.get,get)<get)toast(L('Part of the trade was lost: your storage is full.','Часть обмена потеряна: хранилище заполнено.'),true);return true;}
    case 'fmove':{const f=F(c.f);return f?orderFleetMove(f,+c.to):false;}
    case 'bomb':{const f=F(c.f);if(!f||!ARTY(f.cls))return false;if(!G.nodes[f.node].nbr.includes(+c.to))return deny(L('Artillery can only fire at a neighbouring tile.','Артиллерия стреляет только по соседней клетке.'));
      f.bombard=+c.to;f.keep=!!c.keep;f.path=[];f.mergeInto=null;return true;}
    case 'fstop':{const f=F(c.f);if(!f)return false;f.path=[];f.bombard=null;f.mergeInto=null;return true;}
    case 'merge':return orderMerge(pid,+c.src,+c.tgt);
    case 'split':{const f=F(c.f),k=Math.floor(+c.k);if(!f||!(k>=1&&k<f.count))return false;
      const ph=f.hp/f.count,g=newFleet(pid,f.cls,k,f.node,f.up);g.hp=ph*k;f.hp-=ph*k;f.count-=k;G.fleets.push(g);return true;}
    case 'dock':{const f=F(c.f);if(!f||f.up)return false;const n=G.nodes[f.node];if(n.owner!==pid)return false;const s=live(n,DR[f.cls].ground?'rbarracks':'kazarm')[0];if(!s)return false;s.hangar[f.cls]+=f.count;G.fleets=G.fleets.filter(g=>g!==f);return true;}
    case 'disf':{const f=F(c.f);if(!f)return false;const n=G.nodes[f.node];if(n.owner!==pid||!live(n,DR[f.cls].ground?'rbarracks':'kazarm').length)return false;
      const r=oneEach(DR[f.cls].cost);for(const k in r)r[k]*=f.count;refundAt(pid,f.node,r);G.fleets=G.fleets.filter(g=>g!==f);return true;}
    case 'upg':{const f=F(c.f);return f?upgradeOne(f):false;}
    case 'build':return startStation(pid,+c.n,c.type);
    case 'stcancel':{const f=S(c.s);if(!f||f.s.state!=='build')return false;refundAt(pid,f.n.id,f.s.paid||ST[f.s.type].cost);f.n.stations=f.n.stations.filter(x=>x!==f.s);G.workers.forEach(w=>{if(w.ref===f.s.uid){w.task='idle';w.ref=null;}});return true;}
    case 'stdis':{const f=S(c.s);if(!f||f.s.state==='build')return false;refundAt(pid,f.n.id,oneEach(ST[f.s.type].cost));f.n.stations=f.n.stations.filter(x=>x!==f.s);G.workers.forEach(w=>{if(w.ref===f.s.uid){w.task='idle';w.ref=null;}});return true;}
    case 'aim':{const f=S(c.s);if(!f||f.s.type!=='death'||f.s.state!=='done'||f.s.charge>0)return false;
      if(!f.n.nbr.includes(+c.to))return deny(L('The death turret can only hit an asteroid 1 hop away.','Турель смерти бьёт только по астероиду в 1 прыжке.'));f.s.aim=+c.to;return true;}
    case 'unaim':{const f=S(c.s);if(!f)return false;f.s.aim=null;return true;}
    case 'queue':{const f=S(c.s);if(!f||f.s.state!=='done'||!DR[c.c])return false;
      const ok=f.s.type==='rbarracks'?ROVERS.includes(c.c):f.s.type==='kazarm'?SPACE.includes(c.c):false;
      if(!ok||!canPayAt(pid,f.n.id,DR[c.c].cost))return false;payAt(pid,f.n.id,DR[c.c].cost);f.s.queue.push(c.c);return true;}
    case 'unqueue':{const f=S(c.s);if(!f)return false;const x=f.s.queue.splice(+c.i,1)[0];if(!x)return false;refundAt(pid,f.n.id,DR[x].cost);return true;}
    case 'launch':{
      const f=S(c.s);if(!f||!DR[c.c]||f.s.state!=='done')return false;
      const k=Math.min(f.s.hangar[c.c]||0,tileCap(pid)-tileCount(pid,f.n.id,c.c));
      if(k<=0)return deny(L(`This asteroid already holds ${tileCap(pid)} of your ${dCount(2,c.c).replace(/^\d+ /,'')}. Move them out first.`,`На этом астероиде уже ${dCount(tileCap(pid),c.c)}. Сначала уведите их.`));
      f.s.hangar[c.c]-=k;const ex=G.fleets.find(g=>g.owner===pid&&g.node===f.n.id&&g.cls===c.c&&!g.up&&!g.path.length);
      if(ex){ex.count+=k;ex.hp+=k*DR[c.c].hp;}else G.fleets.push(newFleet(pid,c.c,k,f.n.id));
      toast(L(`${dCount(k,c.c)} launched.`,`Выпущено: ${dCount(k,c.c)}.`));return true;}
    case 'resign':if(!p.alive)return false;coreFall(G.nodes[p.core]);return true;
  }
  return false;
}
// the one way the interface changes the match
function order(c){
  if(!G||(G.over&&!G.spectate))return false;
  if(G.waiting)return deny(L('Waiting for the other players to end the turn…','Ждём, пока другие игроки завершат ход…'));
  const ok=applyCmd(ME,c);
  if(ok&&G.online)myCmds.push(c);
  return ok;
}
let myCmds=[],SNAP=null;
// fields that belong to this screen only (menus, what you've read, the end screen), never rewound
const LOCAL_KEYS=new Set(['spectate','popup','sel','moveMode','hoverPath','unread','anim','splitOpen','notice','trade','result','modal','techSel','hits','flash','ver','modalAt','popupAt','techFor','rockets','over','winner','online','seenTech','waiting','log','timeLeft','coreFell','goldCutLogged','room','iResigned','waitInfo']);
function takeSnapshot(){
  if(!G||!G.online)return;
  const g={};for(const k in G)if(!LOCAL_KEYS.has(k))g[k]=G[k];
  SNAP={g:structuredClone(g),uid:UID,rng:RNG};
}
function restoreSnapshot(){
  const keep={};for(const k in G)if(LOCAL_KEYS.has(k))keep[k]=G[k];
  G=Object.assign(SNAP.g,keep);UID=SNAP.uid;RNG=SNAP.rng;SNAP=null;
  G.moveMode=null;G.hoverPath=null;G.splitOpen=null;
}
// a short fingerprint of the match; every screen sends it after each turn so the server can spot a desync
function stateHash(){
  const parts=[G.turn,RNG,UID];
  for(const p of G.players)parts.push(p.alive,p.energy,RES.map(r=>p.res[r]).join(','),p.gold,[...p.techs].join(','),p.workerQueue);
  for(const n of G.nodes)parts.push(n.owner,n.coreHp,n.type,n.stations.map(s=>s.type+s.state+s.hp+s.work+s.queue.join('')).join('/'));
  for(const f of G.fleets)parts.push(f.id,f.owner,f.cls,f.count,Math.round(f.hp*100),f.node);
  for(const w of G.workers)parts.push(w.id,w.owner,w.node,w.task);
  const s=parts.join('|');let h=5381;for(let i=0;i<s.length;i++)h=(Math.imul(h,33)^s.charCodeAt(i))>>>0;
  return h.toString(36);
}

