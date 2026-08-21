import streamlit as st
import requests
import json
import os
import re
import tempfile
import subprocess
from pathlib import Path

# ============================================================
# PAGE
# ============================================================

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

try:
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    GEMINI_KEY = ""

GEMINI_KEY = GEMINI_KEY or os.getenv(
    "GEMINI_API_KEY",
    ""
)

try:
    VIDEO_API_URL = st.secrets.get("VIDEO_API_URL", "")
except Exception:
    VIDEO_API_URL = ""

VIDEO_API_URL = VIDEO_API_URL or os.getenv(
    "VIDEO_API_URL",
    ""
)

try:
    LIPSYNC_API_URL = st.secrets.get(
        "LIPSYNC_API_URL",
        ""
    )
except Exception:
    LIPSYNC_API_URL = ""

LIPSYNC_API_URL = LIPSYNC_API_URL or os.getenv(
    "LIPSYNC_API_URL",
    ""
)


# ============================================================
# STORY SPLITTER
# ============================================================

def split_story(text, max_chars=7000):

    text = text.strip()

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    parts = re.split(
        r"(?<=[။.!?])\s+",
        text
    )

    result = []
    current = ""

    for part in parts:

        if len(current) + len(part) > max_chars:

            if current:
                result.append(current)

            current = part

        else:

            current += (
                " " if current else ""
            ) + part

    if current:
        result.append(current)

    return result


# ============================================================
# GEMINI STORY PLANNER
# ============================================================

