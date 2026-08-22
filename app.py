import streamlit as st
import requests
import json
import os
import re
import tempfile
import subprocess
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================

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
        value = st.secrets.get(name, default)
        return value or os.getenv(name, default)
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

    parts = re.split(r"(?<=[။.!?])\s+", text)

    result = []
    current = ""

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if len(current) + len(part) + 1 > limit:
            if current:
                result.append(current)

            current = part
        else:
            if current:
                current += " "

            current += part

    if current:
        result.append(current)

    return result


# ============================================================
# CLEAN JSON
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

def generate_story_plan(novel, max_scenes=8):

    if not GEMINI_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY မရှိသေးပါ။ "
            "Streamlit Secrets ထဲမှာ ထည့်ပါ။"
        )

    prompt = f"""
You are a professional cinematic 3D animated movie director,
screenwriter and storyboard artist.

Convert the following Burmese novel into a complete movie plan.

Requirements:

1. Preserve the original story.
2. Identify all important recurring characters.
3. Keep character appearance consistent between scenes.
4. Divide the story into logical cinematic scenes.
5. Create natural Burmese dialogue.
6. Describe character actions and emotions.
7. Describe cinematic camera movement.
8. Create detailed 3D animation prompts.
9. Keep locations and time consistent.
10. Maximum scenes: {max_scenes}

Return ONLY valid JSON.

JSON FORMAT:

{{
  "title": "Movie title",
  "characters": [
    {{
      "id": "character_1",
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
      "characters": ["character_1"],
      "action": "Scene action",
      "emotion": "Emotion",
      "camera": "Camera movement",
      "visual_prompt": "Detailed cinematic 3D prompt",
      "dialogue": [
        {{
          "character": "character_1",
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
        f"?key={GEMINI_KEY}"
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
# CHARACTER CONTEXT
# ============================================================

def get_character_context(scene, characters):

    character_map = {}

    for character in characters:

        if not isinstance(character, dict):
            continue

        cid = str(
            character.get("id", "")
        )

        if cid:
            character_map[cid] = character

    descriptions = []

    for character_id in scene.get(
        "characters",
        []
    ):

        character = character_map.get(
            str(character_id)
        )

        if not character:
            continue

        descriptions.append(
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

    return "\n".join(
        descriptions
    )


# ============================================================
# VIDEO PROMPT
# ============================================================

def build_video_prompt(
    scene,
    characters
):

    character_context = (
        get_character_context(
            scene,
            characters
        )
    )

    return f"""
Cinematic high quality 3D animated movie scene.

Scene:
{scene.get("title", "")}

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

Character consistency:
{character_context}

Visual direction:
{scene.get("visual_prompt", "")}

Style:

professional cinematic 3D animation,
high quality 3D characters,
consistent character design,
realistic environment,
cinematic lighting,
natural facial expressions,
natural body movement,
smooth animation,
depth of field,
professional movie camera,
film-quality composition,
4K quality.

