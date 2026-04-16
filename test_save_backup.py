import os
import shutil
import time
import unittest
from datetime import datetime
from save_backup import copy_with_timestamp, prune_backups, SaveBackupHandler

class TestSaveBackup(unittest.TestCase):
    def setUp(self):
        self.test_source = os.path.abspath("test_source")
        self.test_backup = os.path.abspath("test_backup")
        os.makedirs(self.test_source, exist_ok=True)
        os.makedirs(self.test_backup, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_source):
            shutil.rmtree(self.test_source)
        if os.path.exists(self.test_backup):
            shutil.rmtree(self.test_backup)

    def test_copy_with_timestamp(self):
        test_file = os.path.join(self.test_source, "test.sav")
        with open(test_file, "w") as f:
            f.write("test data")
        
        # Set old mtime on source file
        old_time = time.time() - (10 * 86400)
        os.utime(test_file, (old_time, old_time))
        
        backup_path = copy_with_timestamp(test_file, self.test_backup)
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup mtime is recent, not from source
        self.assertGreater(os.path.getmtime(backup_path), time.time() - 60)

    def test_prune_backups_pattern(self):
        # Create a valid backup
        valid_backup = os.path.join(self.test_backup, "game_20230101_120000_123456.sav")
        with open(valid_backup, "w") as f:
            f.write("valid")
        
        # Create an invalid file that should NOT be pruned even if old
        important_file = os.path.join(self.test_backup, "important.txt")
        with open(important_file, "w") as f:
            f.write("dont delete me")
        
        old_time = time.time() - (8 * 86400)
        os.utime(valid_backup, (old_time, old_time))
        os.utime(important_file, (old_time, old_time))
        
        prune_backups(self.test_backup, days=7)
        
        self.assertFalse(os.path.exists(valid_backup))
        self.assertTrue(os.path.exists(important_file))

    def test_should_backup(self):
        handler = SaveBackupHandler(self.test_backup, extensions=[".sav", ".dsv"])
        self.assertTrue(handler.should_backup("game.sav"))
        self.assertTrue(handler.should_backup("game.dsv"))
        self.assertFalse(handler.should_backup("game.txt"))
        
        handler_no_ext = SaveBackupHandler(self.test_backup)
        self.assertTrue(handler_no_ext.should_backup("game.txt"))

    def test_infinite_loop_prevention(self):
        # Create a nested backup directory
        nested_backup = os.path.join(self.test_source, "backups")
        os.makedirs(nested_backup, exist_ok=True)
        handler = SaveBackupHandler(nested_backup)
        
        # File inside backup dir should NOT be backed up
        backup_file = os.path.join(nested_backup, "some_backup.sav")
        with open(backup_file, "w") as f:
            f.write("data")
        
        # We need to mock copy_with_timestamp or check side effects
        # For simplicity, we can just call handle_event and see it doesn't crash or recurse
        handler.handle_event(backup_file)
        # If it passed the check, it would have tried to copy to nested_backup/some_backup_timestamp.sav
        # We can check that no such file was created
        files = os.listdir(nested_backup)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], "some_backup.sav")

    def test_debounce(self):
        handler = SaveBackupHandler(self.test_backup)
        test_file = os.path.join(self.test_source, "debounce.sav")
        with open(test_file, "w") as f:
            f.write("data")
        
        # First call should backup
        handler.handle_event(test_file)
        # Second call immediately after should be ignored
        handler.handle_event(test_file)
        
        backups = [f for f in os.listdir(self.test_backup) if "debounce" in f]
        self.assertEqual(len(backups), 1)

if __name__ == "__main__":
    unittest.main()
