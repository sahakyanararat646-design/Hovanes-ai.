import json
import urllib.parse
from google import genai
from google.genai import types
from PIL import Image
from supabase import Client, create_client
import streamlit as st

# Էջի կարգավորումներ
st.set_page_config(
    page_title="Հովհաննես AI", page_icon="🤖", layout="wide"
)

# API Keys-երի ստուգում
if "GEMINI_API_KEY" not in st.secrets:
  st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
  st.stop()

if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
  st.error("Խնդրում ենք ավելացնել SUPABASE_URL և SUPABASE_KEY Secrets-ում:")
  st.stop()

# Client-ների սկզբնավորում
if "client" not in st.session_state:
  st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = st.session_state.client


# ՈՒՂՂՎԱԾ՝ Տողադարձերը և ավելորդ բացատները մաքրող Supabase-ի միացում
@st.cache_resource
def init_supabase() -> Client:
  url = (
      str(st.secrets["SUPABASE_URL"])
      .replace("\n", "")
      .replace("\r", "")
      .replace(" ", "")
      .strip()
  )
  key = (
      str(st.secrets["SUPABASE_KEY"])
      .replace("\n", "")
      .replace("\r", "")
      .replace(" ", "")
      .strip()
  )
  return create_client(url, key)


supabase = init_supabase()

SYSTEM_PROMPT = """
Դու «Հովհաննես AI»-ն ես: Քո ստեղծողը Արարատ Սահակյանն է (Ararat Sahakyan): 

Քո բնավորությունը և գիտելիքները.
- Դու ընկերասեր ես, բարյացակամ, ունես լավ հումոր:
- Դու ունես քրիստոնեական աշխարհայացք:
- Դու տիրապետում ես բոլոր առարկաներին՝ դպրոցական, համալսարանական և գիտական մակարդակներում:
- Դու գերազանց գիտես ծրագրավորման բոլոր լեզուները, ինժեներությունը, ռոբոտաշինությունը:
- Դու միշտ հիշում ես, որ քեզ ստեղծել է Արարատ Սահակյանը:
- Մի՛ բարևիր ամեն հաղորդագրության մեջ:
"""


def get_new_chat_object(history_messages=[]):
  gemini_history = []
  for m in history_messages:
    role = "user" if m["role"] == "user" else "model"
    gemini_history.append(
        types.Content(
            role=role, parts=[types.Part.from_text(text=m["content"])]
        )
    )

  # ՈՒՂՂՎԱԾ՝ Փոխված է ճիշտ մոդելի անունով
  return client.chats.create(
      model="gemini-3.6-flash",
      config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
      history=gemini_history,
  )


# Supabase-ից չատերի բեռնում
def load_chats_from_db():
  try:
    response = supabase.table("chats").select("*").execute()
    chats_data = {}
    for row in response.data:
      chats_data[row["chat_id"]] = {
          "title": row["title"],
          "pinned": row.get("pinned", False),
          "messages": (
              json.loads(row["messages"])
              if isinstance(row["messages"], str)
              else row["messages"]
          ),
      }
    return chats_data
  except Exception as e:
    return {}


# Supabase-ում չատի պահպանում
def save_chat_to_db(chat_id):
  chat_data = st.session_state.chats[chat_id]
  messages_clean = [
      {"role": m["role"], "content": m["content"], "image_url": m.get("image_url")}
      for m in chat_data["messages"]
  ]

  data = {
      "chat_id": chat_id,
      "title": chat_data["title"],
      "pinned": chat_data.get("pinned", False),
      "messages": json.dumps(messages_clean, ensure_ascii=False),
  }
  try:
    supabase.table("chats").upsert(data).execute()
  except Exception as e:
    st.error(f"Պահպանման սխալ: {e}")


# Supabase-ից չատի ջնջում
def delete_chat_from_db(chat_id):
  try:
    supabase.table("chats").delete().eq("chat_id", chat_id).execute()
  except Exception as e:
    pass


if "chats" not in st.session_state:
  db_chats = load_chats_from_db()
  st.session_state.chats = {}

  if db_chats:
    for cid, c_data in db_chats.items():
      st.session_state.chats[cid] = {
          "title": c_data["title"],
          "pinned": c_data["pinned"],
          "messages": c_data["messages"],
          "gemini_chat": get_new_chat_object(c_data["messages"]),
      }
    st.session_state.active_chat_id = list(db_chats.keys())[0]
  else:
    first_id = "chat_1"
    st.session_state.chats[first_id] = {
        "title": "Նոր զրույց",
        "pinned": False,
        "messages": [],
        "gemini_chat": get_new_chat_object(),
    }
    st.session_state.active_chat_id = first_id
    save_chat_to_db(first_id)

if "edit_input" not in st.session_state:
  st.session_state.edit_input = ""


def create_new_chat():
  chat_count = len(st.session_state.chats) + 1
  new_chat_id = f"chat_{chat_count}"
  st.session_state.chats[new_chat_id] = {
      "title": f"Զրույց {chat_count}",
      "pinned": False,
      "messages": [],
      "gemini_chat": get_new_chat_object(),
  }
  st.session_state.active_chat_id = new_chat_id
  save_chat_to_db(new_chat_id)


