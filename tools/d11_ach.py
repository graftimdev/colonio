"""Draft 11 stage 2: achievements (online games only), all-resign and turn-1000 stalemate."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


ACH_JS = r"""
/* ---------- achievements ----------
   Earned in online matches only (Early bird: on signing in). Saved to the account as users/{uid}.ach = {id: true, end: best tech count}.
   Detection runs inside resolve() on every screen, but each screen only ever unlocks its own player's (ME), and it never
   changes the match, so online games stay in sync. */
const ACH=[
  {id:1,n:'Long shot',r:'Дальний выстрел',d:'Destroy a core with a ballista bolt.',rd:'Уничтожьте ядро молнией баллисты.'},
  {id:2,n:'Best deal',r:'Выгодная сделка',d:'A boomerang rescue saves your charger.',rd:'Спасите зарядчик бумерангом.'},
  {id:3,n:'Eldritch horror',r:'Древний ужас',d:'Build a leviathan.',rd:'Постройте левиафана.'},
  {id:4,n:'Found you',r:'Попался',d:'Catch a spy with an X-ray turret.',rd:'Поймайте шпиона рентген-турелью.'},
  {id:5,n:'So nice',r:'Как мило',d:'Collect a gift.',rd:'Заберите подарок.'},
  {id:6,n:'Still standing',r:'Ещё стою',d:'Win a Conquest match after being the underdog.',rd:'Выиграйте «Завоевание», побывав отстающим.'},
  {id:7,n:'Mastermind',r:'Стратег',d:'A catapult fired at an empty tile hits an enemy that moved there.',rd:'Катапульта, стрелявшая по пустой клетке, попадает во врага, который туда прилетел.'},
  {id:8,n:'End game',r:'Конец игры',d:'Research every tech in one game.',rd:'Изучите все технологии за одну игру.'},
  {id:9,n:'Early bird',r:'Ранняя пташка',d:'Play Jopium in its early days.',rd:'Сыграйте в Jopium в первые дни.'},
];
let ACH_SESSION=[];
const achHas=id=>!!(profile.ach&&profile.ach[id]);
const achProgress=id=>id===8?[Math.min(TECHS.length,(profile.ach&&profile.ach.end)||0),TECHS.length]:[achHas(id)?1:0,1];
function achUnlock(id,always){
  if(REPLAY||achHas(id)||(!always&&!(G&&G.online&&!G.tut)))return;
  profile.ach=profile.ach||{};profile.ach[id]=true;saveProfile();
  ACH_SESSION.push(id);sfxAch();
  const a=ACH.find(x=>x.id===id);toast(L(`Achievement unlocked: ${a.n}`,`Достижение: ${a.r}`));
  if(Acc.state==='in')Acc.saveAch();
}
// End game also remembers your best tech count for its progress bar
function achTechs(){
  if(!G||!G.online||G.tut)return;const k=P(ME).techs.size;profile.ach=profile.ach||{};
  if(k>((profile.ach.end)||0)){profile.ach.end=k;saveProfile();if(Acc.state==='in')Acc.saveAch();}
  if(k>=TECHS.length)achUnlock(8);
}
function sfxAch(){[523,659,784,1047].forEach((f,i)=>tone('triangle',f,f,.28,.07,i*.09));}
function achHtml(){
  const done=ACH.filter(a=>achHas(a.id)).length;
  return `<div class="sec"><h3>${L('Achievements','Достижения')} · ${done}/${ACH.length}</h3><div class="achgrid">${ACH.map(a=>{const [v,t]=achProgress(a.id),ok=v>=t;
    return `<div class="achtile ${ok?'done':''}" title="${esc(L(a.d,a.rd))}"><div class="achic ${ok?'done':v>0?'':'lock'}">${a.id}</div><b>${L(a.n,a.r)}</b><div class="achbar"><i style="width:${100*v/t}%"></i></div></div>`;}).join('')}</div></div>`;
}
// back in the main menu after a game: what you unlocked in it
function achPopup(){
  if(!ACH_SESSION.length)return false;
  const list=ACH_SESSION.map(id=>ACH.find(a=>a.id===id));ACH_SESSION=[];
  ov.hidden=false;ov.className='';ov.dataset.view='achpop';
  ov.innerHTML=`<div class="card"><h1>${L('New achievements','Новые достижения')}</h1><div class="achgrid">${list.map(a=>`<div class="achtile done"><div class="achic done">${a.id}</div><b>${L(a.n,a.r)}</b><span class="sub">${esc(L(a.d,a.rd))}</span></div>`).join('')}</div><div class="opts"><button class="btn primary" type="button" data-a="m-main">${L('Nice','Отлично')}</button></div></div>`;
  return true;
}
"""

rep("function hitPulse(id,att,win,kind){", ACH_JS + "\nfunction hitPulse(id,att,win,kind){")

# account: load and save achievements; everyone signing in gets Early bird
rep("  apply(d){profile.name=d.name;profile.pic=d.pic||'';profile.elo=d.elo;profile.games=d.games||0;profile.tut=!!d.tut;saveProfile();",
    "  apply(d){profile.name=d.name;profile.pic=d.pic||'';profile.elo=d.elo;profile.games=d.games||0;profile.tut=!!d.tut;profile.ach=Object.assign({},profile.ach||{},d.ach||{});saveProfile();if(!achHas(9))achUnlock(9,true);")
rep("  async setPic(pic){", "  async saveAch(){if(this.state!=='in')return;const {doc,updateDoc}=this.m;try{await updateDoc(doc(this.db,'users',this.user.uid),{ach:profile.ach});}catch(e){console.warn('Jopium: achievements not saved',e);}},\n  async setPic(pic){")

# triggers
rep("  G.flash.add(id);hitPulse(id,[f.owner],[]);\n  if(n.type==='core'&&n.coreHp<=0)coreFall(n);\n  return soaked;",
    "  G.flash.add(id);hitPulse(id,[f.owner],[]);\n  if(n.type==='core'&&n.coreHp<=0){if(f.owner===ME)achUnlock(1);coreFall(n);}\n  return soaked;")
rep("for(const c of ['charger','repair']){const f=s.fleets.find(f=>f.cls===c&&f.hp>0&&f.count>0);if(f){const d=takeDrone(f);f.saved=(f.saved||0)+1;if(f.count<=0)f.hp=0;launchDrones(s.pid,c,dest,[d]);s.saved.push(dN(c));ok=true;break;}}",
    "for(const c of ['charger','repair']){const f=s.fleets.find(f=>f.cls===c&&f.hp>0&&f.count>0);if(f){const d=takeDrone(f);f.saved=(f.saved||0)+1;if(f.count<=0)f.hp=0;launchDrones(s.pid,c,dest,[d]);s.saved.push(dN(c));if(c==='charger'&&s.pid===ME)achUnlock(2);ok=true;break;}}")
rep("      const lv=newFleet(pid,'leviathan',1,f.n.id);lv.pilot=pilot.name;G.fleets.push(lv);",
    "      const lv=newFleet(pid,'leviathan',1,f.n.id);lv.pilot=pilot.name;G.fleets.push(lv);if(pid===ME)achUnlock(3);")
rep("    const killer=xr?G.nodes[f.node].owner:wf[0].owner,by=",
    "    const killer=xr?G.nodes[f.node].owner:wf[0].owner;if(xr&&killer===ME)achUnlock(4);const by=")
rep("    const f=newFleet(pid,g.cls,1,n.id,g.up);G.fleets.push(f);", "    const f=newFleet(pid,g.cls,1,n.id,g.up);G.fleets.push(f);if(pid===ME)achUnlock(5);")
rep("  if(S>.6*avg)return;", "  if(S>.6*avg)return;\n  (G.underdogs=G.underdogs||{})[uid]=true;")
# Mastermind: remember that the catapult aimed at a tile with no enemy in sight; count hits on drones or workers that arrived this turn
rep("      f.bombard=+c.to;f.keep=!!c.keep;f.path=[];f.mergeInto=null;return true;}",
    "      {const V=vis(pid),tn=+c.to;f.blind=f.cls==='catapult'&&!G.fleets.some(g=>g.node===tn&&isFoe(pid,g.owner)&&V.has(tn)&&g.cls!=='spy')&&!G.workers.some(w=>w.node===tn&&isFoe(pid,w.owner));}\n      f.bombard=+c.to;f.keep=!!c.keep;f.path=[];f.mergeInto=null;return true;}")
rep("    const drones=G.fleets.filter(g=>g.node===tn.id&&foe(g.owner)&&g.cls!=='spy').sort(",
    "    if(f.owner===ME&&f.blind&&(G.fleets.some(g=>g.node===tn.id&&foe(g.owner)&&g.cls!=='spy'&&g.trail&&g.trail.length>1)||G.workers.some(w=>w.node===tn.id&&foe(w.owner)&&w.trail&&w.trail.length>1)))achUnlock(7);\n    const drones=G.fleets.filter(g=>g.node===tn.id&&foe(g.owner)&&g.cls!=='spy').sort(")
# End game progress after each turn; Still standing on a Conquest win after being the underdog
rep("  diploTurn();updateMet();\n", "  diploTurn();updateMet();achTechs();\n")
rep("    if(rich){G.winner=rich.id;endGame(rich.id===ME?'won':'lost');}",
    "    if(rich){G.winner=rich.id;if(rich.id===ME&&G.underdogs&&G.underdogs[ME])achUnlock(6);endGame(rich.id===ME?'won':'lost');}")

# the popup after a game, when you reach the main menu
rep("    case 'tut-menu':leaveGame();showMenu('main');break;", "    case 'tut-menu':leaveGame();showMenu('main');break;")
rep("  }else if(view==='main'){\n    ov.innerHTML=`<div class=\"card\"><h1 class=\"logo\">JOPIUM</h1>",
    "  }else if(view==='main'&&!G&&achPopup()){\n    return;\n  }else if(view==='main'){\n    ov.innerHTML=`<div class=\"card\"><h1 class=\"logo\">JOPIUM</h1>")

# ---------- [36] turn 1000: stalemate; [35] everyone resigning ----------
rep("  // winners: first to the jopium goal (conquest), or the last player left\n",
    "  // winners: first to the jopium goal (conquest), or the last player left; turn 1000 is a stalemate\n  if(G.turn>=1000&&!G.over){G.winner=-1;endGame('draw');}\n")
rep("  const title=r==='won'?", "  const title=r==='draw'?L('Stalemate','Пат'):r==='won'?")
rep("  const text=r==='won'?", "  const text=r==='draw'?L('Turn 1000 was reached and nobody won. The match is a draw.','Достигнут 1000-й ход, никто не победил. Ничья.'):r==='won'?")
rep("  if(G.online&&G.winner!=null&&!G.resultSent){G.resultSent=true;Net.send({t:'result',winner:G.winner});}",
    "  if(G.online&&G.winner!=null&&G.winner>=0&&!G.resultSent){G.resultSent=true;Net.send({t:'result',winner:G.winner});}")

rep(".dchips{", ".achgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.achtile{border:1px solid var(--line);border-radius:10px;padding:8px 6px;display:grid;justify-items:center;gap:5px;text-align:center;font-size:12px}.achtile.done{border-color:var(--accent);background:rgba(77,163,255,.12)}.achic{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font:700 13px var(--f-mono,monospace);border:2px solid var(--accent);color:var(--accent)}.achic.done{background:var(--accent);color:#04101f}.achic.lock{border-color:#33415e;color:#5b6a88}.achbar{width:100%;height:6px;border-radius:3px;background:var(--panel2);overflow:hidden;border:1px solid var(--line)}.achbar i{display:block;height:100%;background:var(--accent)}\n.dchips{")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
