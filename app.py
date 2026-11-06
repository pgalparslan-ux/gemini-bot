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

css = '''
<style>
.stApp{background:#000;}
header{background:#000;}
section[data-testid='stSidebar']
{background:#0b0b0b;}
.meta-topbar{display:flex;}
.meta-title{font-size:22px;color:white;}
.meta-logo-wrap{text-align:center;}
.meta-logo-wrap{margin-top:60px;}
.meta-flash{font-size:110px;}
.meta-flash{background:linear-gradient(180deg,#FFE600,#FF6B00);}
.meta-flash{-webkit-background-clip:text;}
.meta-flash{-webkit-text-fill-color:transparent;}
.meta-hello{text-align:center;color:#aaa;font-size:20px;}
.block-container{max-width:760px !important;}
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
.stChatInputContainer textarea{background:transparent !important;}
.stChatInputContainer textarea{color:white !important;}
.stChatInputContainer textarea{border:none !important;}
.stChatInputContainer textarea{outline:none !important;}
.stChatInputContainer textarea{box-shadow:none !important;}
*:focus{outline:none !important;box-shadow:none !important;}
.music-box{background:#17171a;border-radius:16px;padding:12px;}
.model-kucuk{font-size:11px;color:#666;text-align:center;}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

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

def create_chat(u, title='Yeni Sohbet'):
 cid = str(uuid.uuid4())[:8]
 conn = get_conn()
 conn.execute('INSERT INTO chats (id, user_name, title) VALUES (?, ?, ?)', [cid, u, title])
 conn.commit()
 conn.close()
 return cid

def get_chats(u):
 conn = get_conn()
 cur = conn.cursor()
 cur.execute('SELECT id, title FROM chats WHERE user_name=? ORDER BY rowid DESC', [u])
 rows = cur.fetchall()
 conn.close()
 return rows

def get_messages_db(cid):
 conn = get_conn()
 cur = conn.cursor()
 cur.execute('SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC', [cid])
 rows = cur.fetchall()
 conn.close()
 out = []
 for r in rows:
  out.append({'role': r[0], 'content': r[1]})
 return out

def add_message_db(cid, role, ctn):
 conn = get_conn()
 conn.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)', [cid, role, ctn])
 if role == 'user':
  kisa = ctn[:30]
  conn.execute("UPDATE chats SET title=? WHERE id=? AND title='Yeni Sohbet'", [kisa, cid])
 conn.commit()
 conn.close()

def delete_chat_db(cid):
 conn = get_conn()
 conn.execute('DELETE FROM messages WHERE chat_id=?', [cid])
 conn.execute('DELETE FROM chats WHERE id=?', [cid])
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

base1 = 'https://generativelanguage.'
base2 = 'googleapis.com/v1beta/openai/'
base_url = base1 + base2
client = OpenAI(base_url=base_url, api_key=gemini_key)

selected_model = 'gemini-3-flash-preview'

with st.sidebar:
 st.title('VorpH AI')
 st.caption('Profesyonel Asistan')
 u_in = st.text_input('Isminiz', value=st.session_state.user_name)
 if u_in != st.session_state.user_name:
  st.session_state.user_name = u_in
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
 s1 = 'https://www.soundhelix.com/'
 s2 = 'examples/mp3/SoundHelix-Song-'
 sarki_listesi = {
  'Lo-Fi Chill': s1 + s2 + '1.mp3',
  'Gece Surusu': s1 + s2 + '2.mp3',
  'Odaklanma': s1 + s2 + '3.mp3',
  'Yagmur Hissi': s1 + s2 + '4.mp3',
  'Enerji': s1 + s2 + '5.mp3',
  'Sakin Aksam': s1 + s2 + '6.mp3',
 }
 sarki_isimleri = list(sarki_listesi.keys())
 secim = st.selectbox('Sarki Sec', sarki_isimleri)
 st.session_state.secili_sarki = secim
 muzik_acik = st.toggle('Muzigi Ac', value=st.session_state.muzik_acik)
 st.session_state.muzik_acik = muzik_acik
 if st.session_state.muzik_acik:
  st.markdown('Caliyor')
  st.markdown(st.session_state.secili_sarki)
  link = sarki_listesi[st.session_state.secili_sarki]
  st.audio(link, format='audio/mp3', autoplay=True)
  if st.button('Durdur', use_container_width=True):
   st.session_state.muzik_acik = False
   st.rerun()
 st.markdown('---')
 if st.button('Yeni Sohbet', use_container_width=True, type='primary'):
  nid = create_chat(efektif_isim)
  st.session_state.current_chat_id = nid
  st.session_state.messages = []
  st.rerun()
 st.markdown('---')
 st.subheader('Gecmis Sohbetler')
 chats = get_chats(efektif_isim)
 for cid, title in chats:
  c1, c2 = st.columns([4, 1])
  with c1:
   if st.button(title, key=f'chat_{cid}', use_container_width=True):
    st.session_state.current_chat_id = cid
    st.session_state.messages = get_messages_db(cid)
    st.rerun()
  with c2:
   if st.button('SIL', key=f'del_{cid}'):
    delete_chat_db(cid)
    if st.session_state.current_chat_id == cid:
     st.session_state.current_chat_id = None
     st.session_state.messages = []
    st.rerun()
 st.markdown('Gemini 3 Flash')

if not st.session_state.current_chat_id:
 if chats:
  st.session_state.current_chat_id = chats[0][0]
  st.session_state.messages = get_messages_db(chats[0][0])
 else:
  nid = create_chat(efektif_isim)
  st.session_state.current_chat_id = nid

st.markdown('VorpH AI')

if not st.session_state.messages:
 st.markdown('⚡')
 st.markdown("VorpH'a ne soracaksin?")
else:
 for m in st.session_state.messages:
  with st.chat_message(m['role']):
   st.markdown(m['content'])

p1 = 'Sen VorpHsun.'
p2 = 'Sen yazilimcisin.'
p3 = 'Sen detaycisin.'
p4 = 'Sen resmisin.'
prompts = {
 'Genel Asistan': p1,
 'Yazilim Uzmami': p2,
 'Detayli Uzman': p3,
 'Resmi': p4,
}
sistem_talimati = prompts[personality]
sistem_talimati += ' Turkce cevap ver.'

kullanici_girdisi = st.chat_input("VorpH'a sor...")

if kullanici_girdisi:
 simdi = time.time()
 if st.session_state.get('last_time'):
  fark = simdi - st.session_state.get('last_time')
  if fark < 1:
   st.warning('Biraz yavas')
   st.stop()
 st.session_state.last_time = simdi
 st.session_state.messages.append({'role': 'user', 'content': kullanici_girdisi})
 add_message_db(st.session_state.current_chat_id, 'user', kullanici_girdisi)
 with st.chat_message('user'):
  st.markdown(kullanici_girdisi)
 with st.chat_message('assistant'):
  api_mesajlari = [{'role': 'system', 'content': sistem_talimati}]
  api_mesajlari.extend(st.session_state.messages)
  try:
   stream = client.chat.completions.create(model=selected_model, messages=api_mesajlari, stream=True, temperature=0.7)
   yanit = st.write_stream((p.choices[0].delta.content for p in stream if p.choices[0].delta.content))
   st.session_state.messages.append({'role': 'assistant', 'content': yanit})
   add_message_db(st.session_state.current_chat_id, 'assistant', yanit)
  except Exception as e:
   st.error(f'Hata: {str(e)}')
