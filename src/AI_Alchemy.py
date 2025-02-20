import streamlit as st
import os

# Predefined page configuration
PAGE_CONFIG = {
    "Conversational AI": [
        {
            "name": "Chatbot",
            "emoji": "🤖",
            "hover": "24/7 AI assistant for general inquiries and support",
            "filename": "Chatbot.py",
        }
    ],
    "IELTS Tools": [
        {
            "name": "IELTS Writing Examiner",
            "emoji": "📝",
            "hover": "Evaluate & score IELTS writing tasks with detailed feedback",
            "filename": "IELTS_Writing_Examiner.py",
        },
        # {
        #     "name": "IELTS Speaking Simulator",
        #     "emoji": "🎤",
        #     "hover": "Practice IELTS speaking tests with AI evaluation",
        #     "filename": "IELTS_Speaking_Simulator.py"
        # }
    ],
    "Writing Tools": [
        {
            "name": "Summarizer",
            "emoji": "📝",
            "hover": "Condense long texts into key points",
            "filename": "Summarizer.py",
        },
        {
            "name": "Content Repurposer",
            "emoji": "♻️",
            "hover": "Adapt content for different formats/platforms",
            "filename": "Content_Repurposer.py",
        },
        {
            "name": "Proofreader",
            "emoji": "🔍",
            "hover": "Advanced grammar and style checking",
            "filename": "Proofreader.py",
        },
    ],
    "Conversion Tools": [
        {
            "name": "Image to LaTeX Converter",
            "emoji": "📸",
            "hover": "Convert math equations from images to LaTeX",
            "filename": "Image_to_LaTeX_Converter.py",
        },
        {
            "name": "Ascii Artist",
            "emoji": "🎨",
            "hover": "Convert images to ASCII art",
            "filename": "Ascii_Artist.py",
        },
    ],
    "Language Tools": [
        {
            "name": "Translator",
            "emoji": "🌐",
            "hover": "Multi-language translation with context preservation",
            "filename": "Translator.py",
        }
    ],
    "Analysis Tools": [
        {
            "name": "File Q&A",
            "emoji": "📁",
            "hover": "Ask questions about document contents",
            "filename": "File_Q&A.py",
        },
        {
            "name": "Resume Matcher",
            "emoji": "📄",
            "hover": "Match resumes with job descriptions using AI analysis",
            "filename": "Resume_Matcher.py",
        },
    ],
}


def load_css():
    """Load CSS from root assets directory"""
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        css_path = os.path.join(root_dir, "assets", "css", "cards.css")

        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS: {str(e)}")


# Initialize session state
if "selected_page" not in st.session_state:
    st.session_state.selected_page = None


def handle_click(page_name):
    st.session_state.selected_page = f"pages/{page_name}"


st.set_page_config(layout="wide")
load_css()

st.title("AI Toolkit Suite")

for category, tools in PAGE_CONFIG.items():
    st.markdown(
        f"<div class='category-header'>{category}</div>", unsafe_allow_html=True
    )

    cols = st.columns(4)
    for idx, tool in enumerate(tools):
        with cols[idx % 4]:
            # Visible card using markdown
            st.markdown(
                f"""
                <div class='tool-card' data-hover="{tool['hover']}">
                    <div class="tool-emoji">{tool['emoji']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Invisible button for click handling
            if st.button(
                key=f"btn_{tool['filename']}",
                label=tool["name"],
                help=tool["hover"],
                on_click=handle_click,
                args=(tool["filename"],),
            ):
                pass

# Handle page navigation
if st.session_state.selected_page:
    st.switch_page(st.session_state.selected_page)
