const STYLE_RANK_NAMES = ["—", "D", "C", "B", "A", "S", "SS", "SSS"];

const CATEGORIES = [
  {
    id: "player",
    title: "Player",
    icon: "👤",
    actions: [
      { label: "Heal Full HP", action: "heal_full" },
      { label: "Refill Devil Trigger", action: "refill_dt" },
      { label: "+100 Max Health", action: "extend_max_health", payload: { amount: 100 } },
      { label: "+360 Max DT", action: "extend_max_dt", payload: { amount: 360 } },
    ],
    items: [
      { key: "unlimited_health", name: "Unlimited Health", desc: "Locks HP to current maximum each tick" },
      { key: "god_mode", name: "God Mode (Ignore All Damage)", desc: "Sets IgnoreAllDamage flag on NTCombat_CharacterData" },
      { key: "unlimited_devil_trigger", name: "Unlimited Devil Trigger", desc: "Locks Devil Trigger gauge at maximum" },
      { key: "no_dt_end_no_enemies", name: "DT Never Ends Outside Combat", desc: "Prevents automatic DT drain when no enemies remain" },
      { key: "unlimited_overdrive", name: "Unlimited Overdrive / Concentration", desc: "Locks Vergil/Dante Overdrive gauge to max" },
    ],
  },
  {
    id: "combat",
    title: "Combat & Style",
    icon: "⚔️",
    actions: [
      { label: "Drop Active Enemies to 1 HP", action: "enemies_one_hp" },
    ],
    items: [
      { key: "fast_kill", name: "Fast Kill / One-Hit Kill", desc: "Sets active enemies to 1 HP & boosts player damage" },
      {
        key: "damage_mult_enabled",
        name: "Damage Multiplier",
        desc: "Multiplies outgoing player combat damage",
        val: { key: "damage_multiplier", type: "range", min: 1.0, max: 50.0, step: 0.5, suffix: "x" },
      },
      {
        key: "always_demon_evade",
        name: "Always Demon Evade Buff",
        desc: "Keeps Demon Evade damage & style boost active",
        val: { key: "demon_evade_dmg_mult", type: "range", min: 1.0, max: 10.0, step: 0.5, suffix: "x" },
      },
      { key: "force_dismember", name: "Force Dismember Kill", desc: "Forces dismemberment finisher flag on player hits" },
      { key: "sss_style_rank", name: "SSS Style Rank", desc: "Locks Style Rank to SSS & keeps style meter topped up" },
      { key: "no_style_decay", name: "No Style Decay", desc: "Pauses style meter countdown between combos" },
      {
        key: "style_mult_enabled",
        name: "Style Points Multiplier",
        desc: "Multiplies style gain from every attack",
        val: { key: "style_multiplier", type: "range", min: 1.0, max: 25.0, step: 0.5, suffix: "x" },
      },
      { key: "max_mission_score", name: "Max Mission Score", desc: "Locks mission style points to 9,999,999" },
      { key: "zero_damage_taken", name: "Zero Damage Taken Stat", desc: "Locks mission Damage Taken stat to 0 for SSS rank" },
      { key: "unlimited_kablooey_darts", name: "Unlimited Kablooey Darts", desc: "Raises max Kablooey sticky darts to 99" },
    ],
  },
  {
    id: "inventory",
    title: "Inventory & Keys",
    icon: "🎒",
    actions: [
      { label: "+50,000 Red Orbs", action: "add_red_orbs", payload: { amount: 50000 } },
      { label: "+10 Upgrade Points", action: "add_upgrade_points", payload: { amount: 10 } },
      { label: "Max All Keys (99)", action: "batch_keys_99" },
      { label: "Max All Stars (10)", action: "batch_stars_10" },
    ],
    items: [
      { key: "never_decrease_items", name: "Never Decrease Items & Orbs (AOB)", desc: "Prevents stat counter decrements via NTGameStatsManager patch" },
      {
        key: "unlim_red_orbs",
        name: "Unlimited Red Orbs",
        desc: "Maintains Red Orbs at target value",
        val: { key: "red_orbs_lock", type: "number", min: 0, max: 99999999, step: 1000 },
      },
      {
        key: "unlim_gold_orbs",
        name: "Unlimited Gold Orbs",
        desc: "Maintains Gold Orbs in stock",
        val: { key: "gold_orbs_lock", type: "number", min: 0, max: 99, step: 1 },
      },
      {
        key: "unlim_copper_keys",
        name: "Unlimited Copper Keys",
        desc: "Locks MundusKeyBronze count",
        val: { key: "keys_lock", type: "number", min: 0, max: 999, step: 1 },
      },
      { key: "unlim_argent_keys", name: "Unlimited Argent Keys", desc: "Locks MundusKeySilver count (uses Keys target)" },
      { key: "unlim_gold_keys", name: "Unlimited Gold Keys", desc: "Locks MundusKeyGold count (uses Keys target)" },
      { key: "unlim_ivory_keys", name: "Unlimited Ivory Keys", desc: "Locks MundusKeyIvory count (uses Keys target)" },
      {
        key: "unlim_small_vs",
        name: "Unlimited Small Vital Star",
        desc: "Locks Small Vital Star stock",
        val: { key: "stars_lock", type: "number", min: 0, max: 99, step: 1 },
      },
      { key: "unlim_large_vs", name: "Unlimited Large Vital Star", desc: "Locks Large Vital Star stock (uses Stars target)" },
      { key: "unlim_small_dts", name: "Unlimited Small Devil Trigger Star", desc: "Locks Small DT Star stock (uses Stars target)" },
      { key: "unlim_large_dts", name: "Unlimited Large Devil Trigger Star", desc: "Locks Large DT Star stock (uses Stars target)" },
      {
        key: "unlim_health_frag",
        name: "Unlimited Health Cross Fragment",
        desc: "Locks Blue Health Cross Fragment count",
        val: { key: "frags_lock", type: "number", min: 0, max: 99, step: 1 },
      },
      { key: "unlim_dt_frag", name: "Unlimited Devil Trigger Cross Fragment", desc: "Locks Purple DT Cross Fragment count (uses Frags target)" },
      {
        key: "unlim_upgrade_points",
        name: "Unlimited Upgrade Points",
        desc: "Locks unspent skill Upgrade Points",
        val: { key: "upgrade_points_lock", type: "number", min: 0, max: 999, step: 1 },
      },
    ],
  },
  {
    id: "movement",
    title: "Movement & Physics",
    icon: "⚡",
    items: [
      { key: "infinite_air_jumps", name: "Infinite Air Jumps", desc: "Resets jump counter continuously in mid-air" },
      { key: "infinite_air_evades", name: "Infinite Air Evades / Angel Glide", desc: "Clears mid-air evade & glide cooldown lockouts" },
      {
        key: "player_speed_enabled",
        name: "Player Speed Multiplier",
        desc: "Adjusts CustomTimeDilation on Dante / Vergil",
        val: { key: "player_speed", type: "range", min: 0.2, max: 4.0, step: 0.05, suffix: "x" },
      },
      {
        key: "world_speed_enabled",
        name: "Game World Speed (Slomo / Turbo)",
        desc: "Adjusts global WorldInfo TimeDilation",
        val: { key: "world_speed", type: "range", min: 0.1, max: 3.0, step: 0.05, suffix: "x" },
      },
      {
        key: "jump_height_enabled",
        name: "Jump Height Multiplier",
        desc: "Scales DVMovementParameters jump velocity",
        val: { key: "jump_height_mult", type: "range", min: 0.5, max: 4.0, step: 0.1, suffix: "x" },
      },
      {
        key: "custom_gravity_enabled",
        name: "Custom Gravity Z",
        desc: "Overrides WorldGravityZ (default -2250)",
        val: { key: "custom_gravity", type: "range", min: -4000, max: -200, step: 50, suffix: "" },
      },
      { key: "noclip_fly", name: "Zero-Gravity Float / Hover", desc: "Negates downward Z velocity & suspends gravity" },
    ],
  },
  {
    id: "world",
    title: "World & AI",
    icon: "🌍",
    actions: [
      { label: "Reset Mission Timer & Damage", action: "reset_mission_timer" },
    ],
    items: [
      { key: "freeze_mission_timer", name: "Freeze Mission Timer", desc: "Freezes mission elapsed time for S/SSS speed bonus" },
      { key: "freeze_secret_timer", name: "Freeze Secret Mission Timer", desc: "Holds Secret Mission countdown clock" },
      { key: "freeze_enemies_ai", name: "Freeze Enemies AI", desc: "Sets bSuspendAI flag in WorldInfo" },
      { key: "enemies_dont_attack", name: "Enemies Don't Attack (No Tokens)", desc: "Clears attack tokens & cooldowns on AICoordinator" },
      { key: "freeze_world", name: "Freeze World (Players Only)", desc: "Sets bPlayersOnly — freezes everything except player" },
    ],
  },
  {
    id: "progression",
    title: "Progression, Camera & Teleport",
    icon: "🧭",
    actions: [
      { label: "Unlock All Difficulties (SoS/DMD/HoH)", action: "unlock_difficulties", warn: true },
      { label: "Ascend +500 Z", action: "nudge_pos", payload: { dx: 0, dy: 0, dz: 500 } },
      { label: "Drop -300 Z", action: "nudge_pos", payload: { dx: 0, dy: 0, dz: -300 } },
    ],
    items: [
      {
        key: "custom_fov_enabled",
        name: "Custom Camera FOV",
        desc: "Overrides PlayerController FOVAngle (default 85°)",
        val: { key: "custom_fov", type: "range", min: 60, max: 130, step: 1, suffix: "°" },
      },
      {
        key: "player_scale_enabled",
        name: "Player Draw Scale",
        desc: "Resizes character mesh & collision visually",
        val: { key: "player_scale", type: "range", min: 0.3, max: 2.5, step: 0.05, suffix: "x" },
      },
      { key: "hide_hud", name: "Hide HUD (Cinematic Mode)", desc: "Hides in-game HUD overlay for screenshots" },
      { key: "unlock_all_attacks", name: "Unlock All Attacks Flag", desc: "Enables all combat move unlocks in runtime state" },
    ],
    teleport: true,
  },
];

