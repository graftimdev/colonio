# Jopium: Draft 9 (ver. 0.1.9)

Draft 9 overrides anything older in the design document. It is built on the online version (0.1.8): every rule below works in online matches too.

## Menus and lobby
- "Закрыть игру" is now "Выйти" (English: "Quit").
- Main menu buttons light up when the mouse is over them.
- The profile chip shows only the picture, with Elo centred under it.
- Lobby (hosts and joiners alike): the whole screen is the starfield flying forward with the ship in the middle. The lobby name, "Searching for players" and the player grid sit at the bottom, with no box around them.
- "Barracks" is now "Barrack" in English (Russian was already singular).

## Map and lists
- Idle workers and fleets are listed first; units with orders go lower. This applies to "Your workers here", "Your fleets here", and the Empire menu's Workers and Fleets.
- A station that already has enough builders no longer appears on other workers' buttons (it stays on the workers building it).
- Moving units follow their route hop by hop and end exactly where their icon will sit next turn, instead of snapping there afterwards.
- No click bubble on stations.
- When researchers outnumber the worker-turns a tech still needs, the extra ones go idle at the end of the turn.
- Fleet icons sit closer to their tile.
- Resource names in menus became their bar icons. Report lines and the trade dropdowns keep the words.
- The electric barrier has its station icon on the map. The icon is clickable, and its menu switches the barrier on or off.
- The borehole has its own icon: a drill bit going into the ground.

## Unit icons
Interceptor and bomber are unchanged. Frigate: square. Siege: pentagon pointing down. Catapult: hexagon. Engineer: plus. Spy: cross (an X). Boomerang: chevron. Charger: 6-pointed star, slightly bigger. Ballista: triquetra (three rings). Tank: curved triangle. Stomper: crescent. Leviathan: a dragon coiled in a ring inside a big circle, with its worker pilot in the centre, 3.5× a fleet icon (28 px radius at normal zoom).

## Energy
- Start with 30/30 energy. The core makes 10 a turn, each generator 5, each captured core 10.
- From the core's grid, each turn: mining costs 1 per worker (0.5 with Efficient drills), building 1 per worker, and a switched-on barrier 1. Each launched war drone or rover costs 0.5; a war drone on a planet tile costs 1. Leviathans cost nothing. Stations that produce cost nothing.
- Turrets use 1 energy per battle they fight in. Without it they can't fire, but they still take damage.
- The death turret uses 5 energy and 10 Xenocrystal per shot and recharges for 5 turns.
- Every war drone and rover has a 5-energy battery, shown in its fleet menu next to its health.
- A fleet off your connected network is cut off. It then runs on its batteries. The fleet menu and the Empire menu say "cut off", and the report notes it when it happens. Spies never get cut off.
- When the grid can't pay for a fleet, that fleet's drones use their batteries instead. Barriers are paid first, then building, then mining.
- A drone with an empty battery can't move or fire. If any drone in a fleet is empty, the fleet is stuck. It gets a "Self-destruct" button ("Взорваться") that removes the empty drones, with no refund. Giving a stuck fleet an order explains why it can't move.
- Spare energy (more made than used this turn) tops up the batteries of drones on the grid, 0.5 at a time, at random.
- A cut-off cluster with spare energy charges the drones inside it first, then fills its energy storages.
- Docked drones use no energy and recharge 1 a turn in a barrack or upgrade station.
- Selecting one of your cut-off tiles makes the energy chip on the top bar show that cluster's energy and its gain or loss. The Empire menu still shows the core's.

## Resources
- The core holds 100 resources in total (all four together). Each storage adds 30 and a captured core adds 100. The top bar shows total / limit.

## Docking, barracks and upgrade stations
- A fleet's menu no longer has Dock. To dock, open a barrack, upgrade station or settled charger and press "Dock one" in the "Fleets nearby" list at the top. You can dock as many drones a turn as you like.
- Launch opens a list of every docked drone of that type, one per line, with its health and energy. You can launch them one at a time or all together.
- Upgrade stations look like barracks. Each type has Upgrade and Launch. An upgrade takes one turn, and any number can run in the same turn.
- Upgraded and regular drones never share a fleet. Together they still count toward the per-type limit on a tile.
- **Infinite queues** (Settings, off by default): barracks repeat the last drone you queued, and upgrade stations repeat the last upgrade, one a turn, whenever you can pay. A yellow ring marks stations that are working on something.

## Boreholes
- One per planet centre, and up to five in total. The first costs the base price, the second twice it, and so on up to five times.

## Tech tree: six routes (worker-turns in brackets)
1. Trade (2) → Crystal trade (4), Better rates (3)
2. Barrack (2) → Fleet size 10 (4), Utility drones (3) → Upgrade station (4)
3. Planet movement (3) → Boreholes (4), Rover barrack (4)
4. Turret (2) → Chain turret (3) → Electric barrier (4); X-ray turret (3) → Death turret (6)
5. Energy generator (2) → Energy storage (2), Efficient drills (3)
6. Deep scan (2) → Worker thrusters (3), Radio (3)

