"""
DmC: Devil May Cry - Modern Trainer Web Server & Desktop Host Bridge
"""

import argparse
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.serving import make_server

from trainer_backend import DmCTrainerEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
DEFAULT_SETTINGS = os.path.join(BASE_DIR, "settings.json")


def find_edge_executable() -> str | None:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return shutil.which("msedge") or shutil.which("chrome")


def create_app(engine: DmCTrainerEngine, shutdown_event: threading.Event, client_state: dict) -> Flask:
    app = Flask(__name__, static_folder=None)

    @app.after_request
    def add_no_cache_headers(resp):
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp

    @app.get("/")
    def index():
        return send_from_directory(WEB_DIR, "index.html")

    @app.get("/<path:filename>")
    def static_files(filename: str):
        return send_from_directory(WEB_DIR, filename)

    @app.get("/api/state")
    def api_state():
        with engine.lock:
            toggles = dict(engine.config.get("toggles", {}))
            values = dict(engine.config.get("values", {}))
            hotkeys = dict(engine.config.get("hotkeys", {}))
            sound_feedback = bool(engine.config.get("sound_feedback", True))
            telemetry = dict(engine.telemetry)
            addrs = {k: hex(v) for k, v in engine.addrs.items() if isinstance(v, int)}
            counter_dec_available = "CounterDec_Instr" in engine.addrs
            counter_dec_patched = bool(engine.counter_dec_patched)
        return jsonify({
            "telemetry": telemetry,
            "toggles": toggles,
            "values": values,
            "hotkeys": hotkeys,
            "sound_feedback": sound_feedback,
            "addrs": addrs,
            "counter_dec_available": counter_dec_available,
            "counter_dec_patched": counter_dec_patched,
        })

    @app.post("/api/toggle")
    def api_toggle():
        data = request.get_json(silent=True) or {}
        key = data.get("key")
        state = bool(data.get("state", False))
        ok = engine.set_toggle(key, state)
        return jsonify({"ok": ok, "key": key, "state": engine.config["toggles"].get(key, False)}), (200 if ok else 400)

    @app.post("/api/value")
    def api_value():
        data = request.get_json(silent=True) or {}
        key = data.get("key")
        val = data.get("value")
        try:
            num_val = float(val) if isinstance(engine.config["values"].get(key), float) else int(float(val))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Invalid numeric value"}), 400
        ok = engine.set_value(key, num_val)
        return jsonify({"ok": ok, "key": key, "value": engine.config["values"].get(key)}), (200 if ok else 400)

    @app.post("/api/hotkey")
    def api_hotkey():
        data = request.get_json(silent=True) or {}
        action = str(data.get("action", "")).strip()
        hotkey = str(data.get("hotkey", "")).strip()
        if not action:
            return jsonify({"ok": False, "error": "Missing action"}), 400
        ok = engine.set_hotkey(action, hotkey)
        return jsonify({"ok": ok, "action": action, "hotkey": hotkey})

    @app.post("/api/sound")
    def api_sound():
        data = request.get_json(silent=True) or {}
        enabled = bool(data.get("enabled", True))
        engine.set_sound_feedback(enabled)
        return jsonify({"ok": True, "enabled": enabled})

    @app.post("/api/action")
    def api_action():
        data = request.get_json(silent=True) or {}
        action = str(data.get("action", "")).strip()
        payload = data.get("payload") or {}

        if action == "disable_all":
            engine.disable_all()
            return jsonify({"ok": True})

        if action == "apply_preset" and not engine.handle:
            preset = payload.get("preset")
            with engine.lock:
                if preset == "god_sss":
                    for k in ("god_mode", "unlimited_health", "unlimited_devil_trigger", "unlimited_overdrive",
                              "sss_style_rank", "max_mission_score", "zero_damage_taken", "never_decrease_items"):
                        engine.set_toggle(k, True)
                elif preset == "turbo_pro":
                    engine.set_value("player_speed", 1.25)
                    engine.set_value("world_speed", 1.20)
                    engine.set_value("custom_fov", 98.0)
                    for k in ("player_speed_enabled", "world_speed_enabled", "custom_fov_enabled",
                              "infinite_air_evades", "no_style_decay"):
                        engine.set_toggle(k, True)
                elif preset == "farm_fast":
                    for k in ("god_mode", "fast_kill", "unlim_red_orbs", "never_decrease_items", "freeze_mission_timer"):
                        engine.set_toggle(k, True)
                elif preset == "disable_all":
                    engine.disable_all()
                else:
                    return jsonify({"ok": False, "error": f"Unknown preset: {preset}"}), 400
            return jsonify({"ok": True})

        res = engine.perform_action(action, payload)
        status = 200 if res.get("ok") else 400
        return jsonify(res), status

    @app.post("/api/ping")
    def api_ping():
        client_state["seen"] = True
        client_state["last_ping"] = time.monotonic()
        return jsonify({"ok": True})

    @app.post("/api/quit")
    def api_quit():
        shutdown_event.set()
        return jsonify({"ok": True})

    return app


def launch_desktop_window(url: str) -> tuple[subprocess.Popen | None, str | None]:
    edge = find_edge_executable()
    if edge:
        profile_dir = tempfile.mkdtemp(prefix="dmc_trainer_ui_")
        cmd = [
            edge,
            f"--app={url}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=msEdgeSidebarV2",
            "--window-size=1260,880",
        ]
        proc = subprocess.Popen(cmd)
        return proc, profile_dir
    webbrowser.open(url)
    return None, None


def main():
    parser = argparse.ArgumentParser(description="DmC: Devil May Cry Trainer UI Host")
    parser.add_argument("--port", type=int, default=0, help="Port to bind (0 for ephemeral)")
    parser.add_argument("--no-browser", action="store_true", help="Run headless without opening UI window")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS, help="Path to settings.json")
    args = parser.parse_args()

    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    engine = DmCTrainerEngine(args.settings)
    engine.start()

    shutdown_event = threading.Event()
    client_state = {"seen": False, "last_ping": time.monotonic()}

    app = create_app(engine, shutdown_event, client_state)
    server = make_server("127.0.0.1", args.port, app, threaded=True)
    bound_port = server.server_port
    url = f"http://127.0.0.1:{bound_port}/"

    serve_thread = threading.Thread(target=server.serve_forever, daemon=True)
    serve_thread.start()

    browser_proc = None
    profile_dir = None
    if not args.no_browser:
        browser_proc, profile_dir = launch_desktop_window(url)
    else:
        print(f"DmC Trainer API listening at {url}", flush=True)

    def _sig_handler(_signum, _frame):
        shutdown_event.set()

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        while not shutdown_event.is_set():
            if not args.no_browser:
                # If heartbeat was established and stopped for >12s, window closed
                if client_state["seen"] and (time.monotonic() - client_state["last_ping"] > 12.0):
                    break
                # If Edge exited directly without delegating
                if browser_proc is not None and browser_proc.poll() is not None and not client_state["seen"]:
                    # Wait briefly in case Edge handed off window to an existing instance
                    time.sleep(2.0)
                    if not client_state["seen"]:
                        break
            time.sleep(0.25)
    finally:
        engine.stop()
        server.shutdown()
        if profile_dir and os.path.isdir(profile_dir):
            shutil.rmtree(profile_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