let appState = {
  telemetry: {},
  toggles: {},
  values: {},
  hotkeys: {},
  sound_feedback: true,
  counter_dec_available: true,
};

let activeCat = "all";
let searchQuery = "";
let collapsedCats = new Set();
let bindingAction = null;

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return res.json();
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatNum(v) {
  return Number(v || 0).toLocaleString();
}

function renderAllCategories() {
  const container = document.getElementById("mods-container");
  container.innerHTML = "";
  const q = searchQuery.trim().toLowerCase();

  for (const cat of CATEGORIES) {
    if (activeCat !== "all" && activeCat !== cat.id) continue;

    const matchingItems = cat.items.filter((item) => {
      if (!q) return true;
      const hk = (appState.hotkeys[item.key] || "").toLowerCase();
      return (
        item.name.toLowerCase().includes(q) ||
        item.desc.toLowerCase().includes(q) ||
        hk.includes(q)
      );
    });

    if (matchingItems.length === 0 && !cat.teleport && !(cat.actions && !q)) continue;
    if (q && matchingItems.length === 0) continue;

    const card = el("section", "cat-card");
    if (collapsedCats.has(cat.id)) card.classList.add("collapsed");
    card.dataset.catId = cat.id;

    // Header
    const hdr = el("div", "cat-header");
    const left = el("div", "cat-title-wrap");
    left.appendChild(el("span", "cat-icon", cat.icon));
    left.appendChild(el("span", "cat-title", cat.title));
    const badge = el("span", "cat-badge");
    badge.dataset.catBadge = cat.id;
    left.appendChild(badge);
    hdr.appendChild(left);
    hdr.appendChild(el("span", "cat-chevron", "▼"));
    hdr.addEventListener("click", () => {
      if (collapsedCats.has(cat.id)) collapsedCats.delete(cat.id);
      else collapsedCats.add(cat.id);
      card.classList.toggle("collapsed");
    });
    card.appendChild(hdr);

    // Body
    const body = el("div", "cat-body");

    if (cat.actions && cat.actions.length && !q) {
      const strip = el("div", "actions-strip");
      for (const act of cat.actions) {
        const btn = el("button", act.warn ? "action-btn warn" : "action-btn", act.label);
        btn.addEventListener("click", () => handleQuickAction(act));
        strip.appendChild(btn);
      }
      body.appendChild(strip);
    }

    for (const item of matchingItems) {
      body.appendChild(buildModRow(item));
    }

    if (cat.teleport && !q) {
      body.appendChild(buildTeleportPanel());
    }

    card.appendChild(body);
    container.appendChild(card);
  }

  syncDynamicDom();
}

