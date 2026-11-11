import ctypes
from ctypes import wintypes
import json
import os
import struct
import threading
import time
import psutil

# Win32 constants
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_ALL = PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION

TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
PAGE_EXECUTE_READWRITE = 0x40


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
u32_dll.GetAsyncKeyState.restype = ctypes.c_short


# Verified AOB signatures (1-hit unique in DMC-DevilMayCry.exe v1.0.8916.2)
AOB_SIGNATURES = {
    "GNames": ("8B 0D ?? ?? ?? ?? 8B 3D ?? ?? ?? ?? 83 C4 04 89 1C 85 ?? ?? ?? ?? 8B 43 08", 8),
    "GObjects": ("8B 15 ?? ?? ?? ?? 8B 0C B2 E8 ?? ?? ?? ?? A1 ?? ?? ?? ?? 46", 2),
    "GEngine": ("83 7E 20 00 74 3D 8B 0D ?? ?? ?? ?? 83 B9 5C 06 00 00 00", 8),
    "StatsMap": ("8D 4C 24 08 51 B9 ?? ?? ?? ?? E8 ?? ?? ?? ?? 8B 44 24 04 83 F8 FF", 6),
    "CounterDec": ("8B 44 24 14 50 E8 ?? ?? ?? ?? 83 C4 04 85 C0 74 0B ?? ?? ?? ?? ?? 74 04 ?? 89 48 0C 8B 4C 24 04", 24),
}

# Verified UE3 property offsets
OFF_UOBJECT_INDEX = 0x20
OFF_UOBJECT_OUTER = 0x24
OFF_UOBJECT_NAME = 0x28
OFF_UOBJECT_CLASS = 0x30

OFF_ENGINE_GAMEPLAYERS = 0x04DC
OFF_ENGINE_PROFILE = 0x07D4
OFF_PLAYER_ACTOR = 0x003C

OFF_ACTOR_LOCATION = 0x0050
OFF_ACTOR_DRAWSCALE = 0x0068
OFF_ACTOR_CUSTOM_TIMEDIL = 0x008C
OFF_ACTOR_COLLISION_FLAGS = 0x009C  # bCollideWorld = 0x40000000
OFF_ACTOR_WORLDINFO = 0x00D8

OFF_PC_PAWN = 0x0224
OFF_PC_FLAGS = 0x0234          # bGodMode = 0x00000002
OFF_PC_FOVANGLE = 0x03F8
OFF_PC_DESIREDFOV = 0x03FC
OFF_PC_DEFAULTFOV = 0x0400
OFF_PC_HUD = 0x0424
OFF_PC_DVPLAYER = 0x0808
OFF_PC_PLAYER_FLAGS = 0x080C   # m_UnlockAllUpgrades = 0x40, m_UnlockAllAttacks = 0x80

OFF_HUD_FLAGS = 0x0230         # bShowHUD = 0x00000002

OFF_PAWN_PHYS_FLAGS = 0x03A8   # bPhys_UseGravity = 0x00000004
OFF_PAWN_COMBAT_BEHAV = 0x0744
OFF_PAWN_COMBAT_DATA = 0x074C
OFF_PAWN_HEALTH = 0x0840
OFF_PAWN_MAXHEALTH = 0x0844
OFF_PAWN_DVFLAGS = 0x0940      # m_AerialEvadeAvailable = 0x00800000
OFF_PAWN_GLIDE_COUNT = 0x0B7C
OFF_PAWN_AICOORD = 0x0DB0
OFF_PAWN_PLAYER_PARAMS = 0x0E60
OFF_PAWN_TRIGGER_COMP = 0x0E8C
OFF_PAWN_DANTE_GAMEPLAY_PARAMS = 0x0FE0
OFF_PAWN_DANTE_MOVEMENT_PARAMS = 0x0FE4

OFF_TRIGGER_MAX = 0x0080
OFF_TRIGGER_CUR = 0x0084
OFF_TRIGGER_FLAGS = 0x0090     # m_bCheatInfinitePoints=0x10, m_PerkInfinite=0x20, m_bEndWithNoEnemies=0x40

OFF_CB_FLAGS = 0x0100          # m_CanTakeDamage=0x01, m_DieInOneHit=0x02
OFF_CB_CHEAT_SCALAR = 0x0118
OFF_CB_STYLE_DMG_MULT = 0x01C8
OFF_CB_PLAYER_FLAGS = 0x01CC   # m_Cheat_ForceDismemberKill=0x04
OFF_CB_CUR_OVERDRIVE = 0x0270
OFF_CB_MAX_OVERDRIVE = 0x0274
OFF_CB_DANTE_FLAGS = 0x027C    # m_DemonSkillEvadePayoffActive=0x02, m_Cheat_InfiniteOverdrive=0x04
OFF_CB_DEMON_EVADE_DMG = 0x0284
OFF_CB_DEMON_EVADE_STYLE = 0x0288

OFF_CD_GLOBAL_DMG = 0x0108
OFF_CD_FLAGS = 0x0118          # IgnoreAllDamage=0x01

OFF_WI_FLAGS = 0x04D4          # bPlayersOnly=0x0800, bSuspendAI=0x2000
OFF_WI_TIMEDILATION = 0x05F0
OFF_WI_GAME = 0x0678
OFF_WI_GRAVITYZ = 0x0680

OFF_GI_ENEMY_MGR = 0x0464
OFF_GI_STYLE_SYS = 0x04B8
OFF_GI_SHOP_SYS = 0x04CC
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
OFF_SM_RANK = 0x00B8

OFF_PROFILE_XP = 0x00EC
OFF_PROFILE_POINTS_TOTAL = 0x00F0
OFF_PROFILE_POINTS_UNSPENT = 0x00F4
OFF_PROFILE_POINTS_OTHER = 0x00FC

OFF_AI_COORD_NTFLAGS = 0x025C  # m_bGlobalAIDisable=0x02
OFF_AI_COORD_DVFLAGS = 0x02AC  # m_GlobalAttackDenial=0x01

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


def aob_find_first(buf: bytes, pattern_str: str) -> int | None:
    parts = pattern_str.split()
    fixed = [(i, int(p, 16)) for i, p in enumerate(parts) if p != "??"]
    plen = len(parts)
    if not fixed:
        return None
    ao, av = fixed[0]
    pos = 0
    blen = len(buf)
    anchor_b = bytes([av])
    while True:
        idx = buf.find(anchor_b, pos)
        if idx == -1:
            return None
        st = idx - ao
        if st >= 0 and st + plen <= blen:
            ok = True
            for fo, fv in fixed:
                if buf[st + fo] != fv:
                    ok = False
                    break
            if ok:
                return st
        pos = idx + 1


