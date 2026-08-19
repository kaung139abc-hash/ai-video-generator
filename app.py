import streamlit as st
import os
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import resize

st.set_page_config(page_title="AI Video Generator Pro", layout="centered")

st.title("🎬 AI Story Video Generator Pro")
st.subheader("၁ မိနစ်စာ ဗီဒီယိုနှင့် အသံအမျိုးအစားစုံ ဖန်တီးစနစ်")

# Sidebar - Setting များ
st.sidebar.header("⚙️ ဗီဒီယို ဆက်တင်များ")

# အသံ ရွေးချယ်မှု (gTTS accents သုံး၍ ကျား/မ လေသံ ပြောင်းလဲခြင်း)
voice_option = st.sidebar.selectbox(

    "🎙️ အသံအမျိုးအစား ရွေးချယ်ပါ-",
    [
        "မြန်မာ ပုံမှန်အသံ (Myanmar - Native)",
        "အမျိုးသားအသံ (English - US Male Accent)",
        "အမျိုးသမီးအသံ (English - UK Female Accent)",
        "အမျိုးသားအသံ (English - AU Male Accent)",
        "အမျိုးသမီးအသံ (English - IN Female Accent)"
    ]
)

# ဇာတ်လမ်း စာသား ထည့်သွင်းရန်
story_text = st.text_area(
    "📝 ဇာတ်လမ်း စာသား ထည့်သွင်းပါ (၁ မိနစ်စာအထိ ရေးသားနိုင်ပါသည်)-",
    height=150,
    value="ရှေးရှေးတုန်းက သာယာလှတဲ့ သစ်တောအုပ်ကြီးတစ်ခုထဲမှာ သတ္တိရှိတဲ့ ဝက်ဝံလေးတစ်ကောင် ရှိခဲ့ပါတယ်။"
)

if st.button("🚀 ဗီဒီယို စတင်ဖန်တီးမည်"):
    if story_text.strip():
        try:
            st.info("⏳ ဗီဒီယိုနှင့် အသံကို ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ...")

            # 1. အသံ ရွေးချယ်မှု စနစ်
            lang_code = 'my'
            tld_code = 'com'
            
            if "US Male" in voice_option:
                lang_code, tld_code = 'en', 'ca'
            elif "UK Female" in voice_option:
                lang_code, tld_code = 'en', 'co.uk'
            elif "AU Male" in voice_option:
                lang_code, tld_code = 'en', 'com.au'
            elif "IN Female" in voice_option:
                lang_code, tld_code = 'en', 'co.in'

            # 2. အသံဖိုင် စတင်ဖန်တီးခြင်း
            tts = gTTS(text=story_text, lang=lang_code, tld=tld_code, slow=False)
            audio_path = "generated_voice.mp3"
            tts.save(audio_path)

            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # 3. ၁ မိနစ် စည်းကမ်း စစ်ဆေးခြင်း
            if duration > 60:
                st.warning("⚠️ စာသား ရှည်လွန်းသဖြင့် ၁ မိနစ်ထက် ကျော်လွန်နေပါသည်။ စာသားကို နည်းနည်း တိုပေးပါ။")
                audio_clip.close()
            else:
                # 4. နောက်ခံပုံ ပြင်ဆင်ခြင်း
                image_path = "bg_frame.png"
                img = Image.new('RGB', (1080, 1920), color=(15, 20, 30))
                img.save(image_path)

                # 5. Video Clip ဖန်တီးခြင်း
                image_clip = ImageClip(image_path).set_duration(duration)
                image_clip = resize(image_clip, newsize=(1080, 1920))
                video_clip = image_clip.set_audio(audio_clip)

                # 6. ဗီဒီယို ထုတ်ယူခြင်း (Exporting)
                output_path = "final_story_video.mp4"
                video_clip.write_videofile(
                    output_path, 
                    fps=24, 
                    codec="libx264", 
                    audio_codec="aac"
                )

                # Clip များကို ပိတ်ခြင်း
                audio_clip.close()
                video_clip.close()

                st.success("🎉 ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါသည်!")
                st.video(output_path)

        except Exception as e:
            st.error(f"❌ Error ဖြစ်ပွားပါသည်: {str(e)}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသား ထည့်သွင်းပါ။")
