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

# 3D Cartoon Avatar Image များ (URL)
CHAR1_IMAGE = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500"
CHAR2_IMAGE = "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=500"

dialogue_text = st.text_area(
    "📝 စကားပြော Dialogue ရေးပါ (အင်္ဂလိပ် သို့မဟုတ် မြန်မာ)-",
    value="Character 1: Welcome to the story.\nCharacter 2: Let's start the adventure!",
    height=150
)

def create_talk(image_url, text):
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
        "source_url": image_url
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

if st.button("🚀 AI 3D Video ဖန်တီးမည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        st.info("⏳ AI မှ 3D Cartoon မျက်နှာနှင့် ပါးစပ် လှုပ်ရှားမှု ဖန်တီးနေပါသည်။...")
        for index, line in enumerate(lines):
            clean_text = line.split(":", 1)[1].strip() if ":" in line else line
            is_char2 = ("Character 2" in line or "ဇာတ်ကောင် ၂" in line)
            
            img_url = CHAR2_IMAGE if is_char2 else CHAR1_IMAGE
            
            res = create_talk(img_url, clean_text)
            st.write(f"Line {index+1} Result:", res)

st.write("💡 *Secrets ထဲတွင် ထည့်သွင်းထားသော D-ID API Key ကို သုံး၍ ဗီဒီယို ဖန်တီးပေးမည် ဖြစ်ပါသည်။*")
