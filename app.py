import os
import json
import uuid
import asyncio
import subprocess
from pathlib import Path

import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# ============================================================
# CONFIG
# ============================================================

BASE = Path(__file__).parent
DATA = BASE / "data"
PROJECTS = DATA / "projects"
STATIC = BASE / "static"

PROJECTS.mkdir(parents=True, exist_ok=True)
STATIC.mkdir(parents=True, exist_ok=True)

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

app = FastAPI(title="Novel Movie AI")

app.mount(
    "/static",
    StaticFiles(directory=STATIC),
    name="static"
)


# ============================================================
# JSON HELPERS
# ============================================================

def save_json(path, data):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# STORY AI
# ============================================================

def create_story_plan(novel, max_scenes):

    if GEMINI_KEY:

        prompt = f"""
You are an expert movie director, screenwriter
and character continuity supervisor.

Read the complete novel below.

Turn it into a cinematic movie production plan.

Requirements:

1. Understand the entire story.
2. Preserve the original plot.
3. Do not randomly invent major events.
4. Identify recurring characters.
5. Keep character appearance consistent.
6. Create natural dialogue.
7. Create scene locations.
8. Create time of day.
9. Create emotions.
10. Create physical actions.
11. Create camera directions.
12. Create detailed video prompts.
13. Separate narration and dialogue.

Create no more than {max_scenes} scenes.

Return ONLY valid JSON.

FORMAT:

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
  "location":"",
  "time":"",
  "characters":[],
  "summary":"",
  "action":"",
  "emotion":"",
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

        try:

            response = requests.post(
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/gemini-2.5-flash:generateContent"
                "?key=" + GEMINI_KEY,
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

            response.raise_for_status()

            result = response.json()

            text = (
                result["candidates"][0]
                ["content"]["parts"][0]
                ["text"]
            )

            return json.loads(text)

        except Exception as e:

            print("Gemini error:", e)

    # Offline fallback

    paragraphs = [
        x.strip()
        for x in novel.split("\n\n")
        if x.strip()
    ]

    paragraphs = paragraphs[:max_scenes]

    scenes = []

    for i, text in enumerate(
        paragraphs,
        start=1
    ):

        scenes.append({

            "id": i,

            "title":
                f"Scene {i}",

            "location":
                "Story location",

            "time":
                "Story time",

            "characters": [],

            "summary":
                text[:600],

            "action":
                text,

            "emotion":
                "dramatic",

            "camera":
                "cinematic tracking shot",

            "visual_prompt":
                "cinematic movie scene, "
                "realistic characters, "
                "natural body movement, "
                "detailed environment, "
                "dramatic lighting, "
                + text[:1500],

            "dialogue": [],

            "status":
                "queued"
        })

    return {

        "title":
            "Novel Movie",

        "characters": [],

        "scenes":
            scenes
    }


# ============================================================
# TTS
# ============================================================

async def make_voice(
    text,
    output,
    voice="my-MM-ThihaNeural"
):

    try:

        import edge_tts

        await edge_tts.Communicate(
            text,
            voice
        ).save(
            str(output)
        )

        return True

    except Exception as e:

        print("TTS:", e)

        return False


# ============================================================
# VIDEO PROVIDER
# ============================================================

class VideoProvider:

    """
    Video backend abstraction.

    You can connect:
      - local Wan
      - HuggingFace Space
      - custom GPU server
      - another video API

    The frontend does NOT need to change.
    """

    def generate(
        self,
        prompt,
        output,
        seconds=5
    ):

        endpoint = os.getenv(
            "VIDEO_API_URL",
            ""
        ).strip()

        token = os.getenv(
            "VIDEO_API_TOKEN",
            ""
        ).strip()

        if not endpoint:

            raise RuntimeError(
                "VIDEO_API_URL မသတ်မှတ်ရသေးပါ။ "
                "AI video GPU backend လိုအပ်ပါတယ်။"
            )

        headers = {}

        if token:

            headers[
                "Authorization"
            ] = "Bearer " + token

        response = requests.post(

            endpoint,

            json={
                "prompt": prompt,
                "seconds": seconds
            },

            headers=headers,

            timeout=1800
        )

        response.raise_for_status()

        data = response.json()

        video_url = data.get(
            "video_url"
        )

        if not video_url:

            raise RuntimeError(
                "Video backend က video_url မပြန်ပါ။"
            )

        video = requests.get(
            video_url,
            timeout=1800
        )

        video.raise_for_status()

        output.write_bytes(
            video.content
        )

        return output


video_provider = VideoProvider()


# ============================================================
# LIP SYNC PROVIDER
# ============================================================

class LipSyncProvider:

    def generate(
        self,
        video,
        audio,
        output
    ):

        endpoint = os.getenv(
            "LIPSYNC_API_URL",
            ""
        ).strip()

        if not endpoint:

            raise RuntimeError(
                "LIPSYNC_API_URL မသတ်မှတ်ရသေးပါ။"
            )

        with open(
            video,
            "rb"
        ) as vf, open(
            audio,
            "rb"
        ) as af:

            response = requests.post(

                endpoint,

                files={
                    "video": vf,
                    "audio": af
                },

                timeout=1800
            )

        response.raise_for_status()

        output.write_bytes(
            response.content
        )

        return output


lip_sync = LipSyncProvider()


# ============================================================
# FFMPEG
# ============================================================

def combine_video_audio(
    video,
    audio,
    output
):

    subprocess.run(

        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),

            "-map",
            "0:v:0",

            "-map",
            "1:a:0",

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-shortest",

            str(output)
        ],

        check=True
    )


def concat_videos(
    videos,
    output
):

    list_file = (
        output.parent /
        "videos.txt"
    )

    with open(
        list_file,
        "w",
        encoding="utf8"
    ) as f:

        for video in videos:

            f.write(
                "file '"
                + str(video)
                .replace(
                    "'",
                    "'\\''"
                )
                + "'\n"
            )

    subprocess.run(

        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output)
        ],

        check=True
    )


# ============================================================
# PROJECT CREATION
# ============================================================

@app.post(
    "/api/project"
)
async def create_project(

    novel: str = Form(...),

    max_scenes: int = Form(8),

    seconds: int = Form(5)

):

    if not novel.strip():

        return JSONResponse(
            {
                "error":
                "ဝတ္ထုထည့်ပါ"
            },
            status_code=400
        )

    project_id = (
        uuid.uuid4()
        .hex[:10]
    )

    folder = (
        PROJECTS /
        project_id
    )

    folder.mkdir()

    plan = create_story_plan(
        novel,
        max_scenes
    )

    save_json(
        folder /
        "plan.json",
        plan
    )

    save_json(

        folder /
        "state.json",

        {
            "id":
                project_id,

            "status":
                "ready",

            "progress":
                0,

            "seconds":
                seconds
        }
    )

    (
        folder /
        "novel.txt"
    ).write_text(
        novel,
        encoding="utf8"
    )

    return {

        "id":
            project_id,

        "plan":
            plan
    }


# ============================================================
# RENDER
# ============================================================

@app.post(
    "/api/project/{project_id}/generate"
)
async def generate_project(
    project_id: str
):

    folder = (
        PROJECTS /
        project_id
    )

    if not folder.exists():

        return JSONResponse(
            {
                "error":
                "Project မတွေ့ပါ"
            },
            status_code=404
        )

    plan = load_json(
        folder /
        "plan.json"
    )

    state = load_json(
        folder /
        "state.json"
    )

    scenes = plan[
        "scenes"
    ]

    state[
        "status"
    ] = "rendering"

    save_json(
        folder /
        "state.json",
        state
    )

    finished = []

    for scene in scenes:

        sid = scene["id"]

        final_scene = (
            folder /
            f"scene_{sid:03}.mp4"
        )

        if final_scene.exists():

            finished.append(
                final_scene
            )

            scene[
                "status"
            ] = "done"

            continue

        scene[
            "status"
        ] = "generating"

        save_json(
            folder /
            "plan.json",
            plan
        )

        prompt = (
            scene.get(
                "visual_prompt",
                ""
            )
        )

        raw_video = (
            folder /
            f"raw_{sid:03}.mp4"
        )

        audio = (
            folder /
            f"voice_{sid:03}.mp3"
        )

        # 1. VIDEO

        video_provider.generate(

            prompt,

            raw_video,

            state.get(
                "seconds",
                5
            )
        )

        # 2. DIALOGUE

        dialogue = scene.get(
            "dialogue",
            []
        )

        text = " ".join(
            x.get("text", "")
            for x in dialogue
            if x.get("text")
        )

        if text:

            asyncio.run(

                make_voice(

                    text,

                    audio
                )
            )

        # 3. AUDIO

        if audio.exists():

            with_audio = (
                folder /
                f"withaudio_{sid:03}.mp4"
            )

            combine_video_audio(
                raw_video,
                audio,
                with_audio
            )

            # 4. LIP SYNC

            try:

                lip_sync.generate(

                    with_audio,

                    audio,

                    final_scene
                )

            except Exception:

                # Do not fake lip-sync.
                # Keep correctly audio-mixed scene.

                with_audio.replace(
                    final_scene
                )

        else:

            raw_video.replace(
                final_scene
            )

        scene[
            "status"
        ] = "done"

        finished.append(
            final_scene
        )

        state[
            "progress"
        ] = (
            len(finished) /
            len(scenes)
        )

        save_json(
            folder /
            "plan.json",
            plan
        )

        save_json(
            folder /
            "state.json",
            state
        )

    # FINAL MOVIE

    final_movie = (
        folder /
        "final_movie.mp4"
    )

    concat_videos(
        finished,
        final_movie
    )

    state[
        "status"
    ] = "complete"

    state[
        "progress"
    ] = 1

    save_json(
        folder /
        "state.json",
        state
    )

    return {

        "ok":
            True,

        "video":
            f"/api/project/{project_id}/download"
    }


# ============================================================
# STATUS
# ============================================================

@app.get(
    "/api/project/{project_id}"
)
def project_status(
    project_id: str
):

    folder = (
        PROJECTS /
        project_id
    )

    if not folder.exists():

        return JSONResponse(
            {
                "error":
                "not found"
            },
            status_code=404
        )

    return {

        "state":
            load_json(
                folder /
                "state.json"
            ),

        "plan":
            load_json(
                folder /
                "plan.json"
            )
    }


# ============================================================
# DOWNLOAD
# ============================================================

@app.get(
    "/api/project/{project_id}/download"
)
def download(
    project_id: str
):

    movie = (
        PROJECTS /
        project_id /
        "final_movie.mp4"
    )

    if not movie.exists():

        return JSONResponse(
            {
                "error":
                "Movie မပြီးသေးပါ"
            },
            status_code=404
        )

    return FileResponse(

        movie,

        media_type=
        "video/mp4",

        filename=
        "NovelMovie.mp4"
    )


# ============================================================
# WEB PAGE
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def home():

    return """

