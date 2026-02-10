# Disaster Preparedness Assistant (Gemini + Groq) — Streamlit Chatbot

Final Project: **LLM-Based Tools and Gemini API Integration**  
A Streamlit chatbot that helps users with **flood (banjir)** and **earthquake (gempa)** situations using LLMs (Gemini / Groq), with configurable parameters and memory.

> **Important note:** This app is designed for the “safe window” moment (when you are already safe enough to open your phone). It does **not** replace official emergency services.

---

## Features

- **Two Modes**
  - **⚡ Now Action**: Prioritized guidance for the next 0–10 minutes + ready-to-copy messages (family/RT/posko).
  - **🧰 Preparedness Plan**: Go-bag checklist + home preparation + evacuation plan + simple 7-day plan.

- **Creative Parameters (Sidebar Controls)**
  - Provider: **Auto / Gemini / Groq**
  - Language style: **Formal / Santai**
  - Temperature slider

- **Provider Integration**
  - **Auto** tries **Gemini first** and falls back to **Groq** if needed.
  - The UI shows **Last used provider**.

- **Memory**
  - Chat history is stored in `st.session_state` so the bot can respond with context from previous messages.

---

## Tech Stack

- **Streamlit** (UI)
- **LangChain**
- **Gemini API** via `langchain-google-genai`
- **Groq API** via `langchain-groq`

---

