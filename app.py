import streamlit as st
import os
import asyncio
import edge_tts
import replicate

st.set_page_config(page_title="Multi-Voice AI Video Generator", page_icon="🎬", layout="centered")

st.title("🎬 Multi-Voice & Character AI Video Generator")
st.write("ဇာတ်ကောင်အလိုက် မတူညီသော အသံများကို အလိုအလျောက် ခွဲထုတ်၍ ဗီဒီယိုဖန်တီးရန်")

# API Token
api_key = st.text_input("Replicate API Token ထည့်ပါ:", type="password")

# ဇာတ်ကောင်များနှင့် အသံအမျိုးအစားများ သတ်မှတ်ခြင်း
st.markdown("### 🎙️ ဇာတ်ကောင်များ၏ အသံပုံစံများ")
col1, col2 = st.columns(2)
with col1:
    char_1_voice = st.selectbox("ဇာတ်ကောင် ၁ အသံ", ["my-MM-ThihaNeural (အသံနက်/ကျား)", "my-MM-NilarNeural (အသံသွက်/မ)"])
with col2:
    char_2_voice = st.selectbox("ဇာတ်ကောင် ၂ အသံ", ["my-MM-NilarNeural (အသံသွက်/မ)", "my-MM-ThihaNeural (အသံနက်/ကျား)"])

# ဇာတ်လမ်းစာသား ထည့်သွင်းရန်
script_input = st.text_area(
    "ဇာတ်လမ်းစာသား ရိုက်ထည့်ပါ (ပုံစံ: ဇာတ်ကောင် ၁: မင်္ဂလာပါ / ဇာတ်ကောင် ၂: ဟယ်လိုပါ)",
    "ဇာတ်ကောင် ၁: ဟေ့လူ၊ ဒီဘက်ကို ခဏလာခဲ့ပါဦး။\nဇာတ်ကောင် ၂: ဘာဖြစ်လို့လဲ၊ ဘာကိစ္စရှိလို့လဲဗျ။"
)

char_image = st.file_uploader("ဇာတ်ကောင် ပုံတင်ရန် (JPG / PNG)", type=["jpg", "png"])

# အသံထုတ်ပေးသည့် ဖန်ရှင်
async def generate_single_audio(text, voice_name, filename):
    v_id = "my-MM-ThihaNeural" if "Thiha" in voice_name else "my-MM-NilarNeural"
    communicate = edge_tts.Communicate(text, v_id)
    await communicate.save(filename)

if st.button("🚀 အသံနှင့် ဗီဒီယို တစ်ခါတည်း ထုတ်မည်"):
    if script_input and char_image and api_key:
        os.makedirs("temp", exist_ok=True)
        os.environ["REPLICATE_API_TOKEN"] = api_key
        
        lines = script_input.split('\n')
        audio_files = []
        
        with st.spinner("အသံဖိုင်များကို တစ်ကြောင်းချင်းစီ ဖန်တီးနေပါပြီ..."):
            for i, line in enumerate(lines):
                if ":" in line:
                    actor, text = line.split(":", 1)
                    actor_name = actor.strip()
                    
                    if "၁" in actor_name:
                        selected_voice = char_1_voice
                    else:
                        selected_voice = char_2_voice
                        
                    file_name = f"temp/audio_{i}.mp3"
                    asyncio.run(generate_single_audio(text.strip(), selected_voice, file_name))
                    audio_files.append(file_name)
        
        if audio_files:
            with st.spinner("အသံဖိုင်များကို ပေါင်းစပ်နေပါပြီ..."):
                final_audio_path = "temp/final_audio.mp3"
                # pydub မသုံးဘဲ binary အနေနဲ့ အသံဖိုင်တွေကို တိုက်ရိုက်ဆက်ခြင်း
                with open(final_audio_path, "wb") as outfile:
                    for f_name in audio_files:
                        with open(f_name, "rb") as infile:
                            outfile.write(infile.read())
                            
                st.audio(final_audio_path)
            
            image_path = os.path.join("temp", char_image.name)
            with open(image_path, "wb") as f:
                f.write(char_image.getbuffer())
                
            with st.spinner("AI ဇာတ်ကောင် စကားပြောဗီဒီယိုကို ဖန်တီးနေပါပြီ (ခေတ္တစောင့်ပါ)..."):
                try:
                    with open(image_path, "rb") as img_file, open(final_audio_path, "rb") as aud_file:
                        output = replicate.run(
                            "fauconbarbarian/sadtalker:3aa3dac9353cc4d6bd62a8f959573847893d8efa704a529364b68e63a89069d3",
                            input={
                                "source_image": img_file,
                                "driven_audio": aud_file,
                                "still": True,
                                "enhancer": "gfpgan"
                            }
                        )
                    
                    if output:
                        st.success("🎉 အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!")
                        st.video(output)
                        st.markdown(f"[📥 ဗီဒီယိုဖိုင်ကို Download ရယူရန်]({output})")
                        
                except Exception as e:
                    st.error(f"Error ဖြစ်ပွားသည်: {e}")
        else:
            st.warning("စာသားဖော်မတ် မှန်ကန်မှု မရှိပါ။ (ဥပမာ - ဇာတ်ကောင် ၁: စာသား)")
    else:
        st.warning("ကျေးဇူးပြု၍ API Token၊ စာသားနှင့် ပုံကို အပြည့်အစုံ ဖြည့်ပေးပါ။")
