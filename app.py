import streamlit as st
import requests
import time

st.set_page_config(page_title="AI 3D Lip-Sync Story Generator", layout="wide")
st.title("🎭 AI 3D Cartoon Lip-Sync Video Generator")

# Secrets ထဲမှ D-ID API Key ရယူခြင်း
API_KEY = st.secrets.get("DID_API_KEY", "")

if not API_KEY:
    st.error("⚠️ Streamlit Secrets ထဲတွင် `DID_API_KEY` ထည့်သွင်းပေးပါ။")
    st.stop()

# D-ID Official Presenter ID များ
PRESENTERS = {
    "Male 1 (Matt)": "matt",
    "Female 1 (Amy)": "amy",
    "Male 2 (Jack)": "jack",
    "Female 2 (Lori)": "lori"
}

# Sidebar - Settings & Features
st.sidebar.header("⚙️ Settings & Customization")

# Feature 1: Character Selector
st.sidebar.subheader("1. ဇာတ်ကောင် ရွေးချယ်ရန်")
char1_p = st.sidebar.selectbox("Character 1 ရွေးပါ-", list(PRESENTERS.keys()), index=0)
char2_p = st.sidebar.selectbox("Character 2 ရွေးပါ-", list(PRESENTERS.keys()), index=1)

# Feature 2: Voice & Language Settings
st.sidebar.subheader("2. အသံအမျိုးအစား ရွေးချယ်ရန်")
voice_option = st.sidebar.selectbox(
    "Voice Accent / Style ရွေးပါ-",
    [
        "en-US-GuyNeural (US Male)",
        "en-US-JennyNeural (US Female)",
        "en-GB-RyanNeural (UK Male)",
        "en-GB-SoniaNeural (UK Female)"
    ]
)
selected_voice = voice_option.split(" ")[0]

# Mode Selection
st.sidebar.subheader("3. Input Mode")
input_mode = st.sidebar.radio("Input အမျိုးအစား ရွေးပါ-", ["Text Dialogue (စာသား)", "Custom Audio Upload (MP3/WAV)"])

def create_talk_text(presenter_id, text, voice_id):
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
    return requests.post(url, json=payload, headers=headers).json()

def create_talk_audio(presenter_id, audio_url):
    url = "https://api.d-id.com/talks"
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "script": {
            "type": "audio",
            "audio_url": audio_url
        },
        "presenter_id": presenter_id
    }
    return requests.post(url, json=payload, headers=headers).json()

