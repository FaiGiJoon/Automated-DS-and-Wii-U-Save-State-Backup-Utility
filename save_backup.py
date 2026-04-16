import os
import shutil
import time
import sys
import re
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Pattern to match backup files: name_YYYYMMDD_HHMMSS_ffffff.ext
BACKUP_PATTERN = re.compile(r".*_\d{8}_\d{6}_\d{6}\..*")

class SaveBackupHandler(FileSystemEventHandler):
    def __init__(self, backup_dir, extensions=None, retention_days=7):
        self.backup_dir = os.path.abspath(backup_dir)
        self.extensions = extensions
        self.retention_days = retention_days
        self.last_prune_time = 0
        self.last_backup_events = {} # {file_path: timestamp}

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle_event(event.dest_path)

    def handle_event(self, file_path):
        file_path = os.path.abspath(file_path)
        
        # Prevent infinite loop: skip if file is inside the backup directory
        if file_path.startswith(self.backup_dir):
            return

        if self.should_backup(file_path):
            # Debounce: skip if we recently backed up this file
            current_time = time.time()
            last_time = self.last_backup_events.get(file_path, 0)
            if current_time - last_time < 2: # 2 second debounce
                return
            
            if copy_with_timestamp(file_path, self.backup_dir):
                self.last_backup_events[file_path] = current_time
                self.periodic_prune()

    def should_backup(self, file_path):
        if self.extensions:
            return any(file_path.endswith(ext) for ext in self.extensions)
        return True

    def periodic_prune(self):
        # Prune at most once per hour to avoid excessive overhead
        current_time = time.time()
        if current_time - self.last_prune_time > 3600:
            prune_backups(self.backup_dir, self.retention_days)
            self.last_prune_time = current_time

def copy_with_timestamp(source_file, backup_dir):
    """
    Copies source_file to backup_dir with a high-resolution timestamp.
    """
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    filename = os.path.basename(source_file)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_filename = f"{name}_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Using shutil.copy instead of copy2 to update mtime to backup time
        shutil.copy(source_file, backup_path)
        print(f"Backed up: {filename} -> {backup_filename}")
        return backup_path
    except Exception as e:
        print(f"Error backing up {filename}: {e}")
        return None

def prune_backups(backup_dir, days=7):
    """
    Deletes files in backup_dir older than 'days' days.
    """
    if not os.path.exists(backup_dir):
        return

    now = time.time()
    cutoff = now - (days * 86400)
    
    for filename in os.listdir(backup_dir):
        if not BACKUP_PATTERN.match(filename):
            continue

        file_path = os.path.join(backup_dir, filename)
        if os.path.isfile(file_path):
            if os.path.getmtime(file_path) < cutoff:
                try:
                    os.remove(file_path)
                    print(f"Pruned old backup: {filename}")
                except Exception as e:
                    print(f"Error pruning {filename}: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Monitor a folder for save-state files and back them up.")
    parser.add_argument("source", help="Directory to monitor")
    parser.add_argument("backup", help="Directory to store backups")
    parser.add_argument("--retention", type=int, default=7, help="Days to retain backups (default: 7)")
    parser.add_argument("--extensions", nargs="+", help="File extensions to monitor (e.g., .sav .dsv)")
    parser.add_argument("--recursive", action="store_true", help="Monitor subdirectories recursively")

    args = parser.parse_args()

    source_dir = os.path.abspath(args.source)
    backup_dir = os.path.abspath(args.backup)

    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    event_handler = SaveBackupHandler(backup_dir, extensions=args.extensions, retention_days=args.retention)
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=args.recursive)
    
    print(f"Monitoring: {source_dir}")
    print(f"Backups to: {backup_dir}")
    print(f"Retention: {args.retention} days")
    if args.extensions:
        print(f"Extensions: {', '.join(args.extensions)}")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
