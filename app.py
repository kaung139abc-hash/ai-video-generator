import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="AI 3D Lip-Sync Story Generator", layout="centered")
st.title("🎭 AI 3D Cartoon Lip-Sync Video Generator")

# Streamlit Secrets ထဲမှ D-ID API Key ကို ရယူခြင်း
API_KEY = st.secrets.get("DID_API_KEY", "")

if not API_KEY:
    st.error("⚠️ Streamlit Secrets ထဲမှာ `DID_API_KEY` ရှာမတွေ့ပါ။ Secrets ထဲတွင် API Key သေချာ ထည့်သွင်းပေးပါ။")
    st.stop()

# D-ID Official Presenter IDs (3D Cartoons)
CHAR1_ID = "matt"
CHAR2_ID = "amy"

dialogue_text = st.text_area(
    "📝 စကားပြော Dialogue ရေးပါ (အင်္ဂလိပ် သို့မဟုတ် မြန်မာ)-",
    value="Character 1: Welcome to the story.\nCharacter 2: Let's start the adventure!",
    height=150
)

def create_talk_with_presenter(presenter_id, text):
    url = "https://api.d-id.com/talks"
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": "en-US-GuyNeural"}
        },
        "presenter_id": presenter_id
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def get_talk_status(talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {
        "Authorization": f"Basic {API_KEY}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

if st.button("🚀 AI 3D Video ဖန်တီးမည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        st.info("⏳ AI မှ မျက်နှာနှင့် ပါးစပ် လှုပ်ရှားမှု ဖန်တီးနေပါသည်။...")
        for index, line in enumerate(lines):
            clean_text = line.split(":", 1)[1].strip() if ":" in line else line
            is_char2 = ("Character 2" in line or "ဇာတ်ကောင် ၂" in line)
            
            p_id = CHAR2_ID if is_char2 else CHAR1_ID
            
            res = create_talk_with_presenter(p_id, clean_text)
            
            if "id" in res:
                talk_id = res["id"]
                st.write(f"🎬 Line {index+1} ဗီဒီယို ပြုလုပ်နေပါပြီ...")
                
                # Video processing ပြီးသည်အထိ စောင့်ကြည့်ခြင်း
                while True:
                    status_res = get_talk_status(talk_id)
                    status = status_res.get("status")
                    
                    if status == "done":
                        video_url = status_res.get("result_url")
                        st.video(video_url)
                        break
                    elif status == "error":
                        st.error(f"Line {index+1} ဖန်တီးရာတွင် အမှားအယွင်းရှိပါသည်: {status_res}")
                        break
                    
                    time.sleep(3)
            else:
                st.error(f"Error: {res}")

st.write("💡 *Secrets ထဲတွင် ထည့်သွင်းထားသော D-ID API Key ကို သုံး၍ ဗီဒီယို ဖန်တီးပေးမည် ဖြစ်ပါသည်။*")