function buildModRow(item) {
  const row = el("div", "mod-row");
  row.dataset.toggleKey = item.key;

  const info = el("div", "mod-info");
  info.appendChild(el("span", "bolt-icon", "⚡"));
  const txt = el("div", "mod-text");
  txt.appendChild(el("span", "mod-name", item.name));
  txt.appendChild(el("span", "mod-desc", item.desc));
  info.appendChild(txt);
  row.appendChild(info);

  // Value control column
  const ctrl = el("div", "mod-control");
  if (item.val) {
    const vcfg = item.val;
    if (vcfg.type === "range") {
      const slider = el("input", "mod-slider");
      slider.type = "range";
      slider.min = vcfg.min;
      slider.max = vcfg.max;
      slider.step = vcfg.step;
      slider.dataset.valKey = vcfg.key;
      const valBadge = el("span", "val-badge");
      valBadge.dataset.valLabel = vcfg.key;
      valBadge.dataset.suffix = vcfg.suffix || "";

      slider.addEventListener("input", () => {
        valBadge.textContent = `${slider.value}${vcfg.suffix || ""}`;
      });
      slider.addEventListener("change", async () => {
        const num = parseFloat(slider.value);
        appState.values[vcfg.key] = num;
        await postJson("/api/value", { key: vcfg.key, value: num });
      });
      ctrl.appendChild(slider);
      ctrl.appendChild(valBadge);
    } else {
      const inp = el("input", "mod-num-input");
      inp.type = "number";
      inp.min = vcfg.min;
      inp.max = vcfg.max;
      inp.step = vcfg.step;
      inp.dataset.valKey = vcfg.key;
      inp.addEventListener("change", async () => {
        const num = parseInt(inp.value || "0", 10);
        appState.values[vcfg.key] = num;
        await postJson("/api/value", { key: vcfg.key, value: num });
      });
      ctrl.appendChild(inp);
    }
  }
  row.appendChild(ctrl);

  // Segmented toggle switch
  const sw = el("div", "seg-switch");
  sw.dataset.switchKey = item.key;
  sw.appendChild(el("span", "seg-opt seg-off", "Off"));
  sw.appendChild(el("span", "seg-opt seg-on", "On"));
  sw.addEventListener("click", async () => {
    const next = !appState.toggles[item.key];
    appState.toggles[item.key] = next;
    syncDynamicDom();
    await postJson("/api/toggle", { key: item.key, state: next });
  });
  row.appendChild(sw);

  // Hotkey pill
  const hk = el("button", "hotkey-pill");
  hk.dataset.hkAction = item.key;
  hk.title = "Click to rebind hotkey";
  hk.addEventListener("click", () => openHotkeyModal(item.key, item.name));
  row.appendChild(hk);

  return row;
}

