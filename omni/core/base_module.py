from abc import ABC, abstractmethod

class BaseModule(ABC):
    """
    Interface for platform-specific translation modules.
    """

    def __init__(self, file_path, output_path=None):
        self.file_path = file_path
        self.output_path = output_path or f"translated_{file_path}"
        self.manifest = {}

    @abstractmethod
    def extract_strings(self):
        """
        Extract strings from the target file into self.manifest.
        Returns a dictionary {id: {"original": text, "translation": None, "metadata": {}}}.
        """
        pass

    @abstractmethod
    def inject_strings(self, translations):
        """
        Inject translated strings back into the target file.
        translations: {id: translated_text}
        """
        pass

    def get_manifest(self):
        return self.manifest