Do not show subtitles.
Do not show text.
Do not show watermark.
"""


# ============================================================
# VIDEO GENERATION API
# ============================================================

def generate_video(
    prompt,
    duration=5
):

    if not VIDEO_API_URL:
        return None, (
            "VIDEO_API_URL မရှိသေးပါ။"
        )

    try:

        response = requests.post(
            VIDEO_API_URL,
            json={
                "prompt": prompt,
                "duration": duration,
                "seconds": duration
            },
            timeout=1800
        )

        response.raise_for_status()

        data = response.json()

        video_url = (
            data.get("video_url")
            or data.get("url")
            or data.get("video")
        )

        if not video_url:

            return None, (
                "Video API က video URL "
                "မပြန်ပေးပါ။"
            )

        video_response = requests.get(
            video_url,
            timeout=1800
        )

        video_response.raise_for_status()

        output = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4"
        )

        output.write(
            video_response.content
        )

        output.close()

        return output.name, None

    except Exception as error:

        return None, str(error)


# ============================================================
# MYANMAR TTS
# ============================================================

def create_voice(text):

    if not text:
        return None

    text = text.strip()

    if not text:
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

            communicator = edge_tts.Communicate(
                text,
                "my-MM-ThihaNeural"
            )

            await communicator.save(
                output.name
            )

        asyncio.run(create())

        return output.name

    except Exception:

        return None


# ============================================================
# DIALOGUE
# ============================================================

def get_dialogue(scene):

    dialogue = scene.get(
        "dialogue",
        []
    )

    if not isinstance(
        dialogue,
        list
    ):
        return ""

    lines = []

    for item in dialogue:

        if not isinstance(
            item,
            dict
        ):
            continue

        character = str(
            item.get(
                "character",
                ""
            )
        ).strip()

        text = str(
            item.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        if character:

            lines.append(
                f"{character}: {text}"
            )

        else:

            lines.append(text)

    return "\n".join(lines)


# ============================================================
# ADD AUDIO
# ============================================================

def add_voice(
    video_path,
    audio_path
):

    if not video_path:
        return None

    if not audio_path:
        return video_path

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
                video_path,
                "-i",
                audio_path,
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

        return video_path


# ============================================================
# MERGE MP4
# ============================================================

def merge_videos(video_files):

    video_files = [
        item
        for item in video_files
        if item
    ]

    if not video_files:
        return None

    if len(video_files) == 1:
        return video_files[0]

    concat_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".txt",
        mode="w"
    )

    for video in video_files:

        absolute_path = str(
            Path(video).resolve()
        )

        concat_file.write(
            "file '"
            + absolute_path.replace(
                "'",
                "'\\''"
            )
            + "'\n"
        )

    concat_file.close()

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
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_file.name,
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
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
# HEADER
# ============================================================

st.title(
    "🎬 Novel 3D Movie AI"
)

st.markdown(
    """
**📖 Novel → 🧠 AI Story → 🎭 Characters
→ 🎬 Scenes → 💬 Burmese Dialogue
→ 🔊 Voice → 🎥 Video → 🎞️ MP4**
"""
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Movie Settings"
    )

    max_scenes = st.slider(
        "🎬 Maximum Scenes",
        min_value=1,
        max_value=30,
        value=8
    )

    duration = st.slider(
        "⏱️ Scene Duration",
        min_value=3,
        max_value=10,
        value=5
    )

    st.divider()

    if GEMINI_KEY:

        st.success(
            "🧠 Gemini Ready"
        )

    else:

        st.warning(
            "🧠 Gemini API Key မရှိသေးပါ"
        )

    if VIDEO_API_URL:

        st.success(
            "🎥 Video API Ready"
        )

    else:

        st.warning(
            "🎥 Video API မရှိသေးပါ"
        )


# ============================================================
# NOVEL INPUT
# ============================================================

uploaded_file = st.file_uploader(
    "📖 ဝတ္ထုဖိုင်တင်ပါ",
    type=[
        "txt",
        "md"
    ]
)

if uploaded_file:

    novel = uploaded_file.read().decode(
        "utf-8",
        errors="ignore"
    )

else:

    novel = st.text_area(
        "📖 ဝတ္ထု",
        height=350,
        placeholder=(
            "ဝတ္ထုကို ဒီနေရာမှာ ထည့်ပါ..."
        )
    )


# ============================================================
# ANALYZE BUTTON
# ============================================================

if st.button(
    "🧠 AI နဲ့ ဇာတ်လမ်းခွဲမယ်",
    type="primary",
    use_container_width=True
):

    if not novel.strip():

        st.error(
            "ဝတ္ထုထည့်ပါ။"
        )

    else:

        try:

            with st.spinner(
                "AI က ဇာတ်လမ်း၊ Character "
                "နဲ့ Scene တွေ ခွဲနေပါတယ်..."
            ):

                plan = generate_story_plan(
                    novel,
                    max_scenes
                )

                st.session_state[
                    "movie_plan"
                ] = plan

            st.success(
                "✅ Movie Plan ပြီးပါပြီ"
            )

        except Exception as error:

            st.error(
                f"AI Error: {error}"
            )


# ============================================================
# DISPLAY MOVIE PLAN
# ============================================================

if "movie_plan" in st.session_state:

    plan = st.session_state[
        "movie_plan"
    ]

    st.divider()

    st.header(
        "🎬 "
        + str(
            plan.get(
                "title",
                "Novel 3D Movie"
            )
        )
    )

    characters = plan.get(
        "characters",
        []
    )

    scenes = plan.get(
        "scenes",
        []
    )

    # ========================================================
    # CHARACTERS
    # ========================================================

    st.subheader(
        "🎭 Characters"
    )

    for character in characters:

        with st.expander(
            str(
                character.get(
                    "name",
                    "Character"
                )
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
        f"🎥 Scenes ({len(scenes)})"
    )

    for scene in scenes:

        with st.expander(
            "Scene "
            + str(
                scene.get(
                    "id",
                    ""
                )
            )
            + " — "
            + str(
                scene.get(
                    "title",
                    ""
                )
            )
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

            dialogue = get_dialogue(
                scene
            )

            if dialogue:

                st.write(
                    "**Dialogue:**"
                )

                st.text(
                    dialogue
                )


# ============================================================
# GENERATE MOVIE
# ============================================================

if "movie_plan" in st.session_state:

    st.divider()

    st.header(
        "🎞️ Generate Full Movie"
    )

    if not VIDEO_API_URL:

        st.info(
            """
