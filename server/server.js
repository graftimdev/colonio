// Jopium game server.
// It hosts lobbies and relays each turn's orders between players. It does not run the game itself:
// every player's browser runs the same match from the same seed and the same orders (lockstep).
// It also serves the game files from ../client, so one deployment is both the website and the server.
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { WebSocketServer } = require('ws');

const PORT = +process.env.PORT || 8080;
const CLIENT_DIR = path.join(__dirname, '..', 'client');
const GRACE_S = 15;            // extra seconds after the turn timer before the server ends a turn for slow players
const MAX_ORDERS = 400;        // per player per turn
const PIC_OK = /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/;
const TYPES = { '.html': 'text/html; charset=utf-8', '.mp3': 'audio/mpeg', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.ico': 'image/x-icon' };

// ---------------------------------------------------------------- website
const server = http.createServer((req, res) => {
  const url = decodeURIComponent((req.url || '/').split('?')[0]);
  if (url === '/health') { res.writeHead(200, { 'content-type': 'text/plain' }); return res.end('ok'); }
  const file = path.normalize(path.join(CLIENT_DIR, url === '/' ? 'index.html' : url));
  if (!file.startsWith(CLIENT_DIR + path.sep)) { res.writeHead(403); return res.end(); }
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream', 'content-length': st.size, 'cache-control': 'no-cache' });
    fs.createReadStream(file).pipe(res);
  });
});

// ---------------------------------------------------------------- lobbies and matches
const rooms = new Map();   // code -> room
const send = (c, m) => { if (c && c.ws.readyState === 1) c.ws.send(JSON.stringify(m)); };
const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, max);
const pick = (v, list, def) => (list.includes(v) ? v : def);

function newCode() {
  const A = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
  for (;;) {
    let c = ''; for (let i = 0; i < 4; i++) c += A[crypto.randomInt(A.length)];
    if (!rooms.has(c)) return c;
  }
}
function roomInfo(r, forClient) {
  return { code: r.code, name: r.name, mode: r.mode, per: r.per, timer: r.timer, need: r.need, host: r.players[0] === forClient,
    players: r.players.map(p => ({ name: p.name, pic: p.pic })) };
}
function sendLobby(r) { for (const p of r.players) send(p, { t: 'lobby', room: roomInfo(r, p) }); }
function openLobbies(ver) {
  return [...rooms.values()].filter(r => r.state === 'lobby' && r.ver === ver && r.players.length < r.need)
    .map(r => ({ code: r.code, name: r.name, mode: r.mode, timer: r.timer, per: r.per, players: r.players.length, need: r.need }));
}

function leaveRoom(c) {
  const r = c.room; if (!r) return;
  c.room = null; const seat = c.seat; c.seat = null;
  if (r.state === 'lobby') {
    r.players = r.players.filter(p => p !== c);
    if (!r.players.length) { rooms.delete(r.code); return; }
    sendLobby(r);   // the next player in line becomes the host
    return;
  }
  // in a match: the AI takes over this seat from the next turn on
  r.active.delete(seat); r.ended.delete(seat); r.dropped.push(seat);
  if (!r.active.size) { clearTimeout(r.deadline); rooms.delete(r.code); return; }
  progress(r); maybeFinish(r);
}

function startMatch(r) {
  r.state = 'play';
  const seed = crypto.randomInt(1, 2 ** 32 - 1);
  const seats = [];
  for (let i = 0; i < r.need; i++) seats.push(r.players[i] ? { name: r.players[i].name, ai: false } : { name: null, ai: true });
  r.players.forEach((p, i) => { p.seat = i; });
  r.active = new Set(r.players.map((p, i) => i));
  r.turn = 1; r.cmds = {}; r.ended = new Set(); r.dropped = []; r.hashes = new Map();
  for (const p of r.players) send(p, { t: 'start', code: r.code, seed, seats, you: p.seat, opts: { mode: r.mode, per: r.per, timer: r.timer } });
  armDeadline(r);
  console.log(`room ${r.code}: match started with ${r.players.length} players and ${r.need - r.players.length} AI`);
}
function armDeadline(r) {
  clearTimeout(r.deadline);
  if (r.timer) r.deadline = setTimeout(() => { for (const s of r.active) r.ended.add(s); maybeFinish(r); }, (r.timer + GRACE_S) * 1000);
}
function progress(r) {
  const m = { t: 'progress', done: [...r.ended].filter(s => r.active.has(s)).length, need: r.active.size };
  for (const p of r.players) if (p.room === r) send(p, m);
}
function maybeFinish(r) {
  if (r.state !== 'play' || ![...r.active].every(s => r.ended.has(s))) return;
  const m = { t: 'turn', turn: r.turn, cmds: r.cmds, dropped: r.dropped };
  for (const p of r.players) if (p.room === r) send(p, m);
  r.turn++; r.cmds = {}; r.ended = new Set(); r.dropped = [];
  armDeadline(r);
}

