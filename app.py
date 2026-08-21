import streamlit as st
import asyncio
import edge_tts
import os

st.title("🎙️ AI Storyteller Voice Studio (Edge-TTS)")

user_text = st.text_area("စာသားများ ရိုက်ထည့်ပါ -", "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ...")

# အသံကို ပိုပြီး နက်လာစေရန် နှင့် ဇာတ်လမ်းပြောသံဆန်စေရန် Pitch နှင့် Rate ကို ချိန်ညှိထားပါသည်
async def generate_story_audio(text, output_file):
    voice = "my-MM-ThihaNeural"
    # pitch="-30Hz" က အသံကို ပိုနက်စေပြီး၊ rate="-5%" က အသံကို အနည်းငယ်နှေးကွေးတည်ငြိမ်စေပါတယ် (ဇာတ်လမ်းပြောဖို့ အကောင်းဆုံး)
    communicate = edge_tts.Communicate(text, voice, pitch="-30Hz", rate="-5%")
    await communicate.save(output_file)

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
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
