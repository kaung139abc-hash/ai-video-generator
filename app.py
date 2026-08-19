import streamlit as st
import os
import asyncio
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

st.set_page_config(page_title="AI Dialogue Story Generator", layout="centered")

st.title("🎭 AI Dialogue Story Video Generator")

# 1. Theme ရွေးချယ်မှု
theme = st.selectbox(
    "🎨 ဇာတ်လမ်း Theme (ပုံစံ) ရွေးချယ်ပါ-",
    ["Horror (သရဲ/ခြောက်ခြားဖွယ်)", "Fairytale (ပုံပြင်/သာယာဖွယ်)"]
)

# Microsoft Edge-TTS မြန်မာနှင့် အင်္ဂလိပ် အသံများ
VOICES = {
    "မြန်မာ အမျိုးသား (Thiha)": "my-MM-ThihaNeural",
    "မြန်မာ အမျိုးသမီး (Nilar)": "my-MM-NilarNeural",
    "အင်္ဂလိပ် အမျိုးသား (Guy - US)": "en-US-GuyNeural",
    "အမျိုးသမီး (Jenny - US)": "en-US-JennyNeural"
}

# 2. ဇာတ်ကောင်အသံ ရွေးချယ်မှု
col1, col2 = st.columns(2)
with col1:
    voice1_label = st.selectbox("🎙️ ဇာတ်ကောင် (၁) အသံ:", list(VOICES.keys()), index=0)
with col2:
    voice2_label = st.selectbox("🎙️ ဇာတ်ကောင် (၂) အသံ:", list(VOICES.keys()), index=1)

voice1 = VOICES[voice1_label]
voice2 = VOICES[voice2_label]

# 3. စကားပြော Dialogue ရေးရန်
st.write("📝 **စကားပြောပုံစံ ထည့်သွင်းပါ** (တစ်ကြောင်းလျှင် တစ်ယောက် အလှည့်ကျ ရေးပါ) -")
default_text = "ဇာတ်ကောင် ၁: ဒီည တောအုပ်ထဲ မသွားနဲ့နော်။\nဇာတ်ကောင် ၂: ဘာဖြစ်လို့လဲ... ဘာရှိလို့လဲ။\nဇာတ်ကောင် ၁: အဲဒီမှာ ခြောက်ခြားစရာကောင်းတဲ့ သရဲရှိတယ်။"

dialogue_text = st.text_area("Dialogue List", value=default_text, height=180)

async def generate_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

if st.button("🚀 ဗီဒီယို ဖန်တီးမည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        try:
            st.info("⏳ စကားပြော ဗီဒီယို ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ...")
            clips = []

            for index, line in enumerate(lines):
                # စကားပြောထဲမှ ရှေ့စာသားများ ရှင်းထုတ်ခြင်း
                clean_text = line
                if ":" in line:
                    clean_text = line.split(":", 1)[1].strip()
                elif "：" in line:
                    clean_text = line.split("：", 1)[1].strip()

                # ဇာတ်ကောင် ၁ သို့မဟုတ် ၂ အသံ ရွေးချယ်ခြင်း
                if "ဇာတ်ကောင် ၂" in line or "Character 2" in line:
                    current_voice = voice2
                    speaker_label = "ဇာတ်ကောင် ၂"
                else:
                    current_voice = voice1
                    speaker_label = "ဇာတ်ကောင် ၁"

                # ၁။ Edge-TTS ဖြင့် အသံဖိုင် ဖန်တီးခြင်း
                audio_file = f"temp_audio_{index}.mp3"
                asyncio.run(generate_speech(clean_text, current_voice, audio_file))
                
                audio_clip = AudioFileClip(audio_file)

                # ၂။ ပုံရိပ် ရောင်စုံ Frame ဖန်တီးခြင်း (NumPy array ပြောင်း၍ ရုပ်ထွက်သေချာစေရန်)
                bg_color = (15, 5, 20) if "Horror" in theme else (20, 40, 70)
                img = Image.new('RGB', (1080, 1920), color=bg_color)
                draw = ImageDraw.Draw(img)

                # ဘောင် အလှဆင်ခြင်း
                border_color = (200, 30, 30) if "Horror" in theme else (240, 190, 40)
                draw.rectangle([40, 40, 1040, 1880], outline=border_color, width=12)

                # Frame အား NumPy Array ပြောင်း၍ ImageClip ထဲ ထည့်ခြင်း
                img_np = np.array(img)
                img_clip = ImageClip(img_np).set_duration(audio_clip.duration)
                seg_clip = img_clip.set_audio(audio_clip)
                clips.append(seg_clip)

            # ၃။ ဗီဒီယို ပေါင်းစည်းခြင်း
            final_video = concatenate_videoclips(clips)
            output_path = "story_dialogue_video.mp4"
            
            # H.264 & YUV420p ထုတ်ယူခြင်း (ဖုန်း browser တိုင်းတွင် ရုပ်ရော အသံပါ ပေါ်စေသည်)
            final_video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p"]
            )

            for clip in clips:
                clip.close()

            st.success("🎉 ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါသည်!")
            st.video(output_path)

        except Exception as e:
            st.error(f"❌ Error ဖြစ်ပွားပါသည်: {str(e)}")
    else:
        st.warning("စကားပြော စာသားများ ထည့်သွင်းပါ။")
