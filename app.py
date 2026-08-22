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
# GEMINI
# ============================================================

def generate_story_plan(novel, max_scenes):

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY မတွေ့ပါ။"
        )

    prompt = f"""
You are a professional 3D animated movie director.

Convert this Burmese novel into a cinematic movie plan.

Create:
- consistent characters
- detailed scenes
- actions
- emotions
- camera movements
- Burmese dialogue
- detailed 3D visual prompts

Maximum scenes: {max_scenes}

Return ONLY valid JSON.

FORMAT:

{{
  "title": "Movie title",

  "characters": [
    {{
      "id": "c1",
      "name": "Character name",
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
      "action": "Detailed action",
      "emotion": "Emotion",
      "camera": "Cinematic camera movement",
      "visual_prompt": "Detailed 3D movie prompt",

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
            f"Gemini API Error {response.status_code}: "
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
# CHARACTER CONTEXT
# ============================================================

def character_context(scene, characters):

    character_map = {
        str(c.get("id")): c
        for c in characters
        if isinstance(c, dict)
    }

    result = []

    for character_id in scene.get(
        "characters",
        []
    ):

        character = character_map.get(
            str(character_id)
        )

        if character:

            result.append(
                f"""
Name: {character.get("name", "")}
Appearance: {character.get("appearance", "")}
Clothing: {character.get("clothing", "")}
Personality: {character.get("personality", "")}
"""
            )

    return "\n".join(result)


# ============================================================
# VIDEO PROMPT
# ============================================================

def build_video_prompt(scene, characters):

    chars = character_context(
        scene,
        characters
    )

    return f"""
High quality cinematic 3D animated
feature film scene.

Location:
{scene.get("location", "")}

Time:
{scene.get("time", "")}

Action:
{scene.get("action", "")}

Emotion:
{scene.get("emotion", "")}

Camera:
{scene.get("camera", "")}

Characters:
{chars}

Visual:
{scene.get("visual_prompt", "")}

Style:
high quality 3D feature animation,
cinematic movie quality,
detailed faces,
natural anatomy,
natural movement,
consistent character appearance,
consistent clothing,
detailed environment,
cinematic lighting,
realistic shadows,
depth of field,
smooth camera movement,
sharp focus,
high detail.

Negative:
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
# CREATE VIDEO JOB
# ============================================================

