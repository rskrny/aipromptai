import subprocess
import sys
import os

def capture_screenshot(url, output_path="screenshot.png"):
    """Captures a screenshot by running a separate process to avoid asyncio conflicts."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "take_screenshot.py")
        
        # Run the standalone script
        result = subprocess.run(
            [sys.executable, script_path, url, output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            return True
        else:
            return f"Screenshot Script Failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            
    except Exception as e:
        return f"Subprocess Error: {str(e)}"
