import os
import json
import uuid
import asyncio
from pathlib import Path

import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

BASE = Path(__file__).parent
DATA = BASE / "data"
PROJECTS = DATA / "projects"
PROJECTS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Novel Movie AI")


# =========================
# STORY AI
# =========================

def basic_plan(novel, max_scenes=8):
    parts = [
        x.strip()
        for x in novel.replace("\r", "").split("\n\n")
        if x.strip()
    ]

    if not parts:
        parts = [novel.strip()]

    parts = parts[:max_scenes]

    scenes = []

    for i, text in enumerate(parts, 1):
        scenes.append({
            "id": i,
            "title": f"Scene {i}",
            "summary": text[:700],
            "characters": [],
            "dialogue": [],
            "visual_prompt": (
                "cinematic movie scene, realistic human movement, "
                "consistent characters, detailed environment, "
                "dramatic lighting: " + text[:1500]
            ),
            "status": "queued"
        })

    return {
        "title": "Novel Movie",
        "characters": [],
        "scenes": scenes
    }


def gemini_plan(novel, max_scenes):

    key = os.getenv("GEMINI_API_KEY", "").strip()

    if not key:
        return None

    prompt = f"""
You are a professional movie director and screenplay writer.

Read this novel carefully.

Create a coherent movie plan with no more than {max_scenes} scenes.

Keep characters visually consistent.

Preserve the original story.

Create natural dialogue.

Return JSON only:

{{
 "title": "",
 "characters": [
   {{
     "id": "c1",
     "name": "",
     "appearance": "",
     "voice": "my-MM-ThihaNeural"
   }}
 ],
 "scenes": [
   {{
     "id": 1,
     "title": "",
     "summary": "",
     "characters": ["c1"],
     "dialogue": [
       {{
         "character": "c1",
         "text": ""
       }}
     ],
     "visual_prompt": ""
   }}
 ]
}}

NOVEL:

{novel}
"""

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
        "?key=" + key
    )

    response = requests.post(
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

    response.raise_for_status()

    data = response.json()

    text = (
        data["candidates"][0]
        ["content"]["parts"][0]
        ["text"]
    )

    return json.loads(text)


# =========================
# PROJECT
# =========================

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


@app.post("/api/project")
async def create_project(
    novel: str = Form(...),
    max_scenes: int = Form(8)
):

    if not novel.strip():
        return JSONResponse(
            {"error": "ဝတ္ထုထည့်ပါ"},
            status_code=400
        )

    project_id = uuid.uuid4().hex[:10]

    folder = PROJECTS / project_id
    folder.mkdir(parents=True)

    plan = gemini_plan(
        novel,
        max_scenes
    )

    if not plan:
        plan = basic_plan(
            novel,
            max_scenes
        )

    save_json(
        folder / "plan.json",
        plan
    )

    save_json(
        folder / "state.json",
        {
            "id": project_id,
            "status": "ready",
            "progress": 0
        }
    )

    (
        folder / "novel.txt"
    ).write_text(
        novel,
        encoding="utf-8"
    )

    return {
        "id": project_id,
        "plan": plan
    }


@app.get(
    "/api/project/{project_id}"
)
def get_project(project_id: str):

    folder = PROJECTS / project_id

    if not folder.exists():

        return JSONResponse(
            {"error": "Project မတွေ့ပါ"},
            status_code=404
        )

    return {
        "state": load_json(
            folder / "state.json"
        ),
        "plan": load_json(
            folder / "plan.json"
        )
    }


# =========================
# WEB UI
# =========================

HTML = r"""
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
    background:#080b10;
    color:#fff;
    font-family:Arial,sans-serif;
}

.container{
    max-width:900px;
    margin:auto;
    padding:25px;
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
    min-height:350px;
    box-sizing:border-box;
    background:#090c12;
    color:white;
    border:1px solid #30394a;
    border-radius:12px;
    padding:15px;
    font-size:16px;
}

button{
    margin-top:15px;
    padding:14px 22px;
    border:0;
    border-radius:10px;
    background:white;
    color:#111;
    font-weight:bold;
    font-size:16px;
}

.scene{
    border:1px solid #30394a;
    border-radius:10px;
    padding:14px;
    margin-top:10px;
}

.small{
    color:#9ca6b8;
}

</style>

</head>

<body>

<div class="container">

<h1>🎬 Novel → Movie AI</h1>

<div class="card">

<h3>📖 ဝတ္ထု</h3>

<textarea
id="novel"
placeholder="ဝတ္ထုတစ်ပုဒ်လုံး ဒီမှာထည့်ပါ..."
></textarea>

<br>

<label>
Scene အများဆုံး
</label>

<input
id="scenes"
type="number"
value="8"
min="1"
max="30"
>

<br>

<button onclick="createProject()">
🚀 Create Movie Project
</button>

</div>

<div id="result"></div>

</div>


<script>

async function createProject(){

    const novel =
        document.getElementById(
            "novel"
        ).value;

    const scenes =
        document.getElementById(
            "scenes"
        ).value;

    if(!novel.trim()){

        alert("ဝတ္ထုထည့်ပါ");

        return;
    }

    const body =
        new URLSearch
