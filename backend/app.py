from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import json
import os
import random
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/templates")
CORS(app)

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")


def build_chat_models():
    models = []
    groq_api_key = os.environ.get("GROQ_API_KEY")
    gemini_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if groq_api_key:
        models.append((
            "groq",
            ChatGroq(
                api_key=groq_api_key,
                model=GROQ_MODEL,
                temperature=0.3,
                max_tokens=1000,
            ),
        ))

    if gemini_api_key:
        models.append((
            "gemini",
            ChatGoogleGenerativeAI(
                google_api_key=gemini_api_key,
                model=GEMINI_MODEL,
                temperature=0.3,
                max_output_tokens=1000,
            ),
        ))

    return models


def to_langchain_messages(system_prompt, messages):
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


def response_text(response):
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


def invoke_chat(system_prompt, messages):
    chat_messages = to_langchain_messages(system_prompt, messages)
    errors = []

    for provider, model in build_chat_models():
        try:
            return response_text(model.invoke(chat_messages)), provider
        except Exception as exc:
            app.logger.warning("%s chat provider failed: %s", provider, exc)
            errors.append(f"{provider}: {exc}")

    raise RuntimeError(
        "No chat provider succeeded. Configure GROQ_API_KEY for the primary provider "
        "or GOOGLE_API_KEY/GEMINI_API_KEY for the Gemini fallback. "
        f"Provider errors: {' | '.join(errors) if errors else 'none'}"
    )

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

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    user_profile = data.get("profile", {})
    
    system_prompt = f"""You are ElectIQ — an AI-powered Election Intelligence Assistant for Indian elections.
You are helpful, politically neutral, factual, and civic-minded. You help citizens understand elections, voting processes, candidates, and their democratic rights.

Current user profile:
- State: {user_profile.get('state', 'Not specified')}
- Constituency: {user_profile.get('constituency', 'Mumbai North (default)')}
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
def get_candidates():
    constituency = request.args.get("constituency", "Mumbai North")
    return jsonify({"candidates": CANDIDATES, "constituency": constituency})

@app.route("/api/candidate/<int:cid>", methods=["GET"])
def get_candidate(cid):
    candidate = next((c for c in CANDIDATES if c["id"] == cid), None)
    if not candidate:
        return jsonify({"error": "Not found"}), 404
    return jsonify(candidate)

@app.route("/api/timeline", methods=["GET"])
def get_timeline():
    return jsonify({"events": ELECTION_TIMELINE})

@app.route("/api/booths", methods=["GET"])
def get_booths():
    return jsonify({"booths": BOOTHS})

@app.route("/api/turnout", methods=["GET"])
def get_turnout():
    return jsonify(TURNOUT_DATA)

@app.route("/api/history", methods=["GET"])
def get_history():
    constituency = request.args.get("constituency", "Mumbai North")
    return jsonify({"constituency": constituency, "history": HISTORY_DATA})

@app.route("/api/integrity-score/<int:cid>", methods=["GET"])
def get_integrity(cid):
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
    data = request.json
    ids = data.get("ids", [1, 2, 3])
    selected = [c for c in CANDIDATES if c["id"] in ids]
    return jsonify({"candidates": selected})

@app.route("/api/voter-check", methods=["POST"])
def voter_check():
    data = request.json
    epic = data.get("epic", "")
    if len(epic) >= 6:
        return jsonify({
            "registered": True,
            "name": "Voter Name (Demo)",
            "constituency": "Mumbai North",
            "booth": "Government School, Andheri West",
            "booth_no": "B-073",
            "serial_no": random.randint(100, 999)
        })
    return jsonify({"registered": False, "message": "EPIC number not found"})

@app.route("/api/impact", methods=["GET"])
def voter_impact():
    return jsonify({
        "constituency": "Mumbai North",
        "last_margin": 4300,
        "eligible_voters": 180000,
        "turnout_last": 67,
        "your_area_turnout": 54,
        "national_avg": 61,
        "message": "In 2019, the winning margin was just 4,300 votes. Every vote truly counts!"
    })

@app.route("/api/quiz", methods=["GET"])
def get_quiz():
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
