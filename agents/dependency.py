import google.generativeai as genai
import subprocess
import sys

class DependencyAgent:
    def __init__(self, model_name='gemini-2.0-flash'):
        self.model = genai.GenerativeModel(model_name)

    def install_dependencies(self, code):
        """
        Analyzes the code, determines required packages, and installs them.
        """
        prompt = f"""
        Analyze the following Python code and list the PyPI packages required to run it.
        Ignore standard library modules (like os, sys, time, json, socket).
        Only list external packages (like pandas, numpy, streamlit, plotly, sklearn, openai, google-generativeai).
        
        Code:
        ```python
        {code[:10000]} 
        ```
        
        Output ONLY a list of packages, one per line. No other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            packages = response.text.strip().split('\n')
            packages = [p.strip() for p in packages if p.strip()]
            
            if not packages:
                return "No new dependencies found."
            
            installed = []
            failed = []
            
            for package in packages:
                # Simple check to avoid re-installing if possible, 
                # but pip handles this gracefully usually.
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    installed.append(package)
                except subprocess.CalledProcessError:
                    failed.append(package)
            
            return f"Installed: {', '.join(installed)}. Failed: {', '.join(failed)}"
            
        except Exception as e:
            return f"Dependency Error: {e}"
