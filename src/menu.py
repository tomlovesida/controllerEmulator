import json

def show_menu(emu):
    mo = {
        "1": ("Change movement keys", emu.change_move_keys),
        "2": ("Change button keys", emu.change_btn_keys),
        "3": ("Change mouse sensitivity", emu.change_sens),
        "4": ("Change deadzone threshold", emu.change_dz),
        "5": ("Toggle relative mouse mode", emu.toggle_rel_mouse),
        "6": ("Toggle cursor visibility", emu.toggle_cursor),
        "7": ("Show current config", emu.show_cfg),
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
                emu.log.error(f"Menu action failed: {e}")
        else:
            print("Invalid choice. Please try again.")

def change_sens(emu):
    try:
        cur = emu.cfg['settings']['mouse_sensitivity']
        ns = float(input(f"Current sensitivity: {cur}\nNew sensitivity: "))
        emu.change_set("mouse_sensitivity", ns)
    except ValueError:
        print("Invalid number")

def change_dz(emu):
    try:
        cur = emu.cfg['settings']['deadzone_threshold']
        nt = float(input(f"Current threshold: {cur}\nNew threshold: "))
        emu.change_set("deadzone_threshold", nt)
    except ValueError:
        print("Invalid number")

def toggle_rel_mouse(emu):
    cur = emu.cfg['settings'].get('relative_mouse_mode', False)
    emu.change_set("relative_mouse_mode", not cur)

def toggle_cursor(emu):
    cur = emu.cfg['settings'].get('hide_cursor', False)
    emu.change_set("hide_cursor", not cur)

def show_cfg(emu):
    print(json.dumps(emu.cfg, indent=2))

def change_move_keys(emu):
    mvs = ["forward", "backward", "left", "right"]
    for m in mvs:
        try:
            cur = emu.cfg["keybinds"]["movement"][m]
            nk = input(f"Change {m} (current: {cur}): ").strip()
            if nk:
                emu.change_kb("movement", m, nk)
        except KeyError:
            emu.log.error(f"Missing movement key: {m}")

def change_btn_keys(emu):
    for bn in emu.cfg["keybinds"]["buttons"]:
        try:
            cur = emu.cfg["keybinds"]["buttons"][bn]
            nk = input(f"Change {bn} (current: {cur}): ").strip()
            if nk:
                emu.change_kb("buttons", bn, nk)
        except KeyError:
            emu.log.error(f"Missing button key: {bn}")
