import streamlit as st
from gradio_client import Client
import tempfile
import os
import ffmpeg
import shutil
import asyncio
import edge_tts

st.set_page_config(page_title="Free 3D AI Video Studio", layout="centered")
st.title("🎬 100% Free 3D Multi-Scene Video Studio")
st.caption("✨ Scene များစွာကို အလိုအလျောက် Render လုပ်ပြီး ၁ မိနစ်စာ ဗီဒီယို ပေါင်းထုတ်ပေးမည့် စနစ်")

tab1, tab2 = st.tabs(["🎥 3D Multi-Scene Video (၁ မိနစ်စာ)", "🔊 Free AI Voice"])

# ---------------------------------------------------------
# TAB 1: Multi-Scene 3D Motion Video Generator
# ---------------------------------------------------------
with tab1:
    st.subheader("📝 3D Scene မူကွဲများ ရေးပါ")
    st.info("Scene တစ်ခုလျှင် စကြောင်းတစ်ကြောင်းစီ ခွဲရေးပါ။ AI က Scene တစ်ခုချင်းစီကို အခမဲ့ Render လုပ်ပြီး ၁ မိနစ်စာ ဗီဒီယိုဖြစ်အောင် ပေါင်းပေးပါမည်။")
    
    default_scenes = (
        "Scene 1: A 3D Pixar style character walking in a creepy dark forest with a flashlight\n"
        "Scene 2: The character hears a scary noise, looking around nervously, dark atmosphere\n"
        "Scene 3: A shadow monster appears behind the trees, dramatic cinematic lighting\n"
        "Scene 4: The 3D character runs away very fast, panicked expression, smooth animation\n"
        "Scene 5: The character safely enters a safe wooden house and breathes heavily"
    )
    
    scene_text = st.text_area("Scenes ရေးပါ (တစ်ကြောင်းလျှင် Scene ၁ ခု):", value=default_scenes, height=150)
    
    if st.button("🚀 ၁ မိနစ်စာ 3D Video အပြီး ပေါင်းထုတ်မည်"):
        scenes = [line.strip() for line in scene_text.strip().split("\n") if line.strip()]
        
        if not scenes:
            st.warning("Scene ရေးသားပေးပါခင်ဗျာ။")
        else:
            temp_dir = tempfile.mkdtemp()
            video_files = []
            
            st.info("⏳ Scene များကို တစ်ခုပြီးတစ်ခု Render လုပ်နေပါသည်။ ခဏစောင့်ပေးပါ...")
            progress_bar = st.progress(0)
            
            try:
                client = Client("ZeroGPU-Explorers/Text-to-Video")
                
                for idx, prompt in enumerate(scenes):
                    st.write(f"🎬 Scene {idx+1}/{len(scenes)} ကို ရိုက်ကူးနေပါသည်...")
                    
                    # Hugging Face Free Text-to-Video Call
                    result = client.predict(prompt=prompt, api_name="/generate")
                    
                    # Temp ထဲသို့ MP4 အဖြစ် သိမ်းဆည်းခြင်း
                    clip_path = os.path.join(temp_dir, f"clip_{idx}.mp4")
                    shutil.copy(result, clip_path)
                    video_files.append(clip_path)
                    
                    progress_bar.progress(int(((idx + 1) / len(scenes)) * 80))
                
                # FFmpeg ဖြင့် ဗီဒီယိုများကို ပေါင်းစပ်ခြင်း
                st.info("🎬 Clip အားလုံးကို ဗီဒီယို ၁ ပုဒ်တည်းဖြစ်အောင် အချောသတ် ပေါင်းစပ်နေပါသည်။...")
                
                list_file_path = os.path.join(temp_dir, "files.txt")
                with open(list_file_path, "w") as f:
                    for vf in video_files:
                        f.write(f"file '{vf}'\n")
                
                output_final_path = os.path.join(temp_dir, "final_full_movie.mp4")
                
                (
                    ffmpeg
                    .input(list_file_path, format='concat', safe=0)
                    .output(output_final_path, c='copy')
                    .run(overwrite_output=True, quiet=True)
                )
                
                progress_bar.progress(100)
                st.success("✨ ၁ မိနစ်စာ 3D ဗီဒီယို အပြည့်အစုံ ထွက်ရှိလာပါပြီ။")
                
                st.video(output_final_path)
                
                with open(output_final_path, "rb") as f:
                    st.download_button(
                        label="📥 ဗီဒီယိုအပြည့်အစုံ (Full MP4) ဒေါင်းလုဒ်ယူရန်",
                        data=f.read(),
                        file_name="3d_full_story.mp4",
                        mime="video/mp4"
                    )
                    
            except Exception as e:
                st.error(f"Error တက်သွားပါသည် (Server ကျနေပါက ပြန်စမ်းပေးပါ): {e}")

# ---------------------------------------------------------
# TAB 2: Free Voice Generator
# ---------------------------------------------------------
with tab2:
    st.subheader("🔊 Free AI Voice Generator")
    tts_text = st.text_area("အသံပြောင်းရန် စာသား ရေးပါ:", value="Do you hear that scary noise? Run quickly!")
    
    if st.button("🚀 AI Audio ဖိုင် ထုတ်ယူမည်"):
        if tts_text.strip():
            async def generate_speech():
                communicate = edge_tts.Communicate(tts_text, "en-US-ChristopherNeural")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                    await communicate.save(tmp_mp3.name)
                    return tmp_mp3.name
            
            try:
                audio_path = asyncio.run(generate_speech())
                st.success("✨ အသံဖိုင် ရရှိပါပြီ။")
                st.audio(audio_path)
            except Exception as e:
                st.error(f"Error: {e}")
