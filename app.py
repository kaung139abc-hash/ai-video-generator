import streamlit as st
from gradio_client import Client
import tempfile
import os
import ffmpeg
import shutil
import asyncio
import edge_tts

st.set_page_config(page_title="3D AI Horror Video Studio", layout="centered")
st.title("👻 3D AI Horror Studio (7 Characters)")
st.caption("✨ ရွာသူကြီး၊ ကောင်လေး၊ ရွာသူရွာသား ၄ ယောက် နှင့် နတ်ဆိုး အပါအဝင် ၇ ယောက် စကားပြောနိုင်သော စနစ်")

# Secrets သို့မဟုတ် Sidebar မှ Hugging Face Token ယူခြင်း
hf_token = st.secrets.get("HF_TOKEN", "")
if not hf_token:
    hf_token = st.sidebar.text_input("🔑 Hugging Face Token:", type="password")

VOICE_PROFILES = {
    "👴 ရွာသူကြီး (Village Chief)": {"voice": "my-MM-ThihaNeural", "pitch": "-10Hz", "rate": "-10%"},
    "🧙‍♂️ ဂါထာမန်တန်စွမ်းအားရှင် ကောင်လေး": {"voice": "my-MM-ThihaNeural", "pitch": "+5Hz", "rate": "+0%"},
    "👿 နတ်ဆိုးကြီး (Terrifying Male Demon)": {"voice": "my-MM-ThihaNeural", "pitch": "-40Hz", "rate": "-30%"},
    "👨 ရွာသား ၁ - အမျိုးသား (Villager 1 - Male)": {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"},
    "👩 ရွာသား ၂ - အမျိုးသမီး (Villager 2 - Female)": {"voice": "my-MM-NilarNeural", "pitch": "+0Hz", "rate": "+0%"},
    "👦 ရွာသား ၃ - လူငယ်အမျိုးသား (Villager 3 - Young Male)": {"voice": "my-MM-ThihaNeural", "pitch": "+10Hz", "rate": "+5%"},
    "👧 ရွာသား ၄ - မိန်းကလေး (Villager 4 - Young Female)": {"voice": "my-MM-NilarNeural", "pitch": "+10Hz", "rate": "+0%"},
}

st.subheader("🎬 Horror Scene များ ရိုက်ကူးရန်")

num_scenes = st.number_input("ဖန်တီးချင်သော Scene အရေအတွက် ရွေးပါ-", min_value=1, max_value=10, value=6)

scenes_input = []

for i in range(1, num_scenes + 1):
    with st.expander(f"📌 Scene {i} (ဇာတ်ဝင်ခန်း {i})", expanded=(i <= 2)):
        col1, col2 = st.columns(2)
        with col1:
            prompt = st.text_area(
                f"Scene {i} 3D Prompt (English):", 
                value=f"3D Pixar horror style scene {i}, dramatic lighting, creepy atmosphere", 
                key=f"p_{i}", 
                height=80
            )
            voice_choice = st.selectbox(
                f"Scene {i} တွင် ပြောမည့် ဇာတ်ကောင်/အသံ:", 
                list(VOICE_PROFILES.keys()), 
                key=f"v_{i}"
            )
        with col2:
            speech_text = st.text_area(
                f"Scene {i} စကားပြော (မြန်မာစာ):", 
                value="", 
                placeholder="ဒီမှာ စကားပြော စာသား ရိုက်ပါ...", 
                key=f"t_{i}", 
                height=120
            )
            
        scenes_input.append({
            "prompt": prompt,
            "text": speech_text,
            "voice_profile": VOICE_PROFILES[voice_choice]
        })

if st.button("🚀 Horror 3D Video အပြီးသတ် ဖန်တီးမည်"):
    valid_scenes = [s for s in scenes_input if s["prompt"].strip() and s["text"].strip()]
    
    if not valid_scenes:
        st.warning("⚠️ ကျေးဇူးပြု၍ Scene များတွင် စကားပြော စာသားများ ဖြည့်ပေးပါခင်ဗျာ။")
    else:
        temp_dir = tempfile.mkdtemp()
        merged_clips = []
        
        st.info("⏳ AI မှ Video Render ရိုက်ကူးခြင်းနှင့် ဇာတ်ကောင်အသံများကို ထည့်သွင်းနေပါသည်။...")
        progress_bar = st.progress(0)
        
        try:
            token_val = hf_token.strip() if hf_token and hf_token.strip() else None
            
            # Hugging Face Public API မှ ဗီဒီယို ထုတ်ပေးသည့် Space သို့ ချိတ်ဆက်ခြင်း
            client = Client("damo-vilab/modelscope-text-to-video-synthesis", hf_token=token_val)
            
            async def make_audio(text, profile, output_path):
                communicate = edge_tts.Communicate(
                    text=text, 
                    voice=profile["voice"], 
                    pitch=profile["pitch"], 
                    rate=profile["rate"]
                )
                await communicate.save(output_path)

            for idx, item in enumerate(valid_scenes):
                st.write(f"🎬 Scene {idx+1}/{len(valid_scenes)} ကို ဖန်တီးနေပါသည်...")
                
                # 1. Render Video
                video_raw = client.predict(
                    item["prompt"],
                    api_name="/predict"
                )
                
                clip_video_path = os.path.join(temp_dir, f"v_{idx}.mp4")
                video_file_path = video_raw[0] if isinstance(video_raw, (list, tuple)) else video_raw
                shutil.copy(video_file_path, clip_video_path)
                
                # 2. Generate Character Audio
                clip_audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(make_audio(item["text"], item["voice_profile"], clip_audio_path))
                
                # 3. Merge Video & Audio
                scene_output_path = os.path.join(temp_dir, f"scene_{idx}_merged.mp4")
                video_in = ffmpeg.input(clip_video_path)
                audio_in = ffmpeg.input(clip_audio_path)
                
                ffmpeg.output(video_in, audio_in, scene_output_path, vcodec='copy', acodec='aac', shortest=None).run(overwrite_output=True, quiet=True)
                merged_clips.append(scene_output_path)
                
                progress_bar.progress(int(((idx + 1) / len(valid_scenes)) * 80))
                
            # 4. Concatenate All Scenes
            st.info("🎬 Scene အားလုံးကို ဇာတ်လမ်းတစ်ပုဒ်တည်းဖြစ်အောင် ပေါင်းစပ်နေပါသည်။...")
            list_file_path = os.path.join(temp_dir, "files.txt")
            with open(list_file_path, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
            
            final_video_path = os.path.join(temp_dir, "full_horror_movie.mp4")
            (
                ffmpeg
                .input(list_file_path, format='concat', safe=0)
                .output(final_video_path, c='copy')
                .run(overwrite_output=True, quiet=True)
            )
            
            progress_bar.progress(100)
            st.success("✨ ဇာတ်လမ်းအပြည့်အစုံ 3D Horror Video ရရှိပါပြီ။")
            st.video(final_video_path)
            
            with open(final_video_path, "rb") as f:
                st.download_button(
                    label="📥 MP4 Video ဒေါင်းလုဒ်ယူရန်",
                    data=f.read(),
                    file_name="full_horror_story.mp4",
                    mime="video/mp4"
                )

        except Exception as e:
            st.error(f"Error တက်သွားပါသည်: {e}")