# Virtual key map for global hotkeys
VK_MAP = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "NUM0": 0x60, "NUM1": 0x61, "NUM2": 0x62, "NUM3": 0x63,
    "NUM4": 0x64, "NUM5": 0x65, "NUM6": 0x66, "NUM7": 0x67,
    "NUM8": 0x68, "NUM9": 0x69,
    "NUM*": 0x6A, "NUM+": 0x6B, "NUM-": 0x6D, "NUM.": 0x6E, "NUM/": 0x6F,
    "HOME": 0x24, "END": 0x23, "INS": 0x2D, "DEL": 0x2E,
    "PGUP": 0x21, "PGDN": 0x22,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
}
for _c in range(ord("A"), ord("Z") + 1):
    VK_MAP[chr(_c)] = _c

VK_CTRL = 0x11
VK_SHIFT = 0x10
VK_ALT = 0x12


def parse_hotkey(hk: str):
    if not hk:
        return None
    parts = [p.strip().upper() for p in hk.split("+") if p.strip()]
    mods = set()
    key = None
    for p in parts:
        if p in ("CTRL", "CONTROL"):
            mods.add("CTRL")
        elif p == "SHIFT":
            mods.add("SHIFT")
        elif p == "ALT":
            mods.add("ALT")
        elif p in VK_MAP:
            key = VK_MAP[p]
    if key is None:
        return None
    return (frozenset(mods), key)


DEFAULT_CONFIG = {
    "sound_feedback": True,
    "toggles": {
        "unlimited_health": False,
        "god_mode": False,
        "unlimited_devil_trigger": False,
        "no_dt_end_no_enemies": False,
        "unlimited_overdrive": False,
        "fast_kill": False,
        "damage_mult_enabled": False,
        "always_demon_evade": False,
        "force_dismember": False,
        "sss_style_rank": False,
        "no_style_decay": False,
        "style_mult_enabled": False,
        "max_mission_score": False,
        "zero_damage_taken": False,
        "freeze_mission_timer": False,
        "freeze_secret_timer": False,
        "unlimited_kablooey_darts": False,
        "never_decrease_items": False,
        "unlim_red_orbs": False,
        "unlim_gold_orbs": False,
        "unlim_copper_keys": False,
        "unlim_argent_keys": False,
        "unlim_gold_keys": False,
        "unlim_ivory_keys": False,
        "unlim_small_vs": False,
        "unlim_large_vs": False,
        "unlim_small_dts": False,
        "unlim_large_dts": False,
        "unlim_health_frag": False,
        "unlim_dt_frag": False,
        "unlim_upgrade_points": False,
        "infinite_air_jumps": False,
        "infinite_air_evades": False,
        "player_speed_enabled": False,
        "world_speed_enabled": False,
        "jump_height_enabled": False,
        "custom_gravity_enabled": False,
        "freeze_enemies_ai": False,
        "enemies_dont_attack": False,
        "freeze_world": False,
        "noclip_fly": False,
        "custom_fov_enabled": False,
        "hide_hud": False,
        "player_scale_enabled": False,
        "unlock_all_attacks": False,
    },
    "values": {
        "damage_multiplier": 5.0,
        "demon_evade_dmg_mult": 3.0,
        "style_multiplier": 5.0,
        "player_speed": 1.4,
        "world_speed": 1.2,
        "jump_height_mult": 1.8,
        "custom_gravity": -1100.0,
        "custom_fov": 100.0,
        "player_scale": 1.0,
        "red_orbs_lock": 999999,
        "gold_orbs_lock": 3,
        "keys_lock": 99,
        "stars_lock": 10,
        "frags_lock": 3,
        "upgrade_points_lock": 99,
    },
    "hotkeys": {
        "unlimited_health": "F1",
        "unlimited_devil_trigger": "F2",
        "fast_kill": "F3",
        "unlim_red_orbs": "F4",
        "unlim_gold_orbs": "F5",
        "unlim_copper_keys": "F6",
        "unlim_argent_keys": "F7",
        "unlim_gold_keys": "F8",
        "unlim_ivory_keys": "F9",
        "unlim_small_vs": "F10",
        "unlim_large_vs": "F11",
        "unlim_small_dts": "Ctrl+F1",
        "unlim_large_dts": "Ctrl+F2",
        "unlim_health_frag": "Ctrl+F3",
        "unlim_dt_frag": "Ctrl+F4",
        "god_mode": "Num1",
        "sss_style_rank": "Num2",
        "max_mission_score": "Num3",
        "never_decrease_items": "Num4",
        "unlimited_overdrive": "Num5",
        "freeze_mission_timer": "Num6",
        "freeze_secret_timer": "Num7",
        "infinite_air_jumps": "Num8",
        "freeze_enemies_ai": "Num9",
        "damage_mult_enabled": "Num0",
        "save_pos_0": "Num.",
        "load_pos_0": "Num+",
        "undo_teleport": "Num-",
        "disable_all": "Home",
    },
}


