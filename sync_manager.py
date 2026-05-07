import os
import json
import shutil
from datetime import datetime
from github_provider import GitHubProvider
from local_provider import LocalCloudProvider
from game_scanner import GameScanner

class SyncManager:
    def __init__(self, config_path="sync_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.provider = None
        self._init_provider()
        self.scanner = GameScanner(
            citra_path=self.config.get("citra_path"),
            gba_saves_path=self.config.get("gba_saves_path"),
            ryujinx_path=self.config.get("ryujinx_path"),
            yuzu_path=self.config.get("yuzu_path"),
            desmume_path=self.config.get("desmume_path")
        )

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "provider_type": "github", # github or local
            "github_username": "",
            "github_token": "",
            "github_repo_name": "pokesync-saves",
            "local_cloud_path": "",
            "citra_path": "",
            "gba_saves_path": "",
            "ryujinx_path": "",
            "yuzu_path": "",
            "desmume_path": ""
        }

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def _init_provider(self):
        provider_type = self.config.get("provider_type", "github")
        if provider_type == "github":
            if self.config.get("github_username") and self.config.get("github_token"):
                self.provider = GitHubProvider(
                    self.config["github_username"],
                    self.config["github_token"],
                    self.config["github_repo_name"]
                )
        elif provider_type == "local":
            if self.config.get("local_cloud_path"):
                self.provider = LocalCloudProvider(
                    self.config["local_cloud_path"]
                )

    def update_config(self, new_config):
        self.config.update(new_config)
        self.save_config()
        self._init_provider()
        # Update scanner if paths changed
        self.scanner = GameScanner(
            citra_path=self.config.get("citra_path"),
            gba_saves_path=self.config.get("gba_saves_path"),
            ryujinx_path=self.config.get("ryujinx_path"),
            yuzu_path=self.config.get("yuzu_path"),
            desmume_path=self.config.get("desmume_path")
        )

    def get_games(self):
        return self.scanner.scan_all()

    def sync_push(self, game):
        if not self.provider:
            return False, "Sync provider not configured."

        # Copy file to cloud
        # Structure: <platform>/<game_id>/main
        platform = game['platform']
        game_id = game['id']
        filename = os.path.basename(game['local_path'])
        relative_path = os.path.join(platform, game_id, filename)

        try:
            # Create local backup before pushing
            self._create_local_backup(game)

            # Provider push
            return self.provider.push(game['local_path'], relative_path, f"Update {platform} save: {game['name']}")
        except Exception as e:
            return False, f"Sync push failed: {str(e)}"

    def sync_pull(self, game):
        if not self.provider:
            return False, "Sync provider not configured."

        platform = game['platform']
        game_id = game['id']
        filename = os.path.basename(game['local_path'])
        relative_path = os.path.join(platform, game_id, filename)

        try:
            # Backup current local save before overwriting
            self._create_local_backup(game)

            success, msg = self.provider.pull(relative_path, game['local_path'])
            if success:
                return True, f"Pulled {game['name']} from {self.config.get('provider_type')}."
            return False, msg
        except Exception as e:
            return False, f"Sync pull failed: {str(e)}"

    def sync_push_all(self):
        """Pushes all detected game saves to cloud."""
        if not self.provider:
            return False, "Sync provider not configured."

        games = self.get_games()
        if not games:
            return True, "No games detected."

        success_count = 0
        for game in games:
            success, _ = self.sync_push(game)
            if success:
                success_count += 1

        return True, f"Successfully synced {success_count}/{len(games)} games to cloud."

    def sync_manifest_push(self, manifest_path):
        if not self.provider:
            return False, "Sync provider not configured."

        filename = os.path.basename(manifest_path)
        relative_path = os.path.join("manifests", filename)

        return self.provider.push(manifest_path, relative_path, f"Update translation manifest: {filename}")

    def sync_manifest_pull(self, manifest_path):
        if not self.provider:
            return False, "Sync provider not configured."

        filename = os.path.basename(manifest_path)
        relative_path = os.path.join("manifests", filename)

        return self.provider.pull(relative_path, manifest_path)

    def _create_local_backup(self, game):
        if os.path.exists(game['local_path']):
            backup_dir = os.path.abspath(os.path.join("backups", game['platform'], game['id']))
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.basename(game['local_path'])}.bak_{timestamp}"
            shutil.copy2(game['local_path'], os.path.join(backup_dir, backup_name))
