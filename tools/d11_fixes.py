"""Draft 11 stage 1: quick fixes and menus."""
import re
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


rep("const GAME_VERSION='ver. 0.1.10';", "const GAME_VERSION='ver. 0.2.1';")

# [2] workers sit just inside the white dotted ring (27) instead of on it
rep("const ring=i<15?0:1,j=ring?i-15:i,a=.15+j*2*Math.PI/(ring?21:15),rad=ring?39:27;",
    "const ring=i<15?0:1,j=ring?i-15:i,a=.15+j*2*Math.PI/(ring?21:15),rad=ring?33:21.5;")
rep("const rad=u.cls==='leviathan'?66+(G.workers.filter(w=>w.node===u.node).length>15?12:0):44+ring*22;",
    "const rad=u.cls==='leviathan'?60+(G.workers.filter(w=>w.node===u.node).length>15?10:0):44+ring*22;")

# [6] one small pulse, just past the dotted ring, under a second
rep("""    if(t>1700)G.pulseT0=null;""", """    if(t>800)G.pulseT0=null;""")
rep("""      for(const d of [0,550]){const e=(t-d)/1100;if(e<0||e>1)continue;
        ctx.beginPath();ctx.arc(x,y,R*cam.z*(.35+1.1*e),0,Math.PI*2);ctx.fillStyle=`rgba(${col},${.22*(1-e)})`;ctx.fill();ctx.strokeStyle=`rgba(${col},${.9*(1-e)})`;ctx.lineWidth=2.5*sz;ctx.stroke();}""",
    """      {const e=t/700;if(e>=0&&e<=1){ctx.beginPath();ctx.arc(x,y,27*sz*(.92+.22*e),0,Math.PI*2);ctx.strokeStyle=`rgba(${col},${.85*(1-e)})`;ctx.lineWidth=2;ctx.stroke();}}""")

# [15] spies drawn like every other drone; [33] upgraded drones filled with their colour
rep("""  shapePath(ctx,f.cls,x,y,r);ctx.fillStyle=hexa(c,f.cls==='spy'?.08:.25);ctx.fill();
  ctx.strokeStyle=sel?'#fff':c;ctx.lineWidth=sel?2.4:1.8;ctx.setLineDash(f.cls==='spy'?[2,2]:[]);ctx.stroke();ctx.setLineDash([]);
  if(f.up){ctx.fillStyle='#fff';""",
    """  shapePath(ctx,f.cls,x,y,r);ctx.fillStyle=f.up?c:hexa(c,.25);ctx.fill();
  ctx.strokeStyle=sel?'#fff':c;ctx.lineWidth=sel?2.4:1.8;ctx.stroke();
  if(f.up){ctx.fillStyle='#0b1020';""")
s = s.replace("c.setLineDash(m.c==='spy'?[8,8]:[]);", "c.setLineDash([]);")
s = s.replace("c.setLineDash(u.id==='spy'?[8,8]:[]);", "c.setLineDash([]);")

# [34] the pilot looks as big as a worker on the map
rep("if(f.cls==='leviathan'){drawLeviathan(ctx,x,y,r,sel?'#ffffff':c,.18,sz*.42);return;}",
    "if(f.cls==='leviathan'){drawLeviathan(ctx,x,y,r,sel?'#ffffff':c,.18,sz*.5);return;}")

# [16] upkeep: every war drone and rover 0.5 a turn (1 for war drones on a planet); the leviathan uses none
rep("const SPACE=['interceptor',", "for(const c in DR)DR[c].up=c==='leviathan'?0:.5; // upkeep per drone per turn (war drones on planets: 1)\nconst SPACE=['interceptor',")
rep("""h+=`<div class="sub">${L('Cost','Цена')}: ${costHtml(D.cost)} · ${L('upkeep','содержание')} ${BOLT}${D.up}/${L('turn','ход')}</div>`;""",
    """h+=`<div class="sub">${L('Cost','Цена')}: ${costHtml(D.cost)} · ${L('upkeep','содержание')} ${BOLT}${D.up}/${L('turn','ход')}${!D.ground&&D.up?L(' (1 on planets)',' (1 на планетах)'):''}</div>`;""")

