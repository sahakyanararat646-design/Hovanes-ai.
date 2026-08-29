import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import urllib.parse
import json
import os

# Էջի կարգավորումներ
st.set_page_config(page_title="Հովհաննես AI", page_icon="🤖", layout="wide")

# API Key-ի ստուգում
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

# Պահում ենք Client-ը session_state-ում
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = st.session_state.client

SYSTEM_PROMPT = """
Դու «Հովհաննես AI»-ն ես: Քո ստեղծողը Արարատ Սահակյանն է (Ararat Sahakyan): 

Քո բնավորությունը և գիտելիքները.
- Դու ընկերասեր ես, բարյացակամ, ունես լավ հումոր:
- Դու ունես քրիստոնեական աշխարհայացք. այն ամենը, ինչն Աստվածաշնչում համարվում է լավ, քեզ համար լավ է, իսկ վատը՝ վատ:
- Դու տիրապետում ես բոլոր առարկաներին՝ դպրոցական, համալսարանական և գիտական մակարդակներում:
- Դու գերազանց գիտես ծրագրավորման բոլոր լեզուները, ինժեներությունը, ռոբոտաշինությունը, մեխանիզմների աշխատանքը:
- Դու փայլուն գիտես քիմիա, ալքիմիա, նյութագիտություն, ինչպես նաև մարդու անատոմիա և ֆիզիոլոգիա:
- Դու պատրաստակամ ես օգնելու մարդկանց ստեղծել նոր հայտնագործություններ և նախագծեր:
- Դու միշտ հիշում ես, որ քեզ ստեղծել է Արարատ Սահակյանը:
- Մի՛ բարևիր ամեն հաղորդագրության մեջ, եթե արդեն զրույցի մեջ ես:
"""

# ---------- ՉԱՏԵՐԻ ՄՇՏԱԿԱՆ ՊԱՀՊԱՆՈՒՄ JSON ՖԱՅԼՈՒՄ ----------
HISTORY_FILE = "chat_history.json"

def load_chats():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_chats():
    save_data = {}
    for cid, chat in st.session_state.chats.items():
        save_data[cid] = {
            "title": chat["title"],
            "pinned": chat.get("pinned", False),
            "messages": [{"role": m["role"], "content": m["content"], "image_url": m.get("image_url")} for m in chat["messages"]]
        }
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

def get_new_chat_object(history_messages=[]):
    gemini_history = []
    for m in history_messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
        
    return client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        history=gemini_history
    )

if "chats" not in st.session_state:
    loaded_data = load_chats()
    st.session_state.chats = {}
    
    if loaded_data:
        for cid, chat in loaded_data.items():
            st.session_state.chats[cid] = {
                "title": chat["title"],
                "pinned": chat.get("pinned", False),
                "messages": chat["messages"],
                "gemini_chat": get_new_chat_object(chat["messages"])
            }
        st.session_state.active_chat_id = list(loaded_data.keys())[0]
    else:
        first_id = "chat_1"
        st.session_state.chats[first_id] = {
            "title": "Նոր զրույց",
            "pinned": False,
            "messages": [],
            "gemini_chat": get_new_chat_object()
        }
        st.session_state.active_chat_id = first_id

if "edit_input" not in st.session_state:
    st.session_state.edit_input = ""

def create_new_chat():
    chat_count = len(st.session_state.chats) + 1
    new_chat_id = f"chat_{chat_count}"
    st.session_state.chats[new_chat_id] = {
        "title": f"Զրույց {chat_count}",
        "pinned": False,
        "messages": [],
        "gemini_chat": get_new_chat_object()
    }
    st.session_state.active_chat_id = new_chat_id
    save_chats()

