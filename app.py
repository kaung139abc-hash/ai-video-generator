import os
import streamlit as st
from gtts import gTTS

st.title("AI Video Generator & Text-to-Speech")

# စာသားထည့်ရန် Input Box
user_text = st.text_area("အသံပြောင်းလိုသော စာသားများကို ဤနေရာတွင် ရိုက်ထည့်ပါ သို့မဟုတ် ထည့်ပါ -", "ဒီနေရာမှာ ဇာတ်လမ်းစာသားများကို ထည့်နိုင်ပါတယ်။")

if st.button("အသံဖိုင် ထုတ်ယူမည်"):
    if user_text:
        with st.spinner("အသံဖိုင် ဖန်တီးနေပါပြီ..."):
            # စာလုံးရေ အများကြီးဆိုရင် အပိုင်းခွဲထုတ်ခြင်း
            max_length = 400
            chunks = [user_text[i:i+max_length] for i in range(0, len(user_text), max_length)]
            
            os.makedirs("output_audio", exist_ok=True)
            
            for index, chunk in enumerate(chunks):
                tts = gTTS(text=chunk, lang='my', slow=False)
                output_file = f"output_audio/part_{index+1}.mp3"
                tts.save(output_file)
            
            st.success("အသံဖိုင်များ အောင်မြင်စွာ ထွက်ရှိပြီးပါပြီ!")
            
            # ထွက်လာတဲ့ အသံဖိုင်များကို Play ပြရန်နဲ့ Download ဆွဲရန်ပြသခြင်း
            for index in range(len(chunks)):
                file_path = f"output_audio/part_{index+1}.mp3"
                st.audio(file_path)
    else:
        st.warning("ကျေးဇူးပြု၍ စာသားအနည်းဆုံး တစ်ခုခု ထည့်ပေးပါ။")
