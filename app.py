import streamlit as st
import os
import asyncio
import edge_tts
import numpy as np
import requests
from io import BytesIO
from PIL import Image, ImageDraw
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

st.set_page_config(page_title="AI Dialogue Story Generator", layout="centered")

st.title("🎭 AI Dialogue Story Video Generator")

# 1. Theme ရွေးချယ်မှု
theme = st.selectbox(
    "🎨 ဇာတ်လမ်း Theme ရွေးချယ်ပါ-",
    ["Horror (သရဲ/ခြောက်ခြားဖွယ်)", "Fairytale (ပုံပြင်/သာယာဖွယ်)"]
)

# Microsoft Edge-TTS မြန်မာ/အင်္ဂလိပ် အသံများ
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

# 3. စကားပြော Dialogue ရေးရန် (မိနစ်အကန့်အသတ်မရှိ ထည့်နိုင်သည်)
st.write("📝 **စကားပြော Dialogue ရေးပါ** (တစ်ကြောင်းစီ အလှည့်ကျ ရေးပေးပါ) -")
default_text = """ဇာတ်ကောင် ၁: ဒီည တောအုပ်ထဲ မသွားနဲ့နော်။
ဇာတ်ကောင် ၂: ဘာဖြစ်လို့လဲ... ဘာရှိလို့လဲ။
ဇာတ်ကောင် ၁: အဲဒီမှာ ခြောက်ခြားစရာကောင်းတဲ့ သရဲရှိတယ်။
ဇာတ်ကောင် ၂: မင်းကလည်း ကြောက်စရာမလိုပါဘူး။
ဇာတ်ကောင် ၁: မဟုတ်ဘူး တကယ်ပြောတာ... မသွားနဲ့။
ဇာတ်ကောင် ၂: ကဲပါ... ငါဘာမှမဖြစ်ပါဘူး ကြည့်နေလိုက်။"""

dialogue_text = st.text_area("Dialogue List", value=default_text, height=220)

# Character ရုပ်ပုံများ
HORROR_CHAR1 = "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=500"
HORROR_CHAR2 = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500"
FAIRY_CHAR1 = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500"
FAIRY_CHAR2 = "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=500"

def load_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).convert("RGB")

async def generate_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

if st.button("🚀 ဗီဒီယို ဖန်တီးမည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        try:
            st.info("⏳ စကားပြော ရုပ်ပုံများနှင့် အသံများ ပေါင်းစပ်နေပါသည်။ ခဏစောင့်ပါ...")
            
            # Theme အလိုက် Image များ ဒေါင်းလုဒ်ဆွဲခြင်း
            if "Horror" in theme:
                c1_img = load_image_from_url(HORROR_CHAR1).resize((400, 400))
                c2_img = load_image_from_url(HORROR_CHAR2).resize((400, 400))
                bg_color = (15, 8, 20)
                border_color = (200, 30, 30)
            else:
                c1_img = load_image_from_url(FAIRY_CHAR1).resize((400, 400))
                c2_img = load_image_from_url(FAIRY_CHAR2).resize((400, 400))
                bg_color = (15, 30, 55)
                border_color = (235, 180, 40)

            clips = []
            total_duration = 0

            for index, line in enumerate(lines):
                clean_text = line
                if ":" in line:
                    clean_text = line.split(":", 1)[1].strip()
                elif "：" in line:
                    clean_text = line.split("：", 1)[1].strip()

                is_char2 = ("ဇာတ်ကောင် ၂" in line or "Character 2" in line)
                current_voice = voice2 if is_char2 else voice1

                # Audio
                audio_file = f"temp_audio_{index}.mp3"
                asyncio.run(generate_speech(clean_text, current_voice, audio_file))
                audio_clip = AudioFileClip(audio_file)
                total_duration += audio_clip.duration

                # Canvas & Image
                canvas = Image.new('RGB', (1080, 1920), color=bg_color)
                draw = ImageDraw.Draw(canvas)
                draw.rectangle([40, 40, 1040, 1880], outline=border_color, width=8)

                # Character Image paste
                if not is_char2:
                    canvas.paste(c1_img, (100, 600))
                    draw.rectangle([100, 600, 500, 1000], outline=(255, 255, 255), width=5)
                else:
                    canvas.paste(c2_img, (580, 600))
                    draw.rectangle([580, 600, 980, 1000], outline=(255, 255, 255), width=5)

                draw.rectangle([80, 1300, 1000, 1700], fill=(25, 15, 30) if "Horror" in theme else (20, 40, 75), outline=border_color, width=4)

                img_np = np.array(canvas)
                img_clip = ImageClip(img_np).set_duration(audio_clip.duration)
                seg_clip = img_clip.set_audio(audio_clip)
                clips.append(seg_clip)

            if clips:
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

                st.success(f"🎉 ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါသည်! (စုစုပေါင်း ကြာချိန်: {round(total_duration, 1)} စက္ကန့်)")
                st.video(output_path)

        except Exception as e:
            st.error(f"❌ Error ဖြစ်ပွားပါသည်: {str(e)}")
    else:
        st.warning("စကားပြော စာသားများ ထည့်သွင်းပါ။")