VIDEO_API_URL မထည့်ထားသေးပါ။

Gemini က ဇာတ်လမ်းနဲ့ Scene တွေ
ထုတ်ပေးနိုင်ပါတယ်။

MP4 တကယ် generate လုပ်ဖို့
Video Generation API/backend
တစ်ခုလိုပါတယ်။
"""
        )

    if st.button(
        "🎬 Generate Full Movie",
        type="primary",
        use_container_width=True
    ):

        if not VIDEO_API_URL:

            st.error(
                "VIDEO_API_URL မရှိသေးပါ။"
            )

        else:

            plan = st.session_state[
                "movie_plan"
            ]

            characters = plan.get(
                "characters",
                []
            )

            scenes = plan.get(
                "scenes",
                []
            )

            video_files = []

            progress = st.progress(
                0
            )

            status = st.empty()

            total = len(scenes)

            for index, scene in enumerate(
                scenes,
                1
            ):

                status.write(
                    f"🎥 Scene {index}/{total} "
                    "generate လုပ်နေပါတယ်..."
                )

                prompt = build_video_prompt(
                    scene,
                    characters
                )

                video_file, error = generate_video(
                    prompt,
                    duration
                )

                if video_file:

                    dialogue = get_dialogue(
                        scene
                    )

                    if dialogue:

                        audio_file = create_voice(
                            dialogue
                        )

                        if audio_file:

                            video_file = add_voice(
                                video_file,
                                audio_file
                            )

                    video_files.append(
                        video_file
                    )

                else:

                    st.warning(
                        f"Scene {index} failed: "
                        f"{error}"
                    )

                progress.progress(
                    index / total
                )

            status.write(
                "🎞️ Final MP4 merge လုပ်နေပါတယ်..."
            )

            final_video = merge_videos(
                video_files
            )

            if final_video:

                st.success(
                    "🎉 Full Movie MP4 ပြီးပါပြီ!"
                )

                st.video(
                    final_video
                )

                with open(
                    final_video,
                    "rb"
                ) as video_file:

                    st.download_button(
                        "📥 Download MP4",
                        video_file,
                        file_name=(
                            "novel_3d_movie.mp4"
                        ),
                        mime="video/mp4",
                        use_container_width=True
                    )

            else:

                st.error(
                    "MP4 merge မအောင်မြင်ပါ။"
                )