def ask_gemini(novel, max_scenes):

    if not GEMINI_KEY:
        return None

    prompt = f"""
You are a professional film director,
screenwriter and character-continuity supervisor.

Read the novel carefully.

Turn the novel into a cinematic movie
production plan.

IMPORTANT:

- Preserve the original story.
- Do not invent major events.
- Identify all important recurring characters.
- Keep character appearance consistent.
- Create natural dialogue.
- Create realistic physical actions.
- Create emotions.
- Create locations.
- Create time of day.
- Create camera movement.
- Create cinematic visual prompts.
- Keep scene order logical.

Maximum scenes: {max_scenes}

Return ONLY valid JSON.

FORMAT:

{{
  "title": "",
  "characters": [
    {{
      "id": "c1",
      "name": "",
      "appearance": "",
      "personality": "",
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
      "characters": [],
      "emotion": "",
      "action": "",
      "camera": "",
      "visual_prompt": "",
      "dialogue": [
        {{
          "character": "",
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
        "?key="
        + GEMINI_KEY
    )

    try:

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
                    "responseMimeType":
                        "application/json"
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

        return json.loads(text)

    except Exception as e:

        st.warning(
            "Gemini မရသေးပါ။ "
            "Offline story planner သုံးနေပါတယ်။"
        )

        return None


# ============================================================
# OFFLINE FALLBACK
# ============================================================

def offline_plan(novel, max_scenes):

    chunks = split_story(novel)

    chunks = chunks[:int(max_scenes)]

    scenes = []

    for i, text in enumerate(
        chunks,
        start=1
    ):

        scenes.append({

            "id": i,

            "title":
                f"Scene {i}",

            "summary":
                text[:600],

            "location":
                "Story location",

            "time":
                "Story time",

            "characters":
                [],

            "emotion":
                "dramatic",

            "action":
                text,

            "camera":
                "cinematic tracking shot",

            "visual_prompt": (
                "cinematic movie scene, "
                "realistic characters, "
                "natural body movement, "
                "detailed environment, "
                "dramatic film lighting, "
                "professional movie camera, "
                + text[:1200]
            ),

            "dialogue":
                []
        })

    return {

        "title":
            "Novel Movie",

        "characters":
            [],

        "scenes":
            scenes
    }


# ============================================================
# TTS
# ============================================================

def create_voice(text):

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

        async def generate():

            communicator = edge_tts.Communicate(
                text,
                "my-MM-ThihaNeural"
            )

            await communicator.save(
                output.name
            )

        asyncio.run(generate())

        return output.name

    except Exception as e:

        st.warning(
            f"TTS မအောင်မြင်ပါ: {e}"
        )

        return None


# ============================================================
# VIDEO BACKEND
# ============================================================

def generate_video(
    prompt,
    seconds
):

    if not VIDEO_API_URL:

        return (
            None,
            "VIDEO_API_URL မရှိသေးပါ။"
        )

    try:

        response = requests.post(

            VIDEO_API_URL,

            json={
                "prompt": prompt,
                "seconds": seconds
            },

            timeout=1800
        )

        response.raise_for_status()

        data = response.json()

        video_url = data.get(
            "video_url"
        )

        if not video_url:

            return (
                None,
                "Video backend က video_url မပြန်ပါ။"
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

        output.write(
            video.content
        )

        output.close()

        return output.name, None

    except Exception as e:

        return None, str(e)


# ============================================================
# FFmpeg
# ============================================================

def combine_video_audio(
    video,
    audio
):

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
                "-i",
                video,
                "-i",
                audio,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
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
# HEADER
# ============================================================

st.title(
    "🎬 Novel → Movie AI"
)

st.caption(
    "📖 Novel → 🧠 Story → 🎭 Characters → "
    "🎬 Scenes → 🗣️ Voice → 🎥 Video → 🎞️ Movie"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Movie Settings"
    )

    max_scenes = st.slider(
        "Scene အများဆုံး",
        min_value=1,
        max_value=30,
        value=8
    )

    seconds = st.slider(
        "Scene ကြာချိန်",
        min_value=3,
        max_value=10,
        value=5
    )

    st.divider()

    st.subheader(
        "🔌 Connection"
    )

    if GEMINI_KEY:
        st.success(
            "🧠 Gemini Connected"
        )
    else:
        st.warning(
            "🧠 Gemini မချိတ်ထားပါ"
        )

    if VIDEO_API_URL:
        st.success(
            "🎥 Video Backend Connected"
        )
    else:
        st.error(
            "🎥 Video Backend မချိတ်ထားပါ"
        )

    if LIPSYNC_API_URL:
        st.success(
            "👄 Lip-sync Connected"
        )
    else:
        st.info(
            "👄 Lip-sync မချိတ်ထားပါ"
        )


# ============================================================
# NOVEL INPUT
# ============================================================

uploaded = st.file_uploader(
    "📖 ဝတ္ထုဖိုင်ထည့်ပါ",
    type=["txt", "md"]
)

novel = ""

if uploaded:

    novel = uploaded.read().decode(
        "utf-8",
        errors="ignore"
    )

else:

    novel = st.text_area(

        "သို့မဟုတ် ဝတ္ထုကို ဒီမှာထည့်ပါ",

        height=350,

        placeholder=
        "ဝတ္ထုတစ်ပုဒ်လုံးကို ဒီမှာထည့်ပါ..."
    )


# ============================================================
# ANALYZE BUTTON
# ============================================================

if st.button(

    "🧠 ဝတ္ထုကို AI နားလည်အောင်လုပ်မည်",

    type="primary",

    use_container_width=True
):

    if not novel.strip():

        st.error(
            "⚠️ ဝတ္ထုထည့်ပါ။"
        )

    else:

        with st.spinner(
            "🧠 AI က ဇာတ်လမ်းကို "
            "နားလည်ပြီး Character / Scene / "
            "Dialogue ခွဲနေပါတယ်..."
        ):

            plan = ask_gemini(
                novel,
                max_scenes
            )

            if plan is None:

                plan = offline_plan(
                    novel,
                    max_scenes
                )

            st.session_state[
                "plan"
            ] = plan

        st.success(
            "✅ Story analysis ပြီးပါပြီ။"
        )


# ============================================================
# SHOW STORY PLAN
# ============================================================

if "plan" in st.session_state:

    plan = st.session_state[
        "plan"
    ]

    st.divider()

    st.header(
        "🎬 "
        + plan.get(
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

        for character in characters:

            with st.expander(
                character.get(
                    "name",
                    "Character"
                )
            ):

                st.write(
                    "**Appearance:**",
                    character.get(
                        "appearance",
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

    scenes = plan.get(
        "scenes",
        []
    )

    st.subheader(
        f"🎥 Scenes ({len(scenes)})"
    )

    for scene in scenes:

        with st.expander(

            "Scene "
            + str(scene.get("id"))
            + " — "
            + scene.get(
                "title",
                ""
            )
        ):

            st.write(
                "**Summary:**",
                scene.get(
                    "summary",
                    ""
                )
            )

            st.write(
                "**Location:**",
                scene.get(
                    "location",
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
                "**Visual Prompt:**",
                scene.get(
                    "visual_prompt",
                    ""
                )
            )

            dialogue = scene.get(
                "dialogue",
                []
            )

            if dialogue:

                st.write(
                    "🗣️ **Dialogue**"
                )

                for line in dialogue:

                    st.write(
                        "**"
                        + line.get(
                            "character",
                            ""
                        )
                        + ":** "
                        + line.get(
                            "text",
                            ""
                        )
                    )


# ============================================================
# MOVIE GENERATION
# ============================================================

if "plan" in st.session_state:

    st.divider()

    st.header(
        "🚀 Movie Generator"
    )

    if st.button(

        "🎬 ရုပ်ရှင်စတင်ဖန်တီးမည်",

        type="primary",

        use_container_width=True
    ):

        plan = st.session_state[
            "plan"
        ]

        scenes = plan.get(
            "scenes",
            []
        )

        if not VIDEO_API_URL:

            st.error(
                "🎥 Video GPU backend "
                "မချိတ်ထားသေးပါ။"
            )

            st.info(
                "Story analysis ကတော့ "
                "အလုပ်လုပ်ပါတယ်။ "
                "ရုပ်ရှင် video ထုတ်ဖို့ "
                "GPU video backend လိုပါတယ်။"
            )

        else:

            progress = st.progress(
                0
            )

            generated = []

            for index, scene in enumerate(
                scenes
            ):

                st.write(
                    "🎥 Scene "
                    + str(scene.get("id"))
                    + " / "
                    + str(len(scenes))
                )

                video, error = generate_video(

                    scene.get(
                        "visual_prompt",
                        ""
                    ),

                    seconds
                )

                if error:

                    st.error(
                        "Scene "
                        + str(scene.get("id"))
                        + ": "
                        + error
                    )

                    break

                if video:

                    dialogue = scene.get(
                        "dialogue",
                        []
                    )

                    text = " ".join(

                        line.get(
                            "text",
                            ""
                        )

                        for line in dialogue
                    )

                    if text:

                        audio = create_voice(
                            text
                        )

                        if audio:

                            video = combine_video_audio(
                                video,
                                audio
                            )

                    generated.append(
                        video
                    )

                    st.video(
                        video
                    )

                progress.progress(
                    (index + 1)
                    / len(scenes)
                )

            if generated:

                st.success(
                    "🎬 Movie scenes "
                    "ထုတ်ပြီးပါပြီ။"
                )

                st.info(
                    "Final MP4 assembly ကို "
                    "နောက်ဆုံးအဆင့်မှာ "
                    "FFmpeg နဲ့ ပေါင်းနိုင်ပါတယ်။"
                )