class DmCTrainerEngine:
    def __init__(self, settings_path: str):
        self.settings_path = settings_path
        self.lock = threading.RLock()
        self.config = self._load_config()
        self.running = False
        self.thread = None

        # Process / AOB state
        self.pid = None
        self.handle = None
        self.base = None
        self.mod_size = 0
        self.addrs = {}
        self.counter_dec_patched = False

        # Caches
        self.name_cache = {}
        self.name_ptrs = []
        self.gnames_num = 0
        self.stat_ptr_cache = {}
        self.stats_num_last = -1

        # Captured defaults for safe restore
        self.orig_jump_params = {}
        self.orig_style_global_mult = None
        self.orig_detonator_max_darts = None
        self.saved_locations = [None, None, None]
        self.undo_location = None

        # Hotkey debounce
        self.prev_keys = set()
        self.last_event = ""

        # Live telemetry snapshot
        self.telemetry = self._empty_telemetry()

    def _empty_telemetry(self):
        return {
            "attached": False,
            "pid": None,
            "in_game": False,
            "character": "None",
            "health": 0.0,
            "max_health": 0.0,
            "devil_trigger": 0.0,
            "max_devil_trigger": 0.0,
            "overdrive": 0.0,
            "max_overdrive": 0.0,
            "style_rank": 0,
            "style_points": 0.0,
            "mission_score": 0.0,
            "mission_time": 0.0,
            "damage_taken": 0.0,
            "red_orbs": 0,
            "gold_orbs": 0,
            "upgrade_points": 0,
            "xp": 0,
            "copper_keys": 0,
            "argent_keys": 0,
            "gold_keys": 0,
            "ivory_keys": 0,
            "small_vs": 0,
            "large_vs": 0,
            "small_dts": 0,
            "large_dts": 0,
            "blue_frags": 0,
            "purple_frags": 0,
            "active_enemies": 0,
            "location": [0.0, 0.0, 0.0],
            "fov": 85.0,
            "player_speed": 1.0,
            "world_speed": 1.0,
            "gravity": -2250.0,
            "saved_slots": [None, None, None],
            "last_event": self.last_event,
        }

    def _load_config(self):
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        if os.path.exists(self.settings_path):
            try:
                user = json.load(open(self.settings_path, "r", encoding="utf-8"))
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

    # --- Low-level Memory Helpers ---
    def rpm(self, addr: int, sz: int) -> bytes | None:
        if not self.handle or not addr or addr < 0x10000:
            return None
        buf = ctypes.create_string_buffer(sz)
        read = ctypes.c_size_t()
        if not k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), buf, sz, ctypes.byref(read)):
            return None
        if read.value < sz:
            return None
        return buf.raw

    def wpm(self, addr: int, data: bytes) -> bool:
        if not self.handle or not addr or addr < 0x10000:
            return False
        written = ctypes.c_size_t()
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), data, len(data), ctypes.byref(written)))

    def patch_bytes(self, addr: int, data: bytes) -> bool:
        if not self.handle or not addr:
            return False
        old_prot = wintypes.DWORD()
        if not k32.VirtualProtectEx(self.handle, ctypes.c_void_p(addr), len(data), PAGE_EXECUTE_READWRITE, ctypes.byref(old_prot)):
            return False
        ok = self.wpm(addr, data)
        tmp = wintypes.DWORD()
        k32.VirtualProtectEx(self.handle, ctypes.c_void_p(addr), len(data), old_prot.value, ctypes.byref(tmp))
        return ok

    def r_u32(self, addr: int) -> int | None:
        b = self.rpm(addr, 4)
        return struct.unpack("<I", b)[0] if b else None

    def r_i32(self, addr: int) -> int | None:
        b = self.rpm(addr, 4)
        return struct.unpack("<i", b)[0] if b else None

    def r_f32(self, addr: int) -> float | None:
        b = self.rpm(addr, 4)
        return struct.unpack("<f", b)[0] if b else None

    def w_i32(self, addr: int, val: int) -> bool:
        return self.wpm(addr, struct.pack("<i", int(val)))

    def w_u32(self, addr: int, val: int) -> bool:
        return self.wpm(addr, struct.pack("<I", int(val) & 0xFFFFFFFF))

    def w_f32(self, addr: int, val: float) -> bool:
        return self.wpm(addr, struct.pack("<f", float(val)))

    def set_bit(self, addr: int, mask: int, enabled: bool) -> bool:
        cur = self.r_u32(addr)
        if cur is None:
            return False
        nxt = (cur | mask) if enabled else (cur & ~mask)
        if nxt != cur:
            return self.w_u32(addr, nxt)
        return True

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
        self.addrs = {}
        self.counter_dec_patched = False
        self.name_cache.clear()
        self.name_ptrs = []
        self.gnames_num = 0
        self.stat_ptr_cache.clear()
        self.stats_num_last = -1
        self.orig_jump_params.clear()
        self.orig_style_global_mult = None
        self.orig_detonator_max_darts = None
        self.telemetry = self._empty_telemetry()

    def _try_attach(self) -> bool:
        target_pid = None
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if p.info["name"] and p.info["name"].lower() == "dmc-devilmaycry.exe":
                    target_pid = p.info["pid"]
                    break
            except Exception:
                continue
        if not target_pid:
            return False

        snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, target_pid)
        if not snap or snap == wintypes.HANDLE(-1).value:
            return False
        me = MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(MODULEENTRY32W)
        base, size = None, 0
        if k32.Module32FirstW(snap, ctypes.byref(me)):
            while True:
                if me.szModule.lower() == "dmc-devilmaycry.exe":
                    base = ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value
                    size = me.modBaseSize
                    break
                if not k32.Module32NextW(snap, ctypes.byref(me)):
                    break
        k32.CloseHandle(snap)
        if not base:
            return False

        h = k32.OpenProcess(PROCESS_ALL, False, target_pid)
        if not h:
            return False

        self.pid = target_pid
        self.handle = h
        self.base = base
        self.mod_size = size

        if not self._scan_aobs():
            self._detach()
            return False
        return True

    def _scan_aobs(self) -> bool:
        # Read PE header to find .text bounds
        dos = self.rpm(self.base, 0x100)
        if not dos:
            return False
        pe_off = struct.unpack_from("<I", dos, 0x3C)[0]
        hdr = self.rpm(self.base + pe_off, 0x120)
        if not hdr:
            return False
        opt_sz = struct.unpack_from("<H", hdr, 20)[0]
        sec_off = 24 + opt_sz
        text_va, text_sz = struct.unpack_from("<II", hdr, sec_off + 12)  # VirtualAddress, SizeOfRawData
        # Read .text in 4MB chunks
        chunks = []
        chunk_sz = 0x400000
        for off in range(0, text_sz, chunk_sz):
            b = self.rpm(self.base + text_va + off, min(chunk_sz, text_sz - off))
            if not b:
                return False
            chunks.append(b)
        text = b"".join(chunks)

        resolved = {}
        for name, (pat, imm_off) in AOB_SIGNATURES.items():
            pos = aob_find_first(text, pat)
            if pos is None:
                if name == "CounterDec":
                    continue
                return False
            if name == "CounterDec":
                # Only enable CounterDec patch if instruction isn't already hooked by another trainer (E9 jmp)
                if text[pos + 17] == 0x8B:
                    resolved["CounterDec_Instr"] = self.base + text_va + pos + imm_off
            else:
                resolved[name] = struct.unpack_from("<I", text, pos + imm_off)[0]

        self.addrs = resolved
        if "CounterDec_Instr" in self.addrs:
            cur_b = self.rpm(self.addrs["CounterDec_Instr"], 1)
            self.counter_dec_patched = (cur_b == b"\x90")
        else:
            self.counter_dec_patched = False
        return True

    # --- UE3 Reflection Helpers ---
    def _refresh_gnames(self):
        gn_addr = self.addrs.get("GNames")
        if not gn_addr:
            return
        data = self.r_u32(gn_addr)
        num = self.r_u32(gn_addr + 4)
        if not data or not num or num > 1000000:
            return
        if num != self.gnames_num:
            raw = self.rpm(data, num * 4)
            if raw:
                self.name_ptrs = struct.unpack(f"<{num}I", raw)
                self.gnames_num = num

    def get_name(self, idx: int) -> str:
        if idx in self.name_cache:
            return self.name_cache[idx]
        if idx < 0 or idx >= self.gnames_num:
            return ""
        p = self.name_ptrs[idx]
        if not p:
            return ""
        entry = self.rpm(p, 144)
        if not entry or len(entry) < 18:
            return ""
        idx_flags = struct.unpack_from("<I", entry, 8)[0]
        raw = entry[16:]
        if idx_flags & 1:
            end = 0
            while end + 1 < len(raw) and (raw[end] != 0 or raw[end + 1] != 0):
                end += 2
            res = raw[:end].decode("utf-16le", "ignore")
        else:
            res = raw.split(b"\x00")[0].decode("latin1", "ignore")
        self.name_cache[idx] = res
        return res

    def get_obj_class_name(self, obj_ptr: int) -> str:
        if not obj_ptr or obj_ptr < 0x10000:
            return ""
        cls = self.r_u32(obj_ptr + OFF_UOBJECT_CLASS)
        if not cls or cls < 0x10000:
            return ""
        nidx = self.r_i32(cls + OFF_UOBJECT_NAME)
        if nidx is None:
            return ""
        return self.get_name(nidx)

    def _refresh_stats_cache(self):
        sm_addr = self.addrs.get("StatsMap")
        if not sm_addr:
            return
        hdr = self.rpm(sm_addr, 12)
        if not hdr:
            return
        arr_data, arr_num, _ = struct.unpack("<III", hdr)
        if not arr_data or arr_num == 0 or arr_num > 8000:
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
            if stat_ptr and stat_ptr >= 0x10000 and nnum == 0:
                sname = self.get_name(nidx)
                if sname:
                    cache[sname] = stat_ptr
        self.stat_ptr_cache = cache
        self.stats_num_last = arr_num

    def get_stat_int(self, stat_name: str, default: int = 0) -> int:
        p = self.stat_ptr_cache.get(stat_name)
        if not p:
            return default
        v = self.r_i32(p + OFF_STAT_VALUE)
        return v if v is not None else default

    def set_stat_int(self, stat_name: str, value: int) -> bool:
        p = self.stat_ptr_cache.get(stat_name)
        if not p:
            return False
        return self.w_i32(p + OFF_STAT_VALUE, int(value))

    def get_stat_float(self, stat_name: str, default: float = 0.0) -> float:
        p = self.stat_ptr_cache.get(stat_name)
        if not p:
            return default
        v = self.r_f32(p + OFF_STAT_VALUE)
        return v if v is not None else default

    def set_stat_float(self, stat_name: str, value: float) -> bool:
        p = self.stat_ptr_cache.get(stat_name)
        if not p:
            return False
        return self.w_f32(p + OFF_STAT_VALUE, float(value))

    # --- Live Pointers ---
    def _resolve_live_ptrs(self):
        ge_ptr = self.addrs.get("GEngine")
        ge = self.r_u32(ge_ptr) if ge_ptr else None
        if not ge:
            return {}
        profile = self.r_u32(ge + OFF_ENGINE_PROFILE)
        gp_data = self.r_u32(ge + OFF_ENGINE_GAMEPLAYERS)
        lp = self.r_u32(gp_data) if gp_data else None
        pc = self.r_u32(lp + OFF_PLAYER_ACTOR) if lp else None

        pc_cls = self.get_obj_class_name(pc) if pc else ""
        in_game = pc_cls.startswith("DVPlayerController_")
        pawn = self.r_u32(pc + OFF_PC_DVPLAYER) if (pc and in_game) else None
        if pawn and not self.get_obj_class_name(pawn).startswith("DVPawn_"):
            pawn = None
        if not pawn:
            in_game = False

        wi = self.r_u32(pc + OFF_ACTOR_WORLDINFO) if (pc and in_game) else None
        gi = self.r_u32(wi + OFF_WI_GAME) if wi else None
        cb = self.r_u32(pawn + OFF_PAWN_COMBAT_BEHAV) if pawn else None
        cd = self.r_u32(pawn + OFF_PAWN_COMBAT_DATA) if pawn else None
        trig = self.r_u32(pawn + OFF_PAWN_TRIGGER_COMP) if pawn else None
        em = self.r_u32(gi + OFF_GI_ENEMY_MGR) if gi else None
        ss = self.r_u32(gi + OFF_GI_STYLE_SYS) if gi else None
        sm = self.r_u32(gi + OFF_GI_SECRET_MGR) if gi else None
        ai = self.r_u32(pawn + OFF_PAWN_AICOORD) if pawn else None
        hud = self.r_u32(pc + OFF_PC_HUD) if pc else None

        return {
            "ge": ge, "profile": profile, "lp": lp, "pc": pc,
            "in_game": in_game, "pawn": pawn, "pawn_cls": self.get_obj_class_name(pawn) if pawn else "None",
            "wi": wi, "gi": gi, "cb": cb, "cd": cd, "trig": trig,
            "em": em, "ss": ss, "sm": sm, "ai": ai, "hud": hud,
        }

    def _get_active_enemies(self, em_ptr: int) -> list[int]:
        if not em_ptr:
            return []
        hdr = self.rpm(em_ptr + OFF_EM_ACTIVE_ENEMIES, 8)
        if not hdr:
            return []
        data, num = struct.unpack("<II", hdr)
        if not data or num == 0 or num > 200:
            return []
        raw = self.rpm(data, num * 4)
        if not raw:
            return []
        return [p for p in struct.unpack(f"<{num}I", raw) if p and p >= 0x10000]

    def _get_jump_param_objects(self, pawn: int, pawn_cls: str) -> list[int]:
        if not pawn or "Dante" not in pawn_cls:
            return []
        mp = self.r_u32(pawn + OFF_PAWN_DANTE_MOVEMENT_PARAMS)
        if not mp:
            return []
        objs = []
        seen = set()
        for off in (OFF_MOV_PLAYMODE_NORMAL, OFF_MOV_PLAYMODE_DEMON, OFF_MOV_PLAYMODE_ANGEL):
            pm = self.r_u32(mp + off)
            if pm:
                j = self.r_u32(pm + OFF_PLAYMODE_JUMP)
                if j and j not in seen:
                    seen.add(j)
                    objs.append(j)
        return objs

    # --- Apply Cheats & Update Telemetry ---
    def _tick(self):
        with self.lock:
            if not self.handle:
                if not self._try_attach():
                    self.telemetry = self._empty_telemetry()
                    return
            else:
                # Verify process still alive
                if self.r_u32(self.base) is None:
                    self._detach()
                    return

            self._refresh_gnames()
            self._refresh_stats_cache()
            ptrs = self._resolve_live_ptrs()

            toggles = self.config["toggles"]
            vals = self.config["values"]

            # 1. Native Counter_Decrement patch (works anywhere once attached)
            want_patch = bool(toggles.get("never_decrease_items"))
            if want_patch != self.counter_dec_patched and self.addrs.get("CounterDec_Instr"):
                if self.patch_bytes(self.addrs["CounterDec_Instr"], b"\x90" if want_patch else b"\x49"):
                    self.counter_dec_patched = want_patch

            # 2. Inventory & Stats locks (NTGameStatsManager)
            if toggles.get("unlim_red_orbs"):
                v = int(vals["red_orbs_lock"])
                self.set_stat_int("Orb_Red", v)
                if self.get_stat_int("REDORBS_ACQUIRED_TOTAL", 0) < v:
                    self.set_stat_int("REDORBS_ACQUIRED_TOTAL", v)
            if toggles.get("unlim_gold_orbs"):
                v = int(vals["gold_orbs_lock"])
                self.set_stat_int("Orb_Gold", v)
                self.set_stat_int("Orb_Gold_Persistent", v)
            if toggles.get("unlim_copper_keys"):
                self.set_stat_int("MundusKeyBronze", int(vals["keys_lock"]))
            if toggles.get("unlim_argent_keys"):
                self.set_stat_int("MundusKeySilver", int(vals["keys_lock"]))
            if toggles.get("unlim_gold_keys"):
                self.set_stat_int("MundusKeyGold", int(vals["keys_lock"]))
            if toggles.get("unlim_ivory_keys"):
                self.set_stat_int("MundusKeyIvory", int(vals["keys_lock"]))
            if toggles.get("unlim_small_vs"):
                v = int(vals["stars_lock"])
                self.set_stat_int("VitalStar_Small", v)
                self.set_stat_int("VitalStar_Small_Persistent", v)
            if toggles.get("unlim_large_vs"):
                v = int(vals["stars_lock"])
                self.set_stat_int("VitalStar_Large", v)
                self.set_stat_int("VitalStar_Large_Persistent", v)
            if toggles.get("unlim_small_dts"):
                v = int(vals["stars_lock"])
                self.set_stat_int("DevilTriggerStar_Small", v)
                self.set_stat_int("DevilTriggerStar_Small_Persistent", v)
            if toggles.get("unlim_large_dts"):
                v = int(vals["stars_lock"])
                self.set_stat_int("DevilTriggerStar_Large", v)
                self.set_stat_int("DevilTriggerStar_Large_Persistent", v)
            if toggles.get("unlim_health_frag"):
                self.set_stat_int("OrbFragment_Blue", int(vals["frags_lock"]))
            if toggles.get("unlim_dt_frag"):
                self.set_stat_int("OrbFragment_Purple", int(vals["frags_lock"]))

            # 3. Profile locks (Upgrade Points)
            prof = ptrs.get("profile")
            if prof and toggles.get("unlim_upgrade_points"):
                up = int(vals["upgrade_points_lock"])
                cur_u = self.r_i32(prof + OFF_PROFILE_POINTS_UNSPENT)
                if cur_u is not None and cur_u < up:
                    diff = up - cur_u
                    self.w_i32(prof + OFF_PROFILE_POINTS_UNSPENT, up)
                    tot = self.r_i32(prof + OFF_PROFILE_POINTS_TOTAL) or 0
                    oth = self.r_i32(prof + OFF_PROFILE_POINTS_OTHER) or 0
                    self.w_i32(prof + OFF_PROFILE_POINTS_TOTAL, tot + diff)
                    self.w_i32(prof + OFF_PROFILE_POINTS_OTHER, oth + diff)

            # 4. In-game Player / Combat / Style / Movement / World Cheats
            in_game = ptrs.get("in_game", False)
            pawn = ptrs.get("pawn")
            pc = ptrs.get("pc")
            cb = ptrs.get("cb")
            cd = ptrs.get("cd")
            trig = ptrs.get("trig")
            wi = ptrs.get("wi")
            gi = ptrs.get("gi")
            ss = ptrs.get("ss")
            sm = ptrs.get("sm")
            ai = ptrs.get("ai")
            hud = ptrs.get("hud")
            em = ptrs.get("em")

            enemies = self._get_active_enemies(em) if in_game else []

            if in_game and pawn:
                # Health & God Mode
                mhp = self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 1000.0
                if toggles.get("unlimited_health") or toggles.get("god_mode"):
                    self.w_f32(pawn + OFF_PAWN_HEALTH, mhp)

                god = bool(toggles.get("god_mode"))
                if pc:
                    self.set_bit(pc + OFF_PC_FLAGS, 0x00000002, god)
                if cb:
                    self.set_bit(cb + OFF_CB_FLAGS, 0x00000001, not god)
                if cd:
                    self.set_bit(cd + OFF_CD_FLAGS, 0x00000001, god)

                # Devil Trigger
                if trig:
                    mdt = self.r_f32(trig + OFF_TRIGGER_MAX) or 1800.0
                    unlim_dt = bool(toggles.get("unlimited_devil_trigger"))
                    self.set_bit(trig + OFF_TRIGGER_FLAGS, 0x10, unlim_dt)
                    self.set_bit(trig + OFF_TRIGGER_FLAGS, 0x20, unlim_dt)
                    if unlim_dt:
                        self.w_f32(trig + OFF_TRIGGER_CUR, mdt)
                    self.set_bit(trig + OFF_TRIGGER_FLAGS, 0x40, not bool(toggles.get("no_dt_end_no_enemies")))

                # Combat Behaviour (Overdrive, Fast Kill, Damage Mult, Demon Evade, Dismember)
                if cb:
                    unlim_od = bool(toggles.get("unlimited_overdrive"))
                    if "Dante" in ptrs["pawn_cls"]:
                        self.set_bit(cb + OFF_CB_DANTE_FLAGS, 0x04, unlim_od)
                        if unlim_od:
                            max_od = self.r_f32(cb + OFF_CB_MAX_OVERDRIVE) or 100.0
                            self.w_f32(cb + OFF_CB_CUR_OVERDRIVE, max_od)
                        ev_buff = bool(toggles.get("always_demon_evade"))
                        self.set_bit(cb + OFF_CB_DANTE_FLAGS, 0x02, ev_buff)
                        if ev_buff:
                            self.w_f32(cb + OFF_CB_DEMON_EVADE_DMG, float(vals["demon_evade_dmg_mult"]))
                            self.w_f32(cb + OFF_CB_DEMON_EVADE_STYLE, float(vals["demon_evade_dmg_mult"]))

                    self.set_bit(cb + OFF_CB_PLAYER_FLAGS, 0x04, bool(toggles.get("force_dismember")))

                    if toggles.get("fast_kill"):
                        self.w_f32(cb + OFF_CB_STYLE_DMG_MULT, 99999.0)
                    elif toggles.get("damage_mult_enabled"):
                        self.w_f32(cb + OFF_CB_STYLE_DMG_MULT, float(vals["damage_multiplier"]))
                    else:
                        # Reset to 1.0 only if previously boosted above normal style scaling (> 2.5)
                        cur_mult = self.r_f32(cb + OFF_CB_STYLE_DMG_MULT)
                        if cur_mult is not None and cur_mult > 2.5:
                            self.w_f32(cb + OFF_CB_STYLE_DMG_MULT, 1.0)

                # Set m_DieInOneHit on active enemies when fast_kill is enabled
                die_one = bool(toggles.get("fast_kill"))
                for ep in enemies:
                    ecb = self.r_u32(ep + OFF_PAWN_COMBAT_BEHAV)
                    if ecb:
                        self.set_bit(ecb + OFF_CB_FLAGS, 0x02, die_one)

                # Style System
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

                # GameInfo (Damage Taken & Mission Timer)
                if gi:
                    if toggles.get("zero_damage_taken") or toggles.get("god_mode"):
                        self.w_f32(gi + OFF_GI_DAMAGE_TAKEN, 0.0)
                    if toggles.get("freeze_mission_timer"):
                        self.w_f32(gi + OFF_GI_MISSION_TIME, 0.0)

                # Secret Mission Manager
                if sm and toggles.get("freeze_secret_timer"):
                    self.w_f32(sm + OFF_SM_TIMER, 99.0)
                    self.w_i32(sm + OFF_SM_DISPLAY_TIMER, 99)

                # Kablooey Unlimited Darts
                if "Dante" in ptrs["pawn_cls"]:
                    gp = self.r_u32(pawn + OFF_PAWN_DANTE_GAMEPLAY_PARAMS)
                    det = self.r_u32(gp + OFF_GP_DETONATOR_PARAMS) if gp else None
                    if det:
                        if self.orig_detonator_max_darts is None:
                            self.orig_detonator_max_darts = self.r_i32(det + OFF_DETONATOR_MAX_DARTS) or 4
                        target_darts = 99 if toggles.get("unlimited_kablooey_darts") else self.orig_detonator_max_darts
                        if self.r_i32(det + OFF_DETONATOR_MAX_DARTS) != target_darts:
                            self.w_i32(det + OFF_DETONATOR_MAX_DARTS, target_darts)

                # Movement: Air Evades / Glide, Infinite Air Jumps, Jump Height, Speed
                if toggles.get("infinite_air_evades"):
                    self.set_bit(pawn + OFF_PAWN_DVFLAGS, 0x00800000, True)
                    self.w_i32(pawn + OFF_PAWN_GLIDE_COUNT, 0)

                for j_obj in self._get_jump_param_objects(pawn, ptrs["pawn_cls"]):
                    if j_obj not in self.orig_jump_params:
                        self.orig_jump_params[j_obj] = {
                            "cnt": self.r_i32(j_obj + OFF_JUMP_MAX_COUNT) or 1,
                            "min_h": self.r_f32(j_obj + OFF_JUMP_MIN_H) or 250.0,
                            "max_h": self.r_f32(j_obj + OFF_JUMP_MAX_H) or 425.0,
                            "amin_h": self.r_f32(j_obj + OFF_JUMP_AIR_MIN_H) or 100.0,
                            "amax_h": self.r_f32(j_obj + OFF_JUMP_AIR_MAX_H) or 150.0,
                        }
                    orig = self.orig_jump_params[j_obj]
                    want_cnt = 999 if toggles.get("infinite_air_jumps") else orig["cnt"]
                    if self.r_i32(j_obj + OFF_JUMP_MAX_COUNT) != want_cnt:
                        self.w_i32(j_obj + OFF_JUMP_MAX_COUNT, want_cnt)
                    jm = float(vals["jump_height_mult"]) if toggles.get("jump_height_enabled") else 1.0
                    self.w_f32(j_obj + OFF_JUMP_MIN_H, orig["min_h"] * jm)
                    self.w_f32(j_obj + OFF_JUMP_MAX_H, orig["max_h"] * jm)
                    self.w_f32(j_obj + OFF_JUMP_AIR_MIN_H, orig["amin_h"] * jm)
                    self.w_f32(j_obj + OFF_JUMP_AIR_MAX_H, orig["amax_h"] * jm)

                if toggles.get("player_speed_enabled"):
                    self.w_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL, float(vals["player_speed"]))
                elif self.r_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL) not in (None, 1.0, 1.05, 1.2):
                    cur_ps = self.r_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL)
                    if cur_ps is not None and (cur_ps < 0.99 or cur_ps > 1.21):
                        self.w_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL, 1.0)

                # Noclip / Float
                fly_on = bool(toggles.get("noclip_fly"))
                self.set_bit(pawn + OFF_ACTOR_COLLISION_FLAGS, 0x40000000, not fly_on)
                self.set_bit(pawn + OFF_PAWN_PHYS_FLAGS, 0x00000004, not fly_on)

                # Player Scale
                target_scale = float(vals["player_scale"]) if toggles.get("player_scale_enabled") else 1.0
                cur_sc = self.r_f32(pawn + OFF_ACTOR_DRAWSCALE)
                if cur_sc is not None and abs(cur_sc - target_scale) > 0.01:
                    self.w_f32(pawn + OFF_ACTOR_DRAWSCALE, target_scale)

                # WorldInfo (World Speed, Gravity, Freeze World, Freeze AI)
                if wi:
                    if toggles.get("world_speed_enabled"):
                        self.w_f32(wi + OFF_WI_TIMEDILATION, float(vals["world_speed"]))
                    elif abs((self.r_f32(wi + OFF_WI_TIMEDILATION) or 1.0) - 1.0) > 0.01:
                        # Only reset if not inside an engine hitstop? Keep simple: reset if user disabled
                        pass

                    if toggles.get("custom_gravity_enabled"):
                        self.w_f32(wi + OFF_WI_GRAVITYZ, float(vals["custom_gravity"]))

                    self.set_bit(wi + OFF_WI_FLAGS, 0x00000800, bool(toggles.get("freeze_world")))
                    self.set_bit(wi + OFF_WI_FLAGS, 0x00002000, bool(toggles.get("freeze_enemies_ai")))

                if ai:
                    self.set_bit(ai + OFF_AI_COORD_NTFLAGS, 0x02, bool(toggles.get("freeze_enemies_ai")))
                    self.set_bit(ai + OFF_AI_COORD_DVFLAGS, 0x01, bool(toggles.get("enemies_dont_attack")))

                # Camera FOV, Unlock Flags, Hide HUD
                if pc:
                    if toggles.get("custom_fov_enabled"):
                        fov = float(vals["custom_fov"])
                        self.w_f32(pc + OFF_PC_FOVANGLE, fov)
                        self.w_f32(pc + OFF_PC_DESIREDFOV, fov)
                        self.w_f32(pc + OFF_PC_DEFAULTFOV, fov)
                    if toggles.get("unlock_all_attacks"):
                        self.set_bit(pc + OFF_PC_PLAYER_FLAGS, 0x40, True)
                        self.set_bit(pc + OFF_PC_PLAYER_FLAGS, 0x80, True)

                if hud:
                    self.set_bit(hud + OFF_HUD_FLAGS, 0x02, not bool(toggles.get("hide_hud")))

            # 5. Update Telemetry
            loc = [0.0, 0.0, 0.0]
            if pawn:
                lb = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                if lb:
                    loc = [round(x, 1) for x in struct.unpack("<fff", lb)]

            self.telemetry = {
                "attached": True,
                "pid": self.pid,
                "in_game": in_game,
                "character": ptrs["pawn_cls"].replace("DVPawn_", ""),
                "health": round(self.r_f32(pawn + OFF_PAWN_HEALTH) or 0.0, 1) if pawn else 0.0,
                "max_health": round(self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 0.0, 1) if pawn else 0.0,
                "devil_trigger": round(self.r_f32(trig + OFF_TRIGGER_CUR) or 0.0, 1) if trig else 0.0,
                "max_devil_trigger": round(self.r_f32(trig + OFF_TRIGGER_MAX) or 0.0, 1) if trig else 0.0,
                "overdrive": round(self.r_f32(cb + OFF_CB_CUR_OVERDRIVE) or 0.0, 1) if (cb and "Dante" in ptrs["pawn_cls"]) else 0.0,
                "max_overdrive": round(self.r_f32(cb + OFF_CB_MAX_OVERDRIVE) or 0.0, 1) if (cb and "Dante" in ptrs["pawn_cls"]) else 0.0,
                "style_rank": self.r_i32(ss + OFF_STYLE_RANK) or 0 if ss else 0,
                "style_points": round(self.r_f32(ss + OFF_STYLE_POINTS) or 0.0, 1) if ss else 0.0,
                "mission_score": round(self.r_f32(ss + OFF_STYLE_MISSION_SCORE) or 0.0, 0) if ss else 0.0,
                "mission_time": round(self.r_f32(gi + OFF_GI_MISSION_TIME) or 0.0, 1) if gi else 0.0,
                "damage_taken": round(self.r_f32(gi + OFF_GI_DAMAGE_TAKEN) or 0.0, 1) if gi else 0.0,
                "red_orbs": self.get_stat_int("Orb_Red", 0),
                "gold_orbs": self.get_stat_int("Orb_Gold", 0),
                "upgrade_points": self.r_i32(prof + OFF_PROFILE_POINTS_UNSPENT) or 0 if prof else 0,
                "xp": self.r_i32(prof + OFF_PROFILE_XP) or 0 if prof else 0,
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
                "active_enemies": len(enemies),
                "location": loc,
                "fov": round(self.r_f32(pc + OFF_PC_FOVANGLE) or 85.0, 1) if pc else 85.0,
                "player_speed": round(self.r_f32(pawn + OFF_ACTOR_CUSTOM_TIMEDIL) or 1.0, 2) if pawn else 1.0,
                "world_speed": round(self.r_f32(wi + OFF_WI_TIMEDILATION) or 1.0, 2) if wi else 1.0,
                "gravity": round(self.r_f32(wi + OFF_WI_GRAVITYZ) or -2250.0, 0) if wi else -2250.0,
                "saved_slots": [([round(v, 1) for v in s] if s else None) for s in self.saved_locations],
                "last_event": self.last_event,
            }

    # --- Immediate Value Reset Helpers & Actions ---
    def set_toggle(self, key: str, state: bool):
        with self.lock:
            if key not in self.config["toggles"]:
                return False
            self.config["toggles"][key] = bool(state)
            # Cleanly restore one-shot resets when turning off
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
                    self.set_bit(ptrs["cb"] + OFF_CB_DANTE_FLAGS, 0x02, False)
                    self.w_f32(ptrs["cb"] + OFF_CB_DEMON_EVADE_DMG, 0.0)
                    self.w_f32(ptrs["cb"] + OFF_CB_DEMON_EVADE_STYLE, 0.0)
                elif key in ("damage_mult_enabled", "fast_kill") and ptrs.get("cb"):
                    if not self.config["toggles"]["fast_kill"] and not self.config["toggles"]["damage_mult_enabled"]:
                        self.w_f32(ptrs["cb"] + OFF_CB_STYLE_DMG_MULT, 1.0)
            self.save_config()
            return True

    def set_value(self, key: str, value):
        with self.lock:
            if key not in self.config["values"]:
                return False
            self.config["values"][key] = value
            self.save_config()
            return True

    def set_hotkey(self, action: str, hotkey: str):
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
            for k in list(self.config["toggles"].keys()):
                if self.config["toggles"][k]:
                    self.set_toggle(k, False)
            self.last_event = "All cheats disabled"

    def perform_action(self, action: str, payload=None):
        with self.lock:
            if not self.handle:
                return {"ok": False, "error": "Game not attached"}
            ptrs = self._resolve_live_ptrs()
            pawn = ptrs.get("pawn")
            trig = ptrs.get("trig")
            gi = ptrs.get("gi")
            ss = ptrs.get("ss")
            prof = ptrs.get("profile")
            em = ptrs.get("em")

            if action == "heal_full" and pawn:
                mhp = self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 1000.0
                self.w_f32(pawn + OFF_PAWN_HEALTH, mhp)
            elif action == "refill_dt" and trig:
                mdt = self.r_f32(trig + OFF_TRIGGER_MAX) or 1800.0
                self.w_f32(trig + OFF_TRIGGER_CUR, mdt)
            elif action == "extend_max_health" and pawn:
                amt = float((payload or {}).get("amount", 100.0))
                cur_m = self.r_f32(pawn + OFF_PAWN_MAXHEALTH) or 1000.0
                new_m = min(cur_m + amt, 5000.0)
                self.w_f32(pawn + OFF_PAWN_MAXHEALTH, new_m)
                self.w_f32(pawn + OFF_PAWN_HEALTH, new_m)
                self.set_stat_float("MAXHEALTH_PLAYER", new_m)
                self.set_stat_int("MAXHEALTH_SET", 1)
            elif action == "extend_max_dt" and trig:
                amt = float((payload or {}).get("amount", 360.0))
                cur_m = self.r_f32(trig + OFF_TRIGGER_MAX) or 1800.0
                new_m = min(cur_m + amt, 7200.0)
                self.w_f32(trig + OFF_TRIGGER_MAX, new_m)
                self.w_f32(trig + OFF_TRIGGER_CUR, new_m)
                self.set_stat_float("MAXTRIGGERPOINTS_PLAYER", new_m)
                self.set_stat_int("MAXTRIGGERPOINTS_SET", 1)
            elif action == "add_red_orbs":
                amt = int((payload or {}).get("amount", 50000))
                cur = self.get_stat_int("Orb_Red", 0)
                self.set_stat_int("Orb_Red", max(0, cur + amt))
                tot = self.get_stat_int("REDORBS_ACQUIRED_TOTAL", 0)
                if amt > 0:
                    self.set_stat_int("REDORBS_ACQUIRED_TOTAL", tot + amt)
            elif action == "set_stat":
                name = (payload or {}).get("name")
                val = int((payload or {}).get("value", 0))
                if name:
                    self.set_stat_int(name, val)
                    if f"{name}_Persistent" in self.stat_ptr_cache:
                        self.set_stat_int(f"{name}_Persistent", val)
            elif action == "add_upgrade_points" and prof:
                amt = int((payload or {}).get("amount", 10))
                u = self.r_i32(prof + OFF_PROFILE_POINTS_UNSPENT) or 0
                tot = self.r_i32(prof + OFF_PROFILE_POINTS_TOTAL) or 0
                oth = self.r_i32(prof + OFF_PROFILE_POINTS_OTHER) or 0
                self.w_i32(prof + OFF_PROFILE_POINTS_UNSPENT, max(0, u + amt))
                self.w_i32(prof + OFF_PROFILE_POINTS_TOTAL, max(0, tot + amt))
                self.w_i32(prof + OFF_PROFILE_POINTS_OTHER, max(0, oth + amt))
            elif action == "reset_mission_timer" and gi:
                self.w_f32(gi + OFF_GI_MISSION_TIME, 0.0)
                self.w_f32(gi + OFF_GI_DAMAGE_TAKEN, 0.0)
            elif action == "enemies_one_hp" and em:
                for ep in self._get_active_enemies(em):
                    self.w_f32(ep + OFF_PAWN_HEALTH, 1.0)
            elif action == "unlock_difficulties":
                for st in ("OTHER_GAMECOMPLETED", "OTHER_GAMECOMPLETED_HARD", "OTHER_GAMECOMPLETED_SOS", "OTHER_GAMECOMPLETED_DMD", "OTHER_GAMECOMPLETED_HOH"):
                    self.set_stat_int(st, 1)
                self.set_stat_int("MISSION_MISSIONSCOMPLETED_ALL", max(1, self.get_stat_int("MISSION_MISSIONSCOMPLETED_ALL", 0)))
            elif action == "save_pos" and pawn:
                slot = int((payload or {}).get("slot", 0)) % 3
                lb = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                if lb:
                    self.saved_locations[slot] = struct.unpack("<fff", lb)
                    self.last_event = f"Saved position slot {slot + 1}"
            elif action == "load_pos" and pawn:
                slot = int((payload or {}).get("slot", 0)) % 3
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
                dx = float((payload or {}).get("dx", 0.0))
                dy = float((payload or {}).get("dy", 0.0))
                dz = float((payload or {}).get("dz", 0.0))
                lb = self.rpm(pawn + OFF_ACTOR_LOCATION, 12)
                if lb:
                    x, y, z = struct.unpack("<fff", lb)
                    self.wpm(pawn + OFF_ACTOR_LOCATION, struct.pack("<fff", x + dx, y + dy, z + dz))
            elif action == "apply_preset":
                preset = (payload or {}).get("preset")
                if preset == "god_sss":
                    for k in ("god_mode", "unlimited_health", "unlimited_devil_trigger", "unlimited_overdrive", "sss_style_rank", "max_mission_score", "zero_damage_taken", "never_decrease_items"):
                        self.set_toggle(k, True)
                elif preset == "turbo_pro":
                    self.set_value("player_speed", 1.25)
                    self.set_value("world_speed", 1.20)
                    self.set_value("custom_fov", 98.0)
                    for k in ("player_speed_enabled", "world_speed_enabled", "custom_fov_enabled", "infinite_air_evades", "no_style_decay"):
                        self.set_toggle(k, True)
                elif preset == "farm_fast":
                    for k in ("god_mode", "fast_kill", "unlim_red_orbs", "never_decrease_items", "freeze_mission_timer"):
                        self.set_toggle(k, True)
                elif preset == "disable_all":
                    self.disable_all()
            else:
                return {"ok": False, "error": f"Unknown or unavailable action: {action}"}
            return {"ok": True}

    def _poll_hotkeys(self):
        ctrl = bool(u32_dll.GetAsyncKeyState(VK_CTRL) & 0x8000)
        shift = bool(u32_dll.GetAsyncKeyState(VK_SHIFT) & 0x8000)
        alt = bool(u32_dll.GetAsyncKeyState(VK_ALT) & 0x8000)
        cur_mods = set()
        if ctrl: cur_mods.add("CTRL")
        if shift: cur_mods.add("SHIFT")
        if alt: cur_mods.add("ALT")
        cur_mods = frozenset(cur_mods)

        pressed_now = set()
        for action, hk_str in list(self.config["hotkeys"].items()):
            parsed = parse_hotkey(hk_str)
            if not parsed:
                continue
            req_mods, vk = parsed
            is_down = bool(u32_dll.GetAsyncKeyState(vk) & 0x8000)
            if is_down and cur_mods == req_mods:
                pressed_now.add(action)
                if action not in self.prev_keys:
                    self._trigger_hotkey(action)
        self.prev_keys = pressed_now

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
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        with self.lock:
            self._detach()