# [19] the Save button keeps its whole label; [20] Sign out is red; profile closes with a cross
rep("""<div class="opts" style="flex-wrap:nowrap"><input class="txt" id="nameIn" maxlength="16\"""",
    """<div class="opts" style="flex-wrap:nowrap"><input class="txt" id="nameIn" style="min-width:0;flex:1" maxlength="16\"""")
rep("""${Acc.state==='in'?`<button class="btn small" type="button" data-a="acc-name">${L('Save','Сохранить')}</button>`:''}""",
    """${Acc.state==='in'?`<button class="btn small" type="button" data-a="acc-name" style="flex:none;white-space:nowrap">${L('Save','Сохранить')}</button>`:''}""")
rep("""      <div class="opts"><button class="btn primary" type="button" data-a="m-main">${L('Back','Назад')}</button>${Acc.state==='in'?`<button class="btn quiet" type="button" data-a="acc-out">${L('Sign out','Выйти из аккаунта')}</button>`:''}</div></div>`;""",
    """      ${achHtml()}
      ${Acc.state==='in'?`<div class="opts" style="justify-content:center"><button class="btn danger" type="button" data-a="acc-out">${L('Sign out','Выйти из аккаунта')}</button></div>`:''}</div>`;""")
rep("""  }else if(view==='profile'){
    ov.innerHTML=`<div class="card"><h1>${L('Profile','Профиль')}</h1>""",
    """  }else if(view==='profile'){
    ov.innerHTML=`<div class="card"><button class="x" type="button" data-a="m-main" aria-label="${L('Close','Закрыть')}">✕</button><h1>${L('Profile','Профиль')}</h1>""")

# [22] Boreholes and Rover station swap places; Rover station's Barrack link is solid once researched
rep("{id:'borehole',b:2,at:[2,-14],", "{id:'borehole',b:2,at:[2,14],")
rep("{id:'rovers',b:2,at:[2,14],", "{id:'rovers',b:2,at:[2,-14],")
rep("""svg+=`<line class="${p.techs.has(t.id)?'cline':'cguide'}" stroke-dasharray="1 1.2" x1=""",
    """svg+=`<line class="${p.techs.has(t.id)?'cline':'cguide'}" ${p.techs.has(t.id)?'':'stroke-dasharray="1 1.2"'} x1=""")

# [27, 28] trade: pickers work again, and the layout is Give [icons] ×n / Get [icons] ×n
rep("""    h+=`<div class="sec"><h3>${L('Trade','Торговля')}</h3><div class="row"><span class="sub">${L('Give','Отдать')} ${give}</span>${opt('tgive',G.trade.give)}</div><div class="row"><span class="sub">${L('for','за')} ${get}</span>${opt('tget',G.trade.get)}""",
    """    h+=`<div class="sec"><h3>${L('Trade','Торговля')}</h3><div class="trow"><span class="sub tl">${L('Give','Отдать')}</span>${opt('tgive',G.trade.give)}<b class="mono tn2">×${give}</b></div><div class="trow"><span class="sub tl">${L('Get','Получить')}</span>${opt('tget',G.trade.get)}<b class="mono tn2">×${get}</b></div><div class="row" style="justify-content:center">""")
rep("    case 'tgive':case 'tget':G.trade[a==='tgive'?'give':'get']=el.dataset.r;try{localStorage.setItem('jopium-trade',JSON.stringify(G.trade));}catch(e){}break;",
    "    case 'tgive':case 'tget':G.trade[a==='tgive'?'give':'get']=el.dataset.r;try{localStorage.setItem('jopium-trade',JSON.stringify(G.trade));}catch(e){}renderModal();return;")
rep(".tpick{display:inline-flex;gap:4px;flex-wrap:wrap}",
    ".tpick{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;align-items:center;flex:1}.tpick .btn{width:38px;height:34px;display:grid;place-items:center;padding:0}.trow{display:flex;align-items:center;gap:10px;margin:4px 0}.trow .tl{width:56px}.trow .tn2{width:34px;text-align:right}")

