from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Հովհաննես AI 2.0", page_icon="🤖", layout="wide"
)

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

client = genai.Client(api_key=api_key)

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

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🤖 Հովհաննես AI")
    st.write("Ստեղծող՝ **Արարատ Սահակյան**")
    st.divider()

    if st.button("➕ Նոր չատ (New Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️ Ջնջել պատմությունը (Clear Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    uploaded_file = st.file_uploader("📷 Կցել նկար...", type=["jpg", "jpeg", "png"])

st.title("💬 Չատ Հովհաննեսի հետ")

image_to_send = None
if uploaded_file:
    image_to_send = Image.open(uploaded_file)
    st.image(
        image_to_send,
        caption="Բեռնված նկարը",
        use_container_width=True,
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Գրիր քո հարցը այստեղ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history_contents = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            history_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        if image_to_send and len(history_contents) > 0:
            history_contents[-1].parts.append(image_to_send)

        # Բոլոր պահանջված մոդելները
        models_to_try = [
            "gemini-3.6-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        response_text = None
        last_error = ""

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=history_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    ),
                )
                response_text = response.text
                break
            except Exception as e:
                last_error = str(e)
                continue

        if response_text:
            st.markdown(response_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )
        else:
            st.error(f"Սխալ: {last_error}")
