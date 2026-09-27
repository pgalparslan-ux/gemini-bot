import streamlit as st
import google.generativeai as genai

# Sayfa Yapılandırması
st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# API Anahtarın
API_KEY = "AQ.Ab8RN6J_6-EymS1_sAHfxNJwqzlsgZmx37ZlidXSHO7aUlux-w"

# Gemini SDK Yapılandırması
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Geçmiş mesajları hafızada tutma
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana çizdirme
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan mesaj alma
if prompt := st.chat_input("Bir şeyler yazın..."):
    # Kullanıcı mesajını ekrana ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Yanıt Bekleme
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                response = model.generate_content(prompt)
                bot_response = response.text
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            except Exception as e:
                st.error(f"Hata oluştu: {str(e)}")
