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
# GEMINI STORY GENERATOR
# ============================================================

def generate_story_plan(novel, max_scenes=10):

    if not GEMINI_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY မတွေ့ပါ။ "
            "Streamlit Secrets ထဲထည့်ပါ။"
        )

    prompt = f"""
You are a professional 3D animated movie director,
screenwriter and storyboard artist.

Convert the following Burmese novel into a cinematic
3D animated movie plan.

Important:
- Preserve the original story.
- Keep characters visually consistent.
- Create logical scenes.
- Use Burmese dialogue.
- Give every scene a cinematic camera direction.
- Give every scene a detailed 3D animation prompt.
- Do not add unrelated story events.
- Maximum scenes: {max_scenes}

Return ONLY valid JSON.

Format:

{{
  "title": "Movie title",
  "characters": [
    {{
      "id": "character_1",
      "name": "Name",
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
      "action": "What happens",
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

    text = text.strip()

    # Remove Markdown JSON fences
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

    return json.loads(text.strip())


# ============================================================
# CHARACTER CONSISTENCY
# ============================================================

def get_character_context(scene, characters):

    character_map = {
        str(c.get("id")): c
        for c in characters
        if isinstance(c, dict)
    }

    descriptions = []

    for character_id in scene.get("characters", []):

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

    return "\n".join(descriptions)


# ============================================================
# VIDEO PROMPT
# ============================================================

def build_video_prompt(scene, characters):

    character_context = get_character_context(
        scene,
        characters
    )

    return f"""
Cinematic high-quality 3D animated movie.

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
consistent character design,
realistic lighting,
detailed environment,
natural facial expressions,
natural body movement,
smooth animation,
cinematic depth of field,
professional movie composition,
4K quality.

Do not show subtitles.
Do not show text.
Do not show watermark.
"""


# ============================================================
# VIDEO API
# ============================================================

def generate_video(prompt, duration=5):

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
                "Video API က video URL မပြန်ပေးပါ။"
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

    except Exception as e:

        return None, str(e)


# ============================================================
# MYANMAR TTS
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

        async def create():

            communicate = edge_tts.Communicate(
                text,
                "my-MM-ThihaNeural"
            )

            await communicate.save(
                output.name
            )

        asyncio.run(create())

        return output.name

    except Exception:

        return None


# ============================================================
# SCENE DIALOGUE
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

        if
