import time
import uuid
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="VorpH AI",
    page_icon="◼️",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #e0e0e0 !important; }
    h1, h2, h3 { color: #ffffff !important; letter-spacing: -0.5px; }
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
    st.error("Secrets icinde OPENROUTER_API_KEY bulunamadi!")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "VorpH AI"}
)

with st.sidebar:
    st.title("VorpH Kontrol")
    
    user_name = st.text_input("Isminiz:", value=st.session_state.user_name, placeholder="Orn: Ahmet")
    st.session_state.user_name = user_name

    st.markdown("---")
    
    personality = st.selectbox(
        "Asistan Modu",
        ["Genel Asistan", "Detayli Uzman", "Yazilim Uzmami", "Resmi / Akademik"]
    )

    model_choice = st.selectbox(
        "Model",
        ["Hizli & Ucuz (Gemini 2.0 Flash)", "Akilli (Llama 3.3 70B)", "Dengeli (Auto)"],
        index=0
    )
    model_map = {
        "Hizli & Ucuz (Gemini 2.0 Flash)": "google/gemini-2.0-flash-001",
        "Akilli (Llama 3.3 70B)": "meta-llama/llama-3.3-70b-instruct",
        "Dengeli (Auto)": "openrouter/auto"
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
            st.success(f"Dosya yuklendi: {len(text)} karakter")
        except Exception as e:
            st.error(f"Dosya okunamadi: {e}")
    else:
        if st.session_state.file_context:
            if st.button("Yuklenen Dosyayi Kaldir"):
                st.session_state.file_context = ""
                st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sohbeti Sifirla", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.session_state.messages:
            chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button("Indir", chat_text, file_name="vorph_sohbet.txt", use_container_width=True)

# --- DUZELTILMIS KISIM BURASI ---
user_name_val = st.session_state.get("user_name", "")
if user_name_val:
    name_prompt = f" Kullanicinin adi {user_name_val} ve ona ismiyle hitap et."
else:
    name_prompt = ""

if st.session_state.file_context:
    file_prompt = f"\n\nKullanici bir belge yukledi, bu belgeyi dikkate alarak cevap ver. Belge Icerigi:\n{st.session_state.file_context}\n"
else:
    file_prompt = ""

personality_prompts = {
    "Genel Asistan": "Sen VorpH adinda yardimsever, net ve samimi bir asistansin.",
    "Detayli Uzman": "Sen VorpH adinda detayci bir uzmansin. Her cevabinda ornekler, artilar/eksiler ve kaynak mantigi ver.",
    "Yazilim Uzmami": "Sen VorpH adinda senior bir yazilim mimarisin. Kod verirken temiz, yorum satirli ve en iyi pratiklere uygun yaz.",
    "Resmi / Akademik": "Sen VorpH adinda resmi ve akademik dille yazan bir asistansin. Cevaplarin yapilandirilmis ve profesyonel olsun."
}

system_instruction = personality_prompts[personality] + name_prompt + file_prompt + " Tum yanitlarini Turkce ver."

st.title("VorpH AI")
st.caption(f"ID: {st.session_state.user_id} | Model: {selected_model}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("
