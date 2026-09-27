import streamlit as st
from google import genai

# Sayfa Yapılandırması
st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# Streamlit Secrets üzerinden API Anahtarını al
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

# Yeni resmi Google GenAI istemcisini başlat
client = genai.Client(api_key=api_key)

# Geçmiş mesajları hafızada tutma
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana çizdirme
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan mesaj alma
if prompt := st.chat_input("Bir şeyler yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                # Ana Model İsteği
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                )
                bot_response = response.text
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            except Exception as e:
                # 503 Sunucu Yoğunluğu Hatasında Yedek Modele Geçiş
                if "503" in str(e):
                    try:
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=prompt,
                        )
                        bot_response = response.text
                        st.markdown(bot_response)
                        st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    except Exception as fallback_error:
                        st.error("Sunucular şu an çok yoğun, lütfen birkaç saniye sonra tekrar deneyin.")
                else:
                    st.error(f"Hata oluştu: {str(e)}")
