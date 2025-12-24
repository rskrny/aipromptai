import socket
import time
import requests
import subprocess
import sys
import os

def get_free_port():
    """Finds a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def wait_for_server(url, timeout=10):
    """Polls the server until it is responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Flask usually responds on / or we can check a specific health route if we built one.
            # We'll check root.
            response = requests.get(url)
            if response.status_code < 500: # Any non-server-error is fine
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    return False

def start_web_server(file_path, port):
    """Starts a Flask process on the given port."""
    # We run it with the current python executable
    # We assume the generated code uses app.run(port=port) or we force it via env var if possible,
    # BUT since the AI writes the code, we need to tell the AI to accept a port or we need to pass it as an arg.
    # Easier strategy: The AI writes `app.run(port=PORT)`.
    # We will inject the port into the environment variable 'FLASK_RUN_PORT' or similar, 
    # but standard `python app.py` doesn't respect that unless coded to.
    
    # STRATEGY: We will pass the port as a command line argument and hope the AI handles it? 
    # NO, that's risky.
    # BETTER: We will set an environment variable 'PORT' and instruct the AI to use it.
    
    env = os.environ.copy()
    env["PORT"] = str(port)
    
    cmd = [sys.executable, file_path]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(file_path),
        env=env
    )
    return process
