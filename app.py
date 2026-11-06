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

# --- META AI TARZI CSS ---
st.markdown("""
<style>
    .stApp { background: #000000 !important; color: #ececec !important; }
    header[data-testid="stHeader"] { background: #000000 !important; }
    [data-testid="stToolbar"] { display: none !important; }
    section[data-testid="stSidebar"] { background: #0b0b0b !important; border-right: 1px solid #1a1a1a !important; }
    section[data-testid="stSidebar"] * { color: #ececec !important; }

    /* Üst bar - Meta AI gibi */
    .meta-topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 4px 14px 4px;
    }
    .meta-top-left { display: flex; align-items: center; gap: 14px; }
    .meta-circle {
        width: 44px; height: 44px; border-radius: 50%; background: #1a1a1a;
        display: flex; align-items: center; justify-content: center; font-size: 22px; color: white;
    }
    .meta-title { font-size: 22px; font-weight: 500; color: white; }

    /* Ortadaki Meta logosu - mor mavi degrade */
    .meta-logo-wrap { text-align: center; margin-top: 110px; margin-bottom: 10px; }
    .meta-logo {
        font-size: 88px; line-height: 1;
        background: linear-gradient(135deg, #ff5ea8 0%, #a855f7 30%, #6366f1 60%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 18px rgba(168, 85, 247, 0.6));
    }
    .meta-hello { text-align: center; color: #888; font-size: 17px; margin-top: 12px; }

    /* Mesajlar - Meta AI gibi sade, balon yok */
    .block-container { max-width: 760px !important; padding-top: 10px !important; padding-bottom: 150px !important; }
    [data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 12px 0 !important; }
    [data-testid="stChatMessageContent"] { font-size: 17px !important; line-height: 1.65 !important; color: #ececec !important; }

    /* Alt bar - Meta AI gibi gri yuvarlak */
    .stChatInputContainer {
        background: #1c1c1e !important; border: none !important;
        border-radius: 28px !important; padding: 10px 10px 6px 14px !important;
        box-shadow: none !important;
    }
    .stChatInputContainer textarea { background: transparent !important; color: white !important; font-size: 17px !important; }
    .stChatInputContainer textarea::placeholder { color: #888 !important; }

    /* Alt bar altı - + / Aninda / ses görünümü, tek satırda kalır */
    .meta-bottom-row {
        display: flex; align-items: center; justify-content: space-between;
        margin-top: 2px; padding: 0 6px 0 6px;
    }
    .meta-plus {
        width: 36px; height: 36px; border-radius: 50%; border: 1px solid #333;
        display: flex; align-items: center; justify-content: center; font-size: 22px; color: #ccc;
    }
    .meta-right { display: flex; align-items: center; gap: 8px; }
    .meta-aninda {
        border: 1px solid #333; border-radius: 999px; padding: 7px 16px;
        color: white; font-size: 15px; background: transparent;
    }
    .meta-voice {
        width: 40px; height: 40px; border-radius: 50%; background: #1d9bf0;
        display: flex; align-items: center; justify-content: center; font-size: 18px; color: white;
    }
    button { border-radius: 12px !important; }
    @media (max-width: 768px) {
        .block-container { padding-left: 14px !important; padding-right: 14px !important; }
        .meta-logo { font-size: 72px; }
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

# TEK MODEL - Gemini 3 Flash
selected_model = "gemini-3-flash-preview"

# --- YAN ÇUBUK DURUYOR, SİLMEDİM ---
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
    st.caption("Model: Gemini 3 Flash")
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

# --- ÜST BAR - Meta AI gibi ---
st.markdown("""
<div class="meta-topbar">
    <div class="meta-top-left">
        <div class="meta-circle">≡</div>
        <div class="meta-title">VorpH AI</div>
    </div>
    <div class="meta-circle">👓</div>
</div>
""", unsafe_allow_html=True)

# --- MESAJLAR / BOŞ EKRAN LOGOSU ---
if not st.session_state.messages:
    st.markdown("""
    <div class="meta-logo-wrap">
        <div class="meta-logo">✦</div>
        <div class="meta-hello">VorpH'a ne soracaksın?</div>
    </div>
    """, unsafe_allow_html=True)
else:
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

kullanici_girdisi = st.chat_input("VorpH'a sor...")

# Meta AI alt bar görünümü - sadece görüntü, butonlar input'u bozmaz
st.markdown("""
<div class="meta-bottom-row">
    <div class="meta-plus">+</div>
    <div class="meta-right">
        <div class="meta-aninda">Anında</div>
        <div class="meta-voice">|||</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