def create_video_job(prompt, seconds):

    if not VIDEO_WORKER_URL:
        raise RuntimeError(
            "VIDEO_WORKER_URL မရှိပါ။"
        )

    job_id = str(
        int(time.time() * 1000)
    )

    con = get_db()

    con.execute(
        """
        INSERT INTO jobs
        (
            id,
            status,
            prompt,
            video_url,
            error,
            created,
            updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            "queued",
            prompt,
            "",
            "",
            time.time(),
            time.time()
        )
    )

    con.commit()
    con.close()

    response = requests.post(
        VIDEO_WORKER_URL + "/generate",
        json={
            "job_id": job_id,
            "prompt": prompt,
            "seconds": seconds
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Video Worker Error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    return job_id


# ============================================================
# JOB STATUS
# ============================================================

def get_job_status(job_id):

    try:

        if VIDEO_WORKER_URL:

            response = requests.get(
                VIDEO_WORKER_URL
                + f"/jobs/{job_id}",
                timeout=20
            )

            if response.ok:
                return response.json()

    except Exception:
        pass

    con = get_db()

    row = con.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    con.close()

    if row:
        return dict(row)

    return None


# ============================================================
# UI
# ============================================================

st.title("🎬 Novel 3D Movie AI")

st.caption(
    "📖 Novel → 🧠 Gemini → 🎭 Scenes → "
    "🎨 T4 GPU → 🗣️ ElevenLabs → 🎞️ MP4"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Movie Settings")

    max_scenes = st.slider(
        "Maximum Scenes",
        1,
        20,
        4
    )

    seconds = st.slider(
        "Seconds / Scene",
        3,
        8,
        5
    )

    st.divider()

    st.write(
        "Gemini:",
        "✅ READY" if GEMINI_API_KEY else "❌ MISSING"
    )

    st.write(
        "ElevenLabs:",
        "✅ READY" if ELEVENLABS_API_KEY else "⚠️ MISSING"
    )

    st.write(
        "T4 Worker:",
        "✅ READY" if VIDEO_WORKER_URL else "❌ MISSING"
    )


# ============================================================
# NOVEL INPUT
# ============================================================

novel = st.text_area(
    "📖 ဝတ္ထုထည့်ပါ",
    height=300,
    placeholder="""
သမန်းဝံပုလွေ ဇာတ်လမ်း...
"""
)


# ============================================================
# GENERATE STORY
# ============================================================

if st.button(
    "🧠 Generate Movie Story",
    type="primary",
    use_container_width=True
):

    if not novel.strip():

        st.warning(
            "ဝတ္ထုထည့်ပါ။"
        )

    else:

        try:

            with st.spinner(
                "Gemini က ဇာတ်လမ်းခွဲနေပါတယ်..."
            ):

                plan = generate_story_plan(
                    novel,
                    max_scenes
                )

                st.session_state.movie_plan = plan

            st.success(
                "✅ Movie Story Ready"
            )

        except Exception as error:

            st.error(
                "❌ Gemini Error"
            )

            st.code(
                str(error)
            )


# ============================================================
# SHOW PLAN
# ============================================================

if "movie_plan" in st.session_state:

    plan = st.session_state.movie_plan

    title = plan.get(
        "title",
        "Novel 3D Movie"
    )

    characters = plan.get(
        "characters",
        []
    )

    scenes = plan.get(
        "scenes",
        []
    )

    st.divider()

    st.header(
        "🎬 " + str(title)
    )


    # ========================================================
    # CHARACTERS
    # ========================================================

    with st.expander(
        "🎭 Characters",
        expanded=True
    ):

        for character in characters:

            st.markdown(
                f"### {character.get('name', 'Character')}"
            )

            st.write(
                "Appearance:",
                character.get(
                    "appearance",
                    ""
                )
            )

            st.write(
                "Clothing:",
                character.get(
                    "clothing",
                    ""
                )
            )

            st.write(
                "Personality:",
                character.get(
                    "personality",
                    ""
                )
            )


    # ========================================================
    # SCENES
    # ========================================================

    st.subheader(
        "🎞️ Movie Scenes"
    )

    for scene in scenes:

        scene_id = scene.get(
            "id",
            ""
        )

        scene_title = scene.get(
            "title",
            ""
        )

        with st.expander(
            f"Scene {scene_id} — {scene_title}"
        ):

            st.write(
                "Location:",
                scene.get(
                    "location",
                    ""
                )
            )

            st.write(
                "Action:",
                scene.get(
                    "action",
                    ""
                )
            )

            st.write(
                "Emotion:",
                scene.get(
                    "emotion",
                    ""
                )
            )

            st.write(
                "Camera:",
                scene.get(
                    "camera",
                    ""
                )
            )

            st.markdown(
                "#### 🎨 Video Prompt"
            )

            st.code(
                build_video_prompt(
                    scene,
                    characters
                ),
                language="text"
            )

            dialogue = scene.get(
                "dialogue",
                []
            )

            if dialogue:

                st.markdown(
                    "#### 🗣️ Dialogue"
                )

                for line in dialogue:

                    st.write(
                        f"**{line.get('character', '')}:** "
                        f"{line.get('text', '')}"
                    )


    # ========================================================
    # GENERATE VIDEO
    # ========================================================

    st.divider()

    if VIDEO_WORKER_URL:

        if st.button(
            "🎬 Generate Full Movie",
            type="primary",
            use_container_width=True
        ):

            job_ids = []

            total = len(scenes)

            if total == 0:

                st.error(
                    "Scene မရှိပါ။"
                )

            else:

                progress = st.progress(0)

                for index, scene in enumerate(
                    scenes,
                    start=1
                ):

                    try:

                        prompt = build_video_prompt(
                            scene,
                            characters
                        )

                        job_id = create_video_job(
                            prompt,
                           
