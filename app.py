import streamlit as st
import requests
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

st.set_page_config(
    page_title="Novel Movie AI",
    page_icon="🎬",
    layout="wide"
)

# ============================================================
# CONFIG
# ============================================================

DATA = Path("movie_data")
DATA.mkdir(exist_ok=True)

# Streamlit Secrets / environment
GEMINI_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY", "")
)

VIDEO_API_URL = st.secrets.get(
    "VIDEO_API_URL",
    os.getenv("VIDEO_API_URL", "")
)

LIPSYNC_API_URL = st.secrets.get(
    "LIPSYNC_API_URL",
    os.getenv("LIPSYNC_API_URL", "")
)


# ============================================================
# STORY AI
# ============================================================

def split_story(text, max_chars=7000):
    text = text.strip()

    if len(text) <= max_chars:
        return [text]

    parts = re.split(r"(?<=[။.!?])\s+", text)

    result = []
    current = ""

    for p in parts:
        if len(current) + len(p) > max_chars:
            if current:
                result.append(current)
            current = p
        else:
            current += " " + p

    if current:
        result.append(current)

    return result


def ask_gemini(novel, max_scenes):

    if not GEMINI_KEY:
        return None

    prompt = f"""
You are a professional film director and screenplay writer.

Read this complete novel carefully.

Turn it into a cinematic movie plan.

Requirements:
- Understand the story
- Preserve the original plot
- Identify recurring characters
- Keep characters visually consistent
- Create natural dialogue
- Create actions
- Create emotions
- Create locations
- Create camera movement
- Create cinematic visual prompts
- Keep scene order logical

Maximum scenes: {max_scenes}

Return ONLY JSON:

{{
"title":"",
"characters":[
  {{
    "id":"",
    "name":"",
    "appearance":"",
    "personality":"",
    "voice":"my-MM-ThihaNeural"
  }}
],
"scenes":[
  {{
    "id":1,
    "title":"",
    "summary":"",
    "location":"",
    "time":"",
    "characters":[],
    "emotion":"",
    "action":"",
    "camera":"",
    "visual_prompt":"",
    "dialogue":[
      {{
        "character":"",
        "text":""
      }}
    ]
  }}
]
}}

NOVEL:
{novel}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
        "?key=" + GEMINI_KEY
    )

    try:

        r = requests.post(
            url,
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            },
            timeout=180
        )

        r.raise_for_status()

        data = r.json()

        text = (
            data["candidates"][0]
            ["content"]["parts"][0]
            ["text"]
        )

        return json.loads(text)

    except Exception as e:

        st.warning(
            "Gemini မရသေးပါ။ Offline story planner သုံးနေပါတယ်."
        )

        return None


# ============================================================
# OFFLINE STORY PLANNER
# ============================================================

def offline_plan(novel, max_scenes):

    chunks = split_story(novel)

    chunks = chunks[:max_scenes]

    scenes = []

    for i, text in enumerate(chunks, 1
