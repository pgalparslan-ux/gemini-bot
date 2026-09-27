import streamlit as st
from openai import OpenAI

st.title("AI Asistanı")

# OpenRouter API Anahtarınızı Streamlit secrets veya input ile alın
api_key = st.secrets.get("OPENROUTER_API_KEY") or st.sidebar.text_input("OpenRouter API Key", type="password")

if not api_key:
    st.info("Lütfen devam etmek için OpenRouter API anahtarınızı girin.")
    st.stop()

# OpenAI İstemcisini OpenRouter URL'si ile başlatın
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

user_prompt = st.text_input("Sorunuzu yazın:")

if st.button("Gönder"):
    if user_prompt:
        with st.spinner("Yanıt bekleniyor..."):
            try:
                response = client.chat.completions.create(
                    model="openrouter/free",  # 👈 Değişen kısım burası
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Hata oluştu: {e}")
