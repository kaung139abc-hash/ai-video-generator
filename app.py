import os
import streamlit as st
from gtts import gTTS

st.title("🎙️ AI Voice Studio (Text-to-Speech)")

# အသံအမျိုးအစား ရွေးချယ်စရာများ
voice_style = st.selectbox(
    "အသံစတိုင်/အမျိုးအစားကို ရွေးပါ -",
    [
        "ပုံမှန် လူငယ်အသံ (Normal Youth)",
        "အဖိုးအိုအသံ (Deep/Old Man Style)",
        "ကလေးအသံ (High Pitch/Child Style)",
        "ဟောရာဆန်ဆန်/တစ္ဆေသံ (Horror/Creepy Style)",
        "မိန်းမကြီးအသံ (Mature Woman Style)"
    ]
)

user_text = st.text_area("အသံထုတ်လိုသော စာသားများကို ရိုက်ထည့်ပါ -", "မင်္ဂလာပါ၊ ဒါကတော့ အသံအမျိုးမျိုးပြောင်းနိုင်တဲ့ AI စနစ် ဖြစ်ပါတယ်။")

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
        with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/generated_voice.mp3"
            
            # အဖိုးအို သို့မဟုတ် ဟောရာအတွက် slow speed သုံးခြင်း
            is_slow = True if "အဖိုးအို" in voice_style or "ဟောရာ" in voice_style else False
            
            tts = gTTS(text=user_text, lang='my', slow=is_slow)
            tts.save(output_file)
            
            st.success("အသံဖိုင် အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
            
            if "ဟောရာ" in voice_style:
                st.warning("👻 ဟောရာဆန်ဆန် ခြောက်ခြားဖွယ် လေသံဖြင့် ထုတ်ထားပါသည်။")
            elif "အဖိုးအို" in voice_style:
                st.info("👴 အဖိုးအို လေသံစတိုင်ဖြင့် ထုတ်ထားပါသည်။")
                
            st.audio(output_file)
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
