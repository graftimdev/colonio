p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:70]}')
    s = s.replace(a, b)


a = s.index("const TECHS=[")
b = s.index("const TECH=Object.fromEntries")
s = s[:a] + """// Draft 9 tech tree: six routes out of the core. c = worker-turns to research; b = route; at = [depth, sideways offset in degrees]
const TECHS=[
  {id:'trade',b:0,at:[1,0],br:'Trade',rbr:'Торговля',n:'Trade',r:'Торговля',c:2,d:'Lets you trade 3 of one resource for 2 of another.',rd:'Можно менять 3 ед. одного ресурса на 2 ед. другого.'},
  {id:'xtrade',b:0,at:[2,-14],req:'trade',br:'Trade',rbr:'Торговля',n:'Crystal trade',r:'Торговля кристаллами',c:4,d:'Lets you trade Xenocrystal in and out.',rd:'Можно покупать и продавать кристаллы.'},
  {id:'rates',b:0,at:[2,14],req:'trade',br:'Trade',rbr:'Торговля',n:'Better rates',r:'Выгодный курс',c:3,d:'Trades take 4 and give 3.',rd:'Обмен 4 на 3.'},
  {id:'barrack',b:1,at:[1,0],br:'Barrack',rbr:'Казарма',n:'Barrack',r:'Казарма',c:2,d:'Unlocks the barrack: interceptor, bomber, frigate, siege, catapult and boomerang.',rd:'Открывает казарму: перехватчик, бомбер, фрегат, осада, катапульта и бумеранг.'},
  {id:'fleet10',b:1,at:[2,-14],req:'barrack',br:'Barrack',rbr:'Казарма',n:'Fleet size 10',r:'Размер флота 10',c:4,d:'Up to 10 units of one type per tile.',rd:'До 10 единиц одного типа на клетке.'},
  {id:'utility',b:1,at:[2,14],req:'barrack',br:'Barrack',rbr:'Казарма',n:'Utility drones',r:'Вспомогательные дроны',c:3,d:'The barrack can build the spy, engineer and charger.',rd:'Казарма может строить шпиона, инженера и зарядчика.'},
  {id:'upgradest',b:1,at:[3,16],req:'utility',br:'Barrack',rbr:'Казарма',n:'Upgrade station',r:'Станция улучшений',c:4,d:'Unlocks the upgrade station.',rd:'Открывает станцию улучшений.'},
  {id:'planetmove',b:2,at:[1,0],br:'Planets',rbr:'Планеты',n:'Planet movement',r:'Полёты на планеты',c:3,d:'War drones can travel onto planet tiles.',rd:'Боевые дроны могут летать на клетки планет.'},
  {id:'borehole',b:2,at:[2,-14],req:'planetmove',br:'Planets',rbr:'Планеты',n:'Boreholes',r:'Скважины',c:4,d:'Unlocks the borehole: 5 stargold a turn from a planet centre.',rd:'Открывает скважину: 5 звёздного золота за ход в центре планеты.'},
  {id:'rovers',b:2,at:[2,14],req:'planetmove',br:'Planets',rbr:'Планеты',n:'Rover barrack',r:'Казарма роверов',c:4,d:'Unlocks the rover barrack.',rd:'Открывает казарму роверов.'},
  {id:'turret',b:3,at:[1,0],br:'Turrets',rbr:'Турели',n:'Turret',r:'Турель',c:2,d:'Unlocks the turret.',rd:'Открывает турель.'},
  {id:'chain',b:3,at:[2,-14],req:'turret',br:'Turrets',rbr:'Турели',n:'Chain turret',r:'Цепная турель',c:3,d:'Unlocks the chain turret.',rd:'Открывает цепную турель.'},
  {id:'barrier',b:3,at:[3,-18],req:'chain',br:'Turrets',rbr:'Турели',n:'Electric barrier',r:'Электробарьер',c:4,d:'Unlocks the electric barrier.',rd:'Открывает электробарьер.'},
  {id:'xray',b:3,at:[2,14],req:'turret',br:'Turrets',rbr:'Турели',n:'X-ray turret',r:'Рентген турель',c:3,d:'Unlocks the X-ray turret.',rd:'Открывает рентген турель.'},
  {id:'death',b:3,at:[3,18],req:'xray',br:'Turrets',rbr:'Турели',n:'Death turret',r:'Турель смерти',c:6,d:'Unlocks the death turret.',rd:'Открывает турель смерти.'},
  {id:'generator',b:4,at:[1,0],br:'Energy',rbr:'Энергия',n:'Energy generator',r:'Генератор энергии',c:2,d:'Unlocks the energy generator.',rd:'Открывает генератор энергии.'},
  {id:'estorage',b:4,at:[2,-14],req:'generator',br:'Energy',rbr:'Энергия',n:'Energy storage',r:'Накопитель энергии',c:2,d:'Unlocks the energy storage.',rd:'Открывает накопитель энергии.'},
  {id:'drills',b:4,at:[2,14],req:'generator',br:'Energy',rbr:'Энергия',n:'Efficient drills',r:'Экономные буры',c:3,d:'Mining costs half as much energy.',rd:'Добыча тратит вдвое меньше энергии.'},
  {id:'deepscan',b:5,at:[1,0],br:'Worker',rbr:'Рабочие',n:'Deep scan',r:'Глубокое сканирование',c:2,d:"Exploring a tile also reveals its neighbours' rings.",rd:'Исследуя клетку, рабочий также раскрывает кольца соседних.'},
  {id:'thrusters',b:5,at:[2,-14],req:'deepscan',br:'Worker',rbr:'Рабочие',n:'Worker thrusters',r:'Двигатели рабочих',c:3,d:'Workers move 2 hops per turn.',rd:'Рабочие пролетают 2 прыжка за ход.'},
  {id:'radio',b:5,at:[2,14],req:'deepscan',br:'Worker',rbr:'Рабочие',n:'Radio',r:'Радио',c:3,d:'Every planet centre stays in your sight for good.',rd:'Все центры планет навсегда остаются в зоне видимости.'}
];
""" + s[b:]

