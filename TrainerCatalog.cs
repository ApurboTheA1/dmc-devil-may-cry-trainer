using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Input;

namespace DmCTrainerApp
{
    internal sealed class ValueSpec
    {
        public string Key;
        public string ControlType; // "range" or "number"
        public double Min;
        public double Max;
        public double Step;
        public string Suffix;
    }

    internal sealed class ModSpec
    {
        public string Key;
        public string Name;
        public string Desc;
        public ValueSpec Val;
    }

    internal sealed class ActionSpec
    {
        public string Label;
        public string Action;
        public Dictionary<string, object> Payload;
        public bool Warn;
    }

    internal sealed class CategorySpec
    {
        public string Id;
        public string Title;
        public string Icon;
        public List<ActionSpec> Actions = new List<ActionSpec>();
        public List<ModSpec> Items = new List<ModSpec>();
        public bool HasTeleport;
    }

    internal static class TrainerCatalog
    {
        public static readonly string[] StyleRankNames = new string[] { "-", "D", "C", "B", "A", "S", "SS", "SSS" };

        private static ActionSpec Act(string label, string action, Dictionary<string, object> payload, bool warn)
        {
            var a = new ActionSpec();
            a.Label = label;
            a.Action = action;
            a.Payload = payload;
            a.Warn = warn;
            return a;
        }

        private static ModSpec Mod(string key, string name, string desc, ValueSpec val)
        {
            var m = new ModSpec();
            m.Key = key;
            m.Name = name;
            m.Desc = desc;
            m.Val = val;
            return m;
        }

        private static ValueSpec RangeVal(string key, double min, double max, double step, string suffix)
        {
            var v = new ValueSpec();
            v.Key = key;
            v.ControlType = "range";
            v.Min = min;
            v.Max = max;
            v.Step = step;
            v.Suffix = suffix;
            return v;
        }

        private static ValueSpec NumVal(string key, double min, double max, double step)
        {
            var v = new ValueSpec();
            v.Key = key;
            v.ControlType = "number";
            v.Min = min;
            v.Max = max;
            v.Step = step;
            v.Suffix = "";
            return v;
        }

        private static Dictionary<string, object> Dict(string k, object v)
        {
            var d = new Dictionary<string, object>();
            d[k] = v;
            return d;
        }

