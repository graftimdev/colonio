"""Draft 10 stage 4b: keyboard controls (rebindable), General/Keyboard settings tabs, swipe on paged cards."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


# ---------- the binds ----------
rep("function saveSettings(){", r"""// keyboard: every action can have several keys, each changeable in Settings → Keyboard
const KEY_ACTIONS=[
  ['endturn',['Enter'],'End turn','Завершить ход'],
  ['empire',['m'],'Empire','Империя'],
  ['tile',['i'],'Open the selected tile','Открыть выбранную клетку'],
  ['back',['Escape'],'Close a menu / game menu','Закрыть меню / меню игры'],
  ['tech',['f'],'Tech tree','Дерево технологий'],
  ['squad',['q'],'First squadron on the tile','Первая эскадрилья на клетке'],
  ['up',['w','ArrowUp'],'Select the tile above','Клетка выше'],
  ['down',['s','ArrowDown'],'Select the tile below','Клетка ниже'],
  ['left',['a','ArrowLeft'],'Tile to the left / previous menu','Клетка слева / предыдущее меню'],
  ['right',['d','ArrowRight'],'Tile to the right / next menu','Клетка справа / следующее меню'],
  ['st1',['1'],'Station 1 on the tile','Станция 1 на клетке'],
  ['st2',['2'],'Station 2 on the tile','Станция 2 на клетке'],
  ['st3',['3'],'Station 3 on the tile','Станция 3 на клетке'],
  ['st4',['4'],'Station 4 on the tile','Станция 4 на клетке'],
  ['st5',['5'],'Leviathan on the tile','Левиафан на клетке'],
];
const defaultKeys=()=>Object.fromEntries(KEY_ACTIONS.map(([a,k])=>[a,[...k]]));
if(!settings.keys||typeof settings.keys!=='object')settings.keys=defaultKeys();
for(const [a,k] of KEY_ACTIONS)if(!Array.isArray(settings.keys[a]))settings.keys[a]=[...k];
const normKey=k=>k.length===1?k.toLowerCase():k;
const keyLabel=k=>({Enter:'Enter',Escape:'Esc',ArrowUp:'↑',ArrowDown:'↓',ArrowLeft:'←',ArrowRight:'→',' ':L('Space','Пробел')})[k]||k.toUpperCase();
const actionOf=k=>{k=normKey(k);for(const [a] of KEY_ACTIONS)if(settings.keys[a].includes(k))return a;return null;};
function saveSettings(){""")

# ---------- settings: two tabs ----------
rep("""  }else if(view==='settings'){
    const m=Math.round(settings.music*100),s=Math.round(settings.sfx*100);
    ov.innerHTML=`<div class="card"><h1>${L('Settings','Настройки')}</h1>
      <div class="field"><div class="lab">${L('Language','Язык')}</div>""",
    """  }else if(view==='settings'&&setTab==='keys'&&!touchOnly()){
    // keyboard tab: each key of each action can be changed; a key used elsewhere swaps over
    ov.innerHTML=`<div class="card"><h1>${L('Settings','Настройки')}</h1>${setTabs()}
      <div class="keys">${KEY_ACTIONS.map(([a,,en,ru])=>`<div class="krow"><span>${L(en,ru)}</span><span class="kk">${settings.keys[a].map((k,i)=>`<span class="kcap ${keyWait&&keyWait.a===a&&keyWait.i===i?'wait':''}">${keyWait&&keyWait.a===a&&keyWait.i===i?L('Press a key…','Нажмите клавишу…'):esc(keyLabel(k))}</span><button class="btn small" type="button" data-a="k-chg" data-k="${a}" data-i="${i}">${L('Change','Изменить')}</button>`).join('')}</span></div>`).join('')}</div>
      <div class="opts"><button class="btn" type="button" data-a="k-reset">${L('Reset to default','Сбросить по умолчанию')}</button><button class="btn primary" type="button" data-a="m-back">${menuFrom==='game'?L('Back to game','Вернуться в игру'):L('Back','Назад')}</button></div></div>`;
  }else if(view==='settings'){
    const m=Math.round(settings.music*100),s=Math.round(settings.sfx*100);
    ov.innerHTML=`<div class="card"><h1>${L('Settings','Настройки')}</h1>${setTabs()}
      <div class="field"><div class="lab">${L('Language','Язык')}</div>""")
rep("const hostOpts={name:'',mode:'warfare',per:20,opp:3,timer:45};", r"""// settings tabs: General and Keyboard (phones and tablets only get General)
let setTab='general',keyWait=null;
const touchOnly=()=>window.matchMedia&&matchMedia('(hover: none) and (pointer: coarse)').matches;
const setTabs=()=>touchOnly()?'':`<div class="seg tabs" role="tablist">${[['general','General','Общие'],['keys','Keyboard','Клавиатура']].map(([v,en,ru])=>`<button type="button" role="tab" aria-selected="${setTab===v}" class="${setTab===v?'on':''}" data-a="set-tab" data-v="${v}">${L(en,ru)}</button>`).join('')}</div>`;
const hostOpts={name:'',mode:'warfare',per:20,opp:3,timer:45};""")
rep("    case 's-fire':settings.keepFire=!settings.keepFire;saveSettings();showMenu('settings');break;",
    """    case 's-fire':settings.keepFire=!settings.keepFire;saveSettings();showMenu('settings');break;
    case 'set-tab':setTab=d.v;keyWait=null;showMenu('settings');break;
    case 'k-chg':keyWait={a:d.k,i:+d.i};showMenu('settings');break;
    case 'k-reset':settings.keys=defaultKeys();keyWait=null;saveSettings();showMenu('settings');toast(L('Keys reset to default.','Клавиши сброшены.'));break;""")
rep(".lnk{", ".tabs{margin:0 auto 4px}.keys{display:grid;gap:6px;max-height:52vh;overflow:auto}.krow{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.kk{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.kcap{min-width:34px;text-align:center;padding:3px 8px;border:1px solid var(--line);border-radius:6px;font-family:'IBM Plex Mono',monospace;font-size:12px}.kcap.wait{border-color:var(--warn);color:var(--warn)}\n.lnk{")

# ---------- the key handler ----------
rep("window.addEventListener('keydown',e=>{if(e.key!=='Escape'||!G)return;if(G.popup){G.popup=null;renderPopup();}else if(!$('#modal').hidden||!$('#techscr').hidden)closeModal();else if(G.moveMode)cancelMode();});",
    r"""// keyboard controls
const held=new Set(),pressedAt={};let navT=0;
window.addEventListener('keyup',e=>held.delete(normKey(e.key)));
window.addEventListener('blur',()=>held.clear());
window.addEventListener('keydown',e=>{
  // waiting for a new key in Settings → Keyboard
  if(keyWait){e.preventDefault();const k=normKey(e.key),{a,i}=keyWait;keyWait=null;
    if(k!=='Escape'||a==='back'){const other=actionOf(k);
      if(other&&!(other===a&&settings.keys[a][i]===k)){const j=settings.keys[other].indexOf(k);settings.keys[other][j]=settings.keys[a][i];toast(L(`${keyLabel(k)} was used for another action: the two keys swapped.`,`${keyLabel(k)} был занят: клавиши поменялись местами.`));}
      settings.keys[a][i]=k;saveSettings();}
    showMenu('settings');return;}
  if(e.target&&/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName))return;
  const a=actionOf(e.key);
  if(a==='back'||e.key==='Escape'){keyBack();return;}
  if(!G||!ov.hidden||!a)return;
  held.add(normKey(e.key));pressedAt[normKey(e.key)]=performance.now();
  const menu=G.popup||!$('#modal').hidden||!$('#techscr').hidden;
  if(['left','right'].includes(a)&&menu){e.preventDefault();flipMenu(a==='left'?-1:1);return;}
  if(['up','down','left','right'].includes(a)){if(menu)return;e.preventDefault();clearTimeout(navT);navT=setTimeout(navStep,90);return;}
  if(e.repeat)return;
  switch(a){
    case 'endturn':if(!menu){e.preventDefault();$('#endturn').click();}break;
    case 'empire':G.modal&&G.modal.type==='empire'?closeModal():openModal({type:'empire'});break;
    case 'tech':!$('#techscr').hidden?closeModal():openModal({type:'tech'});break;
    case 'tile':if(G.sel!=null){closeModal();openModal({type:'node',id:G.sel});}break;
    case 'squad':{if(G.sel==null)break;const f=idleFirst(G.fleets.filter(f=>f.owner===ME&&f.node===G.sel))[0];if(f){closeModal();openUnit(f);}else toast(L('None of your squadrons is on this tile.','На этой клетке нет ваших эскадрилий.'));break;}
    default:if(/^st[1-5]$/.test(a)&&G.sel!=null){const n=G.nodes[G.sel],k=+a[2];
      if(k===5&&n.stations.length>=4){const lv=G.fleets.find(f=>f.node===n.id&&f.cls==='leviathan'&&f.owner===ME);if(lv){closeModal();openUnit(lv);}break;}
      const st=n.stations[k-1];if(st&&vis(ME).has(n.id)){closeModal();openModal({type:'station',uid:st.uid});}}
  }
});
// Esc: close what is open; with nothing open, open the game menu tab (turn, resign, settings, report)
function keyBack(){
  if(!G||!ov.hidden)return;
  if(G.popup){G.popup=null;renderPopup();}
  else if(!$('#modal').hidden||!$('#techscr').hidden)closeModal();
  else if(G.moveMode)cancelMode();
  else $('#hudbar').click();
}
// W/A/S/D (or the arrows) move the selection to a neighbouring tile; W or S alone works when there is only one tile that way
function navStep(){
  if(!G||G.sel==null)return;
  // a key counts if it is still held or was tapped a moment ago, so quick W+A taps work too
  const now=performance.now(),on=a=>settings.keys[a].some(k=>held.has(k)||now-(pressedAt[k]||0)<220);
  const u=on('up'),d=!u&&on('down'),l=on('left'),r=!l&&on('right');
  for(const k in pressedAt)pressedAt[k]=0;
  const n=G.nodes[G.sel],nb=n.nbr.map(id=>G.nodes[id]),K=known(ME);
  let c=nb.filter(m=>K.has(m.id));
  if(u)c=c.filter(m=>m.y<n.y-1);else if(d)c=c.filter(m=>m.y>n.y+1);else c=c.filter(m=>Math.abs(m.y-n.y)<1);
  if(l)c=c.filter(m=>m.x<n.x-1);else if(r)c=c.filter(m=>m.x>n.x+1);
  if((u||d)&&!l&&!r&&c.length!==1)return;
  if(!c.length)return;
  c.sort((a,b)=>Math.hypot(a.x-n.x,a.y-n.y)-Math.hypot(b.x-n.x,b.y-n.y));
  G.sel=c[0].id;const [sx,sy]=toScreen(c[0].x,c[0].y);if(sx<60||sy<60||sx>innerWidth-60||sy>innerHeight-60)centerOn(c[0],false);refresh();
}
// A/D or the arrows with a menu open: the next squadron or station menu on the same tile, or the next page of a card
function flipMenu(dir){
  if(unlockPage(dir))return;
  const m=G.modal;if(!m)return;const id=G.sel;if(id==null)return;
  const items=[...G.nodes[id].stations.map(s=>({type:'station',uid:s.uid})),...idleFirst(G.fleets.filter(f=>f.owner===ME&&f.node===id)).map(f=>({type:'unit',f:f.id}))];
  const i=items.findIndex(x=>x.type===m.type&&(x.uid===m.uid&&x.uid!=null||x.f===m.f&&x.f!=null));
  if(i<0||items.length<2)return;openModal(items[(i+dir+items.length)%items.length]);
}
// swipe left/right on a paged card
{let sx=null;document.addEventListener('touchstart',e=>{if(e.target.closest&&e.target.closest('#popup'))sx=e.touches[0].clientX;},{passive:true});
 document.addEventListener('touchend',e=>{if(sx==null)return;const dx=e.changedTouches[0].clientX-sx;sx=null;if(Math.abs(dx)>45)unlockPage(dx<0?1:-1);},{passive:true});}""")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
