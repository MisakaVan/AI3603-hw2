import os
import shutil

def remove_debug_directories(base_path):
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if 'debug' in dir_name:
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)
                print(f"Removed directory: {dir_path}")

if __name__ == "__main__":
    logs_path = './logs'
    remove_debug_directories(logs_path)