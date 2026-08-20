import streamlit as st
import tempfile
import os
import ffmpeg
import asyncio
import edge_tts
import requests
import time
from PIL import Image

st.set_page_config(page_title="Cinematic 3D Horror Studio", layout="centered")
st.title("🎬 Cinematic 3D Horror Studio")
st.caption("✨ ရုပ်ရှင်အဆင့်မီ Cinematic 3D Character များဖြင့် ဗီဒီယို ဖန်တီးပေးသည့် စနစ်")

VOICE_MAPPING = {
    "ရွာသူကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-10Hz", "rate": "-10%"},
    "ကောင်လေး": {"voice": "my-MM-ThihaNeural", "pitch": "+5Hz", "rate": "+0%"},
    "နတ်ဆိုးကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-40Hz", "rate": "-20%"},
    "မိန်းကလေး": {"voice": "my-MM-NilarNeural", "pitch": "+10Hz", "rate": "+0%"},
    "ဇာတ်ကြောင်းပြော": {"voice": "my-MM-ThihaNeural", "pitch": "-5Hz", "rate": "-5%"},
}

# Cinematic 3D Movie Prompts (ရုပ်ရှင်အဆင့်မီ ပုံထွက်ရရှိစေရန်)
SCENE_PROMPTS = [
    "High budget 3D animated movie render, Pixar style, close up face of spooky village chief in dark misty forest, cinematic lighting, Unreal Engine 5 render, extremely detailed, 8k resolution",
    "High budget 3D animated movie render, Pixar style, close up face of terrified beautiful anime girl, volumetric dark lighting, Octane render, photorealistic 3D, 8k resolution",
    "High budget 3D animated movie render, Pixar style, close up face of brave young boy with glowing lantern, dramatic shadows, Unreal Engine 5, highly detailed, masterpiece",
    "High budget 3D animated movie render, Pixar style, close up face of scary shadow demon with glowing red eyes, creepy horror atmosphere, masterpiece 3D render, 8k resolution"
]

default_script = """ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး တံခါးတွေ ပိတ်ထားကြ။
မိန်းကလေး: ကိုကို... ဒီရွာပျက်ကြီးထဲကို ဝင်ဖို့ တကယ်ပဲ လိုလို့လား။
ကောင်လေး: မကြောက်ပါနဲ့ ညီမလေးရယ်၊ ငါတို့ ဒီည သဲလွန်စ ရှာရမယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ငါ့ရဲ့ နယ်မြေထဲကို ရောက်လာခဲ့ပြီ။"""

full_script = st.text_area("📝 ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ:", value=default_script, height=180)

def fetch_cinematic_3d_image(idx, save_path):
    prompt = SCENE_PROMPTS[idx % len(SCENE_PROMPTS)]
    encoded = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={idx+777}&nologo=true"
    
    for _ in range(3):
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                return
        except Exception:
            time.sleep(1)
            
    img = Image.new('RGB', (1280, 720), color=(15, 10, 20))
    img.save(save_path)

if st.button("🚀 Cinematic 3D Video ဖန်တီးမည်"):
    lines = [line.strip() for line in full_script.split('\n') if line.strip()]
    if not lines:
        st.warning("⚠️ စာသားများ ထည့်ပေးပါခင်ဗျာ။")
    else:
        temp_dir = tempfile.mkdtemp()
        merged_clips = []
        progress_bar = st.progress(0)

        async def make_audio(text, profile, output_path):
            communicate = edge_tts.Communicate(text=text, voice=profile["voice"], pitch=profile["pitch"], rate=profile["rate"])
            await communicate.save(output_path)

        try:
            for idx, line in enumerate(lines):
                st.write(f"🎬 Scene {idx+1}/{len(lines)} (Cinematic Render) ဖန်တီးနေပါသည်...")
                
                if ":" in line:
                    char_name, speech = line.split(":", 1)
                elif "：" in line:
                    char_name, speech = line.split("：" , 1)
                else:
                    char_name, speech = "ဇာတ်ကြောင်းပြော", line
                
                char_name = char_name.strip()
                speech = speech.strip()
                profile = VOICE_MAPPING.get(char_name, {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"})
                
                # 1. Audio
                audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(make_audio(speech, profile, audio_path))
                
                # 2. Cinematic Image
                img_path = os.path.join(temp_dir, f"i_{idx}.jpg")
                fetch_cinematic_3d_image(idx, img_path)
                
                # 3. Motion Video Clip
                out_scene = os.path.join(temp_dir, f"s_{idx}.mp4")
                in_img = ffmpeg.input(img_path, loop=1)
                in_aud = ffmpeg.input(audio_path)
                ffmpeg.output(in_img, in_aud, out_scene, vcodec='libx264', acodec='aac', shortest=None, pix_fmt='yuv420p', vf='scale=1280:720').run(overwrite_output=True, quiet=True)
                
                merged_clips.append(out_scene)
                progress_bar.progress(int(((idx+1)/len(lines))*85))
                
            # Merge All
            st.info("🎬 ဗီဒီယို တစ်ခုလုံး ပေါင်းစပ်နေပါသည်...")
            list_file = os.path.join(temp_dir, "files.txt")
            with open(list_file, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
                    
            final_path = os.path.join(temp_dir, "cinematic_3d_movie.mp4")
            ffmpeg.input(list_file, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)
            
            progress_bar.progress(100)
            st.success("✨ Cinematic 3D Horror Video ရရှိပါပြီ။")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("📥 MP4 Video ဒေါင်းလုဒ်ယူရန်", data=f.read(), file_name="Cinematic_3D_Horror.mp4", mime="video/mp4")
                
        except Exception as e:
            st.error(f"Error တက်သွားပါသည်: {e}")
