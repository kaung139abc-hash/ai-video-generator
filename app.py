import streamlit as st
from gradio_client import Client, handle_file
import tempfile
import os
import asyncio
import edge_tts

st.set_page_config(page_title="Free 3D AI Video Studio", layout="centered")
st.title("🎬 100% Free AI 3D Video Studio")
st.caption("✨ Microsoft Free Voice & Hugging Face Free AI Engine များကို ချိတ်ဆက်ထားပါသည်။")

tab1, tab2, tab3 = st.tabs(["🔊 Free Voice Generator", "🎥 3D Motion Video", "🗣️ Free Lip-Sync Avatar"])

# ---------------------------------------------------------
# TAB 1: Free Text to Speech Audio Generator (edge-tts)
# ---------------------------------------------------------
with tab1:
    st.subheader("🔊 Free AI Voice (Text to Speech) ဖန်တီးမည်")
    st.info("စာရိုက်ပေးရုံဖြင့် Microsoft ၏ သဘာဝကျသော AI အသံများကို အခမဲ့ MP3 ဖိုင် ထုတ်ပေးပါမည်။")
    
    tts_text = st.text_area(
        "အသံပြောင်းချင်သော စာသား ရေးပါ (English / Romanized):",
        value="Do you hear that scary noise? Run quickly!",
        height=100
    )
    
    voice_option = st.selectbox("အသံအမျိုးအစား ရွေးပါ-", [
        "en-US-GuyNeural (US Male - အမျိုးသားအသံ)",
        "en-US-JennyNeural (US Female - အမျိုးသမီးအသံ)",
        "en-US-ChristopherNeural (Dark/Horror Tone အသံ)",
        "en-GB-RyanNeural (UK Male - အင်္ဂလန် အမျိုးသား)",
        "en-GB-SoniaNeural (UK Female - အင်္ဂလန် အမျိုးသမီး)"
    ])
    
    selected_voice = voice_option.split(" ")[0]
    
    if st.button("🚀 AI Audio ဖိုင် ထုတ်ယူမည်"):
        if tts_text.strip():
            async def generate_speech():
                communicate = edge_tts.Communicate(tts_text, selected_voice)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                    await communicate.save(tmp_mp3.name)
                    return tmp_mp3.name
            
            with st.spinner("⏳ AI အသံဖိုင် ဖန်တီးနေပါသည်။..."):
                try:
                    audio_path = asyncio.run(generate_speech())
                    st.success("✨ အသံဖိုင် ထွက်ရှိလာပါပြီ။")
                    st.audio(audio_path)
                    
                    with open(audio_path, "rb") as f:
                        st.download_button(
                            label="📥 MP3 Audio ဒေါင်းလုဒ်ရယူရန်",
                            data=f.read(),
                            file_name="ai_voice.mp3",
                            mime="audio/mp3"
                        )
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("စာသား ထည့်သွင်းပေးပါခင်ဗျာ။")

# ---------------------------------------------------------
# TAB 2: 3D Motion Video Generation (Text-to-Video)
# ---------------------------------------------------------
with tab2:
    st.subheader("📝 3D Motion Prompt ရေးပါ")
    st.info("3D ဇာတ်ကောင် လှုပ်ရှားမှုများကို အကန့်အသတ်မရှိ အခမဲ့ ထုတ်နိုင်ပါသည်။")
    
    prompt = st.text_area(
        "Prompt (English)-",
        value="A 3D Pixar style character walking happily and eating food, highly detailed, smooth 3d animation",
        height=100
    )
    
    if st.button("🚀 Free 3D Motion Video ဖန်တီးမည်"):
        if not prompt.strip():
            st.warning("Prompt ထည့်သွင်းပေးပါခင်ဗျာ။")
        else:
            try:
                st.info("⏳ Hugging Face Free Server တွင် 3D Video ကို Render လုပ်နေပါသည်။ စက္ကန့် ၄၀ ခန့် စောင့်ပေးပါ...")
                client = Client("ZeroGPU-Explorers/Text-to-Video")
                result = client.predict(
                    prompt=prompt,
                    api_name="/generate"
                )
                st.success("✨ 3D Video ထုတ်လုပ်မှု အောင်မြင်ပါသည်။")
                st.video(result)
                
                with open(result, "rb") as f:
                    st.download_button(
                        label="📥 ဗီဒီယို ဒေါင်းလုဒ်ရယူရန်",
                        data=f.read(),
                        file_name="3d_motion_video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"Error တက်သွားပါသည် (Server ကျနေပါက ခဏစောင့်ပြီး ပြန်စမ်းပါ): {e}")

# ---------------------------------------------------------
# TAB 3: Free Talking Avatar (SadTalker Engine)
# ---------------------------------------------------------
with tab3:
    st.subheader("📸 ဓာတ်ပုံ သို့မဟုတ် 3D Character ကို ပါးစပ် လှုပ်ရှားခိုင်းမည်")
    st.info("Tab 1 မှ ရလာသော MP3 အသံဖိုင် သို့မဟုတ် ကိုယ်ပိုင် အသံဖိုင် တင်၍ ပါးစပ် လှုပ်ရှားခိုင်းနိုင်ပါသည်။")
    
    img_file = st.file_uploader("3D Character ပုံ တင်ပါ (JPG/PNG)-", type=["jpg", "png", "jpeg"])
    audio_file = st.file_uploader("စကားပြော Audio ဖိုင် တင်ပါ (MP3/WAV)-", type=["mp3", "wav"])
    
    if st.button("🚀 Free Lip-Sync Video ဖန်တီးမည်"):
        if not img_file or not audio_file:
            st.warning("⚠️ ပုံနှင့် Audio ဖိုင် နှစ်ခုစလုံး တင်ပေးရန် လိုအပ်ပါသည်။")
        else:
            try:
                st.info("⏳ AI မှ ပုံနှင့် အသံကို ချိတ်ဆက်နေပါသည်။ ခဏစောင့်ပေးပါ...")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    tmp_img.write(img_file.getvalue())
                    img_path = tmp_img.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_aud:
                    tmp_aud.write(audio_file.getvalue())
                    aud_path = tmp_aud.name

                client = Client("vinthony/SadTalker")
                result = client.predict(
                    source_image=handle_file(img_path),
                    driven_audio=handle_file(aud_path),
                    preprocess="crop",
                    still_mode=True,
                    use_enhancer=False,
                    batch_size=1,
                    size=256,
                    pose_style=0,
                    facerender="faceidness",
                    exp_weight=1,
                    use_ref_video=False,
                    ref_video=None,
                    ref_info="pose",
                    use_idle_mode=False,
                    length_of_pose=0,
                    api_name="/generate"
                )
                
                st.success("✨ Lip-Sync Video အောင်မြင်စွာ ထုတ်ပြီးပါပြီ။")
                st.video(result[0])
                
                with open(result[0], "rb") as f:
                    st.download_button(
                        label="📥 Lip-Sync Video ဒေါင်းလုဒ်ရယူရန်",
                        data=f.read(),
                        file_name="lipsync_avatar.mp4",
                        mime="video/mp4"
                    )
                
                os.remove(img_path)
                os.remove(aud_path)

            except Exception as e:
                st.error(f"Error တက်သွားပါသည်: {e}")
