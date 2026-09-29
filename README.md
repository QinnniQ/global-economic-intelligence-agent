<p align="center">
  <img src="assets/banner.png" width="100%" alt="Global Economic Intelligence Agent Banner"/>
</p>

<h1 align="center">🌍 Global Economic Intelligence Agent</h1>

<p align="center">
  <strong>AI-powered macroeconomic intelligence using live data, PDF-based RAG, and LLM analysis</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-Frontend-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img alt="OpenAI" src="https://img.shields.io/badge/OpenAI-LLM%20Powered-412991?style=for-the-badge&logo=openai&logoColor=white">
  <img alt="LangChain" src="https://img.shields.io/badge/LangChain-RAG%20Engine-1C1E24?style=for-the-badge">
  <img alt="ChromaDB" src="https://img.shields.io/badge/ChromaDB-Vector%20Store-4ECDC4?style=for-the-badge">
  <img alt="Plotly" src="https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?style=for-the-badge&logo=plotly&logoColor=white">
</p>

<p align="center">
  <em>A production-minded full-stack AI application combining real-time macroeconomic indicators, document retrieval, and LLM-based synthesis.</em>
</p>

---

## Overview

The **Global Economic Intelligence Agent** combines live macroeconomic data with document retrieval and LLM reasoning to produce grounded economic analysis through an interactive web interface.

It brings together:

- **Live macroeconomic indicators** such as GDP growth, inflation, and unemployment
- **PDF-based Retrieval-Augmented Generation (RAG)** over economic reports
- **LLM synthesis** that combines retrieved context with current indicator data
- **Interactive dashboards and global visualizations**
- **Exportable PDF economic briefings**

The project is designed as an end-to-end AI system rather than a standalone prompt demo: data retrieval, RAG, backend APIs, LLM analysis, visualization, and report generation are separated into distinct application layers.

---

## Architecture

```text
User
  ↓
Streamlit UI
  ↓
FastAPI backend
  ├── Live macro data → World Bank API
  ├── PDF retrieval → ChromaDB
  └── LLM analysis → OpenAI
  ↓
Grounded analysis + charts + PDF report
```

Docker Compose runs the FastAPI backend and Streamlit frontend as separate services on a shared application network. The frontend receives the backend service URL through an environment variable rather than relying on a hard-coded container address.

---

## Screenshots

### Main Dashboard
![Main Dashboard](screenshots/main.png)

### AI Economic Report Generator
![Generate Report](screenshots/generate.png)

### Global Economic Heatmap
![Heatmap](screenshots/heatmap.png)

---

## Features

### 1. Real-Time Macroeconomic Dashboard
- Live World Bank indicator data
- GDP growth, inflation, and unemployment views
- Country-aware dashboard controls
- Plotly trend visualizations and sparklines

### 2. Global Economic Heatmap
- Cross-country indicator comparison
- Interactive geographic visualization

### 3. Ask the AI Economist
- Country and indicator detection from user questions
- LLM-generated macro trend summaries
- RAG-enhanced analysis grounded in retrieved report excerpts
- Combined reasoning over live data and document context

### 4. PDF RAG Engine
- Ingests and vectorizes economic reports
- Stores embeddings in ChromaDB
- Retrieves relevant passages to support generated analysis

### 5. Exportable Economic Briefings
- Generates downloadable PDF reports
- Includes detected country, indicators, analysis, and retrieved context

---

## Tech Stack

### Backend
- Python
- FastAPI
- OpenAI API
- LangChain
- ChromaDB
- World Bank API
- ReportLab

### Frontend
- Streamlit
- Plotly
- Pandas
- Custom CSS
- gTTS for optional audio playback

### Packaging
- Docker
- Docker Compose
- Environment-based configuration
- Container health check for the backend

---

## Repository Structure

```text
.
├── assets/
├── chroma_store/
├── data/
├── reports_out/
├── screenshots/
├── src/
│   ├── agent/
│   │   └── economic_agent.py
│   ├── backend/
│   │   ├── rags/
│   │   ├── routes/
│   │   ├── tools/
│   │   ├── config.py
│   │   └── server.py
│   └── frontend/
│       └── streamlit_app.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Run with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/QinnniQ/global-economic-intelligence-agent.git
cd global-economic-intelligence-agent
```

### 2. Configure environment variables

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-4o-mini
```

### 3. Build and start both services

```bash
docker compose up --build
```

Then open:

```text
Streamlit UI: http://localhost:8501
FastAPI docs: http://localhost:8000/docs
Health check:  http://localhost:8000/health
```

Stop the stack with:

```bash
docker compose down
```

---

## Running Locally without Docker

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your OpenAI API key.

### 4. Start the FastAPI backend

```bash
uvicorn src.backend.server:app --reload --port 8000
```

### 5. Start the Streamlit frontend

Open a second terminal, activate the same environment, then run:

```bash
streamlit run src/frontend/streamlit_app.py
```

By default the frontend expects the backend at `http://localhost:8000`. The address can be overridden with the `BACKEND_URL` environment variable.

---

## Engineering Decisions

- **Separate frontend and backend:** Streamlit handles presentation while FastAPI exposes application capabilities as API routes.
- **Live data + RAG:** structured macroeconomic indicators and unstructured report excerpts are combined rather than relying on a single context source.
- **Explicit retrieval layer:** ChromaDB provides inspectable document retrieval before LLM synthesis.
- **Environment-based secrets:** API keys are loaded from `.env` and never committed.
- **Container-aware configuration:** the frontend backend URL is configurable through `BACKEND_URL`, allowing the same application code to run locally or inside Docker Compose.
- **Health endpoint:** the backend exposes `/health`, and Docker Compose uses it to gate frontend startup.

---

## Current Status

The application can now run either directly in Python or as a two-service Docker Compose stack with a FastAPI backend and Streamlit frontend.

The next engineering phase is focused on automated verification and deployment:

- automated tests
- GitHub Actions CI
- deployment configuration
- logging and observability

These are intentionally listed as roadmap items rather than presented as completed functionality.

---

## What This Project Demonstrates

- End-to-end LLM application engineering
- Retrieval-Augmented Generation over real documents
- Integration of live external APIs with LLM workflows
- FastAPI backend design
- Vector retrieval with ChromaDB
- Interactive Streamlit application development
- Dockerized multi-service application packaging
- Environment-based service configuration
- Structured separation between retrieval, reasoning, API, and presentation layers
- Exportable stakeholder-facing outputs

---

## Contact

**Nicholai Gay**  
AI Engineer — LLM Systems, RAG & AI Agents

[LinkedIn](https://www.linkedin.com/in/nicholai-gay-201905148/) · [GitHub](https://github.com/QinnniQ)
