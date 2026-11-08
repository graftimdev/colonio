# What's new in Jopium 0.1.10 (Draft 10)

## Accounts, Elo and the leaderboard
- Sign in with Google. You stay signed in on your device, and your profile, nickname and Elo carry over to every new version.
- New players get a nickname like `player4821`. Change it any time in **Profile**. Every nickname is unique, and capitals count, so "Tima" and "tima" are different names.
- Upload your own profile picture.
- Elo stays hidden until your first online game ("Play 1 game"). Everyone starts at 1000.
- Online games only: the winner gets +20 Elo and everyone else −20. Leaving or resigning counts as a loss. If everyone else leaves, the last player wins.
- At the end of an online match your Elo rolls from the old number to the new one.
- The **Leaderboard** shows the top 100. When two players have the same Elo, whoever reached it first ranks higher. If you're lower than 100th, you see your own place underneath.

## Tutorial
- New players start with a guided tutorial, in English or Russian. It covers moving, claiming, mining, research, building a Barrack and drones, making a fleet, attacking, linking a planet, mining jopium and flying a leviathan into an enemy core.
- During the tutorial, **Resign** becomes **Menu**, so you can skip it. **Settings → Replay tutorial** brings it back.

## Online lobbies
- A full lobby no longer starts by itself: the host presses **Start**.
- The host can start with fewer players than planned, after confirming. The empty seats stay empty: online matches never add AI players.
- A new waiting animation: a rocket climbing through the stars, tilting and swaying side to side.

## Diplomacy
- A new tech after **Better rates**.
- Send a peace treaty from **Empire → Rivals**. A worker at your core prepares it, which takes one turn. One worker can prepare several treaties at once.
- You can only send treaties to rivals you've met (seen their land or drones). Everyone else shows as "unknown rival".
- At peace, you and your partner:
  - can't attack each other;
  - see each other's cores and spies;
  - can fly through each other's land.
- Where your networks touch, they link (the dotted line is half your colour, half theirs), so your squadrons there stay powered.
- Either player can break the peace with a worker at their core. Whoever breaks it loses every squadron standing on the other player's land.
- The computer always declines peace.

## Underdog gifts
- In matches with 3 or more players, the player who is falling far behind sometimes gets supply drops on their own empty asteroids and planet sections.
- Gifts glow yellow. Only players who can see that tile see them.
- The first to reach a gift takes it:
  - an upgraded frigate, siege, boomerang or catapult on an asteroid, or a tank, stomper or ballista on a planet section;
  - plus 2 of each resource.
- Gifts disappear after 5 turns.
- **Conquest:** a leader 50 jopium ahead of second place mines less until the others catch up.

## Units and combat
- **Ballista, rebuilt:** 2 health, 2 damage, 1 hop. It fires a lightning bolt at a neighbouring tile, paid for in crystals:
  - Charge up to 5 crystals. The bolt jumps from enemy tile to enemy tile, doubling its damage each time: 0.5, 1, 2, 4, 8.
  - It never hits the same tile twice, and it picks the route that hits the most tiles.
  - Each extra ballista in the squadron can add +0.5 to the last hit for 1 more crystal.
  - The bolt is blue for you and orange for enemies.
- Catapults and ballistas always fire, even at an empty tile.
- Tiles that get hit pulse red twice at the start of the next turn. A tile you attacked and won pulses blue.
- War drones fight at full strength on planets. Their only drawback there is double energy use.
- Rovers can't be upgraded. They can still dock in upgrade stations to recharge.

## Economy and map
- **Stargold is now jopium (Жопиум).**
- **Crystal trade:** 2 of a resource buys 1 crystal, and 2 crystals buy 1 resource. Better rates doesn't change this.
- **Boreholes:** a worker sits at the borehole as its operator, using 1 energy a turn. The borehole menu has an **Assign** list.
- **Maps:**
  - Crystal asteroids are never next to each other.
  - Cores never touch a planet.
  - Every core starts next to an iron, copper or silicon asteroid.
- The **Rover station** (formerly rover barrack) needs both Barrack and Planet movement.

## Interface
- **Names swapped:** a group of one drone type is now a **squadron**, and a group of squadrons is a **fleet**.
- **Research** is assigned only in the tech tree, from workers at your core. Idle workers are listed first. Press **Stop** to take a worker off research.
- **Unclaimed tiles** have a **Move to it** list of your workers with their distance.
- **Tech descriptions** name what they unlock. Tap a name for an info card with its picture and stats. Utility drones has 3 pages.
- **Settings** has **General** and **Keyboard** tabs. Every key can be changed or reset.
- **Keyboard controls:** see the README.
- **Icons and display:**
  - The Empire button is a crown.
  - Asteroid names show their resource icon, and trade uses icons.
  - Stations on planets are see-through.
  - Workers keep a neat ring however many share a tile.
  - The leviathan stands clear of the workers.
  - A leviathan under construction has no pilot. A random builder becomes the pilot, drawn at normal worker size.
- **After winning,** you can look around the whole map.

## Computer opponents
- They no longer freeze or fly back and forth between the same two tiles.
- They gather their squadrons into one army, attack together and finish off weakened rivals.
- They take planets, reconnect cut-off land and keep their economy going.
