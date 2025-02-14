import streamlit as st

from tools.content_repurposer import content_repurposer
from tools.summarizer import summarizer


def main():
    st.set_page_config(page_title="AI Tools Suite", layout="wide")
    
    # Load custom CSS
    with open("assets/css/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Sidebar Navigation
    st.sidebar.title("AI Tools Suite")
    tool_choice = st.sidebar.radio(
        "Choose Tool:",
        ("Content Repurposer", "Summarizer")
    )

    # Tool Routing
    if tool_choice == "Content Repurposer":
        content_repurposer()
    elif tool_choice == "Summarizer":
        summarizer()

if __name__ == "__main__":
    main()