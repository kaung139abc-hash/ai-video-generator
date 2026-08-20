import streamlit as st
import requests

st.set_page_config(page_title="3D Horror Studio", layout="centered")

st.title("🎬 Cinematic 3D Horror Studio")
st.write("✨ ရုပ်ရှင်အဆင့်မီ Cinematic 3D Character များဖြင့် ဗီဒီယို ဖန်တီးပေးသည့် စနစ်")

# Sidebar
colab_url = st.sidebar.text_input("🔗 Colab Gradio URL ထည့်ပါ:", placeholder="https://xxxx.gradio.live")

default_script = """ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး တံခါးတွေ ပိတ်ထားကြ။
မိန်းကလေး: ကိုကို... ဒီရွာပျက်ကြီးထဲကို ဝင်ဖို့ တကယ်ပဲ လိုလို့လား။
ကောင်လေး: မကြောက်ပါနဲ့ ညီမလေးရယ်။ ငါတို့ ဒီည သဲလွန်စ ရှာရမယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ငါ့ရဲ့ နယ်မြေထဲ ဝင်လာခဲ့ပြီပဲ။"""

script = st.text_area("📝 ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ:", value=default_script, height=200)

if st.button("🚀 Cinematic 3D Video ဖန်တီးမည်"):
    if not colab_url:
        st.error("⚠️ ဘေးဘက် Sidebar (>) တွင် Colab URL အရင်ထည့်ပေးပါခင်ဗျာ။")
    else:
        # URL အဆုံးရှိ / များကို ရှင်းလင်းခြင်း
        clean_url = colab_url.strip().rstrip('/')
        api_endpoint = f"{clean_url}/api/predict"

        try:
            with st.spinner("🎬 Colab GPU ဖြင့် ဗီဒီယို ထုတ်လုပ်နေပါသည်... ခဏစောင့်ပါ..."):
                response = requests.post(
                    api_endpoint, 
                    json={"data": [script]},
                    timeout=300
                )
                
                if response.status_code == 200:
                    res_data = response.json()
                    # Gradio response မှ video path/URL ရယူခြင်း
                    video_info = res_data["data"][0]
                    video_url = video_info["url"] if isinstance(video_info, dict) and "url" in video_info else video_info

                    st.success("✨ ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါပြီ။")
                    st.video(video_url)
                else:
                    st.error(f"❌ Colab Server Error Code: {response.status_code}")

        except Exception as e:
            st.error(f"❌ ချိတ်ဆက်မှု အမှားဖြစ်သွားပါသည်: {e}")