        public static List<CategorySpec> BuildCategories()
        {
            var list = new List<CategorySpec>();

            // 1. Player
            var player = new CategorySpec { Id = "player", Title = "Player", Icon = "P" };
            player.Actions.Add(Act("Heal Full HP", "heal_full", null, false));
            player.Actions.Add(Act("Refill Devil Trigger", "refill_dt", null, false));
            player.Actions.Add(Act("+100 Max Health", "extend_max_health", Dict("amount", 100), false));
            player.Actions.Add(Act("+360 Max DT", "extend_max_dt", Dict("amount", 360), false));
            player.Items.Add(Mod("unlimited_health", "Unlimited Health", "Locks HP to current maximum each tick", null));
            player.Items.Add(Mod("god_mode", "God Mode (Ignore All Damage)", "Sets IgnoreAllDamage flag on NTCombat_CharacterData", null));
            player.Items.Add(Mod("unlimited_devil_trigger", "Unlimited Devil Trigger", "Locks Devil Trigger gauge at maximum", null));
            player.Items.Add(Mod("no_dt_end_no_enemies", "DT Never Ends Outside Combat", "Prevents automatic DT drain when no enemies remain", null));
            player.Items.Add(Mod("unlimited_overdrive", "Unlimited Overdrive / Concentration", "Locks Vergil/Dante Overdrive gauge to max", null));
            list.Add(player);

            // 2. Combat & Style
            var combat = new CategorySpec { Id = "combat", Title = "Combat & Style", Icon = "C" };
            combat.Actions.Add(Act("Drop Active Enemies to 1 HP", "enemies_one_hp", null, false));
            combat.Items.Add(Mod("fast_kill", "Fast Kill / One-Hit Kill", "Sets active enemies to 1 HP & boosts player damage", null));
            combat.Items.Add(Mod("damage_mult_enabled", "Damage Multiplier", "Multiplies outgoing player combat damage",
                RangeVal("damage_multiplier", 1.0, 50.0, 0.5, "x")));
            combat.Items.Add(Mod("always_demon_evade", "Always Demon Evade Buff", "Keeps Demon Evade damage & style boost active",
                RangeVal("demon_evade_dmg_mult", 1.0, 10.0, 0.5, "x")));
            combat.Items.Add(Mod("force_dismember", "Force Dismember Kill", "Forces dismemberment finisher flag on player hits", null));
            combat.Items.Add(Mod("sss_style_rank", "SSS Style Rank", "Locks Style Rank to SSS & keeps style meter topped up", null));
            combat.Items.Add(Mod("no_style_decay", "No Style Decay", "Pauses style meter countdown between combos", null));
            combat.Items.Add(Mod("style_mult_enabled", "Style Points Multiplier", "Multiplies style gain from every attack",
                RangeVal("style_multiplier", 1.0, 25.0, 0.5, "x")));
            combat.Items.Add(Mod("max_mission_score", "Max Mission Score", "Locks mission style points to 9,999,999", null));
            combat.Items.Add(Mod("zero_damage_taken", "Zero Damage Taken Stat", "Locks mission Damage Taken stat to 0 for SSS rank", null));
            combat.Items.Add(Mod("unlimited_kablooey_darts", "Unlimited Kablooey Darts", "Raises max Kablooey sticky darts to 99", null));
            list.Add(combat);

            // 3. Inventory & Keys
            var inv = new CategorySpec { Id = "inventory", Title = "Inventory & Keys", Icon = "I" };
            inv.Actions.Add(Act("+50,000 Red Orbs", "add_red_orbs", Dict("amount", 50000), false));
            inv.Actions.Add(Act("+10 Upgrade Points", "add_upgrade_points", Dict("amount", 10), false));
            inv.Actions.Add(Act("Max All Keys (99)", "batch_keys_99", null, false));
            inv.Actions.Add(Act("Max All Stars (10)", "batch_stars_10", null, false));
            inv.Items.Add(Mod("never_decrease_items", "Never Decrease Items & Orbs (AOB)", "Prevents stat counter decrements via NTGameStatsManager patch", null));
            inv.Items.Add(Mod("unlim_red_orbs", "Unlimited Red Orbs", "Maintains Red Orbs at target value",
                NumVal("red_orbs_lock", 0, 99999999, 1000)));
            inv.Items.Add(Mod("unlim_gold_orbs", "Unlimited Gold Orbs", "Maintains Gold Orbs in stock",
                NumVal("gold_orbs_lock", 0, 99, 1)));
            inv.Items.Add(Mod("unlim_copper_keys", "Unlimited Copper Keys", "Locks MundusKeyBronze count",
                NumVal("keys_lock", 0, 999, 1)));
            inv.Items.Add(Mod("unlim_argent_keys", "Unlimited Argent Keys", "Locks MundusKeySilver count (uses Keys target)", null));
            inv.Items.Add(Mod("unlim_gold_keys", "Unlimited Gold Keys", "Locks MundusKeyGold count (uses Keys target)", null));
            inv.Items.Add(Mod("unlim_ivory_keys", "Unlimited Ivory Keys", "Locks MundusKeyIvory count (uses Keys target)", null));
            inv.Items.Add(Mod("unlim_small_vs", "Unlimited Small Vital Star", "Locks Small Vital Star stock",
                NumVal("stars_lock", 0, 99, 1)));
            inv.Items.Add(Mod("unlim_large_vs", "Unlimited Large Vital Star", "Locks Large Vital Star stock (uses Stars target)", null));
            inv.Items.Add(Mod("unlim_small_dts", "Unlimited Small Devil Trigger Star", "Locks Small DT Star stock (uses Stars target)", null));
            inv.Items.Add(Mod("unlim_large_dts", "Unlimited Large Devil Trigger Star", "Locks Large DT Star stock (uses Stars target)", null));
            inv.Items.Add(Mod("unlim_health_frag", "Unlimited Health Cross Fragment", "Locks Blue Health Cross Fragment count",
                NumVal("frags_lock", 0, 99, 1)));
            inv.Items.Add(Mod("unlim_dt_frag", "Unlimited Devil Trigger Cross Fragment", "Locks Purple DT Cross Fragment count (uses Frags target)", null));
            inv.Items.Add(Mod("unlim_upgrade_points", "Unlimited Upgrade Points", "Locks unspent skill Upgrade Points",
                NumVal("upgrade_points_lock", 0, 999, 1)));
            list.Add(inv);

            // 4. Movement & Physics
            var mov = new CategorySpec { Id = "movement", Title = "Movement & Physics", Icon = "M" };
            mov.Items.Add(Mod("infinite_air_jumps", "Infinite Air Jumps", "Resets jump counter continuously in mid-air", null));
            mov.Items.Add(Mod("infinite_air_evades", "Infinite Air Evades / Angel Glide", "Clears mid-air evade & glide cooldown lockouts", null));
            mov.Items.Add(Mod("player_speed_enabled", "Player Speed Multiplier", "Adjusts CustomTimeDilation on Dante / Vergil",
                RangeVal("player_speed", 0.2, 4.0, 0.05, "x")));
            mov.Items.Add(Mod("world_speed_enabled", "Game World Speed (Slomo / Turbo)", "Adjusts global WorldInfo TimeDilation",
                RangeVal("world_speed", 0.1, 3.0, 0.05, "x")));
            mov.Items.Add(Mod("jump_height_enabled", "Jump Height Multiplier", "Scales DVMovementParameters jump velocity",
                RangeVal("jump_height_mult", 0.5, 4.0, 0.1, "x")));
            mov.Items.Add(Mod("custom_gravity_enabled", "Custom Gravity Z", "Overrides WorldGravityZ (default -2250)",
                RangeVal("custom_gravity", -4000, -200, 50, "")));
            mov.Items.Add(Mod("noclip_fly", "Zero-Gravity Float / Hover", "Negates downward Z velocity & suspends gravity", null));
            list.Add(mov);

            // 5. World & AI
            var world = new CategorySpec { Id = "world", Title = "World & AI", Icon = "W" };
            world.Actions.Add(Act("Reset Mission Timer & Damage", "reset_mission_timer", null, false));
            world.Items.Add(Mod("freeze_mission_timer", "Freeze Mission Timer", "Freezes mission elapsed time for S/SSS speed bonus", null));
            world.Items.Add(Mod("freeze_secret_timer", "Freeze Secret Mission Timer", "Holds Secret Mission countdown clock", null));
            world.Items.Add(Mod("freeze_enemies_ai", "Freeze Enemies AI", "Sets bSuspendAI flag in WorldInfo", null));
            world.Items.Add(Mod("enemies_dont_attack", "Enemies Don't Attack (No Tokens)", "Clears attack tokens & cooldowns on AICoordinator", null));
            world.Items.Add(Mod("freeze_world", "Freeze World (Players Only)", "Sets bPlayersOnly - freezes everything except player", null));
            list.Add(world);

            // 6. Progression, Camera & Teleport
            var prog = new CategorySpec { Id = "progression", Title = "Progression, Camera & Teleport", Icon = "T", HasTeleport = true };
            var nudgeUp = new Dictionary<string, object>();
            nudgeUp["dx"] = 0; nudgeUp["dy"] = 0; nudgeUp["dz"] = 500;
            var nudgeDown = new Dictionary<string, object>();
            nudgeDown["dx"] = 0; nudgeDown["dy"] = 0; nudgeDown["dz"] = -300;

            prog.Actions.Add(Act("Unlock All Difficulties (SoS/DMD/HoH)", "unlock_difficulties", null, true));
            prog.Actions.Add(Act("Ascend +500 Z", "nudge_pos", nudgeUp, false));
            prog.Actions.Add(Act("Drop -300 Z", "nudge_pos", nudgeDown, false));
            prog.Items.Add(Mod("custom_fov_enabled", "Custom Camera FOV", "Overrides PlayerController FOVAngle (default 85 deg)",
                RangeVal("custom_fov", 60, 130, 1, " deg")));
            prog.Items.Add(Mod("player_scale_enabled", "Player Draw Scale", "Resizes character mesh & collision visually",
                RangeVal("player_scale", 0.3, 2.5, 0.05, "x")));
            prog.Items.Add(Mod("hide_hud", "Hide HUD (Cinematic Mode)", "Hides in-game HUD overlay for screenshots", null));
            prog.Items.Add(Mod("unlock_all_attacks", "Unlock All Attacks Flag", "Enables all combat move unlocks in runtime state", null));
            list.Add(prog);

            return list;
        }