function buildTeleportPanel() {
  const wrap = el("div", "teleport-grid");
  for (let i = 0; i < 3; i++) {
    const card = el("div", "tp-slot-card");
    const head = el("div", "tp-slot-head");
    head.appendChild(el("span", "", `Location Slot ${i + 1}`));
    if (i === 0) {
      const pair = el("div", "");
      pair.style.display = "flex";
      pair.style.gap = "4px";
      const hkSave = el("button", "hotkey-pill");
      hkSave.dataset.hkAction = "save_pos_0";
      hkSave.style.minWidth = "46px";
      hkSave.title = "Hotkey: Save Slot 1";
      hkSave.addEventListener("click", () => openHotkeyModal("save_pos_0", "Save Location Slot 1"));

      const hkLoad = el("button", "hotkey-pill");
      hkLoad.dataset.hkAction = "load_pos_0";
      hkLoad.style.minWidth = "46px";
      hkLoad.title = "Hotkey: Teleport Slot 1";
      hkLoad.addEventListener("click", () => openHotkeyModal("load_pos_0", "Teleport to Slot 1"));
      pair.appendChild(hkSave);
      pair.appendChild(hkLoad);
      head.appendChild(pair);
    }
    card.appendChild(head);

    const coords = el("div", "tp-coords", "Empty");
    coords.dataset.tpSlot = String(i);
    card.appendChild(coords);

    const btns = el("div", "tp-btns");
    const bSave = el("button", "action-btn", "Save");
    bSave.addEventListener("click", () => runAction("save_pos", { slot: i }));
    const bLoad = el("button", "action-btn", "Teleport");
    bLoad.addEventListener("click", () => runAction("load_pos", { slot: i }));
    btns.appendChild(bSave);
    btns.appendChild(bLoad);

    if (i === 0) {
      const bUndo = el("button", "ghost-btn", "Undo");
      bUndo.style.padding = "4px 8px";
      bUndo.title = "Undo Last Teleport (Hotkey customizable)";
      bUndo.addEventListener("click", () => runAction("undo_teleport", {}));
      btns.appendChild(bUndo);
    }
    card.appendChild(btns);
    wrap.appendChild(card);
  }
  return wrap;
}

