# Jopium online (ver. 0.1.9, Draft 9)

Jopium with real online PvP. The **Play** button on the main menu now hosts and joins lobbies on a game server.
People play each other, and empty seats can be filled with the AI.

## What's in this folder

| Path | What it is |
|---|---|
| `client/index.html` | The game. Since Draft 9 this file is the source: edit it directly |
| `client/*.mp3` | Menu and match music |
| `server/server.js` | The game server: lobbies, and passing each turn's orders between players |
| `package.json` | Tells Node.js how to start the server (`npm start`) |
| `render.yaml` | Settings for hosting the server on Render |
| `tools/d9_*.py` | The Draft 9 changes, step by step (already applied; kept as a record) |
| `tools/check.sh` | Checks the game's code for syntax errors (needs Node.js) |
| `tools/testbot.js` | A random-orders bot for testing that online games stay in sync |
| `legacy/` | The 0.1.8 game, and the Draft 8 build script that made it from Draft 7 |
| `tools/package_itch.py` | Makes the zip for itch.io |
| `original-0.1.7.html` | Your Draft 7 game, untouched |

## How online play works

Jopium uses **lockstep** networking, which fits its simultaneous turns:

1. At the start of a match the server sends everyone the same random **seed**, so every player builds the same map.
2. During a turn, each player's actions (move, build, research, and so on) are recorded as small **orders**.
3. Pressing **End turn** sends your orders to the server. The button shows "Waiting · 1/2" until everyone is done.
4. The server sends everyone all the orders. Each player's screen rewinds to the start of the turn, replays every player's orders in seat order, and runs the normal turn resolution, including the AI seats.
5. Each screen sends back a fingerprint of the result. If two screens ever disagree, everyone gets a warning and the server log notes the turn.

The server is small and cheap to run because it never runs the game itself.

- **Leaving or disconnecting:** the AI takes over that empire at the end of the turn, and the report says so.
- **Turn timer:** your turn ends by itself when your timer runs out. If a player's game freezes, the server ends the turn 15 seconds after the timer.
- **Resign:** your core falls and the match ends for you. You can keep watching while the others play.

**Trade-off to know about:** every player's browser holds the whole match, including what's hidden by fog of war. Someone who knows how to use the browser's developer tools could peek at it. That's fine for playing with friends. Ranked play with Elo would need the server to run the game itself (a bigger change, but it can reuse the same orders).

## 1. Try it on your own PC

You need **Node.js** (the LTS version from https://nodejs.org).

In this folder, run:

```
npm install
npm start
```

Open http://localhost:8080 in two browser windows. In one, choose Play → Host lobby. In the other, choose Play → Join lobby.

To play with someone on the same Wi-Fi, they open `http://YOUR-PC-IP:8080?server=ws://YOUR-PC-IP:8080` (find your IP with `ipconfig`).

## 2. Put the server online (Render, free tier)

1. Make a free GitHub account and upload this whole folder as a new repository. `node_modules` and `dist` aren't needed.
2. Make a free account at https://render.com and choose **New → Blueprint**. Pick your repository; Render reads `render.yaml` and creates the service.
3. When it finishes, Render shows your address, for example `https://jopium-server.onrender.com`. Open it: the game loads, and online play already works there.
4. Your server address for the game is the same with `wss://` instead of `https://`, for example `wss://jopium-server.onrender.com`.

On the free plan the server goes to sleep after a while with no players, and the first visitor waits about a minute while it wakes up. A paid plan (a few dollars a month) stays awake. Fly.io and Railway also work: any host that can run `npm start` and allows WebSockets.

## 3. Upload to itch.io

1. Make the zip, using your server address from step 2:
   ```
   python tools/package_itch.py wss://jopium-server.onrender.com
   ```
   This creates `dist/jopium-itch.zip`.
2. On itch.io: **Upload new project**, set **Kind of project** to **HTML**, and upload the zip.
3. Tick **This file will be played in the browser**.
4. Set the viewport to 1280 × 720, and tick **Fullscreen button** and **Mobile friendly**.
5. Save, then open the page in two different browsers (or on two devices) and host and join a lobby to test.

## Changing the game

From Draft 9 on, `client/index.html` is the game's source: edit it directly. Your git history in this folder has every step.

Rules for new features, so online games stay in sync:

- **Every change a player makes must go through `order({...})`**, never by editing the game state directly from a button. Add a `case` for it in `applyCmd`.
- **Use `rnd()`, never `Math.random()`**, for anything that affects the match. `Math.random()` is fine for looks only: stars, sounds, animations.
- **Use `ME` for "the player at this screen"**, never `0`.
- **Add new match state to `stateHash()`** so a desync in it would be caught.
- **Bump `GAME_VERSION`** for every release. The server only lets players with the same version into the same lobby.

To test sync: start a 2-player online match in two browser tabs, paste `tools/testbot.js` into each tab's developer console, wait, then compare `HS` between the tabs (the server log also reports any desync).

## Tested

Draft 9 (ver. 0.1.9), on one PC with the local server:

- Online sync with the test bot: 142 turns (2 players and 2 AI), 1,390 turns and 2,000+ turns (2 players, all techs researched). Identical fingerprints every turn, no desync.
- AI against an idle player, five maps each: Hard wins by turns 27 to 82, Normal by 53 to 200, Easy by 106 to 216. No errors in more than 3,000 AI turns.
- In the browser: new icons, tech tree, Barrack menu, launch list, docking, battle preview, boomerang rescue and free hop, squadrons with press-and-hold, traced paths, leviathan building, full-screen lobby.

Not tested yet: two different computers over the internet, the hosted server on Render, and touch screens (press-and-hold and tracing were tested with a mouse).
