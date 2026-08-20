import streamlit as st
import tempfile
import os
import ffmpeg
import asyncio
import edge_tts
import requests
import time
from PIL import Image

st.set_page_config(page_title="3D AI Horror Studio", layout="centered")
st.title("👻 3D AI Horror Studio")
st.caption("✨ 3D Pixar Style Horror ဗီဒီယိုများကို အမှန်ကန်ဆုံး ဖန်တီးပေးသည့် စနစ်")

# 3D Horror Prompt Template များ (AI နားလည်သော အင်္ဂလိပ်စာသားများ)
SCENE_PROMPTS = [
    "3D Pixar style horror render, dark haunted spooky ancient village at night, glowing red fog, creepy atmosphere, highly detailed 3D animation",
    "3D Pixar style horror render, terrified anime characters running in dark creepy abandoned village, dramatic lighting, 3D cinematic",
    "3D Pixar style horror render, old wooden house inside at night, spooky shadow on wall, eerie atmosphere, ultra detailed 3D render",
    "3D Pixar style horror render, terrifying giant demon monster with glowing red eyes appearing in dark foggy forest, epic 3D render",
    "3D Pixar style horror render, terrifying demon shadow towering over scared villagers, dramatic dark lighting, highly detailed 3D scene",
    "3D Pixar style horror render, glowing magic spell destroying scary monster, smoke and light particles, 3D render",
    "3D Pixar style horror render, creepy dark haunted graveyard at night, full moon, misty atmosphere, highly detailed 3D render",
    "3D Pixar style horror render, scary monster in dark forest vanishing into glowing dust, cinematic 3D render"
]

VOICE_MAPPING = {
    "ရွာသူကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-10Hz", "rate": "-10%"},
    "ကောင်လေး": {"voice": "my-MM-ThihaNeural", "pitch": "+5Hz", "rate": "+0%"},
    "နတ်ဆိုးကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-40Hz", "rate": "-20%"},
    "ရွာသား ၁": {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"},
    "အမျိုးသမီး": {"voice": "my-MM-NilarNeural", "pitch": "+0Hz", "rate": "+0%"},
    "မိန်းကလေး": {"voice": "my-MM-NilarNeural", "pitch": "+10Hz", "rate": "+0%"},
    "ဇာတ်ကြောင်းပြော": {"voice": "my-MM-ThihaNeural", "pitch": "-5Hz", "rate": "-5%"},
}

st.subheader("📝 Horror ဇာတ်လမ်း စာသားများ ထည့်ပါ")

default_script = """ဇာတ်ကြောင်းပြော: အမှောင်ထုလွှမ်းမိုးထားတဲ့ တောအုပ်နက်ကြီးထဲမှာ ရှေးဟောင်းရွာပျက်ကြီးတစ်ခု ရှိခဲ့ပါတယ်။
မိန်းကလေး: ကိုကို... ဒီရွာပျက်ကြီးထဲကို ဝင်ဖို့ တကယ်ပဲ လိုလို့လား၊ ညီမ သိပ်ကြောက်နေပြီ။
ကောင်လေး: မကြောက်ပါနဲ့ ညီမလေးရယ်၊ ငါတို့ ဒီည ရွာထဲက သဲလွန်စတစ်ခုခုရအောင် ရှာရမယ်။
ရွာသူကြီး: သတိထားကြ... ဒီနေရာကနေ ချက်ချင်း ထွက်သွားကြစမ်း၊ နတ်ဆိုးကြီး နိုးလာတော့မယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ငါ့ရဲ့ နယ်မြေထဲကို ရောက်လာခဲ့ပြီ၊ မည်သူမျှ အသက်ရှင်လျက် ထွက်မသွားရဘူး။
ကောင်လေး: ဟာ... ဟိုမှာ ကြောက်စရာ နတ်ဆိုးကြီး ပေါ်လာပြီ၊ မြန်မြန်ပြေးကြ။
မိန်းကလေး: ကူညီကြပါဦး... ငါတို့ကို ဒီနတ်ဆိုးကြီး လက်ကနေ လွတ်အောင် ကယ်ကြပါဦး။
ဇာတ်ကြောင်းပြော: နောက်ဆုံးမှာတော့ သူတို့နှစ်ယောက်ဟာ သရဲခြောက်တဲ့ အမှောင်ထုထဲမှာ ထာဝရ ပျောက်ကွယ်သွားခဲ့ရပါတော့တယ်။"""

