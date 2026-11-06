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

# --- DÜZELTME: Gerçek yan çubuk butonunu gizleme artık ---
st.markdown("""
<style>
    .stApp { background: #000000 !important; color: #ececec !important; }
    /* Header'ı gizleme, yoksa yan çubuk butonu da gidiyor */
    header[data-testid="stHeader"] { background: #000000 !important; }
    [data-testid="stToolbar"] { display: flex !important; }
    /* Gerçek yan çubuk açma butonu - görünür yap */
    [data-testid="collapsedControl"] { display: flex !important; color: white !important; background: transparent !important; }
    [data-testid="collapsedControl"] svg { fill: white !important; color: white !important; }
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
    .meta-sub { text-align: center; color: #666; font-size: 14px; margin-top: 6px; }

    .block-container { max-width: 760px !important; padding-top: 20px !important; padding-bottom: 120px !important; }
    [data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 12px 0 !important; }
    [data-testid="stChatMessageContent"] { font-size: 17px !important; line-height: 1.65 !important; color: #ececec !important; }
    .stChatInputContainer { background: #1c1c1e !important; border: none !important; border-radius: 28px !important; padding: 10px 10px 10px 14px !important; }
    .stChatInputContainer textarea { background: transparent !important; color: white !important; font-size: 17px !important; }
    .stChatInputContainer textarea::placeholder { color: #888 !important; }
    .music-box { background: #17171a !important; border: 1px solid #26262b !important; border-radius: 16px !important; padding: 12px !important; }
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

efektif_isim = st.session_state.user_name.strip() if st.session_state.user_name else "anonim"
gorunen_isim = st.session_state.user_name.strip() if st.session_state.user_name else "Misafir"

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
    st.caption("Profesyonel Asistan - İsimsiz Mod")
    user_name_input = st.text_input("İsminiz (zorunlu değil)", value=st.session_state.user_name, placeholder="Boş bırak = Anonim")
    if user_name_input != st.session_state.user_name:
        st.session_state.user_name = user_name_input
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()
    if not st.session_state.user_name:
        st.caption("👻 Anonim olarak devam ediyorsun")
    else:
        st.caption(f"👋 Merhaba {st.session_state.user_name}")
    st.markdown("---")
    asistan_modlari = ["Genel Asistan", "Yazılım Uzmanı", "Detaylı Uzman", "Resmî"]
    personality = st.selectbox("Asistan Modu", asistan_modlari)
    st.caption("Model: Gemini 3 Flash ⚡")
    st.markdown("---")
    st.subheader("🎵 VorpH Müzik")
    st.caption("Sadece bu sitede çalar")
    sarki_listesi = {
        "Lo-Fi Chill": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "Gece Sürüşü": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "Odaklanma": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "Yağmur Hissi": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "Enerji": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "Sakin Akşam": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
    }
    secim = st.selectbox("Şarkı Seç", list(sarki_listesi.keys()), index=list(sarki_listesi.keys()).index(st.session_state.secili_sarki) if st.session_state.secili_sarki in sarki_listesi else 0)
    st.session_state.secili_sarki = secim
    muzik_acik = st.toggle("🎧 Müziği Aç", value=st.session_state.muzik_acik)
    st.session_state.muzik_acik = muzik_acik
    if st.session_state.muzik_acik:
        st.markdown(f'<div class="music-box">🎶 Şimdi çalıyor:<br><b>{st.session_state.secili_sarki}</b><br><span style="font-size:12px;color:#888;">Sadece VorpH\'da</span></div>', unsafe_allow_html=True)
        st.audio(sarki_listesi[st.session_state.secili_sarki], format="audio/mp3", autoplay=True)
        if st.button("⏹️ Durdur", use_container_width=True):
            st.session_state.muzik_acik = False
            st.rerun()
    else:
        st.caption("Müzik kapalı.")
    st.markdown("---")
    if st.button("Yeni Sohbet", use_container_width=True, type="primary"):
        new_id = create_chat(efektif_isim)
        st.session_state.current_chat_id = new_id
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.subheader("Geçmiş Sohbetler")
    chats = get_chats(efektif_isim)
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
        new_id = create_chat(efektif_isim)
        st.session_state.current_chat_id = new_id

# ÜST BAR - sahte hamburger yok, gerçek Streamlit butonu sol üstte duruyor
st.markdown("""
<div class="meta-topbar">
    <div class="meta-title">⚡ VorpH AI</div>
    <div class="meta-circle">👓</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="meta-logo-wrap">
        <div class="meta-flash">⚡</div>
        <div class="meta-hello">VorpH'a ne soracaksın?</div>
        <div class="meta-sub">Flash hızında - Gemini 3 Flash ile çalışıyor</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

prompts = {
    "Genel Asistan": "Sen VorpH adında samimi bir asistansın. VorpH ismi flash, şimşek anlamına gelir.",
    "Yazılım Uzmanı": "Sen VorpH adında kıdemli bir yazılım mimarisin. VorpH ismi flash, şimşek anlamına gelir.",
    "Detaylı Uzman": "Sen VorpH adında detaylı anlatan bir uzmansın.",
    "Resmî": "Sen VorpH adında resmi bir asistansın."
}

sistem_talimati = prompts[personality] + f" Kullanıcı anonim, ismi {gorunen_isim}. Türkçe cevap ver."

kullanici_girdisi = st.chat_input("VorpH'a sor...")

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
