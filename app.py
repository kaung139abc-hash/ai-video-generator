import google.generativeai as genai
import streamlit as st

st.set_page_config(page_title="Gemini Pro AI Story Generator", page_icon="✨")

st.title("✨ Gemini Pro ဇာတ်လမ်းဖန်တီးရှင်")
st.write(
    "Gemini 1.5 Pro ကို အသုံးပြု၍ သင်လိုချင်သော ဇာတ်လမ်းများကို အလိုအလျောက်"
    " ရေးသားပေးပါမည်။"
)

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

prompt = st.text_area(
    "✍️ ဇာတ်လမ်းအကြောင်းအရာ ရေးပါ (ဥပမာ - ရွာစွန်က သုသာန်ဟောင်းမှာ"
    " တစ္ဆေခြောက်တဲ့ အကြောင်း စိတ်လှုပ်ရှားစရာ ရေးပေးပါ)",
    height=100,
)

if st.button("🚀 ဇာတ်လမ်း ရေးခိုင်းမည်"):
  if not prompt.strip():
    st.warning("ကျေးဇူးပြု၍ ဇာတ်လမ်းအကြောင်းအရာကို ထည့်ပေးပါ။")
  elif not GEMINI_API_KEY:
    st.error(
        "ကျေးဇူးပြု၍ Gemini API Key ကို Streamlit Secrets တွင်"
        " ထည့်သွင်းပေးပါ။"
    )
  else:
    with st.spinner("Gemini Pro မှ ဇာတ်လမ်းကို ဖန်တီးနေပါပြီ... ခဏစောင့်ပါ ⏳"):
      try:
        genai.configure(api_key=GEMINI_API_KEY)

        # Error မတက်စေရန် မော်ဒယ်အမည်အသစ်သို့ ပြောင်းထားသည်
        model = genai.GenerativeModel("gemini-1.5-pro")

        full_prompt = (
            "အောက်ပါ အကြောင်းအရာကို အခြေခံပြီး စိတ်ဝင်စားစရာကောင်းတဲ့"
            f" ဇာတ်လမ်းတစ်ပုဒ်ကို မြန်မာဘာသာဖြင့် ရေးပေးပါ:\n\n{prompt}"
        )

        response = model.generate_content(full_prompt)

        st.success("✅ ဇာတ်လမ်း ရေးသားပြီးပါပြီ!")
        st.markdown("### 📖 သင့်အတွက် ဇာတ်လမ်း")
        st.write(response.text)

      except Exception as e:
        st.error(f"အမှားအယွင်း ဖြစ်ပေါ်နေပါသည် - {e}")
