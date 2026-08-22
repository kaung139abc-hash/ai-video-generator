import os
import re
import json
import sqlite3
import time
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Novel 3D Movie AI",
    page_icon="🎬",
    layout="wide"
)

DATA_DIR = Path("movie_data")
DATA_DIR.mkdir(exist_ok=True)

DB_FILE = DATA_DIR / "jobs.db"


# ============================================================
# SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
ELEVENLABS_API_KEY = get_secret("ELEVENLABS_API_KEY")
VIDEO_WORKER_URL = get_secret("VIDEO_WORKER_URL").rstrip("/")


# ============================================================
# DATABASE
# ============================================================

def get_db():

    con = sqlite3.connect(DB_FILE)
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
# CLEAN GEMINI JSON
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
# GEMINI STORY GENERATOR
# ============================================================

def generate_story_plan(novel, max_scenes):

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY မတွေ့ပါ။ "
            "Streamlit Secrets ထဲမှာ ထည့်ပါ။"
        )

    prompt = f"""
You are a professional cinematic 3D animated movie director.

Convert the following Burmese novel into a complete
3D animated movie plan.

Requirements:

- Keep the original story meaning.
- Create consistent characters.
- Keep character appearance consistent between scenes.
- Divide the story into cinematic scenes.
- Add action and emotion.
- Add camera movement.
- Add Burmese dialogue.
- Create detailed visual prompts.
- Maximum scenes: {max_scenes}.

Return ONLY valid JSON.

FORMAT:

{{
  "title": "Movie title",

  "characters": [
    {{
      "id": "c1",
      "name": "Character name",
      "appearance": "Detailed physical appearance",
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
      "action": "Detailed action",
      "emotion": "Emotion",
      "camera": "Cinematic camera movement",
      "visual_prompt": "Detailed cinematic 3D prompt",

      "dialogue": [
        {{
          "character": "c1",
          "text": "Burmese dialogue"
        }}
      ]
    }}
  ]
}}

NOVEL:

{novel}
"""

    # ========================================================
    # CURRENT GEMINI MODEL
    # ========================================================

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    response = requests.post(
        url,
        params={
            "key": GEMINI_API_KEY
        },
        headers={
            "Content-Type": "application/json"
        },
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        },
        timeout=180
    )

    if not response.ok:

        raise RuntimeError(
            f"Gemini API Error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    text = (
        data["candidates"][0]
        ["content"]["parts"][0]
        ["text"]
    )

    return json.loads(
        clean_json(text)
    )


# ============================================================
# CHARACTER CONSISTENCY
# ============================================================

def character_context(
    scene,
    characters
):

    character_map = {
        str(c.get("id")): c
        for c in characters
        if isinstance(c, dict)
    }

    lines = []

    for character_id in scene.get(
        "characters",
        []
    ):

        character = character_map.get(
            str(character_id)
        )

        if character:

            lines.append(
                f"""
Name:
{character.get("name", "")}

Appearance:
{character.get("appearance", "")}

Clothing:
{character.get("clothing", "")}

Personality:
{character.get("personality", "")}
"""
            )

    return "\n".join(lines)


# ============================================================
# VIDEO PROMPT
# ============================================================

def build_video_prompt(
    scene,
    characters
):

    characters_text = character_context(
        scene,
        characters
    )

    return f"""
High quality cinematic 3D animated
feature film scene.

LOCATION:
{scene.get("location", "")}

TIME:
{scene.get("time", "")}

ACTION:
{scene.get("action", "")}

EMOTION:
{scene.get("emotion", "")}

CAMERA:
{scene.get("camera", "")}

CHARACTERS:
{characters_text}

VISUAL:
{scene.get("visual_prompt", "")}

STYLE:

High quality 3D feature animation,
cinematic movie quality,
detailed realistic 3D characters,
sharp facial details,
natural anatomy,
natural movement,
consistent character design,
consistent clothing,
detailed environment,
cinematic lighting,
realistic shadows,
depth of field,
smooth camera movement,
sharp focus,
high detail,
professional film composition.

NEGATIVE:

blurry,
low resolution,
painting,
watercolor,
sketch,
deformed face,
bad anatomy,
extra fingers,
extra limbs,
duplicate characters,
text,
subtitles,
logo,
watermark.
""".strip()


# ============================================================
# VIDEO WORKER
# ============================================================

def create_video_job(
    prompt,
   
