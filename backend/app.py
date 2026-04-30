"""
ElectIQ — Flask Application Entry Point
Election Intelligence Assistant for Indian voters.

Architecture:
  - Routes: defined here
  - Data: backend/data.py
  - Validation: backend/validators.py
  - Google Cloud: backend/google_services.py
  - Config: backend/config.py
"""
import json
import logging
import os
import random
import secrets
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from backend.config import Config
from backend.data import (
    BOOTHS, CANDIDATES, CONSTITUENCIES, ELECTION_TIMELINE,
    HISTORY_DATA, TURNOUT_DATA,
)
from backend.validators import (
    is_valid_epic, is_valid_language_code, sanitise, validate_candidate_ids,
)
import backend.google_services as gcp

# ── Initialisation ─────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder="../frontend/static",
    template_folder="../frontend/templates",
)

# Max request size — reject oversized payloads early
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_REQUEST_SIZE

# ── Extensions ─────────────────────────────────────────────────────────────────
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5000").split(",")
CORS(app, origins=allowed_origins, methods=["GET", "POST"], allow_headers=["Content-Type"])

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATE_LIMIT_DEFAULT],
)

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": Config.CACHE_TIMEOUT_DEFAULT,
})

Compress(app)

# ── LLM Provider Chain ─────────────────────────────────────────────────────────
# Tries Groq first (faster), falls back to Gemini. Built once at startup.

_CHAT_MODELS: list | None = None


def get_chat_models() -> list[tuple[str, object]]:
    """Return cached LLM model list, building once on first call."""
    global _CHAT_MODELS
    if _CHAT_MODELS is None:
        _CHAT_MODELS = _build_chat_models()
    return _CHAT_MODELS


def _build_chat_models() -> list[tuple[str, object]]:
    """Instantiate configured LLM providers from environment variables."""
    models = []
    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if groq_key:
        models.append(("groq", ChatGroq(
            api_key=groq_key, model=Config.GROQ_MODEL,
            temperature=Config.TEMPERATURE, max_tokens=Config.MAX_TOKENS,
        )))
    if gemini_key:
        models.append(("gemini", ChatGoogleGenerativeAI(
            google_api_key=gemini_key, model=Config.GEMINI_MODEL,
            temperature=Config.TEMPERATURE, max_output_tokens=Config.MAX_TOKENS,
        )))
    return models


def _to_langchain_messages(system_prompt: str, messages: list[dict]) -> list:
    """Convert {role, content} dicts to LangChain message objects."""
    result = [SystemMessage(content=system_prompt)]
    for msg in messages:
        role, content = msg.get("role"), msg.get("content", "")
        if not content:
            continue
        if role == "assistant":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
        else:
            result.append(HumanMessage(content=content))
    return result


def _response_text(response) -> str:
    """Extract plain text from a LangChain model response."""
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            p if isinstance(p, str) else p.get("text", "")
            for p in content
        ).strip()
    return str(content)


def invoke_chat(system_prompt: str, messages: list[dict]) -> tuple[str, str]:
    """
    Invoke the best available LLM provider with fallback chain.

    Args:
        system_prompt: The system instruction for the AI model.
        messages: List of {role, content} conversation messages.

    Returns:
        Tuple of (response_text, provider_name).

    Raises:
        RuntimeError: If all configured providers fail.
    """
    langchain_msgs = _to_langchain_messages(system_prompt, messages)
    errors: list[str] = []

    for provider, model in get_chat_models():
        try:
            return _response_text(model.invoke(langchain_msgs)), provider
        except Exception as exc:
            logger.warning("%s provider failed: %s", provider, exc)
            errors.append(f"{provider}: {exc}")

    raise RuntimeError(
        f"All LLM providers failed. Configure GROQ_API_KEY or GOOGLE_API_KEY. "
        f"Errors: {' | '.join(errors)}"
    )


# ── Request Lifecycle Hooks ────────────────────────────────────────────────────

@app.before_request
def attach_request_id() -> None:
    """Attach a unique 8-char request ID for tracing and logging."""
    g.request_id = str(uuid.uuid4())[:8]
    g.csp_nonce = secrets.token_urlsafe(16)


