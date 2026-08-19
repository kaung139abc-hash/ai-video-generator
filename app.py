import streamlit as st
from gradio_client import Client, handle_file
import tempfile
import os

st.set_page_config(page_title="Free 3D AI Video Studio", layout="centered")
st.title("🎬 100% Free AI 3D Video Studio")
st.caption("✨ Hugging Face ရဲ့ Free AI Engine များကို တိုက်ရိုက် ချိတ်ဆက်ထားပါသည်။")

tab1, tab2 = st.tabs(["🎥 3D Motion Video (Text to Video)", "🗣️ Free Lip-Sync Avatar"])

# ---------------------------------------------------------
# TAB 1: 3D Motion Video Generation (Text-to-Video)
# ---------------------------------------------------------
with tab1:
    st.subheader("📝 3D Motion Prompt ရေးပါ")
    st.info("လမ်းလျှောက်ခြင်း၊ ထမင်းစားခြင်း စသည့် 3D ဇာတ်ကောင် လှုပ်ရှားမှုများကို အကန့်အသတ်မရှိ အခမဲ့ ထုတ်နိုင်ပါသည်။")
    
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
                st.info("⏳ Hugging Face Free Server တွင် 3D Video ကို Render လုပ်နေပါသည်။ စက္ကန့် ၄၀ မှ ၁ မိနစ်ခန့် စောင့်ပေးပါ...")
                
                # Hugging Face Free Text-to-Video Engine သို့ ချိတ်ဆက်ခြင်း
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
# TAB 2: Free Talking Avatar (SadTalker Engine)
# ---------------------------------------------------------
with tab2:
    st.subheader("📸 ဓာတ်ပုံ သို့မဟုတ် 3D Character ကို ပါးစပ် လှုပ်ရှားခိုင်းမည်")
    st.info("D-ID မလိုဘဲ Free SadTalker AI ဖြင့် နှုတ်ခမ်း လှုပ်ရှားပေးပါမည်။")
    
    img_file = st.file_uploader("3D Character ပုံ တင်ပါ (JPG/PNG)-", type=["jpg", "png", "jpeg"])
    audio_file = st.file_uploader("စကားပြော Audio ဖိုင် တင်ပါ (MP3/WAV)-", type=["mp3", "wav"])
    
    if st.button("🚀 Free Lip-Sync Video ဖန်တီးမည်"):
        if not img_file or not audio_file:
            st.warning("⚠️ ပုံနှင့် Audio ဖိုင် နှစ်ခုစလုံး တင်ပေးရန် လိုအပ်ပါသည်။")
        else:
            try:
                st.info("⏳ AI မှ ပုံနှင့် အသံကို ချိတ်ဆက်နေပါသည်။ ခဏစောင့်ပေးပါ...")
                
                # Temp ဖိုင်များ တည်ဆောက်ခြင်း
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    tmp_img.write(img_file.getvalue())
                    img_path = tmp_img.name

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_aud:
                    tmp_aud.write(audio_file.getvalue())
                    aud_path = tmp_aud.name

                # SadTalker Free Engine သို့ ချိတ်ဆက်ခြင်း
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
                
                # Cleanup Temp Files
                os.remove(img_path)
                os.remove(aud_path)

            except Exception as e:
                st.error(f"Error တက်သွားပါသည်: {e}")
