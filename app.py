import time
import uuid
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="VorpH AI",
    page_icon="",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #e0e0e0 !important; }
    h1, h2, h3 { color: #ffffff !important; }
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1a1a1a !important;
    }
    .stChatInputContainer {
        background-color: #0a0a0a !important;
        border: 1px solid #222 !important;
        border-radius: 16px !important;
    }
    button { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_context" not in st.session_state:
    st.session_state.file_context = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

api_key = st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("Secrets icinde OPENROUTER_API_KEY bulunamadi")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "VorpH AI"}
)

with st.sidebar:
    st.title("VorpH Kontrol")
    
    user_name = st.text_input("Isminiz", value=st.session_state.user_name, placeholder="Ornek Ahmet")
    st.session_state.user_name = user_name
    st.markdown("---")
    
    personality = st.selectbox(
        "Asistan Modu",
        ["Genel Asistan", "Detayli Uzman", "Yazilim Uzmami", "Resmi"]
    )

    model_choice = st.selectbox(
        "Model",
        ["Hizli ve Ucuz", "Akilli", "Dengeli"],
        index=0
    )
    model_map = {
        "Hizli ve Ucuz": "google/gemini-2.0-flash-001",
        "Akilli": "meta-llama/llama-3.3-70b-instruct",
        "Dengeli": "openrouter/auto"
    }
    selected_model = model_map[model_choice]

    st.markdown("---")
    st.subheader("Belge ile Sohbet")
    uploaded_file = st.file_uploader("PDF veya TXT yukle", type=["pdf", "txt"])
    
    if uploaded_file:
        try:
            if uploaded_file.type == "application/pdf":
                import fitz
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([page.get_text() for page in doc])
            else:
                text = uploaded_file.read().decode("utf-8", errors="ignore")
            
            st.session_state.file_context = text[:15000]
            st.success("Dosya yuklendi")
        except Exception as e:
            st.error(f"Dosya okunamadi: {e}")
    else:
        if st.session_state.file_context:
            if st.button("Yuklenen Dosyayi Kaldir"):
                st.session_state.file_context = ""
                st.rerun()

    st.markdown("---")
    if st.button("Sohbeti Sifirla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.session_state.messages:
        chat_text = "\n\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        st.download_button("Sohbeti Indir", chat_text, file_name="vorph_sohbet.txt", use_container_width=True)

# System prompt
user_name_val = st.session_state.get("user_name", "")
name_prompt = ""
if user_name_val:
    name_prompt = " Kullanicinin adi " + user_name_val + " ve ona ismiyle hitap et."

file_prompt = ""
if st.session_state.file_context:
    file_prompt = " Kullanici belge yukledi, belgeyi dikkate al. Belge: " + st.session_state.file_context

personality_prompts = {
    "Genel Asistan": "Sen VorpH adinda yardimsever bir asistansin.",
    "Detayli Uzman": "Sen VorpH adinda detayci bir uzmansin. Ornekler ve artilar eksiler ver.",
    "Yazilim Uzmami": "Sen VorpH adinda senior yazilim mimarisin. Temiz kod ver.",
    "Resmi": "Sen VorpH adinda resmi dille yazan bir asistansin."
}

system_instruction = personality_prompts[personality] + name_prompt + file_prompt + " Tum yanitlarini Turkce ver."

st.title("VorpH AI")
st.caption(f"ID: {st.session_state.user_id} | Model: {selected_model}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("Bir sey sor...")

if user_prompt:
    if "last_request_time" in st.session_state and time.time() - st.session_state.last_request_time < 1.5:
        st.warning("Cok hizlisin, 2 saniye bekle.")
        st.stop()
    st.session_state.last_request_time = time.time()

    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        try:
            api_messages = [{"role": "system", "content": system_instruction}]
            api_messages.extend(st.session_state.messages)

            stream = client.chat.completions.create(
                model=selected_model,
                messages=api_messages,
                stream=True,
                temperature=0.7,
            )
            
            full_response = st.write_stream(
                (chunk.choices[0].delta.content for chunk in stream if chunk.choices[0].delta.content)
            )
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Model hatasi: {str(e)}")
