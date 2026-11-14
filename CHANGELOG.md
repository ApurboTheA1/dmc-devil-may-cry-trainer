# Changelog

All notable changes to the **DmC: Devil May Cry Trainer & Cheat Table** project will be documented in this file.

## [1.0.0] — 2026-11-14

### Initial Release

#### Desktop Trainer UI (`DmC_Trainer.exe`, `launcher.cs`, `TrainerCatalog.cs`)
- **Native Windows Desktop App:** Built in C# WPF (`.NET Framework 4.x`) with custom modern dark theme, accent colors, custom scrollbars, and native DWM dark titlebar.
- **Zero Web / Browser Footprint:** Eliminated browser subprocesses, local Flask servers, and external web engines; communicates with the Python backend directly over hidden stdio pipes via JSON-Lines IPC.
- **Categorized Controls:** Segmented `[Off | On]` mod toggles, smooth continuous sliders (`1x–50x` Damage, `1x–25x` Style, Speed, FOV, Gravity, Scale), direct stat grant buttons, and 3-slot position save/load teleportation.
- **Interactive Hotkey System:** Global keyboard hooks with interactive modal rebinding (click any hotkey pill to rebind). `Home` hotkey instantly disables all active cheats.
- **Robust Process Lifecycle:** Auto-launches and manages the background memory worker, with graceful termination and cleanup on window close.

#### Memory Engine & UE3 Reflection (`trainer_backend.py`)
- **Pure Python 3 + Win32 ctypes:** Zero external pip dependencies (runs on standard Windows Python 3.8+).
- **Native Toolhelp32 Process Lookup:** Fast, lightweight process detection and module scanning (`DMC-DevilMayCry.exe`).
- **ASLR-Safe AOB Scanning:** Unique anchored byte signatures scanning the decrypted `.text` segment:
  - `GNames` (`0x00` null name sentinel)
  - `GObjects` (`GObjObjects` global array)
  - `GEngine` (`GameEngine` pointer)
  - `StatsMap` (`NTGameStatsManager::TMap` item/currency dictionary)
  - `CounterDec` (`0x00F2F11A` item decrement opcode with conflict-safe hook detection)
- **Dynamic UE3 Reflection:** Traverses native Unreal Engine 3 object structures in live memory to resolve `NTPlayerPawn`, `NTPlayerController`, `NTGameInfo`, `NTStyleSystem`, `NTDevilTriggerComponent`, `NTCombatDataComponent`, `WorldInfo`, and `NTAICoordinator` dynamically without hardcoded static offsets.
- **Safe Inline Patching:** Allocates memory or safely patches instructions while tracking original bytes; automatically restores all native instructions on detach or application exit.

#### Cheat Table (`DMC-DevilMayCry.CT`)
- **Cheat Engine 7.x Compatible:** Clean, standard XML table structure (`version 45`).
- **Automated Lua Reflection Script:** Auto-attaches to `DMC-DevilMayCry.exe`, performs AOB signature scans, resolves UE3 pointer paths (`dmc_Pawn`, `dmc_Profile`, `dmc_GameInfo`, etc.), and dynamically populates global symbol records.
- **Full Inventory & Economy Mapping:** Resolves exact hash entries in `NTGameStatsManager` for Red Orbs, Gold Orbs, Copper/Argent/Gold/Ivory Keys, Vital Stars, DT Stars, and Cross Fragments.
- **Auto-Assembler Scripts:** Independent AOB-anchored injection scripts for One-Hit Kill / Enemy 1 HP and Never Decrease Items.
