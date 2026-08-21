import streamlit as st
import asyncio
import edge_tts
import os

st.title("🎙️ AI Myanmar Voice Studio")

# မြန်မာယောက်ျားအသံ (Thiha) ကိုသာ သုံးပါမည်
user_text = st.text_area("စာသားများ ရိုက်ထည့်ပါ -", "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ...")

# Pitch ကို -40Hz အထိ ချလိုက်ပါ (ပိုနက်ပြီး လူကြီးသံဆန်သွားပါမယ်)
async def generate_deep_myanmar_voice(text, output_file):
    voice = "my-MM-ThihaNeural"
    communicate = edge_tts.Communicate(text, voice, pitch="-40Hz", rate="+0%")
    await communicate.save(output_file)

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
        with st.spinner("မြန်မာအသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/myanmar_deep.mp3"
            
            try:
                asyncio.run(generate_deep_myanmar_voice(user_text, output_file))
                st.success("အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
                st.audio(output_file)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
