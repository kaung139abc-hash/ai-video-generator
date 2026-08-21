import os
import streamlit as st
import asyncio
import edge_tts

st.title("🎙️ AI Storyteller & Novel Voice Studio")

user_text = st.text_area(
    "ဇာတ်လမ်း သို့မဟုတ် ဝတ္ထုစာသားများ ရိုက်ထည့်ပါ -",
    "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ..."
)

# ဇာတ်လမ်းပြောသံ ပုံစံထုတ်ပေးမည့် function
async def generate_story_audio(text, output_file):
    voice = "my-MM-ThihaNeural"
    # pitch ကို -30Hz ဖြင့် အသံနက်စေပြီး၊ rate ကို -5% ဖြင့် တည်ငြိမ်စေပါသည်
    communicate = edge_tts.Communicate(text, voice, pitch="-30Hz", rate="-5%")
    await communicate.save(output_file)

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text.strip():
        with st.spinner("ဇာတ်လမ်းအသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/story_voice.mp3"
            
            try:
                asyncio.run(generate_story_audio(user_text, output_file))
                st.success("အသံဖိုင် အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
                st.audio(output_file)
            except Exception as e:
                st.error(f"Error ဖြစ်ပေါ်သည်: {e}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
