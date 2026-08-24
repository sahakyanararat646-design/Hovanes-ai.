import google.generativeai as genai
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Հովհաննես AI 2.0", page_icon="🤖", layout="wide"
)

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

genai.configure(api_key=api_key)

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

# Gemini 2.5 Flash
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction
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
        inputs = [prompt]
        if image_to_send:
            inputs.append(image_to_send)

        try:
            response = model.generate_content(inputs)
            response_text = response.text
        except Exception as e:
            response_text = f"Սխալ: {str(e)}"

        st.markdown(response_text)
        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )
