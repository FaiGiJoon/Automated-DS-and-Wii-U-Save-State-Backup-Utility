from abc import ABC, abstractmethod

class CloudProvider(ABC):
    @abstractmethod
    def push(self, local_path, relative_remote_path, commit_message=None):
        """Pushes a file to the cloud provider."""
        pass

    @abstractmethod
    def pull(self, relative_remote_path, local_dest_path):
        """Pulls a file from the cloud provider."""
        pass

    @abstractmethod
    def initialize(self):
        """Initializes the provider (e.g., clones repo, checks directory)."""
        pass