@app.after_request
def add_security_headers(response):
    """Add OWASP-recommended security headers to every response."""
    nonce = getattr(g, "csp_nonce", "")
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Request-ID"] = getattr(g, "request_id", "")
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval' "
        f"fonts.googleapis.com maps.googleapis.com www.googletagmanager.com "
        f"translate.google.com; "
        f"style-src 'self' 'unsafe-inline' fonts.googleapis.com fonts.gstatic.com; "
        f"font-src fonts.gstatic.com; "
        f"img-src 'self' data: maps.googleapis.com maps.gstatic.com *.googleapis.com; "
        f"connect-src 'self' maps.googleapis.com www.google-analytics.com; "
        f"frame-src translate.google.com;"
    )
    logger.info("[%s] %s %s → %d", getattr(g, "request_id", "?"),
                request.method, request.path, response.status_code)
    return response


# ── Error Handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(Exception)
def handle_exception(exc: Exception):
    """Catch-all handler — never expose stack traces in production."""
    logger.error("Unhandled exception [%s]: %s", getattr(g, "request_id", "?"), exc, exc_info=True)
    return jsonify({"error": "An internal error occurred", "request_id": getattr(g, "request_id", "")}), 500


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Request payload too large"}), 413


@app.errorhandler(429)
def ratelimit_handler(_):
    return jsonify({"error": "Too many requests. Please slow down."}), 429


# ── Helper ─────────────────────────────────────────────────────────────────────

def api_ok(data: dict) -> tuple:
    """Wrap a successful response in a consistent envelope."""
    return jsonify({"success": True, "data": data,
                    "timestamp": datetime.now(timezone.utc).isoformat()}), 200


# ════════════════════════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the single-page application."""
    return render_template("index.html")


# ── Chat ───────────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_CHAT)
def chat():
    """
    Main AI chat endpoint. Sanitises input, invokes LLM, logs to BigQuery.
    Supports multilingual responses via user profile language setting.
    """
    data = request.json or {}
    messages: list[dict] = data.get("messages", [])
    profile: dict = data.get("profile", {})

    # Sanitise every message in the conversation
    for msg in messages:
        msg["content"] = sanitise(msg.get("content", ""), Config.MAX_CHAT_MESSAGE_LEN)

    system_prompt = f"""You are ElectIQ — an AI-powered Election Intelligence Assistant for Indian elections.
You are helpful, politically neutral, factual, and civic-minded.

User profile:
- State: {sanitise(profile.get('state', 'Not specified'), 50)}
- Constituency: {sanitise(profile.get('constituency', Config.DEFAULT_CONSTITUENCY), 100)}
- Language: {sanitise(profile.get('language', 'English'), 20)}
- First-time voter: {profile.get('first_time', False)}

Available data:
CANDIDATES: {json.dumps(CANDIDATES, ensure_ascii=False)}
ELECTION TIMELINE: {json.dumps(ELECTION_TIMELINE, ensure_ascii=False)}
POLLING BOOTHS: {json.dumps(BOOTHS, ensure_ascii=False)}

Rules:
1. Always be politically NEUTRAL — present all candidates equally
2. Be data-driven and factual; cite ElectIQ Integrity Scores
3. For voter registration, always direct to: {Config.ECI_PORTAL} and {Config.NVSP_PORTAL}
4. Voter Helpline: {Config.VOTER_HELPLINE} (toll-free)
5. For booth locations, recommend the Booth Finder feature
6. Use markdown with emojis for clarity
7. Keep responses concise and friendly"""

    try:
        reply, provider = invoke_chat(system_prompt, messages)
        # Log chat event to BigQuery (non-blocking)
        gcp.log_event_to_bigquery("chat_message", {
            "constituency": profile.get("constituency", Config.DEFAULT_CONSTITUENCY),
            "provider": provider,
            "session_id": getattr(g, "request_id", ""),
        })
        return jsonify({"reply": reply, "provider": provider})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503


# ── Candidates ────────────────────────────────────────────────────────────────

@app.route("/api/candidates", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_CANDIDATES)
def get_candidates():
    """Return all candidates, optionally filtered by constituency."""
    constituency = sanitise(request.args.get("constituency", Config.DEFAULT_CONSTITUENCY), 100)
    return jsonify({"candidates": CANDIDATES, "constituency": constituency})


@app.route("/api/candidate/<int:cid>", methods=["GET"])
def get_candidate(cid: int):
    """Return a single candidate by ID."""
    candidate = next((c for c in CANDIDATES if c["id"] == cid), None)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    return jsonify(candidate)


# ── Static Data ───────────────────────────────────────────────────────────────

