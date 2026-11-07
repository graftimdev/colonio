p = 'client/index.html'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        raise SystemExit(f'count {c}: {a[:70]}')
    s = s.replace(a, b)


rep("const CLS=[...SPACE,...ROVERS,'leviathan'];", """const CLS=[...SPACE,...ROVERS,'leviathan'];
// spy, engineer and charger need the Utility drones tech
const UTIL=['spy','repair','charger'];
const canMake=(pid,c)=>!UTIL.includes(c)||has(pid,'utility');
// war drones need Planet movement to enter planet tiles; rovers live there and leviathans go anywhere
const planetOk=(pid,cls,id)=>G.nodes[id].planet==null||DR[cls].ground||cls==='leviathan'||has(pid,'planetmove');""")
rep("const ok=f.s.type==='rbarracks'?ROVERS.includes(c.c):f.s.type==='kazarm'?SPACE.includes(c.c):false;",
    "const ok=(f.s.type==='rbarracks'?ROVERS.includes(c.c):f.s.type==='kazarm'?SPACE.includes(c.c):false)&&canMake(pid,c.c);")
rep("list=s.type==='rbarracks'?ROVERS:SPACE;", "list=(s.type==='rbarracks'?ROVERS:SPACE).filter(c=>canMake(ME,c));")
rep("      if(tileCount(u.owner,nx,u.cls,u)+u.count>tileCap(u.owner)){",
    "      if(!planetOk(u.owner,u.cls,nx)){u.path=[];u.mergeInto=null;continue;}\n      if(tileCount(u.owner,nx,u.cls,u)+u.count>tileCap(u.owner)){")
# routes the interface offers also skip planet tiles until Planet movement
i = s.index("const routeSet=(f,pid)=>{")
j = s.index("\n", i)
s = s[:i] + "const routeSet=(f,pid)=>{const k=known(pid);if(!DR[f.cls].ground){if(f.cls==='leviathan'||has(pid,'planetmove'))return k;return new Set([...k].filter(x=>x===f.node||G.nodes[x].planet==null));}const g=groundSet(f.node);return new Set([...g].filter(x=>k.has(x)||P(pid).ai));};" + s[j:]
# AI barrack: only drones it can make
rep("const order=extra.concat(shuffle(['frigate','bomber','interceptor'])", "const order=extra.filter(c=>canMake(pid,c)).concat(shuffle(['frigate','bomber','interceptor'])")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
