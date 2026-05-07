import os
import shutil
from datetime import datetime
from cloud_provider import CloudProvider

class LocalCloudProvider(CloudProvider):
    """
    Simulates a cloud provider using a local folder that is synced
    by a service like Google Drive, Dropbox, or OneDrive.
    """
    def __init__(self, cloud_folder_path):
        self.cloud_folder_path = os.path.abspath(cloud_folder_path)

    def initialize(self):
        try:
            if not os.path.exists(self.cloud_folder_path):
                os.makedirs(self.cloud_folder_path)
            return True, f"Local cloud folder initialized at {self.cloud_folder_path}"
        except Exception as e:
            return False, f"Failed to initialize local cloud folder: {str(e)}"

    def push(self, local_src_path, relative_remote_path, commit_message=None):
        dest_path = os.path.join(self.cloud_folder_path, relative_remote_path)
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(local_src_path, dest_path)
            return True, f"Synced to cloud folder: {relative_remote_path}"
        except Exception as e:
            return False, f"Cloud folder push failed: {str(e)}"

    def pull(self, relative_remote_path, local_dest_path):
        src_path = os.path.join(self.cloud_folder_path, relative_remote_path)
        if not os.path.exists(src_path):
            return False, f"File {relative_remote_path} not found in cloud folder ({src_path})."

        try:
            if os.path.dirname(local_dest_path):
                os.makedirs(os.path.dirname(local_dest_path), exist_ok=True)
            shutil.copy2(src_path, local_dest_path)
            return True, f"Pulled from cloud folder: {relative_remote_path}"
        except Exception as e:
            return False, f"Cloud folder pull failed: {str(e)}"
