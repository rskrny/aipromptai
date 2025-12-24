import streamlit as st
import os
import time
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Import our new modules
from agents.prompter import PrompterAgent
from agents.coder import CoderAgent
from agents.dependency import DependencyAgent
from utils.screenshot import capture_screenshot
from utils.process_manager import get_free_port, wait_for_server, start_web_server

# Load environment variables
load_dotenv()
if not os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    load_dotenv(".env.example")

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    load_dotenv(".env.example")
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

# Page Config
st.set_page_config(page_title="AI Auto-Refiner (Pro)", page_icon="🏭", layout="wide")

# Initialize Agents
prompter = PrompterAgent()
coder = CoderAgent()
dependency_manager = DependencyAgent()

# Sidebar Settings
st.sidebar.header("Configuration")
max_iterations = st.sidebar.slider("Max Iterations", 1, 10, 5)

if not api_key:
    st.error("⚠️ API Key missing. Please check your .env or .env.example file for GOOGLE_API_KEY.")
    st.stop()

# Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "status" not in st.session_state:
    st.session_state.status = "IDLE"
if "current_code" not in st.session_state:
    st.session_state.current_code = None
if "preview_process" not in st.session_state:
    st.session_state.preview_process = None
if "current_port" not in st.session_state:
    st.session_state.current_port = None

user_goal = st.text_area("Enter your goal:", height=100, placeholder="e.g. A modern login screen with a gradient background")

col1, col2 = st.columns([1, 5])
start_btn = col1.button("🚀 Start Factory", type="primary", disabled=st.session_state.status == "RUNNING")
reset_btn = col2.button("🗑️ Reset", disabled=st.session_state.status == "RUNNING")

if reset_btn:
    st.session_state.history = []
    st.session_state.status = "IDLE"
    st.session_state.current_code = None
    if st.session_state.preview_process:
        st.session_state.preview_process.terminate()
        st.session_state.preview_process = None
    st.rerun()

if start_btn and user_goal:
    # Cleanup previous run artifacts
    if os.path.exists("screenshot.png"):
        os.remove("screenshot.png")
    workspace_app_path = os.path.join(os.getcwd(), "workspace", "generated_app.py")
    if os.path.exists(workspace_app_path):
        os.remove(workspace_app_path)

    st.session_state.status = "RUNNING"
    st.session_state.history = []
    st.session_state.current_code = None
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    image_spot = st.empty()
    
    coder_context = []
    
    for i in range(max_iterations):
        iteration_label = i + 1
        
        # --- 1. Prompter AI ---
        status_text.text(f"Iteration {iteration_label}: Prompter AI is reviewing...")
        
        screenshot_file = "screenshot.png" if i > 0 else None
        
        with st.spinner("Prompter AI is analyzing..."):
            prompter_instruction = prompter.review(
                user_goal, 
                st.session_state.current_code, 
                iteration_label, 
                st.session_state.history,
                screenshot_file
            )
            
        if "APPROVED" in prompter_instruction:
            st.session_state.history.append({"iteration": iteration_label, "role": "Prompter AI", "content": "✅ APPROVED"})
            st.success("🎉 System Approved!")
            st.session_state.status = "FINISHED"
            break
            
        st.session_state.history.append({"iteration": iteration_label, "role": "Prompter AI", "content": prompter_instruction})
        
        # --- 2. Coder AI ---
        status_text.text(f"Iteration {iteration_label}: Coder AI is coding...")
        with st.spinner("Coder AI is writing code..."):
            new_code = coder.write_code(prompter_instruction, coder_context)
            st.session_state.current_code = new_code
            
        st.session_state.history.append({"iteration": iteration_label, "role": "Coder AI", "content": new_code, "is_code": True})
        coder_context.append({'instruction': prompter_instruction, 'code': new_code})
        
        # --- 3. Dependency Check ---
        status_text.text(f"Iteration {iteration_label}: Checking Dependencies...")
        with st.spinner("Installing dependencies..."):
            dep_result = dependency_manager.install_dependencies(new_code)
            st.session_state.history.append({"iteration": iteration_label, "role": "System", "content": f"📦 Dependencies: {dep_result}"})

        # --- 4. Run & Screenshot ---
        status_text.text(f"Iteration {iteration_label}: Deploying & Photographing...")
        
        # Save code to workspace
        workspace_dir = os.path.join(os.getcwd(), "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        app_path = os.path.join(workspace_dir, "generated_app.py")
        
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(new_code)
            
        # Kill previous process
        if st.session_state.preview_process:
            st.session_state.preview_process.terminate()
            st.session_state.preview_process.wait()
            st.session_state.preview_process = None
            
        try:
            # Dynamic Port
            port = get_free_port()
            st.session_state.current_port = port
            url = f"http://localhost:{port}"
            
            # Start Process
            st.session_state.preview_process = start_web_server(app_path, port)
            
            # Wait for server to be healthy
            if wait_for_server(url, timeout=10):
                result = capture_screenshot(url=url, output_path="screenshot.png")
                
                if result is True:
                    image_spot.image("screenshot.png", caption=f"Snapshot Iteration {iteration_label}")
                    st.session_state.history.append({"iteration": iteration_label, "role": "System", "content": "📸 Screenshot captured", "image": "screenshot.png"})
                else:
                    st.error(f"Screenshot failed: {result}")
                    st.session_state.history.append({"iteration": iteration_label, "role": "System", "content": f"⚠️ Screenshot failed: {result}"})
            else:
                # Server failed to start - Get the error log
                _, stderr = st.session_state.preview_process.communicate(timeout=2)
                error_msg = f"Server failed to start on port {port}.\nLogs:\n{stderr}"
                st.error(error_msg)
                st.session_state.history.append({"iteration": iteration_label, "role": "System", "content": f"⚠️ App Crash:\n```\n{stderr}\n```"})
                
        except Exception as e:
            st.error(f"Deployment infrastructure failed: {e}")
            
        progress_bar.progress((i + 1) / max_iterations)
        
    st.session_state.status = "IDLE"
    st.rerun()

# Display History
st.divider()
for item in st.session_state.history:
    with st.chat_message(item["role"], avatar="👁️" if item["role"] == "Prompter AI" else "👨‍💻"):
        st.write(f"**{item['role']}**")
        if item.get("is_code"):
            st.code(item["content"], language="python")
        elif item.get("image"):
            st.image(item["image"])
        else:
            st.markdown(item["content"])

if st.session_state.current_code and st.session_state.current_port:
    st.divider()
    st.subheader("Final Result")
    url = f"http://localhost:{st.session_state.current_port}"
    st.markdown(f"[**🔗 Open Live App ({url})**]({url})")