# [29] one Rivals list, at the bottom of the Empire menu (with each rival's jopium in Conquest)
i = s.index("  // rivals: everyone is listed; ones you haven't met yet are \"unknown rival\"")
j = s.index("  h+=`</div><div class=\"sec\"><h3>${L('Workers','Рабочие')}</h3>`;", i)
rivals = s[i:j]
s = s[:i] + s[j:]
k = s.index("  h+=`</div><div class=\"sec\"><h3>${L('Rivals','Соперники')}</h3>`;\n  // in conquest the rivals list shows everyone's jopium")
e = s.index("  return h+`</div>`;\n}", k)
rivals = rivals.replace("(G.treaties||[]).some(t=>t.from===ME&&t.to===q.id);", "(G.treaties||[]).some(t=>t.from===ME&&t.to===q.id),gold=G.mode==='conquest'?` · ${STARGOLD}${q.gold}`:'';")
rivals = rivals.replace("<br><span class=\"sub\">${st}</span>", "<br><span class=\"sub\">${st}${gold}</span>")
s = s[:k] + rivals + s[e:]

# [30] the game menu tab closes when you press anywhere else
rep("$('#hudbar').onclick=()=>{", "document.addEventListener('pointerdown',e=>{const t=$('#top');if(t.classList.contains('open')&&!t.contains(e.target)){t.classList.remove('open');$('#hudbar').setAttribute('aria-expanded',false);}},true);\n$('#hudbar').onclick=()=>{")

# [31] chargers dock in barracks and upgrade stations, and get upgraded; rovers show in an upgrade station only when docked there
rep("const dockKinds=st=>st.type==='kazarm'?SPACE.filter(c=>c!=='charger'):st.type==='rbarracks'?ROVERS:st.type==='upgrade'?[...SPACE,...ROVERS].filter(c=>c!=='charger'):[];",
    "const dockKinds=st=>st.type==='kazarm'?SPACE:st.type==='rbarracks'?ROVERS:st.type==='upgrade'?[...SPACE,...ROVERS]:[];")
rep("list=dockKinds(s).filter(c=>canMake(ME,c)&&(DR[c].ground?has(ME,'rovers'):dU(c)));",
    "list=dockKinds(s).filter(c=>DR[c].ground?s.hangar[c].length>0:canMake(ME,c)&&dU(c));")

# [32] no + / − / centre buttons; [20 answer] C re-centres on your core
rep('    <div class="mapctl" id="mapctl" hidden>', '    <div class="mapctl" id="mapctl" hidden style="display:none">')
rep("  ['squad',['q'],'First squadron on the tile','Первая эскадрилья на клетке'],",
    "  ['squad',['q'],'First squadron on the tile','Первая эскадрилья на клетке'],\n  ['center',['c'],'Centre the map on your core','Центрировать карту на ядре'],")
rep("    case 'tile':if(G.sel!=null){", "    case 'center':centerOn(G.nodes[P(ME).core],false);refresh();break;\n    case 'tile':if(G.sel!=null){")

# [11] Move to it: only on tiles that aren't yours and have none of your workers; one line with your nearest idle worker
rep("""  if(n.owner==null&&p.alive)h+=assignList(L('Move to it','Лететь сюда'),n.id,'wgo',w=>w.path.length>0&&w.path.at(-1)===n.id);""",
    """  if(n.owner!==ME&&p.alive&&!G.workers.some(w=>w.owner===ME&&w.node===n.id))h+=moveToHtml(n);""")
rep("function assignList(title,id,act,on,extra){", r"""// "Move to it": the nearest idle worker that can get here
function moveToHtml(n){
  const K=known(ME);let best=null;
  for(const w of G.workers){if(w.owner!==ME||w.path.length||w.task!=='idle')continue;const pth=findPath(w.node,n.id,K);if(pth&&(!best||pth.length<best.d))best={w,d:pth.length};}
  const coming=G.workers.find(w=>w.owner===ME&&w.path.length&&w.path.at(-1)===n.id);
  let h=`<div class="sec"><h3>${L('Move to it','Лететь сюда')}</h3>`;
  if(coming)h+=`<div class="row"><div class="grow"><b>${esc(coming.name)}</b> <span class="sub">${L(`on the way · ${plural(coming.path.length,'hop')} away`,`в пути · ${cnt(coming.path.length,'hop')}`)}</span></div><button class="btn small" type="button" data-a="wtask" data-t="idle" data-w="${coming.id}">${L('Stop','Стоп')}</button></div>`;
  else if(!best)h+=`<p class="sub" style="margin:0">${L('No idle workers.','Нет свободных рабочих.')}</p>`;
  else h+=`<div class="row"><div class="grow"><b>${esc(best.w.name)}</b> <span class="sub">${L(`${plural(best.d,'hop')} away`,`${cnt(best.d,'hop')} отсюда`)}</span></div><button class="btn small primary" type="button" data-a="wgo" data-w="${best.w.id}" data-n="${n.id}">${L('Assign','Назначить')}</button></div>`;
  return h+`</div>`;
}
function assignList(title,id,act,on,extra){""")
rep("""h+=`<div class="row"><div class="grow"><b>${esc(w.name)}</b> <span class="sub mono">${d?plural(d,'hop'):L('here','здесь')}</span>""",
    """h+=`<div class="row"><div class="grow"><b>${esc(w.name)}</b> <span class="sub mono">${d?L(`${plural(d,'hop')} away`,`${cnt(d,'hop')} отсюда`):L('here','здесь')}</span>""")

