import google.generativeai as genai
import streamlit as st

st.set_page_config(page_title="Հովհաննես AI 2.0", page_icon="🤖")
st.title("🤖 Հովհաննես AI 2.0")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Խնդրում ենք ավելացնել GEMINI_API_KEY-ը Streamlit Secrets-ում:")
    st.stop()

genai.configure(api_key=api_key)

system_instruction = (
    "Քո անունը Հովհաննես է: Դու բարի, խելացի և օգտակար հայկական AI "
    "օգնական ես: Պատասխանիր հարցերին հայերեն, հարգալից և ճշգրիտ:"
)

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash", system_instruction=system_instruction
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Գրիր քո հարցը այստեղ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = model.generate_content(prompt)
        st.markdown(response.text)
        st.session_state.messages.append(
            {"role": "assistant", "content": response.text}
        )
