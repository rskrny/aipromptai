import google.generativeai as genai

class CoderAgent:
    def __init__(self, model_name='gemini-2.0-flash'):
        self.model = genai.GenerativeModel(model_name)

    def write_code(self, instruction, code_history):
        """
        Writes code using Gemini.
        """
        system_instruction = """
        You are an expert Full-Stack Developer specializing in Mobile-First Web Apps.
        Your task is to create a high-quality, "Native-Like" mobile web application using Python (Flask) and HTML/TailwindCSS.
        
        **Tech Stack:**
        - **Backend:** Flask (Python)
        - **Frontend:** HTML5 + Tailwind CSS (via CDN) + JavaScript (Vanilla)
        
        **Requirements:**
        1. **Single File Output (CRITICAL):** 
           - You must combine the Flask app, HTML templates, and CSS/JS into a SINGLE Python file.
           - **DO NOT** use `render_template`. **DO NOT** assume a `templates` folder exists.
           - **MUST USE** `render_template_string` to serve the HTML.
           - Define your HTML as a multi-line string variable (e.g., `HTML_TEMPLATE = """..."""`) at the top of the file.
        2. **Mobile-First Design:**
           - The UI MUST look like a native mobile app (e.g., Uber, Instagram).
           - Use a bottom navigation bar if appropriate.
           - Use large touch targets.
           - Use modern fonts and shadows.
        3. **Functionality:**
           - The app must be functional (mock data is fine).
           - It must run on `localhost`.
           - **CRITICAL**: The app must listen on the port defined in the environment variable `PORT`.
             Use: `port = int(os.environ.get("PORT", 5000))`
             Then: `app.run(host='0.0.0.0', port=port)`
        
        **Output Format:**
        Return ONLY the Python code block. The code should start with imports and end with `if __name__ == '__main__': app.run(...)`.
        """
        
        chat = self.model.start_chat(history=[])
        
        # Feed history
        chat.send_message(system_instruction)
        for turn in code_history:
            chat.send_message(f"Instruction: {turn['instruction']}\nCode: {turn['code']}")
            
        response = chat.send_message(instruction)
        
        # Extract code block if wrapped in markdown
        text = response.text
        if "```python" in text:
            text = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1]
            
        return text.strip()
