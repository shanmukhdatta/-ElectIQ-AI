import json
import os
import random
from datetime import datetime, timedelta
import bleach
import re
import logging

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress

from backend.config import Config

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/templates")

allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
CORS(app, origins=allowed_origins, methods=['GET', 'POST'], allow_headers=['Content-Type'])

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=['200 per day', '50 per hour'])
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': Config.CACHE_TIMEOUT_STATIC})
Compress(app)

GROQ_MODEL = Config.GROQ_MODEL
GEMINI_MODEL = Config.GEMINI_MODEL

def build_chat_models() -> list[tuple[str, object]]:
    """Build the chat models based on available API keys."""
    models = []
    groq_api_key = os.environ.get("GROQ_API_KEY")
    gemini_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if groq_api_key:
        models.append((
            "groq",
            ChatGroq(
                api_key=groq_api_key,
                model=GROQ_MODEL,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
            ),
        ))

    if gemini_api_key:
        models.append((
            "gemini",
            ChatGoogleGenerativeAI(
                google_api_key=gemini_api_key,
                model=GEMINI_MODEL,
                temperature=Config.TEMPERATURE,
                max_output_tokens=Config.MAX_TOKENS,
            ),
        ))

    return models

_CHAT_MODELS = None

def get_chat_models() -> list[tuple[str, object]]:
    """Get the cached chat models, building them if necessary."""
    global _CHAT_MODELS
    if _CHAT_MODELS is None:
        _CHAT_MODELS = build_chat_models()
    return _CHAT_MODELS

def to_langchain_messages(system_prompt: str, messages: list[dict]) -> list:
    """Convert raw messages to Langchain message objects."""
    langchain_messages = [SystemMessage(content=system_prompt)]

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if not content:
            continue
        if role == "assistant":
            langchain_messages.append(AIMessage(content=content))
        elif role == "system":
            langchain_messages.append(SystemMessage(content=content))
        else:
            langchain_messages.append(HumanMessage(content=content))

    return langchain_messages

def response_text(response) -> str:
    """Extract string text from a model response."""
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text", ""))
        return "".join(parts).strip()
    return str(content)

def invoke_chat(system_prompt: str, messages: list[dict]) -> tuple[str, str]:
    """Invoke the chat models using the fallback mechanism."""
    chat_messages = to_langchain_messages(system_prompt, messages)
    errors = []

    for provider, model in get_chat_models():
        try:
            return response_text(model.invoke(chat_messages)), provider
        except Exception as exc:
            logger.warning("%s chat provider failed: %s", provider, exc)
            errors.append(f"{provider}: {exc}")

    raise RuntimeError(
        "No chat provider succeeded. Configure GROQ_API_KEY for the primary provider "
        "or GOOGLE_API_KEY/GEMINI_API_KEY for the Gemini fallback. "
        f"Provider errors: {' | '.join(errors) if errors else 'none'}"
    )

EPIC_PATTERN = re.compile(r'^[A-Z]{3}[0-9]{7}$')

def sanitise(text: str, max_len: int = 2000) -> str:
    """Sanitise and truncate user input."""
    if not text or not isinstance(text, str):
        return ''
    return bleach.clean(text.strip())[:max_len]

# ─────────────────────────────────────────────────────────────────────────────
# Mock Election Data
# ─────────────────────────────────────────────────────────────────────────────

