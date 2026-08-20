import os
from moviepy import AudioFileClip, ImageClip, concatenate_audioclips
import requests
import streamlit as st

st.set_page_config(page_title="AI Horror Video Generator", page_icon="🎬")

st.title("🎬 AI Horror Movie Generator")
st.write("ElevenLabs အသံများဖြင့် ဇာတ်လမ်းဗီဒီယိုကို အလိုအလျောက် ထုတ်လုပ်ပေးသော စနစ်")

API_KEY = st.secrets.get("ELEVENLABS_API_KEY", "")

script_text = st.text_area(
    "📝 ဇာတ်လမ်းစာသား ထည့်ရန် (ဥပမာ - ကိုစိုး: ...)", height=150
)

if st.button("🚀 ဗီဒီယို စတင်ထုတ်လုပ်မည်"):
  if not script_text.strip():
    st.warning("ကျေးဇူးပြု၍ ဇာတ်လမ်းစာသား ထည့်သွင်းပေးပါ။")
  elif not API_KEY:
    st.error(
        "ကျေးဇူးပြု၍ ElevenLabs API Key ကို Streamlit Secrets တွင်"
        " ထည့်သွင်းပေးပါ။"
    )
  else:
    with st.spinner("အသံများနှင့် ဗီဒီယိုကို ဖန်တီးနေပါပြီ... ခဏစောင့်ပါ။"):
      lines = script_text.split("\n")
      audio_files = []

      # ElevenLabs ရဲ့ ပုံသေ Voice ID များ (Default English/Multilingual Voice)
      VOICE_ID = (
          "21m00Tcm4TlvDq8ikWAM"  # Rachel (Default working free voice)
      )

      success_count = 0
      for idx, line in enumerate(lines):
        if not line.strip():
          continue

        # စာသားသန့်စင်ခြင်း
        text_to_speak = line
        if ":" in line:
          text_to_speak = line.split(":", 1)[1].strip()

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": API_KEY,
        }
        data = {
            "text": text_to_speak,
            "model_id": "eleven_monolingual_v1",  # ပိုမို တည်ငြိမ်သော Model ကို သုံးထားသည်
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
          audio_path = f"line_{idx}.mp3"
          with open(audio_path, "wb") as f:
            f.write(response.content)
          audio_files.append(audio_path)
          success_count += 1
        else:
          st.error(f"API Error ({response.status_code}): {response.text}")

      if audio_files:
        try:
          audio_clips = [AudioFileClip(f) for f in audio_files]
          final_audio = concatenate_audioclips(audio_clips)
          final_audio_path = "final_audio.mp3"
          final_audio.write_audiofile(final_audio_path)

          img_url = "https://images.unsplash.com/photo-1509248961158-e54f6934749c?q=80&w=500&auto=format&fit=crop"
          img_data = requests.get(img_url).content
          img_path = "horror_bg.jpg"
          with open(img_path, "wb") as f:
            f.write(img_data)

          video_clip = ImageClip(img_path).with_duration(final_audio.duration)
          video_clip = video_clip.with_audio(final_audio)
          output_video = "final_horror_movie.mp4"
          video_clip.write_videofile(
              output_video, fps=24, codec="libx264", audio_codec="aac"
          )

          st.success("✅ ဗီဒီယို ထွက်ရှိလာပါပြီ!")
          st.video(output_video)
        except Exception as e:
          st.error(f"ဗီဒီယိုဖန်တီးရာတွင် အမှားဖြစ်သွားသည်: {e}")
      else:
        st.error(
            "အသံဖိုင် တစ်ခုမှ ထုတ်ယူ၍ မရပါ (API Key သို့မဟုတ် စာသားကို"
            " စစ်ဆေးပါ)"
        )
