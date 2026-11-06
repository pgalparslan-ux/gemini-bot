import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="VorpH AI",
    page_icon="⚡",
    layout="centered"
)

st.markdown("""
<style>
    .stApp { background: #000000 !important; color: #ececec !important; }
    header[data-testid="stHeader"] { background: #000000 !important; }
    [data-testid="stToolbar"] { display: flex !important; }
    [data-testid="collapsedControl"] { display: flex !important; color: white !important; }
    [data-testid="collapsedControl"] svg { fill: white !important; }
    section[data-testid="stSidebar"] { background: #0b0b0b !important; border-right: 1px solid #1a1a1a !important; }
    section[data-testid="stSidebar"] * { color: #ececec !important; }
    .meta-topbar { display: flex; align-items: center; justify-content: space-between; padding: 6px 4px 18px 4px; margin-top: 8px; }
    .meta-title { font-size: 22px; font-weight: 500; color: white; line-height: 1; }
    .meta-circle { width: 44px; height: 44px; border-radius: 50%; background: #1a1a1a; display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; flex-shrink: 0; }
    .meta-logo-wrap { text-align: center; margin-top: 70px; margin-bottom: 10px; }
    .meta-flash {
        font-size: 110px; line-height: 1;
        background: linear-gradient(180deg, #FFE600 0%, #FFB800 35%, #FF6B00 70%, #FF3D00 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 24px rgba(255, 184, 0, 0.55));
    }
    .meta-hello { text-align: center; color: #aaa; font-size: 20px; margin-top: 14px; font-weight: 500; }
    .block-container { max-width: 760px !important; padding-top: 20px !important; padding-bottom: 120px !important; }
    [data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 12px 0 !important; }
    [data-testid="stChatMessageContent"] { font-size: 17px !important; line-height: 1.65 !important; color: #ececec !important; }
    .stChatInputContainer { background: #1c1c1e !important; border: none !important; border-radius: 28px !important; padding: 10px 10px 10px 14px !important; }
    .stChatInputContainer textarea { background: transparent !important; color: white !important; font-size: 17px !important; }
    .stChatInputContainer textarea::placeholder { color: #888 !important; }
    .music-box { background: #17171a !important; border: 1px solid #26262b !important; border-radius: 16px !important; padding: 12px !important; }
    .model-kucuk { font-size: 11px !important; color: #666 !important; text-align: center !important; margin-top: 30px !important; }
    button { border-radius: 12px !important; }
    @media (max-width: 768px) {
        .block-container { padding-left: 14px !important; padding-right: 14px !important; }
        .meta-flash { font-size: 90px; }
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
if "muzik_acik" not in st.session_state:
    st.session_state.muzik_acik = False
if "secili_sarki" not in st.session_state:
    st.session_state.secili_sarki = "Lo-Fi Chill"

efektif_isim = st.session_state.user_name.strip() if st.session_state
