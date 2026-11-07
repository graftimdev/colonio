/* ---------- player orders ---------- */
const humanWorkersAt=(id,pid=ME)=>G.workers.filter(w=>w.owner===pid&&w.node===id);
function setTask(w,task,ref){w.path=[];w.then=null;w.task=task;w.ref=ref??null;if(task!=='research')w.tech=null;}
function startStation(pid,nid,type){
  const n=G.nodes[nid];if(!n||!ST[type])return false;
  const why=canBuild(pid,n,type);if(why)return deny(why);
  const ws=humanWorkersAt(nid,pid).filter(w=>!w.path.length);if(!ws.length)return deny(L('You need a worker on this asteroid to build.','Для строительства нужен рабочий на этом астероиде.'));
  const pc=stCost(pid,type);payAt(pid,nid,pc);const s=newStation(n,type,{paid:pc});n.stations.push(s);
  setTask(ws.find(w=>w.task==='idle')||ws[0],'build',s.uid);
  toast(L(`${sN(type)} started.`,`Стройка начата: ${sN(type)}.`));
  return true;
}
// rovers can only travel across the tiles of the planet they are on
function groundSet(id){const pl=G.nodes[id].planet;return new Set(pl==null?[id]:G.planets[pl].ids);}
const routeSet=(f,pid)=>{const k=known(pid);if(!DR[f.cls].ground)return k;const g=groundSet(f.node);return new Set([...g].filter(x=>k.has(x)||P(pid).ai));};
function orderFleetMove(f,id){
  const pid=f.owner;if(!G.nodes[id])return false;
  if(DR[f.cls].ground&&!groundSet(f.node).has(id))return deny(L('Rovers cannot leave their planet.','Роверы не могут покинуть свою планету.'));
  const path=findPath(f.node,id,routeSet(f,pid));
  if(!path)return deny(L('No known route to that asteroid.','Нет известного пути к этому астероиду.'));
  if(id!==f.node&&tileCount(pid,id,f.cls,f)+f.count>tileCap(pid))return deny(L(`That asteroid can hold only ${tileCap(pid)} of your ${dCount(2,f.cls).replace(/^\d+ /,'')}. Split the fleet first.`,`На этом астероиде поместится не больше: ${dCount(tileCap(pid),f.cls)}. Сначала разделите флот.`));
  f.path=path;f.bombard=null;f.mergeInto=null;return true;
}
function orderMerge(pid,srcId,tgtId){
  const s=G.fleets.find(f=>f.id===srcId&&f.owner===pid),t=G.fleets.find(f=>f.id===tgtId&&f.owner===pid);
  if(!s||!t||s===t)return false;
  if(s.cls!==t.cls)return deny(L('Only fleets of the same drone type can merge.','Объединять можно только флоты одного типа.'));
  if(s.up!==t.up)return deny(L('Upgraded drones cannot merge with regular ones.','Улучшенные дроны нельзя объединить с обычными.'));
  if(s.node===t.node){mergeFleets(t,s);toast(L(`${dN(t.cls)} fleets merged: ${t.count} drones.`,`Флоты объединены: ${dCount(t.count,t.cls)}.`));return true;}
  const path=findPath(s.node,t.node,routeSet(s,pid));if(!path)return deny(L('No known route to that fleet.','Нет известного пути к этому флоту.'));
  if(tileCount(pid,t.node,t.cls,s)+s.count>tileCap(pid))return deny(L(`Merging would put more than ${tileCap(pid)} ${dCount(2,t.cls).replace(/^\d+ /,'')} on one asteroid. Split the fleet first.`,`После объединения на астероиде будет больше ${tileCap(pid)}. Сначала разделите флот.`));
  s.path=path;s.bombard=null;s.mergeInto=t.id;
  toast(L(`The fleet will fly ${plural(path.length,'hop')} and merge on arrival.`,`Флот пролетит ${cnt(path.length,'hop')} и объединится на месте.`));
  return true;
}
