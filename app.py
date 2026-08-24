import google.generativeai as genai
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Հովհաննես AI 2.0", page_icon="🤖")
st.title("🤖 Հովհաննես AI 2.0")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

genai.configure(api_key=api_key)

system_instruction = (
    "Քո անունը Հովհաննես է: Քեզ ստեղծել է Արարատ Սահակյանը: "
    "Դու քրիստոնյա ես և քո պատասխաններում առաջնորդվում ես Աստվածաշնչի "
    "սկզբունքներով, սիրով, բարությամբ, ազնվությամբ և ճշմարտությամբ: "
    "Դու փայլուն տիրապետում ես բազմաթիվ լեզուների (հայերեն, անգլերեն, ռուսերեն "
    "և այլն) և կարող ես ազատ թարգմանել ու հաղորդակցվել դրանցով: "
    "Բացի դպրոցական բոլոր առարկաներից, դու ունես խորը գիտելիքներ տեխնոլոգիաների, "
    "ծրագրավորման, փիլիսոփայության, արվեստի, տիեզերքի և գիտության տարբեր բնագավառներում: "
    "Եթե օգտատերը նկար է ուղարկում, մանրամասն վերլուծիր այն և պատասխանիր հարցերին:"
)

# Օգտագործում ենք ստանդարտ stable մոդելը
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", system_instruction=system_instruction
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Նկարի բեռնման կոճակ
uploaded_file = st.file_uploader("Կցել նկար...", type=["jpg", "jpeg", "png"])
image_to_send = None

if uploaded_file:
    image_to_send = Image.open(uploaded_file)
    st.image(image_to_send, caption="Բեռնված նկարը", use_column_width=True)

# Զրույցի պատմությունը
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Հարցի մուտքագրում
if prompt := st.chat_input("Գրիր քո հարցը այստեղ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            if image_to_send:
                response = model.generate_content([prompt, image_to_send])
            else:
                response = model.generate_content(prompt)

            st.markdown(response.text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response.text}
            )
        except Exception as e:
            st.error(f"Սխալ տեղի ունեցավ: {e}")
