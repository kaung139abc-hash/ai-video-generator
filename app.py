import streamlit as st
import requests
import asyncio
import aiohttp
import time

st.set_page_config(page_title="AI 3D Lip-Sync Story Generator", layout="wide")
st.title("🎭 AI 3D Cartoon Lip-Sync Video Generator (Fast Mode)")

# Secrets ထဲမှ D-ID API Key ရယူခြင်း
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

st.sidebar.header("⚙️ Settings & Customization")
char1_p = st.sidebar.selectbox("Character 1 ရွေးပါ-", list(PRESENTERS.keys()), index=0)
char2_p = st.sidebar.selectbox("Character 2 ရွေးပါ-", list(PRESENTERS.keys()), index=1)

voice_option = st.sidebar.selectbox(
    "Voice Accent / Style ရွေးပါ-",
    ["en-US-GuyNeural (US Male)", "en-US-JennyNeural (US Female)", "en-GB-RyanNeural (UK Male)", "en-GB-SoniaNeural (UK Female)"]
)
selected_voice = voice_option.split(" ")[0]

input_mode = st.sidebar.radio("Input အမျိုးအစား ရွေးပါ-", ["Text Dialogue (စာသား)", "Custom Audio Upload (MP3/WAV)"])

# Async function for creating talk
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

# Async function to check status
async def async_get_talk_status(session, talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {API_KEY}"}
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def process_single_line(session, line, index, char1, char2, voice):
    clean_text = line.split(":", 1)[1].strip() if ":" in line else line
    is_char2 = ("Character 2" in line or "ဇာတ်ကောင် ၂" in line)
    p_id = PRESENTERS[char2] if is_char2 else PRESENTERS[char1]
    
    res = await async_create_talk(session, p_id, clean_text, voice)
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

async def process_all_lines(lines, char1, char2, voice):
    async with aiohttp.ClientSession() as session:
        tasks = [process_single_line(session, line, idx, char1, char2, voice) for idx, line in enumerate(lines)]
        return await asyncio.gather(*tasks)

st.subheader("📝 Dialogue Input")

if input_mode == "Text Dialogue (စာသား)":
    col_t1, col_t2, col_t3 = st.columns(3)
    default_text = "Character 1: Do you hear that strange voice?\nCharacter 2: Yes, run before it catches us!"
    
    if col_t1.button("💡 ဥပမာ - Horror Dialogue"):
        st.session_state["dialogue"] = "Character 1: Look at the mirror!\nCharacter 2: There is a shadow behind you!"
    elif col_t2.button("💡 ဥပမာ - ဟာသ Dialogue"):
        st.session_state["dialogue"] = "Character 1: Why did the robot go on a diet?\nCharacter 2: Because it had too many bytes!"
    elif col_t3.button("💡 ဥပမာ - မိတ်ဆက် Dialogue"):
        st.session_state["dialogue"] = "Character 1: Hello! Welcome to our channel.\nCharacter 2: Don't forget to subscribe!"

    dialogue_input_val = st.session_state.get("dialogue", default_text)
    dialogue_text = st.text_area("စကားပြော Dialogue ရေးပါ-", value=dialogue_input_val, height=150)

    if st.button("🚀 AI 3D Video အမြန်ထုတ်မည်"):
        lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
        
        if lines:
            progress_bar = st.progress(0)
            st.info("⚡ Parallel Processing စနစ်ဖြင့် စာကြောင်း အားလုံးကို ပြိုင်တူ Render လုပ်နေပါသည်။ ခဏစောင့်ပေးပါ...")
            
            # Run Async processing
            results = asyncio.run(process_all_lines(lines, char1_p, char2_p, selected_voice))
            progress_bar.progress(100)
            
            # Display videos in order
            for idx, video_url, error in sorted(results, key=lambda x: x[0]):
                st.write(f"🎬 **Line {idx+1} Result:**")
                if video_url:
                    st.video(video_url)
                    video_bytes = requests.get(video_url).content
                    st.download_button(
                        label=f"📥 Line {idx+1} Download",
                        data=video_bytes,
                        file_name=f"dialogue_line_{idx+1}.mp4",
                        mime="video/mp4"
                    )
                else:
                    st.error(f"Error in Line {idx+1}: {error}")
else:
    st.info("🎵 Audio Direct Link (MP3/WAV) ဖြင့် Lip-Sync ပြုလုပ်ရန်")
    audio_url_input = st.text_input("Audio Direct URL-", placeholder="https://example.com/audio.mp3")
    selected_char = st.selectbox("Character ရွေးပါ-", list(PRESENTERS.keys()))

    if st.button("🚀 Audio Video ဖန်တီးမည်"):
        if audio_url_input:
            st.info("⏳ Processing...")
            # Sync fallback for single audio
            url = "https://api.d-id.com/talks"
            headers = {"Authorization": f"Basic {API_KEY}", "Content-Type": "application/json"}
            payload = {"script": {"type": "audio", "audio_url": audio_url_input}, "presenter_id": PRESENTERS[selected_char]}
            res = requests.post(url, json=payload, headers=headers).json()
            
            if "id" in res:
                talk_id = res["id"]
                while True:
                    s_res = requests.get(f"https://api.d-id.com/talks/{talk_id}", headers={"Authorization": f"Basic {API_KEY}"}).json()
                    if s_res.get("status") == "done":
                        v_url = s_res.get("result_url")
                        st.video(v_url)
                        st.download_button("📥 Video Download", data=requests.get(v_url).content, file_name="audio_video.mp4", mime="video/mp4")
                        break
                    elif s_res.get("status") == "error":
                        st.error(f"Error: {s_res}")
                        break
                    time.sleep(2)
