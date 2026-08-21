import streamlit as st
import requests
import json
import os
import re
import tempfile
import subprocess
from pathlib import Path

st.set_page_config(
    page_title="Novel 3D Movie AI",
    page_icon="🎬",
    layout="wide"
)

# ============================================================
# SETTINGS
# ============================================================

APP_DIR = Path("movie_data")
APP_DIR.mkdir(exist_ok=True)

def secret(name, default=""):
    try:
        return st.secrets.get(name, default) or os.getenv(name, default)
    except Exception:
        return os.getenv(name, default)

GEMINI_KEY = secret("GEMINI_API_KEY")
VIDEO_API_URL = secret("VIDEO_API_URL")

# ============================================================
# STORY SPLIT
# ============================================================

def split_story(text, limit=6500):
    text = text.strip()

    if not text:
        return []

    if len(text) <= limit:
        return [text]

    pieces = re.split(r"(?<=[။.!?])\s+", text)

    result = []
    current = ""

    for piece in pieces:
        if len(current) + len(piece) > limit:
            if current:
                result.append(current)
            current = piece
        else:
            current += (" " if current else "") + piece

    if current:
        result.append(current)

    return result


# ============================================================
# GEMINI
# ============================================================

def analyze_story(novel, max_scenes):

    if not GEMINI_KEY:
        return None

    prompt = f"""
You are a professional movie director, screenplay writer,
character designer and storyboard artist.

Read the Burmese novel carefully.

Create a cinematic animated movie production plan.

IMPORTANT:
1. Understand the whole story.
2. Preserve the original plot.
3. Do not invent major events.
4. Identify recurring characters.
5. Keep each character visually consistent.
6. Describe age, gender, hair, clothes and appearance.
7. Divide the story into logical scenes.
8. Create natural Burmese dialogue.
9. Create character actions and emotions.
10. Create cinematic camera movement.
11. Create detailed 3D animation visual prompts.
12. Keep locations and time consistent.
13. Characters must look like the same characters
    in every scene.

Maximum scenes: {max_scenes}

Return ONLY valid JSON.

FORMAT:

{{
"title": "",
"style": "cinematic 3D animated film",
"characters": [
  {{
    "id": "c1",
    "name": "",
    "appearance": "",
    "personality": "",
    "clothing": "",
    "voice": "my-MM-ThihaNeural"
  }}
],
"scenes": [
  {{
    "id": 1,
    "title": "",
    "summary": "",
    "location": "",
    "time": "",
    "characters": ["c1"],
    "emotion": "",
    "action": "",
    "camera": "",
    "visual_prompt": "",
    "dialogue": [
      {{
        "character": "c1",
        "text": ""
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
        st.warning(f"Gemini error: {e}")
        return None


# ============================================================
# FALLBACK
# ============================================================

def fallback_plan(novel, max_scenes):

    chunks = split_story(novel)
    chunks = chunks[:int(max_scenes)]

    scenes = []

    for i, text in enumerate(chunks, 1):

        scenes.append({
            "id": i,
            "title": f"Scene {i}",
            "summary": text[:500],
            "location": "As described in the novel",
            "time": "As described in the novel",
            "characters": [],
            "emotion": "dramatic",
            "action": text,
            "camera": (
                "cinematic camera movement, "
                "medium shot, wide shot, "
                "slow tracking movement"
            ),
            "visual_prompt": (
                "cinematic 3D animated movie, "
                "high quality character animation, "
                "natural body movement, "
                "detailed environment, "
                "dramatic cinematic lighting, "
                "professional film camera, "
                + text[:1500]
            ),
            "dialogue": []
        })

    return {
        "title": "Novel 3D Movie",
        "style": "cinematic 3D animated film",
        "characters": [],
        "scenes": scenes
    }


# ============================================================
# TTS
# ============================================================

def make_voice(text):

    if not text.strip():
        return None

    try:
        import edge_tts
        import asyncio

        output = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )
        output.close()

        async def create():
            communication = edge_tts.Communicate(
                text,
                "my-MM-ThihaNeural"
            )
            await communication.save(output.name)

        asyncio.run(create())

        return output.name

    except Exception:
        return None


# ============================================================
# VIDEO API
#
# Expected API:
#
# POST VIDEO_API_URL
# {
#   "prompt": "...",
#   "seconds": 5
# }
#
# Response:
# {
#   "video_url": "https://..."
# }
# ============================================================

def generate_video(prompt, seconds):

    if not VIDEO_API_URL:
        return None, (
            "VIDEO_API_URL မထည့်ထားသေးပါ။ "
            "GPU video backend လိုပါတယ်။"
        )

    try:

        r = requests.post(
            VIDEO_API_URL,
            json={
                "prompt": prompt,
                "seconds": int(seconds)
            },
            timeout=1800
        )

        r.raise_for_status()

        data = r.json()

        video_url = data.get("video_url")

        if not video_url:
            return None, (
                "Video backend က video_url "
                "မပြန်ပါ။"
            )

        video = requests.get(
            video_url,
            timeout=1800
        )

        video.raise_for_status()

        output = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4"
        )

        output.write(video.content)
        output.close()

        return output.name, None

    except Exception as e:
        return None, str(e)


# ============================================================
# ADD VOICE TO VIDEO
# ============================================================

def add_voice(video, audio):

    if not audio:
        return video

    output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )
    output.close()

    try:

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", video,
                "-i", audio,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output.name
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return output.name

    except Exception:
        return video


# ============================================================
# CONCAT MP4
# ============================================================

def merge_videos(files):

    if not files:
        return None

    if len(files) == 1:
        return files[0]

    list_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".txt",
        mode="w"
    )

    for file in files:
        path = str(Path(file).resolve())
        list_file.write(
            "file '" +
            path.replace("'", "'\\''") +
            "'\n"
        )

    list_file.close()

    output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )
    output.close()

    try:

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file.name,
                "-c", "copy",
                output.name
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return output.name

    except Exception:
        return None


# ============================================================
# UI
# ============================================================

st.title("🎬 Novel → 3D Movie AI")

st.markdown(
    """
