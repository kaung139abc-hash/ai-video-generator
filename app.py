import streamlit as st
import requests
import time
import tempfile
import os
import ffmpeg

st.set_page_config(page_title="AI 3D Lip-Sync Story Generator", layout="centered")
st.title("🎭 AI 3D Cartoon Lip-Sync Video Generator")

API_KEY = st.secrets.get("DID_API_KEY", "")

if not API_KEY:
    st.error("⚠️ Streamlit Secrets ထဲတွင် `DID_API_KEY` ထည့်သွင်းပေးပါ။")
    st.stop()

PRESENTERS = {
    "Male 1 (Matt)": "matt",
    "Female 1 (Amy)": "amy",
    "Male 2 (Jack)": "jack",
    "Female 2 (Lori)": "lori"
}

st.sidebar.header("⚙️ Settings")
char1_p = st.sidebar.selectbox("Character 1 (Male/Female)-", list(PRESENTERS.keys()), index=0)
char2_p = st.sidebar.selectbox("Character 2 (Male/Female)-", list(PRESENTERS.keys()), index=1)

def create_talk(presenter_id, text, voice_id):
    url = "https://api.d-id.com/talks"
    headers = {"Authorization": f"Basic {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "script": {"type": "text", "input": text, "provider": {"type": "microsoft", "voice_id": voice_id}},
        "presenter_id": presenter_id
    }
    return requests.post(url, json=payload, headers=headers).json()

def get_talk_status(talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {API_KEY}"}
    return requests.get(url, headers=headers).json()

st.subheader("📝 Dialogue Input")
default_text = "Character 1: Do you hear that strange voice?\nCharacter 2: Yes, run before it catches us!"
dialogue_text = st.text_area("စကားပြော Dialogue ရေးပါ-", value=default_text, height=150)

if st.button("🚀 ဗီဒီယို တစ်ပုဒ်တည်း အပြီးပေါင်းထုတ်မည်"):
    lines = [line.strip() for line in dialogue_text.strip().split("\n") if line.strip()]
    
    if lines:
        video_files = []
        temp_dir = tempfile.mkdtemp()
        
        st.info("⏳ AI မှ စကားပြော ဗီဒီယိုများကို စတင်ဖန်တီးနေပါသည်။...")
        progress_bar = st.progress(0)
        
        success = True
        for index, line in enumerate(lines):
            clean_text = line.split(":", 1)[1].strip() if ":" in line else line
            is_char2 = ("Character 2" in line or "ဇာတ်ကောင် ၂" in line)
            
            selected_char = char2_p if is_char2 else char1_p
            p_id = PRESENTERS[selected_char]
            
            # အသံ အလိုအလျောက် ရွေးချယ်ခြင်း
            voice_id = "en-US-JennyNeural" if ("Female" in selected_char or "Amy" in selected_char or "Lori" in selected_char) else "en-US-GuyNeural"

            res = create_talk(p_id, clean_text, voice_id)
            
            if "id" in res:
                talk_id = res["id"]
                st.write(f"🎬 Line {index+1} ကို Process လုပ်နေပါပြီ...")
                
                while True:
                    status_res = get_talk_status(talk_id)
                    status = status_res.get("status")
                    
                    if status == "done":
                        v_url = status_res.get("result_url")
                        # Video file ဒေါင်းလုဒ်ဆွဲပြီး Temp ထဲသိမ်းခြင်း
                        v_bytes = requests.get(v_url).content
                        file_path = os.path.join(temp_dir, f"clip_{index}.mp4")
                        with open(file_path, "wb") as f:
                            f.write(v_bytes)
                        video_files.append(file_path)
                        break
                    elif status == "error":
                        st.error(f"Line {index+1} မှာ Error တက်သွားပါသည်")
                        success = False
                        break
                    time.sleep(2)
            else:
                st.error(f"D-ID API Error: {res}")
                success = False
                break
            
            progress_bar.progress(int(((index + 1) / len(lines)) * 50))

        # ဗီဒီယိုများကို FFmpeg ဖြင့် ၁ ပုဒ်တည်း ဖြစ်အောင် ပေါင်းစပ်ခြင်း
        if success and len(video_files) == len(lines):
            st.info("🎬 ဗီဒီယို အပိုင်းအစများကို တစ်ပုဒ်တည်းဖြစ်အောင် ပေါင်းစပ်နေပါသည်။...")
            
            list_file_path = os.path.join(temp_dir, "files.txt")
            with open(list_file_path, "w") as f:
                for vf in video_files:
                    f.write(f"file '{vf}'\n")
            
            output_combined_path = os.path.join(temp_dir, "final_story.mp4")
            
            try:
                # FFmpeg concat command
                (
                    ffmpeg
                    .input(list_file_path, format='concat', safe=0)
                    .output(output_combined_path, c='copy')
                    .run(overwrite_output=True, quiet=True)
                )
                
                progress_bar.progress(100)
                st.success("✨ ဗီဒီယို ပေါင်းစပ်မှု အောင်မြင်ပါသည်။")
                
                # ပြသခြင်းနှင့် ဒေါင်းလုဒ်ပေးခြင်း
                st.video(output_combined_path)
                
                with open(output_combined_path, "rb") as f:
                    st.download_button(
                        label="📥 ဗီဒီယိုအပြည့်အစုံ (Full Video) ဒေါင်းလုဒ်ရယူရန်",
                        data=f.read(),
                        file_name="full_story_video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"Video Concatenation Error: {e}")
