import os
import streamlit as st
from gtts import gTTS

st.title("🎙️ AI Voice Studio")

# အသံစတိုင်ရွေးချယ်ခြင်း
voice_style = st.selectbox(
    "အသံစတိုင်ကို ရွေးပါ -",
    [
        "ပုံမှန်အသံ (Normal Voice)",
        "အဖိုးအို/အသံနက်စတိုင် (Deep/Slow Style)",
        "ဟောရာဆန်ဆန် ခြောက်ခြားစရာ (Horror Style)"
    ]
)

user_text = st.text_area("အသံထုတ်လိုသော စာသားများကို ရိုက်ထည့်ပါ -", "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ...")

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
        with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/generated_voice.mp3"
            
            # အဖိုးအို သို့မဟုတ် ဟောရာအတွက် slow (အသံနှေးပြီး လေသံလေးလေးနဲ့ ထွက်စေရန်) ကို အသုံးပြုခြင်း
            is_slow = True if "အဖိုးအို" in voice_style or "ဟောရာ" in voice_style else False
            
            # gTTS ဖြင့် အသံထုတ်ခြင်း
            tts = gTTS(text=user_text, lang='my', slow=is_slow)
            tts.save(output_file)
            
            st.success("အသံဖိုင် အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
            
            if "ဟောရာ" in voice_style:
                st.warning("👻 ဟောရာဆန်ဆန် ခြောက်ခြားဖွယ် လေသံဖြင့် ထုတ်ထားပါသည်။")
            elif "အဖိုးအို" in voice_style:
                st.info("👴 အသံနက်/အနှေး စတိုင်ဖြင့် ထုတ်ထားပါသည်။")
                
            st.audio(output_file)
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
