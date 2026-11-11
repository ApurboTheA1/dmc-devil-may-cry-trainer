"""
DmC: Devil May Cry (Win32 1.0.8916.2) - Memory & UE3 Reflection Engine
Pure Python 3 stdlib + Win32 ctypes (zero third-party dependencies).
Supports embedded stdio JSON-Lines IPC (`--ipc`) for the native WPF UI.
"""

import argparse
import ctypes
from ctypes import wintypes
import json
import os
import struct
import sys
import threading
import time

# Win32 Constants & Structs
PROCESS_ALL = 0x0010 | 0x0020 | 0x0008 | 0x0400  # READ | WRITE | VM_OP | QUERY_INFO
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
PAGE_EXECUTE_READWRITE = 0x40
INVALID_HANDLE = wintypes.HANDLE(-1).value


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256),
        ("szExePath", wintypes.WCHAR * 260),
    ]


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32_dll = ctypes.WinDLL("user32", use_last_error=True)
k32.OpenProcess.restype = wintypes.HANDLE
k32.ReadProcessMemory.restype = wintypes.BOOL
k32.WriteProcessMemory.restype = wintypes.BOOL
k32.VirtualProtectEx.restype = wintypes.BOOL
k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
k32.CloseHandle.restype = wintypes.BOOL
k32.Beep.restype = wintypes.BOOL
k32.Process32FirstW.restype = wintypes.BOOL
k32.Process32NextW.restype = wintypes.BOOL
k32.Module32FirstW.restype = wintypes.BOOL
k32.Module32NextW.restype = wintypes.BOOL
u32_dll.GetAsyncKeyState.restype = ctypes.c_short

# Verified 1-hit unique AOB signatures (DMC-DevilMayCry.exe v1.0.8916.2)
AOB_SIGNATURES = {
    "GNames": ("8B 0D ?? ?? ?? ?? 8B 3D ?? ?? ?? ?? 83 C4 04 89 1C 85 ?? ?? ?? ?? 8B 43 08", 8),
    "GObjects": ("8B 15 ?? ?? ?? ?? 8B 0C B2 E8 ?? ?? ?? ?? A1 ?? ?? ?? ?? 46", 2),
    "GEngine": ("83 7E 20 00 74 3D 8B 0D ?? ?? ?? ?? 83 B9 5C 06 00 00 00", 8),
    "StatsMap": ("8D 4C 24 08 51 B9 ?? ?? ?? ?? E8 ?? ?? ?? ?? 8B 44 24 04 83 F8 FF", 6),
    "CounterDec": ("8B 44 24 14 50 E8 ?? ?? ?? ?? 83 C4 04 85 C0 74 0B ?? ?? ?? ?? ?? 74 04 ?? 89 48 0C 8B 4C 24 04", 24),
}

# Verified UE3 property offsets
OFF_UOBJECT_NAME = 0x28
OFF_UOBJECT_CLASS = 0x30
OFF_ENGINE_GAMEPLAYERS = 0x04DC
OFF_ENGINE_PROFILE = 0x07D4
OFF_PLAYER_ACTOR = 0x003C
OFF_ACTOR_LOCATION = 0x0050
OFF_ACTOR_DRAWSCALE = 0x0068
OFF_ACTOR_CUSTOM_TIMEDIL = 0x008C
OFF_ACTOR_COLLISION_FLAGS = 0x009C
OFF_ACTOR_WORLDINFO = 0x00D8
OFF_PC_FLAGS = 0x0234
OFF_PC_FOVANGLE = 0x03F8
OFF_PC_DESIREDFOV = 0x03FC
OFF_PC_DEFAULTFOV = 0x0400
OFF_PC_HUD = 0x0424
OFF_PC_DVPLAYER = 0x0808
OFF_PC_PLAYER_FLAGS = 0x080C
OFF_HUD_FLAGS = 0x0230
OFF_PAWN_PHYS_FLAGS = 0x03A8
OFF_PAWN_COMBAT_BEHAV = 0x0744
OFF_PAWN_COMBAT_DATA = 0x074C
OFF_PAWN_HEALTH = 0x0840
OFF_PAWN_MAXHEALTH = 0x0844
OFF_PAWN_DVFLAGS = 0x0940
OFF_PAWN_GLIDE_COUNT = 0x0B7C
OFF_PAWN_AICOORD = 0x0DB0
OFF_PAWN_TRIGGER_COMP = 0x0E8C
OFF_PAWN_DANTE_GAMEPLAY_PARAMS = 0x0FE0
OFF_PAWN_DANTE_MOVEMENT_PARAMS = 0x0FE4
OFF_TRIGGER_MAX = 0x0080
OFF_TRIGGER_CUR = 0x0084
OFF_TRIGGER_FLAGS = 0x0090
OFF_CB_FLAGS = 0x0100
OFF_CB_STYLE_DMG_MULT = 0x01C8
OFF_CB_PLAYER_FLAGS = 0x01CC
OFF_CB_CUR_OVERDRIVE = 0x0270
OFF_CB_MAX_OVERDRIVE = 0x0274
OFF_CB_DANTE_FLAGS = 0x027C
OFF_CB_DEMON_EVADE_DMG = 0x0284
OFF_CB_DEMON_EVADE_STYLE = 0x0288
OFF_CD_FLAGS = 0x0118
OFF_WI_FLAGS = 0x04D4
OFF_WI_TIMEDILATION = 0x05F0
OFF_WI_GAME = 0x0678
OFF_WI_GRAVITYZ = 0x0680
OFF_GI_ENEMY_MGR = 0x0464
OFF_GI_STYLE_SYS = 0x04B8
OFF_GI_SECRET_MGR = 0x04EC
OFF_GI_MISSION_TIME = 0x0514
OFF_GI_DAMAGE_TAKEN = 0x0518
OFF_EM_ACTIVE_ENEMIES = 0x0058
OFF_STYLE_PARAMS = 0x02D4
OFF_STYLE_POINTS = 0x0340
OFF_STYLE_RANK = 0x0344
OFF_STYLE_DECAY_DELAY = 0x0348
OFF_STYLE_MISSION_SCORE = 0x0360
OFF_STYLEPARAM_GLOBAL_MULT = 0x0080
OFF_SM_DISPLAY_TIMER = 0x0088
OFF_SM_TIMER = 0x008C
OFF_PROFILE_XP = 0x00EC
OFF_PROFILE_POINTS_TOTAL = 0x00F0
OFF_PROFILE_POINTS_UNSPENT = 0x00F4
OFF_PROFILE_POINTS_OTHER = 0x00FC
OFF_AI_COORD_NTFLAGS = 0x025C
OFF_AI_COORD_DVFLAGS = 0x02AC
OFF_MOV_PLAYMODE_NORMAL = 0x00DC
OFF_MOV_PLAYMODE_DEMON = 0x0174
OFF_MOV_PLAYMODE_ANGEL = 0x0178
OFF_PLAYMODE_JUMP = 0x0050
OFF_JUMP_MIN_H = 0x0044
OFF_JUMP_MAX_H = 0x0048
OFF_JUMP_MAX_COUNT = 0x0074
OFF_JUMP_AIR_MIN_H = 0x0078
OFF_JUMP_AIR_MAX_H = 0x007C
OFF_GP_DETONATOR_PARAMS = 0x03F0
OFF_DETONATOR_MAX_DARTS = 0x00A0
OFF_STAT_VALUE = 0x000C

