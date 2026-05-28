# Voice Controlled Task Manager — AI-Agent-Oriented Technical Design Document

## 1. Objective

Design and implement a voice-first task manager web application where all task operations are performed conversationally using speech.

The implementation is optimized for:
- Fast execution by an AI coding agent
- Existing FastAPI AWS Lambda backend reuse
- Open-source/free runtime stack only
- Low implementation complexity
- Reliable interruption handling
- Minimal infrastructure additions

This document intentionally excludes optional or non-essential components.

---

# 2. Final Architecture Decisions

## Frontend

Chosen Stack:
- React SPA using Vite
- TypeScript
- Browser Web Audio APIs
- Browser WebSocket API

Reasoning:
- Faster implementation than Next.js
- No SSR requirement
- Lower deployment complexity
- Better suited for realtime voice orchestration

Deployment:
- Vercel Free Tier

---

## Backend

Reuse Existing Infrastructure:
- FastAPI running on AWS Lambda
- PostgreSQL RDS
- Existing CRUD endpoints

Additional Requirement:
- Add WebSocket realtime orchestration endpoint

Deployment:
- Existing AWS deployment retained

---

## STT/TTS Decision

Chosen Option:
- Browser-native Web Speech API

Reasoning:
- Meets 1–2 day implementation constraint
- Minimizes infrastructure complexity
- Enables interruption handling via browser speech APIs
- Sufficient for MVP latency requirements

Tradeoff Accepted:
- Browser compatibility limitations
- Less accurate than Whisper-based STT
- Less controllable than server-side TTS

Fallback Strategy:
- Gracefully degrade to push-to-talk retry flow
- Re-prompt on failed transcription

This choice is acceptable for the stated non-functional requirements because:
- Low latency is prioritized
- Interruption handling is easier client-side
- The requirement does not mandate enterprise STT accuracy

---

## Conversational Intelligence

Chosen Runtime:
- Ollama
- Open-source model served locally/self-hosted

Recommended Model:
- qwen2.5:7b-instruct

Reasoning:
- Strong instruction following
- Good function/tool calling behavior
- Runs locally/free
- Lower hallucination rate than smaller models
- Fast enough for conversational orchestration

Deployment:
- Small VPS or local docker container
- Same-region deployment preferred

NOT using:
- OpenAI APIs
- Anthropic APIs
- Proprietary inference services

---

# 3. High-Level System Architecture

```text
Browser React SPA
    |
    | WebSocket
    v
FastAPI Voice Orchestrator
    |
    | HTTP
    v
Ollama LLM Runtime
    |
    | Tool Calls
    v
Existing Task CRUD Endpoints
    |
    v
PostgreSQL RDS
```

---

# 4. Core Design Principles

## Voice-Only Interaction

The UI must not expose:
- Edit buttons
- Delete buttons
- Task forms
- Manual typing flows
- CRUD controls

The UI may expose:
- Microphone button
- Speaking indicator
- Connection status
- Transcript display
- Agenda/task visualization

---

## Interruption-First Architecture

The system must:
- Stop TTS immediately when user speaks
- Cancel assistant playback instantly
- Resume listening without page refresh
- Preserve conversational state

Implementation responsibility:
- Entirely client-side for responsiveness

---

## Tool-Driven Agent

The LLM must never directly mutate task state.

All mutations occur through deterministic tool execution.

LLM responsibilities:
- Intent extraction
- Semantic interpretation
- Clarification generation
- Summarization
- Action planning

Backend responsibilities:
- Validation
- CRUD execution
- State persistence
- Authorization placeholder handling

---

# 5. Frontend Technical Design

## 5.1 Technology Stack

Dependencies:

```text
react
vite
typescript
zustand
react-use-websocket
uuid
```

No heavy UI framework required.

---

## 5.2 Frontend State Machine

The voice assistant should operate using explicit conversational states.

