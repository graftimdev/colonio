# Step 5 of tools/build.py: online turns, lobby screens and the server connection.
# Runs inside build.py (uses its rep / cut_between / snippet helpers and the text `s`).

rep("const GAME_VERSION='ver. 0.1.7';", "const GAME_VERSION='ver. 0.1.8';")

# --- ending a turn: online, send the orders and wait; offline, resolve at once as before
rep("""function endTurn(auto){
  if(!G||(G.over&&!G.spectate))return;""", """function endTurn(auto){
  if(!G||(G.over&&!G.spectate))return;
  if(G.online&&(G.waiting||(!P(ME).alive&&humansLeft())))return;""")
rep("pending.forEach(w=>w.task='idle');", "pending.forEach(w=>order({t:'task',w:w.id,task:'idle'}));")
rep("""  G.moveMode=null;G.hoverPath=null;G.splitOpen=null;
  sfxTurn();resolve();
  // the report only pops up when someone's core fell; everything else waits behind the Report button
  if(G.coreFell&&!G.over)openModal({type:'report'});""", """  if(G.online){submitTurn();return;}
  G.moveMode=null;G.hoverPath=null;G.splitOpen=null;
  sfxTurn();resolve();
  afterResolve();
}
function afterResolve(){
  // the report only pops up when someone's core fell; everything else waits behind the Report button
  if(G.coreFell&&!G.over)openModal({type:'report'});""")

rep("else if(!P(ME).alive)endGame('lost');", "else if(!P(ME).alive)endGame(G.iResigned?'resigned':'lost');")

# --- the turn timer keeps running online even with a menu open, and stops while you wait for others
rep("if(!G||G.over||!G.turnTime||!$('#overlay').hidden)return;G.timeLeft-=dt;",
    "if(!G||G.over||!G.turnTime||G.waiting||(!G.online&&!$('#overlay').hidden))return;G.timeLeft-=dt;")
rep("const alarm=!!G.turnTime&&!G.over&&t<=5&&t>0&&$('#overlay').hidden;",
    "const alarm=!!G.turnTime&&!G.over&&!G.waiting&&t<=5&&t>0&&$('#overlay').hidden;")

# --- End turn button: shows who we are waiting for online
rep("""  $('#endturn').disabled=G.over&&!G.spectate;
  $('#endturn').textContent=G.spectate?L('Next turn','Следующий ход'):L('End turn','Завершить ход');""",
"""  const watching=G.online&&G.spectate&&!P(ME).alive&&humansLeft();
  $('#endturn').disabled=(G.over&&!G.spectate)||G.waiting||watching;
  $('#endturn').textContent=watching?L('Watching','Наблюдение'):G.waiting?L('Waiting','Ожидание')+(G.waitInfo?' · '+G.waitInfo:''):G.spectate?L('Next turn','Следующий ход'):L('End turn','Завершить ход');""")

# --- resign / leave
rep("$('#resign').onclick=()=>{if(!G)return;if(G.over)showEnd();else endGame('resigned');};",
    "$('#resign').onclick=()=>{if(!G)return;if(G.over)showEnd();else if(G.online)resignOnline();else endGame('resigned');};")
rep("function leaveGame(){G=null;", "function leaveGame(){if(G&&G.online)Net.leaveRoom();G=null;SNAP=null;myCmds=[];")

# --- end screen: online there is no "next game" with the same people (yet)
rep("""<button class="btn primary" type="button" data-a="e-next">${L('Next game','Следующая игра')}</button>""",
    """${G.online?'':`<button class="btn primary" type="button" data-a="e-next">${L('Next game','Следующая игра')}</button>`}""")
rep("""${L('Watch the AIs','Смотреть за ИИ')}""", """${G.online?L('Keep watching','Смотреть дальше'):L('Watch the AIs','Смотреть за ИИ')}""")
rep("L(`Every rival AI has been shut down. You control the belt after ${G.turn-1} turns.`,`Все ИИ-соперники отключены. За ${cnt(G.turn-1,'turn')} вы взяли пояс под контроль.`)",
    "L(`Every rival has been shut down. You control the belt after ${G.turn-1} turns.`,`Все соперники отключены. За ${cnt(G.turn-1,'turn')} вы взяли пояс под контроль.`)")

# --- lobby and join screens now talk to the server
cut_between("  }else if(view==='lobby'){", "  }else if(view==='board'){", """  }else if(view==='lobby'){
    ov.innerHTML=lobbyHtml();if(LOBBY)startLobbyAnim();
  }else if(view==='join'){
    ov.innerHTML=joinHtml();
""")
rep("if(/^[mseh]-/.test(a))return menuAct(a,d);", "if(/^[msehjl]-/.test(a))return menuAct(a,d);")
rep("case 'm-join':showMenu('join');break;",
    "case 'm-join':LOBBIES=null;netError='';showMenu('join');Net.send({t:'list'});break;")
rep("case 'h-go':keepLobbyName();showMenu('lobby');break;\n    case 'm-leave':showMenu('main');break;",
"""case 'h-go':keepLobbyName();LOBBY=null;netError='';showMenu('lobby');
      Net.send({t:'host',who:{name:profile.name,pic:PIC_OK.test(profile.pic)?profile.pic:''},name:hostOpts.name||L(`${profile.name}'s lobby`,`Лобби ${profile.name}`),mode:hostOpts.mode,per:hostOpts.per,opp:hostOpts.opp,timer:hostOpts.timer});break;
    case 'm-leave':Net.leaveRoom();showMenu('main');break;
    case 'l-start':Net.send({t:'start'});break;
    case 'j-go':Net.send({t:'join',code:d.c,who:{name:profile.name,pic:PIC_OK.test(profile.pic)?profile.pic:''}});break;
    case 'j-code':{const v=(($('#codeIn')||{}).value||'').trim().toUpperCase();if(v)Net.send({t:'join',code:v,who:{name:profile.name,pic:PIC_OK.test(profile.pic)?profile.pic:''}});break;}
    case 'j-refresh':LOBBIES=null;netError='';showMenu('join');Net.send({t:'list'});break;""")

rep('/* ---------- menus ---------- */', snippet('net.js') + '\n/* ---------- menus ---------- */')
