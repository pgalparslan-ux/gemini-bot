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
    section[data-testid="stSidebar"] { background: #0b0b0b !important; }
    .meta-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 4px 18px 4px;
    }
    .meta-title { font-size: 22px; color: white; }
    .meta-circle {
        width: 44px; height: 44px;
        border-radius: 50%;
        background: #1a1a1a;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px; color: white;
    }
    .meta-logo-wrap { text-align: center; margin-top: 60px; }
    .meta-flash {
        font-size: 110px; line-height: 1;
        background: linear-gradient(180deg, #FFE600, #FF6B00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .meta-hello { text-align: center; color: #aaa; font-size: 20px; margin-top: 12px; }
    .block-container { max-width: 760px !important; padding-top: 20px !important; padding-bottom: 120px !important; }

    /* --- 2 IKONU KALDIR --- */
    [data-testid="stChatMessageAvatar"] { display: none !important; }
    [data-testid="stChatMessageAvatarUser"] { display: none !important; }
    [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    [data-testid="stChatMessage"] > div:first-child { display: none !important; }
    /* Mesaj icerigi sola yaslansin, ikon boslugu kalmasin */
    [data-testid="stChatMessageContent"] { margin-left: 0px !important; padding-left: 0px !important; }

    /* --- KONUSMA CUBUGU - KIRMIZI CERCEVE KAPALI --- */
    [data-testid="stChatInput"] {
        background: #262626 !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-radius: 28px !important;
        padding: 6px 6px 6px 16px !important;
    }
    .stChatInputContainer {
        background: #262626 !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        border-radius: 28px !important;
        padding: 6px 6px 6px 16px !important;
    }
    /* Tiklayinca da kirmizi / mavi cerceve cikmasin */
    [data-testid="stChatInput"]:focus,
    [data-testid="stChatInput"]:focus-within,
    [data-testid="stChatInput"]:focus-visible,
    .stChatInputContainer:focus,
    .stChatInputContainer:focus-within,
    .stChatInputContainer:focus-visible {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stChatInputContainer textarea {
        background: transparent !important;
        color: white !important;
        font-size: 17px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stChatInputContainer textarea:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stChatInputContainer textarea::placeholder {
        color: #8a8a8a !important;
    }
    [data-testid="stChatInput"] button {
        background: #3a3a3a !important;
        color: white !important;
        border-radius: 50% !important;
        border: none !important;
    }
    /* Genel focus kirmizisini da kapat */
    *:focus { outline: none !important; box-shadow: none !important; }
    *:focus-visible { outline: none !important; box-shadow: none !important; }

    .music-box { background: #17171a !important; border-radius: 16px !important; padding: 12px !important; }
    .model-kucuk { font-size: 11px !important; color: #666 !important; text-align: center !important; margin-top: 30px !important; }
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
    conn.commit()
    conn.close()

def create_chat(user_name, title="Yeni Sohbet"):
    chat_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    conn.execute(
        "INSERT INTO chats (id, user_name, title) VALUES (?, ?, ?)",
        [chat_id, user_name, title]
    )
    conn.commit()
    conn.close()
    return chat_id

def get_chats(user_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title FROM chats WHERE user_name=? ORDER BY rowid DESC",
        [user_name]
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_messages_db(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC",
        [chat_id]
    )
    rows = cur.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({"role": r[0], "content": r[1]})
    return out

def add_message_db(chat_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        [chat_id, role, content]
    )
    if role == "user":
        kisa = content[:30]
        conn.execute(
            "UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'",
            [kisa, chat_id]
        )
    conn.commit()
    conn.close()

def delete_chat_db(chat_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM messages WHERE chat_id=?",
        [chat_id]
    )
    conn.execute(
        "DELETE FROM chats WHERE id=?",
        [chat_id]
    )
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

efektif_isim = "anonim"
gorunen_isim = "Misafir"
if st.session_state.user_name:
    if st.session_state.user_name.strip() != "":
        efektif_isim = st.session_state.user_name.strip()
        gorunen_isim = st.session_state.user_name.strip()

gemini_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_key:
    st.error("Secrets icinde GEMINI_API_KEY yok")
    st.stop()

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=gemini_key
)

selected_model = "gemini-3-flash-preview"

with st.sidebar:
    st.title("⚡ VorpH AI")
    st.caption("Profesyonel Asistan")
    user_name_input = st.text_input(
        "Isminiz",
        value=st.session_state.user_name,
        placeholder="Bos birak = Anonim"
    )
    if user_name_input != st.session_state.user_name:
        st.session_state.user_name = user_name_input
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()
    if st.session_state.user_name == "":
        st.caption("Anonim devam ediyorsun")
    else:
        st.caption("Merhaba")
        st.caption(st.session_state.user_name)
    st.markdown("---")
    asistan_modlari = ["Genel Asistan", "Yazilim Uzmami", "Detayli Uzman", "Resmi"]
    personality = st.selectbox("Asistan Modu", asistan_modlari)
    st.markdown("---")
    st.subheader("VorpH Muzik")
    st.caption("Sadece bu sitede calar