        public static string MapWpfKeyToHotkey(Key rawKey, ModifierKeys modifiers)
        {
            Key k = (rawKey == Key.System) ? Key.None : rawKey;
            if (k == Key.None) return null;
            if (k == Key.LeftCtrl || k == Key.RightCtrl || k == Key.LeftShift || k == Key.RightShift ||
                k == Key.LeftAlt || k == Key.RightAlt || k == Key.LWin || k == Key.RWin)
            {
                return null;
            }

            string token = null;
            if (k >= Key.F1 && k <= Key.F12)
            {
                token = "F" + ((int)k - (int)Key.F1 + 1);
            }
            else if (k >= Key.NumPad0 && k <= Key.NumPad9)
            {
                token = "Num" + ((int)k - (int)Key.NumPad0);
            }
            else if (k == Key.Decimal) token = "Num.";
            else if (k == Key.Add) token = "Num+";
            else if (k == Key.Subtract) token = "Num-";
            else if (k == Key.Multiply) token = "Num*";
            else if (k == Key.Divide) token = "Num/";
            else if (k >= Key.D0 && k <= Key.D9)
            {
                token = ((int)k - (int)Key.D0).ToString();
            }
            else if (k >= Key.A && k <= Key.Z)
            {
                token = ((char)('A' + ((int)k - (int)Key.A))).ToString();
            }
            else if (k == Key.Home) token = "Home";
            else if (k == Key.End) token = "End";
            else if (k == Key.Insert) token = "Ins";
            else if (k == Key.Delete) token = "Del";
            else if (k == Key.PageUp) token = "PgUp";
            else if (k == Key.PageDown) token = "PgDn";

            if (token == null) return null;

            var mods = new List<string>();
            if ((modifiers & ModifierKeys.Control) != 0) mods.Add("Ctrl");
            if ((modifiers & ModifierKeys.Shift) != 0) mods.Add("Shift");
            if ((modifiers & ModifierKeys.Alt) != 0) mods.Add("Alt");

            if (mods.Count > 0)
            {
                return string.Join("+", mods.ToArray()) + "+" + token;
            }
            return token;
        }
    }

    internal sealed class IpcClient
    {
        private readonly object writeLock = new object();
        private readonly Process proc;
        private readonly JavaScriptSerializer json = new JavaScriptSerializer();

        public IpcClient(Process backendProcess)
        {
            proc = backendProcess;
            json.MaxJsonLength = 4 * 1024 * 1024;
        }

        public Dictionary<string, object> DeserializeLine(string line)
        {
            if (string.IsNullOrEmpty(line)) return null;
            return json.Deserialize<Dictionary<string, object>>(line);
        }

        public void Send(Dictionary<string, object> payload)
        {
            if (proc == null || proc.HasExited) return;
            string line = json.Serialize(payload);
            lock (writeLock)
            {
                try
                {
                    proc.StandardInput.WriteLine(line);
                    proc.StandardInput.Flush();
                }
                catch { }
            }
        }
    }
}