a = s.index("const WEB={")
b = s.index("\n", s.index("const BRANCH_LBL=")) + 1
s = s[:a] + """// star-map positions (percent of the tech screen), worked out from each tech's route and depth
const WEB={};
{const R0=[0,17,31,44];for(const t of TECHS){const ang=(-90+t.b*60+t.at[1])*Math.PI/180,r=R0[t.at[0]];WEB[t.id]=[50+Math.cos(ang)*r,50+Math.sin(ang)*r];}}
const BRANCH_LBL=['Trade','Barrack','Planets','Turrets','Energy','Worker'].map((n,b)=>{const ru=['ТОРГОВЛЯ','КАЗАРМА','ПЛАНЕТЫ','ТУРЕЛИ','ЭНЕРГИЯ','РАБОЧИЕ'][b],ang=(-90+b*60)*Math.PI/180;return [n.toUpperCase(),ru,50+Math.cos(ang)*24,50+Math.sin(ang)*24+1];});
""" + s[b:]
rep("const tileCap=pid=>6+2*['fleet1','fleet2','fleet3'].filter(t=>has(pid,t)).length;", "const tileCap=pid=>has(pid,'fleet10')?10:6;")
rep("    if(has(p.id,'optics'))for(const n of G.nodes)if(n.owner===p.id)n.nbr.forEach(x=>p.explored.add(x));",
    "    if(has(p.id,'radio'))for(const pl of G.planets||[])p.explored.add(pl.center);")
a = s.index("const AI_TECH=[")
b = s.index("\n", a)
s = s[:a] + "const AI_TECH=['generator','barrack','turret','deepscan','trade','drills','planetmove','utility','fleet10','chain','xray','thrusters','estorage','borehole','upgradest','rovers','radio','barrier','rates','death','xtrade'];" + s[b:]

# stations now need their techs
for st, tech in [('kazarm', 'barrack'), ('upgrade', 'upgradest'), ('barrier', 'barrier'), ('estorage', 'estorage'),
                 ('generator', 'generator'), ('rbarracks', 'rovers'), ('borehole', 'borehole')]:
    key = f"\n  {st}:{{n:"
    i = s.index(key)
    j = s.index("cost:", i)
    s = s[:j] + f"tech:'{tech}'," + s[j:]
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
