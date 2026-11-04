import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

# --- AYARLAR ---
st.set_page_config(page_title="VorpH AI", page_icon="◼️", layout="centered")

# --- CSS: CHATGPT TARZI + MOBIL ---
st.markdown("""
<style>
    .stApp { background: #0a0a0a !important; color: #ececec !important; }
    section[data-testid="stSidebar"] { background: #050505 !important; border-right: 1px solid #1f1f1f !important; }
    
    /* Mesaj balonlari - ChatGPT tarzi */
    [data-testid="stChatMessage"] { 
        background: transparent !important; 
        border: none !important;
        padding: 1rem 0 !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
        background: #1e1e1e !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 12px 16px !important;
        border: 1px solid #2a2a2a !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stChatMessageContent"] {
        background: #111111 !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 12px 16px !important;
        border: 1px solid #222 !important;
    }
    /* Mobil */
    @media (max-width: 768px) {
        .stChatInputContainer { padding: 0 5px !important; }
        [data-testid="stChatMessageContent"] { max-width: 95% !important; }
    }
    /* Yaziyor efekti icin */
    .stSpinner > div { border-top-color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# --- VERITABANI - PERFORMANSLI ---
def get_conn():
    conn = sqlite3.connect("vorph.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, user_name TEXT, title TEXT, model TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_msg_chat ON messages(chat_id)")
    conn.commit()
    conn.close()

def create_chat(user_name, title="Yeni Sohbet"):
    chat_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    conn.execute("INSERT INTO chats (id, user_name, title) VALUES (?, ?, ?)", (chat_id, user_name, title))
    conn.commit()
    conn.close()
    return chat_id

def get_chats(user_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at FROM chats WHERE user_name=? ORDER BY created_at DESC", (user_name,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_messages_db(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC", (chat_id,))
    rows = cur.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def add_message_db(chat_id, role, content):
    conn = get_conn()
    conn.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
    # Ilk mesajsa basligi guncelle
    if role == "user":
        conn.execute("UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'", (content[:30], chat_id))
    conn.commit()
    conn.close()

def delete_chat_db(chat_id):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

init_db()

# --- SESSION ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- API ---
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("Secrets icinde OPENROUTER_API_KEY yok")
    st.stop()
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

# --- SIDEBAR ---
with st.sidebar:
    st.title("VorpH AI")
    st.caption("Profesyonel Asistan")
    
    user_name_input = st.text_input("Isminiz", value=st.session_state.user_name, placeholder="Ismini yaz")
    if user_name_input != st.session_state.user_name:
        st.session_state.user_name = user_name_input
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()

    if not st.session_state.user_name:
        st.warning("Sohbet icin isminizi girin")
        st.stop()

    st.markdown("---")
    personality = st.selectbox("Asistan Modu", ["Genel Asistan", "Yazilim Uzmami", "Detayli Uzman", "Resmi"], index=0)
    model_opt = st.selectbox("Model", ["Hizli (Gemini Flash)", "Akilli (Llama 70B)", "Dengeli (Auto)"])
    model_map = {"Hizli (Gemini Flash)": "google/gemini-2.0-flash-001", "Akilli (Llama 70B)": "meta-llama/llama-3.3-70b-instruct", "Dengeli (Auto)": "openrouter/auto"}
    selected_model = model_map[model_opt]

    if st.button("➕ Yeni Sohbet", use_container_width=True, type="primary"):
        new_id = create_chat(st.session_state.user_name)
        st.session_state.current_chat_id = new_id
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.subheader("Gecmis Sohbetler")
    chats = get_chats(st.session_state.user_name)
    for cid, title, created in chats:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(title, key=f"chat_{cid}", use_container_width=True):
                st.session_state.current_chat_id = cid
                st.session_state.messages = get_messages_db(cid)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{cid}"):
                delete_chat_db(cid)
                if st.session_state.current_chat_id == cid:
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                st.rerun()

# --- ANA EKRAN ---
# Otomatik ilk sohbet olustur
if not st.session_state.current_chat_id:
    if chats:
        st.session_state.current_chat_id = chats[0][0]
        st.session_state.messages = get_messages_db(chats[0][0])
    else:
        new_id = create_chat(st.session_state.user_name)
        st.session_state.current_chat_id = new_id

st.title("VorpH AI")
st.caption(f"Kullanici: {st.session_state.user_name} | Sohbet: {st.session_state.current_chat_id}")

# Gecmisi goster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# System prompt - gercekten calisan
prompts = {
    "Genel Asistan": "Sen VorpH adinda samimi ve yardimsever bir asistansin. Kisa ve net cevap ver.",
    "Yazilim Uzmami": "Sen VorpH adinda kidemli bir yazilim mimarisin. Sadece kod odakli dusun, en iyi pratikleri kullan, kod bloklari ile acikla, gereksiz konusma.",
    "Detayli Uzman": "Sen VorpH adinda arastirmaci bir uzmansin. Her konuyu ornekler, maddeler, artilar ve eksiler ile detayli anlat.",
    "Resmi": "Sen VorpH adinda kurumsal ve resmi bir asistansin. Akademik ve profesyonel dil kullan."
}
user_name_val = st.session_state.user_name
system_prompt = prompts[personality] + f" Kullanicinin adi {user_name_val}. Ona ismiyle hitap et. Turkce cevap ver."

# Input
user_input = st.chat_input("Bir sey yaz...")

if user_input:
    # Rate limit
    now = time.time()
    if st.session_state.get("last_time") and now - st.session_state.get("last_time") < 1:
        st.warning("Biraz yavas")
        st.stop()
    st.session_state.last_time = now

    st.session_state.messages.append({"role": "user", "content": user_input})
    add_message_db(st.session_state.current_chat_id, "user", user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        api_msgs = [{"role": "system", "content": system_prompt}]
        api_msgs.extend(st.session_state.messages)
        
        try:
            stream = client.chat.completions.create(model=selected_model, messages=api_msgs, stream=True, temperature=0.7)
            response = st.write_stream((chunk.choices[0].delta.content for chunk in stream if chunk.choices[0].delta.content))
            st.session_state.messages.append({"role": "assistant", "content": response})
            add_message_db(st.session_state.current_chat_id, "assistant", response)
        except Exception as e:
            st.error(f"Hata: {str(e)}")
