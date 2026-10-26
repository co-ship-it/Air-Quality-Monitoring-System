"""
health_advice.py
================
Personalised, GENERAL health guidance based on the AQI category and the
user's health profile (for example "Asthma or lung disease").

Simple idea used:
    1. Each AQI category has a "risk level" from 0 to 3.
    2. Sensitive people (children, older adults, people with lung or heart
       disease, pregnant women) are advised one level more cautiously.
    3. The risk level decides the tips and the activity guide.

This is general information based on the CPCB category descriptions,
not medical advice.
"""

from __future__ import annotations

import pandas as pd

PROFILES = {
    "general": "General public",
    "sensitive": "Children or older adults",
    "lung": "Asthma or lung disease",
    "heart": "Heart disease",
    "pregnant": "Pregnant",
    "active": "Outdoor worker or athlete",
}

SENSITIVE_PROFILES = {"sensitive", "lung", "heart", "pregnant"}

# AQI category -> base risk level (0 = low ... 3 = very high)
CATEGORY_RISK = {
    "Good": 0, "Satisfactory": 0, "Moderate": 1,
    "Poor": 2, "Very Poor": 3, "Severe": 3,
}

RISK_LABELS = ["Low", "Moderate", "High", "Very high"]

# Extra tips for each profile at each risk level
PROFILE_TIPS = {
    "general": [
        ["Enjoy outdoor activities."],
        ["Normal activities are fine; take breaks during long outdoor exercise."],
        ["Shorten long or intense outdoor activities.", "Prefer indoor exercise today."],
        ["Avoid outdoor exercise.", "Wear an N95/FFP2 mask if you must go out.",
         "Keep windows closed and use an air purifier if you have one."],
    ],
    "sensitive": [
        ["Outdoor play and walks are fine."],
        ["Limit long, tiring outdoor activity.", "Watch for coughing or tiredness."],
        ["Keep children and older adults indoors as much as possible.",
         "Move school or park activities indoors."],
        ["Stay indoors.", "Avoid all outdoor physical activity.",
         "Seek medical help for breathing difficulty."],
    ],
    "lung": [
        ["Keep your reliever inhaler with you as usual."],
        ["Carry your inhaler.", "Reduce heavy outdoor exercise."],
        ["Stay indoors as much as possible.", "Follow your asthma action plan.",
         "Wear a well-fitted mask outdoors."],
        ["Stay indoors with windows closed.", "Contact your doctor if symptoms get worse.",
         "Do not exercise outdoors."],
    ],
    "heart": [
        ["Normal activity is fine."],
        ["Avoid strenuous outdoor activity."],
        ["Stay indoors as much as possible.", "Avoid exertion outdoors.",
         "Watch for chest pain, palpitations or unusual tiredness."],
        ["Stay indoors and rest.", "Seek medical help immediately for chest pain "
         "or breathlessness."],
    ],
    "pregnant": [
        ["Normal activity is fine."],
        ["Limit long outdoor exposure, especially near busy roads."],
        ["Stay indoors as much as possible.", "Wear a well-fitted mask outdoors."],
        ["Stay indoors with windows closed.", "Consult your doctor if you feel unwell."],
    ],
    "active": [
        ["A great day for outdoor training or work."],
        ["Take regular breaks; reduce very intense training outdoors."],
        ["Move training indoors.", "Outdoor workers: wear an N95/FFP2 mask and take "
         "frequent breaks."],
        ["Postpone outdoor training.", "Outdoor workers: wear an N95/FFP2 mask and limit "
         "hours outside if possible."],
    ],
}

# Activity guide: recommendation at each risk level (0-3)
ACTIVITIES = {
    "Walking outdoors":         ["OK", "OK", "Limit", "Avoid"],
    "Running or outdoor sports": ["OK", "Limit", "Avoid", "Avoid"],
    "Children playing outside":  ["OK", "Limit", "Avoid", "Avoid"],
    "Cycling or walking commute": ["OK", "OK", "Limit", "Avoid"],
    "Opening windows":           ["OK", "OK", "Limit", "Avoid"],
}

STATUS_TEXT = {"OK": "✅ OK", "Limit": "⚠️ Limit", "Avoid": "⛔ Avoid"}


def risk_level(category_name: str, profile: str = "general") -> int:
    """Risk level 0-3 for this category; one level higher for sensitive profiles."""
    level = CATEGORY_RISK.get(category_name, 0)
    if profile in SENSITIVE_PROFILES and category_name != "Good":
        level += 1
    return min(level, 3)


def personal_tips(category_name: str, profile: str = "general") -> list[str]:
    tips = PROFILE_TIPS.get(profile, PROFILE_TIPS["general"])
    return tips[risk_level(category_name, profile)]


def all_tips(category: dict, profile: str = "general") -> list[str]:
    """CPCB category advice + profile tips, without repeating the same advice."""
    tips = list(category["advice"])
    if profile != "general":                   # general advice is already in the list
        tips += [t for t in personal_tips(category["name"], profile) if t not in tips]
    return tips


def activity_guide(category_name: str, profile: str = "general") -> pd.DataFrame:
    """Table of everyday activities with OK / Limit / Avoid for this AQI category."""
    level = risk_level(category_name, profile)
    return pd.DataFrame({
        "Activity": list(ACTIVITIES.keys()),
        "Recommendation": [STATUS_TEXT[values[level]] for values in ACTIVITIES.values()],
    })
