import os
import json
import time
import requests
import streamlit as st

st.set_page_config(
    page_title="Novel 3D Movie AI",
    page_icon="🎬",
    layout="wide"
)

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY", "")
)

ELEVENLABS_API_KEY = st.secrets.get(
    "ELEVENLABS_API_KEY",
    os.getenv("ELEVENLABS_API_KEY", "")
)

VIDEO_WORKER_URL = st.secrets.get(
    "VIDEO_WORKER_URL",
    os.getenv("VIDEO_WORKER_URL", "")
).rstrip("/")


# ============================================================
# GEMINI
# ============================================================

def generate_movie_plan(novel):

    if not GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY မရှိပါ")

    prompt = f"""
Create a cinematic 3D animated movie plan
from this Burmese story.

Create 5 scenes.

For every scene include:
- location
- characters
- action
- emotion
- camera
- visual_prompt
- Burmese dialogue

Keep characters visually consistent.

Return ONLY JSON.

Format:

{{
  "title": "Movie title",
  "characters": [
    {{
      "id": "wolf",
      "name": "Character",
      "appearance": "Detailed appearance"
    }}
  ],
  "scenes": [
    {{
      "id": 1,
      "title": "Scene title",
      "location": "Location",
      "characters": ["wolf"],
      "action": "Action",
      "emotion": "Emotion",
      "camera": "Camera movement",
      "visual_prompt": "Detailed cinematic 3D prompt",
      "dialogue": "Burmese dialogue"
    }}
  ]
}}

STORY:

{novel}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    response = requests.post(
        url,
        params={"key": GEMINI_API_KEY},
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

    if response.status_code != 200:
        raise Exception(
            f"Gemini Error {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]

    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    return json.loads(text)


# ============================================================
# VIDEO WORKER
# ============================================================

def generate_video(prompt, seconds=5):

    if not VIDEO_WORKER_URL:
        raise Exception(
            "VIDEO_WORKER_URL မရှိပါ"
        )

    url = VIDEO_WORKER_URL + "/generate"

    response = requests.post(
        url,
        json={
            "prompt": prompt,
            "seconds": seconds
        },
        timeout=60
    )

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Video Worker Error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    return response.json()


# ============================================================
# UI
# ============================================================

st.title("🎬 Novel 3D Movie AI")

st.write(
    "📖 Novel → Gemini → 🎨 T4 GPU → 🎞️ Movie"
)

st.divider()


novel = st.text_area(
    "📖 ဝတ္ထုထည့်ပါ",
    height=300,
    placeholder=(
        "ဥပမာ - သမန်းဝံပုလွေဇာတ်လမ်း..."
    )
)


if st.button(
    "🧠 ဇာတ်လမ်းဖန်တီးမယ်",
    type="primary",
    use_container_width=True
):

    if not novel.strip():

        st.warning(
            "ဝတ္ထုထည့်ပါ"
        )

    else:

        try:

            with st.spinner(
                "Gemini က ဇာတ်လမ်းခွဲနေပါတယ်..."
            ):

                movie = generate_movie_plan(
                    novel
                )

            st.session_state["movie"] = movie

            st.success(
                "✅ Movie plan ရပြီ"
            )

        except Exception as e:

            st.error(
                "❌ Error"
            )

            st.code(
                str(e)
            )


# ============================================================
# SHOW MOVIE
# ============================================================

if "movie" in st.session_state:

    movie = st.session_state["movie"]

    st.header(
        "🎬 " + movie.get(
            "title",
            "My Movie"
        )
    )


    # --------------------------------------------------------
    # CHARACTERS
    # --------------------------------------------------------

    characters = movie.get(
        "characters",
        []
    )

    with st.expander(
        "🎭 Characters",
        expanded=True
    ):

        for character in characters:

            st.markdown(
                "### "
                + character.get(
                    "name",
                    "Character"
                )
            )

            st.write(
                character.get(
                    "appearance",
                    ""
                )
            )


    # --------------------------------------------------------
    # SCENES
    # --------------------------------------------------------

    scenes = movie.get(
        "scenes",
        []
    )

    st.subheader(
        "🎞️ Scenes"
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
            f"Scene {scene_id}: {scene_title}"
        ):

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

            st.markdown(
                "#### 🎨 Video Prompt"
            )

            prompt = scene.get(
                "visual_prompt",
                ""
            )

            st.code(
                prompt,
                language="text"
            )

            st.markdown(
                "#### 🗣️ Dialogue"
            )

            st.write(
                scene.get(
                    "dialogue",
                    ""
                )
            )


    # --------------------------------------------------------
    # GENERATE VIDEO
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "🎬 Movie ထုတ်မယ်",
        type="primary",
        use_container_width=True
    ):

        if not VIDEO_WORKER_URL:

            st.error(
                "VIDEO_WORKER_URL မရှိပါ"
            )

        else:

            progress = st.progress(0)

            video_results = []

            total = len(scenes)

            for index, scene in enumerate(
                scenes,
                start=1
            ):

                try:

                    prompt = scene.get(
                        "visual_prompt",
                        ""
                    )

                    result = generate_video(
                        prompt,
                        seconds=5
                    )

                    video_results.append(
                        result
                    )

                    st.success(
                        f"Scene {index} ပြီးပါပြီ ✅"
                    )

                except Exception as e:

                    st.error(
                        f"Scene {index} Error: {e}"
                    )

                progress.progress(
                    index / total
                )


            st.session_state[
                "video_results"
            ] = video_results


# ============================================================
# VIDEO RESULTS
# ============================================================

if "video_results" in st.session_state:

    st.divider()

    st.header(
        "🎞️ Generated Videos"
    )

    for result in st.session_state[
        "video_results"
    ]:

        if isinstance(
            result,
            dict
        ):

            video_url = result.get(
                "video_url",
                result.get(
                    "url",
                    ""
                )
            )

            if video_url:

                if video_url.startswith(
                    "http"
                ):

                    st.video(
                        video_url
                    )

                else:

                    st.video(
                        VIDEO_WORKER_URL
                        + video_url
                    )

            else:

                st.json(result)

        else:

            st.write(result)
