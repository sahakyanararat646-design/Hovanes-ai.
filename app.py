import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

# Էջի կարգավորումներ
st.set_page_config(page_title="Հովհաննես AI", page_icon="🤖", layout="wide")

# API Key-ի ստուգում
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

# Պահում ենք Client-ը session_state-ում, որպեսզի չփակվի
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = st.session_state.client

# ---------- SYSTEM INSTRUCTION ----------
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

# ---------- ՉԱՏԵՐԻ ՊԱՀՊԱՆՈՒՄ ----------
if "chats" not in st.session_state:
    st.session_state.chats = {}

def get_new_chat_object():
    return client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )

if "active_chat_id" not in st.session_state:
    first_id = "chat_1"
    st.session_state.chats[first_id] = {
        "title": "Նոր զրույց",
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
        "messages": [],
        "gemini_chat": get_new_chat_object()
    }
    st.session_state.active_chat_id = new_chat_id

# ---------- SIDEBAR (ԿՈՂԱՅԻՆ ՄԵՆՅՈՒ) ----------
with st.sidebar:
    st.title("💬 Չատերի Պատմություն")
    
    if st.button("➕ Նոր չատ", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    st.write("**Քո չատերը․**")
    
    for cid, chat_data in reversed(list(st.session_state.chats.items())):
        button_type = "primary" if cid == st.session_state.active_chat_id else "secondary"
        if st.button(chat_data["title"], key=cid, type=button_type, use_container_width=True):
            st.session_state.active_chat_id = cid
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Ջնջել այս չատը", use_container_width=True):
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[st.session_state.active_chat_id]
            st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
        else:
            create_new_chat()
        st.rerun()

# ---------- ՀԻՄՆԱԿԱՆ ՉԱՏԻ ԷԿՐԱՆ ----------
active_chat = st.session_state.chats[st.session_state.active_chat_id]
st.title(f"🤖 {active_chat['title']}")

# Ցուցադրում ենք նախորդ հաղորդագրությունները + Edit կոճակ
for idx, message in enumerate(active_chat["messages"]):
    with st.chat_message(message["role"]):
        if "image" in message and message["image"] is not None:
            st.image(message["image"], use_column_width=True)
        if message["content"]:
            st.markdown(message["content"])
            
            if message["role"] == "user":
                col1, col2 = st.columns([1, 10])
                with col1:
                    if st.button("✏️ Փոխել", key=f"edit_{idx}"):
                        st.session_state.edit_input = message["content"]
                        st.rerun()

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
        active_chat["title"] = prompt[:30] + ("..." if len(prompt) > 30 else "")

    active_chat["messages"].append({"role": "user", "content": prompt, "image": image_obj})
    
    with st.chat_message("user"):
        if image_obj:
            st.image(image_obj, use_column_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Մտածում եմ..."):
            try:
                # Եթե հարցի մեջ խնդրվում է նկար գեներացնել
                if any(w in prompt.lower() for w in ["նկարիր", "գեներացրու նկար", "ստեղծիր նկար", "draw", "generate image"]):
                    img_result = client.models.generate_images(
                        model='imagen-3.0-generate-002',
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/jpeg",
                            aspect_ratio="1:1",
                        )
                    )
                    for generated_image in img_result.generated_images:
                        gen_img = Image.open(io.BytesIO(generated_image.image.image_bytes))
                        st.image(gen_img, caption="Գեներացված նկար")
                        active_chat["messages"].append({"role": "assistant", "content": "Ահա ձեր ուզած նկարը:", "image": gen_img})
                else:
                    contents = [prompt]
                    if image_obj:
                        contents.append(image_obj)

                    response = active_chat["gemini_chat"].send_message(contents)
                    st.markdown(response.text)
                    active_chat["messages"].append({"role": "assistant", "content": response.text})

            except Exception as e:
                err_text = str(e)
                if "429" in err_text:
                    st.warning("⚠️ Անվճար լիմիտը սպառվել է: Խնդրում ենք սպասել 30 վայրկյան:")
                elif "closed" in err_text:
                    # Եթե կապը կտրվի, վերաստեղծում ենք չատի օբյեկտը
                    active_chat["gemini_chat"] = get_new_chat_object()
                    st.warning("⚠️ Կապը թարմացվեց: Խնդրում ենք կրկին ուղարկել հարցը:")
                else:
                    st.error(f"Սխալ: {e}")
