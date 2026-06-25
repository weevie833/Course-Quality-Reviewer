# Course Quality Reviewer (CQR)

A tool for evaluating Canvas course exports against the OSCQR quality standards. Upload a `.imscc` export file, run an AI-powered evaluation across 8 quality standards, and download a formatted Word report.

---

## Prerequisites

Before you begin, you need:

- **Python 3.10 or higher** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com/downloads](https://git-scm.com/downloads)
- **An Anthropic API key** — [console.anthropic.com](https://console.anthropic.com/)

> **Windows users:** When installing Python, check the box that says **"Add Python to PATH"** during setup.

---

## Installation

### 1. Clone the repository

**Mac / Linux — Terminal:**
```
git clone https://github.com/weevie833/Course-Quality-Reviewer.git
cd Course-Quality-Reviewer
```

**Windows — Command Prompt or PowerShell:**
```
git clone https://github.com/weevie833/Course-Quality-Reviewer.git
cd Course-Quality-Reviewer
```

---

### 2. Create a virtual environment

A virtual environment keeps CQR's dependencies separate from other Python projects on your computer.

**Mac / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` appear at the start of your command prompt. You'll need to run the activation command each time you open a new terminal window before starting the app.

---

### 3. Install dependencies

**Mac / Linux:**
```
pip3 install -r requirements.txt
```

**Windows:**
```
pip install -r requirements.txt
```

---

### 4. Add your API key

Copy the example environment file and add your key:

**Mac / Linux:**
```
cp .env.example .env
```

**Windows:**
```
copy .env.example .env
```

Then open `.env` in any text editor (Notepad, TextEdit, VS Code, etc.) and replace `sk-ant-...` with your actual Anthropic API key.

---

## Running the App

### Mac / Linux

```
python3 -m uvicorn main:app --port 8001
```

Then open your browser and go to: **http://localhost:8001**

To stop the server, press `Ctrl+C` in the terminal.

### Windows

```
python -m uvicorn main:app --port 8001
```

Then open your browser and go to: **http://localhost:8001**

To stop the server, press `Ctrl+C` in the Command Prompt window.

---

## Updating to the Latest Version

When a new version is released, pull the latest code and reinstall dependencies.

**Mac / Linux:**
```
git pull
pip3 install -r requirements.txt
```

**Windows:**
```
git pull
pip install -r requirements.txt
```

Then restart the server.

---

## Troubleshooting

**"python3: command not found" (Mac)**
Try `python --version` to check what's installed. If Python 3.10+ is shown, use `python` instead of `python3` in all commands.

**"'python' is not recognized" (Windows)**
Python was not added to PATH during installation. Reinstall Python from [python.org](https://www.python.org/downloads/) and check "Add Python to PATH."

**"Port 8001 is already in use"**
Another process (or a previous server session) is using the port. On Mac/Linux: `lsof -ti :8001 | xargs kill -9`. On Windows: open Task Manager, find the Python process, and end it — then restart.

**API key errors**
Double-check that your `.env` file contains your key with no extra spaces and no quotes around the value:
```
ANTHROPIC_API_KEY=sk-ant-yourKeyHere
```

---

## What Gets Sent to the AI

The text content of your Canvas course (assignments, discussions, pages, syllabus, quizzes, rubrics) is sent to the Anthropic API for evaluation. No student data is included. Anthropic does not use API data to train models. See [Anthropic's privacy policy](https://www.anthropic.com/privacy) for details.
