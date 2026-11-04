import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="VorpH AI", page_icon="◼️", layout="centered")

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
    c.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, user_name TEXT, title TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT)")
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
    cur.execute("SELECT id, title FROM chats WHERE user_name=? ORDER BY rowid DESC", (user_name,))
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
    if role == "user":
        kisa_baslik = content[:30]
        conn.execute("UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'", (kisa_baslik, chat_id))
    conn.commit()
    conn.close()

def delete_chat_db(chat_id):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

init_db()

if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

api_key = st.secrets.get("OPENROUTER_API_KEY", "")
if not api_key:
    st.error("Secrets içinde OPENROUTER_API_KEY bulunamadı")
    st.stop()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

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
    personality = st.selectbox("Asistan Modu", ["Genel Asistan", "Yazılım Uzmanı", "Detaylı Uzman", "Resmî"], index=0)
    model_opt = st.selectbox("Model", ["Hızlı (Gemini Flash)", "Akıllı (Llama 70B)", "