```text
REQUIRES_INTERACTION (Initial state - Must display a "Start Session" button to bypass browser autoplay policies)
IDLE
LISTENING
PROCESSING
SPEAKING
INTERRUPTED
ERROR
RECONNECTING

State transitions must be deterministic.

---

Critical Rule: The useVoiceSession hook MUST NOT initialize SpeechSynthesis or SpeechRecognition until the user explicitly clicks a button to transition from REQUIRES_INTERACTION to IDLE.

## 5.3 Audio Pipeline

## Input Flow

```text
Microphone
    -> Web Speech API STT
    -> Partial Transcript
    -> Final Transcript
    -> WebSocket Event
```

---

## Output Flow

```text
Assistant Text
    -> SpeechSynthesis API
    -> Browser Audio Playback
```

---

## 5.4 Interruption Handling Design

Critical Requirement.

Implementation Strategy:

When assistant is speaking:

1. Browser continuously monitors microphone energy.
2. If user speech detected:
   - immediately call:

```javascript
speechSynthesis.cancel()
```

3. Transition state:

```text
SPEAKING -> INTERRUPTED -> LISTENING
```

4. Resume STT capture.

---

## 5.5 Voice Session Hook

Primary abstraction:

```text
useVoiceSession()
```

Responsibilities:
- STT lifecycle
- TTS lifecycle
- interruption detection
- websocket messaging
- reconnect handling
- transcript buffering
- assistant playback queue

---

## 5.6 Suggested Frontend Structure

```text
src/
  components/
    VoiceOrb.tsx
    TranscriptPanel.tsx
    ConnectionBanner.tsx

  hooks/
    useVoiceSession.ts
    useSpeechRecognition.ts
    useSpeechSynthesis.ts
    useInterruptDetection.ts

  services/
    websocket.ts
    voiceProtocol.ts

  store/
    voiceStore.ts

  types/
    voice.ts

  pages/
    App.tsx
```

---

# 6. Backend Technical Design

## 6.1 Responsibilities

The FastAPI orchestration layer is responsible for:
- websocket session management
- conversational memory
- LLM interaction
- tool routing
- task CRUD orchestration
- clarification flows
- summarization generation

The backend is NOT responsible for:
- STT
- TTS playback
- interruption audio handling

---

## 6.2 New Backend Module

Add:

```text
voice_router/
```

Suggested structure:

```text
voice_router/
  websocket.py
  orchestrator.py
  prompts.py
  tools.py
  session_memory.py
  dto.py
```

---

# 7. WebSocket Protocol

## 7.1 Client -> Server Events

### USER_TRANSCRIPT

```json
{
  "type": "USER_TRANSCRIPT",
  "payload": {
    "text": "remind me tomorrow morning to call john"
  }
}
```

---

### INTERRUPT

```json
{
  "type": "INTERRUPT"
}
```

---

### SESSION_START

```json
{
  "type": "SESSION_START"
}
```

---

## 7.2 Server -> Client Events

### ASSISTANT_RESPONSE

```json
{
  "type": "ASSISTANT_RESPONSE",
  "payload": {
    "text": "Sure. I created a task for tomorrow morning to call John."
  }
}
```

---

### ACTION_CONFIRMATION_REQUIRED

```json
{
  "type": "ACTION_CONFIRMATION_REQUIRED",
  "payload": {
    "text": "You have two workout tasks tomorrow evening. Which one should I delete?"
  }
}
```

---

### ERROR

```json
{
  "type": "ERROR",
  "payload": {
    "message": "I didn't catch that. Could you repeat it?"
  }
}
```

---

# 8. LLM Orchestration Design

## 8.1 Agent Model

Single orchestrator agent.

Do NOT implement multi-agent architecture.

Reasoning:
- Faster implementation
- Lower coordination complexity
- Better fit for coding agent delivery
- Easier debugging
- Reduced latency

---

## 8.2 Conversation Memory

In-memory session store.

Session memory includes:

```python
class VoiceSessionMemory:
    session_id: str
    last_referenced_task_ids: list[str]
    pending_confirmation: dict | None
    recent_transcript_history: list[str]
