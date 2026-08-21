import streamlit as st
import asyncio
import edge_tts
import os

st.title("🎙️ AI Voice Studio (Male/Female Options)")

# အသံစတိုင် ရွေးချယ်ခြင်း
# my-MM-ThihaNeural က ယောက်ျားအသံ၊ my-MM-NilarNeural က မိန်းမအသံ ဖြစ်ပါတယ်
voice_option = st.selectbox(
    "အသံစတိုင်ကို ရွေးပါ -",
    ["ယောက်ျားအသံ (Thiha)", "မိန်းမအသံ (Nilar)"]
)

# Voice Mapping
voice_map = {
    "ယောက်ျားအသံ (Thiha)": "my-MM-ThihaNeural",
    "မိန်းမအသံ (Nilar)": "my-MM-NilarNeural"
}

user_text = st.text_area("စာသားများ ရိုက်ထည့်ပါ -", "မင်္ဂလာပါ။ ကျွန်တော်က AI အသံဖိုင် စမ်းသပ်နေတာပါ။")

async def generate_audio(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
        with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            output_file = "output_audio/generated_voice.mp3"
            
            # Asyncio loop ကို Run ခြင်း
            try:
                asyncio.run(generate_audio(user_text, voice_map[voice_option], output_file))
                st.success("အသံဖိုင် ထွက်ရှိပါပြီ!")
                st.audio(output_file)
            except Exception as e:
                st.error(f"အမှားတစ်ခု ဖြစ်ပေါ်နေသည်: {e}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
