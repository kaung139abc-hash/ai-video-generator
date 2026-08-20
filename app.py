import streamlit as st
import tempfile
import os
import ffmpeg
import asyncio
import edge_tts
import requests
import time
from PIL import Image

st.set_page_config(page_title="Universal AI Story & Video Creator", layout="centered")
st.title("🎬 Universal AI Story & Video Creator")
st.caption("✨ မည်သည့် ဇာတ်လမ်း၊ မည်သည့် ပုံပြင်မဆို စိတ်ကြိုက် ဗီဒီယို ဖန်တီးပေးသည့် စနစ်")

# ၁။ ရုပ်ပုံ ဒီဇိုင်း မုဒ် (Art Style) ရွေးချယ်ရန်
style = st.selectbox(
    "🎨 ရုပ်ပုံ ဒီဇိုင်း မုဒ် (Art Style) ရွေးပါ-",
    [
        "3D Pixar / Disney Style",
        "Anime / Manga Style",
        "Realistic Cinematic / Movie Style",
        "Fantasy / Fairy Tale Style",
        "Cartoon / Comic Style",
        "Dark / Horror Style"
    ]
)

STYLE_PROMPTS = {
    "3D Pixar / Disney Style": "3D Pixar animation style, vibrant colors, detailed 3D render",
    "Anime / Manga Style": "anime style, studio ghibli aesthetic, beautiful Japanese animation",
    "Realistic Cinematic / Movie Style": "cinematic movie scene, 8k resolution, realistic lighting, photo realistic",
    "Fantasy / Fairy Tale Style": "magical fantasy art style, enchanted fairytale illustration, glowing light",
    "Cartoon / Comic Style": "colorful comic book style, cartoon illustration, bright lines",
    "Dark / Horror Style": "dark horror style, creepy atmosphere, dramatic dark lighting"
}

