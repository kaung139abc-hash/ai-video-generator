import streamlit as st
from gradio_client import Client

st.set_page_config(page_title="3D Horror Studio", layout="centered")

st.title("🎬 Cinematic 3D Horror Studio")
st.write("✨ ရုပ်ရှင်အဆင့်မီ Cinematic 3D Character များဖြင့် ဗီဒီယို ဖန်တီးပေးသည့် စနစ်")

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
        try:
            with st.spinner("🎬 Colab GPU ဖြင့် ဗီဒီယို ထုတ်လုပ်နေပါသည်... ခဏစောင့်ပါ..."):
                client = Client(colab_url)
                # api_name ကို False ထားပေးထားပါသည်
                result = client.predict(script, api_name=False)
                st.success("✨ ဗီဒီယို ဖန်တီးမှု အောင်မြင်ပါပြီ။")
                st.video(result)
                with open(result, "rb") as f:
                    st.download_button("📥 MP4 Download", data=f.read(), file_name="3D_Horror.mp4", mime="video/mp4")
        except Exception as e:
            st.error(f"❌ Error ဖြစ်သွားပါသည်: {e}")
