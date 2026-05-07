import os
import requests
import git
import urllib.parse
import shutil
from datetime import datetime
from cloud_provider import CloudProvider

class GitHubProvider(CloudProvider):
    def __init__(self, username, token, repo_name, local_dir="save_repo"):
        self.username = username
        self.token = token
        self.repo_name = repo_name
        self.local_dir = os.path.abspath(local_dir)
        self.api_base = "https://api.github.com"
        self._repo = None

    def _get_headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def initialize(self):
        """Ensures repo exists on GitHub and is initialized locally."""
        if not self.username or not self.token or not self.repo_name:
            return False, "Missing GitHub credentials or repo name."

        # Check/Create Remote Repo
        exists, msg = self.ensure_repo_exists()
        if not exists:
            return False, msg

        # Initialize Local Repo
        return self.initialize_local_repo()

    def ensure_repo_exists(self):
        url = f"{self.api_base}/repos/{self.username}/{self.repo_name}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                return True, "Repository exists."
            elif response.status_code == 404:
                create_url = f"{self.api_base}/user/repos"
                data = {
                    "name": self.repo_name,
                    "private": True,
                    "description": "OmniNexus Automated Backups"
                }
                create_res = requests.post(create_url, json=data, headers=self._get_headers(), timeout=10)
                if create_res.status_code == 201:
                    return True, "Repository created successfully."
                else:
                    return False, f"Failed to create repository: {create_res.text}"
            else:
                return False, f"Error checking repository: {response.text}"
        except Exception as e:
            return False, f"Network error: {str(e)}"

    def _get_auth_url(self):
        safe_user = urllib.parse.quote(self.username)
        safe_token = urllib.parse.quote(self.token)
        return f"https://{safe_user}:{safe_token}@github.com/{self.username}/{self.repo_name}.git"

    def initialize_local_repo(self):
        auth_url = self._get_auth_url()
        try:
            if os.path.exists(self.local_dir):
                if not os.path.exists(os.path.join(self.local_dir, ".git")):
                    if os.listdir(self.local_dir):
                         os.rename(self.local_dir, f"{self.local_dir}_backup_{int(datetime.now().timestamp())}")
                    self._repo = git.Repo.clone_from(auth_url, self.local_dir)
                else:
                    self._repo = git.Repo(self.local_dir)
                    if self._repo.remotes.origin.url != auth_url:
                        self._repo.remotes.origin.set_url(auth_url)
            else:
                self._repo = git.Repo.clone_from(auth_url, self.local_dir)

            with self._repo.config_writer() as cw:
                cw.set_value("user", "name", self.username)
                cw.set_value("user", "email", f"{self.username}@users.noreply.github.com")

            return True, "Local repo initialized."
        except Exception as e:
            return False, f"Initialization failed: {str(e)}"

    def push(self, local_src_path, relative_remote_path, commit_message=None):
        if not self._repo:
            success, msg = self.initialize()
            if not success: return False, msg

        dest_path = os.path.join(self.local_dir, relative_remote_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        try:
            shutil.copy2(local_src_path, dest_path)

            if commit_message is None:
                commit_message = f"Sync {relative_remote_path} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            self._repo.git.add(A=True)
            if self._repo.is_dirty():
                self._repo.index.commit(commit_message)
                self._repo.remotes.origin.push()
                return True, "GitHub Push successful."
            else:
                return True, "GitHub: Nothing to commit."
        except Exception as e:
            return False, f"GitHub Push failed: {str(e)}"

    def pull(self, relative_remote_path, local_dest_path):
        if not self._repo:
            success, msg = self.initialize()
            if not success: return False, msg
        try:
            self._repo.remotes.origin.pull()

            repo_file_path = os.path.join(self.local_dir, relative_remote_path)
            if os.path.exists(repo_file_path):
                os.makedirs(os.path.dirname(local_dest_path), exist_ok=True)
                shutil.copy2(repo_file_path, local_dest_path)
                return True, "GitHub Pull successful."
            else:
                return False, f"File {relative_remote_path} not found in repository."
        except Exception as e:
            return False, f"GitHub Pull failed: {str(e)}"

    def get_local_repo_path(self):
        return self.local_dir
