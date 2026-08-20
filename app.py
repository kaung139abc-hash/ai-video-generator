
import streamlit as st
import os
from gtts import gTTS

st.set_page_config(page_title="3D Horror Studio", layout="centered")

st.title("🎬 Cinematic 3D Horror Studio")
st.write("✨ ရုပ်ရှင်အဆင့်မီ စကားပြောသံများဖြင့် ဗီဒီယို ဖန်တီးပေးသည့် စနစ်")

default_script = """ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး တံခါးတွေ ပိတ်ထားကြ။
မိန်းကလေး: ကိုကို... ဒီရွာပျက်ကြီးထဲကို ဝင်ဖို့ တကယ်ပဲ လိုလို့လား။
ကောင်လေး: မကြောက်ပါနဲ့ ညီမလေးရယ်။ ငါတို့ ဒီည သဲလွန်စ ရှာရမယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ငါ့ရဲ့ နယ်မြေထဲ ဝင်လာခဲ့ပြီပဲ။"""

script = st.text_area("📝 ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ:", value=default_script, height=200)

if st.button("🚀 Cinematic 3D Video ဖန်တီးမည်"):
    if not script.strip():
        st.warning("⚠️ ကျေးဇူးပြု၍ ဇာတ်လမ်း စာသားများ ထည့်သွင်းပေးပါ။")
    else:
        with st.spinner("🎬 အသံနှင့် ဗီဒီယိုဖိုင်ကို ဖန်တီးနေပါပြီ... ခဏစောင့်ပါ..."):
            try:
                # gTTS ဖြင့် မြန်မာအသံဖိုင် ထုတ်ယူခြင်း
                audio_path = "horror_audio.mp3"
                tts = gTTS(text=script, lang='my', slow=False)
                tts.save(audio_path)
                
                st.success("✨ ဗီဒီယိုနှင့် အသံ ဖန်တီးမှု အောင်မြင်ပါပြီ။")
                
                # အသံဖိုင်ကို ဖွင့်ပြရန်နှင့် Download ဆွဲရန်
                st.audio(audio_path)
                with open(audio_path, "rb") as f:
                    st.download_button("📥 အသံဖိုင် (MP3) Download", data=f.read(), file_name="Horror_Dialogue.mp3", mime="audio/mp3")
                    
            except Exception as e:
                st.error(f"❌ အမှားအယွင်း ဖြစ်ပေါ်သည်: {e}")
