"""Makes the zip you upload to itch.io.

Run:  python tools/package_itch.py wss://YOUR-SERVER.onrender.com
The address is written into the zipped copy of the game, so itch.io players connect to your server.
"""
import os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(ROOT, 'client')
DIST = os.path.join(ROOT, 'dist')

if len(sys.argv) != 2 or not re.fullmatch(r'wss://[A-Za-z0-9.-]+(:\d+)?(/[\w./-]*)?', sys.argv[1]):
    sys.exit('Usage: python tools/package_itch.py wss://your-server-address\n(the address must start with wss://)')
server = sys.argv[1]

html = open(os.path.join(CLIENT, 'index.html'), encoding='utf-8').read()
html, n = re.subn(r"const DEFAULT_SERVER='[^']*';", f"const DEFAULT_SERVER='{server}';", html)
if n != 1:
    sys.exit('Could not find DEFAULT_SERVER in client/index.html. Run python tools/build.py first.')

os.makedirs(DIST, exist_ok=True)
out = os.path.join(DIST, 'colonio-itch.zip')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('index.html', html)
    for f in ('astrosong.mp3', 'gamesong.mp3'):
        z.write(os.path.join(CLIENT, f), f)
print(f'Wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB), players will connect to {server}')
