import os
import requests
import git
import urllib.parse
from datetime import datetime

class GitHubProvider:
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

    def ensure_repo_exists(self):
        """Checks if the repository exists on GitHub, and creates it if it doesn't."""
        if not self.username or not self.token or not self.repo_name:
            return False, "Missing GitHub credentials or repo name."

        url = f"{self.api_base}/repos/{self.username}/{self.repo_name}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                return True, "Repository exists."
            elif response.status_code == 404:
                # Create the repo
                create_url = f"{self.api_base}/user/repos"
                data = {
                    "name": self.repo_name,
                    "private": True,
                    "description": "PokeSync Automated Save Backups"
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
        """Clones or opens the local repository."""
        auth_url = self._get_auth_url()
        try:
            if os.path.exists(self.local_dir):
                if not os.path.exists(os.path.join(self.local_dir, ".git")):
                    import shutil
                    # If directory exists but isn't a git repo, we might need to be careful.
                    # For PokeSync style, we just clear and clone if it's not a git repo.
                    if os.listdir(self.local_dir):
                         # Not empty, and not a git repo.
                         # To be safe, we could backup or just rename.
                         os.rename(self.local_dir, f"{self.local_dir}_backup_{int(datetime.now().timestamp())}")

                    self._repo = git.Repo.clone_from(auth_url, self.local_dir)
                else:
                    self._repo = git.Repo(self.local_dir)
                    # Ensure remote URL is correct (in case token changed)
                    if self._repo.remotes.origin.url != auth_url:
                        self._repo.remotes.origin.set_url(auth_url)
            else:
                self._repo = git.Repo.clone_from(auth_url, self.local_dir)
            return True, "Local repo initialized."
        except Exception as e:
            return False, f"Initialization failed: {str(e)}"

    def pull(self):
        if not self._repo:
            success, msg = self.initialize_local_repo()
            if not success: return False, msg
        try:
            self._repo.remotes.origin.pull()
            return True, "Pull successful."
        except Exception as e:
            return False, f"Pull failed: {str(e)}"

    def push(self, commit_message=None):
        if not self._repo:
            success, msg = self.initialize_local_repo()
            if not success: return False, msg

        if commit_message is None:
            commit_message = f"Sync saves - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        try:
            self._repo.git.add(A=True)
            if self._repo.is_dirty():
                self._repo.index.commit(commit_message)
                self._repo.remotes.origin.push()
                return True, "Push successful."
            else:
                return True, "Nothing to commit."
        except Exception as e:
            return False, f"Push failed: {str(e)}"

    def get_local_path(self, relative_path):
        return os.path.join(self.local_dir, relative_path)
