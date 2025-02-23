import streamlit as st
from g4f.client import Client
from tools.llm_utils import stream_content

client = Client()

st.title("📝 File Q&A")

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# File uploader
uploaded_file = st.file_uploader("Upload an article", type=("txt", "md"))

# Question input
question = st.text_input(
    "Ask something about the article",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file,
)

# Handle file upload and system message
if uploaded_file:
    article = uploaded_file.read().decode()
    
    # Only add the system message if it's not already in the chat history
    if not any(msg["role"] == "system" for msg in st.session_state.messages):
        system_prompt = (
            f"You are a helpful assistant analyzing the following article:\n\n"
            f"<article>\n{article}\n</article>\n\n"
            f"Please answer questions based only on the information provided in this article."
        )
        st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Handle question and generate response
if question and uploaded_file:
    # Add user message
    user_message = {"role": "user", "content": question}
    st.session_state.messages.append(user_message)
    
    # Generate response
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages,
        stream=True,
    )
    
    # Display answer
    st.write("### Answer")
    response = st.write_stream(stream_content(stream))
    
    # Add assistant message
    assistant_message = {"role": "assistant", "content": response}
    st.session_state.messages.append(assistant_message)
