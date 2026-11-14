# DmC: Devil May Cry — Native Desktop Trainer & Cheat Engine Table

[![Platform](https://img.shields.io/badge/Platform-Windows%20(Win32%20%2F%20x64)-blue)](#requirements)
[![Python](https://img.shields.io/badge/Python-3.8%2B%20(Zero%20Dependencies)-3776AB)](#quick-start)
[![UI](https://img.shields.io/badge/UI-WPF%20%2F%20C%23%20(.NET%204.x)-512BD4)](#quick-start)
[![Engine](https://img.shields.io/badge/Unreal%20Engine-3.x%20(v1.0.8916.2)-lightgrey)](#how-it-works)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A high-performance standalone **Windows desktop trainer** (native C# WPF GUI + pure Python stdlib memory engine) and companion **Cheat Engine 7.x table** for **DmC: Devil May Cry** (`DMC-DevilMayCry.exe` v1.0.8916.2 / Steam Win32), **created using AI**. 

Built using ASLR-safe **dynamic AOB scanning** and live **Unreal Engine 3 reflection (`GNames`, `GObjects`, `GEngine`, `NTGameStatsManager`)** — supporting both **Dante** and **Vergil (Vergil's Downfall)** with zero external pip dependencies and zero browser footprint.

> **Note:** This trainer, memory reflection engine, WPF desktop interface, and Cheat Engine table were researched, developed, and optimized using AI.

---

## Repository Contents

| File | Description |
| :--- | :--- |
| [`DmC_Trainer.exe`](DmC_Trainer.exe) | Compiled native Windows desktop trainer application (WPF / .NET Framework 4.x) with custom dark UI, sliders, and hotkey modal rebinding. |
| [`launcher.cs`](launcher.cs) | C# WPF application entry point, XAML dark templates, JSON-Lines stdio IPC manager, and global keyboard hook. |
| [`TrainerCatalog.cs`](TrainerCatalog.cs) | Declarative definitions of all 45+ cheats, groups, categories, icons, and hotkeys. |
| [`trainer_backend.py`](trainer_backend.py) | Pure Python 3 + Win32 `ctypes` memory engine, UE3 reflection resolver, `NTGameStatsManager` hash resolver, and IPC server. |
| [`Launch_Trainer.bat`](Launch_Trainer.bat) | Simple Windows batch launcher for `DmC_Trainer.exe`. |
| [`DMC-DevilMayCry.CT`](DMC-DevilMayCry.CT) | Cheat Engine 7.x XML cheat table with automated Lua UE3 reflection resolver and standalone Auto-Assembler scripts. |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history, performance optimizations, and technical notes. |
| [`LICENSE`](LICENSE) | MIT License. |

---

## Features

### 1. Player & Health
- **Unlimited Health & God Mode:** Lock Dante or Vergil's health at maximum or enable UE3 native `IgnoreAllDamage` flag.
- **Unlimited Devil Trigger:** Continuous maximum Devil Trigger meter.
- **DT Never Ends Outside Combat:** Preserves DT gauge between battles.
- **Unlimited Overdrive:** Keeps Overdrive gauge permanently topped up.
- **Instant Actions:** One-click Instant Heal, Instant Max DT, and Max Health / DT upgrades.

### 2. Combat, Style & Scoring
- **Fast Kill / One-Hit Kill:** Instant elimination of any targeted or attacked hostile entity.
- **Damage Multiplier Slider (`1.0x` – `50.0x`):** Scalable melee, ranged, and aerial damage output.
- **Always Demon Evade Buff:** Lock demon evade damage amplification active with custom multiplier.
- **SSS Style Rank Lock & Freeze Decay:** Locks style rating to SSS (`9999`) and disables grade decay timers.
- **Style Points Multiplier Slider (`1.0x` – `25.0x`):** Accelerate mission rating gains.
- **Mission Score & Stats:** Instant max mission score (`9,999,999`) and zero damage taken counters.
- **Unlimited Kablooey Darts:** Continuous `99` active darts without reloading.
- **Drop Active Enemies to 1 HP:** Set all live hostile pawns in the current encounter to 1 HP.

### 3. Inventory, Keys & Economy
- **Never Decrease Items & Orbs:** Byte-safe opcode patch preventing inventory consumption (with conflict detection if another trainer is hooked).
- **Infinite Keys:** Unlimited Copper, Argent, Gold, and Ivory Keys.
- **Infinite Consumables:** Unlimited Small/Large Vital Stars, Small/Large DT Stars, and Gold Orbs.
- **Stat Upgrades:** Health Cross Fragments, DT Cross Fragments, and Upgrade Points.
- **Quick Grants:** One-click `+50,000 Red Orbs`, `+10 Upgrade Points`, and Max All Keys & Stars.

### 4. Movement, Physics & World
- **Infinite Air Jumps:** Unlimited double-jumps without touching the ground.
- **Infinite Air Evades & Angel Glide:** Endless aerial dashing and gliding mobility.
- **Speed Multiplier Sliders:** Independent Player Movement Speed (`0.5x` – `5.0x`) and Game World Speed (`0.1x` – `5.0x`).
- **Jump Height & Gravity:** Customizable jump velocity and gravity Z axis (including Zero-G Hover).

### 5. AI, Mission Timers & Progression
- **Freeze Timers:** Stop main mission clock and secret challenge mission countdowns.
- **Freeze Enemies & Suppress Attacks:** Suspend enemy AI processing (`bSuspendAI`) or revoke combat action tokens.
- **World Freeze (`bPlayersOnly`):** Freeze all environment and enemy physics while the player moves freely.
- **Difficulty & Attack Unlocks:** Instantly unlock Son of Sparda, Dante Must Die, and Hell and Hell difficulty modes, and enable all combat skills.

### 6. 3-Slot Position Teleportation
- Save and restore coordinates across 3 independent memory slots (`F5`–`F7` Save, `F8`–`F10` Teleport).
- Undo last teleport (`F11`) and vertical Z-axis nudges (+200 / -200 units).

---

## Quick Start

### Requirements
- **OS:** Windows 10 / 11 (64-bit or 32-bit).
- **Game Version:** Steam Win32 release of *DmC: Devil May Cry* (`DMC-DevilMayCry.exe` v1.0.8916.2).
- **Runtime:** 
  - Standard Windows `.NET Framework 4.5+` (pre-installed on Windows 10/11).
  - Python 3.8+ (64-bit or 32-bit, included in PATH). **Zero third-party pip packages required.**

### Launching the Trainer
1. Start **DmC: Devil May Cry** via Steam.
2. Double-click [`Launch_Trainer.bat`](Launch_Trainer.bat) (or run [`DmC_Trainer.exe`](DmC_Trainer.exe)).
3. Look at the status header: once the game is detected, it will display:
   ```
   Attached · PID [xxxx] · Dante (or Vergil)
   ```
4. Toggle cheats using the `[Off | On]` buttons or global hotkeys. Click any hotkey pill in the UI to rebind it interactively.
5. Press `Home` at any time to instantly deactivate all active cheats.

### Using the Cheat Engine Table
1. Open [`DMC-DevilMayCry.CT`](DMC-DevilMayCry.CT) in [Cheat Engine 7.x](https://www.cheatengine.org/).
2. Attach Cheat Engine to `DMC-DevilMayCry.exe`.
3. Enable **`[Enable] Resolve UE3 Pointers & Stats (AOB + Reflection)`** at the top of the table.
4. The embedded Lua engine will automatically perform AOB pattern scans, traverse `GNames`/`GObjects`/`GEngine`, and map all player pointers and stats.

---

## How It Works

```
┌────────────────────────────────┐       stdio JSON-Lines IPC       ┌──────────────────────────────┐
│  DmC_Trainer.exe (C# WPF UI)   │ ◄──────────────────────────────► │  trainer_backend.py (Engine) │
│  - Custom dark XAML styles     │                                  │  - Toolhelp32 process lookup │
│  - Sliders & hotkey rebinding  │                                  │  - UE3 reflection traversal  │
│  - Win32 GetAsyncKeyState hook │                                  │  - NTGameStatsManager TMap   │
└────────────────────────────────┘                                  └──────────────┬───────────────┘
                                                                                   │
                                                                 ReadProcessMemory │ WriteProcessMemory
                                                                                   ▼
                                                                    ┌──────────────────────────────┐
                                                                    │   DMC-DevilMayCry.exe        │
                                                                    │   - GNames / GObjects        │
                                                                    │   - GEngine / WorldInfo      │
                                                                    │   - NTPlayerPawn (Health/DT) │
                                                                    │   - Item decrement opcode    │
                                                                    └──────────────────────────────┘
```

- **Dynamic AOB Scanning:** Scans the game's decrypted `.text` segment in memory at runtime to locate `GNames`, `GObjects`, `GEngine`, and `NTGameStatsManager`. No hardcoded static offsets are used, ensuring compatibility across ASLR variations.
- **Unreal Engine 3 Reflection:** Traverses native UE3 internal structures (`UObject`, `UClass`, `FField`, `FProperty`) to dynamically locate player pawns, controllers, and components across both Dante and Vergil campaigns.
- **Clean Instruction Restoration:** The backend records all original instructions prior to patching and automatically restores native machine code upon cheat deactivation, trainer detachment, or exit.

---

## Troubleshooting

- **Trainer shows "Waiting for game...":** Make sure `DMC-DevilMayCry.exe` is running. If you run the game or Steam as Administrator, run the trainer as Administrator as well so Windows permissions allow memory access.
- **AOB Match Failure / Hook Conflict:** If you run another trainer (such as FLiNG) simultaneously, our memory engine automatically detects foreign hooks at the opcode site and safely yields native patching to prevent crashes.
- **Hotkeys not responding:** Ensure the trainer is running. The global hook listens for keys via Win32 `GetAsyncKeyState`. You can click any hotkey badge in the UI to assign a different key.

---

## AI-Assisted Creation Disclosure

This project was created with **AI assistance** (including AOB signature reverse-engineering, UE3 memory reflection design, the pure-Python Win32 engine, the WPF C# desktop interface, and the Cheat Engine XML/Lua table) and tested live against the Steam build of `DMC-DevilMayCry.exe`. All source files are plain-text, un-obfuscated, and open-source so anyone can inspect and audit every line of code and memory operation.

---

## Disclaimer

- Provided strictly for **offline, single-player, personal, and educational use**.
- **Contains no proprietary game assets, executables, or DRM bypasses.**
- Always **back up your game save files** (`%USERPROFILE%\Documents\My Games\DmC Devil May Cry\`) before editing currencies or progression stats.
- Not affiliated with or endorsed by Capcom, Ninja Theory, or Steam. Use at your own risk.
