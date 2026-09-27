import streamlit as st
import requests

# Sayfa Yapılandırması
st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# API Anahtarın (aistudio.google.com'dan aldığın geçerli anahtar)
API_KEY = "AQ.Ab8RN6J_6-EymS1_sAHfxNJwqzlsgZmx37ZlidXSHO7aUlux-w"

# Güncel Gemini 1.5 Flash Endpoint
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

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

    # API İsteği Hazırlama
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    
    headers = {'Content-Type': 'application/json'}

    # Yanıt Bekleme
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                response = requests.post(URL, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    bot_response = result['candidates'][0]['content']['parts'][0]['text']
                    st.markdown(bot_response)
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                else:
                    st.error(f"Hata oluştu: HTTP Error {response.status_code}\n\nDetay: {response.text}")
            except Exception as e:
                st.error(f"Bağlantı hatası: {str(e)}")