<!DOCTYPE html>

<html lang="my">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>Novel Movie AI</title>

<style>

body{
margin:0;
background:#080a0f;
color:white;
font-family:Arial;
}

main{
max-width:900px;
margin:auto;
padding:20px;
}

.card{
background:#141923;
border:1px solid #293140;
border-radius:16px;
padding:20px;
margin-bottom:20px;
}

textarea{
width:100%;
min-height:330px;
box-sizing:border-box;
background:#080b10;
color:white;
border:1px solid #30394a;
border-radius:12px;
padding:15px;
font-size:16px;
}

input{
background:#080b10;
color:white;
border:1px solid #30394a;
padding:10px;
border-radius:8px;
}

button{
background:white;
color:#111;
border:0;
padding:13px 20px;
border-radius:10px;
font-weight:bold;
margin-top:15px;
}

.scene{
padding:12px;
border:1px solid #30394a;
border-radius:10px;
margin-top:10px;
}

.bar{
height:12px;
background:#292f3d;
border-radius:10px;
overflow:hidden;
}

.fill{
height:100%;
width:0%;
background:white;
}

</style>

</head>

<body>

<main>

<h1>🎬 Novel → Movie AI</h1>

<div class="card">

<h3>📖 ဝတ္ထု</h3>

<textarea
id="novel"
placeholder="ဝတ္ထုတစ်ပုဒ်လုံး ထည့်ပါ..."
></textarea>

