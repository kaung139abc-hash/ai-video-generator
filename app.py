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
    "🎨 ဇာတ်လမ်း Theme ရွေးချယ်ပါ-",
    ["Horror (သရဲ/ခြောက်ခြားဖွယ်)", "Fairytale (ပုံပြင်/သာယာဖွယ်)"]
)

# Microsoft Edge-TTS အသံများ
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
st.write("📝 **စကားပြောပုံစံ ထည့်သွင်းပါ** -")
default_text = """ဇာတ်ကောင် ၁: ဒီည တောအုပ်ထဲ မသွားနဲ့နော်။
ဇာတ်ကောင် ၂: ဘာဖြစ်လို့လဲ... ဘာရှိလို့လဲ။
ဇာတ်ကောင် ၁: အဲဒီမှာ ခြောက်ခြားစရာကောင်းတဲ့ သရဲရှိတယ်။"""

dialogue_text = st.text_area("Dialogue List", value=default_text, height=200)

async def generate_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

if st.button("🚀 ဗီဒီယို ဖန်တီးမည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        try:
            st.info("⏳ စကားပြော ဗီဒီယို ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ...")
            clips = []
            total_duration = 0

            for index, line in enumerate(lines):
                # စကားပြောထဲမှ ရှေ့စာသားများ ရှင်းထုတ်ခြင်း
                clean_text = line
                if ":" in line:
                    clean_text = line.split(":", 1)[1].strip()
                elif "：" in line:
                    clean_text = line.split("：", 1)[1].strip()

                # ဇာတ်ကောင် ခွဲခြားခြင်း
                if "ဇာတ်ကောင် ၂" in line or "Character 2" in line:
                    current_voice = voice2
                    speaker_name = "CHARACTER 2"
                    is_char2 = True
                else:
                    current_voice = voice1
                    speaker_name = "CHARACTER 1"
                    is_char2 = False

                # ၁။ Edge-TTS ဖြင့် အသံဖိုင် ဖန်တီးခြင်း
                audio_file = f"temp_audio_{index}.mp3"
                asyncio.run(generate_speech(clean_text, current_voice, audio_file))
                
                audio_clip = AudioFileClip(audio_file)
                total_duration += audio_clip.duration

                if total_duration > 60:
                    st.warning("⚠️ စာသား ၁ မိနစ်ထက် ကျော်လွန်နေပါသည်။")
                    audio_clip.close()
                    break

                # ၂။ Visual Frame အလှဆင် ရေးဆွဲခြင်း
                bg_color = (15, 8, 20) if "Horror" in theme else (15, 30, 55)
                img = Image.new('RGB', (1080, 1920), color=bg_color)
                draw = ImageDraw.Draw(img)

                border_color = (200, 30, 30) if "Horror" in theme else (235, 180, 40)
                
                # အပြင်ဘက် ဘောင်
                draw.rectangle([40, 40, 1040, 1880], outline=border_color, width=8)

                # ဇာတ်ကောင် Avatar Icon ရေးဆွဲခြင်း (ဘယ်/ညာ အလှည့်ကျ ပြသရန်)
                if not is_char2:
                    # ဇာတ်ကောင် ၁ (ဘယ်ဘက်)
                    draw.ellipse([150, 600, 450, 900], fill=(220, 50, 50) if "Horror" in theme else (50, 120, 220), outline=(255,255,255), width=5)
                    draw.rectangle([500, 680, 950, 820], fill=(40, 20, 30) if "Horror" in theme else (30, 50, 90), outline=border_color, width=3)
                else:
                    # ဇာတ်ကောင် ၂ (ညာဘက်)
                    draw.ellipse([630, 600, 930, 900], fill=(160, 40, 200) if "Horror" in theme else (40, 180, 120), outline=(255,255,255), width=5)
                    draw.rectangle([130, 680, 580, 820], fill=(40, 20, 30) if "Horror" in theme else (30, 50, 90), outline=border_color, width=3)

                # အောက်ခြေ စကားပြော Subtitle Card Box
                draw.rectangle([80, 1300, 1000, 1700], fill=(25, 15, 30) if "Horror" in theme else (20, 40, 75), outline=border_color, width=4)

                # Frame အား NumPy Array ပြောင်း၍ MoviePy Clip လုပ်ခြင်း
                img_np = np.array(img)
                img_clip = ImageClip(img_np).set_duration(audio_clip.duration)
                seg_clip = img_clip.set_audio(audio_clip)
                clips.append(seg_clip)

            if clips:
                # ၃။ ဗီဒီယို ပေါင်းစည်းခြင်း
                final_video = concatenate_videoclips(clips)
                output_path = "story_dialogue_video.mp4"
                
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