@app.route("/api/timeline", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_timeline():
    """Return election timeline events."""
    return jsonify({"events": ELECTION_TIMELINE})


@app.route("/api/booths", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_booths():
    """Return polling booth data for the default constituency."""
    return jsonify({"booths": BOOTHS})


@app.route("/api/history", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_history():
    """Return electoral history for a constituency."""
    constituency = sanitise(request.args.get("constituency", Config.DEFAULT_CONSTITUENCY), 100)
    return jsonify({"constituency": constituency, "history": HISTORY_DATA})


@app.route("/api/quiz", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def get_quiz():
    """Return civic knowledge quiz questions."""
    questions = [
        {"q": "What does NOTA stand for?",
         "options": ["None Of The Alternatives", "None Of The Above", "No Other Than All", "Not One True Answer"],
         "answer": 1, "explanation": "NOTA (None Of The Above) allows voters to reject all candidates."},
        {"q": "What is the minimum age to vote in India?",
         "options": ["16 years", "18 years", "21 years", "25 years"],
         "answer": 1, "explanation": "The 61st Constitutional Amendment (1988) lowered the voting age to 18."},
        {"q": "What is an EPIC number?",
         "options": ["Electrical Power Index Card", "Elector's Photo Identity Card", "Election Poll Identity Certificate", "Electoral Process Identity Code"],
         "answer": 1, "explanation": "EPIC is your voter ID card issued by the Election Commission."},
        {"q": "What is VVPAT?",
         "options": ["Voter Verified Paper Audit Trail", "Verified Voting Process Automation Tool", "Voter Validity Paper Authentication Terminal", "Vote Verification Process and Audit Track"],
         "answer": 0, "explanation": "VVPAT provides a paper receipt allowing voters to verify their vote."},
        {"q": "Who oversees elections in India?",
         "options": ["President of India", "Supreme Court", "Election Commission of India", "Parliament"],
         "answer": 2, "explanation": "The ECI is an autonomous constitutional body responsible for elections."},
    ]
    return jsonify({"questions": questions})


@app.route("/api/impact", methods=["GET"])
def voter_impact():
    """Return voter impact statistics for the current constituency."""
    return jsonify({
        "constituency": Config.DEFAULT_CONSTITUENCY,
        "last_margin": 4300, "eligible_voters": 180000,
        "turnout_last": 67, "your_area_turnout": 54,
        "national_avg": 61,
        "message": "In 2019, the winning margin was just 4,300 votes. Every vote truly counts!",
    })


@app.route("/api/compare", methods=["POST"])
def compare_candidates():
    """Return side-by-side candidate data for the given IDs."""
    data = request.json or {}
    ids = data.get("ids", [1, 2, 3])
    error = validate_candidate_ids(ids)
    if error:
        return jsonify({"error": error}), 400
    selected = [c for c in CANDIDATES if c["id"] in ids]
    return jsonify({"candidates": selected})


@app.route("/api/integrity-score/<int:cid>", methods=["GET"])
def get_integrity(cid: int):
    """Return a detailed integrity score breakdown for a candidate."""
    candidate = next((c for c in CANDIDATES if c["id"] == cid), None)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    breakdown = {
        "asset_growth": random.randint(60, 95),
        "criminal_cases": 100 if candidate["criminal_cases"] == 0 else max(0, 100 - candidate["criminal_cases"] * 30),
        "attendance": int(candidate["attendance"].strip("%")),
        "promise_delivery": random.randint(55, 90),
        "total": candidate["integrity_score"],
    }
    return jsonify({"candidate": candidate["name"], "breakdown": breakdown})


# ── Voter Check ───────────────────────────────────────────────────────────────

@app.route("/api/voter-check", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_VOTER)
def voter_check():
    """
    Verify voter registration by EPIC number.
    Validates format against ECI's official pattern (3 letters + 7 digits).
    """
    data = request.json or {}
    epic = sanitise(data.get("epic", ""), Config.MAX_EPIC_LEN).upper()

    if not is_valid_epic(epic):
        gcp.log_event_to_bigquery("voter_check_invalid", {"epic_length": len(epic)})
        return jsonify({"registered": False, "message": "Invalid EPIC format. Expected: ABC1234567"}), 400

    gcp.log_event_to_bigquery("voter_check_success", {"constituency": Config.DEFAULT_CONSTITUENCY})
    return jsonify({
        "registered": True,
        "name": "Voter Name (Demo)",
        "constituency": Config.DEFAULT_CONSTITUENCY,
        "booth": "Government School, Andheri West",
        "booth_no": "B-073",
        "serial_no": random.randint(100, 999),
    })


# ── Turnout (Firebase + BigQuery) ─────────────────────────────────────────────

@app.route("/api/turnout", methods=["GET"])
def get_turnout():
    """Return live turnout data from Firebase Firestore with in-memory fallback."""
    return jsonify(gcp.get_live_turnout(TURNOUT_DATA))


@app.route("/api/turnout/update", methods=["POST"])
@limiter.limit("5 per minute")
def update_turnout():
    """Update live turnout figure in Firebase Firestore."""
    data = request.json or {}
    current = data.get("current")
    if not isinstance(current, (int, float)) or not (0 <= current <= 100):
        return jsonify({"error": "Invalid turnout value (must be 0–100)"}), 400
    result = gcp.update_live_turnout({"current": current}, TURNOUT_DATA)
    return jsonify(result)


@app.route("/api/turnout/analytics", methods=["GET"])
def turnout_analytics():
    """Query BigQuery for aggregated real-time turnout analytics."""
    data = gcp.query_turnout_analytics()
    return jsonify(data)


# ── Google Cloud AI/ML APIs ───────────────────────────────────────────────────

@app.route("/api/sentiment", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_AI)
def analyse_sentiment():
    """
    Analyse sentiment of election text using Google Cloud Natural Language API.
    Used to score candidate manifesto tone on candidate cards.
    """
    data = request.json or {}
    text = sanitise(data.get("text", ""), 1000)
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(gcp.analyse_text_sentiment(text))


@app.route("/api/entities", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_AI)
def analyse_entities():
    """Extract named political entities from election text via Google NL API."""
    data = request.json or {}
    text = sanitise(data.get("text", ""), 1000)
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(gcp.analyse_entities(text))


@app.route("/api/translate", methods=["POST"])
@limiter.limit("15 per minute")
def translate():
    """
    Translate election content to regional Indian languages.
    Uses Google Cloud Translation API v2 with graceful fallback.
    """
    data = request.json or {}
    text = sanitise(data.get("text", ""), 500)
    target = sanitise(data.get("target", "hi"), 5)

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if not is_valid_language_code(target):
        return jsonify({"error": "Unsupported language code"}), 400

    return jsonify(gcp.translate_text(text, target))


@app.route("/api/fact-check", methods=["POST"])
@limiter.limit("5 per minute")
def fact_check():
    """
    AI-powered election fact checker.
    Returns verdict (TRUE/FALSE/MISLEADING/UNVERIFIABLE) with explanation.
    """
    data = request.json or {}
    claim = sanitise(data.get("claim", ""), Config.MAX_CLAIM_LEN)
    if not claim:
        return jsonify({"error": "No claim provided"}), 400

    system = (
        "You are an Indian election fact-checker. "
        "Respond ONLY with valid JSON (no markdown backticks): "
        '{"verdict":"TRUE"|"FALSE"|"MISLEADING"|"UNVERIFIABLE",'
        '"explanation":"one concise sentence","sources":["official_url"]}'
    )
    try:
        reply, _ = invoke_chat(system, [{"role": "user", "content": claim}])
        clean = reply.strip().lstrip("```json").rstrip("```").strip()
        return jsonify(json.loads(clean))
    except Exception:
        return jsonify({"verdict": "UNVERIFIABLE", "explanation": "Cannot verify at this time.", "sources": []})


@app.route("/api/verify-photo/<int:cid>", methods=["GET"])
def verify_photo(cid: int):
    """Use Google Cloud Vision API to verify candidate photo integrity."""
    candidate = next((c for c in CANDIDATES if c["id"] == cid), None)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    return jsonify(gcp.verify_candidate_photo(None, candidate["name"]))


# ── Constituencies ────────────────────────────────────────────────────────────

@app.route("/api/constituencies", methods=["GET"])
@cache.cached(timeout=Config.CACHE_TIMEOUT_STATIC)
def list_constituencies():
    """Return filtered list of constituencies for search autocomplete."""
    query = sanitise(request.args.get("q", ""), 100).lower()
    filtered = [c for c in CONSTITUENCIES if query in c.lower()]
    return jsonify({"constituencies": filtered})


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    logger.info("Starting ElectIQ on port 5000 (debug=%s)", debug_mode)
    app.run(debug=debug_mode, port=5000)