```

No persistent conversational memory required.

---

## 8.3 System Prompt Design

The system prompt must:
- enforce voice-first behavior
- enforce clarification before destructive actions
- force tool usage for CRUD operations
- prevent hallucinated task confirmations
- encourage concise spoken responses
- preserve conversational naturalness

---

## 8.4 Tool Calling Strategy

The LLM receives:
- current transcript
- recent conversational history
- available tools

The LLM outputs:
- either conversational response
- or tool invocation request

*Critical Sanitization Requirement:* Because we are using an open-source model (Ollama), the orchestrator MUST include a strict JSON sanitization layer before executing tools.
1. Strip any markdown wrapping (e.g., remove ```json and ```).
2. Pass the raw string through a Pydantic validation model.
3. If Pydantic throws a ValidationError, the orchestrator must gracefully prompt the LLM to fix the arguments or fallback to asking the user for clarification. Do NOT crash the WebSocket session.

Tools are executed server-side.

---

# 9. Tool Definitions

## 9.1 Create Task Tool

Maps directly to existing API.

Input:

```json
{
  "title": "Call John",
  "due_date": "2026-05-28T09:00:00Z"
}
```

Maps to:

```python
TaskCreate
```

---

## 9.2 Update Task Tool

Maps directly to:

```python
TaskUpdate
```

---

## 9.3 Delete Task Tool

Requires:
- explicit confirmation
- resolved task identity

Never delete ambiguously.

---

## 9.4 Search Task Tool

Required because semantic references exist.

Examples:
- "my evening workout"
- "that task for tomorrow"
- "the dentist thing"

Implementation:
- SQL ilike matching
- optional pg_trgm similarity

Recommended:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

# 10. Conversational Flows

## 10.1 Create Multiple Tasks

Input:

```text
Tomorrow remind me to buy milk, call Sarah, and send the invoice.
```

Flow:

1. LLM extracts multiple tasks.
2. Backend executes sequential creates.
3. Assistant summarizes outcome.

Response:

```text
I added three tasks for tomorrow: buy milk, call Sarah, and send the invoice.
```

---

## 10.2 Ambiguous Delete

Input:

```text
Delete my workout task.
```

If multiple matches:

```text
I found two workout tasks. One is tomorrow evening and another is Friday morning. Which one should I delete?
```

Store pending action.

Wait for confirmation.

---

## 10.3 Agenda Summarization

Input:

```text
What do I have tomorrow?
```

Assistant should summarize naturally.

NOT:

```text
Task 1...
Task 2...
```

Instead:

```text
Tomorrow looks fairly busy. You have a morning dentist appointment, an afternoon product review meeting, and an evening workout.
```

---

# 11. Temporal Parsing

## Recommendation

Use:

```text
chrono-node
```

Reasoning:
- Open source
- Handles:
  - tomorrow
  - evening
  - next monday
  - afternoon
  - in two hours

The frontend should NOT parse dates.

All temporal interpretation occurs server-side.

---

# 12. Existing DTO Compatibility

The orchestration layer must map exactly to:

## Existing DTOs

### TaskCreate

```python
class TaskCreate(BaseModel):
    title: str
    status: TaskStatus = TaskStatus.TODO
    due_date: datetime | None
```

### TaskUpdate

```python
class TaskUpdate(BaseModel):
    title: str | None
    status: TaskStatus | None
    due_date: datetime | None
```

### TaskResponse

```python
class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: TaskStatus
    due_date: datetime | None
