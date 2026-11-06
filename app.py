import time
import uuid
import sqlite3
import streamlit as st
from openai import OpenAI

st.set_page_config(
 page_title='VorpH AI',
 page_icon='⚡',
 layout='centered'
)

st.markdown('''
<style>
.stApp{background:#000 !important;}
header{background:#000 !important;}
[data-testid='stToolbar']{display:flex !important;}
[data-testid='collapsedControl']{display:flex !important;}
section[data-testid='stSidebar']{background:#0b0b0b !important;}
.meta-topbar{display:flex;justify-content:space-between;}
.meta-title{font-size:22px;color:white;}
.meta-circle{width:44px;height:44px;border-radius:50%;}
.meta-circle{background:#1a1a1a;display:flex;}
.meta-circle{align-items:center;justify-content:center;}
.meta-logo-wrap{text-align:center;margin-top:60px;}
.meta-flash{font-size:110px;line-height:1;}
.meta-flash{background:linear-gradient(180deg,#FFE600,#FF6B00);}
.meta-flash{-webkit-background-clip:text;}
.meta-flash{-webkit-text-fill-color:transparent;}
.meta-hello{text-align:center;color:#aaa;font-size:20px;}
.block-container{max-width:760px !important;}
.block-container{padding-bottom:120px !important;}
[data-testid='stChatMessageAvatar']{display:none !important;}
[data-testid='stChatMessage']>div:first-child{display:none !important;}
[data-testid='stChatInput']{background:#262626 !important;}
[data-testid='stChatInput']{border:none !important;}
[data-testid='stChatInput']{outline:none !important;}
[data-testid='stChatInput']{box-shadow:none !important;}
[data-testid='stChatInput']{border-radius:28px !important;}
.stChatInputContainer{background:#262626 !important;}
.stChatInputContainer{border:none !important;}
.stChatInputContainer{outline:none !important;}
.stChatInputContainer{box-shadow:none !important;}
.stChatInputContainer{border-radius:28px !important;}
[data-testid='stChatInput']:focus{border:none !important;}
[data-testid='stChatInput']:focus{outline:none !important;}
[data-testid='stChatInput']:focus{box-shadow:none !important;}
.stChatInputContainer:focus{border:none !important;}
.stChatInputContainer:focus{outline:none !important;}
.stChatInputContainer:focus{box-shadow:none !important;}
.stChatInputContainer textarea{background:transparent !important;}
.stChatInputContainer textarea{color:white !important;}
.stChatInputContainer textarea{border:none !important;}
.stChatInputContainer textarea{outline:none !important;}
.stChatInputContainer textarea{box-shadow:none !important;}
.stChatInputContainer textarea::placeholder{color:#8a8a8a !important;}
[data-testid='stChatInput'] button{background:#3a3a3a !important;}
[data-testid='stChatInput'] button{border:none !important;}
*:focus{outline:none !important;box-shadow:none !important;}
.music-box{background:#17171a !important;}
.music-box{border-radius:16px !important;padding:12px !important;}
.model-kucuk{font-size:11px !important;color:#666 !important;}
.model-kucuk{text-align:center !important;margin-top:30px !important;}
</style>
''', unsafe_allow_html=True)

def get_conn():
 c = sqlite3.connect('vorph.db', check_same_thread=False)
 c.execute('PRAGMA journal_mode=WAL;')
 return c

def init_db():
 conn = get_conn()
 conn.execute('CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, user_name TEXT, title TEXT)')
 conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT)')
 conn.commit()
 conn.close()

def create_chat(user_name, title='Yeni Sohbet'):
 chat_id = str(uuid.uuid4())[:8]
 conn = get_conn()
 conn.execute('INSERT INTO chats (id, user_name, title) VALUES (?, ?, ?)', [chat_id, user_name, title])
 conn.commit()
 conn.close()
 return chat_id

def get_chats(user_name):
 conn = get_conn()
 cur = conn.cursor()
 cur.execute('SELECT id, title FROM chats WHERE user_name=? ORDER BY rowid DESC', [user_name])
 rows = cur.fetchall()
 conn.close()
 return rows

def get_messages_db(chat_id):
 conn = get_conn()
 cur = conn.cursor()
 cur.execute('SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC', [chat_id])
 rows = cur.fetchall()
 conn.close()
 out = []
 for r in rows:
  out.append({'role': r[0], 'content': r[1]})
 return out

def add_message_db(chat_id, role, content):
 conn = get_conn()
 conn.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)', [chat_id, role, content])
 if role == 'user':
  kisa = content[:30]
  conn.execute("UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'", [kisa, chat_id])
 conn.commit()
 conn.close()

def delete_chat_db(chat_id):
 conn = get_conn()
 conn.execute('DELETE FROM messages WHERE chat_id=?', [chat_id])
 conn.execute('DELETE FROM chats WHERE id=?', [chat_id])
 conn.commit()
 conn.close()

