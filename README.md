# AI Software Factory

This is a sophisticated AI-powered "Software Factory" that iteratively builds, deploys, and refines web applications based on user prompts.

## Features
- **Prompter AI**: Refines user requests into technical specs.
- **Coder AI**: Generates Flask + TailwindCSS applications.
- **Visual Feedback**: Uses Playwright to take screenshots of the running app.
- **Self-Correction**: The AI critiques its own work based on the screenshots and iterates.

## Setup (GitHub Codespaces)
1. Open this repo in GitHub Codespaces.
2. The `.devcontainer` configuration will automatically install all dependencies.
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Setup (Local)
*Note: Local setup on Windows is complex due to process management. Linux/WSL is recommended.*

1.  **Install Python**: Ensure you have Python installed.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
3.  **Run**:
    ```bash
    streamlit run app.py
    ```