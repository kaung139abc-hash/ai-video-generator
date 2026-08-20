import os
from moviepy import AudioFileClip, ImageClip, concatenate_audioclips
import requests
import streamlit as st

st.set_page_config(page_title="AI Horror Video Generator", page_icon="🎬")

st.title("🎬 AI Horror Movie Generator")
st.write("အမှားအယွင်းကင်းစင်သော ဇာတ်လမ်းနှင့် အသံဖိုင်များကို အလိုအလျောက် ထုတ်လုပ်ပေးသော စနစ်")

ELEVENLABS_API_KEY = st.secrets.get("ELEVENLABS_API_KEY", "")

default_script = "ကိုစိုး: အားလုံးပဲ မင်္ဂလာပါ။ ဒီညတော့ ကျုပ်တို့ရွာရဲ့ အနောက်ဘက်က ရှေးဟောင်းသုသာန်ဟောင်းကြီးထဲကို သွားရောက် စူးစမ်းကြမယ်။"

script_text = st.text_area("📝 ဇာတ်လမ်းစာသား ထည့်ရန်", value=default_script, height=150)

if st.button("🚀 ဗီဒီယို စတင်ထုတ်လုပ်မည်"):
    if not script_text.strip():
        st.warning("ကျေးဇူးပြု၍ ဇာတ်လမ်းစာသား ထည့်သွင်းပေးပါ။")
    elif not ELEVENLABS_API_KEY:
        st.error("ကျေးဇူးပြု၍ ElevenLabs API Key ကို Streamlit Secrets တွင် ထည့်သွင်းပေးပါ။")
    else:
        with st.spinner("အသံများနှင့် ဗီဒီယိုကို ဖန်တီးနေပါပြီ... ခဏစောင့်ပါ ⏳"):
            try:
                lines = script_text.split("\n")
                audio_files = []

                # Free plan အတွက် အလုပ်လုပ်သော Default Voice ID (Rachel)
                free_voice_id = "21m00Tcm4TlvDq8ikWAM"

                success_count = 0
                for idx, line in enumerate(lines):
                    if not line.strip():
                        continue

                    # ဇာတ်ကောင်ခွဲစရာမလိုဘဲ Free plan သုံးလို့ရမယ့် Default Voice ကိုသာ သုံးမည်
                    text_to_speech = line.split(":", 1)[1].strip() if ":" in line else line.strip()

                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{free_voice_id}"
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": ELEVENLABS_API_KEY
                    }
                    data = {
                        "text": text_to_speech,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                    }

                    response = requests.post(url, json=data, headers=headers)
                    if response.status_code == 200:
                        audio_path = f"line_{idx}.mp3"
                        with open(audio_path, "wb") as f:
                            f.write(response.content)
                        audio_files.append(audio_path)
                        success_count += 1
                    else:
                        st.error(f"ElevenLabs API Error ({response.status_code}): {response.text}")
                        break

                if audio_files and success_count == len([l for l in lines if l.strip()]):
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
                    video_clip.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")

                    st.success("✅ ဗီဒီယို ထွက်ရှိလာပါပြီ!")
                    st.video(output_video)
                else:
                    st.error("အသံဖိုင်များ ထုတ်ယူရာတွင် အဆင်မပြေမှု တချို့ရှိခဲ့ပါသည်။")

            except Exception as e:
                st.error(f"ဗီဒီယိုဖန်တီးရာတွင် မျှော်လင့်မထားသော အမှားဖြစ်သွားသည်: {e}")
