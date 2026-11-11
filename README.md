# DmC: Devil May Cry — Ultimate Trainer & Cheat Table

Built for **DmC: Devil May Cry (`DMC-DevilMayCry.exe` v1.0.8916.2 / Steam Win32)** using ASLR-safe **AOB scanning** and live **Unreal Engine 3 reflection (`GNames`, `GObjects`, `GEngine`, `NTGameStatsManager`)**. Works for both **Dante** and **Vergil (Vergil's Downfall)**.

## Files Included

- `DmC_Trainer.exe` — Native no-console Windows launcher for the dark-themed desktop trainer UI.
- `app.py` + `web/` — Local Flask bridge & modern responsive WeMod-style dark UI (also supports `--no-browser` and `--port`).
- `trainer_backend.py` — Win32 process memory engine, UE3 reflection resolver, `NTGameStatsManager` TMap stat resolver, 45+ live cheats, hotkeys, presets, and 3-slot teleportation.
- `DMC-DevilMayCry.CT` — Full **Cheat Engine 7.x** XML cheat table with auto-updating Lua UE3 reflection resolver (`GNames` / `GObjects` / `GEngine` / `StatsMap`) and standalone Auto-Assembler AOB scripts.
- `Launch_Trainer.bat` — Alternative batch launcher.

## Quick Start

1. Launch **DmC: Devil May Cry**.
2. Double-click **`DmC_Trainer.exe`** (or run `python app.py`).
3. Wait for the status bar in the top-left to show **`Attached · PID ... · Dante/Vergil`**.
4. Toggle mods in the UI or via global hotkeys (click any hotkey pill in the UI to rebind; press `Home` to disable all active mods).

## Feature Highlights

- **Player**: Unlimited Health, God Mode (`IgnoreAllDamage`), Unlimited Devil Trigger, DT Never Ends Outside Combat, Unlimited Overdrive, Instant Heal / Refill DT / Extend Max Health & Max DT.
- **Combat & Style**: Fast Kill / One-Hit Kill, Damage Multiplier slider (`1x–50x`), Always Demon Evade Buff + multiplier, Force Dismember Kill, SSS Style Rank Lock, No Style Decay, Style Points Multiplier (`1x–25x`), Max Mission Score (`9,999,999`), Zero Damage Taken Stat, Unlimited Kablooey Darts (`99`), Drop All Active Enemies to 1 HP.
- **Inventory & Keys**: Never Decrease Items & Orbs (AOB hook with safe yield if another trainer owns the hook), Unlimited Red Orbs, Gold Orbs, Copper/Argent/Gold/Ivory Keys, Small/Large Vital Stars, Small/Large DT Stars, Health & DT Cross Fragments, Unlimited Upgrade Points, Quick `+50k Red Orbs` / `+10 Upgrade Points` / Max Keys & Stars.
- **Movement & Physics**: Infinite Air Jumps, Infinite Air Evades / Angel Glide, Player Speed Multiplier, Game World Speed (Turbo / Slomo), Jump Height Multiplier, Custom Gravity Z, Zero-Gravity Float / Hover.
- **World, AI & Timers**: Freeze Mission Timer, Freeze Secret Mission Timer, Freeze Enemies AI (`bSuspendAI`), Enemies Don't Attack (No Combat Tokens), Freeze World (`bPlayersOnly`), Reset Mission Timer & Damage.
- **Progression, Camera & Teleport**: Custom Camera FOV, Player Draw Scale, Hide HUD, Unlock All Attacks Flag, Unlock All Post-Story Difficulties (SoS / DMD / HoH), 3-Slot Position Save / Teleport / Undo Teleport + vertical Z nudges.

## Cheat Engine Table (`DMC-DevilMayCry.CT`)

1. Open `DMC-DevilMayCry.CT` in Cheat Engine 7.x and attach to `DMC-DevilMayCry.exe`.
2. Enable **`[Enable] Resolve UE3 Pointers & Stats (AOB + Reflection)`** at the top of the table (runs Lua AOB scan + UE3 reflection to populate `dmc_Pawn`, `dmc_Profile`, `dmc_GameInfo`, `dmc_StyleSystem`, `dmc_TriggerComp`, `dmc_CombatData`, `dmc_CombatBehav`, `dmc_WorldInfo`, `dmc_AICoord`, `dmc_SecretMgr`, and `dmc_Stat_*` addresses).
3. Use any pointer entry or standalone Auto-Assembler AOB scripts (`One-Hit Kill / Enemy 1 HP [IsDead AOB]`, `Never Decrease Items [Counter_Decrement AOB]`).
