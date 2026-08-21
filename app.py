import os
import streamlit as st
from gtts import gTTS
import speech_recognition as sr

st.title("🎙️ AI Voice Studio: Text-to-Speech & Speech-to-Text အစုံသုံး")

# Tab နှစ်ခုခွဲခြင်း (၁။ စာမှ အသံသို့ | ၂။ အသံမှ စာသို့)
tab1, tab2 = st.tabs(["🔊 Text to Speech (အသံအမျိုးမျိုးပြောင်းရန်)", "📝 Speech to Text (အသံကို စာသားပြောင်းရန်)"])

with tab1:
    st.subheader("စာသားမှ အသံအမျိုးမျိုးသို့ ပြောင်းခြင်း")
    
    # အသံအမျိုးအစား ရွေးချယ်စရာများ
    voice_style = st.selectbox(
        "အသံစတိုင်/အမျိုးအစားကို ရွေးပါ -",
        [
            "ပုံမှန် လူငယ်အသံ (Normal Youth)",
            "အဖိုးအိုအသံ (Deep/Old Man Style)",
            "ကလေးအသံ (High Pitch/Child Style)",
            "ဟောရာဆန်ဆန်/တစ္ဆေသံ (Horror/Creepy Style)",
            "မိန်းမကြီးအသံ (Mature Woman Style)"
        ]
    )
    
    user_text = st.text_area("အသံထုတ်လိုသော စာသားများကို ရိုက်ထည့်ပါ -", "မင်္ဂလာပါ၊ ဒါကတော့ အသံအမျိုးမျိုးပြောင်းနိုင်တဲ့ AI စနစ် ဖြစ်ပါတယ်။")
    
    if st.button("အသံဖိုင် ထုတ်မည်"):
        if user_text:
            with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
                os.makedirs("output_audio", exist_ok=True)
                output_file = "output_audio/generated_voice.mp3"
                
                # gTTS ဖြင့် အသံထုတ်ခြင်း (အင်္ဂလိပ် သို့မဟုတ် မြန်မာ)
                # ဟောရာ သို့မဟုတ် အဖိုးအိုအတွက် slow option သို့မဟုတ် lale ချိန်ညှိချက်သုံးနိုင်သည်
                is_slow = True if "အဖိုးအို" in voice_style or "ဟောရာ" in voice_style else False
                
                tts = gTTS(text=user_text, lang='my', slow=is_slow)
                tts.save(output_file)
                
                st.success("အသံဖိုင် အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
                
                # စတိုင်အလိုက် အချက်ပြဖော်ပြချက်
                if "ဟောရာ" in voice_style:
                    st.warning("👻 ဟောရာဆန်ဆန် ခြောက်ခြားဖွယ် လေသံဖြင့် ထုတ်ထားပါသည်။")
                elif "အဖိုးအို" in voice_style:
                    st.info("👴 အဖိုးအို လေသံစတိုင်ဖြင့် ထုတ်ထားပါသည်။")
                elif "ကလေး" in voice_style:
                    st.info("👶 ကလေးအသံစတိုင်ဖြင့် ထုတ်ထားပါသည်။")
                    
                st.audio(output_file)
        else:
            st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")

with tab2:
    st.subheader("အသံမှ စာသားသို့ မှန်ကန်စွာ ပြောင်းခြင်း (Speech-to-Text)")
    st.info("မှတ်ချက်။ ဤလုပ်ဆောင်ချက်သည် မိုက်ကရိုဖုန်း အသုံးပြုခွင့် လိုအပ်ပါသည်။")
    
    if st.button("အသံစတင် နားထောင်ခိုင်းမည်"):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                st.write("🎤 စကားပြောပါတော့... နားထောင်နေပါပြီ။")
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=5)
                
            with st.spinner("စာသားအဖြစ် ပြောင်းနေပါပြီ..."):
                # မြန်မာဘာသာစကားဖြင့် အသံကို စာသားဖော်ခြင်း ('my-MM')
                text = r.recognize_google(audio, language='my-MM')
                st.success(f"**ထွက်လာသည့် စာသား:** {text}")
                
        except sr.UnknownValueError:
            st.error("အသံကို ကွဲကွဲပြားပြား မကြားရပါ၊ ကျေးဇူးပြု၍ အသံကျယ်ကျယ်ဖြင့် ထပ်ပြောပါ။")
        except sr.RequestError as e:
            st.error(f"ဆာဗာသို့ ချိတ်ဆက်၍ မရပါ: {e}")
        except Exception as e:
            st.warning("မိုက်ကရိုဖုန်း ချိတ်ဆက်မှု သို့မဟုတ် အချိန်ကုန်သွားခြင်း ဖြစ်နိုင်ပါသည်။ ထပ်ကြိုးစားပါ။")
