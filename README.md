# ElectIQ - Election Intelligence Assistant

*"Democracy works best when citizens are informed. ElectIQ makes every voter an expert."*

Live Demo: https://electiq-ai.onrender.com

## Project Structure

```text
electiq/
├── backend/
│   ├── app.py              # Flask backend and APIs
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── templates/
│   │   └── index.html      # Main UI served by Flask
│   └── static/
│       ├── css/style.css   # Design system
│       └── js/app.js       # Frontend logic
├── .env.example            # Environment template
├── run.sh                  # Linux/Mac startup
├── run.bat                 # Windows startup
└── README.md
```

## Setup & Run

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/keys)
- Optional fallback: a [Google AI Studio Gemini API key](https://aistudio.google.com/app/apikey)

### Step 1: Clone or unzip the project

```bash
cd electiq
```

### Step 2: Set up your API keys

```bash
cp .env.example .env
```

Edit `.env` and set:

```text
GROQ_API_KEY=gsk_...your-key...
GOOGLE_API_KEY=...your-gemini-key...
```

Groq is the primary chat provider. Gemini is used automatically as a fallback if Groq is not configured or the Groq call fails.

### Step 3: Run

Linux/Mac:

```bash
chmod +x run.sh
./run.sh
```

Windows:

```text
Double-click run.bat
```

Manual:

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
python backend/app.py
```

### Step 4: Open in browser

```text
http://localhost:5000
```

## Features

| Feature | Description |
|---|---|
| AI Assistant | LangChain-powered conversational guide using Groq with Gemini fallback |
| Voter Journey | Step-by-step interactive journey from registration to results |
| Candidates | Full candidate profiles with Integrity Scores and manifestos |
| Compare | Side-by-side candidate comparison on 8+ dimensions |
| Booth Finder | Live queue estimates, directions, accessibility info |
| War Room | Real-time turnout tracker with hourly chart |
| Time Machine | Historical constituency data with AI analysis |
| Civic Quiz | Gamified election knowledge test with badges |
| Vote Impact | Personal vote impact calculator |
| Voter Check | EPIC number registration verification |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | AI chat using LangChain, Groq primary, Gemini fallback |
| GET  | `/api/candidates` | All candidates for constituency |
| GET  | `/api/candidate/<id>` | Single candidate detail |
| POST | `/api/compare` | Compare multiple candidates |
| GET  | `/api/timeline` | Election timeline events |
| GET  | `/api/booths` | Polling booth list with queue |
| GET  | `/api/turnout` | Live turnout data |
| GET  | `/api/history` | Historical election results |
| GET  | `/api/quiz` | Quiz questions |
| GET  | `/api/impact` | Vote impact calculator data |
| POST | `/api/voter-check` | EPIC number verification |

## Design System

- **Fonts:** Playfair Display for headings, DM Sans for body, JetBrains Mono for data
- **Theme:** Deep Civic: ink black, gold, and saffron
- **Responsive:** Mobile-first with collapsible sidebar
- **Animations:** CSS-only fade and slide transitions

## Hackathon Alignment

| Criteria | Implementation |
|---|---|
| Code Quality | Modular Flask backend with a small provider adapter |
| AI Integration | LangChain ecosystem with Groq primary model and Google Gemini fallback |
| UI/UX | Custom design system, animated, responsive |
| Google Services | Gemini fallback, Maps booth finder, Calendar integration hooks |
| Accessibility | High contrast, semantic HTML, keyboard navigation |
| Civic Impact | Voter education, multilingual support, integrity scoring |

Made with care by shanmukh datta
