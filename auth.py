import tekore as tk
import os

path = os.path.dirname(os.path.abspath(__file__))

def get_user_token():
    CONFIG_FILE = path + '/creds.config'
    conf = tk.config_from_file(CONFIG_FILE, return_refresh=True)
    token = tk.refresh_user_token(*conf[:2], conf[3])
    return token