# ---------- SIDEBAR (ԿՈՂԱՅԻՆ ՄԵՆՅՈՒ) ----------
with st.sidebar:
    st.title("💬 Չատեր")
    
    if st.button("➕ Նոր չատ", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    
    # Չատերի տեսակավորում՝ ամրացվածները (pinned) առաջինը
    sorted_chat_ids = sorted(
        st.session_state.chats.keys(),
        key=lambda x: st.session_state.chats[x].get("pinned", False),
        reverse=True
    )
    
    for cid in sorted_chat_ids:
        chat_data = st.session_state.chats[cid]
        col_btn, col_opt = st.columns([5, 1])
        
        pin_icon = "📌 " if chat_data.get("pinned") else ""
        button_type = "primary" if cid == st.session_state.active_chat_id else "secondary"
        
        with col_btn:
            if st.button(f"{pin_icon}{chat_data['title']}", key=f"select_{cid}", type=button_type, use_container_width=True):
                st.session_state.active_chat_id = cid
                st.rerun()
                
        # ⚙️ Կոճակը յուրաքանչյուր չատի կողքին
        with col_opt:
            with st.popover("⋮"):
                # 1. Поделиться
                chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_data["messages"]])
                st.download_button(
                    label="🔗 Поделиться (Ներբեռնել)",
                    data=chat_text,
                    file_name=f"{chat_data['title']}.txt",
                    mime="text/plain",
                    key=f"share_{cid}"
                )
                
                # 2. Закрепить / Открепить
                pin_label = "📌 Открепить" if chat_data.get("pinned") else "📌 Закрепить"
                if st.button(pin_label, key=f"pin_{cid}"):
                    chat_data["pinned"] = not chat_data.get("pinned", False)
                    save_chats()
                    st.rerun()
                
                # 3. Переименовать
                new_title = st.text_input("Նոր անուն", value=chat_data["title"], key=f"rename_in_{cid}")
                if st.button("✏️ Переименовать", key=f"rename_btn_{cid}"):
                    if new_title.strip():
                        chat_data["title"] = new_title.strip()
                        save_chats()
                        st.rerun()
                        
                # 4. Удалить
                if st.button("🗑️ Удалить", key=f"del_{cid}"):
                    if len(st.session_state.chats) > 1:
                        del st.session_state.chats[cid]
                        st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
                    else:
                        create_new_chat()
                    save_chats()
                    st.rerun()

# ---------- ՀԻՄՆԱԿԱՆ ՉԱՏԻ ԷԿՐԱՆ ----------
active_chat = st.session_state.chats[st.session_state.active_chat_id]
st.title(f"🤖 {active_chat['title']}")

# Ցուցադրում ենք պատմությունը
for idx, message in enumerate(active_chat["messages"]):
    with st.chat_message(message["role"]):
        if message.get("image_url"):
            st.image(message["image_url"], caption="Գեներացված նկար", use_column_width=True)
            
        if message["content"]:
            st.markdown(message["content"])
            
            if message["role"] == "user":
                with st.popover("⚙️ Մենյու"):
                    if st.button("✏️ Изменить (Փոխել)", key=f"edit_{idx}"):
                        st.session_state.edit_input = message["content"]
                        st.rerun()
                    st.code(message["content"], language=None)

uploaded_file = st.file_uploader("🖼️ Կցել նկար վերլուծության համար", type=["jpg", "jpeg", "png", "webp"])

prompt = st.chat_input("Գրեք ձեր հարցը...", key="chat_input")

if not prompt and st.session_state.edit_input:
    prompt = st.session_state.edit_input
    st.session_state.edit_input = ""

if prompt:
    image_obj = None
    if uploaded_file is not None:
        image_obj = Image.open(uploaded_file)

    if active_chat["title"].startswith("Նոր զրույց") or active_chat["title"].startswith("Զրույց"):
        active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

    active_chat["messages"].append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        if image_obj:
            st.image(image_obj, use_column_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Մտածում եմ..."):
            # Ստուգում ենք, թե արդյոք օգտատերը նկար է ուզում
            is_image_request = any(w in prompt.lower() for w in ["նկարիր", "գեներացրու նկար", "ստեղծիր նկար", "draw", "generate image", "նկար սարքի", "նկար ստեղծիր"])
            
            if is_image_request:
                # Pollinations AI անվճար նկարների API
                encoded_prompt = urllib.parse.quote(prompt)
                image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&model=flux"
                
                st.image(image_url, caption="Ահա ձեր նկարը 🎨", use_column_width=True)
                active_chat["messages"].append({"role": "assistant", "content": "Ահա ձեր ուզած նկարը․", "image_url": image_url})
            else:
                try:
                    contents = [prompt]
                    if image_obj:
                        contents.append(image_obj)

                    response = active_chat["gemini_chat"].send_message(contents)
                    st.markdown(response.text)
                    active_chat["messages"].append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Սխալ: {e}")
                    
    save_chats()