async function runAction(action, payload) {
  const res = await postJson("/api/action", { action, payload });
  if (!res.ok && res.error) {
    document.getElementById("last-event").textContent = res.error;
  }
  await fetchState();
}

async function handleQuickAction(act) {
  if (act.action === "batch_keys_99") {
    for (const k of ["MundusKeyBronze", "MundusKeySilver", "MundusKeyGold", "MundusKeyIvory"]) {
      await postJson("/api/action", { action: "set_stat", payload: { name: k, value: 99 } });
    }
    await fetchState();
    return;
  }
  if (act.action === "batch_stars_10") {
    for (const s of ["VitalStar_Small", "VitalStar_Large", "DevilTriggerStar_Small", "DevilTriggerStar_Large"]) {
      await postJson("/api/action", { action: "set_stat", payload: { name: s, value: 10 } });
    }
    await fetchState();
    return;
  }
  await runAction(act.action, act.payload || {});
}

function syncDynamicDom() {
  const t = appState.telemetry || {};
  const attached = Boolean(t.attached);

  // Header status
  const dot = document.getElementById("conn-dot");
  dot.className = `status-dot ${attached ? "online" : "offline"}`;
  document.getElementById("conn-text").textContent = attached
    ? `Attached · PID ${t.pid}${t.in_game ? "" : " (Menus / Loading)"}`
    : "Waiting for DMC-DevilMayCry.exe...";

  const charPill = document.getElementById("char-pill");
  if (attached && t.character && t.character !== "None") {
    charPill.textContent = t.character;
    charPill.classList.remove("hidden");
  } else {
    charPill.classList.add("hidden");
  }

  const hookPill = document.getElementById("hook-pill");
  if (attached) {
    hookPill.classList.remove("hidden");
    hookPill.textContent = appState.counter_dec_available
      ? "CounterDec Hook Ready"
      : "External Counter Hook Detected (Safe Yield)";
  } else {
    hookPill.classList.add("hidden");
  }

  // Sound button
  const sndBtn = document.getElementById("btn-sound");
  const sndOn = Boolean(appState.sound_feedback);
  sndBtn.classList.toggle("active", sndOn);
  sndBtn.querySelector(".btn-icon").textContent = sndOn ? "🔊" : "🔇";
  sndBtn.querySelector(".btn-label").textContent = sndOn ? "Sound On" : "Sound Off";

  // Telemetry
  const rankIdx = Math.max(0, Math.min(7, Number(t.style_rank || 0)));
  const rankEl = document.getElementById("t-style-rank");
  rankEl.textContent = STYLE_RANK_NAMES[rankIdx];
  rankEl.className = `style-rank rank-${rankIdx}`;
  document.getElementById("t-style-pts").textContent = formatNum(Math.round(t.style_points || 0));

  document.getElementById("t-hp").textContent = `${Math.round(t.health || 0)} / ${Math.round(t.max_health || 0)}`;
  document.getElementById("t-dt").textContent = `${Math.round(t.devil_trigger || 0)} / ${Math.round(t.max_devil_trigger || 0)}`;
  document.getElementById("t-od").textContent = `${Math.round(t.overdrive || 0)} / ${Math.round(t.max_overdrive || 100)}`;
  document.getElementById("t-red-orbs").textContent = formatNum(t.red_orbs);
  document.getElementById("t-gold-up").textContent = `${t.gold_orbs || 0} · ${t.upgrade_points || 0} pt`;
  document.getElementById("t-keys").textContent = `${t.copper_keys || 0} / ${t.argent_keys || 0} / ${t.gold_keys || 0} / ${t.ivory_keys || 0}`;
  document.getElementById("t-stars").textContent = `${t.small_vs || 0}/${t.large_vs || 0} · ${t.small_dts || 0}/${t.large_dts || 0}`;
  document.getElementById("t-frags").textContent = `${t.blue_frags || 0} / ${t.purple_frags || 0}`;
  document.getElementById("t-timer-enemies").textContent = `${Number(t.mission_time || 0).toFixed(1)}s · ${t.active_enemies || 0}`;

  const loc = t.location || [0, 0, 0];
  document.getElementById("coords-text").textContent = `Pos: ${loc[0].toFixed(1)}, ${loc[1].toFixed(1)}, ${loc[2].toFixed(1)}`;
  if (t.last_event) {
    document.getElementById("last-event").textContent = t.last_event;
  }

  // Active total count & per-category badges
  let totalActive = 0;
  for (const val of Object.values(appState.toggles || {})) {
    if (val) totalActive++;
  }
  document.getElementById("active-count").textContent = String(totalActive);

  for (const cat of CATEGORIES) {
    const badge = document.querySelector(`[data-cat-badge="${cat.id}"]`);
    if (!badge) continue;
    const activeInCat = cat.items.filter((i) => appState.toggles[i.key]).length;
    badge.textContent = activeInCat ? `${activeInCat} / ${cat.items.length} active` : `${cat.items.length}`;
    badge.classList.toggle("has-active", activeInCat > 0);
  }

  // Mod rows
  document.querySelectorAll(".mod-row").forEach((row) => {
    const key = row.dataset.toggleKey;
    const on = Boolean(appState.toggles[key]);
    row.classList.toggle("active", on);
    const sw = row.querySelector(".seg-switch");
    if (sw) sw.classList.toggle("on", on);
  });

  // Value inputs (don't clobber active focus)
  document.querySelectorAll("[data-val-key]").forEach((inp) => {
    const k = inp.dataset.valKey;
    if (document.activeElement !== inp && appState.values[k] !== undefined) {
      inp.value = appState.values[k];
    }
  });
  document.querySelectorAll("[data-val-label]").forEach((lbl) => {
    const k = lbl.dataset.valLabel;
    if (appState.values[k] !== undefined) {
      lbl.textContent = `${appState.values[k]}${lbl.dataset.suffix || ""}`;
    }
  });

  // Hotkeys
  document.querySelectorAll("[data-hk-action]").forEach((btn) => {
    const act = btn.dataset.hkAction;
    const hk = appState.hotkeys[act] || "";
    btn.textContent = hk ? hk.replace(/\+/g, " ") : "Bind";
    btn.classList.toggle("empty", !hk);
  });

  // Saved teleport slots
  const slots = t.saved_slots || [null, null, null];
  document.querySelectorAll("[data-tp-slot]").forEach((node) => {
    const idx = Number(node.dataset.tpSlot);
    const coords = slots[idx];
    node.textContent = coords ? `${coords[0]}, ${coords[1]}, ${coords[2]}` : "Empty";
  });
}

