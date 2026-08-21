import os
import streamlit as st
import asyncio
import edge_tts
from moviepy.editor import TextClip, AudioFileClip, ColorClip, CompositeVideoClip

st.title("🎬 Novel to MP4 Video AI Generator")

user_text = st.text_area(
    "ဗီဒီယိုဖန်တီးမည့် ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ -",
    "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ..."
)

# အသံထုတ်ပေးသည့် ဖန်ရှင် (Edge-TTS)
async def generate_audio(text, output_file):
    voice = "my-MM-ThihaNeural"
    communicate = edge_tts.Communicate(text, voice, pitch="-30Hz", rate="-5%")
    await communicate.save(output_file)

# MoviePy ဖြင့် MP4 ဗီဒီယို ဖန်တီးသည့် ဖန်ရှင်
def create_mp4_video(audio_path, output_video_path):
    try:
        # အသံဖိုင်ကို တင်ခြင်း
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # အမည်းရောင် နောက်ခံ ဗီဒီယိုဖန်တီးခြင်း (အရွယ်အစား 720x1280 - TikTok/Shorts ပုံစံ)
        bg_clip = ColorClip(size=(720, 1280), color=(10, 10, 15), duration=duration)
        
        # အသံကို ဗီဒီယိုနဲ့ ပေါင်းစပ်ခြင်း
        video = bg_clip.set_audio(audio_clip)
        
        # MP4 ဖိုင်အဖြစ် သိမ်းဆည်းခြင်း
        video.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")
        return True
    except Exception as e:
        st.error(f"ဗီဒီယိုထုတ်လုပ်ရာတွင် Error ဖြစ်သည်: {e}")
        return False

if st.button("🚀 MP4 ဗီဒီယို ဖန်တီးမည်"):
    if user_text.strip():
        with st.spinner("အသံဖိုင်နှင့် ဗီဒီယိုကို ဖန်တီးနေပါပြီ... ခေတ္တစောင့်ဆိုင်းပေးပါ"):
            os.makedirs("output_media", exist_ok=True)
            audio_file = "output_media/story_audio.mp3"
            video_file = "output_media/story_video.mp4"
            
            try:
                # ၁။ အသံဖိုင်ထုတ်ရန်
                asyncio.run(generate_audio(user_text, audio_file))
                
                # ၂။ MP4 ဗီဒီယို ထုတ်ရန်
                success = create_mp4_video(audio_file, video_file)
                
                if success:
                    st.success("🎉 MP4 ဗီဒီယို အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
                    # ဗီဒီယိုကို တိုက်ရိုက်ပြသရန်နှင့် Download ဆွဲရန်
                    st.video(video_file)
                    
                    with open(video_file, "rb") as f:
                        st.download_button(
                            label="📥 MP4 ဗီဒီယိုကို Download ရယူရန်",
                            data=f,
                            file_name="novel_story.mp4",
                            mime="video/mp4"
                        )
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
