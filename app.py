import time
import uuid
import streamlit as st
from openai import OpenAI

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="VorpH AI",
    page_icon="◼️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- MONOKROM CSS ---
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

# --- SESSION ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_context" not in st.session_state:
    st.session_state.file_context = ""

# --- API ---
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("Secrets içinde OPENROUTER_API_KEY bulunamadı! Streamlit > Settings > Secrets kısmına ekle.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "VorpH AI"}
)

# --- SIDEBAR ---
with st.sidebar:
    st.title("VorpH Kontrol")
    
    user_name = st.text_input("İsminiz:", value=st.session_state.get("user_name", ""), placeholder="Örn: Ahmet")
    if user_name:
        st.session_state.user_name = user_name

    st.markdown("---")
    
    personality = st.selectbox(
        "Asistan Modu",
        ["Genel Asistan", "Detaylı Uzman", "Yazılım Uzmanı", "Resmi / Akademik"]
    )

    model_choice = st.selectbox(
        "Model",
        ["Hızlı & Ucuz (Gemini 2.0 Flash)", "Akıllı (Llama 3.3 70B)", "Dengeli (Auto)"],
        index=0
    )
    model_map = {
        "Hızlı & Ucuz (Gemini 2.0 Flash)": "google/gemini-2.0-flash-001",
        "Akıllı (Llama 3.3 70B)": "meta-llama/llama-3.3-70b-instruct",
        "Dengeli (Auto)": "openrouter/auto"
    }
    selected_model = model_map[model_choice]

    st.markdown("---")
    st.subheader("Belge ile Sohbet")
    uploaded_file = st.file_uploader("PDF veya TXT yükle", type=["pdf", "txt"])
    
    if uploaded_file:
        try:
            if uploaded_file.type == "application/pdf":
                import fitz  # PyMuPDF
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([page.get_text() for page in doc])
            else:
                text = uploaded_file.read().decode("utf-8", errors="ignore")
            
            st.session_state.file_context = text[:15000]  # İlk 15k karakteri al
            st.success(f"Dosya yüklendi: {len(text)} karakter")
        except Exception as e:
            st.error(f"Dosya okunamadı: {e}")
    else:
        if st.session_state.file_context:
            if st.button("Yüklenen Dosyayı Kaldır"):
                st.session_state.file_context = ""
                st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sohbeti Sıfırla", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        # Sohbeti indir
        if st.session_state.messages:
            chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button("İndir", chat_text, file_name="vorph_sohbet.txt", use_container_width=True)

# --- SYSTEM PROMPT MANTIĞI ---
personality_prompts = {
    "Genel Asistan": "Sen VorpH adında yardımsever, net ve samimi bir asistansın.",
    "Detaylı Uzman": "Sen VorpH adında detaycı bir uzmansın. Her cevabında örnekler, artılar/eksiler ve kaynak mantığı ver.",
    "Yazılım Uzmanı": "Sen VorpH adında senior bir yazılım mimarısın. Kod verirken temiz, yorum satırlı ve en iyi pratiklere uygun yaz. Gereksiz açıklama yapma.",
    "Resmi / Akademik": "Sen VorpH adında resmi ve akademik dille yazan bir asistansın. Cevapların yapılandırılmış ve profesyonel olsun."
}

name_prompt = f" Kullanıcının adı {st.session_state.get('user_name','')} ve ona