// Hotkey binding modal
function openHotkeyModal(action, label) {
  bindingAction = action;
  document.getElementById("hotkey-target-name").textContent = label;
  document.getElementById("hotkey-modal").classList.remove("hidden");
}

function closeHotkeyModal() {
  bindingAction = null;
  document.getElementById("hotkey-modal").classList.add("hidden");
}

function mapKeyEventToHotkey(e) {
  if (["Control", "Shift", "Alt", "Meta"].includes(e.key)) return null;
  const mods = [];
  if (e.ctrlKey) mods.push("Ctrl");
  if (e.shiftKey) mods.push("Shift");
  if (e.altKey) mods.push("Alt");

  let k = null;
  if (e.code && e.code.startsWith("Numpad")) {
    const tail = e.code.slice(6);
    const numMap = {
      Decimal: "Num.",
      Add: "Num+",
      Subtract: "Num-",
      Multiply: "Num*",
      Divide: "Num/",
    };
    if (numMap[tail]) k = numMap[tail];
    else if (/^[0-9]$/.test(tail)) k = `Num${tail}`;
  } else if (/^F([1-9]|1[0-2])$/.test(e.key)) {
    k = e.key;
  } else if (/^[a-zA-Z0-9]$/.test(e.key)) {
    k = e.key.toUpperCase();
  } else {
    const special = {
      Home: "Home",
      End: "End",
      Insert: "Ins",
      Delete: "Del",
      PageUp: "PgUp",
      PageDown: "PgDn",
    };
    if (special[e.key]) k = special[e.key];
  }

  if (!k) return null;
  return mods.length ? `${mods.join("+")}+${k}` : k;
}

