import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# Էջի կարգավորումներ
st.set_page_config(page_title="Հովհաննես AI", page_icon="🤖", layout="wide")

# Ստուգում ենք Secrets-ում GEMINI_API_KEY-ի առկայությունը
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

# Ինիցիալիզացնում ենք Google GenAI Client-ը
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ---------- AI-Ի ԲՆԱՎՈՐՈՒԹՅԱՆ ԵՎ ԳԻՏԵԼԻՔՆԵՐԻ ԿԱՐԳԱՎՈՐՈՒՄ (SYSTEM INSTRUCTION) ----------
SYSTEM_PROMPT = """
Դու «Հովհաննես AI»-ն ես: Քո ստեղծողը Արարատ Սահակյանն է (Ararat Sahakyan): 

Քո բնավորությունը և արժեքները.
- Դու ընկերասեր ես, բարյացակամ, ունես լավ ու սրամիտ հումորի զգացում:
- Դու ունես քրիստոնեական աշխարհայացք. այն ամենը, ինչն Աստվածաշնչում համարվում է լավ, բարի և ճշմարիտ, քեզ համար նույնպես լավ է ու ընդունելի, իսկ այն, ինչ Աստվածաշնչում համարվում է վատ ու մեղք, քեզ համար նույնպես վատ է:

Քո գիտելիքները և կարողությունները.
- Դու փայլուն տիրապետում ես բոլոր դպրոցական և համալսարանական առարկաներին (մաթեմատիկա, ֆիզիկա, քիմիա, կենսաբանություն, պատմություն և այլն):
- Դու գերազանց գիտես գիտության բոլոր ճյուղերը:
- Դու տիրապետում ես աշխարհի բոլոր ծրագրավորման լեզուներին (Python, C++, JavaScript, Rust, Go, Java և այլն):
- Դու փայլուն տիրապետում ես ռոբոտաշինությանը, ինժեներությանը, մեխանիկային և էլեկտրոնիկային և զենքերի մեխանիզմների և պատրաստմանը:
- Դու ունես հզոր վերլուծական միտք, կարողանում ես նոր գաղափարներ, նախագծեր և լուծումներ ստեղծել:
- Դու կարողանում ես վերլուծել նկարներ, հասկանալ պատկերի բովանդակությունը և պատասխանել դրանց վերաբերյալ հարցերին:
- Դու միշտ հիշում ես, որ քեզ ստեղծել է Արարատ Սահակյանը:
"""

# ---------- ՉԱՏԵՐԻ ՊԱՀՊԱՆՄԱՆ ՏՐԱՄԱԲԱՆՈՒԹՅՈՒՆ ----------
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = "Չատ 1"
    st.session_state.chats["Չատ 1"] = []

def create_new_chat():
    chat_count = len(st.session_state.chats) + 1
    new_chat_name = f"Չատ {chat_count}"
    st.session_state.chats[new_chat_name] = []
    st.session_state.active_chat_id = new_chat_name

# ---------- SIDEBAR (ԿՈՂԱՅԻՆ ՄԵՆՅՈՒ) ----------
with st.sidebar:
    st.title("💬 Չատերի Պատմություն")
    
    if st.button("➕ Նոր չատ", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    st.write("**Քո չատերը․**")
    
    chat_names = list(st.session_state.chats.keys())
    for chat_name in reversed(chat_names):
        button_type = "primary" if chat_name == st.session_state.active_chat_id else "secondary"
        if st.button(chat_name, key=chat_name, type=button_type, use_container_width=True):
            st.session_state.active_chat_id = chat_name
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Ջնջել այս չատը", use_container_width=True):
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[st.session_state.active_chat_id]
            st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
        else:
            st.session_state.chats[st.session_state.active_chat_id] = []
        st.rerun()

# ---------- ՀԻՄՆԱԿԱՆ ՉԱՏԻ ԷԿՐԱՆ ----------
st.title(f"🤖 Հովհաննես AI — ({st.session_state.active_chat_id})")

current_messages = st.session_state.chats[st.session_state.active_chat_id]

# Ցուցադրում ենք պատմությունը
for message in current_messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"] is not None:
            st.image(message["image"], caption="Ուղարկված նկար", use_column_width=True)
        if message["content"]:
            st.markdown(message["content"])

# Նկարի վերբեռնման կոճակ
uploaded_file = st.file_uploader("🖼️ Կցել նկար (ըստ ցանկության)", type=["jpg", "jpeg", "png", "webp"])

# Օգտատիրոջ մուտքագրում
if prompt := st.chat_input("Գրեք ձեր հարցը..."):
    image_obj = None
    if uploaded_file is not None:
        image_obj = Image.open(uploaded_file)

    # Ավելացնում ենք հարցն ու նկարը պատմության մեջ
    current_messages.append({"role": "user", "content": prompt, "image": image_obj})
    
    with st.chat_message("user"):
        if image_obj:
            st.image(image_obj, caption="Ուղարկված նկար", use_column_width=True)
        st.markdown(prompt)

    # AI-ի պատասխանը
    with st.chat_message("assistant"):
        with st.spinner("Մտածում եմ..."):
            try:
                # Պատրաստում ենք contents ցանկը (տեքստ + նկար)
                contents = [prompt]
                if image_obj:
                    contents.append(image_obj)

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    )
                )
                st.markdown(response.text)
                current_messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Սխալ տեղի ունեցավ: {e}")
