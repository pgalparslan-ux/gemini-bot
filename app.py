import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="VorpH AI",
    page_icon="VorpH",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background: #000000 !important; color: #ececec !important; }
    header[data-testid="stHeader"] { background: #000000 !important; }
    [data-testid="stToolbar"] { display: none !important; }
    section[data-testid="stSidebar"] { background: #0a0a0a !important; border-right: 1px solid #1a1a1a !important; }
    .topbar {
        position: fixed; top: 0; left: 0; right: 0; z-index: 999;
        background: #000000; height: 60px;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 12px; border-bottom: 1px solid #111;
    }
    .topbar-title { font-size: 19px; font-weight: 600; color: white; flex: 1; margin-left: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .topbar-btn {
        width: 40px; height: 40px; border-radius: 50%; background: #171717;
        display: flex; align-items: center; justify-content: center; font-size: 18px; color: white;
    }
    .topbar-pill { background: #171717; border-radius: 999px; padding: 8px 10px; display: flex; gap: 10px; align-items: center; }
    .block-container { padding-top: 75px !important; padding-bottom: 130px !important; max-width: 760px !important; }
    [data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 12px 0 !important; }
    [data-testid="stChatMessageContent"] { font-size: 17px !important; line-height: 1.6 !important; color: #ececec !important; }
    .stChatInputContainer {
        background: #151515 !important; border: 1px solid #222 !important;
        border-radius: 24px !important; padding: 6px 8px !important;
        box-shadow: 0 -10px 30px rgba(0,0,0,0.8) !important;
    }
    .stChatInputContainer textarea { background: transparent !important; color: white !important; font-size: 16px !important; }
    .stChatInputContainer textarea::placeholder { color: #888 !important; }
    button[kind="secondary"] { background: #1a1a1a !important; border: 1px solid #222 !important; color: white !important; border-radius: 999px !important; }
    @media (max-width: 768px) {
        .block-container { padding-left: 14px !important; padding-right: 14px !important; }
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
        kisa = content[:32]
        conn.execute("UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'", (kisa, chat_id))
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
    st.session_state.user_name = "Hexyy"
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "hizli_modu" not in st.session_state:
    st.session_state.hizli_modu = True

# --- GEMINI API KEY ---
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
if not gemini_key:
    st.error("Secrets içinde GEMINI_API_KEY bulunamadı. Streamlit > Manage app > Settings > Secrets kısmına GEMINI_API_KEY ekle.")
    st.stop()

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=gemini_key
)

# --- VARSAYILAN DEĞERLER - else kullanmadan düzeltildi ---
personality = "Genel Asistan"
selected_model = "gemini-2.0-flash"
chats = get_chats(st.session_state.user_name)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### VorpH AI")
    isim = st.text_input("İsminiz", value=st.session_state.user_name)
    st.session_state.user_name = isim
    st.markdown("---")
    modlar = [
        "Genel Asistan",
        "Yazılım Uzmanı",
        "Detaylı Uzman",
        "Resmî"
    ]
    personality = st.selectbox("Asistan Modu", modlar)
    modeller = [
        "Hızlı - Gemini 2.0 Flash",
        "Akıllı - Gemini 2.5 Flash",
        "Güçlü - Gemini 1.5 Pro"
    ]
    model_opt = st.selectbox("Model", modeller)
    model_map = {
        "Hızlı - Gemini 2.0 Flash": "gemini-2.0-flash",
        "Akıllı - Gemini 2.5 Flash": "gemini-2.5-flash",
        "Güçlü - Gemini 1.5 Pro": "gemini-1.5-pro"
    }
    selected_model = model_map[model_opt]
    st.markdown("---")
    if st.button("➕ Yeni Sohbet", use_container_width=True, type="primary"):
        nid = create_chat(st.session_state.user_name)
        st.session_state.current_chat_id = nid
        st.session_state.messages = []
        st.rerun()
    st.subheader("Geçmiş Sohbetler")
    chats = get_chats(st.session_state.user_name)
    for cid, title in chats:
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(title, key=f"chat_{cid}", use_container_width=True):
                st.session_state.current_chat_id = cid
                st.session_state.messages = get_messages_db(cid)
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{cid}"):
                delete_chat_db(cid)
                st.session_state.current_chat_id = None
                st.session_state.messages = []
                st.rerun()

if not st.session_state.current_chat_id:
    if chats:
        st.session_state.current_chat_id = chats[0][0]
        st.session_state.messages = get_messages_db(chats[0][0])
    else:
        nid = create_chat(st.session_state.user_name, "Proje Geliştirmeleri")
        st.session_state.current_chat_id = nid

aktif_baslik = "Yeni Sohbet"
for cid, title in chats:
    if cid == st.session_state.current_chat_id:
        aktif_baslik = title

# --- ÜST BAR ---
st.markdown(
    f"""
    <div class="topbar">
        <div class="topbar-btn">☰</div>
        <div class="topbar-title">{aktif_baslik}</div>
        <div class="topbar-pill">
            <span>✏️</span>
            <span>•••</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- MESAJLAR ---
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; margin-top:120px; color:#777;">
        <div style="font-size:28px; color:white; font-weight:600;">VorpH'a ne soracaksın?</div>
        <div style="margin-top:10px;">Proje geliştirmeleri için buradayım</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for idx, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3, c4 = st.columns([1, 1, 1, 10])
            with c1:
                if st.button("👍", key=f"like_{idx}"):
                    st.toast("Teşekkürler!")
            with c2:
                if st.button("👎", key=f"dis_{idx}"):
                    st.toast("Not edildi")
            with c3:
                if st.button("📋", key=f"copy_{idx}"):
                    st.toast("Kopyalandı")

prompts = {
    "Genel Asistan": "Sen VorpH adında samimi bir asistansın.",
    "Yazılım Uzmanı": "Sen VorpH adında kıdemli bir yazılım mimarisin.",
    "Detaylı Uzman": "Sen VorpH adında detaylı anlatan bir uzmansın.",
    "Resmî": "Sen VorpH adında resmi bir asistansın."
}
ad = st.session_state.user_name
sistem = prompts.get(personality, prompts["Genel Asistan"]) + f" Kullanıcının adı {ad}. Türkçe cevap ver."

# --- ALT BAR ---
col_arti, col_aninda, col_ses = st.columns([1, 2, 1])
with col_arti:
    if st.button("＋", key="plus_btn"):
        st.toast("Dosya yükleme yakında")
with col_aninda:
    hizli = st.toggle("Anında", value=st.session_state.hizli_modu)
    st.session_state.hizli_modu = hizli
with col_ses:
    if st.button("🎙️", key="voice_btn"):
        st.toast("Sesli giriş yakında - şimdilik yazın")

kullanici_girdisi = st.chat_input("Yanıtla...")

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
        api_mesajlari = [{"role": "system", "content": sistem}]
        api_mesajlari.extend(st.session_state.messages)
        try:
            stream = client.chat.completions.create(
                model=selected_model,
                messages=api_mesajlari,
                stream=True,
                temperature=0.7
            )
            yanit = st.write_stream(
                (p.choices[0].delta.content for p in stream if p.choices[0].delta.content)
            )
            st.session_state.messages.append({"role": "assistant", "content": yanit})
            add_message_db(st.session_state.current_chat_id, "assistant", yanit)
            st.rerun()
        except Exception as e:
            st.error(f"Hata: {str(e)}")
