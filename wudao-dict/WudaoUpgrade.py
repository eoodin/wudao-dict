from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import quote
import os
import urllib.error
import socket # For socket.timeout

RED_PATTERN = '\033[31m%s\033[0m'

def ie():
    try:
        # Use a more reliable target and shorter timeout for connectivity check
        urlopen('http://www.baidu.com', timeout=2) 
        return True
    except (urllib.error.URLError, socket.timeout):
        return False
    except Exception:
        # Catch any other unexpected errors during the check
        return False

def get_update():
    local_ver = 0.0 # Default to 0.0 if file doesn't exist or is invalid
    ver_file = './Ver'
    if os.path.exists(ver_file):
        try:
            with open(ver_file, 'r') as f:
                local_ver = float(f.read().strip())
        except (IOError, ValueError) as e:
            print(f"Warning: Could not read or parse local version file '{ver_file}': {e}")
            # Keep local_ver as 0.0
    
    if ie():
        try:
            # Increased timeout slightly for the actual version check
            res = urlopen('http://chestnutheng.cn/Ver', timeout=5) 
            xml = res.read().decode('utf-8')
            web_ver = float(xml.strip())
            
            if web_ver > local_ver:
                print('-'*60)
                print(RED_PATTERN % '新的版本已经发布！请在wudao-dict下运行git pull更新。')
                print('-'*60)
            # else: # Optional: Inform user they are up-to-date
            #     print("You are using the latest version.")
                
        except socket.timeout:
            print("Warning: Connection timed out while checking for updates.")
        except urllib.error.URLError as e:
            print(f"Warning: Network error while checking for updates: {e}")
        except ValueError as e:
            print(f"Warning: Could not parse version from server: {e}")
        except Exception as e: # Catch any other unexpected errors
            print(f"Warning: An unexpected error occurred during update check: {e}")
    else:
        print("Warning: No internet connection detected. Cannot check for updates.")
          
if __name__ == '__main__':
    # get_update() doesn't return anything meaningful to print
    get_update()
