import os
import sys
import argparse
from color_constants import SUCCESS, INFO, WARNING, ERROR, HEADER, RESET
from sync_manager import SyncManager

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    from PIL import Image
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class PokeSyncApp(ctk.CTk if GUI_AVAILABLE else object):
    def __init__(self, manager):
        if not GUI_AVAILABLE:
            raise ImportError("customtkinter and Pillow not found. Please install them to use the GUI.")

        super().__init__()
        self.manager = manager
        self.title("PokeSync - Universal Save Sync")
        self.geometry("450x800") # Mobile-style aspect ratio

        # UI State
        self.current_view = None
        self.current_platform = "All"
        self.search_query = ""

        self.setup_ui()

    def setup_ui(self):
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Main content area
        self.grid_rowconfigure(1, weight=0) # Bottom Nav bar

        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")

        self.nav_bar = ctk.CTkFrame(self, height=70, corner_radius=0)
        self.nav_bar.grid(row=1, column=0, sticky="nsew")
        self.nav_bar.grid_propagate(False)

        self.nav_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.home_btn = ctk.CTkButton(self.nav_bar, text="Home", corner_radius=20,
                                     command=lambda: self.show_view("Home"))
        self.home_btn.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

        self.settings_btn = ctk.CTkButton(self.nav_bar, text="Settings", corner_radius=20,
                                         command=lambda: self.show_view("Settings"))
        self.settings_btn.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")

        self.utils_btn = ctk.CTkButton(self.nav_bar, text="Utils", corner_radius=20,
                                      command=lambda: self.show_view("Utils"))
        self.utils_btn.grid(row=0, column=2, padx=5, pady=10, sticky="nsew")

        self.show_view("Home")

    def show_view(self, view_name):
        self.current_view = view_name

        # Update button styles
        self.home_btn.configure(fg_color=("gray75", "gray25") if view_name != "Home" else ["#3B8ED0", "#1F6AA5"])
        self.settings_btn.configure(fg_color=("gray75", "gray25") if view_name != "Settings" else ["#3B8ED0", "#1F6AA5"])
        self.utils_btn.configure(fg_color=("gray75", "gray25") if view_name != "Utils" else ["#3B8ED0", "#1F6AA5"])

        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        if view_name == "Home":
            self._render_home()
        elif view_name == "Settings":
            self._render_settings()
        elif view_name == "Utils":
            self._render_utils()

    def _render_home(self):
        # Header / Search Bar
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header_frame, text="Explore", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")

        search_frame = ctk.CTkFrame(self.main_container, fg_color=("gray90", "gray15"), corner_radius=15)
        search_frame.pack(fill="x", padx=20, pady=10)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search games...",
                                        border_width=0, fg_color="transparent")
        self.search_entry.pack(fill="x", padx=10, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_games)

        # Category Filter Chips
        filter_frame = ctk.CTkScrollableFrame(self.main_container, orientation="horizontal",
                                             height=40, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=5)

        categories = ["All", "GBA", "Citra", "Ryujinx", "Yuzu"]
        self.category_btns = {}

        for cat in categories:
            btn = ctk.CTkButton(filter_frame, text=cat, width=80, corner_radius=20,
                               command=lambda c=cat: self.set_platform_filter(c))
            btn.pack(side="left", padx=5)
            self.category_btns[cat] = btn

        self._update_chip_styles()

        # Recommended Carousel
        ctk.CTkLabel(self.main_container, text="Recommended",
                    font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        self.carousel_frame = ctk.CTkScrollableFrame(self.main_container, orientation="horizontal",
                                                    height=180, fg_color="transparent")
        self.carousel_frame.pack(fill="x", padx=10)

        # All Games Vertical List
        ctk.CTkLabel(self.main_container, text="All Games",
                    font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        self.games_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.games_frame.pack(fill="both", expand=True, padx=10)

        self.refresh_home_lists()

    def _render_settings(self):
        scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_frame, text="Settings", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")

        ctk.CTkLabel(scroll_frame, text="GitHub Configuration", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
        self.user_entry = self._create_setting(scroll_frame, "Username", self.manager.config["github_username"])
        self.token_entry = self._create_setting(scroll_frame, "Token (PAT)", self.manager.config["github_token"], show="*")
        self.repo_entry = self._create_setting(scroll_frame, "Repo Name", self.manager.config["github_repo_name"])

        ctk.CTkLabel(scroll_frame, text="Emulator Paths", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.gba_path_entry = self._create_setting(scroll_frame, "GBA Saves Path", self.manager.config.get("gba_saves_path", ""))
        self.citra_path_entry = self._create_setting(scroll_frame, "Citra Path", self.manager.config.get("citra_path", ""))

        ctk.CTkButton(scroll_frame, text="Save & Refresh", corner_radius=10,
                     command=self.save_settings).pack(pady=30, padx=20, fill="x")

    def _render_utils(self):
        ctk.CTkLabel(self.main_container, text="Utilities", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")

        utils_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        utils_frame.pack(fill="both", expand=True, padx=20, pady=10)

        utils = [
            ("ROM Translation", "Launch Omni-Translate", "python3 omni.py --help"),
            ("AI Save Backup", "Launch Save-State Backup", "python3 save_backup.py --help"),
            ("macOS Tagger", "Tag ROMs with Metadata", "python3 mac_rom_tagger.py --help"),
            ("Real-time Translator", "Overlay Translation", "python3 translator.py --help")
        ]

        for name, desc, cmd in utils:
            card = ctk.CTkFrame(utils_frame, corner_radius=15)
            card.pack(fill="x", pady=10)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=15)

            ctk.CTkLabel(info_frame, text=name, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=desc, font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")

            ctk.CTkButton(card, text="Open Help", width=80, corner_radius=10,
                         command=lambda c=cmd: self._launch_util(c)).pack(side="right", padx=15)

    def _launch_util(self, command):
        # In a real app, this might launch a new process or window
        # For now, we'll just show a message or print to console
        print(f"Launching utility: {command}")
        messagebox.showinfo("Utility", f"This would launch: {command}\n(Functionality limited in demo)")

    def _create_setting(self, parent, label, value, show=None):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=20)
        entry = ctk.CTkEntry(parent, show=show)
        entry.insert(0, value)
        entry.pack(fill="x", padx=20, pady=(0, 10))
        return entry

    def filter_games(self, event=None):
        self.search_query = self.search_entry.get().lower()
        self.refresh_home_lists()

    def set_platform_filter(self, platform):
        self.current_platform = platform
        self._update_chip_styles()
        self.refresh_home_lists()

    def _update_chip_styles(self):
        for cat, btn in self.category_btns.items():
            if cat == self.current_platform:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text_color="white")
            else:
                btn.configure(fg_color=("gray85", "gray25"), text_color=("black", "white"))

    def refresh_home_lists(self):
        # Clear existing
        for widget in self.carousel_frame.winfo_children():
            widget.destroy()
        for widget in self.games_frame.winfo_children():
            widget.destroy()

        all_games = self.manager.get_games()

        # Apply filters
        filtered_games = []
        for game in all_games:
            matches_search = self.search_query in game['name'].lower() or \
                             self.search_query in game['platform'].lower()
            matches_platform = self.current_platform == "All" or \
                               game['platform'] == self.current_platform

            if matches_search and matches_platform:
                filtered_games.append(game)

        # Recommended (subset, first 4)
        for game in filtered_games[:4]:
            self._create_game_card(self.carousel_frame, game, horizontal=True)

        # All Games
        if not filtered_games:
            ctk.CTkLabel(self.games_frame, text="No games found").pack(pady=20)
        else:
            for game in filtered_games:
                self._create_game_card(self.games_frame, game, horizontal=False)

    def _create_game_card(self, parent, game, horizontal=False):
        if horizontal:
            card = ctk.CTkFrame(parent, width=150, height=160, corner_radius=15)
            card.pack(side="left", padx=10, pady=5)
            card.pack_propagate(False)

            # Platform Tag
            tag_color = self._get_platform_color(game['platform'])
            ctk.CTkLabel(card, text=game['platform'], font=ctk.CTkFont(size=10),
                        fg_color=tag_color, text_color="white", corner_radius=5).pack(pady=(10, 5))

            ctk.CTkLabel(card, text=game['name'], font=ctk.CTkFont(size=13, weight="bold"),
                        wraplength=130).pack(pady=5)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="bottom", pady=10)
            ctk.CTkButton(btn_frame, text="↑", width=40, fg_color="green",
                         command=lambda: self.sync_action("push", game)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="↓", width=40, fg_color="blue",
                         command=lambda: self.sync_action("pull", game)).pack(side="left", padx=2)
        else:
            card = ctk.CTkFrame(parent, corner_radius=10)
            card.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(card, text=game['name'], font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=10)

            # Actions on the right
            ctk.CTkButton(card, text="Pull", width=60, fg_color="blue",
                         command=lambda g=game: self.sync_action("pull", g)).pack(side="right", padx=5)
            ctk.CTkButton(card, text="Push", width=60, fg_color="green",
                         command=lambda g=game: self.sync_action("push", g)).pack(side="right", padx=5)

            tag_color = self._get_platform_color(game['platform'])
            ctk.CTkLabel(card, text=game['platform'], font=ctk.CTkFont(size=10),
                        fg_color=tag_color, text_color="white", corner_radius=5).pack(side="right", padx=10)

    def _get_platform_color(self, platform):
        colors = {
            "GBA": "#2ecc71",
            "Citra": "#f1c40f",
            "Ryujinx": "#e67e22",
            "Yuzu": "#3498db"
        }
        return colors.get(platform, "#95a5a6")

    def save_settings(self):
        new_config = {
            "github_username": self.user_entry.get(),
            "github_token": self.token_entry.get(),
            "github_repo_name": self.repo_entry.get(),
            "gba_saves_path": self.gba_path_entry.get(),
            "citra_path": self.citra_path_entry.get()
        }
        self.manager.update_config(new_config)
        messagebox.showinfo("Success", "Settings saved.")
        # Optionally refresh games if on home, but here we just confirm.

    def refresh_games(self):
        if self.current_view == "Home":
            self.refresh_home_lists()

    def sync_action(self, action, game):
        if action == "push":
            success, msg = self.manager.sync_push(game)
        else:
            success, msg = self.manager.sync_pull(game)

        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

def cli_main():
    parser = argparse.ArgumentParser(description="PokeSync CLI")
    parser.add_argument("--list", action="store_true", help="List detected games")
    parser.add_argument("--push", help="Push save for game ID")
    parser.add_argument("--pull", help="Pull save for game ID")
    parser.add_argument("--platform", help="Platform for push/pull (Citra, GBA, Ryujinx, Yuzu)")

    args = parser.parse_args()
    manager = SyncManager()

    if args.list:
        games = manager.get_games()
        # Header adjusted to align with the [*] prefix (4 chars: \033[96m\033[1m[*]\033[0m )
        # Actually it is just 4 chars printed: [*] plus one space.
        print(f"{HEADER}     {'Platform':<10} {'ID':<20} {'Name'}{RESET}")
        print("-" * 55)
        for g in games:
            print(f"{INFO} {g['platform']:<10} {g['id']:<20} {g['name']}")

    elif args.push:
        games = [g for g in manager.get_games() if g['id'] == args.push]
        if args.platform:
            games = [g for g in games if g['platform'].lower() == args.platform.lower()]

        if not games:
            print(f"{ERROR} Game {args.push} not found.")
        else:
            success, msg = manager.sync_push(games[0])
            if success:
                print(f"{SUCCESS} {msg}")
            else:
                print(f"{ERROR} {msg}")

    elif args.pull:
        games = [g for g in manager.get_games() if g['id'] == args.pull]
        if args.platform:
            games = [g for g in games if g['platform'].lower() == args.platform.lower()]

        if not games:
            print(f"{ERROR} Game {args.pull} not found.")
        else:
            success, msg = manager.sync_pull(games[0])
            if success:
                print(f"{SUCCESS} {msg}")
            else:
                print(f"{ERROR} {msg}")
    else:
        if GUI_AVAILABLE:
            app = PokeSyncApp(manager)
            app.mainloop()
        else:
            parser.print_help()

if __name__ == "__main__":
    cli_main()
