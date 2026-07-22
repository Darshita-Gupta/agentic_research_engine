# Setup Guide: Scientific Paper Agent

This guide outlines the instructions to manually configure and run the scientific paper agent via either the **Streamlit Web Dashboard** or the **CLI Runner**.

---

## Prerequisites

1. **Python**: Ensure Python `3.10` or higher is installed.
2. **uv**: This project uses Astral's ultra-fast package installer `uv`. If you do not have it, install it using:
   - **Windows (PowerShell)**:
     ```powershell
     powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **macOS / Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```

---

## 1. Setup API Keys

1. Copy the `.env.example` template to create your `.env` file:
   ```bash
   copy .env.example .env
   ```
2. Open the newly created `.env` file and fill in your developer keys:
   - `GROQ_API_KEY`: Key from [Groq Console](https://console.groq.com/) (supports Llama 3.3).
   - `CORE_API_KEY`: Free key requested from [CORE API Services](https://core.ac.uk/services/api#form).

## Optional: Creating & Activating Virtual Environment

While `uv run` manages virtual environments automatically behind the scenes, you can manually create and activate the `.venv` if you want to run commands (like `python` or `streamlit`) directly:

1. **Create the environment**:
   ```bash
   uv venv
   ```
2. **Activate the environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source .venv/bin/activate
     ```

Once activated, you can execute standard commands directly without the `uv run` prefix (e.g. `streamlit run app.py` or `python main.py`).

---

## 2. Running the Application

`uv` automatically handles creating the virtual environment and installing all dependencies defined in `pyproject.toml` on first run if you use `uv run`.

### Option A: Launch the Streamlit Web Application (Recommended)
Run the following command to start the interactive web interface:
```bash
uv run streamlit run app.py
```
After the server boots, navigate to the local URL in your web browser:
👉 **[http://localhost:8501](http://localhost:8501)**

### Option B: Run the CLI Test Suite
Run the CLI script to execute the pre-configured scientific queries sequentially through standard stdout printing:
```bash
uv run python main.py
```

---

## Project Structure Overview

- **`app.py`**: Entry point for the Streamlit web dashboard.
- **`main.py`**: Entry point for the CLI runner.
- **`pyproject.toml`**: Dependency configuration for `uv`.
- **`src/`**: Core package containing modular graph state machine details:
  - `config.py`: Environment loader and validation safety gates.
  - `prompts.py`: Separated node prompt string configurations.
  - `state.py`: Structuring messages inside `AgentState`.
  - `schemas.py`: Structural output parsers.
  - `utils.py`: CORE search engine wrappers & markdown tools.
  - `tools.py`: Search, download, and feedback tool decorators.
  - `graph.py`: Node builders & compiled LangGraph graph transitions.

---

## 3. Pushing to GitHub

To initialize a local Git repository and push your project to GitHub:

1. **Initialize Git**:
   ```bash
   git init
   ```
2. **Stage your files**:
   ```bash
   git add .
   ```
3. **Create the initial commit**:
   ```bash
   git commit -m "feat: modular scientific paper agent with Streamlit and Groq"
   ```
4. **Create a GitHub repository**:
   - Go to [github.com/new](https://github.com/new) and create a repository. Keep it empty (do **not** initialize with a README, license, or `.gitignore` since they are already present).
5. **Rename branch and push**:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
   git push -u origin main
   ```
