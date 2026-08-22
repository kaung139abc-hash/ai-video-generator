import os
import re
import json
import sqlite3
import time
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Novel 3D Movie AI",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# SETTINGS
# ============================================================

DATA_DIR = Path("movie_data")
DATA_DIR.mkdir(exist_ok=True)

DB_FILE = DATA_DIR / "jobs.db"


def secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        return value or os.getenv(name, default)
    except Exception:
        return os.getenv(name, default)


GEMINI_API_KEY = secret("GEMINI_API_KEY")
VIDEO_WORKER_URL = secret(
    "VIDEO_WORKER_URL"
).rstrip("/")


# ============================================================
# DATABASE
# ============================================================

def get_db():

    con = sqlite3.connect(
        DB_FILE
    )

    con.row_factory = sqlite3.Row

    con.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT,
            prompt TEXT,
            video_url TEXT,
            error TEXT,
            created REAL,
            updated REAL
        )
    """)

    con.commit()

    return con


# ============================================================
# JSON CLEAN
# ============================================================

def clean_json(text):

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


# ============================================================
# GEMINI STORY PLAN
# ============================================================

def generate_story_plan(
    novel,
    max_scenes
):

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY မရှိပါ။"
        )

    prompt = f"""
You are a professional cinematic
3D animated movie director.

Convert the following Burmese novel
into a complete movie plan.

Requirements:

1. Preserve the story.
2. Identify recurring characters.
3. Keep character appearance consistent.
4. Divide the story into cinematic scenes.
5. Create Burmese dialogue.
6. Describe action and emotion.
7. Describe camera movement.
8. Create detailed 3D animation prompts.
9. Keep locations consistent.
10. Maximum scenes: {max_scenes}

Return ONLY valid JSON.

FORMAT:

{{
  "title": "Movie title",

  "characters": [
    {{
      "id": "c1",
      "name": "Character",
      "appearance": "Detailed appearance",
      "clothing": "Clothing",
      "personality": "Personality"
    }}
  ],

  "scenes": [
    {{
      "id": 1,
      "title": "Scene title",
      "location": "Location",
      "time": "Time",
      "characters": ["c1"],
      "action": "Action",
      "emotion": "Emotion",
      "camera": "Camera movement
