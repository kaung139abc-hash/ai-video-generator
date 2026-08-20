# ၁။ လိုအပ်တဲ့ library များသွင်းခြင်း
!pip install gTTS moviepy

from gtts import gTTS
import os

# ၂။ Cinematic စကားပြောသံ ဖန်တီးခြင်း
def create_cinematic_audio(text, filename="dialogue.mp3"):
    # Horror/Cinema ဆန်ဆန် အသံထွက်အောင် ချိန်ညှိခြင်း (Language 'my' က မြန်မာစာအတွက်)
    tts = gTTS(text=text, lang='my', slow=False)
    tts.save(filename)
    return filename

# ၃။ ဇာတ်လမ်းစာသား
script = "ရွာသူကြီး: ဒီည ရွာထဲကို နတ်ဆိုးကြီး ဝင်လာပြီ။ အကုန်လုံး တံခါးတွေ ပိတ်ထားကြ။"

# အသံဖိုင်ထုတ်ခြင်း
audio_file = create_cinematic_audio(script)
print(f"ရုပ်ရှင်ဆန်ဆန် အသံဖိုင်ကို {audio_file} အဖြစ် သိမ်းဆည်းလိုက်ပါပြီ။")
