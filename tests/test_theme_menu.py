import unittest
import tkinter as tk

from game.screens.friend_list import FriendListPanel


class ThemeMenuTests(unittest.TestCase):
    def test_friend_list_uses_app_theme_colors(self):
        root = tk.Tk()
        root.withdraw()
        try:
            class DummyApp:
                def __init__(self):
                    self.data = {"social": {}, "options": {"friend_list_collapsed": True}}
                    self._lang = {"code": "en"}
                    self.f_small = ("Arial", 9)
                    self.f_menu_btn = ("Arial", 10, "bold")
                    self.BG_PANEL = "#123456"
                    self.BG_MID = "#abcdef"
                    self.BTN_DEFAULT = "#654321"
                    self.GOLD = "#112233"
                    self.MENU_BTN_ACT = "#445566"
                    self.SILVER = "#778899"
                    self.TEXT_DISABLED = "#aabbcc"
                    self.WHITE = "#ddeeff"

            app = DummyApp()
            parent = tk.Frame(root)
            panel = FriendListPanel(app, parent)

            self.assertEqual(panel.panel.cget("bg"), "#123456")
            self.assertEqual(panel.open_button.cget("bg"), "#654321")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
