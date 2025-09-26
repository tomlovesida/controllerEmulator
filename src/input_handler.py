import keyboard
import mouse
import win32api
import time
import vgamepad as vg

def setup_mouse(cfg):
    try:
        sw = win32api.GetSystemMetrics(0)
        sh = win32api.GetSystemMetrics(1)
        cx, cy = sw // 2, sh // 2

        win32api.SetCursorPos((cx, cy))
        lmx, lmy = mouse.get_position()

        if cfg["settings"].get("hide_cursor", False):
            win32api.ShowCursor(False)

        return lmx, lmy
    except Exception as e:
        raise Exception(f"Failed to setup mouse mode: {e}")

def cleanup_mouse(cfg):
    try:
        if cfg["settings"].get("hide_cursor", False):
            win32api.ShowCursor(True)
    except Exception as e:
        raise Exception(f"Failed to cleanup mouse mode: {e}")

def print_ctrl(cfg):
    try:
        print("Controls:")
        m = cfg["keybinds"]["movement"]
        print(f"{m['forward'].upper()}{m['left'].upper()}{m['backward'].upper()}{m['right'].upper()} - Character movement (left joystick)")
        print("Mouse - Camera/look (right joystick)")

        b = cfg["keybinds"]["buttons"]
        for bn, k in b.items():
            l = str(k).upper()
            print(f"{l} - {bn.upper()} button")

        print("' - Exit")
    except KeyError as e:
        raise Exception(f"Missing control configuration: {e}")

def handle_move(cfg, left_stick):
    try:
        lx, ly = 0.0, 0.0
        mk = cfg["keybinds"]["movement"]

        if is_pressed(mk["forward"]):
            ly = -1.0
        elif is_pressed(mk["backward"]):
            ly = 1.0

        if is_pressed(mk["left"]):
            lx = -1.0
        elif is_pressed(mk["right"]):
            lx = 1.0

        left_stick(lx, ly)
    except KeyError as e:
        raise Exception(f"Missing movement key configuration: {e}")

def handle_mouse(cfg, right_stick, crx, cry, lmt, lmx, lmy):
    try:
        mx, my = mouse.get_position()

        if lmx is not None and lmy is not None:
            dx = mx - lmx
            dy = my - lmy

            sens = cfg["settings"]["mouse_sensitivity"]

            if abs(dx) > 0 or abs(dy) > 0:
                lmt = time.time()

                from .controller import ControllerEmulator
                ce = ControllerEmulator()
                sx = ce.crv(dx, sens)
                sy = ce.crv(dy, sens)

                sx = max(-1.0, min(1.0, sx))
                sy = max(-1.0, min(1.0, sy))

                dz = cfg["settings"]["deadzone_threshold"]
                sx = ce.deadzone(sx, dz)
                sy = ce.deadzone(sy, dz)

                a = 0.25
                crx = (1 - a) * crx + a * sx
                cry = (1 - a) * cry + a * sy
            else:
                ct = time.time()
                if ct - lmt > 0.2:
                    crx = 0.0
                    cry = 0.0

            right_stick(crx, cry)

            if cfg["settings"].get("relative_mouse_mode", False):
                sw = win32api.GetSystemMetrics(0)
                sh = win32api.GetSystemMetrics(1)
                cx, cy = sw // 2, sh // 2
                win32api.SetCursorPos((cx, cy))
                lmx, lmy = cx, cy
            else:
                lmx, lmy = mx, my
        else:
            lmx, lmy = mx, my

        return crx, cry, lmt, lmx, lmy
    except Exception as e:
        raise Exception(f"Mouse handling error: {e}")

def handle_dpad(cfg, gp, dpad, log):
    try:
        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE

        ap = False
        if "dpad" in cfg["keybinds"]:
            for d, k in cfg["keybinds"]["dpad"].items():
                if is_pressed(k):
                    ap = True
                    if d == "up":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH
                    elif d == "down":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH
                    elif d == "left":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST
                    elif d == "right":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST
                    break

        if not ap:
            for bn, k in cfg["keybinds"]["buttons"].items():
                if bn.startswith("dpad_") and is_pressed(k):
                    d = bn.replace("dpad_", "")
                    if d == "up":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH
                    elif d == "down":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH
                    elif d == "left":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST
                    elif d == "right":
                        cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST
                    break

        if cd != dpad:
            dpad = cd
            gp.directional_pad(cd)
            gp.update()

        return dpad
    except KeyError as e:
        log.error(f"Missing d-pad configuration: {e}")
    except Exception as e:
        log.error(f"D-pad handling error: {e}")

def handle_btns(cfg, btn_state, trig, btn_map, log):
    try:
        bm = btn_map()
        for bn, b in cfg["keybinds"]["buttons"].items():
            ip = any_pressed(b)

            if bn in ["l2", "r2"]:
                v = 1.0 if ip else 0.0
                trig(bn, v)
            elif not bn.startswith("dpad_"):
                if bn in bm:
                    btn_state(bm[bn], ip)

    except KeyError as e:
        log.error(f"Missing button configuration: {e}")
    except Exception as e:
        log.error(f"Button handling error: {e}")

def any_pressed(b):
    try:
        if isinstance(b, list):
            return any(is_pressed(x) for x in b)
        return is_pressed(b)
    except Exception as e:
        raise Exception(f"Binding check error for {b}: {e}")

def is_pressed(b):
    if not b:
        return False
    am = {
        'return': 'enter',
    }
    bn = am.get(b.lower(), b.lower())

    if bn.startswith('mouse:'):
        bt = bn.split(':', 1)[1]
        if bt in { 'left', 'right', 'middle', 'x1', 'x2' }:
            try:
                return mouse.is_pressed(bt)
            except Exception:
                return False
        return False
    else:
        try:
            return keyboard.is_pressed(bn)
        except Exception:
            return False
