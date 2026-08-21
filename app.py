import streamlit as st
import asyncio
import edge_tts
import os

st.title("🎙️ AI Voice Studio (Deep Male Voice)")

user_text = st.text_area("စာသားများ ရိုက်ထည့်ပါ -", "ကျွန်တော် အခု အသံနက်နက်နဲ့ ပြောနေပါပြီ။")

# Pitch ကို -10Hz လျှော့ချခြင်းဖြင့် အသံပိုနက်စေပါတယ်
async def generate_deep_audio(text, output_file):
    voice = "my-MM-ThihaNeural"
    communicate = edge_tts.Communicate(text, voice, pitch="-10Hz")
    await communicate.save(output_file)

if st.button("အသံနက်နက်နဲ့ ထုတ်မည်"):
    if user_text:
        with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/deep_voice.mp3"
            
            try:
                asyncio.run(generate_deep_audio(user_text, output_file))
                st.success("အသံဖိုင် ထွက်ရှိပါပြီ!")
                st.audio(output_file)
            except Exception as e:
                st.error(f"Error: {e}")
