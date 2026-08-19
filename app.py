import streamlit as st
import requests
import asyncio
import aiohttp
import time

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

if st.button("🚀 AI 3D Video ထုတ်လုပ်မည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        st.info("⏳ AI မှ မျက်နှာနှင့် ပါးစပ် လှုပ်ရှားမှု ဖန်တီးနေပါသည်။...")
        results = asyncio.run(process_all_lines(lines, char1_p, char2_p))
        
        st.success("✨ ဗီဒီယိုများ ထွက်ရှိလာပါပြီ။")
        
        for idx, video_url, error in sorted(results, key=lambda x: x[0]):
            if video_url:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🎬 **Line {idx+1}:**")
                    st.video(video_url)
                with col2:
                    st.write(" ")
                    st.write(" ")
                    video_bytes = requests.get(video_url).content
                    st.download_button(
                        label=f"📥 Line {idx+1} Download",
                        data=video_bytes,
                        file_name=f"dialogue_line_{idx+1}.mp4",
                        mime="video/mp4",
                        key=f"dl_{idx}"
                    )
            else:
                st.error(f"Error in Line {idx+1}: {error}")
