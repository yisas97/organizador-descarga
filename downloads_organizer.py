
import os
import shutil
import logging
import signal
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

logging.basicConfig(
    filename='downloads_organizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Diccionarios de las categorias 
EXTENSIONS = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
    'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.ppt', '.pptx', '.csv', '.odt'],
    'music': ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.midi', '.aac', '.wma'],
    'programs': ['.exe', '.msi', '.app', '.bat', '.cmd', '.py', '.jar', '.dll'],
    'compressed': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
    'others': [] # son los que no estan en las demas categorias
}

class FileOrganizer(FileSystemEventHandler):
    def __init__(self, downloads_path):
        self.downloads_path = downloads_path
        self.pending_files = {}
        logging.info(f"Organizer started. Monitoring: {downloads_path}")
        self.process_existing_files()

    def process_existing_files(self):
        logging.info("Processing existing files...")
        downloads_dir = Path(self.downloads_path)
        for file_path in downloads_dir.glob('*'):
            if file_path.is_file():
                creation_time = datetime.fromtimestamp(file_path.stat().st_ctime)
                self.pending_files[str(file_path)] = creation_time
                logging.info(f"Added existing file to queue: {file_path.name}")

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            self.pending_files[file_path] = datetime.now()
            logging.info(f"New file detected: {os.path.basename(file_path)}")

    def process_pending_files(self):
        files_to_remove = []

        for file_path, creation_time in self.pending_files.items():
            self.organize_file(file_path)
            files_to_remove.append(file_path)

        # Clean up processed files list
        for file_path in files_to_remove:
            del self.pending_files[file_path]

    def organize_file(self, file_path):
        try:
            file = Path(file_path)
            if not file.exists():
                return

            category = 'others'
            for cat, extensions in EXTENSIONS.items():
                if file.suffix.lower() in extensions:
                    category = cat
                    break

            dest_folder = Path(self.downloads_path) / category
            dest_folder.mkdir(exist_ok=True)

            # Mover el archivo
            shutil.move(str(file), str(dest_folder / file.name))
            logging.info(f"File organized: {file.name} -> {category}")

        except Exception as e:
            logging.error(f"Error organizing {file_path}: {str(e)}")

def signal_handler(signum, frame):
    logging.info(f"Stop signal received: {signal.Signals(signum).name}")
    logging.info("Stopping downloads organizer...")
    observer.stop()
    sys.exit(0)

def main():
    pid_file = "downloads_organizer.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)
                logging.warning(f"An instance is already running with PID {old_pid}")
                sys.exit(1)
            except OSError:
                pass
        except Exception as e:
            logging.error(f"Error checking existing process: {e}")

    pid = os.getpid()
    with open(pid_file, "w") as f:
        f.write(str(pid))

    logging.info(f"Organizer started with PID: {pid}")
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        downloads_path = str(Path.home() / "Downloads")
        
        global observer
        organizer = FileOrganizer(downloads_path)
        observer = Observer()
        observer.schedule(organizer, downloads_path, recursive=False)
        observer.start()

        #logging.info("Downloads organizer started - Checking every 2 hours")
        logging.info("Downloads organizer started - Processing files...")

        organizer.process_pending_files()
        logging.info("Processing completed.")
        
        observer.stop()
        observer.join()

    except Exception as e:
        logging.error(f"Error in main program: {str(e)}")

if __name__ == "__main__":
    main()