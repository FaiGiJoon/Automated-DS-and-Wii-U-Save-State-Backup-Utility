import os
import sys
import argparse
from sync_manager import SyncManager

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class PokeSyncApp(ctk.CTk if GUI_AVAILABLE else object):
    def __init__(self, manager):
        if not GUI_AVAILABLE:
            raise ImportError("customtkinter not found. Please install it to use the GUI.")

        super().__init__()
        self.manager = manager
        self.title("PokeSync - Universal Save Sync")
        self.geometry("800x600")

        self.setup_ui()

    def setup_ui(self):
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar for settings
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="GitHub Settings", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        self.user_entry = self._create_setting("Username", self.manager.config["github_username"])
        self.token_entry = self._create_setting("Token (PAT)", self.manager.config["github_token"], show="*")
        self.repo_entry = self._create_setting("Repo Name", self.manager.config["github_repo_name"])

        ctk.CTkLabel(self.sidebar, text="Emulator Paths", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        self.gba_path_entry = self._create_setting("GBA Saves Path", self.manager.config.get("gba_saves_path", ""))
        self.citra_path_entry = self._create_setting("Citra Path", self.manager.config.get("citra_path", ""))

        ctk.CTkButton(self.sidebar, text="Save & Refresh", command=self.save_settings).pack(pady=20)

        # Main area for games
        self.main_frame = ctk.CTkScrollableFrame(self, label_text="Detected Games")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.refresh_games()

    def _create_setting(self, label, value, show=None):
        ctk.CTkLabel(self.sidebar, text=label).pack(anchor="w", padx=10)
        entry = ctk.CTkEntry(self.sidebar, show=show)
        entry.insert(0, value)
        entry.pack(fill="x", padx=10, pady=(0, 10))
        return entry

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
        self.refresh_games()

    def refresh_games(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        games = self.manager.get_games()
        if not games:
            ctk.CTkLabel(self.main_frame, text="No games detected. Check emulator paths in config.").pack(pady=20)
            return

        for game in games:
            frame = ctk.CTkFrame(self.main_frame)
            frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(frame, text=f"{game['platform']}: {game['name']}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

            ctk.CTkButton(frame, text="Push", width=60, fg_color="green", command=lambda g=game: self.sync_action("push", g)).pack(side="right", padx=5, pady=5)
            ctk.CTkButton(frame, text="Pull", width=60, fg_color="blue", command=lambda g=game: self.sync_action("pull", g)).pack(side="right", padx=5, pady=5)

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
        print(f"{'Platform':<10} {'ID':<20} {'Name'}")
        print("-" * 50)
        for g in games:
            print(f"{g['platform']:<10} {g['id']:<20} {g['name']}")

    elif args.push:
        games = [g for g in manager.get_games() if g['id'] == args.push]
        if args.platform:
            games = [g for g in games if g['platform'].lower() == args.platform.lower()]

        if not games:
            print(f"Game {args.push} not found.")
        else:
            success, msg = manager.sync_push(games[0])
            print(msg)

    elif args.pull:
        games = [g for g in manager.get_games() if g['id'] == args.pull]
        if args.platform:
            games = [g for g in games if g['platform'].lower() == args.platform.lower()]

        if not games:
            print(f"Game {args.pull} not found.")
        else:
            success, msg = manager.sync_pull(games[0])
            print(msg)
    else:
        if GUI_AVAILABLE:
            app = PokeSyncApp(manager)
            app.mainloop()
        else:
            parser.print_help()

if __name__ == "__main__":
    cli_main()
