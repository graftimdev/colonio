"""Builds client/index.html (online-ready Jopium) from original-0.1.7.html.

Run:  python tools/build.py
Every change to the original game is listed here, so it can be re-applied to a newer draft.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
SRC = os.path.join(ROOT, 'original-0.1.7.html')
OUT = os.path.join(ROOT, 'client', 'index.html')

s = open(SRC, encoding='utf-8').read()


def rep(old, new, count=1):
    """Replace text that must appear exactly `count` times."""
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f'build: expected {count} match(es), found {n}: {old[:90]!r}')
    s = s.replace(old, new)


def snippet(name):
    return open(os.path.join(TOOLS, name), encoding='utf-8').read()


def cut_between(start, end, new):
    """Replace from `start` (inclusive) up to `end` (exclusive); both must be unique."""
    global s
    for m in (start, end):
        if s.count(m) != 1:
            sys.exit(f'build: marker not unique: {m[:80]!r}')
    a, b = s.index(start), s.index(end)
    if b < a:
        sys.exit('build: markers out of order')
    s = s[:a] + new + s[b:]


def section(start, end):
    """Index range of a unique block, for edits that must stay inside it."""
    a = s.index(start)
    b = s.index(end, a)
    return a, b


# ---------------------------------------------------------------- 1. seeded randomness
# Every Math.random() that changes the match becomes rnd(); sound, stars and the lobby animation keep Math.random.
lines = s.split('\n')
def in_logic(i):
    t = lines[i]
    return not any(k in t for k in ('getChannelData', 'const stars=', 'const pts=Array.from', 'p.z-=dt', 'sx<0||sy<0'))
for i, t in enumerate(lines):
    if 'Math.random()' in t and in_logic(i):
        lines[i] = t.replace('Math.random()', 'rnd()')
s = '\n'.join(lines)

rep("let G=null,UID=1;", """let G=null,UID=1;
// ME: the player sitting at this screen (always 0 against the AI; the lobby seat online).
// REPLAY: true while orders are being re-applied at the end of an online turn (no toasts or error beeps then).
let ME=0,REPLAY=false;
// seeded random numbers for everything that changes the match, so every player's copy stays identical online
let RNG=1;
function seedRng(s){RNG=(s>>>0)||1;}
function rnd(){RNG=(RNG+0x6D2B79F5)>>>0;let t=RNG;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;}""")

# ---------------------------------------------------------------- 2. "player 0 is you" -> ME
rep("if(f.bombard!=null&&(f.owner!==0||!settings.keepFire))f.bombard=null;", "if(f.bombard!=null&&!f.keep)f.bombard=null;")
rep("k.has(x)||pid!==0", "k.has(x)||P(pid).ai")
rep("human=pid===0;", "human=pid===ME&&!REPLAY;")
s = re.sub(r'\b(owner|coreOf|pid|killer|prev|id)(===|!==)0\b', r'\1\2ME', s)
s = re.sub(r'\b(P|vis|known|fleetSight|energyProd|energyUse|energyCap|sharedCap|tileCap|includes)\(0\)', r'\1(ME)', s)
s = re.sub(r'\b(canBuild|payAt|stCost|tileCount|walletAt|clusterOf|researchersOn|canPayAt|has|newFleet|refundAt)\(0,', r'\1(ME,', s)

rep("const pName=q=>q.id===ME?profile.name:q.name.replace(/ AI$/,L(' AI',' ИИ'));\nconst pShort=q=>q.id===ME?profile.name:q.short;",
    "const pName=q=>q.human?q.name:q.name.replace(/ AI$/,L(' AI',' ИИ'));\nconst pShort=q=>q.human?q.name:q.short;")
rep("function toast(msg,bad){const t=$('#toast');", "function toast(msg,bad){if(REPLAY)return;const t=$('#toast');")
rep("function deny(msg){sfxError();", "function deny(msg){if(REPLAY)return false;sfxError();")

# ---------------------------------------------------------------- 3. new match: seed, seats, names
rep("""function newGame(opts){
  try{localStorage.setItem('jopium-setup',JSON.stringify(opts));}catch(e){}
  UID=1;
  const np=opts.bots+1,""", """// opts.online: {seed, seats:[{name,ai}], you} from the server; every player builds the same map from the same seed
function newGame(opts){
  const on=opts.online||null;
  if(!on)try{localStorage.setItem('jopium-setup',JSON.stringify(opts));}catch(e){}
  UID=1;ME=on?on.you:0;seedRng(on?on.seed:Math.floor(Math.random()*4294967296));myCmds=[];SNAP=null;
  const np=on?on.seats.length:opts.bots+1,""")
rep("""sel:cores[0],moveMode:null,hoverPath:null,unread:0,anim:null,splitOpen:null,notice:null,trade,result:null,modal:null,names:shuffle([...NAMES]),techSel:null,hits:[]};
  for(let i=0;i<np;i++){
    G.players.push(Object.assign({id:i,ai:i>0,core:cores[i],alive:true,energy:20,
      res:{iron:20,copper:15,silicon:10,xeno:0},explored:new Set([cores[i]]),techs:new Set(),techSeen:new Set(),prog:{},workersBuilt:0,workerQueue:0,freeQ:0,gold:0},PLAYERS[i]));
  }
  for(let i=0;i<np;i++)for(let w=0;w<5;w++)G.workers.push(newWorker(i,cores[i]));
  G.conn=G.players.map(p=>connSet(p.id));""",
"""sel:cores[ME],moveMode:null,hoverPath:null,unread:0,anim:null,splitOpen:null,notice:null,trade,result:null,modal:null,names:shuffle([...NAMES]),techSel:null,hits:[],
     online:!!on,room:on?on.room:null,seenTech:new Set(),waiting:false};
  for(let i=0;i<np;i++){
    const seat=on?on.seats[i]:{name:i===0?profile.name:null,ai:i>0};
    const who=seat.ai?{}:{name:seat.name,short:seat.name,human:true};
    G.players.push(Object.assign({id:i,ai:!!seat.ai,core:cores[i],alive:true,energy:20,
      res:{iron:20,copper:15,silicon:10,xeno:0},explored:new Set([cores[i]]),techs:new Set(),prog:{},workersBuilt:0,workerQueue:0,freeQ:0,gold:0},PLAYERS[i],who));
  }
  for(let i=0;i<np;i++)for(let w=0;w<5;w++)G.workers.push(newWorker(i,cores[i]));
  G.conn=G.players.map(p=>connSet(p.id));
  takeSnapshot();""")
rep("centerOn(nodes[cores[0]],true)", "centerOn(nodes[cores[ME]],true)")
rep("p.techSeen.has(t.id)", "G.seenTech.has(t.id)")
rep("TECHS.forEach(t=>{if(p.techs.has(t.id))p.techSeen.add(t.id);});", "TECHS.forEach(t=>{if(p.techs.has(t.id))G.seenTech.add(t.id);});")

# ---------------------------------------------------------------- 4. orders work for any player, as messages
cut_between('/* ---------- player orders ---------- */', 'function upgradeOne(f){', snippet('orders.js'))
rep('/* ---------- camera and canvas ---------- */', snippet('cmds.js') + '/* ---------- camera and canvas ---------- */')

# map clicks
rep("if(mm.mode==='bombard'){if(G.nodes[mm.from].nbr.includes(id)){mm.u.bombard=id;mm.u.path=[];mm.u.mergeInto=null;toast(",
    "if(mm.mode==='bombard'){if(order({t:'bomb',f:mm.u.id,to:id,keep:settings.keepFire})){toast(")
rep("));}else deny(L('Artillery can only fire at a neighbouring tile.','Артиллерия стреляет только по соседней клетке.'));}\n", "));}}\n")
rep("else if(mm.mode==='aim'){if(G.nodes[mm.from].nbr.includes(id)){mm.s.aim=id;toast(L('The death turret fires at the end of this turn.','Турель смерти выстрелит в конце хода.'));}else deny(L('The death turret can only hit an asteroid 1 hop away.','Турель смерти бьёт только по астероиду в 1 прыжке.'));}",
    "else if(mm.mode==='aim'){if(order({t:'aim',s:mm.s.uid,to:id}))toast(L('The death turret fires at the end of this turn.','Турель смерти выстрелит в конце хода.'));}")
rep("else if(mm.u.cls)orderFleetMove(mm.u,id);", "else if(mm.u.cls)order({t:'fmove',f:mm.u.id,to:id});")
rep("else{const path=findPath(mm.u.node,id,known(ME));if(path){mm.u.path=path;mm.u.task='idle';mm.u.ref=null;mm.u.then=null;mm.u.tech=null;}else deny(L('No known route to that asteroid.','Нет известного пути к этому астероиду.'));}",
    "else order({t:'wmove',w:mm.u.id,to:id});")

# buttons (only inside act())
a, b = section('function act(a,d){', '\nfunction onChange(el){')
body = s[a:b]
def arep(old, new):
    global body
    if body.count(old) != 1:
        sys.exit(f'build(act): expected 1 match, found {body.count(old)}: {old[:90]!r}')
    body = body.replace(old, new)
arep("case 'tset':{const w=Wk(d.w),t=G.popup&&G.popup.t;if(!w||!t||!techOpen(p,TECH[t]))break;if(researchersOn(ME,t,w)>=techLeft(p,t)){deny(L('Enough workers are already researching this.','Это уже исследует достаточно рабочих.'));break;}setTask(w,'research');w.tech=t;break;}",
     "case 'tset':{const t=G.popup&&G.popup.t;if(t)order({t:'research',w:+d.w,tech:t});break;}")
arep("case 'tunset':{const w=Wk(d.w);if(w)setTask(w,'idle');break;}", "case 'tunset':order({t:'task',w:+d.w,task:'idle'});break;")
arep("setTask(w,'research');w.tech=t;if(G.techFor===w.id)G.techFor=null;toast(", "if(!order({t:'research',w:w.id,tech:t}))break;if(G.techFor===w.id)G.techFor=null;toast(")
arep("if(w){setTask(w,'idle');toast(L(`${w.name} stopped researching.`", "if(w&&order({t:'task',w:w.id,task:'idle'})){toast(L(`${w.name} stopped researching.`")
arep("case 'freew':{if(p.freeOffer&&!p.workerQueue){p.workerQueue++;p.freeQ++;p.freeOffer=false;toast(", "case 'freew':{if(order({t:'freew'})){toast(")
arep("case 'wtask':{const w=Wk(d.w);if(w)setTask(w,d.t);break;}", "case 'wtask':order({t:'task',w:+d.w,task:d.t});break;")
arep("case 'wbuild':{const w=Wk(d.w),f=S(d.s);if(w&&f){if(buildersOn(f.s.uid,w)>=f.s.work){deny(L('Enough workers are already building this.','Это уже строит достаточно рабочих.'));break;}setTask(w,'build',f.s.uid);}break;}",
     "case 'wbuild':order({t:'task',w:+d.w,task:'build',ref:+d.s});break;")
arep("case 'wfix':{const w=Wk(d.w);if(w)setTask(w,'fix',+d.s);break;}", "case 'wfix':order({t:'task',w:+d.w,task:'fix',ref:+d.s});break;")
arep("case 'fstop':{const f=F(d.f);if(f){f.path=[];f.bombard=null;f.mergeInto=null;}break;}", "case 'fstop':order({t:'fstop',f:+d.f});break;")
arep("if(f&&k>=1&&k<f.count){const ph=f.hp/f.count,g=newFleet(ME,f.cls,k,f.node,f.up);g.hp=ph*k;f.hp-=ph*k;f.count-=k;G.fleets.push(g);G.splitOpen=null;toast(",
     "if(f&&order({t:'split',f:f.id,k})){G.splitOpen=null;toast(")
arep("case 'fdock':{const f=F(d.f);if(!f)break;const s=live(G.nodes[f.node],DR[f.cls].ground?'rbarracks':'kazarm')[0];if(s){s.hangar[f.cls]+=f.count;G.fleets=G.fleets.filter(g=>g!==f);}break;}",
     "case 'fdock':order({t:'dock',f:+d.f});break;")
arep("case 'fdis':{const f=F(d.f);if(!f)break;const r=oneEach(DR[f.cls].cost);for(const k in r)r[k]*=f.count;refundAt(ME,f.node,r);G.fleets=G.fleets.filter(g=>g!==f);toast(",
     "case 'fdis':{const f=F(d.f);if(!f||!order({t:'disf',f:f.id}))break;toast(")
arep("case 'fupg':{const f=F(d.f);if(f)upgradeOne(f);break;}", "case 'fupg':order({t:'upg',f:+d.f});break;")
arep("case 'start':startStation(G.sel,d.t);break;", "case 'start':order({t:'build',n:G.sel,type:d.t});break;")
arep("case 'stcancel':{const f=S(d.s);if(f&&f.s.state==='build'){refundAt(ME,f.n.id,f.s.paid||ST[f.s.type].cost);f.n.stations=f.n.stations.filter(x=>x!==f.s);G.workers.forEach(w=>{if(w.ref===f.s.uid){w.task='idle';w.ref=null;}});toast(",
     "case 'stcancel':{const f=S(d.s);if(f&&order({t:'stcancel',s:f.s.uid})){toast(")
arep("case 'stdis':{const f=S(d.s);if(f){refundAt(ME,f.n.id,oneEach(ST[f.s.type].cost));f.n.stations=f.n.stations.filter(x=>x!==f.s);G.workers.forEach(w=>{if(w.ref===f.s.uid){w.task='idle';w.ref=null;}});toast(",
     "case 'stdis':{const f=S(d.s);if(f&&order({t:'stdis',s:f.s.uid})){toast(")
arep("case 'unaim':{const f=S(d.s);if(f)f.s.aim=null;break;}", "case 'unaim':order({t:'unaim',s:+d.s});break;")
arep("case 'kbuild':{const f=S(d.s);if(f&&canPayAt(ME,f.n.id,DR[d.c].cost)){payAt(ME,f.n.id,DR[d.c].cost);f.s.queue.push(d.c);}break;}", "case 'kbuild':order({t:'queue',s:+d.s,c:d.c});break;")
arep("case 'kcancel':{const f=S(d.s);if(f){const c=f.s.queue.splice(+d.i,1)[0];if(c)refundAt(ME,f.n.id,DR[c].cost);}break;}", "case 'kcancel':order({t:'unqueue',s:+d.s,i:+d.i});break;")
ka, kb = body.index("    case 'kasm':{"), body.index("    case 'hire':")
body = body[:ka] + "    case 'kasm':order({t:'launch',s:+d.s,c:d.c});break;\n" + body[kb:]
arep("case 'hire':{const c=workerCost(p);if(workerTotal(p)<12&&canPayAt(ME,p.core,c)){payAt(ME,p.core,c);p.workerQueue++;}break;}", "case 'hire':order({t:'hire'});break;")
ta = body.index("    case 'trade':{\n"); tb = body.index("  }\n  refresh();\n}", ta)
body = body[:ta] + "    case 'trade':order({t:'trade',give:G.trade.give,get:G.trade.get});break;\n" + body[tb:]
s = s[:a] + body + s[b:]

rep("if(a==='wtech'){const w=G.workers.find(w=>w.id===+el.dataset.w);if(w){w.tech=el.value||null;",
    "if(a==='wtech'){const w=G.workers.find(w=>w.id===+el.dataset.w);if(w&&order({t:'wtech',w:w.id,tech:el.value||null})){")
rep("if(d.over){sfxClick();orderMerge(d.id,+d.over.dataset.fdrop);}", "if(d.over){sfxClick();order({t:'merge',src:d.id,tgt:+d.over.dataset.fdrop});refresh();}")

# ---------------------------------------------------------------- 5. online turns, lobby and server connection
for step in ('online_patch.py',):
    path = os.path.join(TOOLS, step)
    if os.path.exists(path):
        exec(open(path, encoding='utf-8').read())

# ---------------------------------------------------------------- checks
left = [m.start() for m in re.finditer(r'\b(owner|coreOf|pid|killer|prev|id)(===|!==)0\b', s)]
if left:
    sys.exit(f'build: player-0 checks left at offsets {left[:5]}')
open(OUT, 'w', encoding='utf-8', newline='\n').write(s)
print(f'build: wrote {OUT} ({len(s):,} chars)')