CANDIDATES = [
    {
        "id": 1,
        "name": "Aarav Mehta",
        "party": "Progressive Alliance",
        "party_color": "#2563eb",
        "constituency": "Mumbai North",
        "photo": "👨‍💼",
        "education": "LLB, Delhi University",
        "assets": "₹2.4 Cr",
        "criminal_cases": 0,
        "attendance": "87%",
        "integrity_score": 82,
        "manifesto": {
            "education": "Free university education for all students below poverty line",
            "healthcare": "Universal healthcare coverage under ₹500/month",
            "economy": "IT corridor expansion creating 50,000 jobs",
            "environment": "30% renewable energy by 2030",
            "infrastructure": "Metro expansion to all major suburbs"
        }
    },
    {
        "id": 2,
        "name": "Priya Sharma",
        "party": "National Unity Front",
        "party_color": "#dc2626",
        "constituency": "Mumbai North",
        "photo": "👩‍💼",
        "education": "MBA, IIM Ahmedabad",
        "assets": "₹1.1 Cr",
        "criminal_cases": 0,
        "attendance": "92%",
        "integrity_score": 91,
        "manifesto": {
            "education": "Smart classrooms in every government school",
            "healthcare": "1000 new primary health centres",
            "economy": "MSME support fund of ₹500 Cr",
            "environment": "Plant 10 million trees in 5 years",
            "infrastructure": "Highway expansion and rural connectivity"
        }
    },
    {
        "id": 3,
        "name": "Rajesh Kumar",
        "party": "Peoples Democratic Party",
        "party_color": "#16a34a",
        "constituency": "Mumbai North",
        "photo": "🧑‍💼",
        "education": "BA Political Science, Mumbai University",
        "assets": "₹78 Lakh",
        "criminal_cases": 1,
        "attendance": "74%",
        "integrity_score": 63,
        "manifesto": {
            "education": "Scholarship for SC/ST students in private colleges",
            "healthcare": "Free medicines for BPL families",
            "economy": "Farm loan waiver and minimum support price reform",
            "environment": "Ban single-use plastic by 2026",
            "infrastructure": "Rural roads under PM Gram Sadak Yojana 2.0"
        }
    }
]

ELECTION_TIMELINE = [
    {"event": "Voter Registration Opens", "date": "2026-04-01", "status": "completed"},
    {"event": "Voter Registration Closes", "date": "2026-04-20", "status": "completed"},
    {"event": "Candidate Nomination", "date": "2026-04-25", "status": "completed"},
    {"event": "Campaign Period", "date": "2026-05-01", "status": "upcoming"},
    {"event": "Polling Day", "date": "2026-05-15", "status": "upcoming"},
    {"event": "Result Declaration", "date": "2026-05-18", "status": "upcoming"}
]

TURNOUT_DATA = {
    "current": 34,
    "last_election": 67,
    "national_avg": 61,
    "constituency": "Mumbai North",
    "hours": [
        {"hour": "7AM", "turnout": 8},
        {"hour": "9AM", "turnout": 18},
        {"hour": "11AM", "turnout": 28},
        {"hour": "1PM", "turnout": 34},
        {"hour": "3PM", "turnout": None},
        {"hour": "5PM", "turnout": None},
        {"hour": "6PM", "turnout": None},
    ]
}

BOOTHS = [
    {"id": 1, "name": "Government School, Andheri West", "ward": "Ward 71", "officer": "Smt. Lalitha Devi", "queue": "Short (5-10 min)", "accessibility": True, "lat": 19.1136, "lng": 72.8697},
    {"id": 2, "name": "Municipal Corporation Hall, Versova", "ward": "Ward 72", "officer": "Shri. Ramesh Patil", "queue": "Moderate (15-20 min)", "accessibility": True, "lat": 19.1217, "lng": 72.8120},
    {"id": 3, "name": "Community Centre, Lokhandwala", "ward": "Ward 73", "officer": "Smt. Kavita Singh", "queue": "Long (30+ min)", "accessibility": False, "lat": 19.1353, "lng": 72.8345}
]

HISTORY_DATA = [
    {"year": 2014, "winner": "BJP", "margin": 12000, "turnout": 58},
    {"year": 2019, "winner": "Congress", "margin": 4300, "turnout": 63},
    {"year": 2024, "winner": "BJP", "margin": 8900, "turnout": 67},
]

