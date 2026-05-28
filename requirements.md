### **Project Overview & Core Rules**

* 
**Project Name:** Voice Controlled Task Manager.


* 
**Objective:** Build a web application where users manage tasks entirely through voice interaction.


* 
**Core Capabilities:** The assistant must allow users to create , read , update , and delete tasks.


* 
**Strict UI Constraints:** Everything must happen through voice conversation. There must be absolutely no typing for task actions , no edit buttons , no delete buttons , and no manual CRUD interactions.


* 
**Overall Experience:** The assistant must listen to the user , respond using voice , and handle real-time conversations naturally. It should feel like a real AI voice agent, not a normal chatbot.


* 
**Timeline:** The estimated completion time is 1-2 days.



---

### **Technical Infrastructure**

* 
**Required Components:** The project must include Speech-to-Text (STT) , Text-to-Speech (TTS) , real-time voice interaction , voice-based CRUD operations , conversational AI workflows , and context-aware responses.


* 
**Storage Options:** Data can be handled using a Database (such as MySQL or PostgreSQL) , Local storage , or a Google Spreadsheet.


* 
**Authentication (Optional):** Signup, login, and session handling are optional but good to have.


* 
**Architecture Flexibility:** Candidates may structure the application using multiple agents if needed, such as a Planner agent, Conversation agent, Task execution agent, or Scheduling agent.



---

### **Conversational Behaviors & Edge Cases**

* 
**Context & Semantic Understanding:** The assistant must understand which task a user is referring to across turns. It must grasp time-based contexts natively (e.g., today, tomorrow, evening, morning, afternoon). It must also understand semantic meaning instead of relying only on exact task names (e.g., "evening workout").


* 
**Action Confirmation:** The assistant must confirm actions using voice naturally. For destructive actions like deleting, it must ask follow-up questions if the request is unclear and delete the task *only* after explicit confirmation.


* 
**Reading/Summarizing:** When reading the agenda, the assistant should summarize tasks conversationally instead of merely listing them out.


* 
**Handling Multiple Tasks:** The assistant must be able to process multiple task requests efficiently in a single breath and create them correctly.


* 
**Interruption Handling:** If the user interrupts while the assistant is speaking, the assistant must stop playback immediately and continue the conversation smoothly and naturally.



---

### **Reliability & Error Handling**

* 
**Graceful Degradation:** The system must naturally recover from unclear commands , STT failures , TTS failures , WebSocket disconnects , and LLM timeout issues.


* 
**Execution Safety:** The assistant should validate actions before execution and handle retries or fallback responses for invalid operations.


* 
**Latency:** It must maintain a smooth conversational flow with low response latency.



---

### **Submission Details**

* 
**Required Artifacts:** A GitHub repository , setup instructions , and preferably a live demo link so the project can be tested easily.


* 
**Deployment:** A production-grade deployment is not required. Deployment can be done using any free hosting platform (e.g., GitHub Pages, Vercel, Netlify, Render) or a free domain service.