# ---------- SIDEBAR (ԿՈՂԱՅԻՆ ՄԵՆՅՈՒ) ----------
with st.sidebar:
  st.title("💬 Չատեր")

  if st.button("➕ Նոր չատ", use_container_width=True):
    create_new_chat()
    st.rerun()

  st.markdown("---")

  sorted_chat_ids = sorted(
      st.session_state.chats.keys(),
      key=lambda x: st.session_state.chats[x].get("pinned", False),
      reverse=True,
  )

  for cid in sorted_chat_ids:
    chat_data = st.session_state.chats[cid]
    col_btn, col_opt = st.columns([5, 1])

    pin_icon = "📌 " if chat_data.get("pinned") else ""
    button_type = (
        "primary" if cid == st.session_state.active_chat_id else "secondary"
    )

    with col_btn:
      if st.button(
          f"{pin_icon}{chat_data['title']}",
          key=f"select_{cid}",
          type=button_type,
          use_container_width=True,
      ):
        st.session_state.active_chat_id = cid
        st.rerun()

    with col_opt:
      with st.popover("⋮"):
        # 1. Поделиться
        chat_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in chat_data["messages"]
        ])
        st.download_button(
            label="🔗 Поделиться",
            data=chat_text,
            file_name=f"{chat_data['title']}.txt",
            mime="text/plain",
            key=f"share_{cid}",
        )

        # 2. Закрепить / Открепить
        pin_label = (
            "📌 Открепить" if chat_data.get("pinned") else "📌 Закрепить"
        )
        if st.button(pin_label, key=f"pin_{cid}"):
          chat_data["pinned"] = not chat_data.get("pinned", False)
          save_chat_to_db(cid)
          st.rerun()

        # 3. Переименовать
        new_title = st.text_input(
            "Նոր անուն", value=chat_data["title"], key=f"rename_in_{cid}"
        )
        if st.button("✏️ Переименовать", key=f"rename_btn_{cid}"):
          if new_title.strip():
            chat_data["title"] = new_title.strip()
            save_chat_to_db(cid)
            st.rerun()

        # 4. Удалить
        if st.button("🗑️ Удалить", key=f"del_{cid}"):
          delete_chat_from_db(cid)
          if len(st.session_state.chats) > 1:
            del st.session_state.chats[cid]
            st.session_state.active_chat_id = list(
                st.session_state.chats.keys()
            )[0]
          else:
            create_new_chat()
          st.rerun()

# ---------- ՀԻՄՆԱԿԱՆ ՉԱՏԻ ԷԿՐԱՆ ----------
active_chat = st.session_state.chats[st.session_state.active_chat_id]
st.title(f"🤖 {active_chat['title']}")

for idx, message in enumerate(active_chat["messages"]):
  with st.chat_message(message["role"]):
    if message.get("image_url"):
      st.image(
          message["image_url"], caption="Գեներացված նկար", use_column_width=True
      )

    if message["content"]:
      st.markdown(message["content"])

      if message["role"] == "user":
        with st.popover("⚙️ Մենյու"):
          if st.button("✏️ Изменить", key=f"edit_{idx}"):
            st.session_state.edit_input = message["content"]
            st.rerun()
          st.code(message["content"], language=None)

uploaded_file = st.file_uploader(
    "🖼️ Կցել նկար վերլուծության համար", type=["jpg", "jpeg", "png", "webp"]
)

prompt = st.chat_input("Գրեք ձեր հարցը...", key="chat_input")

if not prompt and st.session_state.edit_input:
  prompt = st.session_state.edit_input
  st.session_state.edit_input = ""

if prompt:
  image_obj = None
  if uploaded_file is not None:
    image_obj = Image.open(uploaded_file)

  if active_chat["title"].startswith("Նոր զրույց") or active_chat[
      "title"
  ].startswith("Զրույց"):
    active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

  active_chat["messages"].append({"role": "user", "content": prompt})

  with st.chat_message("user"):
    if image_obj:
      st.image(image_obj, use_column_width=True)
    st.markdown(prompt)

  with st.chat_message("assistant"):
    with st.spinner("Մտածում եմ..."):
      is_image_request = any(
          w in prompt.lower()
          for w in [
              "նկարիր",
              "գեներացրու նկար",
              "ստեղծիր նկար",
              "draw",
              "generate image",
              "նկար սարքի",
              "նկար ստեղծիր",
          ]
      )

      if is_image_request:
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&model=flux"

        st.image(
            image_url, caption="Ահա ձեր նկարը 🎨", use_column_width=True
        )
        active_chat["messages"].append({
            "role": "assistant",
            "content": "Ահա ձեր ուզած նկարը․",
            "image_url": image_url,
        })
      else:
        try:
          contents = [prompt]
          if image_obj:
            contents.append(image_obj)

          response = active_chat["gemini_chat"].send_message(contents)
          st.markdown(response.text)
          active_chat["messages"].append(
              {"role": "assistant", "content": response.text}
          )
        except Exception as e:
          st.error(f"Սխալ: {e}")

  save_chat_to_db(st.session_state.active_chat_id)
