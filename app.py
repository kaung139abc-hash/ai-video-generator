import streamlit as st
from gradio_client import Client
import tempfile
import os
import ffmpeg
import shutil
import asyncio
import edge_tts

st.set_page_config(page_title="3D AI Horror Video Studio", layout="centered")
st.title("👻 3D AI Horror Video Generator")
st.caption("✨ 3D Video + AI Horror Voice ကို အလိုအလျောက် အသံပေါင်းစပ်ပေးမည့် စနစ်")

st.subheader("📝 Scene များနှင့် ပြောမည့် စကားလုံးများ ရေးပါ")
st.info("Scene တစ်ခုစီအတွက် 3D Visual Prompt နှင့် ပါဝင်မည့် အသံ (Voiceover) ကို ရေးပေးပါ။")

# Default Horror Scenes Demo
default_scene_1 = "A 3D Pixar character walking in a creepy dark foggy forest with a flashlight, highly detailed"
default_voice_1 = "It is so dark here. I think someone is following me."

default_scene_2 = "The character stops and looks back nervously, a dark creepy shadow monster behind trees"
default_voice_2 = "Who is there? Please don't come close to me!"

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🎬 Scene 1 (Visual & Voice)**")
    s1_prompt = st.text_area("Scene 1 3D Prompt:", value=default_scene_1, height=100)
    s1_voice = st.text_area("Scene 1 စကားပြောအသံ (English):", value=default_voice_1, height=70)

with col2:
    st.markdown("**🎬 Scene 2 (Visual & Voice)**")
    s2_prompt = st.text_area("Scene 2 3D Prompt:", value=default_scene_2, height=100)
    s2_voice = st.text_area("Scene 2 စကားပြောအသံ (English):", value=default_voice_2, height=70)

voice_style = st.selectbox("🎙️ AI Horror အသံအမျိုးအစား ရွေးပါ-", [
    "en-US-ChristopherNeural (Dark/Horror Tone)",
    "en-US-GuyNeural (Male Tone)",
    "en-US-JennyNeural (Female Tone)"
])
selected_voice = voice_style.split(" ")[0]

if st.button("🚀 အသံပါဝင်သော 3D Horror Video အပြီးသတ် ဖန်တီးမည်"):
    scenes_data = [
        {"prompt": s1_prompt, "voice": s1_voice},
        {"prompt": s2_prompt, "voice": s2_voice}
    ]
    
    temp_dir = tempfile.mkdtemp()
    merged_clips = []
    
    st.info("⏳ AI မှ Video Render ပြုလုပ်ခြင်းနှင့် Horror Voice ထည့်သွင်းခြင်းများကို လုပ်ဆောင်နေပါသည်။...")
    progress_bar = st.progress(0)
    
    try:
        client = Client("ZeroGPU-Explorers/Text-to-Video")
        
        async def make_audio(text, output_path):
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(output_path)

        for idx, item in enumerate(scenes_data):
            if not item["prompt"].strip():
                continue
                
            st.write(f"🎬 Scene {idx+1} ကို လုပ်ဆောင်နေပါသည်...")
            
            # 1. Generate 3D Video
            video_raw = client.predict(prompt=item["prompt"], api_name="/generate")
            clip_video_path = os.path.join(temp_dir, f"v_{idx}.mp4")
            shutil.copy(video_raw, clip_video_path)
            
            # 2. Generate Audio
            clip_audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
            if item["voice"].strip():
                asyncio.run(make_audio(item["voice"], clip_audio_path))
            
            # 3. Merge Video + Audio for this Scene using FFmpeg
            scene_output_path = os.path.join(temp_dir, f"scene_{idx}_merged.mp4")
            
            video_in = ffmpeg.input(clip_video_path)
            if item["voice"].strip() and os.path.exists(clip_audio_path):
                audio_in = ffmpeg.input(clip_audio_path)
                # Combine video and audio, shortest duration
                ffmpeg.output(video_in, audio_in, scene_output_path, vcodec='copy', acodec='aac', shortest=None).run(overwrite_output=True, quiet=True)
            else:
                shutil.copy(clip_video_path, scene_output_path)
                
            merged_clips.append(scene_output_path)
            progress_bar.progress(int(((idx + 1) / len(scenes_data)) * 80))
            
        # 4. Concatenate all merged scenes into Final Full Video
        st.info("🎬 Scene အားလုံးကို ဗီဒီယို ၁ ပုဒ်တည်းဖြစ်အောင် အချောသတ် ပေါင်းစပ်နေပါသည်။...")
        
        list_file_path = os.path.join(temp_dir, "files.txt")
        with open(list_file_path, "w") as f:
            for mc in merged_clips:
                f.write(f"file '{mc}'\n")
        
        final_video_path = os.path.join(temp_dir, "final_horror_movie.mp4")
        (
            ffmpeg
            .input(list_file_path, format='concat', safe=0)
            .output(final_video_path, c='copy')
            .run(overwrite_output=True, quiet=True)
        )
        
        progress_bar.progress(100)
        st.success("✨ Horror အသံပါဝင်သော 3D Video အပြည့်အစုံ ထွက်ရှိလာပါပြီ။")
        
        st.video(final_video_path)
        
        with open(final_video_path, "rb") as f:
            st.download_button(
                label="📥 Horror MP4 Video ဒေါင်းလုဒ်ယူရန်",
                data=f.read(),
                file_name="3d_horror_story.mp4",
                mime="video/mp4"
            )

    except Exception as e:
        st.error(f"Error တက်သွားပါသည်: {e}")