// ---------------------------------------------------------------- messages
const wss = new WebSocketServer({ server, maxPayload: 256 * 1024 });
wss.on('connection', ws => {
  const c = { ws, name: 'Player', pic: '', ver: '', room: null, seat: null };
  ws.on('message', data => {
    let m; try { m = JSON.parse(data); } catch (e) { return; }
    if (!m || typeof m.t !== 'string') return;
    const who = w => { if (w && typeof w === 'object') { c.name = clean(w.name, 18) || 'Player'; c.pic = PIC_OK.test(w.pic || '') && w.pic.length < 60000 ? w.pic : ''; } };
    const r = c.room;
    switch (m.t) {
      case 'hello': who(m); c.ver = clean(m.ver, 20); break;
      case 'list': send(c, { t: 'lobbies', list: openLobbies(c.ver) }); break;
      case 'host': {
        who(m.who); leaveRoom(c);
        const nr = { code: newCode(), ver: c.ver, name: clean(m.name, 28) || `${c.name}'s lobby`, mode: pick(m.mode, ['warfare', 'conquest'], 'warfare'),
          per: Math.max(10, Math.min(30, Math.round(+m.per) || 20)), need: Math.max(2, Math.min(6, (Math.round(+m.opp) || 1) + 1)),
          timer: pick(+m.timer, [0, 30, 45, 60], 45), state: 'lobby', players: [c] };
        rooms.set(nr.code, nr); c.room = nr; sendLobby(nr);
        console.log(`room ${nr.code}: hosted by ${c.name} (${nr.need} seats)`);
        break;
      }
      case 'join': {
        who(m.who);
        const t = rooms.get(clean(m.code, 4).toUpperCase());
        if (!t || t.state !== 'lobby') return send(c, { t: 'error', msg: 'That lobby is not open any more.' });
        if (t.ver !== c.ver) return send(c, { t: 'error', msg: `That lobby runs a different version of Jopium (${t.ver}). Refresh the page to update.` });
        if (t === r) return;
        if (t.players.length >= t.need) return send(c, { t: 'error', msg: 'That lobby is full.' });
        leaveRoom(c); t.players.push(c); c.room = t; sendLobby(t);
        if (t.players.length === t.need) startMatch(t);
        break;
      }
      case 'leave': leaveRoom(c); break;
      case 'start': if (r && r.state === 'lobby' && r.players[0] === c && r.players.length >= 2) startMatch(r); break;
      case 'end': case 'resign': {
        if (!r || r.state !== 'play' || m.turn !== r.turn || !r.active.has(c.seat)) return;
        if (m.t === 'end') {
          if (r.ended.has(c.seat)) return;
          const list = Array.isArray(m.cmds) ? m.cmds.filter(x => x && typeof x === 'object' && typeof x.t === 'string').slice(0, MAX_ORDERS) : [];
          r.cmds[c.seat] = list;
        } else (r.cmds[c.seat] = r.cmds[c.seat] || []).push({ t: 'resign' });
        r.ended.add(c.seat); progress(r); maybeFinish(r);
        break;
      }
      case 'hash': {
        // every screen reports a fingerprint after each turn; different fingerprints mean the games drifted apart
        if (!r || r.state !== 'play' || typeof m.h !== 'string') return;
        const turn = +m.turn; if (!r.hashes.has(turn)) r.hashes.set(turn, new Map());
        const hs = r.hashes.get(turn); hs.set(c.seat, m.h.slice(0, 20));
        if (hs.size >= r.active.size) {
          if (new Set(hs.values()).size > 1) { console.warn(`room ${r.code}: desync on turn ${turn}`, [...hs]); for (const p of r.players) if (p.room === r) send(p, { t: 'desync', turn }); }
          r.hashes.delete(turn);
        }
        break;
      }
    }
  });
  ws.on('close', () => leaveRoom(c));
});
// drop connections that stopped answering, and keep hosting services from closing quiet ones
setInterval(() => {
  for (const ws of wss.clients) {
    if (ws.isAlive === false) { ws.terminate(); continue; }
    ws.isAlive = false; ws.ping();
  }
}, 30000);
wss.on('connection', ws => { ws.isAlive = true; ws.on('pong', () => { ws.isAlive = true; }); });

server.listen(PORT, () => console.log(`Jopium server on http://localhost:${PORT}`));
