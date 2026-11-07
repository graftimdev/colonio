#!/bin/sh
# Syntax-check the game's script with Node: python extracts the <script> body, node --check parses it.
cd "$(dirname "$0")/.."
NODE="${NODE:-node}"
python -I -c "
s=open('client/index.html',encoding='utf-8').read()
open('.check.js','w',encoding='utf-8').write(s[s.index('<script>')+8:s.rindex('</script>')])
" && "$NODE" --check .check.js && echo "syntax ok"; rm -f .check.js
