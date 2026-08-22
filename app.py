import os
import re
import json
import sqlite3
import time
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="Novel 3D Movie AI",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# DIRECTORIES
# ============================================================

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

VIDEO_WORKER_URL = get_secret(
    "VIDEO_WORKER_URL"
).rstrip("/")


# ============================================================
# DATABASE
# ============================================================

def get_db():

    con = sqlite3.connect(DB_FILE)

    con.row_factory = sqlite3.Row

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT,
            prompt TEXT,
            video_url TEXT,
            error TEXT,
            created REAL,
            updated REAL
        )
        """
    )

    con.commit()

    return con


# ============================================================
# JSON CLEANER
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
            "GEMINI_API_KEY မရှိပါ။ "
            "Streamlit Secrets ထဲထည့်ပါ။"
        )

    prompt = f"""
You are a professional cinematic 3D animated movie director.

Convert the following Burmese novel into a complete
cinematic 3D animated movie plan.

IMPORTANT:

1. Keep the story meaning.
2. Create consistent recurring characters.
3. Keep character appearance consistent.
4. Divide the story into cinematic scenes.
5. Add action and emotion.
6. Add camera movement.
7. Add Burmese dialogue.
8. Create detailed 3D visual prompts.
9. Keep locations visually consistent.
10. Maximum scenes: {max_scenes}

Return ONLY valid JSON.

JSON FORMAT:

