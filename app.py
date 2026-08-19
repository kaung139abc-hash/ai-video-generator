import streamlit as st
import os
from gtts import gTTS
from PIL import Image, ImageDraw
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

st.set_page_config(page_title="AI Dialogue Story Generator", layout="centered")

st.title("🎭 AI Dialogue Story Video Generator")

# 1. Theme ရွေးချယ်မှု
theme = st.selectbox(
    "🎨 ဇာတ်လမ်း Theme (ပုံစံ) ရွေးချယ်ပါ-",
    ["Horror (သရဲ/ခြောက်ခြားဖွယ်)", "Fairytale (ပုံပြင်/သာယာဖွယ်)"]
)

# 2. ဇာတ်ကောင်အသံ ရွေးချယ်မှု
col1, col2 = st.columns(2)
with col1:
    voice1 = st.selectbox("🎙️ ဇာတ်ကောင် (၁) အသံ:", ["Myanmar Native", "US Male Accent", "UK Female Accent"])
with col2:
    voice2 = st.selectbox("🎙️ ဇာတ်ကောင် (၂) အသံ:", ["UK Female Accent", "Myanmar Native", "AU Male Accent"])

# 3. စကားပြော Dialogue ရေးရန်
st.write("📝 **စကားပြောပုံစံ ထည့်သွင်းပါ** (တစ်ကြောင်းလျှင် တစ်ယောက် အလှည့်ကျ ရေးပါ) -")
default_text = "ဇာတ်ကောင် ၁: ဒီည တောအုပ်ထဲ မသွားနဲ့နော်။\nဇာတ်ကောင် ၂: ဘာဖြစ်လို့လဲ... ဘာရှိလို့လဲ။\nဇာတ်ကောင် ၁: အဲဒီမှာ ခြောက်ခြားစရာကောင်းတဲ့ သရဲရှိတယ်။"

dialogue_text = st.text_area("Dialogue List", value=default_text, height=180)

def get_gtts_config(voice_choice):
    if "US Male" in voice_choice:
        return 'en', 'ca'
    elif "UK Female" in voice_choice:
        return 'en', 'co.uk'
    elif "AU Male" in voice_choice:
        return 'en', 'com.au'
    return 'my', 'com'

if st.button("🚀 ဗီဒီယို ဖန်တီးမည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        try:
            st.info("⏳ စကားပြော ဗီဒီယို ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ...")
            clips = []

            for index, line in enumerate(lines):
                # ဇာတ်ကောင် ၁ သို့မဟုတ် ၂ ခွဲခြားခြင်း
                if "ဇာတ်ကောင် ၂" in line or "Character 2" in line:
                    speaker = "ဇာတ်ကောင် ၂"
                    lang, tld = get_gtts_config(voice2)
                else:
                    speaker = "ဇာတ်ကောင် ၁"
                    lang, tld = get_gtts_config(voice1)

                # ၁။ အသံဖိုင် ဖန်တီးခြင်း
                tts = gTTS(text=line, lang=lang, tld=tld, slow=False)
                audio_file = f"temp_audio_{index}.mp3"
                tts.save(audio_file)
                audio_clip = AudioFileClip(audio_file)

                # ၂။ Theme အလိုက် ဇာတ်ရုပ် Visual Background ဖန်တီးခြင်း
                img = Image.new('RGB', (1080, 1920), color=(10, 5, 10) if "Horror" in theme else (20, 35, 60))
                draw = ImageDraw.Draw(img)

                # Theme အလိုက် အလှဆင် ရောင်ခြည်/Border သတ်မှတ်ခြင်း
                border_color = (180, 20, 20) if "Horror" in theme else (230, 180, 50)
                draw.rectangle([50, 50, 1030, 1870], outline=border_color, width=10)

                img_file = f"temp_img_{index}.png"
                img.save(img_file)

                # ၃။ Video Segment ဖန်တီးခြင်း
                img_clip = ImageClip(img_file).set_duration(audio_clip.duration)
                seg_clip = img_clip.set_audio(audio_clip)
                clips.append(seg_clip)

            # ၄။ Segment အားလုံးကို တစ်ဆက်တည်း ပေါင်းစပ်ခြင်း
            final_video = concatenate_videoclips(clips)
            output_path = "story_dialogue_video.mp4"
            final_video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p"]
            )

            # ပိတ်ရန်
            for clip in clips:
                clip.close()

            st.success("🎉 ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါသည်!")
            st.video(output_path)

        except Exception as e:
            st.error(f"❌ Error ဖြစ်ပွားပါသည်: {str(e)}")
    else:
        st.warning("စကားပြော စာသားများ ထည့်သွင်းပါ။")