def get_talk_status(talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {API_KEY}"}
    return requests.get(url, headers=headers).json()

# Feature 5: Simple Dialogue Templates / Prompts
st.subheader("📝 Dialogue Input")

if input_mode == "Text Dialogue (စာသား)":
    # Quick Template Buttons
    col_t1, col_t2, col_t3 = st.columns(3)
    default_text = "Character 1: Welcome to the story.\nCharacter 2: Let's start the adventure!"
    
    if col_t1.button("💡 ဥပမာ - မိတ်ဆက် Dialogue"):
        st.session_state["dialogue"] = "Character 1: Hello! Welcome to our channel.\nCharacter 2: Hi everyone, don't forget to subscribe!"
    elif col_t2.button("💡 ဥပမာ - ဟာသ Dialogue"):
        st.session_state["dialogue"] = "Character 1: Why did the robot go on a diet?\nCharacter 2: I don't know, why?\nCharacter 1: Because it had too many bytes!"
    elif col_t3.button("💡 ဥပမာ - သတင်း / ဗဟုသုတ"):
        st.session_state["dialogue"] = "Character 1: Did you know AI is evolving fast?\nCharacter 2: Yes, it is making video creation super easy!"

    dialogue_input_val = st.session_state.get("dialogue", default_text)
    
    dialogue_text = st.text_area(
        "စကားပြော Dialogue ရေးပါ (Line တစ်ခုစီတွင် Character 1: သို့မဟုတ် Character 2: တင်ပေးပါ)-",
        value=dialogue_input_val,
        height=160
    )

    if st.button("🚀 AI 3D Video ဖန်တီးမည်"):
        lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
        
        if lines:
            st.info("⏳ AI မှ မျက်နှာနှင့် ပါးစပ် လှုပ်ရှားမှု ဖန်တီးနေပါသည်။ စက္ကန့် ၃၀ ခန့် စောင့်ပေးပါ...")
            
            for index, line in enumerate(lines):
                clean_text = line.split(":", 1)[1].strip() if ":" in line else line
                is_char2 = ("Character 2" in line or "ဇာတ်ကောင် ၂" in line)
                
                p_id = PRESENTERS[char2_p] if is_char2 else PRESENTERS[char1_p]
                
                res = create_talk_text(p_id, clean_text, selected_voice)
                
                if "id" in res:
                    talk_id = res["id"]
                    st.write(f"🎬 Line {index+1} ဗီဒီယို ပြုလုပ်နေပါပြီ...")
                    
                    while True:
                        status_res = get_talk_status(talk_id)
                        status = status_res.get("status")
                        
                        if status == "done":
                            video_url = status_res.get("result_url")
                            
                            # Video ပြသခြင်း
                            st.video(video_url)
                            
                            # Download Button ထည့်သွင်းခြင်း (Feature 3)
                            video_bytes = requests.get(video_url).content
                            st.download_button(
                                label=f"📥 Line {index+1} Video ဒေါင်းလုဒ်ရယူရန်",
                                data=video_bytes,
                                file_name=f"dialogue_line_{index+1}.mp4",
                                mime="video/mp4"
                            )
                            break
                        elif status == "error":
                            st.error(f"Line {index+1} Error တက်သွားပါသည်: {status_res}")
                            break
                        
                        time.sleep(3)
                else:
                    st.error(f"Error: {res}")

else:
    # Feature 4: Audio File URL / Upload Mode
    st.info("🎵 အသံဖိုင်ဖြင့် Lip-Sync ပြုလုပ်ရန် (Public Accessibility ရှိသော Audio Direct Link ကို ထည့်ပါ)")
    audio_url_input = st.text_input("Audio Direct URL (MP3/WAV Link)-", placeholder="https://example.com/audio.mp3")
    selected_char = st.selectbox("ဗီဒီယို ပြုလုပ်မည့် Character ရွေးပါ-", list(PRESENTERS.keys()))

    if st.button("🚀 Audio ဖြင့် Video ဖန်တီးမည်"):
        if audio_url_input:
            st.info("⏳ AI မှ အသံဖိုင်နှင့် နှုတ်ခမ်း လှုပ်ရှားမှု ချိတ်ဆက်နေပါသည်။...")
            p_id = PRESENTERS[selected_char]
            res = create_talk_audio(p_id, audio_url_input)
            
            if "id" in res:
                talk_id = res["id"]
                while True:
                    status_res = get_talk_status(talk_id)
                    status = status_res.get("status")
                    
                    if status == "done":
                        video_url = status_res.get("result_url")
                        st.video(video_url)
                        
                        video_bytes = requests.get(video_url).content
                        st.download_button(
                            label="📥 Video ဒေါင်းလုဒ်ရယူရန်",
                            data=video_bytes,
                            file_name="audio_lipsync_video.mp4",
                            mime="video/mp4"
                        )
                        break
                    elif status == "error":
                        st.error(f"Error တက်သွားပါသည်: {status_res}")
                        break
                    
                    time.sleep(3)
            else:
                st.error(f"Error: {res}")
        else:
            st.warning("⚠️ Audio URL ထည့်ပေးပါခင်ဗျာ။")

st.write("---")
st.caption("💡 *Secrets ထဲတွင် ထည့်သွင်းထားသော D-ID API Key ကို သုံး၍ ဗီဒီယို ဖန်တီးပေးမည် ဖြစ်ပါသည်။*")
