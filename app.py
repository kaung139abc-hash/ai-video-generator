import streamlit as st
import requests
import asyncio
import aiohttp
import time
import tempfile
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

st.set_page_config(page_title="AI 3D Lip-Sync Story Generator", layout="wide")
st.title("🎭 AI 3D Cartoon Lip-Sync Video Generator")

API_KEY = st.secrets.get("DID_API_KEY", "")

if not API_KEY:
    st.error("⚠️ Streamlit Secrets ထဲတွင် `DID_API_KEY` ထည့်သွင်းပေးပါ။")
    st.stop()

PRESENTERS = {
    "Male 1 (Matt)": "matt",
    "Female 1 (Amy)": "amy",
    "Male 2 (Jack)": "jack",
    "Female 2 (Lori)": "lori"
}

st.sidebar.header("⚙️ Settings")
char1_p = st.sidebar.selectbox("Character 1 (Male/Female) ရွေးပါ-", list(PRESENTERS.keys()), index=0)
char2_p = st.sidebar.selectbox("Character 2 (Male/Female) ရွေးပါ-", list(PRESENTERS.keys()), index=1)

async def async_create_talk(session, presenter_id, text, voice_id):
    url = "https://api.d-id.com/talks"
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": voice_id}
        },
        "presenter_id": presenter_id
    }
    async with session.post(url, json=payload, headers=headers) as response:
        return await response.json()

async def async_get_talk_status(session, talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {API_KEY}"}
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def process_single_line(session, line, index, char1, char2):
    clean_text = line.split(":", 1)[1].strip() if ":" in line else line
    is_char2 = ("Character 2" in line or "ဇာတ်ကောင် ၂" in line)
    
    selected_char = char2 if is_char2 else char1
    p_id = PRESENTERS[selected_char]
    
    # အမျိုးသမီး / အမျိုးသား အသံ ခွဲခြားခြင်း
    if "Female" in selected_char or "Amy" in selected_char or "Lori" in selected_char:
        voice_id = "en-US-JennyNeural"
    else:
        voice_id = "en-US-GuyNeural"

    res = await async_create_talk(session, p_id, clean_text, voice_id)
    if "id" in res:
        talk_id = res["id"]
        while True:
            status_res = await async_get_talk_status(session, talk_id)
            if status_res.get("status") == "done":
                return index, status_res.get("result_url"), None
            elif status_res.get("status") == "error":
                return index, None, status_res
            await asyncio.sleep(2)
    else:
        return index, None, res

async def process_all_lines(lines, char1, char2):
    async with aiohttp.ClientSession() as session:
        tasks = [process_single_line(session, line, idx, char1, char2) for idx, line in enumerate(lines)]
        return await asyncio.gather(*tasks)

st.subheader("📝 Dialogue Input")
default_text = "Character 1: Do you hear that strange voice?\nCharacter 2: Yes, run before it catches us!"
dialogue_text = st.text_area("စကားပြော Dialogue ရေးပါ-", value=default_text, height=150)

if st.button("🚀 ဗီဒီယို တစ်ပုဒ်တည်း ပေါင်းထုတ်မည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        st.info("⏳ AI မှ ဗီဒီယိုဖိုင်များကို ထုတ်လုပ်နေပါသည်။...")
        results = asyncio.run(process_all_lines(lines, char1_p, char2_p))
        
        video_urls = [res[1] for res in sorted(results, key=lambda x: x[0]) if res[1]]
        
        if len(video_urls) == len(lines):
            st.info("🎬 ဗီဒီယိုများကို တစ်ပုဒ်တည်း ဖြစ်အောင် ပေါင်းစပ်နေပါသည်...")
            
            temp_files = []
            clips = []
            
            try:
                # ဒေါင်းလုဒ်ဆွဲပြီး တစ်ပေါင်းတည်း ဆက်ခြင်း
                for url in video_urls:
                    r = requests.get(url)
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tf.write(r.content)
                    tf.close()
                    temp_files.append(tf.name)
                    clips.append(VideoFileClip(tf.name))
                
                final_clip = concatenate_videoclips(clips)
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
                
                # ပြသခြင်းနှင့် ဒေါင်းလုဒ်ပေးခြင်း
                st.success("✨ ဗီဒီယို ပေါင်းစပ်မှု အောင်မြင်ပါသည်။")
                st.video(output_path)
                
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 ဗီဒီယိုအပြည့်အစုံ ဒေါင်းလုဒ်ရယူရန်",
                        data=f.read(),
                        file_name="full_combined_story.mp4",
                        mime="video/mp4"
                    )
            finally:
                # Temp ဖိုင်များ ရှင်းလင်းခြင်း
                for clip in clips:
                    clip.close()
                for tf_path in temp_files:
                    if os.path.exists(tf_path):
                        os.remove(tf_path)
        else:
            st.error("ဗီဒီယို အချို့ ထုတ်လုပ်ရာတွင် Error တက်သွားပါသည်။")
