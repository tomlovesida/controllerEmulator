import keyboard
import mouse
import win32api
import vgamepad as vg
import time
import threading
import logging
import os
import sys
import json
from .config import load_cfg, save_cfg, def_cfg

class ControllerEmulator:
    def __init__(self):
        self.gp = None
        self.run = False
        self.t = None
        self.lmx = None
        self.lmy = None
        self.crx = 0.0
        self.cry = 0.0
        self.lmt = 0.0
        self.dpad = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE
        self.log = self.setup_log()
        self.cfg = load_cfg(self.log)
        self.setup_ctrl()

    def deadzone(self, v, dz):
        return 0.0 if abs(v) < dz else v

    def crv(self, d, s, e=1.0):
        return s * (abs(d) ** e) * (1 if d > 0 else -1)

    def setup_log(self):
        l = logging.getLogger('ControllerEmulator')
        l.setLevel(logging.INFO)

        if not l.handlers:
            h = logging.StreamHandler()
            f = logging.Formatter('%(levelname)s: %(message)s')
            h.setFormatter(f)
            l.addHandler(h)

        return l

    def setup_ctrl(self):
        try:
            self.gp = vg.VDS4Gamepad()
            self.log.info("DualShock 4 controller emulated successfully!")
        except Exception as e:
            self.log.error(f"Failed to setup controller: {e}")
            raise

    def btn_state(self, btn, pressed):
        try:
            if pressed:
                if btn in [vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS]:
                    self.gp.press_special_button(special_button=btn)
                else:
                    self.gp.press_button(button=btn)
            else:
                if btn in [vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS]:
                    self.gp.release_special_button(special_button=btn)
                else:
                    self.gp.release_button(button=btn)
            self.gp.update()
        except Exception as e:
            self.log.error(f"Failed to set button state: {e}")

    def left_stick(self, x, y):
        try:
            self.gp.left_joystick_float(x_value_float=x, y_value_float=y)
            self.gp.update()
        except Exception as e:
            self.log.error(f"Failed to set left joystick: {e}")

    def right_stick(self, x, y):
        try:
            self.gp.right_joystick_float(x_value_float=x, y_value_float=y)
            self.gp.update()
        except Exception as e:
            self.log.error(f"Failed to set right joystick: {e}")

    def trig(self, t, v):
        try:
            if t == "l2":
                self.gp.left_trigger_float(value_float=v)
            elif t == "r2":
                self.gp.right_trigger_float(value_float=v)
            self.gp.update()
        except Exception as e:
            self.log.error(f"Failed to set {t} trigger: {e}")

    def reset(self):
        try:
            if self.gp:
                self.gp.reset()
                self.gp.update()
            self.crx = 0.0
            self.cry = 0.0
            self.lmt = 0.0
            self.dpad = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE
            self.log.info("Controller reset!")
        except Exception as e:
            self.log.error(f"Failed to reset controller: {e}")

    def btn_map(self):
        return {
            "cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
            "circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
            "square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
            "triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
            "l1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
            "r1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
            "l3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
            "r3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
            "share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
            "options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
            "touchpad": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD,
            "ps": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS
        }

    def change_kb(self, cat, act, nk):
        try:
            if cat in self.cfg["keybinds"] and act in self.cfg["keybinds"][cat]:
                self.cfg["keybinds"][cat][act] = nk
                save_cfg(self.cfg, self.log)
                self.log.info(f"Changed {act} to {nk}")
                return True
            else:
                self.log.error(f"Invalid keybind: {cat}.{act}")
                return False
        except Exception as e:
            self.log.error(f"Failed to change keybind: {e}")
            return False

    def change_set(self, s, v):
        try:
            if s in self.cfg["settings"]:
                self.cfg["settings"][s] = v
                save_cfg(self.cfg, self.log)
                self.log.info(f"Changed {s} to {v}")
                return True
            else:
                self.log.error(f"Invalid setting: {s}")
                return False
        except Exception as e:
            self.log.error(f"Failed to change setting: {e}")
            return False

    def setup_mouse(self):
        try:
            sw = win32api.GetSystemMetrics(0)
            sh = win32api.GetSystemMetrics(1)
            cx, cy = sw // 2, sh // 2
            
            win32api.SetCursorPos((cx, cy))
            self.lmx, self.lmy = mouse.get_position()
            
            if self.cfg["settings"].get("hide_cursor", False):
                win32api.ShowCursor(False)
                
        except Exception as e:
            self.log.error(f"Failed to setup mouse mode: {e}")

    def cleanup_mouse(self):
        try:
            if self.cfg["settings"].get("hide_cursor", False):
                win32api.ShowCursor(True)
        except Exception as e:
            self.log.error(f"Failed to cleanup mouse mode: {e}")

    def start_kb(self):
        if self.run and self.t and self.t.is_alive():
            self.log.warning("Keyboard mapping already running")
            return
            
        self.run = True
        self.log.info("Keyboard and mouse mapping started!")
        self.print_ctrl()
        self.setup_mouse()
        
        self.t = threading.Thread(target=self.input_loop, daemon=True)
        self.t.start()

    def input_loop(self):
        bm = self.btn_map()
        
        while self.run:
            try:
                self.handle_move()
                self.handle_mouse()
                self.handle_dpad()
                self.handle_btns(bm)
                
                if self.is_pressed("'"):
                    self.stop_kb()
                    break
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.error(f"Input handler error: {e}")
                
            time.sleep(0.001)

    def handle_move(self):
        try:
            lx, ly = 0.0, 0.0
            mk = self.cfg["keybinds"]["movement"]
            
            if self.is_pressed(mk["forward"]):
                ly = -1.0
            elif self.is_pressed(mk["backward"]):
                ly = 1.0
            
            if self.is_pressed(mk["left"]):
                lx = -1.0
            elif self.is_pressed(mk["right"]):
                lx = 1.0
            
            self.left_stick(lx, ly)
        except KeyError as e:
            self.log.error(f"Missing movement key configuration: {e}")

    def handle_mouse(self):
        try:
            mx, my = mouse.get_position()
            
            if self.lmx is not None and self.lmy is not None:
                dx = mx - self.lmx
                dy = my - self.lmy
                
                sens = self.cfg["settings"]["mouse_sensitivity"]
                
                if abs(dx) > 0 or abs(dy) > 0:
                    self.lmt = time.time()
                    
                    sx = self.crv(dx, sens)
                    sy = self.crv(dy, sens)
                    
                    sx = max(-1.0, min(1.0, sx))
                    sy = max(-1.0, min(1.0, sy))
                    
                    dz = self.cfg["settings"]["deadzone_threshold"]
                    sx = self.deadzone(sx, dz)
                    sy = self.deadzone(sy, dz)
                    
                    spd = abs(sx - self.crx) + abs(sy - self.cry)
                    a = 0.15 if spd > 0.5 else 0.0
                    self.crx = (1 - a) * self.crx + a * sx if a > 0 else sx
                    self.cry = (1 - a) * self.cry + a * sy if a > 0 else sy
                else:
                    ct = time.time()
                    if ct - self.lmt > 0.05:
                        self.crx = 0.0
                        self.cry = 0.0
                
                self.right_stick(self.crx, self.cry)
                
                if self.cfg["settings"].get("relative_mouse_mode", False):
                    sw = win32api.GetSystemMetrics(0)
                    sh = win32api.GetSystemMetrics(1)
                    cx, cy = sw // 2, sh // 2
                    win32api.SetCursorPos((cx, cy))
                    self.lmx, self.lmy = cx, cy
                else:
                    self.lmx, self.lmy = mx, my
            else:
                self.lmx, self.lmy = mx, my
                
        except Exception as e:
            self.log.error(f"Mouse handling error: {e}")

    def handle_dpad(self):
        try:
            cd = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE
            
            ap = False
            if "dpad" in self.cfg["keybinds"]:
                for d, k in self.cfg["keybinds"]["dpad"].items():
                    if self.is_pressed(k):
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
                for bn, k in self.cfg["keybinds"]["buttons"].items():
                    if bn.startswith("dpad_") and self.is_pressed(k):
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
            
            if cd != self.dpad:
                self.dpad = cd
                self.gp.directional_pad(cd)
                self.gp.update()
                
        except KeyError as e:
            self.log.error(f"Missing d-pad configuration: {e}")
        except Exception as e:
            self.log.error(f"D-pad handling error: {e}")

    def handle_btns(self, bm):
        try:
            for bn, b in self.cfg["keybinds"]["buttons"].items():
                ip = self.any_pressed(b)
                
                if bn in ["l2", "r2"]:
                    v = 1.0 if ip else 0.0
                    self.trig(bn, v)
                elif not bn.startswith("dpad_"):
                    if bn in bm:
                        self.btn_state(bm[bn], ip)
                
        except KeyError as e:
            self.log.error(f"Missing button configuration: {e}")
        except Exception as e:
            self.log.error(f"Button handling error: {e}")

    def any_pressed(self, b):
        try:
            if isinstance(b, list):
                return any(self.is_pressed(x) for x in b)
            return self.is_pressed(b)
        except Exception as e:
            self.log.error(f"Binding check error for {b}: {e}")
            return False

    def is_pressed(self, b):
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

    def stop_kb(self):
        if not self.run:
            return
            
        self.run = False
        self.cleanup_mouse()
        self.crx = 0.0
        self.cry = 0.0
        self.lmt = 0.0
        self.reset()
        
        if self.t and self.t.is_alive():
            self.t.join(timeout=1.0)
            
        self.log.info("Keyboard mapping stopped!")

    def print_ctrl(self):
        try:
            print("Controls:")
            m = self.cfg["keybinds"]["movement"]
            print(f"{m['forward'].upper()}{m['left'].upper()}{m['backward'].upper()}{m['right'].upper()} - Character movement (left joystick)")
            print("Mouse - Camera/look (right joystick)")
            
            b = self.cfg["keybinds"]["buttons"]
            for bn, k in b.items():
                l = str(k).upper()
                print(f"{l} - {bn.upper()} button")
            
            print("' - Exit")
        except KeyError as e:
            self.log.error(f"Missing control configuration: {e}")

    def demo(self):
        self.log.info("Running demo sequence...")

        try:
            self.btn_state(vg.DS4_BUTTONS.DS4_BUTTON_CROSS, True)
            time.sleep(0.5)
            self.btn_state(vg.DS4_BUTTONS.DS4_BUTTON_CROSS, False)

            print("Moving left joystick...")
            mvs = [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
            for x, y in mvs:
                self.left_stick(x, y)
                time.sleep(1.0)

            print("Testing triggers...")
            self.trig("l2", 1.0)
            time.sleep(0.5)
            self.trig("r2", 1.0)
            time.sleep(0.5)

            self.reset()
            self.log.info("Demo sequence completed!")

        except Exception as e:
            self.log.error(f"Demo sequence failed: {e}")

    def show_menu(self):
        mo = {
            "1": ("Change movement keys", self.change_move_keys),
            "2": ("Change button keys", self.change_btn_keys),
            "3": ("Change mouse sensitivity", self.change_sens),
            "4": ("Change deadzone threshold", self.change_dz),
            "5": ("Toggle relative mouse mode", self.toggle_rel_mouse),
            "6": ("Toggle cursor visibility", self.toggle_cursor),
            "7": ("Show current config", self.show_cfg),
            "8": ("Back to main menu", None)
        }
        
        while True:
            print("\n=== Configuration Menu ===")
            for k, (d, _) in mo.items():
                print(f"{k}. {d}")
            
            c = input("Enter choice (1-8): ").strip()
            
            if c in mo:
                _, a = mo[c]
                if a is None:
                    break
                try:
                    a()
                except Exception as e:
                    self.log.error(f"Menu action failed: {e}")
            else:
                print("Invalid choice. Please try again.")

    def change_sens(self):
        try:
            cur = self.cfg['settings']['mouse_sensitivity']
            ns = float(input(f"Current sensitivity: {cur}\nNew sensitivity: "))
            self.change_set("mouse_sensitivity", ns)
        except ValueError:
            print("Invalid number")

    def change_dz(self):
        try:
            cur = self.cfg['settings']['deadzone_threshold']
            nt = float(input(f"Current threshold: {cur}\nNew threshold: "))
            self.change_set("deadzone_threshold", nt)
        except ValueError:
            print("Invalid number")

    def toggle_rel_mouse(self):
        cur = self.cfg['settings'].get('relative_mouse_mode', False)
        self.change_set("relative_mouse_mode", not cur)

    def toggle_cursor(self):
        cur = self.cfg['settings'].get('hide_cursor', False)
        self.change_set("hide_cursor", not cur)

    def show_cfg(self):
        print(json.dumps(self.cfg, indent=2))

    def change_move_keys(self):
        mvs = ["forward", "backward", "left", "right"]
        for m in mvs:
            try:
                cur = self.cfg["keybinds"]["movement"][m]
                nk = input(f"Change {m} (current: {cur}): ").strip()
                if nk:
                    self.change_kb("movement", m, nk)
            except KeyError:
                self.log.error(f"Missing movement key: {m}")

    def change_btn_keys(self):
        for bn in self.cfg["keybinds"]["buttons"]:
            try:
                cur = self.cfg["keybinds"]["buttons"][bn]
                nk = input(f"Change {bn} (current: {cur}): ").strip()
                if nk:
                    self.change_kb("buttons", bn, nk)
            except KeyError:
                self.log.error(f"Missing button key: {bn}")
