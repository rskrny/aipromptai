import google.generativeai as genai
import os
from PIL import Image

class PrompterAgent:
    def __init__(self, model_name='gemini-2.0-flash'):
        self.model = genai.GenerativeModel(model_name)

    def review(self, user_goal, current_code, iteration_count, history, screenshot_path=None):
        """
        Reviews the goal, code, and ACTUAL SCREENSHOT.
        """
        if iteration_count == 1:
            # Planning Phase
            system_instruction = f"""
            You are an expert Technical Lead and Mobile Architect.
            Your goal is to translate the User's Request into a detailed technical specification for the Coder AI.
            
            User Request: "{user_goal}"
            Iteration: {iteration_count} (Initial Planning)
            
            Task:
            1. **Analyze the User Request**. What is the core value? What are the key features?
            2. **Define the Mobile UX**. How should it look and feel? (Native-like, bottom nav, etc.)
            3. **Outline the Technical Implementation**. Flask routes, HTML structure, Tailwind classes.
            
            **Output**:
            Provide a clear, structured set of instructions for the Coder AI to build the FIRST VERSION (MVP).
            Focus on getting the core structure and UI up and running.
            """
        else:
            # Review Phase
            system_instruction = f"""
            You are an expert Technical Lead, UX Designer, and Backend Architect. 
            Your goal is to ensure the User's Request is perfectly implemented by the Coder AI.
            
            User Request: "{user_goal}"
            Iteration: {iteration_count}
            
            Task:
            1. **Analyze the Screenshot** (if provided). This is the ACTUAL output of the code running in a MOBILE SIMULATOR.
               - Does it look like a NATIVE APP?
               - Is the layout responsive?
               - Are the buttons finger-friendly?
            2. **Analyze the Code**.
               - Is the logic sound?
               - Are there security risks?
            3. **Compare strictly against the 'User Request'**.
            4. **Output**:
               - If the app is perfect (visually and logically), respond with exactly: "APPROVED".
               - If it needs work, provide a structured critique.
            
            **Format your response as follows:**
            
            ## 📱 Mobile UX Inspection
            [Critique based on the screenshot. Does it feel like an app?]
            
            ## ⚙️ Logic/Code Critique
            [Critique based on the code structure and logic.]
            
            ## 🛠️ Instructions for Coder
            [Specific, actionable steps to fix the issues.]
            """
        
        inputs = [system_instruction]
        
        if current_code:
            inputs.append(f"Current Code:\n```python\n{current_code}\n```")
        
        if screenshot_path and os.path.exists(screenshot_path):
            img = Image.open(screenshot_path)
            inputs.append("Here is the screenshot of the running application:")
            inputs.append(img)
        else:
            inputs.append("No screenshot available yet (first run or error).")

        # Add history context (simplified)
        if history:
            last_critique = next((h['content'] for h in reversed(history) if h['role'] == 'Prompter AI'), None)
            if last_critique:
                inputs.append(f"Previous Instruction: {last_critique}")

        try:
            response = self.model.generate_content(inputs)
            return response.text
        except Exception as e:
            return f"Error generating critique: {e}"
