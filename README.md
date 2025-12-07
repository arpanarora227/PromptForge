# Hackathon Project (Hack Trent 2025)
# **PromptForge – Prompt Template Engine**

A system that lets users control *how* AI thinks, not just what it answers.

PromptForge is a **Prompt Template Engine** that stores and applies personal response styles, solving the biggest problems in everyday AI use: no memory of your style, constant repetition, and inconsistent responses .
Think of it as a **template holder for your mind** - creating your own AI behavior patterns without training a model.

*Deployed Website:* [PromptForge](https://promptforge-fyt1.onrender.com/)


---

## **🚀 Features**

### **1. Prompt Template Engine**

Create, store, and apply custom prompt structures instantly:

* Answer-only mode
* Detailed explanation mode
* Teaching mode
* Research assistant mode
* Any personal style you define

These templates guide AI output consistently across sessions, fixing inconsistency and repetition issues shown on page 3 .

---

## **🧠 Why PromptForge?**

Current AI systems have three major issues:

* **No memory** of how you like responses
* **Constant repetition** of instructions like “explain in detail” or “keep it short”
* **Zero consistency**, switching styles between queries

PromptForge solves this by injecting your preferred template into every message, giving AI your consistent voice and structure every time .

---

## **🛠️ Tech Stack**

**Frontend**: HTML, CSS, JavaScript
**Backend**: Python (Flask)
**AI Engine**: OpenRouter (Llama-3.1-70b-Instruct)
**Database**: Snowflake (for storing history and metadata)
**Voice Integration**: ElevenLabs API
**Deployment**: Render + GitHub

---

## **⚙️ How It Works**

1. **User Input**
   Select template + enter query.

2. **Template Injection**
   Flask merges your defined template into the user query.

3. **AI Routing (OpenRouter)**
   The request is sent to Llama-3.1-70b-Instruct.

4. **Structured Response**
   The model returns output shaped by your custom template.

5. **Snowflake Storage**
   Saves history, metadata, and template usage.

---

## **🔮 Future Scope**

* File upload support (PDF, CSV) for contextual templates
* ML workflow assistant (training, preprocessing automation)
* Multi-model routing
* Real-time voice assistant
* User authentication
* Team templates
* Vision: turning PromptForge into a universal AI plugin that attaches to any chatbot or research tool

---