CONSTITUENCIES = [
    'Mumbai North', 'Delhi Central', 'Bangalore South',
    'Chennai North', 'Kolkata East', 'Hyderabad', 'Pune', 'Jaipur'
]

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Return the main index page."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_CHAT)
def chat():
    """Handle chat requests with the AI model."""
    data = request.json or {}
    messages = data.get("messages", [])
    
    for m in messages:
        m['content'] = sanitise(m.get('content', ''), Config.MAX_CHAT_LEN)
        
    user_profile = data.get("profile", {})
    
    system_prompt = f"""You are ElectIQ — an AI-powered Election Intelligence Assistant for Indian elections.
You are helpful, politically neutral, factual, and civic-minded. You help citizens understand elections, voting processes, candidates, and their democratic rights.

Current user profile:
- State: {user_profile.get('state', 'Not specified')}
- Constituency: {user_profile.get('constituency', Config.DEFAULT_CONSTITUENCY)}
- Language preference: {user_profile.get('language', 'English')}
- First time voter: {user_profile.get('first_time', 'Unknown')}

You have access to the following real data:
CANDIDATES: {json.dumps(CANDIDATES, ensure_ascii=False)}
ELECTION TIMELINE: {json.dumps(ELECTION_TIMELINE, ensure_ascii=False)}
POLLING BOOTHS: {json.dumps(BOOTHS, ensure_ascii=False)}

Key rules:
1. Always be politically NEUTRAL — present all candidates equally
2. For booth locations, suggest the user use the Booth Finder feature
3. For registration, guide them step by step
4. For candidate comparison, be data-driven and factual
5. Keep responses concise and friendly
6. If asked about policies, compare ALL candidates fairly
7. Encourage voting and civic participation
8. Use markdown formatting with emojis where appropriate

When comparing candidates, always compare ALL three candidates fairly and equally."""

    try:
        reply, provider = invoke_chat(system_prompt, messages)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify({"reply": reply, "provider": provider})

@app.route("/api/candidates", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_CANDIDATES)
def get_candidates():
    """Return the list of candidates for a constituency."""
    constituency = request.args.get("constituency", Config.DEFAULT_CONSTITUENCY)
    return jsonify({"candidates": CANDIDATES, "constituency": constituency})

@app.route("/api/candidate/<int:cid>", methods=["GET"])
def get_candidate(cid: int):
    """Return a single candidate by ID."""
    candidate = next((c for c in CANDIDATES if c["id"] == cid), None)
    if not candidate:
        return jsonify({"error": "Not found"}), 404
    return jsonify(candidate)

