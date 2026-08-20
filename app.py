import streamlit as st
from gradio_client import Client
import tempfile
import os
import ffmpeg
import shutil
import asyncio
import edge_tts

st.set_page_config(page_title="3D AI Horror Video Studio", layout="centered")
st.title("👻 3D AI Horror Studio (Multi-Character)")
st.caption("✨ ဇာတ်ကောင် ၄ ယောက် (မြန်မာအမျိုးသား၊ အမျိုးသမီး၊ သရဲအသံနက်၊ သရဲမ ကွဲအက်အက်အသံ) ပါဝင်သော စနစ်")

# Voice Profiles with custom Pitch & Rate for Horror effects
VOICE_PROFILES = {
    "👨 မြန်မာ အမျိုးသား (Normal Male)": {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"},
    "👩 မြန်မာ အမျိုးသမီး (Normal Female)": {"voice": "my-MM-NilarNeural", "pitch": "+0Hz", "rate": "+0%"},
    "👻 သရဲ/မိစ္ဆာ အသံနက်ကြီး (Male Ghost)": {"voice": "my-MM-ThihaNeural", "pitch": "-35Hz", "rate": "-25%"},
    "🧟‍♀️ သရဲမ/စုန်းမ ကွဲအက်အက်အသံ (Female Ghost)": {"voice": "my-MM-NilarNeural", "pitch": "-25Hz", "rate": "-20%"},
    "💀 English Dark Horror Voice": {"voice": "en-US-ChristopherNeural", "pitch": "-15Hz", "rate": "-15%"},
}

st.subheader("🎬 Scene တစ်ခုစီအတွက် ဇာတ်ကောင်နှင့် စကားပြောများ ရွေးပါ")

scenes_input = []

# Create 4 Scenes for 4 Different Characters
for i in range(1, 5):
    with st.expander(f"📌 Scene {i} (ဇာတ်ကောင် {i} စကားပြောရန်)", expanded=(i<=2)):
        col1, col2 = st.columns(2)
        with col1:
            prompt = st.text_area(f"Scene {i} 3D Prompt (English):", 
                                  value=f"A 3D character scene {i}, cinematic lighting, horror movie style", 
                                  key=f"p_{i}", height=80)
            voice_choice = st.selectbox(f"Scene {i} အတွက် အသံရွေးပါ:", list(VOICE_PROFILES.keys()), index=(i-1)%4, key=f"v_{i}")
        with col2:
            speech_text = st.text_area(f"Scene {i} စကားပြော (မြန်မာ/English):", 
                                       value=f"ဒီမှာ စကားပြော ရေးပါ...", 
                                       key=f"t_{i}", height=120)
            
        scenes_input.append({
            "prompt": prompt,
            "text": speech_text,
            "voice_profile": VOICE_PROFILES[voice_choice]
        })

if st.button("🚀 ဇာတ်ကောင် ၄ မျိုးပါဝင်သော 3D Horror Video ဖန်တီးမည်"):
    temp_dir = tempfile.mkdtemp()
    merged_clips = []
    
    st.info("⏳ AI မှ Video Render ပြုလုပ်ခြင်းနှင့် အသံစနစ်များကို ပေါင်းစပ်နေပါသည်။...")
    progress_bar = st.progress(0)
    
    try:
        client = Client("fffiloni/CogVideoX-5B-Space")
        
        async def make_audio(text, profile, output_path):
            communicate = edge_tts.Communicate(
                text=text, 
                voice=profile["voice"], 
                pitch=profile["pitch"], 
                rate=profile["rate"]
            )
            await communicate.save(output_path)

        valid_scenes = [s for s in scenes_input if s["prompt"].strip() and s["text"].strip() and s["text"] != "ဒီမှာ စကားပြော ရေးပါ..."]
        
        if not valid_scenes:
            st.warning("အနည်းဆုံး Scene ၁ ခုတွင် စကားပြော စာသား ဖြည့်စွက်ပေးပါခင်ဗျာ။")
        else:
            for idx, item in enumerate(valid_scenes):
                st.write(f"🎬 Scene {idx+1}/{len(valid_scenes)} ကို ဖန်တီးနေပါသည်...")
                
                # 1. Render 3D Video
                video_raw = client.predict(prompt=item["prompt"], api_name="/generate")
                clip_video_path = os.path.join(temp_dir, f"v_{idx}.mp4")
                shutil.copy(video_raw, clip_video_path)
                
                # 2. Generate Audio with Pitch/Rate controls
                clip_audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(make_audio(item["text"], item["voice_profile"], clip_audio_path))
                
                # 3. Merge Video & Audio using FFmpeg
                scene_output_path = os.path.join(temp_dir, f"scene_{idx}_merged.mp4")
                video_in = ffmpeg.input(clip_video_path)
                audio_in = ffmpeg.input(clip_audio_path)
                
                ffmpeg.output(video_in, audio_in, scene_output_path, vcodec='copy', acodec='aac', shortest=None).run(overwrite_output=True, quiet=True)
                merged_clips.append(scene_output_path)
                
                progress_bar.progress(int(((idx + 1) / len(valid_scenes)) * 80))
                
            # 4. Concatenate All Scenes
            st.info("🎬 Scene အားလုံးကို ဗီဒီယို ၁ ပုဒ်တည်းဖြစ်အောင် ပေါင်းစပ်နေပါသည်...")
            list_file_path = os.path.join(temp_dir, "files.txt")
            with open(list_file_path, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
            
            final_video_path = os.path.join(temp_dir, "final_4person_horror.mp4")
            (
                ffmpeg
                .input(list_file_path, format='concat', safe=0)
                .output(final_video_path, c='copy')
                .run(overwrite_output=True, quiet=True)
            )
            
            progress_bar.progress(100)
            st.success("✨ ဇာတ်ကောင်စုံ အသံပါဝင်သော 3D Horror Video ရရှိပါပြီ။")
            st.video(final_video_path)
            
            with open(final_video_path, "rb") as f:
                st.download_button(
                    label="📥 MP4 Video ဒေါင်းလုဒ်ယူရန်",
                    data=f.read(),
                    file_name="3d_horror_4characters.mp4",
                    mime="video/mp4"
                )

    except Exception as e:
        st.error(f"Error တက်သွားပါသည်: {e}")
