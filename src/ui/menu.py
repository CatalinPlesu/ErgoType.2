import signal
import sys
import os
import tty
import termios

class Menu:
    def __init__(self, title="Menu"):
        self.title = title
        self.items = []            # list of callables
        self.selected = 0
        self.header = None
        self.footer = None

    def add_item(self, func):
        """func(True) -> title; func(False) -> execution code"""
        self.items.append(func)

    def _clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _get_key(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            k = sys.stdin.read(1)

            if not k:
                return None

            if ord(k) in (10, 13):   # Enter
                return "enter"
            if ord(k) == 3:          # Ctrl+C
                raise KeyboardInterrupt
            if ord(k) == 9:          # Tab
                return "down"
            if ord(k) == 27:         # escape or arrow
                k2 = sys.stdin.read(1)
                if k2 == '[':
                    k3 = sys.stdin.read(1)
                    return {
                        'A': 'up',
                        'B': 'down',
                        'C': 'right',
                        'D': 'left'
                    }.get(k3, None)
                return "escape"

            if k.isdigit():
                return k

            return k.lower()

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _draw(self):
        self._clear()
        title_block = f"=== {self.title} ==="
        print(title_block)

        if self.header:
            print('-' * len(title_block))
            print(self.header)
            print('-' * len(title_block))

        print()

        # index 0 = Exit
        menu_len = len(self.items) + 1
        for idx in range(menu_len):
            label = "Exit" if idx == 0 else self.items[idx - 1](True)

            if idx == self.selected:
                print(f"\033[7m {idx}. {label} \033[0m")
            else:
                print(f" {idx}. {label}")

        print("\nUse arrows or numbers. Enter to select. Esc to exit.")

        if self.footer:
            print('-' * len(title_block))
            print(self.footer)
            print('-' * len(title_block))

    def run(self):
        running = True

        while running:
            try:
                self._draw()
                key = self._get_key()

                if key in ("up", "k"):
                    self.selected = (self.selected - 1) % (len(self.items) + 1)

                elif key in ("down", "j", "tab"):
                    self.selected = (self.selected + 1) % (len(self.items) + 1)

                elif key in ("escape", "left", "h"):
                    running = False

                elif key == "enter":
                    self._clear()
                    if self.selected == 0:
                        running = False
                    else:
                        self.items[self.selected - 1](False)
                        input("\nPress Enter to return...")

                elif key and key.isdigit():
                    num = int(key)
                    if 0 <= num <= len(self.items):
                        self.selected = num

            except KeyboardInterrupt:
                print("\n\nInterrupted. Exiting...")
                sys.exit(0)

        print("Exited menu.")