window.addEventListener("keydown", async (e) => {
  if (!bindingAction) return;
  e.preventDefault();
  e.stopPropagation();
  if (e.key === "Escape") {
    closeHotkeyModal();
    return;
  }
  if (e.key === "Backspace") {
    await postJson("/api/hotkey", { action: bindingAction, hotkey: "" });
    appState.hotkeys[bindingAction] = "";
    closeHotkeyModal();
    syncDynamicDom();
    return;
  }
  const combo = mapKeyEventToHotkey(e);
  if (!combo) return;
  await postJson("/api/hotkey", { action: bindingAction, hotkey: combo });
  appState.hotkeys[bindingAction] = combo;
  closeHotkeyModal();
  syncDynamicDom();
});

async function fetchState() {
  try {
    const res = await fetch("/api/state");
    if (!res.ok) return;
    appState = await res.json();
    syncDynamicDom();
  } catch (_) {
    // Ignore transient poll errors during exit
  }
}

async function init() {
  document.getElementById("category-tabs").addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeCat = btn.dataset.cat;
    renderAllCategories();
  });

  document.getElementById("search-input").addEventListener("input", (e) => {
    searchQuery = e.target.value || "";
    renderAllCategories();
  });

  document.getElementById("btn-sound").addEventListener("click", async () => {
    const next = !appState.sound_feedback;
    appState.sound_feedback = next;
    syncDynamicDom();
    await postJson("/api/sound", { enabled: next });
  });

  document.getElementById("btn-disable-all").addEventListener("click", () => {
    runAction("disable_all", {});
  });

  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      runAction("apply_preset", { preset: btn.dataset.preset });
    });
  });

  document.getElementById("hotkey-clear-btn").addEventListener("click", async () => {
    if (!bindingAction) return;
    await postJson("/api/hotkey", { action: bindingAction, hotkey: "" });
    appState.hotkeys[bindingAction] = "";
    closeHotkeyModal();
    syncDynamicDom();
  });
  document.getElementById("hotkey-cancel-btn").addEventListener("click", closeHotkeyModal);

  await fetchState();
  renderAllCategories();

  // Live poll + heartbeat keepalive
  setInterval(fetchState, 350);
  const ping = () => fetch("/api/ping", { method: "POST" }).catch(() => {});
  ping();
  setInterval(ping, 2000);
}

init();
