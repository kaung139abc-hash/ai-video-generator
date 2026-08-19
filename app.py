import streamlit as st
import os
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip

st.title("🎬 AI Story Video Generator")

story_text = st.text_area(
    "ဇာတ်လမ်း စာသား ထည့်သွင်းပြီး AI ဗီဒီယို ဖန်တီးပါ -",
    "တောအုပ်တစ်ခုထဲမှာ ဝက်ဝံလေးတစ်ကောင် နို့ဆီဘူးတစ်ဘူး တွေ့သွားခဲ့တယ်။"
)

if st.button("🚀 ဗီဒီယို ဖန်တီးမည်"):
    if story_text.strip():
        try:
            st.info("ဗီဒီယို ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ...")

            # ၁။ အသံဖိုင် ဖန်တီးခြင်း
            tts = gTTS(text=story_text, lang='my')
            audio_path = "voice.mp3"
            tts.save(audio_path)

            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # ၂။ နောက်ခံ ပုံရိပ် ဖန်တီးခြင်း (PIL)
            image_path = "background.png"
            img = Image.new('RGB', (1080, 1920), color=(20, 20, 35))
            img.save(image_path)

            # ၃။ Video Clip ဖန်တီးခြင်း
            image_clip = ImageClip(image_path).set_duration(duration)
            video_clip = image_clip.set_audio(audio_clip)

            # ၄။ ဗီဒီယို ထုတ်ယူခြင်း
            output_path = "output_video.mp4"
            video_clip.write_videofile(
                output_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac"
            )

            audio_clip.close()
            video_clip.close()

            st.success("ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါသည်!")
            st.video(output_path)

        except Exception as e:
            st.error(f"Error ဖြစ်ပွားပါသည်: {str(e)}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသား ထည့်သွင်းပါ။")
