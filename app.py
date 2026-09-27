import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# API Anahtarını al
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Anahtarı Streamlit Secrets içinde bulunamadı!")
    st.stop()

# İstemciyi başlat
client = genai.Client(api_key=api_key)

config = types.GenerateContentConfig(
    system_instruction="Sen her zaman Türkçe cevap veren yardımsever bir yapay zeka asistanısın."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Bir şeyler yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                # Doğrudan en kararlı model
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config=config
                )
                bot_response = response.text
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            except Exception as e:
                # Gerçek hatayı ekrana basıyoruz
                st.error(f"Sistem Hatası: {str(e)}")
