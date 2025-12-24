# AI Prompt Enhancer

This is a simple Streamlit application that takes a user's simple prompt and "enhances" it using an AI model (simulated in the template) to be better suited for AI coding assistants.

## Setup

1.  **Install Python**: Ensure you have Python installed.
2.  **Create a Virtual Environment** (optional but recommended):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Rename `.env.example` to `.env`.
2.  Add your OpenAI API Key (or other provider) to the `.env` file.
3.  **Important**: You need to uncomment the OpenAI code in `app.py` and implement the actual API call to make it work with a real LLM.

## Running the App

```bash
streamlit run app.py
```

## How it works

1.  Type a prompt in the chat input.
2.  The `enhance_prompt` function processes the input.
3.  The enhanced prompt is displayed in the chat.
