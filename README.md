# Voice Controlled Task Manager

A voice-first task manager web application where all operations are performed conversationally. Manage your daily agenda entirely through speech without typing, clicking edit buttons, or navigating manual CRUD forms.

## 🎙️ Core Features

- **Voice-Only Interaction:** Create, read, update, and delete tasks naturally using your voice.
- **Contextual Understanding:** Refers to tasks contextually (e.g., "my evening workout", "that task for tomorrow").
- **Interruption Handling:** Stop the assistant instantly mid-sentence by speaking. The application elegantly handles interruptions and gracefully resumes listening.
- **Action Confirmation:** Safely asks for clarification before performing destructive actions like deleting tasks.
- **Agenda Summarization:** Reads your daily agenda as a natural summary rather than a robotic list.
- **Real-Time Orchestration:** Uses WebSockets for low-latency conversational exchanges.

## 🛠️ Tech Stack

- **Frontend:** React, TypeScript, Vite, Zustand, Browser Web Speech API (STT/TTS).
- **Backend:** FastAPI (Python), SQLAlchemy, WebSockets.
- **Database:** SQLite (configured out-of-the-box).
- **Conversational AI:** Ollama running `qwen2.5:7b-instruct` locally for zero-latency, private, and offline conversational intent extraction and tool calling.
- **Deployment:** Fully dockerized via Docker Compose.

## 🚀 Getting Started

The easiest way to run this application locally is using Docker Compose. It will spin up the FastAPI backend, the React frontend, and the Ollama LLM service seamlessly.

### Prerequisites
- Docker
- Docker Compose

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tasks-voice-interface
   ```

2. **Start the services:**
   ```bash
   docker-compose up --build
   ```
   *Note: On the first run, Docker will download the required Ollama model (`qwen2.5:7b-instruct`), which may take a few minutes depending on your internet connection.*

3. **Access the application:**
   - **Frontend UI:** Open your browser and navigate to http://localhost:5173
   - **Backend API Docs:** Navigate to http://localhost:8000/docs

## 🗣️ Usage

1. Open the frontend application in your browser.
2. Click the microphone/start button to initiate the session (required by browsers to allow audio playback).
3. Start speaking! Try commands like:
   - *"Remind me tomorrow morning to call John."*
   - *"What's on my agenda for today?"*
   - *"Actually, update that call with John to tomorrow evening."*
   - *"Delete the call with John."*

## 🏗️ Architecture Overview

The system uses an **AI-Agent-Oriented** architecture heavily reliant on specific tool/function calling:
- **Browser:** Captures speech and converts it to text using the native Web Speech API.
- **WebSocket Connection:** Streams the final transcript to the backend.
- **FastAPI Orchestrator:** Maintains conversation memory and routes the transcript to the LLM.
- **Ollama (qwen2.5:7b):** Extracts intent and decides whether to respond conversationally or to execute a backend task management tool (Create, Read, Update, Delete).
- **Audio Output:** Text responses from the backend are converted back to audio using the browser's native Text-to-Speech API.

## 📜 License

MIT License
