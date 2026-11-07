"""Draft 9: top bar shows the 100 combined resource limit and a selected cut-off cluster's energy; Empire shows cut-off fleets."""
p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:80]}')
    s = s.replace(a, b)


rep("""  const use=energyUse(ME),prod=energyProd(ME),net=Math.round((prod-use)*10)/10;
  $('#energy').innerHTML=`${Math.floor(p.energy)}/${energyCap(ME)} <span class="${net<0?'bad':'good'}">${net>=0?'+':''}${net}</span>`;""",
    """  // with one of your cut-off tiles selected, the energy chip shows that cluster's own energy instead of the core's
  const cl=G.sel!=null&&G.nodes[G.sel].owner===ME&&!G.conn[ME].has(G.sel)?clusterEnergy(ME,G.sel):null;
  const use=cl?cl.use:energyUse(ME),prod=cl?cl.prod:energyProd(ME),net=Math.round((prod-use)*10)/10;
  $('#energy').innerHTML=cl?`<span class="warn">${L('Cut off','Отрезано')}</span> ${Math.floor(cl.stored)}/${cl.cap} <span class="${net<0?'bad':'good'}">${net>=0?'+':''}${net}</span>`:`${Math.floor(p.energy)}/${energyCap(ME)} <span class="${net<0?'bad':'good'}">${net>=0?'+':''}${net}</span>`;""")
rep("""+`<span class="chip muted" title="${L(`Storage: ${BASE_RES} of each, plus ${shared} shared`,`Хранилище: по ${BASE_RES} каждого и ${shared} общего`)}">/${BASE_RES}${shared?'+'+shared:''}</span>`;""",
    """+`<span class="chip muted" title="${L(`Resources held in total, out of ${BASE_RES} plus ${shared} from storages`,`Всего ресурсов из ${BASE_RES} и ${shared} от складов`)}">${resTotal(p)}/${resCap(ME)}</span>`;""")
rep("${L(`${BASE_RES} of each plus ${sharedCap(ME)} shared`,`по ${BASE_RES} каждого и ${sharedCap(ME)} общего`)}",
    "${L(`${resTotal(P(ME))} of ${resCap(ME)} in total`,`всего ${resTotal(P(ME))} из ${resCap(ME)}`)}")
rep("${L(`${BASE_RES} each + ${sharedCap(ME)} shared`,`по ${BASE_RES} + ${sharedCap(ME)} общего`)}",
    "${L(`${resTotal(p)} of ${resCap(ME)} in total`,`всего ${resTotal(p)} из ${resCap(ME)}`)}")
rep(":L('holding','на месте');\n    h+=`<div class=\"row\" data-fdrop=",
    ":L('holding','на месте');\n    const cutTxt=f.cls!=='spy'&&f.cls!=='leviathan'&&!fleetOnGrid(f)?` · <span class=\"warn\">${L('cut off','отрезан')}</span>`:'';\n    h+=`<div class=\"row\" data-fdrop=")
rep("· <span class=\"sub\">${nodeName(G.nodes[f.node])} · ${task}</span></div></div>`;",
    "· <span class=\"sub\">${nodeName(G.nodes[f.node])} · ${task}${cutTxt} · ${BOLT}${f.cls==='leviathan'?'∞':avgEn(f)}</span></div></div>`;")
rep("function payEnergy(pid,id,amt){", """// a cut-off cluster's own energy: what its batteries hold, what it makes and what it uses a turn
function clusterEnergy(pid,id){
  const cl=clusterOf(pid,id),ids=new Set(cl.map(x=>x.id));
  const prod=cl.reduce((a,x)=>a+5*live(x,'generator').length+(x.type==='captured'?10:0),0);
  let use=0;for(const w of G.workers)if(w.owner===pid&&ids.has(w.node)&&!w.path.length){if(w.task==='build')use+=1;if(w.task==='mine')use+=has(pid,'drills')?.5:1;}
  for(const x of cl)for(const st of live(x,'barrier'))if(!st.off)use+=1;
  for(const f of G.fleets)if(f.owner===pid&&ids.has(f.node)&&!fleetOnGrid(f))use+=droneUse(f)*f.count;
  return {stored:cl.reduce((a,x)=>a+x.estore,0),cap:cl.reduce((a,x)=>a+30*live(x,'estorage').length,0),prod,use};
}
function payEnergy(pid,id,amt){""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