<br><br>

Scene အများဆုံး

<input
id="scenes"
type="number"
value="8"
min="1"
max="30"
>

&nbsp;

Scene ကြာချိန်

<input
id="seconds"
type="number"
value="5"
min="3"
max="15"
>

<br>

<button
onclick="createProject()"
>
🧠 Analyze Novel
</button>

</div>

<div id="result"></div>

</main>

<script>

let projectId = null;

async function createProject(){

const novel =
document.getElementById(
"novel"
).value;

const scenes =
document.getElementById(
"scenes"
).value;

const seconds =
document.getElementById(
"seconds"
).value;

if(!novel.trim()){

alert(
"ဝတ္ထုထည့်ပါ"
);

return;

}

const body =
new URLSearchParams();

body.append(
"novel",
novel
);

body.append(
"max_scenes",
scenes
);

body.append(
"seconds",
seconds
);

document.getElementById(
"result"
).innerHTML =
"<div class='card'>🧠 AI က ဇာတ်လမ်းနားလည်နေပါတယ်...</div>";

const r =
await fetch(
"/api/project",
{
method:"POST",
body:body
}
);

const data =
await r.json();

if(data.error){

alert(
data.error
);

return;

}

projectId =
data.id;

let html = `
<div class="card">

<h2>🎬 ${data.plan.title}</h2>

<p>Job ID: ${data.id}</p>

<button
onclick="generate()"
>
🚀 Generate Movie
</button>

</div>
`;

for(
const s of data.plan.scenes
){

html += `

<div class="card scene">

<h3>
🎥 Scene ${s.id}
</h3>

<b>
${escapeHtml(s.title || "")}
</b>

<p>
${escapeHtml(s.summary || "")}
</p>

</div>

`;

}

document.getElementById(
"result"
).innerHTML =
html;

}


async function generate(){

document.getElementById(
"result"
).insertAdjacentHTML(
"afterbegin",
"<div class='card'>🎬 Movie render စနေပါပြီ...</div>"
);

const r =
await fetch(
"/api/project/"
+ projectId
+ "/generate",
{
method:"POST"
}
);

const data =
await r.json();

if(data.error){

alert(
data.error
);

return;

}

document.getElementById(
"result"
).insertAdjacentHTML(
"afterbegin",

`
<div class="card">

<h2>
✅ Movie ပြီးပါပြီ
</h2>

<a
href="${data.video}"
target="_blank"
>
🎬 MP4 ကြည့်ရန် / သိမ်းရန်
</a>

</div>
`
);

}


function escapeHtml(text){

return String(text)
.replace(
/[&<>"']/g,
function(m){

return {

"&":"&amp;",
"<":"&lt;",
">":"&gt;",
'"':"&quot;",
"'":"&#039;"

}[m];

}
);

}

</script>

</body>

</html>

"""
