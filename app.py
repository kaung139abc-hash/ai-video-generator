import os
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

st.title("🎙️ AI Voice Studio (Deep Male & Horror Voice)")

# အသံအမျိုးအစား ရွေးချယ်စရာများ
voice_style = st.selectbox(
    "အသံစတိုင်/အမျိုးအစားကို ရွေးပါ -",
    [
        "ယောက်ျားအသံနက်နက် (Deep Male Voice)",
        "ဟောရာဆန်ဆန်/တစ္ဆေသံ (Horror/Creepy Style)",
        "ပုံမှန်အသံ (Normal Voice)"
    ]
)

user_text = st.text_area("အသံထုတ်လိုသော စာသားများကို ရိုက်ထည့်ပါ -", "ည ၁၂ နာရီ တိတိ။ တိတ်ဆိတ်ငြိမ်သက်နေတဲ့ အခန်းထဲမှာ...")

if st.button("အသံဖိုင် ထုတ်မည်"):
    if user_text:
        with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            os.makedirs("output_audio", exist_ok=True)
            temp_file = "output_audio/temp.mp3"
            output_file = "output_audio/final_voice.mp3"
            
            # gTTS ဖြင့် ပုံမှန်အသံ အရင်ထုတ်ခြင်း
            tts = gTTS(text=user_text, lang='my', slow=False)
            tts.save(temp_file)
            
            # pydub ဖြင့် အသံကို ယောက်ျားအသံနက်နက် သို့မဟုတ် ဟောရာစတိုင်ဖြစ်အောင် ပြောင်းလဲခြင်း
            sound = AudioSegment.from_mp3(temp_file)
            
            if "ယောက်ျားအသံနက်နက်" in voice_style or "ဟောရာဆန်ဆန်" in voice_style:
                # အသံကို ပိုနိမ့်သွားအောင် (Pitch ကျအောင်) ပြုလုပ်ခြင်းဖြင့် ယောက်ျားသံနက် သို့မဟုတ် ကြောက်စရာအသံ ပုံစံဖော်ခြင်း
                # sample_rate ကို ချိန်ညှိခြင်းဖြင့် အသံထွက်ကို ထူထဲနက်ရှိုင်းစေသည်
                new_sample_rate = int(sound.frame_rate * 0.8) # အသံကို ပိုထူပြီး နက်စေရန်
                deep_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
                deep_sound = deep_sound.set_frame_rate(44100)
                deep_sound.export(output_file, format="mp3")
            else:
                sound.export(output_file, format="mp3")
            
            st.success("အသံဖိုင် အောင်မြင်စွာ ထွက်ရှိပါပြီ!")
            st.audio(output_file)
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားထည့်ပါ။")
