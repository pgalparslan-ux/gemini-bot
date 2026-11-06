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

st.session_state.setdefault("user_name", "")
st.session_state.setdefault("current_chat_id", None)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("muzik_acik", False)
st.session_state.setdefault("secili_sarki", "Lo-Fi Chill")
st.session_state.setdefault("ozel_link", "")
st.session_state.setdefault("ozel_caliyor", False)

efektif_isim = "anonim"
if st.session_state.user_name:
    if st.session_state.user_name.strip() != "":
        efektif_isim = st.session_state.user_name.strip()

gemini_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_key:
    st.error("Secrets içinde GEMINI_API_KEY yok")
    st.stop()

base1 = "https://generativelanguage."
base2 = "googleapis.com/v1beta/openai/"
base_url = base1 + base2
client = OpenAI(base_url=base_url, api_key=gemini_key)
selected_model = "gemini-3-flash-preview"

with st.sidebar:
    st.title("⚡ VorpH AI")
    st.caption("Profesyonel Asistan")
    u_in = st.text_input("İsminiz", value=st.session_state.user_name, placeholder="Boş bırak = Anonim")
    if u_in != st.session_state.user_name:
        st.session_state.user_name = u_in
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()
    if st.session_state.user_name == "":
        st.caption("Anonim devam ediyorsun")
    else:
        st.caption("Merhaba")
        st.caption(st.session_state.user_name)
    st.markdown("---")
    modlar = ["Genel Asistan", "Yazılım Uzmanı", "Detaylı Uzman", "Resmî"]
    personality = st.selectbox("Asistan Modu", modlar)
    st.markdown("---")
    st.subheader("VorpH Müzik")
    st.caption("Müzik")
    s1 = "https://www.soundhelix.com/"
    s2 = "examples/mp3/SoundHelix-Song-"
    sarki_listesi = {
        "Lo-Fi Chill": s1 + s2 + "1.mp3",
        "Gece Sürüşü": s1 + s2 + "2.mp3",
        "Odaklanma": s1 + s2 + "3.mp3",
        "Yağmur Hissi": s1 + s2 + "4.mp3",
        "Enerji": s1 + s2 + "5.mp3",
        "Sakin Akşam": s1 + s2 + "6.mp3",
    }
    sarki_isimleri = list(sarki_listesi.keys())
    secim = st.selectbox("Şarkı Seç", sarki_isimleri)
    st.session_state.secili_sarki = secim
    muzik_acik = st.toggle("Müziği Aç", value=st.session_state.muzik_acik)
    st.session_state.muzik_acik = muzik_acik
    if st.session_state.muzik_acik:
        st.markdown('<div class="music-box">Çalıyor</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.secili_sarki)
        link = sarki_listesi[st.session_state.secili_sarki]
        st.audio(link, format="audio/mp3", autoplay=True)
        if st.button("Durdur", use_container_width=True):
            st.session_state.muzik_acik = False
            st.rerun()
    st.markdown("---")
    st.subheader("Link ile Çal")
    st.caption("YouTube veya MP3 linki yapıştır")
    link_girdi = st.text_input("Şarkı Linki", value=st.session_state.ozel_link, placeholder="YouTube linki buraya...")
    if link_girdi != st.session_state.ozel_link:
        st.session_state.ozel_link = link_girdi
    if st.button("Çalmaya Başla", use_container_width=True, type="primary"):
        if st.session_state.ozel_link.strip() == "":
            st.warning("Önce bir link yaz")
        else:
            st.session_state.ozel_caliyor = True
            st.session_state.muzik_acik = False
            st.rerun()
    if st.session_state.ozel_caliyor:
        if st.session_state.ozel_link.strip() != "":
            st.markdown('<div class="music-box">Linkten Çalıyor</div>', unsafe_allow_html=True)
            st.caption(st.session_state.ozel_link)
            l = st.session_state.ozel_link.strip()
            if "youtube.com" in l or "youtu.be" in l:
                st.video(l)
            elif l.endswith(".mp3"):
                st.audio(l, format="audio/mp3", autoplay=True)
            else:
                st.video(l)
            if st.button("Link Şarkıyı Durdur", use_container_width=True):
                st.session_state.ozel_caliyor = False
                st.session_state.ozel_link = ""
                st.rerun()
    st.markdown("---")
    if st.button("Yeni Sohbet", use_container_width=True, type="primary"):
        nid = create_chat(efektif_isim)
        st.session_state.current_chat_id = nid
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.subheader("Geçmiş Sohbetler")
    chats = get_chats(efektif_isim)
    for cid, title in chats:
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(title, key=f"chat_{cid}", use_container_width=True):
                st.session_state.current_chat_id = cid
                st.session_state.messages = get_messages_db(cid)
                st.rerun()
        with c2:
            if st.button("SİL", key=f"del_{cid}"):
                delete_chat_db(cid)
                if st.session_state.current_chat_id == cid:
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                st.rerun()
    st.markdown('<div class="model-kucuk">Gemini 3 Flash</div>', unsafe_allow_html=True)
    st.markdown('<div class="telif">Tüm telif haklarının sahibi YouTube\'dir.</div>', unsafe_allow_html=True)

if not st.session_state.current_chat_id:
    if chats:
        st.session_state.current_chat_id = chats[0][0]
        st.session_state.messages = get_messages_db(chats[0][0])
    else:
        nid = create_chat(efektif_isim)
        st.session_state.current_chat_id = nid

st.markdown("""
<div class="meta-topbar">
    <div class="meta-title">VorpH AI</div>
    <div class="meta-circle">O</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="meta-logo-wrap">
        <div class="meta-flash">⚡</div>
        <div class="meta-hello">VorpH'a ne soracaksın?</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

p1 = "Sen VorpH'sun."
p2 = "Sen yazılımcısın."
p3 = "Sen detaycısın."
p4 = "Sen resmîsin."
prompts = {
    "Genel Asistan": p1,
    "Yazılım Uzmanı": p2,
    "Detaylı Uzman": p3,
    "Resmî": p4,
}
sistem_talimati = prompts[personality]
sistem_talimati += " Türkçe cevap ver."

kullanici_girdisi = st.chat_input("VorpH'a sor...")

if kullanici_girdisi:
    simdi = time.time()
    if st.session_state.get("last_time"):
        fark = simdi - st.session_state.get("last_time")
        if fark < 1:
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
            stream = client.chat.completions.create(model=selected_model, messages=api_mesajlari, stream=True, temperature=0.7)
            yanit = st.write_stream((p.choices[0].delta.content for p in stream if p.choices[0].delta.content))
            st.session_state.messages.append({"role": "assistant", "content": yanit})
            add_message_db(st.session_state.current_chat_id, "assistant", yanit)
        except Exception as e:
            st.error(f"Hata: {str(e)}")