# Data-driven inventory lock mapping: toggle -> (value_key, [(stat_name, keep_max_only), ...])
STAT_LOCK_TABLE = (
    ("unlim_red_orbs", "red_orbs_lock", [("Orb_Red", False), ("REDORBS_ACQUIRED_TOTAL", True)]),
    ("unlim_gold_orbs", "gold_orbs_lock", [("Orb_Gold", False), ("Orb_Gold_Persistent", False)]),
    ("unlim_copper_keys", "keys_lock", [("MundusKeyBronze", False)]),
    ("unlim_argent_keys", "keys_lock", [("MundusKeySilver", False)]),
    ("unlim_gold_keys", "keys_lock", [("MundusKeyGold", False)]),
    ("unlim_ivory_keys", "keys_lock", [("MundusKeyIvory", False)]),
    ("unlim_small_vs", "stars_lock", [("VitalStar_Small", False), ("VitalStar_Small_Persistent", False)]),
    ("unlim_large_vs", "stars_lock", [("VitalStar_Large", False), ("VitalStar_Large_Persistent", False)]),
    ("unlim_small_dts", "stars_lock", [("DevilTriggerStar_Small", False), ("DevilTriggerStar_Small_Persistent", False)]),
    ("unlim_large_dts", "stars_lock", [("DevilTriggerStar_Large", False), ("DevilTriggerStar_Large_Persistent", False)]),
    ("unlim_health_frag", "frags_lock", [("OrbFragment_Blue", False)]),
    ("unlim_dt_frag", "frags_lock", [("OrbFragment_Purple", False)]),
)

VK_MAP = {
    **{f"F{i}": 0x6F + i for i in range(1, 13)},
    **{f"NUM{i}": 0x60 + i for i in range(10)},
    "NUM*": 0x6A, "NUM+": 0x6B, "NUM-": 0x6D, "NUM.": 0x6E, "NUM/": 0x6F,
    "HOME": 0x24, "END": 0x23, "INS": 0x2D, "DEL": 0x2E, "PGUP": 0x21, "PGDN": 0x22,
    **{str(i): 0x30 + i for i in range(10)},
    **{chr(c): c for c in range(ord("A"), ord("Z") + 1)},
}

DEFAULT_CONFIG = {
    "sound_feedback": True,
    "toggles": {
        "unlimited_health": False, "god_mode": False, "unlimited_devil_trigger": False,
        "no_dt_end_no_enemies": False, "unlimited_overdrive": False, "fast_kill": False,
        "damage_mult_enabled": False, "always_demon_evade": False, "force_dismember": False,
        "sss_style_rank": False, "no_style_decay": False, "style_mult_enabled": False,
        "max_mission_score": False, "zero_damage_taken": False, "freeze_mission_timer": False,
        "freeze_secret_timer": False, "unlimited_kablooey_darts": False,
        "never_decrease_items": False, "unlim_red_orbs": False, "unlim_gold_orbs": False,
        "unlim_copper_keys": False, "unlim_argent_keys": False, "unlim_gold_keys": False,
        "unlim_ivory_keys": False, "unlim_small_vs": False, "unlim_large_vs": False,
        "unlim_small_dts": False, "unlim_large_dts": False, "unlim_health_frag": False,
        "unlim_dt_frag": False, "unlim_upgrade_points": False, "infinite_air_jumps": False,
        "infinite_air_evades": False, "player_speed_enabled": False, "world_speed_enabled": False,
        "jump_height_enabled": False, "custom_gravity_enabled": False, "freeze_enemies_ai": False,
        "enemies_dont_attack": False, "freeze_world": False, "noclip_fly": False,
        "custom_fov_enabled": False, "hide_hud": False, "player_scale_enabled": False,
        "unlock_all_attacks": False,
    },
    "values": {
        "damage_multiplier": 5.0, "demon_evade_dmg_mult": 3.0, "style_multiplier": 5.0,
        "player_speed": 1.4, "world_speed": 1.2, "jump_height_mult": 1.8,
        "custom_gravity": -1100.0, "custom_fov": 100.0, "player_scale": 1.0,
        "red_orbs_lock": 999999, "gold_orbs_lock": 3, "keys_lock": 99,
        "stars_lock": 10, "frags_lock": 3, "upgrade_points_lock": 99,
    },
    "hotkeys": {
        "unlimited_health": "F1", "unlimited_devil_trigger": "F2", "fast_kill": "F3",
        "unlim_red_orbs": "F4", "unlim_gold_orbs": "F5", "unlim_copper_keys": "F6",
        "unlim_argent_keys": "F7", "unlim_gold_keys": "F8", "unlim_ivory_keys": "F9",
        "unlim_small_vs": "F10", "unlim_large_vs": "F11",
        "unlim_small_dts": "Ctrl+F1", "unlim_large_dts": "Ctrl+F2",
        "unlim_health_frag": "Ctrl+F3", "unlim_dt_frag": "Ctrl+F4",
        "god_mode": "Num1", "sss_style_rank": "Num2", "max_mission_score": "Num3",
        "never_decrease_items": "Num4", "unlimited_overdrive": "Num5",
        "freeze_mission_timer": "Num6", "freeze_secret_timer": "Num7",
        "infinite_air_jumps": "Num8", "freeze_enemies_ai": "Num9", "damage_mult_enabled": "Num0",
        "save_pos_0": "Num.", "load_pos_0": "Num+", "undo_teleport": "Num-", "disable_all": "Home",
    },
}


def aob_find_first(buf: bytes, pattern_str: str) -> int | None:
    tokens = pattern_str.split()
    fixed = [(i, int(t, 16)) for i, t in enumerate(tokens) if t != "??"]
    if not fixed:
        return None
    ao, ab = fixed[0]
    plen, blen = len(tokens), len(buf)
    pos = ao
    while True:
        idx = buf.find(ab, pos)
        if idx == -1:
            return None
        st = idx - ao
        if st >= 0 and st + plen <= blen and all(buf[st + fo] == fv for fo, fv in fixed):
            return st
        pos = idx + 1


def parse_hotkey(hk: str):
    if not hk:
        return None
    mods, key = set(), None
    for p in (x.strip().upper() for x in hk.split("+") if x.strip()):
        if p in ("CTRL", "CONTROL"):
            mods.add("CTRL")
        elif p in ("SHIFT", "ALT"):
            mods.add(p)
        elif p in VK_MAP:
            key = VK_MAP[p]
    return (frozenset(mods), key) if key is not None else None


def find_game_pid_and_module() -> tuple[int | None, int | None, int]:
    """Find DMC-DevilMayCry.exe PID and Win32 base module via pure Toolhelp32."""
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap or snap == INVALID_HANDLE:
        return None, None, 0
    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    target_pid = None
    try:
        if k32.Process32FirstW(snap, ctypes.byref(pe)):
            while True:
                if pe.szExeFile.lower() == "dmc-devilmaycry.exe":
                    target_pid = pe.th32ProcessID
                    break
                if not k32.Process32NextW(snap, ctypes.byref(pe)):
                    break
    finally:
        k32.CloseHandle(snap)
    if not target_pid:
        return None, None, 0

    msnap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, target_pid)
    if not msnap or msnap == INVALID_HANDLE:
        return None, None, 0
    me = MODULEENTRY32W()
    me.dwSize = ctypes.sizeof(MODULEENTRY32W)
    base, size = None, 0
    try:
        if k32.Module32FirstW(msnap, ctypes.byref(me)):
            while True:
                if me.szModule.lower() == "dmc-devilmaycry.exe":
                    base = ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value
                    size = me.modBaseSize
                    break
                if not k32.Module32NextW(msnap, ctypes.byref(me)):
                    break
    finally:
        k32.CloseHandle(msnap)
    return (target_pid, base, size) if base else (None, None, 0)


