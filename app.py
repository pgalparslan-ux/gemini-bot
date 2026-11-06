import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title='VorpH AI', page_icon='⚡', layout='centered')

st.markdown("""
<style>
:root { --primary-color: #262626 !important; }
.stApp { background: #000000 !important; color: #ececec !important; }
header[data-testid="stHeader"] { background: #000000 !important; }
[data-testid="stToolbar"] { display: flex !important; }
[data-testid="collapsedControl"] { display: flex !important; color: white !important; }
section[data-testid="stSidebar"] { background: #0b0b0b !important; border-right: 1px solid #1a1a1a !important; }
section[data-testid="stSidebar"] * { color: #ececec !important; }
.meta-topbar { display: flex; align-items: center; justify-content: space-between; padding: 6px 4px 18px 4px; margin-top: 8px; }
.meta-title { font-size: 22px; font-weight: 500; color: white; line-height: 1; }
.meta-circle { width: 44px; height: 44px; border-radius: 50%; background: #1a1a1a; display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; }
.meta-logo-wrap { text-align: center; margin-top: 70px; margin-bottom: 10px; }
.meta-flash { font-size: 110px; line-height: 1; background: linear-gradient(180deg, #FFE600 0%, #FFB800 35%, #FF6B00 70%, #FF3D00 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 24px rgba(255,184,0,0.55)); }
.meta-hello { text-align: center; color: #aaa; font-size: 20px; margin-top: 14px; font-weight: 500; }
.block-container { max-width: 760px !important; padding-top: 20px !important; padding-bottom: 120px !important; }
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 12px 0 !important; }
[data-testid="stChatMessageContent"] { font-size: 17px !important; line-height: 1.65 !important; color: #ececec !important; }
[data-testid="stChatMessageAvatar"] { display: none !important; }
[data-testid="stChatMessageAvatarUser"] { display: none !important; }
[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
div[data-testid="stChatInput"] { background: #262626 !important; border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; border-radius: 28px !important; padding: 6px 6px 6px 16px !important; }
div[data-testid="stChatInput"] > div { border: none !important; outline: none !important; box-shadow: none !important; background: transparent !important; }
div[data-testid="stChatInput"]:focus { border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; }
div[data-testid="stChatInput"]:focus-within { border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; }
div[data-testid="stChatInput"]:focus-visible { border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; }
.stChatInputContainer { background: #262626 !important; border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; border-radius: 28px !important; padding: 6px 6px 6px 16px !important; }
.stChatInputContainer:focus { border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; }
.stChatInputContainer:focus-within { border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; }
.stChatInputContainer:focus-visible { border: 1px solid #262626 !important; outline: none !important; box-shadow: none !important; }
.stChatInputContainer textarea { background: transparent !important; color: white !important; font-size: 17px !important; border: none !important; outline: none !important; box-shadow: none !important; }
.stChatInputContainer textarea:focus { border: none !important; outline: none !important; box-shadow: none !important; }
.stChatInputContainer textarea::placeholder { color: #8a8a8a !important; }
div[data-testid="stChatInput"] button { background: #3a3a3a !important; color: white !important; border-radius: 50% !important; border: none !important; outline: none !important; box-shadow: none !important; }
div[data-testid="stChatInput"] button:focus { outline: none !important; box-shadow: none !important; }
*:focus { outline: none !important; box-shadow: none !important; }
*:focus-visible { outline: none !important; box-shadow: none !important; }
.music-box { background: #17171a !important; border: 1px solid #26262b !important; border-radius: 16px !important; padding: 12px !important; }
.model-kucuk { font-size: 11px !important; color: #666 !important; text-align: center !important; margin-top: 30px !important; }
.telif { font-size: 10px !important; color: #777 !important; text-align: center !important; margin-top: 8px !important; line-height: 1.4 !important; }
button { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

def get_conn():
    conn = sqlite3.connect("vorph.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, user_name TEXT, title TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT)")
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
    out = []
    for r in rows:
        out.append({"role": r[0], "content": r[1]})
    return out

def add_message_db(chat_id, role, content):
