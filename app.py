import streamlit as st
import tempfile
import os
import ffmpeg
import asyncio
import edge_tts
import requests

st.set_page_config(page_title="3D AI Horror Studio", layout="centered")
st.title("👻 3D AI Horror Studio (1-Click Bulk Script)")
st.caption("✨ စာသားအကုန်လုံး တစ်ခါတည်း ကူးထည့်လိုက်ရုံဖြင့် ဗီဒီယို တန်းထုတ်ပေးသည့် စနစ်")

# ဇာတ်ကောင် အသံများ သတ်မှတ်ချက်
VOICE_MAPPING = {
    "ရွာသူကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-10Hz", "rate": "-10%"},
    "ကောင်လေး": {"voice": "my-MM-ThihaNeural", "pitch": "+5Hz", "rate": "+0%"},
    "နတ်ဆိုးကြီး": {"voice": "my-MM-ThihaNeural", "pitch": "-40Hz", "rate": "-30%"},
    "ရွာသား ၁": {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"},
    "အမျိုးသမီး": {"voice": "my-MM-NilarNeural", "pitch": "+0Hz", "rate": "+0%"},
    "မိန်းကလေး": {"voice": "my-MM-NilarNeural", "pitch": "+10Hz", "rate": "+0%"},
}

st.subheader("📝 ဇာတ်လမ်းတစ်ပုဒ်လုံးကို အောက်တွင် တစ်ခါတည်း ထည့်ပါ")

# နမူနာ ဇာတ်လမ်း ထည့်ထားပေးခြင်း
default_script = """ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး အိမ်တံခါးတွေ သေချာပိတ်ထားကြ။
ရွာသား ၁: သူကြီးမင်းရယ်... အပြင်မှာ ကြောက်စရာ အသံကြီးတွေ ကြားနေရတယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ရွာတစ်ရွာလုံးကို ငါ ဝါးမျိုပစ်မယ်။
ကောင်လေး: မင်းရဲ့ ယုတ်မာမှုတွေ ဒီမှာတင် အဆုံးသတ်ရမယ် နတ်ဆိုးကြီး။
မိန်းကလေး: ကြည့်လိုက်ကြပါဦး... ကောင်လေးကြောင့် နတ်ဆိုးကြီး ပျက်စီးသွားပြီ။
အမျိုးသမီး: နတ်ဆိုးကြီး သေဆုံးသွားလို့ ရွာသူရွာသားတွေလည်း ဝမ်းသာခဲ့ကြပါတယ်ရှင့်။"""

full_script = st.text_area("ဇာတ်လမ်း စာသားများ (တစ်လိုင်းလျှင် Scene တစ်ခု):", value=default_script, height=220)

if st.button("🚀 ဇာတ်လမ်းတစ်ခုလုံး ဗီဒီယို တန်းထုတ်မည်"):
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
                st.write(f"🎬 Scene {idx+1}/{len(lines)} ကို ဖန်တီးနေပါသည်...")
                
                # ဇာတ်ကောင်နှင့် စကားပြော ခွဲခြားခြင်း
                if ":" in line:
                    char_name, speech = line.split(":", 1)
                elif "：" in line:
                    char_name, speech = line.split("：" , 1)
                else:
                    char_name, speech = "ရွာသား ၁", line
                
                char_name = char_name.strip()
                speech = speech.strip()
                
                profile = VOICE_MAPPING.get(char_name, {"voice": "my-MM-ThihaNeural", "pitch": "+0Hz", "rate": "+0%"})
                
                # 1. Voice Audio
                audio_path = os.path.join(temp_dir, f"a_{idx}.mp3")
                asyncio.run(make_audio(speech, profile, audio_path))
                
                # 2. 3D Image
                prompt = requests.utils.quote(f"3D Pixar horror style, scene {idx+1}, creepy night village background")
                img_url = f"https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&seed={idx+777}&nologo=true"
                img_res = requests.get(img_url, timeout=30)
                img_path = os.path.join(temp_dir, f"i_{idx}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img_res.content)
                    
                # 3. Merge Audio + Image
                out_scene = os.path.join(temp_dir, f"s_{idx}.mp4")
                in_img = ffmpeg.input(img_path, loop=1)
                in_aud = ffmpeg.input(audio_path)
                ffmpeg.output(in_img, in_aud, out_scene, vcodec='libx264', acodec='aac', shortest=None, pix_fmt='yuv420p', vf='scale=1280:720').run(overwrite_output=True, quiet=True)
                
                merged_clips.append(out_scene)
                progress_bar.progress(int(((idx+1)/len(lines))*80))
                
            # Merge all scenes
            st.info("🎬 အပြီးသတ် ဗီဒီယို ပေါင်းစပ်နေပါသည်။...")
            list_file = os.path.join(temp_dir, "files.txt")
            with open(list_file, "w") as f:
                for mc in merged_clips:
                    f.write(f"file '{mc}'\n")
                    
            final_path = os.path.join(temp_dir, "full_movie.mp4")
            ffmpeg.input(list_file, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)
            
            progress_bar.progress(100)
            st.success("✨ ဇာတ်လမ်းအပြည့်အစုံ ဗီဒီယို ရရှိပါပြီ။")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("📥 MP4 Video ဒေါင်းလုဒ်ယူရန်", data=f.read(), file_name="horror_story.mp4", mime="video/mp4")
                
        except Exception as e:
            st.error(f"Error တက်သွားပါသည်: {e}")
