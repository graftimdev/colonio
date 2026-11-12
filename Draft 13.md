# What's new in Colonio 0.2.3 (Draft 13)

## New stations
- **Motion turret** (Turrets, after the chain turret): a shield with **M**, 3 health, no damage.
  - Every battle round it sends the first enemy drone in the damage order back to the tile it came from, with a blink and a zip.
  - If that tile has enemies too, the drone stays and takes 1 damage instead.
  - Leviathans are immune.
- **Anti-healing dome** (Turrets, after the X-ray turret): enemy drones that end their move under it can't be healed for 5 turns. A crossed-out green plus marks them.
  - On the map it looks like the electric barrier's field, but green. On a tile that also has a barrier, the dome shows as a smaller green ring inside it.
  - Its icon is a broken heart. It uses 1 energy a turn while on, and you can switch it off.

## Drones
- **Health per drone:** each drone in a squadron now has its own health. Damage still hits one drone at a time, regular drones before upgraded ones.
- **Engineers:**
  - Outside battle, each engineer repairs 0.5 health on every drone and every turret on its tile, every turn.
  - In battle, each engineer gives 1 health per battle to your front drones. Health that isn't needed in one round is kept for the next.
  - Upgraded engineers rebuild a destroyed station: 6 of them in 1 turn, fewer take longer (1 engineer: 6 turns).
- **Upgraded and regular drones can share a squadron:**
  - The "U" letter is gone. The icon fills from the bottom by how many drones are upgraded.
  - A mixed squadron moves at its slowest drone's speed. When upgraded bombers or interceptors join regular ones, a pop-up offers **Split** or **Close**, with "Don't ask again" for this session.
  - Each upgrade bonus counts for each upgraded drone: frigate shields, siege barrier breaks, boomerang damage, stomper hits on their own tile, and tank energy saving.
  - **Settings → General → Split upgraded drones automatically** keeps them apart the old way. It's off by default.
- **Siege:** 0.5 damage to drones (was 1) and 4 to turrets and cores (was 5).
- **Ballista:** only one per squadron.
- **Settled charger:**
  - It becomes a building in an extra 5th spot next to the tile's stations, with up to 10 docking lights and a number from 11 docked drones on.
  - Anyone can open it and see the docked drones and their health, but not their energy.
  - When a battle reaches its tile, every docked drone undocks and fights.
  - Docked drones count toward the tile's drone limit.
  - A leviathan can't share a tile with a settled charger.
- **X-ray turret:** it also sees enemy spies 1 hop away.

## Sounds
- **Catapults:** a hollow pop for each rocket that leaves, and a crack with a short rumble when it lands.
- **Workers:** a short falling blip and a small spark when a worker you can see is lost.

## Menus
- **Settings:**
  - Every on/off setting uses the same sliding switch. Descriptions open from a **?** next to each name.
  - The tabs are all the same width.
  - A new **Wiki** tab has two pages:
    - **Damage order:** shows who gets hit first, with every unit's icon.
    - **Hidden rules:** explains the rules that are hard to find, such as catapult targets, engineers, death turrets and cores, barriers, bombers, siege drones, chargers and the new stations.
- **Resource bar:** a small arrow under it opens and closes the game menu, like pressing the bar.
- **Trade:** in the Empire menu, the resource buttons line up with the Trade button.
- **Messages:** small messages appear right above **End turn** instead of on top of it.
- The electric barrier's on/off is a switch too.
- **Name change:** Xenocrystal is now called **crystals** everywhere.

## Tutorials
- **Settings** and **Report** can be opened at any time during a tutorial.
- **Engineer lesson:** 6 interceptors at 1 health each are healed to full by 6 engineers in one turn.
- **Ballista lesson:** the line has one more enemy tile, so the bolt hits 5 times and the 5th hit lands on the core.