**ဝတ္ထုတစ်ပုဒ် → AI Story Understanding → Character Design
→ Scene → Dialogue → Myanmar Voice → 3D Animation Video → MP4**
"""
)

with st.sidebar:

    st.header("⚙️ Movie Settings")

    max_scenes = st.slider(
        "🎬 Scene အများဆုံး",
        1,
        30,
        8
    )

    seconds = st.slider(
        "⏱️ Scene ကြာချိန်",
        3,
        10,
        5
    )

    st.divider()

    if GEMINI_KEY:
        st.success("🧠 Gemini Ready")
    else:
        st.warning(
            "🧠 Gemini မချိတ်ထားပါ"
        )

    if VIDEO_API_URL:
        st.success(
            "🎥 Video GPU Backend Ready"
        )
    else:
        st.error(
            "🎥 Video GPU Backend မရှိသေးပါ"
        )


# ============================================================
# NOVEL INPUT
# ============================================================

uploaded = st.file_uploader(
    "📖 ဝတ္ထုဖိုင်",
    type=["txt", "md"]
)

if uploaded:
    novel = uploaded.read().decode(
        "utf-8",
        errors="ignore"
    )
else:
    novel = st.text_area(
        "ဝတ္ထု",
        height=350,
        placeholder="ဝတ္ထုတစ်ပုဒ်လုံး ထည့်ပါ..."
    )


# ============================================================
# ANALYZE
# ============================================================

if st.button(
    "🧠 AI နဲ့ ဝတ္ထုနားလည်စေမည်",
    type="primary",
    use_container_width=True
):

    if not novel.strip():

        st.error(
            "ဝတ္ထုထည့်ပါ။"
        )

    else:

        with st.spinner(
            "AI က ဇာတ်လမ်းတစ်ပုဒ်လုံးကို "
            "နားလည်ပြီး Character / Scene / "
            "Dialogue ခွဲနေပါတယ်..."
        ):

            plan = analyze_story(
                novel,
                max_scenes
            )

            if plan is None:
                plan = fallback_plan(
                    novel,
                    max_scenes
                )

            st.session_state["plan"] = plan

        st.success(
            "✅ Movie plan ပြီးပါပြီ"
        )


# ============================================================
# SHOW PLAN
# ============================================================

if "plan" in st.session_state:

    plan = st.session_state["plan"]

    st.divider()

    st.header(
        "🎬 " +
        plan.get(
            "title",
            "Novel Movie"
        )
    )

    characters = plan.get(
        "characters",
        []
    )

    if characters:

        st.subheader(
            "🎭 Characters"
        )

        for c in characters:

            with st.expander(
                c.get(
                    "name",
                    "Character"
                )
            ):

                st.write(
                    "**Appearance:**",
                    c.get(
                        "appearance",
                        ""
                    )
                )

                st.write(
                    "**Personality:**",
                    c.get(
                        "personality",
                        ""
                    )
                )

                st.write(
                    "**Clothing:**",
                    c.get(
                        "clothing",
                        ""
                    )
                )

    scenes = plan.get(
        "scenes",
        []
    )

    st.subheader(
        f"🎥 Scenes ({len(scenes)})"
    )

    for scene in scenes:

        with st.expander(
            f"Scene {scene.get('id')} — "
            f"{scene.get('title', '')}"
        ):

            st.write(
                "**Summary:**",
                scene.get(
                    "summary",
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

            st.write(
                "**Visual:**",
                scene.get(
                    "visual_prompt",
                    ""
                )
            )

            for line in scene.get(
                "dialogue",
                []
            ):

                st.write(
                    f"**{line.get('character', '')}:** "
                    f"{line.get('text', '')}"
                )


# ============================================================
# GENERATE MOVIE
# ============================================================

if "plan" in st.session_state:

    st.divider()

    if st.button(
        "🚀 🎬 GENERATE 3D MOVIE",
        type="primary",
        use_container_width=True
    ):

        plan = st.session_state["plan"]
        scenes = plan.get("scenes", [])

        if not VIDEO_API_URL:

            st.error(
                "🎥 Video GPU backend မချိတ်ထားသေးပါ။"
            )

            st.info(
                "ဒီ Streamlit app က GPU video model "
                "ကိုယ်တိုင် run မလုပ်နိုင်ပါ။ "
                "VIDEO_API_URL ထည့်ပေးထားတဲ့ video "
                "backend တစ်ခုလိုပါတယ်။"
            )

        else:

            videos = []

            progress = st.progress(0)

            for index, scene in enumerate(
                scenes
            ):

                st.write(
                    f"🎥 Scene {scene.get('id')} "
                    f"/ {len(scenes)}"
                )

                # Character consistency
                character_text = ""

                for character in plan.get(
                    "characters",
                    []
                ):

                    character_text += (
                        character.get(
                            "name",
                            ""
                        )
                        + ": "
                        + character.get(
                            "appearance",
                            ""
                        )
                        + ", "
                        + character.get(
                            "clothing",
                            ""
                        )
                        + "\n"
                    )

                prompt = (
                    "cinematic 3D animated movie, "
                    "high quality 3D character animation, "
                    "consistent recurring characters, "
                    "natural body movement, "
                    "realistic facial expression, "
                    "cinematic lighting, "
                    "detailed environment, "
                    "professional movie camera, "
                    "smooth camera movement, "
                    "film quality, "
                    "\nCHARACTERS:\n"
                    + character_text
                    + "\nSCENE:\n"
                    + scene.get(
                        "visual_prompt",
                        ""
                    )
                    + "\nACTION:\n"
                    + scene.get(
