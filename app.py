import os
import streamlit as st
import asyncio
import edge_tts

st.title("🎬 Novel → Movie & Voice AI (Streamlit)")

user_text = st.text_area(
    "ဝတ္ထု (သို့မဟုတ်) ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ -",
    "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ..."
)

max_scenes = st.slider("Scene အများဆုံး ခွဲမည်", min_value=1, max_value=10, value=3)

# ဇာတ်လမ်းကို အပိုင်းလိုက် (Scenes) ခွဲထုတ်ပေးသည့် ဖန်ရှင်
def basic_plan(novel, max_s):
    parts = [x.strip() for x in novel.replace("\r", "").split("\n\n") if x.strip()]
    if not parts:
        parts = [novel.strip()]
    parts = parts[:max_s]
    
    scenes = []
    for i, text in enumerate(parts, 1):
        scenes.append({
            "id": i,
            "title": f"Scene {i}",
            "summary": text,
        })
    return scenes

# အသံထုတ်ပေးသည့် ဖန်ရှင် (Edge-TTS - Thiha အသံနက်)
async def generate_audio(text, output_file):
    voice = "my-MM-ThihaNeural"
    communicate = edge_tts.Communicate(text, voice, pitch="-30Hz", rate="-5%")
    await communicate.save(output_file)

if st.button("🚀 ဇာတ်လမ်းနှင့် အသံဖိုင် ဖန်တီးမည်"):
    if user_text.strip():
        with st.spinner("ဇာတ်လမ်းကို Scene များ ခွဲထုတ်နေပါပြီ..."):
            scenes = basic_plan(user_text, max_scenes)
            
            st.success("အောင်မြင်သည်!")
            
            # Scene တစ်ခုချင်းစီကို ပြသပေးခြင်း
            for scene in scenes:
                st.markdown(f"### 📌 {scene['title']}")
                st.write(scene['summary'])
                
                # Scene တစ်ခုချင်းအတွက် အသံဖိုင်ထုတ်ရန်
                output_file = f"output_scene_{scene['id']}.mp3"
                try:
                    asyncio.run(generate_audio(scene['summary'], output_file))
                    st.audio(output_file)
                except Exception as e:
                    st.error(f"အသံထုတ်ရာတွင် Error ဖြစ်သည်: {e}")
                st.divider()
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
