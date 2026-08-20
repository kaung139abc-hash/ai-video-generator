import streamlit as st
from gradio_client import Client

st.set_page_config(page_title="Cinematic 3D Horror Studio", layout="centered")

st.title("🎬 Cinematic 3D Horror Studio")
st.write("✨ ဝတ္ထုဇာတ်လမ်းမှသည် ရုပ်ရှင်အဆင့်မီ ဇာတ်ကောင် လှုပ်ရှားဗီဒီယိုများ ဖန်တီးသည့်စနစ်")

# Colab မှ ထွက်လာသော Gradio URL ကို ဤနေရာတွင် ထည့်ပါ
colab_url = st.sidebar.text_input("🔗 Colab Gradio URL ထည့်ပါ:", placeholder="https://xxxx.gradio.live")

default_script = """ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး တံခါးတွေ ပိတ်ထားကြ။
မိန်းကလေး: ကိုကို... ဒီရွာပျက်ကြီးထဲကို ဝင်ဖို့ တကယ်ပဲ လိုလို့လား။
ကောင်လေး: မကြောက်ပါနဲ့ ညီမလေးရယ်။ ငါတို့ ဒီည သဲလွန်စ ရှာရမယ်။
နတ်ဆိုးကြီး: ဟားဟားဟား... မင်းတို့ ငါ့ရဲ့ နယ်မြေထဲ ဝင်လာခဲ့ပြီပဲ။"""

script = st.text_area("📝 ဝတ္ထု ဇာတ်လမ်း စာသားများ ရိုက်ထည့်ပါ:", value=default_script, height=200)

if st.button("🚀 ရုပ်ရှင်ဇာတ်ကား ဖန်တီးမည်"):
    if not colab_url:
        st.error("⚠️ ကျေးဇူးပြု၍ ဘေးဘက် Sidebar (>) တွင် Colab URL ထည့်ပေးပါ။")
    elif not script.strip():
        st.warning("⚠️ ဇာတ်လမ်း စာသားများ ထည့်သွင်းပေးပါ။")
    else:
        with st.spinner("🎬 AI ဖြင့် ဇာတ်ကောင် အမူအရာနှင့် အသံများကို တွဲစပ်နေပါသည် (အချိန်အနည်းငယ်ကြာတတ်သည်)..."):
            try:
                # Colab ဆာဗာသို့ လှမ်းချိတ်ဆက်၍ ဗီဒီယိုထုတ်ခိုင်းခြင်း (Timeout များကို ၁၅ မိနစ်အထိ တိုးမြှင့်ထားသည်)
                client = Client(colab_url.strip())
                result_video = client.predict(script_text=script, api_name="/predict", timeout=900)
                
                st.success("✨ ရုပ်ရှင်ဇာတ်ကား ဖန်တီးမှု အောင်မြင်ပါပြီ။")
                
                # ထွက်လာသော MP4 ဗီဒီယိုကို ပြသခြင်းနှင့် Download ဆွဲခွင့်ပေးခြင်း
                st.video(result_video)
                with open(result_video, "rb") as f:
                    st.download_button("📥 MP4 Movie Download", data=f.read(), file_name="Cinematic_Horror.mp4", mime="video/mp4")
                    
            except Exception as e:
                st.error(f"❌ ချိတ်ဆက်မှု အမှားဖြစ်သွားပါသည်: {e}")