{{
  "title": "Movie title",

  "characters": [
    {{
      "id": "c1",
      "name": "Character name",
      "appearance": "Detailed physical appearance",
      "clothing": "Clothing description",
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

      "camera": "Professional cinematic camera movement",

      "visual_prompt": "Detailed cinematic 3D animation prompt",

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
        "v1beta/models/gemini-2.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    response = requests.post(
        url,
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        },
        timeout=180
    )

    response.raise_for_status()

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

def character_context(scene, characters):

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
Character:
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

    character_info = character_context(
        scene,
        characters
    )

    prompt = f"""
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
{character_info}

VISUAL DIRECTION:
{scene.get("visual_prompt", "")}

STYLE:

High quality polished 3D animation,
cinematic feature film quality,
realistic detailed 3D characters,
sharp facial details,
natural anatomy,
natural body movement,
consistent character design,
consistent clothing,
detailed environment,
cinematic lighting,
soft realistic shadows,
depth of field,
professional movie camera,
smooth camera movement,
sharp focus,
high detail,
film-quality composition.

AVOID:

blurry image,
painting style,
watercolor style,
sketch,
low resolution,
deformed face,
extra fingers,
extra limbs,
duplicate characters,
text,
subtitles,
logo,
watermark.
"""

    return prompt.strip()


# ============================================================
# CREATE VIDEO JOB
# ============================================================

def create_video_job(
    prompt,
    seconds
):

    if not VIDEO_WORKER_URL:

        raise RuntimeError(
            "VIDEO_WORKER_URL မရှိပါ။ "
            "Streamlit Secrets ကိုစစ်ပါ။"
        )

    job_id = str(
        int(time.time() * 1000)
    )

    con = get_db()

    con.execute(
        """
        INSERT INTO jobs
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

    response.raise_for_status()

    return job_id


# ============================================================
# CHECK VIDEO JOB
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

st.title(
    "🎬 Novel 3D Movie AI"
)

st.caption(
    "Novel → Story → Characters → Scenes → GPU Worker → MP4"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Movie Settings"
    )

    max_scenes = st.slider(
        "Maximum Scenes",
        min_value=1,
        max_value=20,
        value=4
    )

    seconds = st.slider(
        "Seconds / Scene",
        min_value=3,
        max_value=8,
        value=5
    )

    st.divider()

    if GEMINI_API_KEY:
        st.success(
            "Gemini API: READY"
        )
    else:
        st.error(
            "Gemini API: MISSING"
        )

    if VIDEO_WORKER_URL:
        st.success(
            "GPU Worker: READY"
        )
    else:
        st.error(
            "GPU Worker: MISSING"
        )


# ============================================================
# NOVEL INPUT
# ============================================================

novel = st.text_area(
    "📖 ဝတ္ထုထည့်ပါ",

    height=300,

    placeholder="""
ဥပမာ -

တောင်တန်းများဝန်းရံထားသော
ရွာငယ်လေးတစ်ရွာတွင်
သမန်းဝံပုလွေတစ်ကောင်
နေထိုင်နေခဲ့သည်...
"""
)


# ============================================================
# CREATE MOVIE PLAN
# ============================================================

if st.button(
    "🧠 Create Movie Plan",
    type="primary",
    use_container_width=True
):

    if not novel.strip():

        st.warning(
            "အရင်ဆုံး ဝတ္ထုထည့်ပါ။"
        )

    else:

        try:

            with st.spinner(
                "AI က Movie Plan ပြုလုပ်နေပါတယ်..."
            ):

                movie_plan = generate_story_plan(
                    novel,
                    max_scenes
                )

                st.session_state.movie_plan = (
                    movie_plan
                )

            st.success(
                "✅ Movie Plan Ready"
            )

        except Exception as error:

            st.error(
                "❌ Story Generation Error"
            )

            st.code(
                str(error)
            )


# ============================================================
# SHOW MOVIE PLAN
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
                "**Appearance:**",
                character.get(
                    "appearance",
                    ""
                )
            )

            st.write(
                "**Clothing:**",
                character.get(
                    "clothing",
                    ""
                )
            )

            st.write(
                "**Personality:**",
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
                "**Location:**",
                scene.get(
                    "location",
                    ""
                )
            )

            st.write(
                "**Time:**",
                scene.get(
                    "time",
                    ""
                )
            )

            st.write(
                "**Action:**",
                scene.get(
                    "action",
                    ""
                )
            )

            st.write(
                "**Emotion:**",
                scene.get(
                    "emotion",
                    ""
                )
            )

            st.write(
                "**Camera:**",
                scene.get(
                    "camera",
                    ""
                )
            )


            st.markdown(
                "#### 🎨 Video Prompt"
            )

            video_prompt = build_video_prompt(
                scene,
                characters
            )

            st.code(
                video_prompt,
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

                    character_name = line.get(
                        "character",
                        ""
                    )

                    text = line.get(
                        "text",
                        ""
                    )

                    st.write(
                        f"**{character_name}:** {text}"
                    )


    # ========================================================
    # VIDEO GENERATION
    # ========================================================

    st.divider()

    if not VIDEO_WORKER_URL:

        st.warning(
            "⚠️ GPU Worker URL မထည့်ရသေးပါ။"
        )

    else:

        if st.button(
            "🎬 Queue Full Movie",
            type="primary",
            use_container_width=True
        ):

            job_ids = []

            progress = st.progress(
                0
            )

            total = len(scenes)

            if total == 0:

                st.error(
                    "Scene မရှိပါ။"
                )

            else:

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
                            seconds
                        )

                        job_ids.append(
                            job_id
                        )

                    except Exception as error:

                        st.error(
                            f"Scene {index} Error: {error}"
                        )

                    progress.progress(
                        index / total
                    )


                st.session_state.job_ids = (
                    job_ids
                )

                st.success(
                    f"✅ {len(job_ids)} scenes queued"
                )


# ============================================================
# JOB STATUS
# ============================================================

if st.session_state.get(
    "job_ids"
):

    st.divider()

    st.subheader(
        "📋 Video Jobs"
    )


    for job_id in st.session_state.job_ids:

        status = get_job_status(
            job_id
        )

        if not status:
            continue


        state = status.get(
            "status",
            "unknown"
        )


        if state == "done":

            st.success(
                f"{job_id} — ✅ DONE"
            )

            video_url = status.get(
                "video_url",
                ""
            )

            if video_url:

                if video_url.startswith(
                    "http"
                ):

                    full_url = video_url

                else:

                    full_url = (
                        VIDEO_WORKER_URL
                        + video_url
                    )

                st.video(
                    full_url
                )


        elif state == "failed":

            st.error(
                f"{job_id} — ❌ FAILED"
            )

            st.error(
                status.get(
                    "error",
                    "Unknown error"
                )
            )


        elif state == "running":

            st.warning(
                f"{job_id} — 🎬 Generating..."
            )


        else:

            st.info(
                f"{job_id} — ⏳ {state}"
            )


    if st.button(
        "🔄 Refresh Video Status"
    ):

        st.rerun()
