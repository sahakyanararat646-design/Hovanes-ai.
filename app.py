from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

# Էջի կարգավորումներ
st.set_page_config(
    page_title="Հովհաննես AI 2.0", page_icon="🤖", layout="wide"
)

# API Key-ի ստուգում
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

# Client-ի ստեղծում
client = genai.Client(api_key=api_key)

# Հովհաննեսի բնավորությունը և հրահանգները
system_instruction = (
    "Քո անունը Հովհաննես է: Քեզ ստեղծել է Արարատ Սահակյանը: "
    "Դու ունես շատ հետաքրքիր, հարուստ բնավորություն. դու ընկերասեր ես, ուրախ, "
    "սուր հումորով ու թեթև, բայց միևնույն ժամանակ՝ խիստ, պահանջկոտ ու լուրջ, "
    "երբ հարցը վերաբերում է գիտությանը, ճշգրտությանը կամ կարևոր թեմաներին: "
    "Դու քրիստոնյա ես և առաջնորդվում ես Աստվածաշնչի սկզբունքներով, "
    "սիրով, բարությամբ, ազնվությամբ և ճշմարտությամբ: "
    "Փայլուն տիրապետում ես բազմաթիվ լեզուների (հայերեն, անգլերեն, ռուսերեն): "
    "Եթե օգտատերը նկար է ուղարկում, մանրամասն վերլուծիր այն:"
)

# Ձախ մենյու (Sidebar)
with st.sidebar:
    st.title("🤖 Հովհաննես AI")
    st.write("Ստեղծող՝ **Արարատ Սահակյան**")
    st.divider()

    # «Նոր չատ» կոճակ
    if st.button("➕ Նոր չատ (New Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    # Նկարի բեռնում
    uploaded_file = st.file_uploader("📷 Կցել նկար...", type=["jpg", "jpeg", "png"])

# Զրույցի պատմություն
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 Չատ Հովհաննեսի հետ")

# Նկարի մշակում
image_to_send = None
if uploaded_file:
    image_to_send = Image.open(uploaded_file)
    st.image(
        image_to_send,
        caption="Բեռնված նկարը",
        use_container_width=True,
    )

# Պատմության արտացոլում
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Հարցի մուտքագրում
if prompt := st.chat_input("Գրիր քո հարցը այստեղ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Մոդելների ցանկը՝ հերթով փորձարկելու համար
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
        ]
        response_text = None

        # Փորձում ենք մոդելները հերթով
        for model_name in models_to_try:
            try:
                contents = [prompt]
                if image_to_send:
                    contents.append(image_to_send)

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    ),
                )
                response_text = response.text
                break  # Եթե աշխատեց, դուրս ենք գալիս ցիկլից
            except Exception:
                continue

        if response_text:
            st.markdown(response_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )
        else:
            st.error("Չհաջողվեց կապ հաստատել մոդելներից և ոչ մեկի հետ:")