- You start with no barrack and no generator: research them first.
- The Barrack tech gives the interceptor, bomber, frigate, siege, catapult and boomerang. Utility drones adds the spy, engineer and charger.
- Fleet size 10 is the only fleet-size tech (6 → 10).
- Without Planet movement, war drones can't enter planet tiles. Workers can.
- Radio keeps every planet centre in sight for good.

## New units
**Charger**: 10 health, no damage, 1 hop a turn, 0.5 energy a turn. Costs 5 Iron, 2 Copper, 2 Silicon and 4 Xenocrystal. Takes 2 turns to build. One per tile, and a charger fleet is always 1 drone.
- "Settle" ("Сесть"): it stops using energy, charges itself 0.5 a turn, and lets drones dock into it from its menu. Docked drones get 0.5 a turn.
- A charger that has just settled must stay for at least a turn. It can't stand up while drones are docked in it, or while your leviathan is on its tile.
- Drones docked in a charger don't count toward the tile limit. They can't launch if that would break the limit. They are destroyed if enemy war drones are on the tile.
- Upgrade: while settled on an unclaimed tile, the charger links that tile into your network. The tile is drawn with a dotted ring, and workers can't build or mine there until they claim it. If the link connects to your core's network, its docked drones get 1 energy a turn.

**Boomerang**: 2 health, 1 damage, 1 hop a turn, 0.5 energy a turn. Costs 3 Iron, 2 Copper and 2 Xenocrystal.
- After winning a battle it flies back to the tile it attacked from.
- Next turn, if its route passes through the tile it attacked, that tile doesn't count as a hop. If that double hop ends in another battle and it wins, it returns to the first battle's tile.
- Rescue: once every boomerang on a side has fallen, each fallen boomerang saves one unit from that battle, in this order: charger, engineer, worker, spy. The unit goes to the enemy-free neighbouring tile closest to your core. With no such tile, nothing happens.
- Upgrade: +2 damage in a battle it entered through a free hop.

**Leviathan** (Warfare only): a giant war drone with 50 health, 20 damage and 1 hop a turn. It uses no energy and can have no upgrades. A player can have several.
- Build it on a planet centre from "Build a station here" for 100 stargold and 2 worker-turns. It takes no station slot. The worker who finishes it becomes its pilot and dies with it.
- It can't share a tile with your other fleets (a settled charger is the exception), and they can't share its tile. Drones docked on its tile can't launch.
- If the build would finish while your fleets are on, or heading to, that centre, End turn is blocked with an explanation. If the timer runs out instead, the build is cancelled, the 100 stargold comes back, and the worker goes idle.

## Battles
- Damage order, first hit first: Leviathan, Stomper, Tank, Ballista, Frigate, Catapult, Bomber, Interceptor, Siege, Chain turret, Turret, X-ray turret, Death turret, Boomerang, Spy, Engineer, Charger, Worker, Core. Siege bonus damage only lands on turrets and the core.
- Workers on a battle tile take part with 1 health each (no damage).
- War drones deal and take the same damage on planets (the old −1 is gone).
- Spies still stay out of battles (they are caught by enemy war drones or X-ray turrets, as before).
- **Battle preview**: ordering a fleet onto a tile with visible enemies (fleets, turrets, a core or workers) first shows "If you move to this asteroid / core / planet section / planet centre, you would win/lose". It lists what the winner would keep and what boomerangs would save. It is an estimate from what you can see, assuming nobody else moves. Press Move to go anyway.

## Planets in Warfare
- Warfare maps now have dwarf planets. Stargold mined there builds leviathans. In Conquest, 100 stargold still wins and there are no leviathans.

## Squadrons and paths
- **Select**: press and hold the map for a second without moving. A confirm sound plays and a wave spreads from your finger or cursor. Then drag a box over your fleets. With 2 or more selected, a pop-up offers to make a squadron.
- **Squadrons** are listed in the Empire menu above Fleets, and their fleets leave the Fleets list (they stay on the map as usual). Move sends all of them to one tile at the speed of the slowest fleet, and is refused if the tile can't hold them. See opens the list of its fleets with their own orders. Disband returns them to the Fleets list.
- **Traced paths**: after choosing Move, a click sends the unit by the shortest route. Instead, hold and drag through neighbouring tiles to trace your own route; dragging back onto the previous tile undoes a step. It works for workers, fleets and squadrons.

## Computer opponents
- They follow all the new rules: the new tech tree, energy and batteries, docking and upgrades, Planet movement, boreholes and leviathans. They also build the odd boomerang.
- Basic tactics:
  - Workers move away from enemy war fleets on or next to their tile when no escort or turret protects them.
  - Fleets fall back from a stronger enemy next door, and go home to recharge when their batteries run low.
  - They only attack tiles they expect to beat, and only targets they have the battery to reach.
  - They blow up empty drones so the rest of the fleet can move.
- Against a player who does nothing: Hard wins by turns 27 to 82, Normal by 53 to 200, Easy by 106 to 216 (five maps each).

## Decisions taken where the brief left room
- A fleet is stuck as soon as any one of its drones is empty. Self-destruct removes only the empty drones.
- "Dock one" takes the fleet's last drone. Each docked drone keeps its own share of the fleet's health and its own battery.
- In the preview, only the fleet you are moving is counted as moving.
- Workers saved by a boomerang go idle on the safe tile.
