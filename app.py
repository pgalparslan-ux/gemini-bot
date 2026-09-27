import json
import urllib.request
import streamlit as st

# Sayfa Ayarları
st.set_page_config(page_title="Gemini AI Sohbet", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

API_KEY = "AQ.Ab8RN6J_6-EymS1_sAHfxNJwqzlsgZmx37ZlidXSHO7aUlux-w"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"

# Sohbet geçmişini hafızada tut
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana yazdır
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan mesaj al
if prompt := st.chat_input("Bir şeyler yazın..."):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Yapay zekaya istek gönder
    tam_mesaj = f"Sadece Türkçe yanıt ver. Cevabının sonuna veya yanına kesinlikle İngilizce çeviri, parantez içi açıklama EKLEME. Kullanıcı mesajı: {prompt}"
    payload = {"contents": [{"parts": [{"text": tam_mesaj}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})

    with st.chat_message("assistant"):
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                cevap = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                st.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap})
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