class DmCTrainerEngine:
    def __init__(self, settings_path: str):
        self.settings_path = settings_path
        self.lock = threading.RLock()
        self.config = self._load_config()
        self.running = False
        self.thread = None

        self.pid = None
        self.handle = None
        self.base = None
        self.mod_size = 0
        self.addrs = {}
        self.counter_dec_patched = False

        # Reusable RPM 4-byte buffer & caches
        self._buf4 = ctypes.create_string_buffer(4)
        self._read4 = ctypes.c_size_t()
        self.name_cache = {}
        self.name_ptrs = []
        self.gnames_num = 0
        self.obj_cls_cache = {}
        self.stat_ptr_cache = {}
        self.stats_num_last = -1

        self.orig_jump_params = {}
        self.orig_style_global_mult = None
        self.orig_detonator_max_darts = None
        self.saved_locations = [None, None, None]
        self.undo_location = None

        self._was_fast_kill = False
        self._was_jump_mod = False
        self._last_attach_attempt = 0.0
        self.prev_keys = set()
        self.last_event = ""
        self.telemetry = self._empty_telemetry()

    def _empty_telemetry(self):
        return {
            "attached": False, "pid": None, "in_game": False, "character": "None",
            "health": 0.0, "max_health": 0.0, "devil_trigger": 0.0, "max_devil_trigger": 0.0,
            "overdrive": 0.0, "max_overdrive": 0.0, "style_rank": 0, "style_points": 0.0,
            "mission_score": 0.0, "mission_time": 0.0, "damage_taken": 0.0,
            "red_orbs": 0, "gold_orbs": 0, "upgrade_points": 0, "xp": 0,
            "copper_keys": 0, "argent_keys": 0, "gold_keys": 0, "ivory_keys": 0,
            "small_vs": 0, "large_vs": 0, "small_dts": 0, "large_dts": 0,
            "blue_frags": 0, "purple_frags": 0, "active_enemies": 0,
            "location": [0.0, 0.0, 0.0], "fov": 85.0, "player_speed": 1.0,
            "world_speed": 1.0, "gravity": -2250.0, "saved_slots": [None, None, None],
            "last_event": self.last_event,
        }

    def _load_config(self):
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    user = json.load(f)
                for sec in ("toggles", "values", "hotkeys"):
                    if isinstance(user.get(sec), dict):
                        cfg[sec].update(user[sec])
                if "sound_feedback" in user:
                    cfg["sound_feedback"] = bool(user["sound_feedback"])
            except Exception:
                pass
        return cfg

    def save_config(self):
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    # --- Optimized Memory I/O ---
    def rpm(self, addr: int, sz: int) -> bytes | None:
        if not self.handle or not addr or addr < 0x10000:
            return None
        buf = ctypes.create_string_buffer(sz)
        read = ctypes.c_size_t()
        if not k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), buf, sz, ctypes.byref(read)) or read.value < sz:
            return None
        return buf.raw

    def _rpm4(self, addr: int, fmt: str):
        if not self.handle or not addr or addr < 0x10000:
            return None
        if not k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), self._buf4, 4, ctypes.byref(self._read4)) or self._read4.value < 4:
            return None
        return struct.unpack_from(fmt, self._buf4, 0)[0]

    def r_u32(self, addr: int) -> int | None: return self._rpm4(addr, "<I")
    def r_i32(self, addr: int) -> int | None: return self._rpm4(addr, "<i")
    def r_f32(self, addr: int) -> float | None: return self._rpm4(addr, "<f")

    def wpm(self, addr: int, data: bytes) -> bool:
        if not self.handle or not addr or addr < 0x10000:
            return False
        written = ctypes.c_size_t()
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), data, len(data), ctypes.byref(written)))

    def w_i32(self, addr: int, val: int) -> bool: return self.wpm(addr, struct.pack("<i", int(val)))
    def w_u32(self, addr: int, val: int) -> bool: return self.wpm(addr, struct.pack("<I", int(val) & 0xFFFFFFFF))
    def w_f32(self, addr: int, val: float) -> bool: return self.wpm(addr, struct.pack("<f", float(val)))

    def set_bits(self, addr: int, set_mask: int = 0, clr_mask: int = 0) -> bool:
        cur = self.r_u32(addr)
        if cur is None:
            return False
        nxt = (cur | set_mask) & ~clr_mask
        return self.w_u32(addr, nxt) if nxt != cur else True

    def patch_bytes(self, addr: int, data: bytes) -> bool:
        if not self.handle or not addr:
            return False
        old_prot, tmp = wintypes.DWORD(), wintypes.DWORD()
        if not k32.VirtualProtectEx(self.handle, ctypes.c_void_p(addr), len(data), PAGE_EXECUTE_READWRITE, ctypes.byref(old_prot)):
            return False
        ok = self.wpm(addr, data)
        k32.VirtualProtectEx(self.handle, ctypes.c_void_p(addr), len(data), old_prot.value, ctypes.byref(tmp))
        return ok

    # --- Attach & AOB Scan ---
    def _detach(self):
        if self.handle:
            if self.counter_dec_patched and self.addrs.get("CounterDec_Instr"):
                self.patch_bytes(self.addrs["CounterDec_Instr"], b"\x49")
            k32.CloseHandle(self.handle)
        self.handle = None
        self.pid = None
        self.base = None
        self.mod_size = 0
        self.addrs.clear()
        self.counter_dec_patched = False
        self.name_cache.clear()
        self.name_ptrs = []
        self.gnames_num = 0
        self.obj_cls_cache.clear()
        self.stat_ptr_cache.clear()
        self.stats_num_last = -1
        self.orig_jump_params.clear()
        self.orig_style_global_mult = None
        self.orig_detonator_max_darts = None
        self._was_fast_kill = False
        self._was_jump_mod = False
        self.telemetry = self._empty_telemetry()

    def _try_attach(self) -> bool:
        target_pid, base, size = find_game_pid_and_module()
        if not target_pid or not base:
            return False
        h = k32.OpenProcess(PROCESS_ALL, False, target_pid)
        if not h:
            return False
        self.pid, self.handle, self.base, self.mod_size = target_pid, h, base, size
        if not self._scan_aobs():
            self._detach()
            return False
        return True

    def _scan_aobs(self) -> bool:
        dos = self.rpm(self.base, 0x100)
        if not dos:
            return False
        pe_off = struct.unpack_from("<I", dos, 0x3C)[0]
        hdr = self.rpm(self.base + pe_off, 0x120)
        if not hdr:
            return False
        opt_sz = struct.unpack_from("<H", hdr, 20)[0]
        text_va, text_sz = struct.unpack_from("<II", hdr, 24 + opt_sz + 12)
        text = self.rpm(self.base + text_va, text_sz)
        if not text:
            return False

        resolved = {}
        for name, (pat, imm_off) in AOB_SIGNATURES.items():
            pos = aob_find_first(text, pat)
            if pos is None:
                if name == "CounterDec":
                    continue
                return False
            if name == "CounterDec":
                if text[pos + 17] == 0x8B:
                    resolved["CounterDec_Instr"] = self.base + text_va + pos + imm_off
            else:
                resolved[name] = struct.unpack_from("<I", text, pos + imm_off)[0]

        self.addrs = resolved
        instr = resolved.get("CounterDec_Instr")
        self.counter_dec_patched = (self.rpm(instr, 1) == b"\x90") if instr else False
        return True

    # --- UE3 Reflection ---
    def _refresh_gnames(self):
        gn_addr = self.addrs.get("GNames")
        if not gn_addr:
            return
        hdr = self.rpm(gn_addr, 8)
        if not hdr:
            return
        data, num = struct.unpack("<II", hdr)
        if data and 0 < num <= 1000000 and num != self.gnames_num:
            raw = self.rpm(data, num * 4)
            if raw:
                self.name_ptrs = struct.unpack(f"<{num}I", raw)
                self.gnames_num = num

    def get_name(self, idx: int) -> str:
        cached = self.name_cache.get(idx)
        if cached is not None:
            return cached
        if idx < 0 or idx >= self.gnames_num:
            return ""
        entry = self.rpm(self.name_ptrs[idx], 144)
        if not entry or len(entry) < 18:
            return ""
        idx_flags = struct.unpack_from("<I", entry, 8)[0]
        raw = entry[16:]
        if idx_flags & 1:
            res = raw[: (raw.find(b"\x00\x00") // 2) * 2 + 2].decode("utf-16le", "ignore").rstrip("\x00")
        else:
            res = raw.split(b"\x00", 1)[0].decode("latin1", "ignore")
        self.name_cache[idx] = res
        return res

    def get_obj_class_name(self, obj_ptr: int) -> str:
        if not obj_ptr or obj_ptr < 0x10000:
            return ""
        cached = self.obj_cls_cache.get(obj_ptr)
        if cached is not None:
            return cached
        cls = self.r_u32(obj_ptr + OFF_UOBJECT_CLASS)
        if not cls or cls < 0x10000:
            return ""
        nidx = self.r_i32(cls + OFF_UOBJECT_NAME)
        res = self.get_name(nidx) if nidx is not None else ""
        if res:
            if len(self.obj_cls_cache) > 512:
                self.obj_cls_cache.clear()
            self.obj_cls_cache[obj_ptr] = res
        return res

    def _refresh_stats_cache(self):
        sm_addr = self.addrs.get("StatsMap")
        if not sm_addr:
            return
        hdr = self.rpm(sm_addr, 8)
        if not hdr:
            return
        arr_data, arr_num = struct.unpack("<II", hdr)
        if not arr_data or not (0 < arr_num <= 8000):
            return
        if arr_num == self.stats_num_last and self.stat_ptr_cache:
            return
        self._refresh_gnames()
        raw = self.rpm(arr_data, arr_num * 20)
        if not raw:
            return
        cache = {}
        for i in range(arr_num):
            nidx, nnum, stat_ptr, _, _ = struct.unpack_from("<IIIII", raw, i * 20)
            if stat_ptr >= 0x10000 and nnum == 0:
                sname = self.get_name(nidx)
                if sname:
                    cache[sname] = stat_ptr
        self.stat_ptr_cache = cache
        self.stats_num_last = arr_num

    def get_stat_int(self, name: str, default: int = 0) -> int:
        p = self.stat_ptr_cache.get(name)
        v = self.r_i32(p + OFF_STAT_VALUE) if p else None
        return v if v is not None else default

    def set_stat_int(self, name: str, val: int) -> bool:
        p = self.stat_ptr_cache.get(name)
        return self.w_i32(p + OFF_STAT_VALUE, val) if p else False

    def set_stat_float(self, name: str, val: float) -> bool:
        p = self.stat_ptr_cache.get(name)
        return self.w_f32(p + OFF_STAT_VALUE, val) if p else False

    # --- Live Pointer Resolution ---
    def _resolve_live_ptrs(self) -> dict:
        ge = self.r_u32(self.addrs.get("GEngine"))
        if not ge:
            return {}
        profile = self.r_u32(ge + OFF_ENGINE_PROFILE)
        gp_data = self.r_u32(ge + OFF_ENGINE_GAMEPLAYERS)
        lp = self.r_u32(gp_data) if gp_data else None
        pc = self.r_u32(lp + OFF_PLAYER_ACTOR) if lp else None
        in_game = self.get_obj_class_name(pc).startswith("DVPlayerController_") if pc else False
        pawn = self.r_u32(pc + OFF_PC_DVPLAYER) if (pc and in_game) else None
        pawn_cls = self.get_obj_class_name(pawn) if pawn else ""
        if not pawn_cls.startswith("DVPawn_"):
            pawn, in_game = None, False

        wi = self.r_u32(pc + OFF_ACTOR_WORLDINFO) if in_game else None
        gi = self.r_u32(wi + OFF_WI_GAME) if wi else None
        return {
            "ge": ge, "profile": profile, "pc": pc, "in_game": in_game,
            "pawn": pawn, "pawn_cls": pawn_cls or "None", "wi": wi, "gi": gi,
            "cb": self.r_u32(pawn + OFF_PAWN_COMBAT_BEHAV) if pawn else None,
            "cd": self.r_u32(pawn + OFF_PAWN_COMBAT_DATA) if pawn else None,
            "trig": self.r_u32(pawn + OFF_PAWN_TRIGGER_COMP) if pawn else None,
            "em": self.r_u32(gi + OFF_GI_ENEMY_MGR) if gi else None,
            "ss": self.r_u32(gi + OFF_GI_STYLE_SYS) if gi else None,
            "sm": self.r_u32(gi + OFF_GI_SECRET_MGR) if gi else None,
            "ai": self.r_u32(pawn + OFF_PAWN_AICOORD) if pawn else None,
            "hud": self.r_u32(pc + OFF_PC_HUD) if pc else None,
        }

    def _get_active_enemies(self, em_ptr: int) -> list[int]:
        if not em_ptr:
            return []
        hdr = self.rpm(em_ptr + OFF_EM_ACTIVE_ENEMIES, 8)
        if not hdr:
            return []
        data, num = struct.unpack("<II", hdr)
        if not data or not (0 < num <= 200):
            return []
        raw = self.rpm(data, num * 4)
        return [p for p in struct.unpack(f"<{num}I", raw) if p >= 0x10000] if raw else []

    def _get_jump_param_objects(self, pawn: int, pawn_cls: str) -> list[int]:
        if not pawn or "Dante" not in pawn_cls:
            return []
        mp = self.r_u32(pawn + OFF_PAWN_DANTE_MOVEMENT_PARAMS)
        if not mp:
            return []
        objs, seen = [], set()
        for off in (OFF_MOV_PLAYMODE_NORMAL, OFF_MOV_PLAYMODE_DEMON, OFF_MOV_PLAYMODE_ANGEL):
            pm = self.r_u32(mp + off)
            j = self.r_u32(pm + OFF_PLAYMODE_JUMP) if pm else None
            if j and j not in seen:
                seen.add(j)
                objs.append(j)
        return objs

    # --- Core Loop Tick ---
    def _tick(self):
        with self.lock:
            now = time.monotonic()
            if not self.handle:
                if now - self._last_attach_attempt < 0.5:
                    return
                self._last_attach_attempt = now
                if not self._try_attach():
                    self.telemetry = self._empty_telemetry()
                    return
            elif self.r_u32(self.base) is None:
                self._detach()
                return

            self._refresh_gnames()
            self._refresh_stats_cache()
            ptrs = self._resolve_live_ptrs()
            toggles, vals = self.config["toggles"], self.config["values"]

            # 1. Counter_Decrement AOB Patch
            want_patch = bool(toggles.get("never_decrease_items"))
            instr = self.addrs.get("CounterDec_Instr")
            if want_patch != self.counter_dec_patched and instr:
                if self.patch_bytes(instr, b"\x90" if want_patch else b"\x49"):
                    self.counter_dec_patched = want_patch

            # 2. Data-driven inventory stat locks
            for tkey, vkey, stats in STAT_LOCK_TABLE:
                if toggles.get(tkey):
                    v = int(vals[vkey])
                    for sname, keep_max in stats:
                        if not keep_max or self.get_stat_int(sname, 0) < v:
                            self.set_stat_int(sname, v)

            # 3. Profile Upgrade Points lock
            prof = ptrs.get("profile")
            if prof and toggles.get("unlim_upgrade_points"):
                up = int(vals["upgrade_points_lock"])
                cur_u = self.r_i32(prof + OFF_PROFILE_POINTS_UNSPENT)
                if cur_u is not None and cur_u < up:
                    diff = up - cur_u
                    self.w_i32(prof + OFF_PROFILE_POINTS_UNSPENT, up)
                    self.w_i32(prof + OFF_PROFILE_POINTS_TOTAL, (self.r_i32(prof + OFF_PROFILE_POINTS_TOTAL) or 0) + diff)
                    self.w_i32(prof + OFF_PROFILE_POINTS_OTHER, (self.r_i32(prof + OFF_PROFILE_POINTS_OTHER) or 0) + diff)

            # 4. In-Game Mods
            in_game = ptrs.get("in_game", False)
            pawn, pc, cb, cd = ptrs.get("pawn"), ptrs.get("pc"), ptrs.get("cb"), ptrs.get("cd")
            trig, wi, gi, ss = ptrs.get("trig"), ptrs.get("wi"), ptrs.get("gi"), ptrs.get("ss")
            sm, ai, hud, em = ptrs.get("sm"), ptrs.get("ai"), ptrs.get("hud"), ptrs.get("em")
            is_dante = "Dante" in ptrs.get("pawn_cls", "")
            enemy_count = (self.r_i32(em + OFF_EM_ACTIVE_ENEMIES + 4) or 0) if (in_game and em) else 0
            enemy_count = enemy_count if 0 <= enemy_count <= 200 else 0

            if in_game and pawn:
                mhp = self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 1000.0
                god = bool(toggles.get("god_mode"))
                if toggles.get("unlimited_health") or god:
                    self.w_f32(pawn + OFF_PAWN_HEALTH, mhp)

                if pc:
                    self.set_bits(pc + OFF_PC_FLAGS, 0x02 if god else 0, 0 if god else 0x02)
                if cb:
                    self.set_bits(cb + OFF_CB_FLAGS, 0 if god else 0x01, 0x01 if god else 0)
                if cd:
                    self.set_bits(cd + OFF_CD_FLAGS, 0x01 if god else 0, 0 if god else 0x01)

                if trig:
                    unlim_dt = bool(toggles.get("unlimited_devil_trigger"))
                    no_end = bool(toggles.get("no_dt_end_no_enemies"))
                    set_m = (0x30 if unlim_dt else 0) | (0 if no_end else 0x40)
                    clr_m = (0 if unlim_dt else 0x30) | (0x40 if no_end else 0)
                    self.set_bits(trig + OFF_TRIGGER_FLAGS, set_m, clr_m)
                    if unlim_dt:
                        self.w_f32(trig + OFF_TRIGGER_CUR, self.r_f32(trig + OFF_TRIGGER_MAX) or 1800.0)

                if cb:
                    if is_dante:
                        unlim_od = bool(toggles.get("unlimited_overdrive"))
                        ev_buff = bool(toggles.get("always_demon_evade"))
                        self.set_bits(cb + OFF_CB_DANTE_FLAGS, (0x04 if unlim_od else 0) | (0x02 if ev_buff else 0),
                                      (0 if unlim_od else 0x04) | (0 if ev_buff else 0x02))
                        if unlim_od:
                            self.w_f32(cb + OFF_CB_CUR_OVERDRIVE, self.r_f32(cb + OFF_CB_MAX_OVERDRIVE) or 100.0)
                        if ev_buff:
                            mult = float(vals["demon_evade_dmg_mult"])
                            self.w_f32(cb + OFF_CB_DEMON_EVADE_DMG, mult)
                            self.w_f32(cb + OFF_CB_DEMON_EVADE_STYLE, mult)

                    dism = bool(toggles.get("force_dismember"))
                    self.set_bits(cb + OFF_CB_PLAYER_FLAGS, 0x04 if dism else 0, 0 if dism else 0x04)

                    if toggles.get("fast_kill"):
                        self.w_f32(cb + OFF_CB_STYLE_DMG_MULT, 99999.0)
                    elif toggles.get("damage_mult_enabled"):
                        self.w_f32(cb + OFF_CB_STYLE_DMG_MULT, float(vals["damage_multiplier"]))
                    else:
                        cur_mult = self.r_f32(cb + OFF_CB_STYLE_DMG_MULT)
                        if cur_mult is not None and cur_mult > 2.5:
                            self.w_f32(cb + OFF_CB_STYLE_DMG_MULT, 1.0)

                fast_kill = bool(toggles.get("fast_kill"))
                if fast_kill or self._was_fast_kill:
                    for ep in self._get_active_enemies(em):
                        ecb = self.r_u32(ep + OFF_PAWN_COMBAT_BEHAV)
                        if ecb:
                            self.set_bits(ecb + OFF_CB_FLAGS, 0x02 if fast_kill else 0, 0 if fast_kill else 0x02)
                    self._was_fast_kill = fast_kill

                if ss:
                    if toggles.get("sss_style_rank"):
                        self.w_i32(ss + OFF_STYLE_RANK, 7)
                        self.w_f32(ss + OFF_STYLE_POINTS, 9999.0)
                        self.w_f32(ss + OFF_STYLE_DECAY_DELAY, 99.0)
                    elif toggles.get("no_style_decay"):
                        self.w_f32(ss + OFF_STYLE_DECAY_DELAY, 99.0)
                    if toggles.get("max_mission_score"):
                        self.w_f32(ss + OFF_STYLE_MISSION_SCORE, 9999999.0)

                    ssp = self.r_u32(ss + OFF_STYLE_PARAMS)
                    if ssp:
                        if self.orig_style_global_mult is None:
                            self.orig_style_global_mult = self.r_f32(ssp + OFF_STYLEPARAM_GLOBAL_MULT) or 1.0
                        if toggles.get("style_mult_enabled"):
                            self.w_f32(ssp + OFF_STYLEPARAM_GLOBAL_MULT, float(vals["style_multiplier"]))
                        else:
                            cur_sm = self.r_f32(ssp + OFF_STYLEPARAM_GLOBAL_MULT)
                            if cur_sm is not None and abs(cur_sm - self.orig_style_global_mult) > 0.01:
                                self.w_f32(ssp + OFF_STYLEPARAM_GLOBAL_MULT, self.orig_style_global_mult)

                if gi:
                    if toggles.get("zero_damage_taken") or god:
                        self.w_f32(gi + OFF_GI_DAMAGE_TAKEN, 0.0)
                    if toggles.get("freeze_mission_timer"):
                        self.w_f32(gi + OFF_GI_MISSION_TIME, 0.0)

                if sm and toggles.get("freeze_secret_timer"):
                    self.w_f32(sm + OFF_SM_TIMER, 99.0)
                    self.w_i32(sm + OFF_SM_DISPLAY_TIMER, 99)

                if is_dante:
                    gp = self.r_u32(pawn + OFF_PAWN_DANTE_GAMEPLAY_PARAMS)
                    det = self.r_u32(gp + OFF_GP_DETONATOR_PARAMS) if gp else None
                    if det:
                        if self.orig_detonator_max_darts is None:
                            self.orig_detonator_max_darts = self.r_i32(det + OFF_DETONATOR_MAX_DARTS) or 4
                        target_darts = 99 if toggles.get("unlimited_kablooey_darts") else self.orig_detonator_max_darts
                        if self.r_i32(det + OFF_DETONATOR_MAX_DARTS) != target_darts:
                            self.w_i32(det + OFF_DETONATOR_MAX_DARTS, target_darts)

                if toggles.get("infinite_air_evades"):
                    self.set_bits(pawn + OFF_PAWN_DVFLAGS, 0x00800000, 0)
                    self.w_i32(pawn + OFF_PAWN_GLIDE_COUNT, 0)

                jump_active = bool(toggles.get("infinite_air_jumps") or toggles.get("jump_height_enabled"))
                if jump_active or self._was_jump_mod:
                    for j_obj in self._get_jump_param_objects(pawn, ptrs["pawn_cls"]):
                        if j_obj not in self.orig_jump_params:
                            self.orig_jump_params[j_obj] = (
                                self.r_i32(j_obj + OFF_JUMP_MAX_COUNT) or 1,
                                self.r_f32(j_obj + OFF_JUMP_MIN_H) or 250.0,
                                self.r_f32(j_obj + OFF_JUMP_MAX_H) or 425.0,
                                self.r_f32(j_obj + OFF_JUMP_AIR_MIN_H) or 100.0,
                                self.r_f32(j_obj + OFF_JUMP_AIR_MAX_H) or 150.0,
                            )
                        cnt, min_h, max_h, amin_h, amax_h = self.orig_jump_params[j_obj]
                        want_cnt = 999 if toggles.get("infinite_air_jumps") else cnt
                        if self.r_i32(j_obj + OFF_JUMP_MAX_COUNT) != want_cnt:
                            self.w_i32(j_obj + OFF_JUMP_MAX_COUNT, want_cnt)
                        jm = float(vals["jump_height_mult"]) if toggles.get("jump_height_enabled") else 1.0
                        self.w_f32(j_obj + OFF_JUMP_MIN_H, min_h * jm)
                        self.w_f32(j_obj + OFF_JUMP_MAX_H, max_h * jm)
                        self.w_f32(j_obj + OFF_JUMP_AIR_MIN_H, amin_h * jm)
                        self.w_f32(j_obj + OFF_JUMP_AIR_MAX_H, amax_h * jm)
                    self._was_jump_mod = jump_active

                if toggles.get("player_speed_enabled"):
                    self.w_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL, float(vals["player_speed"]))

                fly_on = bool(toggles.get("noclip_fly"))
                self.set_bits(pawn + OFF_ACTOR_COLLISION_FLAGS, 0 if fly_on else 0x40000000, 0x40000000 if fly_on else 0)
                self.set_bits(pawn + OFF_PAWN_PHYS_FLAGS, 0 if fly_on else 0x04, 0x04 if fly_on else 0)

                target_scale = float(vals["player_scale"]) if toggles.get("player_scale_enabled") else 1.0
                cur_sc = self.r_f32(pawn + OFF_ACTOR_DRAWSCALE)
                if cur_sc is not None and abs(cur_sc - target_scale) > 0.01:
                    self.w_f32(pawn + OFF_ACTOR_DRAWSCALE, target_scale)

                if wi:
                    if toggles.get("world_speed_enabled"):
                        self.w_f32(wi + OFF_WI_TIMEDILATION, float(vals["world_speed"]))
                    if toggles.get("custom_gravity_enabled"):
                        self.w_f32(wi + OFF_WI_GRAVITYZ, float(vals["custom_gravity"]))
                    fw, fai = bool(toggles.get("freeze_world")), bool(toggles.get("freeze_enemies_ai"))
                    self.set_bits(wi + OFF_WI_FLAGS, (0x800 if fw else 0) | (0x2000 if fai else 0),
                                  (0 if fw else 0x800) | (0 if fai else 0x2000))

                if ai:
                    fai, no_atk = bool(toggles.get("freeze_enemies_ai")), bool(toggles.get("enemies_dont_attack"))
                    self.set_bits(ai + OFF_AI_COORD_NTFLAGS, 0x02 if fai else 0, 0 if fai else 0x02)
                    self.set_bits(ai + OFF_AI_COORD_DVFLAGS, 0x01 if no_atk else 0, 0 if no_atk else 0x01)

                if pc:
                    if toggles.get("custom_fov_enabled"):
                        fov = float(vals["custom_fov"])
                        self.w_f32(pc + OFF_PC_FOVANGLE, fov)
                        self.w_f32(pc + OFF_PC_DESIREDFOV, fov)
                        self.w_f32(pc + OFF_PC_DEFAULTFOV, fov)
                    if toggles.get("unlock_all_attacks"):
                        self.set_bits(pc + OFF_PC_PLAYER_FLAGS, 0xC0, 0)

                if hud:
                    hide = bool(toggles.get("hide_hud"))
                    self.set_bits(hud + OFF_HUD_FLAGS, 0 if hide else 0x02, 0x02 if hide else 0)

            # 5. Telemetry Snapshot
            loc = [0.0, 0.0, 0.0]
            if pawn:
                lb = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                if lb:
                    loc = [round(x, 1) for x in struct.unpack("<fff", lb)]

            self.telemetry = {
                "attached": True, "pid": self.pid, "in_game": in_game,
                "character": ptrs.get("pawn_cls", "None").replace("DVPawn_", ""),
                "health": round(self.r_f32(pawn + OFF_PAWN_HEALTH) or 0.0, 1) if pawn else 0.0,
                "max_health": round(self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 0.0, 1) if pawn else 0.0,
                "devil_trigger": round(self.r_f32(trig + OFF_TRIGGER_CUR) or 0.0, 1) if trig else 0.0,
                "max_devil_trigger": round(self.r_f32(trig + OFF_TRIGGER_MAX) or 0.0, 1) if trig else 0.0,
                "overdrive": round(self.r_f32(cb + OFF_CB_CUR_OVERDRIVE) or 0.0, 1) if (cb and is_dante) else 0.0,
                "max_overdrive": round(self.r_f32(cb + OFF_CB_MAX_OVERDRIVE) or 0.0, 1) if (cb and is_dante) else 0.0,
                "style_rank": (self.r_i32(ss + OFF_STYLE_RANK) or 0) if ss else 0,
                "style_points": round(self.r_f32(ss + OFF_STYLE_POINTS) or 0.0, 1) if ss else 0.0,
                "mission_score": round(self.r_f32(ss + OFF_STYLE_MISSION_SCORE) or 0.0, 0) if ss else 0.0,
                "mission_time": round(self.r_f32(gi + OFF_GI_MISSION_TIME) or 0.0, 1) if gi else 0.0,
                "damage_taken": round(self.r_f32(gi + OFF_GI_DAMAGE_TAKEN) or 0.0, 1) if gi else 0.0,
                "red_orbs": self.get_stat_int("Orb_Red", 0),
                "gold_orbs": self.get_stat_int("Orb_Gold", 0),
                "upgrade_points": (self.r_i32(prof + OFF_PROFILE_POINTS_UNSPENT) or 0) if prof else 0,
                "xp": (self.r_i32(prof + OFF_PROFILE_XP) or 0) if prof else 0,
                "copper_keys": self.get_stat_int("MundusKeyBronze", 0),
                "argent_keys": self.get_stat_int("MundusKeySilver", 0),
                "gold_keys": self.get_stat_int("MundusKeyGold", 0),
                "ivory_keys": self.get_stat_int("MundusKeyIvory", 0),
                "small_vs": self.get_stat_int("VitalStar_Small", 0),
                "large_vs": self.get_stat_int("VitalStar_Large", 0),
                "small_dts": self.get_stat_int("DevilTriggerStar_Small", 0),
                "large_dts": self.get_stat_int("DevilTriggerStar_Large", 0),
                "blue_frags": self.get_stat_int("OrbFragment_Blue", 0),
                "purple_frags": self.get_stat_int("OrbFragment_Purple", 0),
                "active_enemies": enemy_count, "location": loc,
                "fov": round(self.r_f32(pc + OFF_PC_FOVANGLE) or 85.0, 1) if pc else 85.0,
                "player_speed": round(self.r_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL) or 1.0, 2) if pawn else 1.0,
                "world_speed": round(self.r_f32(wi + OFF_WI_TIMEDILATION) or 1.0, 2) if wi else 1.0,
                "gravity": round(self.r_f32(wi + OFF_WI_GRAVITYZ) or -2250.0, 0) if wi else -2250.0,
                "saved_slots": [([round(v, 1) for v in s] if s else None) for s in self.saved_locations],
                "last_event": self.last_event,
            }

    # --- Controls & Actions ---
    def set_toggle(self, key: str, state: bool) -> bool:
        with self.lock:
            if key not in self.config["toggles"]:
                return False
            self.config["toggles"][key] = bool(state)
            if not state and self.handle:
                ptrs = self._resolve_live_ptrs()
                if key == "world_speed_enabled" and ptrs.get("wi"):
                    self.w_f32(ptrs["wi"] + OFF_WI_TIMEDILATION, 1.0)
                elif key == "custom_gravity_enabled" and ptrs.get("wi"):
                    self.w_f32(ptrs["wi"] + OFF_WI_GRAVITYZ, -2250.0)
                elif key == "custom_fov_enabled" and ptrs.get("pc"):
                    for o in (OFF_PC_FOVANGLE, OFF_PC_DESIREDFOV, OFF_PC_DEFAULTFOV):
                        self.w_f32(ptrs["pc"] + o, 85.0)
                elif key == "player_speed_enabled" and ptrs.get("pawn"):
                    self.w_f32(ptrs["pawn"] + OFF_ACTOR_CUSTOM_TIMEDIL, 1.0)
                elif key == "always_demon_evade" and ptrs.get("cb"):
                    self.set_bits(ptrs["cb"] + OFF_CB_DANTE_FLAGS, 0, 0x02)
                    self.w_f32(ptrs["cb"] + OFF_CB_DEMON_EVADE_DMG, 0.0)
                    self.w_f32(ptrs["cb"] + OFF_CB_DEMON_EVADE_STYLE, 0.0)
                elif key in ("damage_mult_enabled", "fast_kill") and ptrs.get("cb"):
                    if not self.config["toggles"]["fast_kill"] and not self.config["toggles"]["damage_mult_enabled"]:
                        self.w_f32(ptrs["cb"] + OFF_CB_STYLE_DMG_MULT, 1.0)
            self.save_config()
            return True

    def set_value(self, key: str, value) -> bool:
        with self.lock:
            if key not in self.config["values"]:
                return False
            self.config["values"][key] = value
            self.save_config()
            return True

    def set_hotkey(self, action: str, hotkey: str) -> bool:
        with self.lock:
            self.config["hotkeys"][action] = hotkey
            self.save_config()
            return True

    def set_sound_feedback(self, enabled: bool):
        with self.lock:
            self.config["sound_feedback"] = bool(enabled)
            self.save_config()

    def disable_all(self):
        with self.lock:
            for k, v in list(self.config["toggles"].items()):
                if v:
                    self.set_toggle(k, False)
            self.last_event = "All cheats disabled"

    def perform_action(self, action: str, payload=None) -> dict:
        payload = payload or {}
        with self.lock:
            if action == "disable_all":
                self.disable_all()
                return {"ok": True}

            if action == "apply_preset":
                preset = payload.get("preset")
                if preset == "god_sss":
                    for k in ("god_mode", "unlimited_health", "unlimited_devil_trigger", "unlimited_overdrive",
                              "sss_style_rank", "max_mission_score", "zero_damage_taken", "never_decrease_items"):
                        self.set_toggle(k, True)
                elif preset == "turbo_pro":
                    self.set_value("player_speed", 1.25)
                    self.set_value("world_speed", 1.20)
                    self.set_value("custom_fov", 98.0)
                    for k in ("player_speed_enabled", "world_speed_enabled", "custom_fov_enabled",
                              "infinite_air_evades", "no_style_decay"):
                        self.set_toggle(k, True)
                elif preset == "farm_fast":
                    for k in ("god_mode", "fast_kill", "unlim_red_orbs", "never_decrease_items", "freeze_mission_timer"):
                        self.set_toggle(k, True)
                elif preset == "disable_all":
                    self.disable_all()
                else:
                    return {"ok": False, "error": f"Unknown preset: {preset}"}
                return {"ok": True}

            if not self.handle:
                return {"ok": False, "error": "Game not attached"}

            ptrs = self._resolve_live_ptrs()
            pawn, trig, gi, prof, em = ptrs.get("pawn"), ptrs.get("trig"), ptrs.get("gi"), ptrs.get("profile"), ptrs.get("em")

            if action == "heal_full" and pawn:
                self.w_f32(pawn + OFF_PAWN_HEALTH, self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 1000.0)
            elif action == "refill_dt" and trig:
                self.w_f32(trig + OFF_TRIGGER_CUR, self.r_f32(trig + OFF_TRIGGER_MAX) or 1800.0)
            elif action == "extend_max_health" and pawn:
                new_m = min((self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 1000.0) + float(payload.get("amount", 100.0)), 5000.0)
                self.w_f32(pawn + OFF_PAWN_MAXHEALTH, new_m)
                self.w_f32(pawn + OFF_PAWN_HEALTH, new_m)
                self.set_stat_float("MAXHEALTH_PLAYER", new_m)
                self.set_stat_int("MAXHEALTH_SET", 1)
            elif action == "extend_max_dt" and trig:
                new_m = min((self.r_f32(trig + OFF_TRIGGER_MAX) or 1800.0) + float(payload.get("amount", 360.0)), 7200.0)
                self.w_f32(trig + OFF_TRIGGER_MAX, new_m)
                self.w_f32(trig + OFF_TRIGGER_CUR, new_m)
                self.set_stat_float("MAXTRIGGERPOINTS_PLAYER", new_m)
                self.set_stat_int("MAXTRIGGERPOINTS_SET", 1)
            elif action == "add_red_orbs":
                amt = int(payload.get("amount", 50000))
                self.set_stat_int("Orb_Red", max(0, self.get_stat_int("Orb_Red", 0) + amt))
                if amt > 0:
                    self.set_stat_int("REDORBS_ACQUIRED_TOTAL", self.get_stat_int("REDORBS_ACQUIRED_TOTAL", 0) + amt)
            elif action == "set_stat":
                name, val = payload.get("name"), int(payload.get("value", 0))
                if name:
                    self.set_stat_int(name, val)
                    if f"{name}_Persistent" in self.stat_ptr_cache:
                        self.set_stat_int(f"{name}_Persistent", val)
            elif action == "add_upgrade_points" and prof:
                amt = int(payload.get("amount", 10))
                self.w_i32(prof + OFF_PROFILE_POINTS_UNSPENT, max(0, (self.r_i32(prof + OFF_PROFILE_POINTS_UNSPENT) or 0) + amt))
                self.w_i32(prof + OFF_PROFILE_POINTS_TOTAL, max(0, (self.r_i32(prof + OFF_PROFILE_POINTS_TOTAL) or 0) + amt))
                self.w_i32(prof + OFF_PROFILE_POINTS_OTHER, max(0, (self.r_i32(prof + OFF_PROFILE_POINTS_OTHER) or 0) + amt))
            elif action == "reset_mission_timer" and gi:
                self.w_f32(gi + OFF_GI_MISSION_TIME, 0.0)
                self.w_f32(gi + OFF_GI_DAMAGE_TAKEN, 0.0)
            elif action == "enemies_one_hp" and em:
                for ep in self._get_active_enemies(em):
                    self.w_f32(ep + OFF_PAWN_HEALTH, 1.0)
            elif action == "unlock_difficulties":
                for st in ("OTHER_GAMECOMPLETED", "OTHER_GAMECOMPLETED_HARD", "OTHER_GAMECOMPLETED_SOS",
                           "OTHER_GAMECOMPLETED_DMD", "OTHER_GAMECOMPLETED_HOH"):
                    self.set_stat_int(st, 1)
                self.set_stat_int("MISSION_MISSIONSCOMPLETED_ALL", max(1, self.get_stat_int("MISSION_MISSIONSCOMPLETED_ALL", 0)))
            elif action == "save_pos" and pawn:
                slot = int(payload.get("slot", 0)) % 3
                lb = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                if lb:
                    self.saved_locations[slot] = struct.unpack("<fff", lb)
                    self.last_event = f"Saved position slot {slot + 1}"
            elif action == "load_pos" and pawn:
                slot = int(payload.get("slot", 0)) % 3
                loc = self.saved_locations[slot]
                if loc:
                    cur = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                    if cur:
                        self.undo_location = struct.unpack("<fff", cur)
                    self.wpm(pawn + OFF_ACTOR_LOCATION, struct.pack("<fff", *loc))
                    self.last_event = f"Teleported to slot {slot + 1}"
            elif action == "undo_teleport" and pawn and self.undo_location:
                self.wpm(pawn + OFF_ACTOR_LOCATION, struct.pack("<fff", *self.undo_location))
                self.last_event = "Undid teleport"
            elif action == "nudge_pos" and pawn:
                lb = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                if lb:
                    x, y, z = struct.unpack("<fff", lb)
                    self.wpm(pawn + OFF_ACTOR_LOCATION, struct.pack("<fff", x + float(payload.get("dx", 0)),
                             y + float(payload.get("dy", 0)), z + float(payload.get("dz", 0))))
            else:
                return {"ok": False, "error": f"Unknown or unavailable action: {action}"}
            return {"ok": True}

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "telemetry": dict(self.telemetry),
                "toggles": dict(self.config["toggles"]),
                "values": dict(self.config["values"]),
                "hotkeys": dict(self.config["hotkeys"]),
                "sound_feedback": bool(self.config.get("sound_feedback", True)),
                "counter_dec_available": "CounterDec_Instr" in self.addrs,
                "counter_dec_patched": bool(self.counter_dec_patched),
            }

    # --- Hotkey Polling & Background Loop ---
    def _poll_hotkeys(self):
        mods = set()
        if u32_dll.GetAsyncKeyState(0x11) & 0x8000: mods.add("CTRL")
        if u32_dll.GetAsyncKeyState(0x10) & 0x8000: mods.add("SHIFT")
        if u32_dll.GetAsyncKeyState(0x12) & 0x8000: mods.add("ALT")
        cur_mods = frozenset(mods)

        pressed = set()
        for action, hk_str in list(self.config["hotkeys"].items()):
            parsed = parse_hotkey(hk_str)
            if not parsed:
                continue
            req_mods, vk = parsed
            if (u32_dll.GetAsyncKeyState(vk) & 0x8000) and cur_mods == req_mods:
                pressed.add(action)
                if action not in self.prev_keys:
                    self._trigger_hotkey(action)
        self.prev_keys = pressed

    def _trigger_hotkey(self, action: str):
        if action == "disable_all":
            self.disable_all()
            self._beep(420, 90)
        elif action == "save_pos_0":
            self.perform_action("save_pos", {"slot": 0})
            self._beep(650, 60)
        elif action == "load_pos_0":
            self.perform_action("load_pos", {"slot": 0})
            self._beep(880, 60)
        elif action == "undo_teleport":
            self.perform_action("undo_teleport")
            self._beep(520, 60)
        elif action in self.config["toggles"]:
            nxt = not self.config["toggles"][action]
            self.set_toggle(action, nxt)
            self.last_event = f"{action}: {'ON' if nxt else 'OFF'}"
            self._beep(920 if nxt else 480, 55)

    def _beep(self, freq: int, dur: int):
        if self.config.get("sound_feedback"):
            threading.Thread(target=lambda: k32.Beep(freq, dur), daemon=True).start()

    def _loop(self):
        while self.running:
            try:
                self._poll_hotkeys()
                self._tick()
            except Exception as e:
                self.last_event = f"Error: {e}"
            time.sleep(0.05)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        with self.lock:
            self._detach()