full_script = st.text_area("ဇာတ်လမ်း စာသားများ (တစ်လိုင်းလျှင် Scene တစ်ခု):", value=default_script, height=220)

def fetch_3d_horror_image(scene_index, save_path):
    # Prompt ကို AI ပုံဆွဲစနစ် ကြိုက်သည့် 3D Pixar Horror Keywords များဖြင့် ထုတ်ပေးခြင်း
    prompt_text = SCENE_PROMPTS[scene_index % len(SCENE_PROMPTS)]
    encoded = requests.utils.quote(prompt_text)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={scene_index + 101}&nologo=true"
    
    for _ in range(3):
        try:
            res = requests.get(url, timeout=40)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                return
        except Exception:
            time.sleep(2)
            
    img = Image.new('RGB', (1280, 720), color=(15, 10, 25))
    img.save(save_path)

if st.button("🚀 3D Horror Video တန်းထုတ်မည်"):
    lines = [line.strip() for line in full_script.split('\n') if line.strip()]
    if not lines:
        st.warning("⚠️ ကျေးဇူးပြု၍ စာသားများ ထည့်ပေးပါခင်ဗျာ။")
    else:
        temp_dir = tempfile.mkdtemp()
        merged_clips = []
        progress_bar = st.progress(0)
        
        async def make_audio(text, profile, output_path):
            communicate = edge_tts.Communicate(text=text, voice=profile["voice"], pitch=profile["pitch"], rate=profile["rate"])
            await communicate.save(output_path)

        try:
            for idx, line in enumerate(lines):
                st.write(f"🎬 Scene {idx+1}/{len(lines)} (3D Pixar Style) ကို ဖန်တီးနေပါသည်...")
                
                if ":" in line:
                    char_name, speech = line.split(":", 1)
                elif "：" in line:
                    char_name, speech = line.split("：" , 1)
                else:
                    char_name, speech = "ဇာတ်ကြောင်းပြော", line
                
                char_name = char_name.strip()
                speech = speech.strip()
                
                profile = VOICE_MAPPING.get(char_name, {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"})
                
                # 1. Voice Audio Generation
                audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(make_audio(speech, profile, audio_path))
                
                # 2. Perfect 3D Pixar Horror Image Generation
                img_path = os.path.join(temp_dir, f"i_{idx}.jpg")
                fetch_3d_horror_image(idx, img_path)
                    
                # 3. Merge Audio + Image
                out_scene = os.path.join(temp_dir, f"s_{idx}.mp4")
                in_img = ffmpeg.input(img_path, loop=1)
                in_aud = ffmpeg.input(audio_path)
                ffmpeg.output(in_img, in_aud, out_scene, vcodec='libx264', acodec='aac', shortest=None, pix_fmt='yuv420p', vf='scale=1280:720').run(overwrite_output=True, quiet=True)
                
                merged_clips.append(out_scene)
                progress_bar.progress(int(((idx+1)/len(lines))*80))
                
            # Merge all scenes into full movie
            st.info("🎬 အပြီးသတ် 3D ဗီဒီယို ပေါင်းစပ်နေပါသည်။...")
            list_file = os.path.join(temp_dir, "files.txt")
            with open(list_file, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
                    
            final_path = os.path.join(temp_dir, "full_3d_horror_movie.mp4")
            ffmpeg.input(list_file, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)
            
            progress_bar.progress(100)
            st.success("✨ 3D Pixar Horror ဗီဒီယို အပြည့်အစုံ ရရှိပါပြီ။")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("📥 MP4 Video ဒေါင်းလုဒ်ယူရန်", data=f.read(), file_name="3D_Horror_Story.mp4", mime="video/mp4")
                
        except Exception as e:
            st.error(f"Error တက်သွားပါသည်: {e}")
