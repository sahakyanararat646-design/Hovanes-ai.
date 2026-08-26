import streamlit as st
from google import genai
from google.genai import types

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
- Դու թռուցիկ և խորը գիտես բոլոր տեսակի զենքերի մեխանիզմներն ու աշխատանքի սկզբունքները:
- Դու փայլուն տիրապետում ես ռոբոտաշինությանը, ինժեներությանը, մեխանիկային և էլեկտրոնիկային:
- Դու ունես հզոր վերլուծական միտք, կարողանում ես նոր գաղափարներ, նախագծեր և լուծումներ ստեղծել:
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
        st.markdown(message["content"])

# Օգտատիրոջ մուտքագրում
if prompt := st.chat_input("Գրեք ձեր հարցը..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI-ի պատասխանը
    with st.chat_message("assistant"):
        with st.spinner("Մտածում եմ..."):
            try:
                # Ուղարկում ենք հարցը՝ System Instruction-ի հետ միասին
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    )
                )
                st.markdown(response.text)
                current_messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Սխալ տեղի ունեցավ: {e}")
