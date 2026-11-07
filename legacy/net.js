/* ---------- online play: connection to the game server ---------- */
// The server only relays orders between players; every screen runs the match itself (see applyCmd).
// Where the server lives: ?server=wss://... in the page address wins; a page served by the game server itself
// (your PC, or the hosting service) talks to that same address; anything else (itch.io) uses DEFAULT_SERVER.
const DEFAULT_SERVER='wss://jopium-server.onrender.com';
const SERVER_URL=(()=>{
  try{const q=new URLSearchParams(location.search).get('server');if(q)return q;}catch(e){}
  const h=location.hostname||'';
  if(/^(localhost|127\.0\.0\.1|\[::1\])$/.test(h)||h.endsWith('.onrender.com')||h.endsWith('.fly.dev')||h.endsWith('.up.railway.app'))
    return (location.protocol==='https:'?'wss://':'ws://')+location.host;
  return DEFAULT_SERVER;
})();
const PIC_OK=/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/;
let LOBBY=null,LOBBIES=null,netError='';
const Net={
  ws:null,ready:false,queue:[],
  connect(){
    if(this.ws)return;
    let ws;try{ws=new WebSocket(SERVER_URL);}catch(e){netError=L("Can't reach the game server.",'Не удаётся связаться с игровым сервером.');onNetClose();return;}
    this.ws=ws;netError='';
    ws.onopen=()=>{this.ready=true;this.raw({t:'hello',name:profile.name,pic:PIC_OK.test(profile.pic)?profile.pic:'',ver:GAME_VERSION});for(const m of this.queue.splice(0))this.raw(m);};
    ws.onmessage=e=>{let m;try{m=JSON.parse(e.data);}catch(x){return;}onNet(m);};
    ws.onclose=()=>{const was=this.ready;this.ready=false;this.ws=null;this.queue=[];if(!was&&!netError)netError=L("Can't reach the game server. Check your internet connection and try again.",'Не удаётся связаться с игровым сервером. Проверьте подключение к интернету и попробуйте снова.');onNetClose();};
  },
  raw(m){try{this.ws.send(JSON.stringify(m));}catch(e){}},
  send(m){if(this.ready)this.raw(m);else{this.queue.push(m);this.connect();}},
  leaveRoom(){if(this.ready)this.raw({t:'leave'});LOBBY=null;}
};
function onNetClose(){
  if(G&&G.online&&!G.over){G.waiting=true;G.notice=L('Connection to the game server was lost. This match cannot continue; open the game menu to leave.','Связь с игровым сервером потеряна. Матч не может продолжиться; откройте меню игры, чтобы выйти.');toast(L('Connection lost.','Связь потеряна.'),true);openModal({type:'report'});refresh();return;}
  if(LOBBY){LOBBY=null;showMenu('play');}
  const v=ov.dataset.view;
  if(!G&&(v==='join'||v==='play'||v==='host'))showMenu(v);
}
function onNet(m){
  switch(m.t){
    case 'lobbies':LOBBIES=m.list||[];if(!G&&ov.dataset.view==='join')showMenu('join');break;
    case 'lobby':{const same=LOBBY&&LOBBY.code===m.room.code;LOBBY=m.room;if(G)break;if(same&&ov.dataset.view==='lobby')renderLobbyParts();else showMenu('lobby');break;}
    case 'closed':LOBBY=null;if(!G){showMenu('play');toast(m.msg||L('The lobby was closed.','Лобби закрыто.'),true);}break;
    case 'error':toast(m.msg||L('Something went wrong.','Что-то пошло не так.'),true);if(!G&&ov.dataset.view==='join')showMenu('join');break;
    case 'start':
      LOBBY=null;
      newGame({mode:m.opts.mode,per:m.opts.per,timer:m.opts.timer,diff:'normal',online:{seed:m.seed,seats:m.seats,you:m.you,room:m.code}});
      toast(L('Match started. Good luck!','Матч начался. Удачи!'));
      break;
    case 'progress':if(G&&G.online){G.waitInfo=`${m.done}/${m.need}`;renderTop();}break;
    case 'turn':onlineTurn(m);break;
    case 'desync':if(G&&G.online)toast(L(`Warning: players' games went out of sync on turn ${m.turn}. Please report this.`,`Внимание: игры игроков рассинхронизировались на ходу ${m.turn}. Сообщите об этом.`),true);break;
  }
}
// send this turn's orders and wait for everyone else
function submitTurn(){
  if(!G||!G.online||G.waiting)return;
  G.waiting=true;G.waitInfo='';G.moveMode=null;G.hoverPath=null;G.splitOpen=null;
  Net.send({t:'end',turn:G.turn,cmds:myCmds});
  refresh();
}
// everyone has ended the turn: rewind to the start of the turn, replay all orders in seat order, then resolve
function onlineTurn(m){
  if(!G||!G.online||!SNAP||m.turn!==G.turn)return;
  restoreSnapshot();
  REPLAY=true;
  try{for(let pid=0;pid<G.players.length;pid++)for(const c of (m.cmds[pid]||[])){try{applyCmd(pid,c);}catch(e){console.warn('Jopium: order failed',c,e);}}}
  finally{REPLAY=false;}
  const gone=(m.dropped||[]).map(pid=>G.players[pid]).filter(q=>q&&!q.ai);
  gone.forEach(q=>{q.ai=true;});
  myCmds=[];G.waiting=false;G.waitInfo='';
  sfxTurn();resolve();
  for(const q of gone)log(L(`${pShort(q)} left the match; an AI took over their empire.`,`${pShort(q)} покинул матч, его империей теперь управляет ИИ.`),'warn',null,G.players.map(x=>x.id));
  takeSnapshot();
  Net.send({t:'hash',turn:m.turn,h:stateHash()});
  afterResolve();
  // out of the match: keep watching without holding up the people still playing.
  // Once no person is left in the match, nobody is waiting: watchers step through turns with Next turn.
  if(!P(ME).alive&&humansLeft()){G.waiting=true;Net.send({t:'end',turn:G.turn,cmds:[]});refresh();}
}
// is any person (not an AI) still playing?
const humansLeft=()=>G.players.some(p=>p.human&&!p.ai&&p.alive)&&G.players.filter(p=>p.alive).length>1;
function resignOnline(){
  if(!P(ME).alive)return;
  G.iResigned=true;
  if(G.waiting)Net.send({t:'resign',turn:G.turn});
  else{order({t:'resign'});G.waiting=false;submitTurn();}
  toast(L('You resigned. The match ends for you when this turn resolves.','Вы сдались. Матч для вас закончится, когда этот ход завершится.'));
}
function picAvatar(pic,label,cls){const ok=PIC_OK.test(pic||'');return `<span class="av ${cls||''}" ${ok?`style="background-image:url('${pic}')"`:''} role="img" aria-label="${esc(label)}">${ok?'':AV_EMPTY}</span>`;}
const modeName=m=>m==='conquest'?L('Conquest','Завоевание'):L('Warfare','Сражение');
const timerName=t=>t?L(`${t} s turns`,`ход ${t} с`):L('no timer','без таймера');
function lobbySlots(){
  const R0=LOBBY;let h='';
  for(let i=0;i<R0.need;i++){const q=R0.players[i];
    h+=q?`<div class="slot on">${picAvatar(q.pic,q.name)}<span>${esc(q.name)}${i===0?' ★':''}</span></div>`:`<div class="slot"><span>${L('Waiting…','Ожидание…')}</span></div>`;}
  return h;
}
function lobbyCount(){const R0=LOBBY;return `${R0.players.length<R0.need?L('Searching for players','Поиск игроков'):L('Starting…','Начинаем…')} · ${R0.players.length}/${R0.need}`;}
function renderLobbyParts(){
  if(!LOBBY)return;
  const c=$('#lcount'),g=$('#lslots'),b=$('#lstart');
  if(c)c.textContent=lobbyCount();if(g)g.innerHTML=lobbySlots();if(b)b.disabled=LOBBY.players.length<2;
}
function lobbyHtml(){
  const R0=LOBBY;
  if(!R0)return `<div class="card"><h1>${L('Connecting…','Подключение…')}</h1><p>${esc(netError)||L('Contacting the game server.','Связываемся с игровым сервером.')}</p><div class="opts"><button class="btn" type="button" data-a="m-play">${L('Back','Назад')}</button></div></div>`;
  return `<div class="card"><h1 style="font-size:20px">${esc(R0.name)}</h1>
      <canvas id="lobbycv" aria-label="${L('Searching for players','Поиск игроков')}"></canvas>
      <div class="lcount" id="lcount">${lobbyCount()}</div>
      <p class="sub" style="margin:0;text-align:center">${L('Lobby code','Код лобби')} <b class="mono" style="color:var(--fg);letter-spacing:.15em">${esc(R0.code)}</b> · ${modeName(R0.mode)} · ${L(`${R0.per} asteroids per player`,`${R0.per} астероидов на игрока`)} · ${timerName(R0.timer)}</p>
      <div class="lgrid" id="lslots">${lobbySlots()}</div>
      ${R0.host?`<p class="sub" style="margin:0">${L('The match starts by itself when every seat is taken. Start early and the AI takes the empty seats.','Матч начнётся сам, когда все места займут. Если начать раньше, пустые места займёт ИИ.')}</p>`:''}
      <div class="opts">${R0.host?`<button class="btn primary" type="button" id="lstart" data-a="l-start" ${R0.players.length<2?'disabled':''}>${L('Start now','Начать сейчас')}</button>`:''}<button class="btn danger" type="button" data-a="m-leave">${L('Leave lobby','Покинуть лобби')}</button></div></div>`;
}
function joinHtml(){
  let list;
  if(netError)list=`<div class="empty">${esc(netError)}</div>`;
  else if(LOBBIES==null)list=`<div class="empty">${L('Looking for lobbies…','Ищем лобби…')}</div>`;
  else if(!LOBBIES.length)list=`<div class="empty">${L('No open lobbies right now. Host one, or ask a friend for their lobby code.','Сейчас нет открытых лобби. Создайте своё или попросите у друга код лобби.')}</div>`;
  else list=LOBBIES.map(r=>`<div class="row"><div class="grow"><b>${esc(r.name)}</b><br><span class="sub">${modeName(r.mode)} · ${r.players}/${r.need} · ${timerName(r.timer)}</span></div><button class="btn small primary" type="button" data-a="j-go" data-c="${esc(r.code)}">${L('Join','Войти')}</button></div>`).join('');
  return `<div class="card"><h1>${L('Join lobby','Найти лобби')}</h1>
      <div class="sec">${list}</div>
      <div class="field"><label class="lab" for="codeIn">${L('Lobby code','Код лобби')}</label><div class="opts" style="flex-wrap:nowrap"><input class="txt mono" id="codeIn" maxlength="4" autocomplete="off" spellcheck="false" style="text-transform:uppercase;letter-spacing:.2em"><button class="btn primary" type="button" data-a="j-code" style="flex:none">${L('Join','Войти')}</button></div></div>
      <div class="opts"><button class="btn" type="button" data-a="m-play">${L('Back','Назад')}</button><button class="btn" type="button" data-a="j-refresh">${L('Refresh','Обновить')}</button></div></div>`;
}
