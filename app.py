import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="VorpH AI",
    page_icon="◼️",
    layout="centered"
)

st.markdown("""
<style>
    .stApp { background: #0a0a0a !important; color: #ececec !important; }
    section[data-testid="stSidebar"] { background: #050505 !important; border-right: 1px solid #1f1f1f !important; }
    [data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 1rem 0 !important; }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
        background: #1e1e1e !important; border-radius: 18px 18px 4px 18px !important; padding: 12px 16px !important; border: 1px solid #2a2a2a !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stChatMessageContent"] {
        background: #111111 !important; border-radius: 18px 18px 18px 4px !important; padding: 12px 16px !important; border: 1px solid #222 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_conn():
    conn = sqlite3.connect("vorph.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, user_name TEXT, title TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_msg_chat ON messages(chat_id)")
    conn.commit()
    conn.close()

def create_chat(user_name, title="Yeni Sohbet"):
    chat_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    conn.execute("INSERT INTO chats (id, user_name, title) VALUES (?, ?, ?)", [chat_id, user_name, title])
    conn.commit()
    conn.close()
    return chat_id

def get_chats(user_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM chats WHERE user_name=? ORDER BY rowid DESC", [user_name])
    rows = cur.fetchall()
    conn.close()
    return rows

def get_messages_db(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC", [chat_id])
    rows = cur.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def add_message_db(chat_id, role, content):
    conn = get_conn()
    conn.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", [chat_id, role, content])
    if role == "user":
        kisa = content[:30]
        conn.execute("UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'", [kisa, chat_id])
    conn.commit()
    conn.close()

def delete_chat_db(chat_id):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE chat_id=?", [chat_id])
    conn.execute("DELETE FROM chats WHERE id=?", [chat_id])
    conn.commit()
    conn.close()

init_db()

if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

gemini_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_key:
    st.error("Secrets icinde GEMINI_API_KEY yok")
    st.stop()

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=gemini_key
)

with st.sidebar:
    st.title("VorpH AI")
    st.caption("Profesyonel Asistan")
    user_name_input = st.text_input("İsminiz", value=st.session_state.user_name, placeholder="Örn: Ahmet")
    if user_name_input != st.session_state.user_name:
        st.session_state.user_name = user_name_input
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()
    if not st.session_state.user_name:
        st.warning("Sohbet için isminizi girin")
        st.stop()
    st.markdown("---")
    asistan_modlari = ["Genel Asistan", "Yazılım Uzmanı", "Detaylı Uzman", "Resmî"]
    personality = st.selectbox("Asistan Modu", asistan_modlari)
    model_listesi = ["Hızlı - Gemini Flash", "Akıllı - Gemini 2.5 Flash", "Dengeli - Gemini 1.5 Flash"]
    model_opt = st.selectbox("Model", model_listesi)
    model_map = {
        "Hızlı - Gemini Flash": "gemini-2.0-flash",
        "Akıllı - Gemini 2.5 Flash": "gemini-2.5-flash",
        "Dengeli - Gemini 1.5 Flash": "gemini-1.5-flash"
    }
    selected_model = model_map[model_opt]
    if st.button("Yeni Sohbet", use_container_width=True, type="primary"):
        new_id = create_chat(st.session_state.user_name)
        st.session_state.current_chat_id = new_id
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.subheader("Geçmiş Sohbetler")
    chats = get_chats(st.session_state.user_name)
    for cid, title in chats:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(title, key=f"chat_{cid}", use_container_width=True):
                st.session_state.current_chat_id = cid
                st.session_state.messages = get_messages_db(cid)
                st.rerun()
        with col2:
            if st.button("SİL", key=f"del_{cid}"):
                delete_chat_db(cid)
                if st.session_state.current_chat_id == cid:
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                st.rerun()

if not st.session_state.current_chat_id:
    if chats:
        st.session_state.current_chat_id = chats[0][0]
        st.session_state.messages = get_messages_db(chats[0][0])
    else:
        new_id = create_chat(st.session_state.user_name)
        st.session_state.current_chat_id = new_id

st.title("VorpH AI")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompts = {
    "Genel Asistan": "Sen VorpH adında samimi bir asistansın.",
    "Yazılım Uzmanı": "Sen VorpH adında kıdemli bir yazılım mimarisin.",
    "Detaylı Uzman": "Sen VorpH adında detaylı anlatan bir uzmansın.",
    "Resmî": "Sen VorpH adında resmi bir asistansın."
}

ad = st.session_state.user_name
sistem_talimati = prompts[personality] + f" Kullanıcının adı {ad}. Türkçe cevap ver."

kullanici_girdisi = st.chat_input("Bir şey yazın...")

if kullanici_girdisi:
    simdi = time.time()
    if st.session_state.get("last_time") and simdi - st.session_state.get("last_time") < 1:
        st.warning("Biraz yavaş")
        st.stop()
    st.session_state.last_time = simdi
    st.session_state.messages.append({"role": "user", "content": kullanici_girdisi})
    add_message_db(st.session_state.current_chat_id, "user", kullanici_girdisi)
    with st.chat_message("user"):
        st.markdown(kullanici_girdisi)
    with st.chat_message("assistant"):
        api_mesajlari = [{"role": "system", "content": sistem_talimati}]
        api_mesajlari.extend(st.session_state.messages)
        try:
            stream = client.chat.completions.create(
                model=selected_model,
                messages=api_mesajlari,
                stream=True,
                temperature=0.7
            )
            yanit = st.write_stream(
                (parca.choices[0].delta.content for parca in stream if parca.choices[0].delta.content)
            )
            st.session_state.messages.append({"role": "assistant", "content": yanit})
            add_message_db(st.session_state.current_chat_id, "assistant", yanit)
        except Exception as e:
            st.error(f"Hata: {str(e)}")
