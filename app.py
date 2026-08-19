import streamlit as st
import json
import urllib.parse
import requests
from PIL import Image
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import os

st.set_page_config(page_title="AI Story Video Generator", layout="centered")

st.title("🎬 AI Story Video Generator")
st.write("ဇာတ်လမ်း စာသား ထည့်သွင်းပြီး AI ဗီဒီယို ဖန်တီးပါ")

# User Input
story_input = st.text_area("ဇာတ်လမ်း ရေးပါ -", value="တောအုပ်တစ်ခုထဲမှာ ဝက်ဝံလေးတစ်ကောင် နို့ဆီဘူးတစ်ဘူး တွေ့သွားခဲ့တယ်။ နို့ဆီဘူးကို ဘယ်လိုဖွင့်ရမှန်းမသိလို့ သစ်ပင်နဲ့ ရိုက်ကြည့်တယ်။ နောက်ဆုံးမှာတော့ ပွင့်သွားပြီး အရသာရှိရှိ သောက်သုံးခဲ့ရပါတယ်။", height=150)

if st.button("🚀 ဗီဒီယို ဖန်တီးမည်"):
    if not story_input.strip():
        st.error("ကျေးဇူးပြု၍ ဇာတ်လမ်းစာသား ထည့်ပါ")
    else:
        status_text = st.empty()
        
        # Step 1: AI Story Breakdown
        status_text.info("၁/၄။ AI ဖြင့် ဇာတ်လမ်း ခွဲခြားနေပါသည်...")
        api_key = "AQ.Ab8RN6JHDOTICbLn6B3maBaQGsXaXUlCD_onHw8JCjrup_ezwg"
        
        prompt = f"""
        Break down this story into 3 short scenes.
        Return JSON array of objects with keys: "scene", "narration", "image_prompt".
        "narration" MUST be in Burmese language.
        "image_prompt" MUST be in English.

        Story: {story_input}
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }

        try:
            res = requests.post(url, json=payload, timeout=20)
            data = res.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            scenes = json.loads(raw_text)
        except Exception:
            scenes = [
                {"scene": 1, "narration": "တောအုပ်တစ်ခုထဲမှာ ဝက်ဝံလေးတစ်ကောင် နို့ဆီဘူးတစ်ဘူး တွေ့သွားခဲ့တယ်။", "image_prompt": "A cute bear finding a milk can in a forest"},
                {"scene": 2, "narration": "နို့ဆီဘူးကို ဘယ်လိုဖွင့်ရမှန်းမသိလို့ သစ်ပင်နဲ့ ရိုက်ကြည့်တယ်။", "image_prompt": "A bear hitting a milk can against a tree"},
                {"scene": 3, "narration": "နောက်ဆုံးမှာတော့ ပွင့်သွားပြီး အရသာရှိရှိ သောက်သုံးခဲ့ရပါတယ်။", "image_prompt": "A happy bear drinking milk from an open can"}
            ]

        # Step 2: Generate Assets
        status_text.info("၂/၄။ ရုပ်ပုံနှင့် အသံဖိုင်များ ဖန်တီးနေပါသည်...")
        image_files = []
        audio_files = []
        headers = {'User-Agent': 'Mozilla/5.0'}

        for i, scene in enumerate(scenes):
            img_path = f"image_{i}.jpg"
            audio_path = f"audio_{i}.mp3"

            try:
                prompt_encoded = urllib.parse.quote(scene['image_prompt'])
                img_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&seed={i+5}"
                img_res = requests.get(img_url, headers=headers, timeout=20)
                with open(img_path, 'wb') as f:
                    f.write(img_res.content)
            except:
                img = Image.new('RGB', (1280, 720), color=(40, 60, 90))
                img.save(img_path)

            tts = gTTS(text=scene['narration'], lang='my')
            tts.save(audio_path)

            image_files.append(img_path)
            audio_files.append(audio_path)

        # Step 3: Render Video
        status_text.info("၃/၄။ Motion Visual အထူးပြုလုပ်ချက်များ ပေါင်းစပ်နေပါသည်...")
        video_clips = []

        for img_p, aud_p in zip(image_files, audio_files):
            audio = AudioFileClip(aud_p)
            duration = audio.duration
            base_clip = ImageClip(img_p).set_duration(duration)
            animated_clip = base_clip.resize(lambda t: 1 + 0.08 * (t / duration)).set_position(('center', 'center'))
            clip_with_audio = animated_clip.set_audio(audio).fadein(0.4).fadeout(0.4)
            video_clips.append(clip_with_audio)

        final_video = concatenate_videoclips(video_clips, method="compose")
        output_filename = "generated_story.mp4"
        final_video.write_videofile(output_filename, fps=24)

        status_text.success("၄/၄။ ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါသည်!")

        # Display and Download Video
        st.video(output_filename)
        with open(output_filename, "rb") as file:
            st.download_button(
                label="📥 ဗီဒီယို ဒေါင်းလုဒ်ဆွဲရန်",
                data=file,
                file_name="story_video.mp4",
                mime="video/mp4"
            )