# ၂။ ဇာတ်ကောင် အသံများ သတ်မှတ်ချက်
VOICES = {
    "ဇာတ်ကြောင်းပြော (ကျား)": {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"},
    "ဇာတ်ကြောင်းပြော (မ)": {"voice": "my-MM-NilarNeural", "pitch": "+0Hz", "rate": "+0%"},
    "အမျိုးသား ဇာတ်ကောင်": {"voice": "my-MM-ThihaNeural", "pitch": "+5Hz", "rate": "+5%"},
    "အမျိုးသမီး ဇာတ်ကောင်": {"voice": "my-MM-NilarNeural", "pitch": "+5Hz", "rate": "+5%"},
    "ကလေး / လူငယ် / သတ္တဝါ": {"voice": "my-MM-NilarNeural", "pitch": "+15Hz", "rate": "+10%"},
    "သက်ကြီးရွယ်အို": {"voice": "my-MM-ThihaNeural", "pitch": "-15Hz", "rate": "-10%"},
    "သရဲ / နတ်ဆိုး / Monster": {"voice": "my-MM-ThihaNeural", "pitch": "-40Hz", "rate": "-20%"},
}

st.subheader("📝 ဇာတ်လမ်း သို့မဟုတ် ပုံပြင် စာသားများ ထည့်ပါ")
st.caption("💡 ရေးနည်း - `ဇာတ်ကောင်: စကားပြောစာသား` (ဥပမာ - ယုန်ကလေး: မင်္ဂလာပါ / ဇာတ်ကြောင်းပြော: ရှေးရှေးတုန်းက...)")

sample_script = """ဇာတ်ကြောင်းပြော: ရှေးရှေးတုန်းက လှပတဲ့ သစ်တောကြီးတစ်ခု ထဲမှာ ယုန်ကလေးတစ်ကောင် ရှိခဲ့ပါတယ်။
ယုန်ကလေး: ဒီနေ့ ရာသီဥတုလေးက တကယ်ကို သာယာတာပဲနော်။
အမျိုးသား: ဟေ... ဟိုမှာ ယုန်ကလေးတစ်ကောင် ပြေးနေတာပဲ။
ဇာတ်ကြောင်းပြော: ဒီလိုနဲ့ သူတို့အားလုံး ပျော်ရွှင်စွာ အတူတကွ နေထိုင်ခဲ့ကြပါတော့တယ်။"""

user_script = st.text_area("ဇာတ်လမ်း စာသားများ (တစ်လိုင်းလျှင် Scene တစ်ခု):", value=sample_script, height=200)

def fetch_image(prompt_text, style_prefix, seed, save_path):
    full_prompt = f"{style_prefix}, {prompt_text}"
    encoded = requests.utils.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={seed}&nologo=true"
    
    for _ in range(3):
        try:
            res = requests.get(url, timeout=40)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                return
        except Exception:
            time.sleep(2)
            
    # Server မရပါက Backup ရုပ်ပုံ ထုတ်ပေးခြင်း
    img = Image.new('RGB', (1280, 720), color=(30, 30, 50))
    img.save(save_path)

if st.button("🚀 ဗီဒီယို စတင်ဖန်တီးမည်"):
    lines = [l.strip() for l in user_script.split('\n') if l.strip()]
    if not lines:
        st.warning("⚠️ ဇာတ်လမ်း စာသားများ ထည့်ပေးပါ။")
    else:
        temp_dir = tempfile.mkdtemp()
        merged_clips = []
        progress_bar = st.progress(0)
        
        async def generate_voice(text, profile, out_path):
            comm = edge_tts.Communicate(text=text, voice=profile["voice"], pitch=profile["pitch"], rate=profile["rate"])
            await comm.save(out_path)

        try:
            style_prefix = STYLE_PROMPTS[style]
            
            for idx, line in enumerate(lines):
                st.write(f"🎬 Scene {idx+1}/{len(lines)} ဖန်တီးနေပါသည်...")
                
                # Split character and line
                if ":" in line:
                    char_name, speech = line.split(":", 1)
                elif "：" in line:
                    char_name, speech = line.split("：", 1)
                else:
                    char_name, speech = "ဇာတ်ကြောင်းပြော", line
                
                char_name = char_name.strip()
                speech = speech.strip()
                
                # Dynamic Voice Selection based on character name
                if any(k in char_name for k in ["မ", "မိန်းမ", "သမီး", "ကောင်မလေး", "မမ"]):
                    voice_prof = VOICES["အမျိုးသမီး ဇာတ်ကောင်"]
                elif any(k in char_name for k in ["ကလေး", "ယုန်", "ကြောင်", "ခွေး", "ဝက်"]):
                    voice_prof = VOICES["ကလေး / လူငယ် / သတ္တဝါ"]
                elif any(k in char_name for k in ["နတ်ဆိုး", "သရဲ", "ဘီလူး", "ကျားကြီး"]):
                    voice_prof = VOICES["သရဲ / နတ်ဆိုး / Monster"]
                elif any(k in char_name for k in ["အဘိုး", "လူကြီး", "သူကြီး"]):
                    voice_prof = VOICES["သက်ကြီးရွယ်အို"]
                elif any(k in char_name for k in ["ကျား", "မင်းသား", "အမျိုးသား", "ကောင်လေး"]):
                    voice_prof = VOICES["အမျိုးသား ဇာတ်ကောင်"]
                else:
                    voice_prof = VOICES["ဇာတ်ကြောင်းပြော (ကျား)"]
                
                # 1. Voice Generation
                aud_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(generate_voice(speech, voice_prof, aud_path))
                
                # 2. Image Generation based on story text & chosen style
                img_path = os.path.join(temp_dir, f"i_{idx}.jpg")
                fetch_image(speech, style_prefix, idx + 555, img_path)
                
                # 3. Merge Audio + Image to Video Clip
                out_scene = os.path.join(temp_dir, f"s_{idx}.mp4")
                in_i = ffmpeg.input(img_path, loop=1)
                in_a = ffmpeg.input(aud_path)
                ffmpeg.output(in_i, in_a, out_scene, vcodec='libx264', acodec='aac', shortest=None, pix_fmt='yuv420p', vf='scale=1280:720').run(overwrite_output=True, quiet=True)
                
                merged_clips.append(out_scene)
                progress_bar.progress(int(((idx+1)/len(lines))*80))
                
            # Merge All Scenes into Final Story Movie
            st.info("🎬 ဗီဒီယို တစ်ပုဒ်လုံး ပေါင်းစပ်နေပါသည်...")
            list_file = os.path.join(temp_dir, "files.txt")
            with open(list_file, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
                    
            final_mp4 = os.path.join(temp_dir, "story_video.mp4")
            ffmpeg.input(list_file, format='concat', safe=0).output(final_mp4, c='copy').run(overwrite_output=True, quiet=True)
            
            progress_bar.progress(100)
            st.success("✨ သင်ဖန်တီးထားသော ဗီဒီယို ရရှိပါပြီ။")
            st.video(final_mp4)
            with open(final_mp4, "rb") as f:
                st.download_button("📥 MP4 Video ဒေါင်းလုဒ်ယူရန်", data=f.read(), file_name="story_video.mp4", mime="video/mp4")
                
        except Exception as e:
            st.error(f"Error တက်သွားပါသည်: {e}")