@app.route("/api/timeline", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_timeline():
    """Return the election timeline."""
    return jsonify({"events": ELECTION_TIMELINE})

@app.route("/api/booths", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_booths():
    """Return the list of polling booths."""
    return jsonify({"booths": BOOTHS})

@app.route("/api/turnout", methods=["GET"])
def get_turnout():
    """Return voter turnout data."""
    return jsonify(TURNOUT_DATA)

@app.route("/api/history", methods=["GET"])
def get_history():
    """Return historical election data."""
    constituency = request.args.get("constituency", Config.DEFAULT_CONSTITUENCY)
    return jsonify({"constituency": constituency, "history": HISTORY_DATA})

@app.route("/api/integrity-score/<int:cid>", methods=["GET"])
def get_integrity(cid: int):
    """Return the integrity score breakdown for a candidate."""
    candidate = next((c for c in CANDIDATES if c["id"] == cid), None)
    if not candidate:
        return jsonify({"error": "Not found"}), 404
    breakdown = {
        "asset_growth": random.randint(60, 95),
        "criminal_cases": 100 if candidate["criminal_cases"] == 0 else max(0, 100 - candidate["criminal_cases"] * 30),
        "attendance": int(candidate["attendance"].strip("%")),
        "promise_delivery": random.randint(55, 90),
        "total": candidate["integrity_score"]
    }
    return jsonify({"candidate": candidate["name"], "breakdown": breakdown})

@app.route("/api/compare", methods=["POST"])
def compare_candidates():
    """Compare multiple candidates by ID."""
    data = request.json or {}
    ids = data.get("ids", [1, 2, 3])
    selected = [c for c in CANDIDATES if c["id"] in ids]
    return jsonify({"candidates": selected})

@app.route("/api/voter-check", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_VOTER)
def voter_check():
    """Check voter registration using EPIC number."""
    data = request.json or {}
    epic = sanitise(data.get("epic", ""), Config.MAX_EPIC_LEN).upper()
    if not EPIC_PATTERN.match(epic):
        return jsonify({'registered': False, 'message': 'Invalid EPIC format'}), 400
    
    return jsonify({
        "registered": True,
        "name": "Voter Name (Demo)",
        "constituency": Config.DEFAULT_CONSTITUENCY,
        "booth": "Government School, Andheri West",
        "booth_no": "B-073",
        "serial_no": random.randint(100, 999)
    })

@app.route("/api/impact", methods=["GET"])
def voter_impact():
    """Return data showing the impact of a single vote."""
    return jsonify({
        "constituency": Config.DEFAULT_CONSTITUENCY,
        "last_margin": 4300,
        "eligible_voters": 180000,
        "turnout_last": 67,
        "your_area_turnout": 54,
        "national_avg": 61,
        "message": "In 2019, the winning margin was just 4,300 votes. Every vote truly counts!"
    })

@app.route("/api/quiz", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_quiz():
    """Return election quiz questions."""
    questions = [
        {
            "q": "What does NOTA stand for?",
            "options": ["None Of The Alternatives", "None Of The Above", "No Other Than All", "Not One True Answer"],
            "answer": 1,
            "explanation": "NOTA (None Of The Above) allows voters to reject all candidates while still participating."
        },
        {
            "q": "What is the minimum age to vote in India?",
            "options": ["16 years", "18 years", "21 years", "25 years"],
            "answer": 1,
            "explanation": "The 61st Constitutional Amendment (1988) lowered the voting age from 21 to 18."
        },
        {
            "q": "What is an EPIC number?",
            "options": ["Electrical Power Index Card", "Elector's Photo Identity Card", "Election Poll Identity Certificate", "Electoral Process Identity Code"],
            "answer": 1,
            "explanation": "EPIC (Elector's Photo Identity Card) is your voter ID issued by the Election Commission."
        },
        {
            "q": "What is VVPAT?",
            "options": ["Voter Verified Paper Audit Trail", "Verified Voting Process Automation Tool", "Voter Validity Paper Authentication Terminal", "Vote Verification Process and Audit Track"],
            "answer": 0,
            "explanation": "VVPAT provides a paper receipt allowing voters to verify their vote was cast correctly."
        },
        {
            "q": "Who oversees elections in India?",
            "options": ["President of India", "Supreme Court", "Election Commission of India", "Parliament"],
            "answer": 2,
            "explanation": "The Election Commission of India (ECI) is an autonomous constitutional body responsible for administering elections."
        }
    ]
    return jsonify({"questions": questions})

@app.route('/api/fact-check', methods=['POST'])
@limiter.limit('5 per minute')
def fact_check():
    """AI-powered election fact checker."""
    data = request.json or {}
    claim = sanitise(data.get('claim', ''), 500)
    if not claim:
        return jsonify({'error': 'No claim provided'}), 400
    system = (
        'You are an Indian election fact-checker. '
        'Respond ONLY with valid JSON (no markdown): '
        '{"verdict":"TRUE"|"FALSE"|"MISLEADING"|"UNVERIFIABLE",'
        '"explanation":"one sentence","sources":["url"]}'
    )
    try:
        reply, _ = invoke_chat(system, [{'role': 'user', 'content': claim}])
        clean = reply.strip().lstrip('```json').rstrip('```').strip()
        return jsonify(json.loads(clean))
    except Exception:
        return jsonify({'verdict': 'UNVERIFIABLE', 'explanation': 'Cannot verify at this time.', 'sources': []})

@app.route('/api/constituencies', methods=['GET'])
def list_constituencies():
    """Return filtered list of constituencies."""
    query = sanitise(request.args.get('q', ''), 100).lower()
    filtered = [c for c in CONSTITUENCIES if query in c.lower()]
    return jsonify({'constituencies': filtered})

@app.after_request
def add_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' fonts.googleapis.com maps.googleapis.com www.googletagmanager.com translate.google.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com fonts.gstatic.com; "
        "font-src fonts.gstatic.com; "
        "img-src 'self' data: maps.googleapis.com maps.gstatic.com *.googleapis.com www.googletagmanager.com; "
        "connect-src 'self' maps.googleapis.com www.google-analytics.com;"
    )
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unhandled exceptions globally."""
    logger.error('Unhandled exception: %s', e, exc_info=True)
    return jsonify({'error': 'An internal error occurred'}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors."""
    return jsonify({'error': 'Too many requests. Please slow down.'}), 429

if __name__ == '__main__':
    required_keys = []  # add key names if you want startup validation
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, port=5000)
