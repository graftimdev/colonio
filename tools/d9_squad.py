"""Draft 9: press-and-hold selection, squadrons, traced paths."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:80]}')
    s = s.replace(a, b)


# ---------------------------------------------------------------- traced paths: orders can carry their own route
rep("function orderFleetMove(f,id){\n  const pid=f.owner;if(!G.nodes[id])return false;",
    """// a route traced by hand: each tile next to the one before, no tile twice, only tiles in `allowed`
function checkPath(from,path,allowed){
  if(!Array.isArray(path)||!path.length||path.length>60)return null;
  let cur=from;const seen=new Set([from]),out=[];
  for(const x of path){const id=+x;if(!G.nodes[id]||!G.nodes[cur].nbr.includes(id)||seen.has(id)||(allowed&&!allowed.has(id)))return null;seen.add(id);out.push(id);cur=id;}
  return out;
}
function orderFleetMove(f,id,manual){
  const pid=f.owner;if(!G.nodes[id])return false;f.sync=null;""")
rep("  const path=findPath(f.node,id,routeSet(f,pid));\n  if(!path)return deny(L('No known route to that asteroid.','Нет известного пути к этому астероиду.'));",
    "  const path=manual?checkPath(f.node,manual,routeSet(f,pid)):findPath(f.node,id,routeSet(f,pid));\n  if(!path||(manual&&path[path.length-1]!==id))return deny(L('No known route to that asteroid.','Нет известного пути к этому астероиду.'));")
rep("return orderFleetMove(f,+c.to);}", "return orderFleetMove(f,+c.to,c.path);}")
rep("case 'wmove':{const w=Wk(c.w);if(!w||!G.nodes[c.to])return false;const path=findPath(w.node,+c.to,known(pid));",
    "case 'wmove':{const w=Wk(c.w);if(!w||!G.nodes[c.to])return false;const path=c.path?checkPath(w.node,c.path,known(pid)):findPath(w.node,+c.to,known(pid));")

# ---------------------------------------------------------------- squadrons (kept per player, part of the match)
rep("    case 'loopq':p.loopQ=!!c.v;return true;", """    case 'loopq':p.loopQ=!!c.v;return true;
    case 'squad':{
      const ids=[...new Set((c.ids||[]).map(Number))].filter(id=>F(id));if(ids.length<2)return false;
      p.squads=(p.squads||[]).map(q=>({...q,ids:q.ids.filter(x=>!ids.includes(x))})).filter(q=>q.ids.length>1);
      p.sqN=(p.sqN||0)+1;p.squads.push({id:p.sqN,ids});return true;}
    case 'squaddel':p.squads=(p.squads||[]).filter(q=>q.id!==+c.q);return true;
    case 'squadmove':{
      const q=(p.squads||[]).find(q=>q.id===+c.q);if(!q)return false;
      const fl=q.ids.map(F).filter(f=>f&&!f.settled);const to=+c.to;if(!fl.length||!G.nodes[to])return false;
      if(fl.some(stuck))return deny(L("Some fleets in this squadron have drones with no energy, so the squadron can't move.",'В эскадрилье есть флоты с дронами без энергии, она не может двигаться.'));
      const by={};for(const f of fl)if(f.node!==to)by[f.cls]=(by[f.cls]||0)+f.count;
      for(const cl in by){const there=G.fleets.filter(g=>g.owner===pid&&g.node===to&&g.cls===cl&&!fl.includes(g)).reduce((a,g)=>a+g.count,0);
        if(there+by[cl]>capFor(pid,cl))return deny(L(`That tile can't hold that many ${dCount(2,cl).replace(/^\\d+ /,'')}.`,`На этой клетке не поместится столько: ${dN(cl)}.`));}
      const paths=fl.map(f=>f.node===to?[]:findPath(f.node,to,routeSet(f,pid)));
      if(paths.some(x=>x==null))return deny(L('Not every fleet in the squadron has a known route there.','Не у всех флотов эскадрильи есть известный путь туда.'));
      // the squadron moves together, at the speed of its slowest fleet
      const slow=Math.min(...fl.map(f=>DR[f.cls].spd));
      fl.forEach((f,i)=>{f.path=paths[i];f.bombard=null;f.mergeInto=null;f.sync=slow;});
      return true;}""")
rep("    // a boomerang passing back through the tile it attacked last turn gets that hop for free",
    "    if(f.sync)steps=Math.min(steps,f.sync);\n    // a boomerang passing back through the tile it attacked last turn gets that hop for free")
rep("    u.node=u.path.shift();u.trail.push(u.node);", "    u.node=u.path.shift();u.trail.push(u.node);if(!u.path.length)u.sync=null;")

# ---------------------------------------------------------------- map input: hold to select, drag to trace a route
rep("let drag=null;", "let drag=null,lpT=0;\n// a short rising tone: press-and-hold selection is armed\nfunction sfxConfirm(){tone('sine',520,880,.12,.07);tone('sine',880,1180,.1,.05,.08);}")
rep("  drag={x:e.clientX,y:e.clientY,cx:cam.x,cy:cam.y,moved:false,hit:hitAt(sx,sy)};\n});",
    """  const mm=G.moveMode;
  drag={x:e.clientX,y:e.clientY,cx:cam.x,cy:cam.y,moved:false,hit:hitAt(sx,sy),trace:mm&&mm.mode==='move'?[mm.from]:null};
  // press and hold for a second (without moving) to select fleets by dragging a box
  clearTimeout(lpT);
  if(!mm)lpT=setTimeout(()=>{if(drag&&!drag.moved&&!pinch){drag.select={x0:sx,y0:sy,x1:sx,y1:sy};sfxConfirm();const [wx,wy]=toWorld(sx,sy);ripples.push({x:wx,y:wy,t:performance.now(),big:true});if(navigator.vibrate)try{navigator.vibrate(20);}catch(e){}}},1000);
});
cv.addEventListener('contextmenu',e=>e.preventDefault());""")
rep("    const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>5)drag.moved=true;\n    if(drag.moved){",
    """    const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>5)drag.moved=true;
    if(drag.select){drag.select.x1=sx;drag.select.y1=sy;return;}
    if(drag.moved)clearTimeout(lpT);
    // in move mode, dragging traces a route through neighbouring tiles; dragging back onto the previous tile undoes a step
    if(drag.trace&&drag.moved){
      const id=nodeAt(sx,sy),t=drag.trace,last=t[t.length-1],mm=G.moveMode;
      if(id!=null&&id!==last&&mm){
        if(t.length>1&&id===t[t.length-2])t.pop();
        else if(G.nodes[last].nbr.includes(id)&&!t.includes(id)&&known(ME).has(id)&&(!mm.u.cls||mm.squad!=null||routeSet(mm.u,ME).has(id)))t.push(id);
        G.hoverPath=t.slice(1);
      }
      return;
    }
    if(drag.moved){""")
rep("  const d=drag;drag=null;if(!d||d.moved||!G)return;",
    """  const d=drag;drag=null;clearTimeout(lpT);
  if(d&&d.select&&G){finishSelect(d.select);return;}
  if(d&&d.trace&&d.moved&&G&&G.moveMode){finishTrace(d.trace);return;}
  if(!d||d.moved||!G)return;""")
rep("    else if(mm.u.cls){if(mm.u.cls!=='spy'&&enemiesAt(id))openPreview(mm.u,id);",
    "    else if(mm.squad!=null)order({t:'squadmove',q:mm.squad,to:id});\n    else if(mm.u.cls){if(mm.u.cls!=='spy'&&enemiesAt(id))openPreview(mm.u,id);")
rep("function openUnit(u){", """// a traced route was released: send the unit along it
function finishTrace(t){
  const mm=G.moveMode;G.moveMode=null;G.hoverPath=null;
  if(t.length<2){refresh();return;}
  const to=t[t.length-1],path=t.slice(1);
  if(mm.squad!=null)order({t:'squadmove',q:mm.squad,to});
  else if(mm.u.cls)order({t:'fmove',f:mm.u.id,to,path});
  else order({t:'wmove',w:mm.u.id,to,path});
  refresh();
}
// a selection box was released: offer to make the selected fleets a squadron
function finishSelect(b){
  const x0=Math.min(b.x0,b.x1),x1=Math.max(b.x0,b.x1),y0=Math.min(b.y0,b.y1),y1=Math.max(b.y0,b.y1);
  const ids=[...new Set(G.hits.filter(h=>h.kind==='fleet'&&h.u.owner===ME&&h.x>=x0-h.r&&h.x<=x1+h.r&&h.y>=y0-h.r&&h.y<=y1+h.r).map(h=>h.u.id))];
  if(ids.length<2){toast(L('Select at least 2 of your fleets to make a squadron.','Выделите хотя бы 2 своих флота, чтобы создать эскадрилью.'));refresh();return;}
  G.popup={type:'squad',ids};G.popupAt=performance.now();refresh();
}
function openUnit(u){""")
# the selection box and a bigger wave for the hold
rep("  for(const r of ripples){const e=(now-r.t)/520,[x,y]=toScreen(r.x,r.y);ctx.beginPath();ctx.arc(x,y,(6+30*e)*Math.max(.7,sz),0,Math.PI*2);",
    "  for(const r of ripples){const e=(now-r.t)/520,[x,y]=toScreen(r.x,r.y);ctx.beginPath();ctx.arc(x,y,(r.big?10+90*e:6+30*e)*Math.max(.7,sz),0,Math.PI*2);")
rep("  if(G.sel!=null){const n=G.nodes[G.sel];const [x,y]=toScreen(n.x,n.y);ctx.beginPath();ctx.arc(x,y,27*sz,0,Math.PI*2);",
    "  if(drag&&drag.select){const b=drag.select;ctx.save();ctx.setLineDash([5,4]);ctx.strokeStyle='rgba(77,163,255,.95)';ctx.fillStyle='rgba(77,163,255,.1)';ctx.lineWidth=1.5;ctx.beginPath();ctx.rect(Math.min(b.x0,b.x1),Math.min(b.y0,b.y1),Math.abs(b.x1-b.x0),Math.abs(b.y1-b.y0));ctx.fill();ctx.stroke();ctx.restore();}\n  if(G.sel!=null){const n=G.nodes[G.sel];const [x,y]=toScreen(n.x,n.y);ctx.beginPath();ctx.arc(x,y,27*sz,0,Math.PI*2);")
rep("    if(mm.mode==='move')G.hoverPath=id!=null?findPath(mm.from,id,mm.u.cls&&DR[mm.u.cls].ground?groundSet(mm.u.node):known(ME)):null;",
    "    if(mm.mode==='move')G.hoverPath=id!=null?findPath(mm.from,id,mm.squad!=null?known(ME):mm.u.cls?routeSet(mm.u,ME):known(ME)):null;")
rep(":mm.u.cls?L(`${dN(mm.u.cls)} fleet", ":mm.squad!=null?L(`Squadron ${mm.squad} selected: click a destination.`,`Эскадрилья ${mm.squad} выбрана: укажите цель.`):mm.u.cls?L(`${dN(mm.u.cls)} fleet")

# ---------------------------------------------------------------- squadron pop-up and Empire section
rep("  if(m.type==='preview'){", r"""  if(m.type==='squad'){
    const fl=m.ids.map(id=>G.fleets.find(f=>f.id===id)).filter(Boolean);
    h+=`<h2>${L(`Make a squadron of ${fl.length} fleets?`,`Создать эскадрилью из ${fl.length} флотов?`)}</h2><p class="sub" style="margin:0">${fl.map(f=>dCount(f.count,f.cls)).join(', ')}</p><p class="sub" style="margin:0">${L('Squadrons are in the Empire menu. They move together, at the speed of the slowest fleet.','Эскадрильи — в меню «Империя». Они летят вместе, со скоростью самого медленного флота.')}</p><div class="opts"><button class="btn primary" type="button" data-a="sqmake">${L('Make squadron','Создать эскадрилью')}</button><button class="btn" type="button" data-a="pclose">${L('Cancel','Отмена')}</button></div>`;
  }else if(m.type==='preview'){""")
rep("    case 'pclose':G.popup=null;break;", """    case 'pclose':G.popup=null;break;
    case 'sqmake':{if(G.popup&&G.popup.type==='squad'&&order({t:'squad',ids:G.popup.ids}))toast(L('Squadron made. Find it in the Empire menu.','Эскадрилья создана. Она в меню «Империя».'));G.popup=null;break;}
    case 'sqmove':{closeModal();const q=(P(ME).squads||[]).find(q=>q.id===+d.q);const f=q&&q.ids.map(id=>G.fleets.find(f=>f.id===id)).find(Boolean);if(f){G.moveMode={squad:q.id,u:{},mode:'move',from:f.node};refresh();}return;}
    case 'sqsee':G.squadOpen=G.squadOpen===+d.q?null:+d.q;break;
    case 'sqdel':order({t:'squaddel',q:+d.q});break;""")
rep("  h+=`<div class=\"sec\"><h3>${L('Fleets','Флоты')}</h3>", r"""  const sqs=(p.squads||[]).map(q=>({q,fl:q.ids.map(id=>G.fleets.find(f=>f.id===id&&f.owner===ME)).filter(Boolean)})).filter(x=>x.fl.length);
  if(sqs.length){
    h+=`<div class="sec"><h3>${L('Squadrons','Эскадрильи')}</h3>`;
    for(const {q,fl:sf} of sqs){
      h+=`<div class="row"><div class="grow"><b>${L('Squadron','Эскадрилья')} ${q.id}</b><br><span class="sub">${sf.map(f=>dCount(f.count,f.cls)).join(', ')}</span></div><div class="acts"><button class="btn small" type="button" data-a="sqmove" data-q="${q.id}">${L('Move','Лететь')}</button><button class="btn small" type="button" data-a="sqsee" data-q="${q.id}">${G.squadOpen===q.id?L('Hide','Скрыть'):L('See','Открыть')}</button><button class="btn small quiet" type="button" data-a="sqdel" data-q="${q.id}">${L('Disband','Распустить')}</button></div></div>`;
      if(G.squadOpen===q.id)for(const f of sf)h+=fleetRow(f,G.nodes[f.node]);
    }
    h+=`</div>`;
  }
  h+=`<div class="sec"><h3>${L('Fleets','Флоты')}</h3>""")
# map redraws at full rate while selecting
rep("const mapBusy=()=>!!(G&&(G.anim||drag||pinch||ripples.length||G.moveMode));", "const mapBusy=()=>!!(G&&(G.anim||drag||pinch||ripples.length||G.moveMode));")
rep("'goldCutLogged','room','lastFight','battleAt',", "'goldCutLogged','room','lastFight','battleAt','squadOpen',")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
