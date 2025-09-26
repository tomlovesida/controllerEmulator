import os
import logging
from src.controller import ControllerEmulator

def main():
    print("Kois PS4 Controller Emulater")
    print("===============================================")

    try:
        emu = ControllerEmulator()

        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nOptions:")
            print("1. Start keyboard and mouse mapping")
            print("2. Run demo sequence")
            print("3. Reset controller")
            print("4. Configuration menu")
            print("5. Exit")

            c = input("Enter your choice (1-5): ").strip()

            if c == "1":
                emu.start_kb()
            elif c == "2":
                emu.demo()
            elif c == "3":
                emu.reset()
            elif c == "4":
                emu.show_menu()
            elif c == "5":
                print("Exiting...")
                if emu.run:
                    emu.stop_kb()
                break
            else:
                print("Invalid choice. Please try again.")

    except Exception as e:
        logging.error(f"Application error: {e}")
        print("Make sure ViGEmBus driver is installed and vgamepad library is available.")

if __name__ == "__main__":
    main()
