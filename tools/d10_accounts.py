"""Draft 10 stage 6 (client): Google sign-in with Firebase, unique nicknames, uploaded pictures,
Elo (hidden until the first online game), the real leaderboard, Elo change on the end screen."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


rep("const GAME_VERSION='ver. 0.1.9';\nconst profile={name:'Player',pic:'',elo:1000};",
    "const GAME_VERSION='ver. 0.1.10';\n// games: online games played (Elo is shown after the first); uid: the signed-in account, if any\nconst profile={name:'Player',pic:'',elo:1000,games:0,uid:null};")

# ---------- the account module ----------
rep("let LOBBY=null,LOBBIES=null,netError='';", r"""let LOBBY=null,LOBBIES=null,netError='';
/* ---------- accounts: Google sign-in through Firebase ----------
   users/{uid}: {name, pic, elo, games, tut, created} — Elo, games and score are written only by the game server.
   names/{name}: {uid} — one document per nickname, so two players can never hold the same name (capitals count).
   The claude.ai copy can't reach Firebase, so it stays a guest-only test version. */
const FB_CONFIG={apiKey:"AIzaSyDdiasH4cwsumx0QYhqMRRnd_ICjzkuPzI",authDomain:"jopium-243b1.firebaseapp.com",projectId:"jopium-243b1",storageBucket:"jopium-243b1.firebasestorage.app",messagingSenderId:"379443429897",appId:"1:379443429897:web:0891ab92bcf64848672ed8"};
const FB_V='10.12.2';
const GUEST_ONLY=location.protocol==='file:'||/(^|\.)claude\.ai$|claudeusercontent\.com$|claude\.site$|anthropic\.com$/.test(location.hostname||'');
const NAME_OK=/^[A-Za-z0-9_]{3,16}$/;
const Acc={
  state:GUEST_ONLY?'guest':'loading', // loading → out (needs sign-in) → in; or guest
  m:null,auth:null,db:null,user:null,token:'',unsub:null,
  async init(){
    if(this.state==='guest')return;
    try{
      const base=`https://www.gstatic.com/firebasejs/${FB_V}/`;
      const [a,au,fs]=await Promise.all([import(base+'firebase-app.js'),import(base+'firebase-auth.js'),import(base+'firebase-firestore.js')]);
      this.m={...a,...au,...fs};
      const app=a.initializeApp(FB_CONFIG);
      this.auth=au.getAuth(app);this.db=fs.getFirestore(app); // sign-in is kept on this device until the player signs out
      au.onAuthStateChanged(this.auth,u=>this.onUser(u));
    }catch(e){console.warn('Jopium: accounts unavailable',e);this.state='guest';accChanged();}
  },
  async signIn(){
    const {GoogleAuthProvider,signInWithPopup,signInWithRedirect}=this.m;
    try{await signInWithPopup(this.auth,new GoogleAuthProvider());}
    catch(e){if(/popup-blocked|operation-not-supported/.test(e.code||''))await signInWithRedirect(this.auth,new GoogleAuthProvider());else if(!/popup-closed|cancelled-popup/.test(e.code||''))toast(L("Couldn't sign in. Try again.",'Не удалось войти. Попробуйте ещё раз.'),true);}
  },
  async signOut(){if(this.auth)await this.m.signOut(this.auth);},
  async onUser(u){
    if(this.unsub){this.unsub();this.unsub=null;}
    this.user=u;
    if(!u){this.state='out';profile.uid=null;accChanged();return;}
    this.token=await u.getIdToken();
    const {doc,getDoc,onSnapshot}=this.m,ref=doc(this.db,'users',u.uid);
    let snap=await getDoc(ref),fresh=false;
    if(!snap.exists()){await this.create(u.uid);snap=await getDoc(ref);fresh=true;}
    this.state='in';profile.uid=u.uid;this.apply(snap.data());
    this.unsub=onSnapshot(ref,d=>{if(d.exists())this.apply(d.data());});
    Net.rehello();
    accChanged(fresh||!snap.data().tut);
  },
  apply(d){profile.name=d.name;profile.pic=d.pic||'';profile.elo=d.elo;profile.games=d.games||0;profile.tut=!!d.tut;saveProfile();if(!G&&ov.dataset.view&&['main','profile','board'].includes(ov.dataset.view))showMenu(ov.dataset.view);},
  // a new account: default picture, nickname player + a free number from 1 to 10000
  async create(uid){
    const {doc,runTransaction,serverTimestamp}=this.m;
    for(let i=0;i<40;i++){
      const name='player'+(1+Math.floor(Math.random()*10000));
      try{await runTransaction(this.db,async t=>{const nr=doc(this.db,'names',name);if((await t.get(nr)).exists())throw new Error('taken');
        t.set(nr,{uid});t.set(doc(this.db,'users',uid),{name,pic:'',elo:1000,games:0,tut:false,created:serverTimestamp()});});return;}
      catch(e){if(e.message!=='taken')throw e;}
    }
    throw new Error('no free nickname');
  },
  async rename(name){
    if(!NAME_OK.test(name))return L('Use 3 to 16 letters, digits or _.','Используйте от 3 до 16 букв, цифр или _.');
    if(name===profile.name)return '';
    const {doc,runTransaction}=this.m,uid=this.user.uid,old=profile.name;
    try{await runTransaction(this.db,async t=>{const nr=doc(this.db,'names',name);if((await t.get(nr)).exists())throw new Error('taken');
      t.set(nr,{uid});t.delete(doc(this.db,'names',old));t.update(doc(this.db,'users',uid),{name});});return '';}
    catch(e){return e.message==='taken'?L('That name is taken. Try another.','Это имя занято. Попробуйте другое.'):L("Couldn't save the name.",'Не удалось сохранить имя.');}
  },
  async setPic(pic){const {doc,updateDoc}=this.m;await updateDoc(doc(this.db,'users',this.user.uid),{pic});},
  async tutDone(){if(this.state==='in'){const {doc,updateDoc}=this.m;try{await updateDoc(doc(this.db,'users',this.user.uid),{tut:true});}catch(e){}}profile.tut=true;saveProfile();},
  // the top 100 by Elo (ties: who got there first), plus your own place when you are lower
  async board(){
    const {collection,query,orderBy,limit,getDocs,where,getCountFromServer,doc,getDoc}=this.m,col=collection(this.db,'users');
    const top=(await getDocs(query(col,orderBy('score','desc'),limit(100)))).docs.map(d=>({uid:d.id,...d.data()}));
    let me=null;
    if(this.state==='in'&&profile.games>0&&!top.some(r=>r.uid===this.user.uid)){
      const mine=(await getDoc(doc(this.db,'users',this.user.uid))).data();
      if(mine&&mine.score!=null)me={...mine,uid:this.user.uid,place:1+(await getCountFromServer(query(col,where('score','>',mine.score)))).data().count};
    }
    return {top,me};
  },
};
let BOARD=null,nameMsg='';
// called whenever the account state changes; a brand-new account goes straight into the tutorial
function accChanged(needTut){
  if(G)return;
  if(Acc.state==='out'){showMenu('login');return;}
  if(needTut&&typeof startTutorial==='function'){closeOverlay();startTutorial();return;}
  if(['login','main',''].includes(ov.dataset.view||''))showMenu('main');
}
const eloText=()=>profile.games>0?`Elo ${profile.elo}`:L('Play 1 game','Сыграйте 1 игру');""")

# hello carries the sign-in token, so the server knows who is in each seat
rep("ws.onopen=()=>{this.ready=true;this.raw({t:'hello',name:profile.name,pic:PIC_OK.test(profile.pic)?profile.pic:'',ver:GAME_VERSION});",
    "ws.onopen=()=>{this.ready=true;this.raw(helloMsg());")
rep("function onNet(m){", """function helloMsg(){return {t:'hello',name:profile.name,pic:PIC_OK.test(profile.pic)?profile.pic:'',ver:GAME_VERSION,token:Acc.token||''};}
function onNet(m){""")
rep("    case 'turn':onlineTurn(m);break;",
    "    case 'turn':onlineTurn(m);break;\n    case 'elo':eloResult(m);break;")

# ---------- menus ----------
rep("""  $('#pchipWrap').innerHTML=view==='main'?`<button class="pchip" type="button" data-a="m-profile" aria-label="${L('Profile','Профиль')}">${avatar()}<span class="elo">Elo ${profile.elo}</span></button>`:'';""",
    """  $('#pchipWrap').innerHTML=view==='main'?`<button class="pchip" type="button" data-a="m-profile" aria-label="${L('Profile','Профиль')}">${avatar()}<span class="elo">${eloText()}</span></button>`:'';""")
rep("""  if(view==='main'){
    ov.innerHTML=`<div class="card"><h1 class="logo">JOPIUM</h1>""",
    """  if(view==='login'){
    // first visit (or signed out): Google is the only way in
    ov.innerHTML=`<div class="card"><h1 class="logo">JOPIUM</h1><p style="text-align:center;margin:0">${L('Sign in to play. Your profile, Elo and nickname are saved to your Google account and stay through every update.','Войдите, чтобы играть. Профиль, Elo и никнейм сохраняются в вашем аккаунте Google и не пропадают при обновлениях.')}</p>
      <div class="mbtns"><button class="btn primary gbtn" type="button" data-a="acc-in"><svg viewBox="0 0 18 18" width="18" height="18" aria-hidden="true"><path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"/><path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"/><path fill="#FBBC05" d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1z"/><path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"/></svg> ${L('Sign in with Google','Войти через Google')}</button></div></div>`;
  }else if(view==='main'){
    ov.innerHTML=`<div class="card"><h1 class="logo">JOPIUM</h1>""")
# profile: nickname with a Save button (checked for uniqueness), uploaded picture, Elo or "Play 1 game"
rep("""      <div class="field"><label class="lab" for="nameIn">${L('Username','Имя игрока')}</label><input class="txt" id="nameIn" maxlength="18" value="${esc(profile.name)}" autocomplete="off" spellcheck="false"></div>
      <div class="field"><div class="lab">Elo<b>${profile.elo}</b></div></div>
      <div class="opts"><button class="btn primary" type="button" data-a="m-main">${L('Back','Назад')}</button></div></div>`;""",
    """      <div class="field"><label class="lab" for="nameIn">${L('Username','Имя игрока')}</label><div class="opts" style="flex-wrap:nowrap"><input class="txt" id="nameIn" maxlength="16" value="${esc(profile.name)}" autocomplete="off" spellcheck="false">${Acc.state==='in'?`<button class="btn small" type="button" data-a="acc-name">${L('Save','Сохранить')}</button>`:''}</div>${nameMsg?`<p class="sub ${nameMsg.ok?'good':'bad'}" style="margin:0">${esc(nameMsg.t)}</p>`:''}</div>
      <div class="field"><div class="lab">Elo<b>${profile.games>0?profile.elo:L('Play 1 game','Сыграйте 1 игру')}</b></div></div>
      ${Acc.state==='guest'?`<p class="sub" style="margin:0">${L('Guest profile: it stays on this device. Accounts, Elo and the leaderboard are in the full game.','Гостевой профиль хранится на этом устройстве. Аккаунты, Elo и таблица лидеров — в полной версии игры.')}</p>`:''}
      <div class="opts"><button class="btn primary" type="button" data-a="m-main">${L('Back','Назад')}</button>${Acc.state==='in'?`<button class="btn quiet" type="button" data-a="acc-out">${L('Sign out','Выйти из аккаунта')}</button>`:''}</div></div>`;""")
rep("""    ov.innerHTML=`<div class="card"><h1>${L('Leaderboard','Таблица лидеров')}</h1>
      <div class="lbhead"><span>#</span><span></span><span>${L('Player','Игрок')}</span><span>Elo</span></div>
      <div class="lbrow"><span class="rk">1</span>${avatar()}<b>${esc(profile.name)}</b><span class="mono">${profile.elo}</span></div>
      <div class="opts"><button class="btn" type="button" data-a="m-main">${L('Back','Назад')}</button></div></div>`;""",
    """    // places 1 to 100; ties go to whoever reached that Elo first; your own place shows below when you are lower
    const row=(r,place)=>`<div class="lbrow ${r.uid===profile.uid?'me':''}"><span class="rk">${place}</span>${picAvatar(r.pic,r.name)}<b>${esc(r.name)}</b><span class="mono">${r.elo}</span></div>`;
    let body;
    if(Acc.state==='guest')body=`<div class="empty">${L('The leaderboard is in the full game (itch.io or the server link).','Таблица лидеров есть в полной версии игры (itch.io или ссылка на сервер).')}</div>`;
    else if(!BOARD)body=`<div class="empty">${L('Loading…','Загрузка…')}</div>`;
    else if(BOARD.err)body=`<div class="empty">${esc(BOARD.err)}</div>`;
    else if(!BOARD.top.length)body=`<div class="empty">${L('Nobody has played an online game yet.','Ещё никто не сыграл сетевую игру.')}</div>`;
    else body=BOARD.top.map((r,i)=>row(r,i+1)).join('')+(BOARD.me?`<div class="lbgap">…</div>${row(BOARD.me,BOARD.me.place)}`:'');
    ov.innerHTML=`<div class="card"><h1>${L('Leaderboard','Таблица лидеров')}</h1>
      <div class="lbhead"><span>#</span><span></span><span>${L('Player','Игрок')}</span><span>Elo</span></div>
      <div class="lblist">${body}</div>
      <div class="opts"><button class="btn" type="button" data-a="m-main">${L('Back','Назад')}</button></div></div>`;""")
rep("    case 'm-board':showMenu('board');break;",
    "    case 'm-board':BOARD=null;showMenu('board');if(Acc.state==='in'||Acc.state==='out')Acc.board().then(b=>{BOARD=b;if(ov.dataset.view==='board')showMenu('board');}).catch(e=>{console.warn(e);BOARD={err:L(\"Couldn't load the leaderboard.\",'Не удалось загрузить таблицу.')};if(ov.dataset.view==='board')showMenu('board');});break;\n    case 'acc-in':Acc.signIn();break;\n    case 'acc-out':Acc.signOut();break;\n    case 'acc-name':{const v=($('#nameIn')||{}).value||'';Acc.rename(v.trim()).then(err=>{nameMsg=err?{t:err,ok:false}:{t:L('Saved.','Сохранено.'),ok:true};showMenu('profile');});break;}")
rep("    case 'm-profile':showMenu('profile');break;", "    case 'm-profile':nameMsg='';showMenu('profile');break;")
rep("    case 'm-picdel':profile.pic='';saveProfile();showMenu('profile');break;",
    "    case 'm-picdel':profile.pic='';saveProfile();if(Acc.state==='in')Acc.setPic('');showMenu('profile');break;")
# the uploaded picture: square crop, 128 px (accepted: PNG, JPG, WebP, GIF as a still)
rep("      profile.pic=c.toDataURL('image/jpeg',.85);saveProfile();showMenu('profile');",
    "      profile.pic=c.toDataURL('image/jpeg',.85);saveProfile();if(Acc.state==='in')Acc.setPic(profile.pic).catch(()=>toast(L(\"Couldn't save the picture.\",'Не удалось сохранить фото.'),true));showMenu('profile');")
rep("      <input type=\"file\" id=\"picIn\" accept=\"image/*\" hidden>", "      <input type=\"file\" id=\"picIn\" accept=\"image/png,image/jpeg,image/webp,image/gif\" hidden>")
# guests may still type a local name; signed-in players save through the button
rep("  if(e.target.id==='nameIn'){profile.name=e.target.value.trim().slice(0,18)||'Player';saveProfile();}",
    "  if(e.target.id==='nameIn'&&Acc.state!=='in'){profile.name=e.target.value.trim().slice(0,16)||'Player';saveProfile();}")

# ---------- the end screen: Elo slot roll (option B) ----------
rep("function endGame(result){", r"""// the server applied this match's Elo: roll the digits from the old value to the new one
let ELO_RES=null;
function eloResult(m){ELO_RES=m;profile.elo=m.after;profile.games=m.games;saveProfile();if(ov.dataset.view==='end')showEnd();}
function eloRoll(){
  const r=ELO_RES;if(!r)return G&&G.online&&!G.spectate?'':(G&&G.online?`<p class="sub" style="text-align:center">${L('Updating Elo…','Обновляем Elo…')}</p>`:'');
  const up=r.after>=r.before,d=r.after-r.before,a=String(r.before).padStart(4,' '),b=String(r.after).padStart(4,' ');
  return `<div class="eloroll" data-from="${r.before}" data-to="${r.after}">${[...b].map((ch,i)=>`<span class="dg"><span class="rl" data-f="${a[i]}" data-t="${ch}">${ch}</span></span>`).join('')}<div class="ebar"><i class="${up?'up':'down'}"></i></div><div class="${up?'good':'bad'}">${up?'+':'−'}${Math.abs(d)} Elo${r.first?L(' · your first rated game',' · ваша первая рейтинговая игра'):''}</div></div>`;
}
function animateElo(){
  const box=ov.querySelector('.eloroll');if(!box||box.dataset.done)return;box.dataset.done=1;
  const up=+box.dataset.to>=+box.dataset.from;
  box.querySelectorAll('.rl').forEach((el,i)=>{const f=el.dataset.f,t=el.dataset.t;if(f===t||t===' ')return;
    const seq=[];let x=f===' '?0:+f;const step=up?1:-1;for(let k=0;k<10*(1+i);k++){seq.push(x);x=(x+step+10)%10;}while(x!==+t){seq.push(x);x=(x+step+10)%10;}seq.push(+t);
    el.innerHTML=seq.map(n=>`<span>${n}</span>`).join('');
    el.animate([{transform:'translateY(0)'},{transform:`translateY(-${(seq.length-1)*1.3}em)`}],{duration:900+i*300,delay:350,easing:'cubic-bezier(.2,.7,.2,1)',fill:'forwards'});});
  const bar=box.querySelector('.ebar i');if(bar)bar.animate([{width:'50%'},{width:up?'62%':'38%'}],{duration:1400,delay:600,easing:'ease-out',fill:'forwards'});
}
function endGame(result){""")
rep("  ov.innerHTML=`<div class=\"card\"><button class=\"x\" type=\"button\" data-a=\"e-close\" aria-label=\"${L('Close and watch the map','Закрыть и смотреть карту')}\">✕</button><h1>${title}</h1><p>${text}</p><div class=\"opts\">",
    "  ov.innerHTML=`<div class=\"card\"><button class=\"x\" type=\"button\" data-a=\"e-close\" aria-label=\"${L('Close and watch the map','Закрыть и смотреть карту')}\">✕</button><h1>${title}</h1><p>${text}</p>${G.online?eloRoll():''}<div class=\"opts\">")
rep(".tabs{margin:0 auto 4px}", ".gbtn{display:flex;align-items:center;justify-content:center;gap:10px}.lblist{max-height:52vh;overflow:auto;display:grid;gap:2px}.lbrow.me{outline:1px solid var(--accent);border-radius:8px}.lbgap{text-align:center;color:var(--muted)}\n.eloroll{display:grid;justify-items:center;gap:8px;font-family:'IBM Plex Mono',monospace}.eloroll .dg{display:inline-block;width:1.1em;height:1.3em;overflow:hidden;background:var(--panel2);border-radius:5px;margin:0 2px;font-size:30px;line-height:1.3em;text-align:center;vertical-align:top}.eloroll .rl{display:flex;flex-direction:column}.eloroll .rl span{height:1.3em}.ebar{width:150px;height:6px;background:var(--panel2);border-radius:3px;overflow:hidden}.ebar i{display:block;height:100%;width:50%}.ebar i.up{background:var(--good)}.ebar i.down{background:var(--bad)}\n.tabs{margin:0 auto 4px}")

# start: accounts first; the main menu (or sign-in) appears once we know who is playing
rep("resize();showMenu('main');", "resize();showMenu(Acc.state==='guest'?'main':'login');Acc.init();")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