init_db()

if 'user_name' not in st.session_state:
 st.session_state.user_name = ''
if 'current_chat_id' not in st.session_state:
 st.session_state.current_chat_id = None
if 'messages' not in st.session_state:
 st.session_state.messages = []
if 'muzik_acik' not in st.session_state:
 st.session_state.muzik_acik = False
if 'secili_sarki' not in st.session_state:
 st.session_state.secili_sarki = 'Lo-Fi Chill'

efektif_isim = 'anonim'
if st.session_state.user_name:
 if st.session_state.user_name.strip() != '':
  efektif_isim = st.session_state.user_name.strip()

gemini_key = st.secrets.get('GEMINI_API_KEY', '')
if not gemini_key:
 st.error('Secrets yok')
 st.stop()

client = OpenAI(
 base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
 api_key=gemini_key
)

selected_model = 'gemini-3-flash-preview'

with st.sidebar:
 st.title('VorpH AI')
 st.caption('Profesyonel Asistan')
 user_name_input = st.text_input('Isminiz', value=st.session_state.user_name)
 if user_name_input != st.session_state.user_name:
  st.session_state.user_name = user_name_input
  st.session_state.current_chat_id = None
  st.session_state.messages = []
  st.rerun()
 if st.session_state.user_name == '':
  st.caption('Anonim devam')
 else:
  st.caption('Merhaba')
  st.caption(st.session_state.user_name)
 st.markdown('---')
 modlar = ['Genel Asistan', 'Yazilim Uzmami', 'Detayli Uzman', 'Resmi']
 personality = st.selectbox('Asistan Modu', modlar)
 st.markdown('---')
 st.subheader('VorpH Muzik')
 st.caption('Muzik')
 sarki_listesi = {
  'Lo-Fi Chill': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
  'Gece Surusu': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
  'Odaklanma': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
  'Yagmur Hissi': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
  'Enerji': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3',
  'Sakin Aksam': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
 }
 sarki_isimleri = list(sarki_listesi.keys())
 secim = st.selectbox('Sarki Sec', sarki_isimleri)
 st.session_state.secili_sarki = secim
 muzik_acik = st.toggle('Muzigi Ac', value=st.session_state.muzik_acik)
 st.session_state.muzik_acik = muzik_acik
 if st.session_state.muzik_acik:
  st.markdown('<div class="music-box">Caliyor</div>', unsafe_allow_html=True)
  st.markdown(st.session_state.secili_sarki)
  st.audio(sarki_listesi[st.session_state.secili_sarki], format='audio/mp3', autoplay=True)
  if st.button('Durdur', use_container_width=True):
   st.session_state.muzik_acik = False
   st.rerun()
 st.markdown('---')
 if st.button('Yeni Sohbet', use_container_width=True, type='primary'):
  new_id = create_chat(efektif_isim)
  st.session_state.current_chat_id = new_id
  st.session_state.messages = []
  st.rerun()
 st.markdown('---')
 st.subheader('Gecmis Sohbetler')
 chats = get_chats(efektif_isim)
 for cid, title in chats:
  col1, col2 = st.columns([4, 1])
  with col1:
   if st.button(title, key=f'chat_{cid}', use_container_width=True):
    st.session_state.current_chat_id = cid
    st.session_state.messages = get_messages_db(cid)
    st.rerun()
  with col2:
   if st.button('SIL', key=f'del_{cid}'):
    delete_chat_db(cid)
    if st.session_state.current_chat_id == cid:
     st.session_state.current_chat_id = None
     st.session_state.messages = []
    st.rerun()
 st.markdown('<div class="model-kucuk">Gemini 3 Flash</div>', unsafe_allow_html=True)

if not st.session_state.current_chat_id:
 if chats:
  st.session_state.current_chat_id = chats[0][0]
  st.session_state.messages = get_messages_db(chats[0][0])
 else:
  new_id = create_chat(efektif_isim)
  st.session_state.current_chat_id = new_id

st.markdown('''<div class="meta-topbar"><div class="meta-title">VorpH AI</div></div>''', unsafe_allow_html=True)

if not st.session_state.messages:
 st.markdown('''<div class="meta-logo-wrap"><div class="meta-flash">⚡</div><div class="meta-hello">VorpH'a ne soracaksin?</div></div>''', unsafe_allow_html=True)
else:
 for m in st.session_state.messages:
  with st.chat_message(m['role']):
   st.markdown(m['content'])

prompts = {
 'Genel Asistan': 'Sen VorpH adinda samimi bir asistansin.',
 'Yazilim Uzmami': 'Sen VorpH adinda kidemli bir yazilim mimarisin.',
 'Detayli Uzman': 'Sen VorpH adinda detayli anlatan bir uzmansin.',
 'Resmi': 'Sen VorpH adinda resmi bir asist