```

No schema modifications required.

---

# 13. Required New API Endpoints

## WebSocket Endpoint

```text
/ws/voice
```

Responsibilities:
- session lifecycle
- transcript ingestion
- orchestration
- realtime responses

---

## Optional Health Endpoint

```text
/voice/health
```

Checks:
- Ollama availability
- DB connectivity
- websocket readiness

---

# 14. Error Handling Strategy

## STT Failure

If transcript confidence low:

```text
I didn't quite catch that. Could you repeat it?
```

---

## WebSocket Disconnect

Frontend behavior:
- auto reconnect
- preserve transcript history locally
- retry with exponential backoff

---

## LLM Timeout

Timeout threshold:

```text
10 seconds
```

Fallback:

```text
I'm taking longer than expected. Please try again.
```

---

## Tool Execution Failure

Never expose stack traces.

Instead:

```text
I couldn't complete that task operation right now.
```

---

# 15. Security Constraints

For MVP:
- use guest session mode
- bind all task operations to placeholder user
- no JWT implementation
- no OAuth

Important:
- never trust client-provided task IDs
- validate ownership server-side

---

# 16. Deployment Strategy

## Frontend

Platform:
- Vercel Free Tier

Build:

```text
npm run build
```

---

## Backend

Platform:
- Existing AWS Lambda deployment

---

## Ollama

Recommended:
- Docker container
- Small VPS

Example:

```bash
docker run -d \
  -p 11434:11434 \
  ollama/ollama
```

Pull model:

```bash
ollama pull qwen2.5:7b
```

---

# 17. AI Coding Agent Implementation Order

## Phase 1 — Frontend Voice Runtime

Deliver:
- microphone capture
- STT
- TTS
- interruption cancellation
- websocket integration

---

## Phase 2 — WebSocket Backend

*Agent Instruction:* STOP before writing code for this phase. You must ask the user to provide the existing `main.py`, existing Pydantic models (DTOs), and database schema files. Do not hallucinate the existing API layer.

Deliver:
- websocket endpoint
- session lifecycle
- orchestration loop integrated with the user's provided FastAPI application structure

---

## Phase 3 — LLM Tool Calling

Deliver:
- Ollama integration
- CRUD tools
- confirmation flows

---

## Phase 4 — Conversational Memory

Deliver:
- pending confirmation handling
- semantic references
- contextual followups

---

## Phase 5 — Resilience

Deliver:
- reconnect handling
- timeout handling
- graceful degradation

---

# 18. Minimal Acceptance Criteria

The implementation is complete when:

- User can create tasks entirely by voice
- User can update tasks entirely by voice
- User can delete tasks entirely by voice
- User can query agenda conversationally
- Multiple task creation works
- Interruption handling works reliably
- No manual CRUD UI exists
- Backend reuses existing task APIs
- All inference runs on open-source/self-hosted runtime

---

# 19. Explicitly Excluded Scope

The following are intentionally excluded:

- Authentication system
- Multi-user production hardening
- Persistent conversation memory
- Analytics
- Background scheduling
- Mobile apps
- Email notifications
- Calendar integrations
- Multi-agent orchestration
- Whisper streaming infrastructure
- Kubernetes
- Redis
- Kafka
- Vector databases
- LangChain
- Heavy orchestration frameworks

---

# 20. Recommended OSS Libraries Summary

## Frontend

```text
react
vite
typescript
zustand
react-use-websocket
```

## Backend

```text
fastapi
uvicorn
websockets
httpx
pydantic
sqlalchemy
```

## AI Runtime

```text
ollama
qwen2.5:7b
```

## Date Parsing

```text
chrono-node
```

---

# 21. Final Implementation Notes for AI Coding Agent

Critical rules:

1. Never allow direct CRUD UI interactions.
2. Keep assistant responses short and conversational.
3. Always confirm destructive actions.
4. Prioritize interruption responsiveness over perfect transcription.
5. Keep orchestration deterministic.
6. Avoid introducing infrastructure not required by MVP.
7. Prefer explicit state machines over implicit async behavior.
8. Do not introduce heavy agent frameworks.
9. All task writes must flow through existing DTO contracts.
10. The frontend owns realtime conversational UX.

