"""Draft 10 stage 3b: diplomacy screens (Rivals list, treaty/break popups, incoming treaties), peace link lines."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:90]}')
    s = s.replace(a, b)


rep("const TASKN_EN={idle:'Idle',mine:'Mining',claim:'Claiming',research:'Researching',build:'Building',fix:'Repairing'};",
    "const TASKN_EN={idle:'Idle',mine:'Mining',claim:'Claiming',research:'Researching',build:'Building',fix:'Repairing',diplo:'Diplomacy'};")
rep("const TASKN_RU={idle:'Без дела',mine:'Добывает',claim:'Захватывает',research:'Исследует',build:'Строит',fix:'Чинит'};",
    "const TASKN_RU={idle:'Без дела',mine:'Добывает',claim:'Захватывает',research:'Исследует',build:'Строит',fix:'Чинит',diplo:'Дипломатия'};")
rep("  if(w.task==='research')return w.tech?",
    "  if(w.task==='diplo')return `${taskN('diplo')}: ${(w.diplo||[]).map(d=>(d.brk?L('break peace with ','разрыв мира с '):L('peace treaty to ','мир с '))+esc(pShort(P(d.to)))).join(', ')}`;\n  if(w.task==='research')return w.tech?")

# ---------- Empire: Rivals ----------
rep("  h+=`</div><div class=\"sec\"><h3>${L('Workers','Рабочие')}</h3>`;",
    r"""  // rivals: everyone is listed; ones you haven't met yet are "unknown rival"
  const met=metOf(ME);
  h+=`</div><div class="sec"><h3>${L('Rivals','Соперники')}</h3>`;
  for(const q of G.players){if(q.id===ME)continue;
    if(!met.has(q.id)){h+=`<div class="row"><div class="grow sub">${L('Unknown rival','Неизвестный соперник')}${q.alive?'':' · '+L('out','выбыл')}</div></div>`;continue;}
    const inc=(G.treaties||[]).find(t=>t.from===q.id&&t.to===ME&&t.ans==null),sent=(G.treaties||[]).some(t=>t.from===ME&&t.to===q.id);
    const st=!q.alive?L('Out of the game','Выбыл'):atPeace(ME,q.id)?`<span class="good">${L('At peace','Мир')}</span>`:inc?`<span class="warn">${L('Wants peace','Предлагает мир')}</span>`:sent?L('Treaty sent','Договор отправлен'):L('No treaty','Нет договора');
    h+=`<div class="row ${q.alive?'click':''}" ${q.alive?`data-a="rival" data-p="${q.id}"`:''}><div class="grow"><b style="color:${q.color}">${esc(pName(q))}</b><br><span class="sub">${st}</span></div></div>`;}
  h+=`</div><div class="sec"><h3>${L('Workers','Рабочие')}</h3>`;""")

# ---------- popups ----------
rep("  }else if(m.type==='charge'){", r"""  }else if(m.type==='rival'){
    // send a treaty or break the peace: a worker at the core spends this turn on it
    const q=P(m.p),peace=atPeace(ME,m.p),ws=idleFirst(G.workers.filter(w=>w.owner===ME&&w.node===p.core&&!w.path.length));
    const can=peace||has(ME,'diplomacy');
    h+=`<h2>${peace?L(`Do you want to break the peace with ${esc(pName(q))}?`,`Разорвать мир с ${esc(pName(q))}?`):L(`Do you want to send a peace treaty to ${esc(pName(q))}?`,`Отправить мирный договор игроку ${esc(pName(q))}?`)}</h2>`;
    if(peace)h+=`<p class="sub" style="margin:0">${L("If you break it, all your squadrons on their tiles are destroyed. Theirs on your tiles are not.",'Если вы разорвёте мир, все ваши эскадрильи на их клетках будут уничтожены. Их эскадрильи на ваших клетках — нет.')}</p>`;
    if(!can)h+=`<p class="sub" style="margin:0">${L('Research Diplomacy (after Better rates) to send peace treaties.','Изучите Дипломатию (после «Выгодного курса»), чтобы отправлять мирные договоры.')}</p>`;
    else{
      h+=`<div class="sec"><h3>${L('Your workers at the core','Ваши рабочие в ядре')} · ${ws.length}</h3>`;
      if(!ws.length)h+=`<p class="sub" style="margin:0">${L('A worker standing at your core spends one turn on this. Move one there first.','Это занимает один ход рабочего в ядре. Сначала приведите туда рабочего.')}</p>`;
      for(const w of ws){const here=w.task==='diplo'&&(w.diplo||[]).some(d=>d.to===m.p);
        h+=`<div class="row"><div class="grow"><b>${esc(w.name)}</b><br><span class="sub">${workerStatus(w)}</span></div>${here?`<button class="btn small" type="button" data-a="dstop" data-w="${w.id}">${L('Stop','Стоп')}</button>`:`<button class="btn small primary" type="button" data-a="dset" data-w="${w.id}" data-p="${m.p}" data-b="${peace?1:0}">${peace?L('Yes, break it','Да, разорвать'):L('Assign','Назначить')}</button>`}</div>`;}
      h+=`</div>`;
    }
    h+=`<div class="opts"><button class="btn" type="button" data-a="pclose">${peace?L('No','Нет'):L('Close','Закрыть')}</button></div>`;
  }else if(m.type==='treaty'){
    const q=P(m.from);
    h+=`<h2>${L(`${esc(pName(q))} wants to make peace with you`,`${esc(pName(q))} хочет заключить с вами мир`)}</h2><p class="sub" style="margin:0">${L("At peace you can't attack each other, you see each other's cores and spies, and your networks link where they touch. Either of you can break it later.",'В мире вы не можете нападать друг на друга, видите ядра и шпионов друг друга, а ваши сети соединяются там, где соприкасаются. Любой из вас может потом разорвать мир.')}</p>`;
    h+=`<div class="opts"><button class="btn primary" type="button" data-a="tans" data-p="${m.from}" data-y="1">${L('Accept','Принять')}</button><button class="btn" type="button" data-a="tans" data-p="${m.from}" data-y="0">${L('Decline','Отклонить')}</button></div>`;
  }else if(m.type==='charge'){""")

# ---------- clicks ----------
rep("    case 'chg':if(G.popup&&G.popup.type==='charge')G.popup.cr=+d.k;break;",
    """    case 'chg':if(G.popup&&G.popup.type==='charge')G.popup.cr=+d.k;break;
    case 'rival':closeModal();G.popup={type:'rival',p:+d.p};G.popupAt=performance.now();break;
    case 'dset':order({t:'diplo',w:+d.w,to:+d.p,brk:d.b==='1'});break;
    case 'dstop':order({t:'task',w:+d.w,task:'idle'});break;
    case 'tans':{if(order({t:'peaceans',from:+d.p,yes:d.y==='1'})){(G.treatySeen=G.treatySeen||new Set()).add(+d.p);G.popup=null;toast(d.y==='1'?L('Accepted: peace starts when this turn ends.','Принято: мир начнётся в конце хода.'):L('Declined.','Отклонено.'));}break;}""")

# incoming treaties pop up on their own once per turn
rep("function refresh(){\n  if(!G)return;\n",
    "function refresh(){\n  if(!G)return;\n  if(!G.popup&&!G.modal&&!G.over){const t=(G.treaties||[]).find(t=>t.to===ME&&t.ans==null&&!(G.treatySeen&&G.treatySeen.has(t.from+':'+t.t)));if(t){(G.treatySeen=G.treatySeen||new Set()).add(t.from+':'+t.t);G.popup={type:'treaty',from:t.from};G.popupAt=performance.now();}}\n")
rep("'techFor','rockets','shocks','pulses','pulseT0',", "'techFor','rockets','shocks','pulses','pulseT0','treatySeen',")

# ---------- map: partners' networks join with a two-colour dotted line ----------
rep("  ctx.setLineDash([]);\n  for(const f of G.fleets)if(f.cls==='charger'&&f.up&&f.settled",
    """  ctx.setLineDash([]);
  for(const x of G.peace||[]){if(!G.conn[x.a]||!G.conn[x.b])continue;
    for(const id of G.conn[x.a])if(V.has(id))for(const nb of G.nodes[id].nbr)if(G.conn[x.b].has(nb)&&V.has(nb)){
      const [ax,ay]=toScreen(G.nodes[id].x,G.nodes[id].y),[bx,by]=toScreen(G.nodes[nb].x,G.nodes[nb].y),mx=(ax+bx)/2,my=(ay+by)/2;
      ctx.setLineDash([3,5]);ctx.lineWidth=2;ctx.strokeStyle=hexa(P(x.a).color,.9);ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(mx,my);ctx.stroke();
      ctx.strokeStyle=hexa(P(x.b).color,.9);ctx.beginPath();ctx.moveTo(mx,my);ctx.lineTo(bx,by);ctx.stroke();ctx.setLineDash([]);}}
  for(const f of G.fleets)if(f.cls==='charger'&&f.up&&f.settled""")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