def run_ipc(settings_path: str):
    """Stdio JSON-Lines IPC loop for DmC_Trainer.exe (auto-exits on stdin EOF)."""
    engine = DmCTrainerEngine(settings_path)
    engine.start()
    stop_evt = threading.Event()
    emit_lock = threading.Lock()
    last_sent = [None]

    def emit_state(force: bool = False):
        snap = engine.snapshot()
        line = json.dumps(snap, separators=(",", ":"))
        with emit_lock:
            if force or line != last_sent[0]:
                sys.stdout.write(line + "\n")
                sys.stdout.flush()
                last_sent[0] = line

    def stdin_reader():
        try:
            for raw in sys.stdin:
                raw = raw.strip()
                if not raw:
                    continue
                msg = json.loads(raw)
                cmd = msg.get("cmd")
                if cmd == "toggle":
                    engine.set_toggle(msg.get("key", ""), bool(msg.get("state", False)))
                elif cmd == "value":
                    k, val = msg.get("key", ""), msg.get("value")
                    with engine.lock:
                        cur = engine.config["values"].get(k)
                    if cur is not None:
                        engine.set_value(k, float(val) if isinstance(cur, float) else int(float(val)))
                elif cmd == "hotkey":
                    engine.set_hotkey(str(msg.get("action", "")), str(msg.get("hotkey", "")))
                elif cmd == "sound":
                    engine.set_sound_feedback(bool(msg.get("enabled", True)))
                elif cmd == "action":
                    res = engine.perform_action(str(msg.get("action", "")), msg.get("payload") or {})
                    if not res.get("ok") and res.get("error"):
                        engine.last_event = res["error"]
                elif cmd == "quit":
                    stop_evt.set()
                    break
                emit_state(force=True)
        except Exception:
            pass
        finally:
            stop_evt.set()

    threading.Thread(target=stdin_reader, daemon=True).start()
    emit_state(force=True)
    try:
        while not stop_evt.is_set():
            time.sleep(0.20)
            emit_state(force=False)
    finally:
        engine.stop()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="DmC Trainer Engine")
    p.add_argument("--ipc", action="store_true", help="Run stdio JSON-lines IPC loop")
    p.add_argument("--settings", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json"))
    args = p.parse_args()
    if args.ipc:
        run_ipc(args.settings)
