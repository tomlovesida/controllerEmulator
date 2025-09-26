import json
import os
import sys
import logging

def get_paths():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bd = os.path.dirname(sys.executable)
        dd = sys._MEIPASS
    else:
        bd = os.path.dirname(__file__)
        dd = bd

    return {"base_dir": bd, "data_dir": dd}

def def_cfg():
    return {
        "keybinds": {
            "movement": {"forward": "w", "backward": "s", "left": "a", "right": "d"},
            "buttons": {
                "cross": "space", "circle": "c", "square": "x", "triangle": "y",
                "l1": "r", "r1": "t", "l2": "q", "r2": "e",
                "l3": "f", "r3": "g", "share": "backspace", "options": "enter",
                "touchpad": "tab", "ps": "home",
                "dpad_up": "i", "dpad_down": "k", "dpad_left": "j", "dpad_right": "l",
                "example_mouse_bind": "mouse:left"
            },
            "dpad": {
                "up": "up", "down": "down", "left": "left", "right": "right"
            }
        },
        "settings": {
            "mouse_sensitivity": 0.05,
            "deadzone_threshold": 0.01,
            "controller_type": "dualshock4",
            "relative_mouse_mode": False,
            "hide_cursor": False
        }
    }

def load_cfg(log):
    p = get_paths()
    c = [
        os.path.join(p["base_dir"], 'config.json'),
        os.path.join(p["data_dir"], 'config.json'),
    ]
    for cp in c:
        try:
            with open(cp, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in config file '{cp}': {e}")
            break
    log.warning("Config file not found, using defaults; a new one will be created next to the executable on save.")
    cfg = def_cfg()
    try:
        prev = getattr(load_cfg, 'cfg', None)
        load_cfg.cfg = cfg
        save_cfg(cfg, log)
        log.info("Default configuration created.")
        if prev is not None:
            load_cfg.cfg = prev
    except Exception as e:
        log.error(f"Could not create default config: {e}")
    return cfg

def save_cfg(cfg, log):
    p = get_paths()
    cp = os.path.join(p["base_dir"], 'config.json')
    try:
        os.makedirs(os.path.dirname(cp), exist_ok=True)
        with open(cp, 'w') as f:
            json.dump(cfg, f, indent=2)
        log.info(f"Configuration saved successfully to {cp}")
    except IOError as e:
        log.error(f"Failed to save config to {cp}: {e}")
        try:
            ar = os.environ.get('APPDATA') or os.path.expanduser('~')
            fd = os.path.join(ar, 'ControllerEmulator')
            os.makedirs(fd, exist_ok=True)
            fp = os.path.join(fd, 'config.json')
            with open(fp, 'w') as f:
                json.dump(cfg, f, indent=2)
            log.info(f"Configuration saved to fallback location {fp}")
        except Exception as e2:
            log.error(f"Fallback save failed: {e2}")
