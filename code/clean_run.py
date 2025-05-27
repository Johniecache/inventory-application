import os
import shutil
import subprocess
import sys
from app.Logger import Logger

def clear_pycache_dirs(root_dir):
    """clears the pycache directories so theres no lingering data from previous runs

    Args:
        root_dir (file): directory of the root and/or root folder
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames: # if theres is a folder named pycache
            pycache_path = os.path.join(dirpath, '__pycache__') # create a path to it
            try:
                shutil.rmtree(pycache_path) # try to remove path
                Logger.info(f"Deleted {pycache_path}") # log the deleted file
            except Exception as e:
                Logger.warning(f"Failed to delte {pycache_path}: {e}") # if failed then log that

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__)) # set the root directory
    clear_pycache_dirs(root_dir) # call the clear pycache method to delete old pycache files/folders

    app_path = os.path.join(root_dir, 'app', 'app.py') # set the directory of the app folder
    if not os.path.exists(app_path): # if it doesnt exist
        Logger.error(f"Error: {app_path} does not exist.") # log that it doesnt exist
        sys.exit(1) # exit early

    try:
        subprocess.run([sys.executable, app_path]) # create subprocess to execute the app.py file
    except KeyboardInterrupt:
        Logger.info("Ending session...") # end session if input was entered
    except Exception as e:
        Logger.error(f"An error occurred while running the app: {e}") # log error if couldn't run the program for some reason

if __name__ == '__main__':
    main() # main loop calling main
