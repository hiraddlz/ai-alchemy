import streamlit as st
from g4f.client import Client

client = Client()

def generate_summary(story_text: str) -> str:
    # Define the prompt for summarization
    prompt = f"Summarize the following story in one paragraph:\n\n{story_text}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def summarizer():
    st.title("🧠 AI Summarizer")
    
    # Memory input
    with st.form("summary_form"):
        input_text = st.text_area("Add text to summarize:")
        if st.form_submit_button("Summarize"):
            summary = generate_summary(input_text)
            st.write("### Summary:")
            st.write(summary)


summarizer()