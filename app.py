import os
import streamlit as st
import requests

st.title("🎙️ AI Voice Studio (ElevenLabs Free Tier)")

API_KEY = "sk_d7d126e55b9b5970c5606ffab6f5f69e9d4b4c1e888795ef"

# Free Account API ဖြင့် သုံးလို့ရသော Default Voice IDs များ (Adam နှင့် Rachel)
voice_options = {
    "Adam (ယောက်ျားအသံ)": "pNInz6obpgDQGcFmaJgB",
    "Rachel (မိန်းမအသံ)": "21m00Tcm4TlvDq8ikWAM"
}

selected_voice_name = st.selectbox("အသံစတိုင်ကို ရွေးပါ -", list(voice_options.keys()))
voice_id = voice_options[selected_voice_name]

user_text = st.text_area("စာသားများ ရိုက်ထည့်ပါ -", "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ...")

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
        with st.spinner("ElevenLabs ဖြင့် အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/elevenlabs_voice.mp3"
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": API_KEY
            }
            
            data = {
                "text": user_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                st.success("အသံဖိုင် အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
                st.audio(output_file)
            else:
                st.error(f"Error ဖြစ်ပေါ်သည်: {response.text}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