# [3] reports open by themselves only with the new setting on (off by default)
rep("const settings={music:.5,sfx:.6,keepFire:false,loopQ:false,", "const settings={music:.5,sfx:.6,keepFire:false,loopQ:false,autoReport:false,")
rep("  if(G.coreFell&&!G.over)openModal({type:'report'});", "  if(G.coreFell&&!G.over&&settings.autoReport)openModal({type:'report'});")
rep("""      <div class="field"><div class="lab"><span>${L('Infinite queues','Бесконечные очереди')}</span>""",
    """      <div class="field"><div class="lab"><span>${L('Show important reports','Показывать важные отчёты')}</span><button type="button" class="switch ${settings.autoReport?'on':''}" role="switch" aria-checked="${settings.autoReport}" data-a="s-rep" aria-label="${L('Show important reports','Показывать важные отчёты')}"><i></i></button></div><p class="sub" style="margin:0">${L('Open the turn report by itself when something important happens, like losing your core.','Открывать отчёт за ход самостоятельно, когда происходит что-то важное, например падение ядра.')}</p></div>
      <div class="field"><div class="lab"><span>${L('Infinite queues','Бесконечные очереди')}</span>""")
rep("    case 's-fire':", "    case 's-rep':settings.autoReport=!settings.autoReport;saveSettings();showMenu('settings');break;\n    case 's-fire':")

# [13, 26] a hidden page: music stops at once; games against the computer pause (online timers keep running on the server)
rep("let audioReady=false;", r"""let audioReady=false,pageHidden=false,duck=1;
document.addEventListener('visibilitychange',()=>{
  pageHidden=document.hidden;
  if(pageHidden){for(const t of Object.values(TRACKS)){t.el.pause();t.g=0;t.el.volume=0;}curTrack=null;if(AC&&AC.state==='running')AC.suspend().catch(()=>{});}
  else if(AC&&AC.state==='suspended'&&audioReady)AC.resume().catch(()=>{});
});""")
rep("  const want=gameClosed||settings.music<=0?null:G?'game':'menu';", "  const want=gameClosed||pageHidden||settings.music<=0?null:G?'game':'menu';")
rep("    t.el.volume=Math.max(0,Math.min(1,t.g*settings.music));", "    t.el.volume=Math.max(0,Math.min(1,t.g*settings.music*duck));")
rep("if(!G||G.over||!G.turnTime||G.waiting||(!G.online&&!$('#overlay').hidden))return;G.timeLeft-=dt;",
    "if(!G||G.over||!G.turnTime||G.waiting||(!G.online&&(!$('#overlay').hidden||pageHidden)))return;G.timeLeft-=dt;")

# [7] in move mode, dragging pans the map unless you start the drag on the unit's own tile (then it traces a route)
rep("drag={x:e.clientX,y:e.clientY,cx:cam.x,cy:cam.y,moved:false,hit:hitAt(sx,sy),trace:mm&&mm.mode==='move'?[mm.from]:null};",
    "drag={x:e.clientX,y:e.clientY,cx:cam.x,cy:cam.y,moved:false,hit:hitAt(sx,sy),trace:mm&&mm.mode==='move'&&nodeAt(sx,sy)===mm.from?[mm.from]:null};")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
