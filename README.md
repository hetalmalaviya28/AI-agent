# VidyAI – AI Personalized Learning & Teacher Assistant Platform

**Challenge 20 – Education | IBM SkillsBuild | Groq API**

VidyAI is a full-stack, production-style AI education platform for government and rural schools in Gujarat. It combines a **ChatGPT-like conversational interface** with specialized AI agents for students and teachers.

---

## Features

### ChatGPT-like Chat Interface
- Real-time AI streaming responses
- Conversation history with rename/delete
- 6 specialized AI modes
- Markdown rendering (tables, code, lists, headings)
- Light/dark mode
- Fully responsive (mobile-friendly)

### 5 Specialized AI Agents
1. **Personalized Learning** – Recommends topics based on quiz scores and progress
2. **Lesson Plan Generator** – Creates complete classroom-ready lesson plans
3. **Assessment Generator** – Generates MCQs, True/False, Fill-in-blanks, Short Answer
4. **Performance Analytics** – Analyzes student performance data with insights
5. **Teacher Assistant** – Dedicated AI for teacher queries and classroom content

### Multilingual Support
- English, Gujarati, Hindi (AI auto-detects and responds in user's language)

### Dashboards
- **Student Dashboard**: Progress tracking, AI recommendations, quick actions
- **Teacher Dashboard**: Class overview, weak topics, student insights, quick actions

### Educational Resources
- Curated resources from NCERT, Khan Academy, DIKSHA, IBM SkillsBuild, BYJU's
- Filter by subject, class, topic, difficulty

---

## Quick Start

### 1. Prerequisites
- Python 3.9+ with pip
- A Groq API key from [console.groq.com](https://console.groq.com) (free tier available)

### 2. Install dependencies
```bash
cd vidyai
pip install flask flask-cors groq python-dotenv
```

### 3. Configure environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and set your Groq API key:
# GROQ_API_KEY=your_key_here
# GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Run the application
```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Demo Accounts

| Role    | Email               | Password |
|---------|---------------------|----------|
| Student | student@demo.com    | demo123  |
| Teacher | teacher@demo.com    | demo123  |

---

## Environment Variables

| Variable      | Description                          | Default                    |
|---------------|--------------------------------------|----------------------------|
| GROQ_API_KEY  | Your Groq API key (REQUIRED)         | –                          |
| GROQ_MODEL    | Groq model to use                    | llama-3.3-70b-versatile    |
| SECRET_KEY    | Flask session secret key             | (dev default)              |
| FLASK_DEBUG   | Enable debug mode                    | True                       |
| PORT          | Port to run on                       | 5000                       |

### Available Groq Models
- `llama-3.3-70b-versatile` (recommended – best quality)
- `llama3-70b-8192`
- `mixtral-8x7b-32768`
- `llama3-8b-8192` (fastest)
- `gemma2-9b-it`

---

## Project Structure

```
vidyai/
├── app.py              # Main Flask application (all routes)
├── ai_engine.py        # Groq API integration & AI agent prompts
├── database.py         # SQLite database layer
├── seed.py             # Demo data seeder
├── .env                # Environment variables (not committed)
├── .env.example        # Example environment template
├── vidyai.db           # SQLite database (auto-created)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── chat.html              # Main ChatGPT-like interface
│   ├── student_dashboard.html
│   ├── teacher_dashboard.html
│   ├── assessments.html
│   ├── lesson_plans.html
│   ├── resources.html
│   └── _sidebar.html          # Shared sidebar partial
└── static/
    ├── css/main.css    # Complete stylesheet (light + dark mode)
    └── js/
        ├── utils.js    # Shared utilities (theme, sidebar, logout)
        ├── chat.js     # Chat interface (streaming, history, modes)
        └── markdown.js # Markdown renderer
```

---

## Security

- Groq API key is stored server-side only in `.env`
- API key is never sent to the browser or included in responses
- Session-based authentication
- Role-based access (student vs teacher)
- Input validation on all API endpoints
- Error messages sanitized before display

---

## Technology Stack

| Component   | Technology                     |
|-------------|-------------------------------|
| Backend     | Python 3 + Flask               |
| AI Engine   | Groq API (LLaMA 3.3 70B)       |
| Database    | SQLite (via built-in sqlite3)  |
| Frontend    | Vanilla HTML/CSS/JavaScript    |
| Streaming   | Server-Sent Events (SSE)       |
| Auth        | Flask sessions + SHA-256       |

---

## IBM Technologies Used

- **IBM Bob** – Development environment for building and iterating
- **IBM Granite AI Architecture** – Educational AI design principles
- **IBM SkillsBuild** – Referenced as educational resource for students
- **IBM Cloud** – Ready for deployment on IBM Cloud Code Engine

---

## AI Agent Details

Each mode uses a specialized system prompt:

| Mode            | Agent Focus                                    |
|-----------------|------------------------------------------------|
| General Tutor   | All-subjects Q&A, step-by-step explanations    |
| Personalized    | Progress analysis, learning path recommendations|
| Lesson Planner  | Complete structured lesson plans               |
| Assessment      | Quiz/test generation with answers + feedback   |
| Analytics       | Performance data interpretation                |
| Teacher Assist  | Classroom content, worksheets, homework        |

---

Built for **IBM SkillsBuild – Challenge 20: Education**
