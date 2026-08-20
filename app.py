import streamlit as st
import tempfile
import os
import ffmpeg
import asyncio
import edge_tts
import requests
from gradio_client import Client, handle_file

st.set_page_config(page_title="100% Free 3D Lip-Sync Video Generator", layout="centered")
st.title("🎬 3D AI Lip-Sync Video Creator")
st.caption("✨ API Key မလိုဘဲ ၁၀၀% အခမဲ့ ပါးစပ်လှုပ် 3D ဗီဒီယို ထုတ်ပေးသည့် စနစ်")

VOICE_MAPPING = {
    "ရွာသူကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-10Hz", "rate": "-10%"},
    "ကောင်လေး": {"voice": "my-MM-ThihaNeural", "pitch": "+5Hz", "rate": "+0%"},
    "နတ်ဆိုးကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-40Hz", "rate": "-20%"},
    "မိန်းကလေး": {"voice": "my-MM-NilarNeural", "pitch": "+10Hz", "rate": "+0%"},
    "ဇာတ်ကြောင်းပြော": {"voice": "my-MM-ThihaNeural", "pitch": "-5Hz", "rate": "-5%"},
}

default_script = """ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး တံခါးတွေ ပိတ်ထားကြ။
မိန်းကလေး: ကိုကို... ဒီရွာပျက်ကြီးထဲကို ဝင်ဖို့ တကယ်ပဲ လိုလို့လား။
ကောင်လေး: မကြောက်ပါနဲ့ ညီမလေးရယ်၊ ငါတို့ ဒီည သဲလွန်စ ရှာရမယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ငါ့ရဲ့ နယ်မြေထဲကို ရောက်လာခဲ့ပြီ။"""

full_script = st.text_area("📝 ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ:", value=default_script, height=180)

def fetch_3d_face_image(char_name, save_path):
    """3D Pixar Horror Character Face Image Generation"""
    prompt = f"3D Pixar style animated horror character portrait, close up face of {char_name}, dark cinematic lighting, highly detailed 3D render, masterpiece"
    encoded = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
    res = requests.get(url, timeout=30)
    with open(save_path, "wb") as f:
        f.write(res.content)

def generate_free_lipsync(image_path, audio_path, output_video_path):
    """HuggingFace Free SadTalker Space ဖြင့် ပါးစပ်လှုပ် Video ဖန်တီးခြင်း"""
    client = Client("vinthony/SadTalker")
    result = client.predict(
        source_image=handle_file(image_path),
        driven_audio=handle_file(audio_path),
        preprocess="full",
        still=True,
        enhancer="gfpgan",
        batch_size=1,
        size=256,
        pose_style=0,
        facerender="faceid",
        exp_weight=1.0,
        use_ref_video=False,
        ref_video=None,
        ref_info="pose",
        use_idle_mode=False,
        length_of_pose=0,
        api_name="/generate"
    )
    # result[0] တွင် ရရှိလာသော Video Path ကို ယူပါမည်
    video_tmp_path = result[0] if isinstance(result, tuple) else result
    os.system(f"cp '{video_tmp_path}' '{output_video_path}'")

if st.button("🚀 ၁၀၀% Free 3D Lip-Sync Video စတင်ထုတ်မည်"):
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
                st.write(f"🎬 Scene {idx+1}/{len(lines)} ကို ဖန်တီးနေပါသည်...")
                
                if ":" in line:
                    char_name, speech = line.split(":", 1)
                elif "：" in line:
                    char_name, speech = line.split("：", 1)
                else:
                    char_name, speech = "ဇာတ်ကြောင်းပြော", line
                
                char_name = char_name.strip()
                speech = speech.strip()
                profile = VOICE_MAPPING.get(char_name, {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"})
                
                # 1. Audio Generation
                audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(make_audio(speech, profile, audio_path))
                
                # 2. 3D Face Image Generation
                img_path = os.path.join(temp_dir, f"i_{idx}.jpg")
                fetch_3d_face_image(char_name, img_path)
                
                # 3. Free Lip-Sync Video Generation
                st.write(f"👄 Scene {idx+1} အတွက် ပါးစပ်လှုပ်ရှားမှု (Lip-Sync) ပြုလုပ်နေပါသည်...")
                out_scene = os.path.join(temp_dir, f"s_{idx}.mp4")
                generate_free_lipsync(img_path, audio_path, out_scene)
                
                merged_clips.append(out_scene)
                progress_bar.progress(int(((idx+1)/len(lines))*85))
                
            # Merge All Scenes into Final Video
            st.info("🎬 ဗီဒီယို အပိုင်းများကို ပေါင်းစပ်နေပါသည်...")
            list_file = os.path.join(temp_dir, "files.txt")
            with open(list_file, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
                    
            final_path = os.path.join(temp_dir, "final_3d_lipsync.mp4")
            ffmpeg.input(list_file, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)
            
            progress_bar.progress(100)
            st.success("✨ ၁၀၀% ပါးစပ်လှုပ် 3D Horror Video အပြည့်အစုံ ရရှိပါပြီ။")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("📥 MP4 Video ဒေါင်းလုဒ်ယူရန်", data=f.read(), file_name="3D_LipSync_Story.mp4", mime="video/mp4")
                
        except Exception as e:
            st.error(f"Error တက်သွားပါသည်: {e}")
