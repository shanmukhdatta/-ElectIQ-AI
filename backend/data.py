"""
ElectIQ — Static Election Data
In production, replace with live database queries via BigQuery.
"""
from typing import Any


CANDIDATES: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Aarav Mehta",
        "party": "Progressive Alliance",
        "party_color": "#2563eb",
        "constituency": "Mumbai North",
        "photo": "👨💼",
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
            "infrastructure": "Metro expansion to all major suburbs",
        },
    },
    {
        "id": 2,
        "name": "Priya Sharma",
        "party": "National Unity Front",
        "party_color": "#dc2626",
        "constituency": "Mumbai North",
        "photo": "👩💼",
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
            "infrastructure": "Highway expansion and rural connectivity",
        },
    },
    {
        "id": 3,
        "name": "Rajesh Kumar",
        "party": "Peoples Democratic Party",
        "party_color": "#16a34a",
        "constituency": "Mumbai North",
        "photo": "🧑💼",
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
            "infrastructure": "Rural roads under PM Gram Sadak Yojana 2.0",
        },
    },
]

ELECTION_TIMELINE: list[dict[str, str]] = [
    {"event": "Voter Registration Opens", "date": "2026-04-01", "status": "completed"},
    {"event": "Voter Registration Closes", "date": "2026-04-20", "status": "completed"},
    {"event": "Candidate Nomination", "date": "2026-04-25", "status": "completed"},
    {"event": "Campaign Period", "date": "2026-05-01", "status": "upcoming"},
    {"event": "Polling Day", "date": "2026-05-15", "status": "upcoming"},
    {"event": "Result Declaration", "date": "2026-05-18", "status": "upcoming"},
]

TURNOUT_DATA: dict[str, Any] = {
    "current": 34,
    "last_election": 67,
    "national_avg": 61,
    "constituency": "Mumbai North",
    "hours": [
        {"hour": "7AM",  "turnout": 8},
        {"hour": "9AM",  "turnout": 18},
        {"hour": "11AM", "turnout": 28},
        {"hour": "1PM",  "turnout": 34},
        {"hour": "3PM",  "turnout": None},
        {"hour": "5PM",  "turnout": None},
        {"hour": "6PM",  "turnout": None},
    ],
}

BOOTHS: list[dict[str, Any]] = [
    {"id": 1, "name": "Government School, Andheri West",     "ward": "Ward 71",
     "officer": "Smt. Lalitha Devi",   "queue": "Short (5-10 min)",    "accessibility": True,  "lat": 19.1136, "lng": 72.8697},
    {"id": 2, "name": "Municipal Corporation Hall, Versova", "ward": "Ward 72",
     "officer": "Shri. Ramesh Patil",  "queue": "Moderate (15-20 min)","accessibility": True,  "lat": 19.1217, "lng": 72.8120},
    {"id": 3, "name": "Community Centre, Lokhandwala",       "ward": "Ward 73",
     "officer": "Smt. Kavita Singh",   "queue": "Long (30+ min)",       "accessibility": False, "lat": 19.1353, "lng": 72.8345},
]

HISTORY_DATA: list[dict[str, Any]] = [
    {"year": 2014, "winner": "BJP",      "margin": 12000, "turnout": 58},
    {"year": 2019, "winner": "Congress", "margin": 4300,  "turnout": 63},
    {"year": 2024, "winner": "BJP",      "margin": 8900,  "turnout": 67},
]

CONSTITUENCIES: list[str] = [
    "Mumbai North", "Delhi Central", "Bangalore South", "Chennai North",
    "Kolkata East", "Hyderabad", "Pune", "Jaipur", "Lucknow",
    "Patna Sahib", "Bhopal", "Ahmedabad East", "Surat", "Nagpur",
]
