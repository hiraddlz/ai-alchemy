import tempfile

import streamlit as st
from redlines import Redlines  # Import Redlines

from tools.image_utils import ocr
from tools.llm_utils import LLMClient

# Initialize the LLM client
llm_client = LLMClient()


def ielts_examiner(ielts_writing, max_attempts=3):
    system_prompt = """You are an expert IELTS writing examiner. You assess the given essay and provide feedback, identify mistakes, and suggest corrections.
                Your output must be a JSON following this structure:
                Format strictly as:
                ```json
                {
                    'band': the band score (e.g., 7.0, 8.5),
                    'feedback': your feedback (maximum 100 words),
                    'mistakes': [{'mistake': the whole sentence, 'correction': a correction for that sentence}]
                }```
                """
    user_prompt = f"""
ielts_writing:\n
{ielts_writing}
"""
    for attempt in range(max_attempts):
        try:
            return llm_client.json_output(llm_client.generate_text(system_prompt, user_prompt))
        except Exception as e:
            # If this is the last attempt, return None
            if attempt == max_attempts - 1:
                return None


def show_ielts_result(result):
    st.success(f"🎉 Score: {result['band']} / 9")
    st.subheader("📝 Feedback:")
    st.write(result["feedback"])
    st.subheader("⚠️ Mistakes and Corrections:")
    for i, mistake in enumerate(result["mistakes"]):
        st.markdown("---")
        st.write(f"**Mistake {i+1}:** {mistake['mistake']}")
        st.write(f"**Correction {i+1}:** {mistake['correction']}")
        # Generate and display the diff
        with st.expander(f"## 🔍 See Changes Highlighted (Mistake {i+1})"):
            diff = Redlines(mistake["mistake"], mistake["correction"])
            st.markdown(diff.output_markdown, unsafe_allow_html=True)


def main():
    """IELTS Writing Examiner App."""

    st.title("📝 IELTS Writing Examiner 🎓")
    st.write("✨ Get AI-powered feedback on your IELTS writing. ✨")

    with st.form("ielts_examiner_form"):
        input_text = st.text_area(
            "✍️ Paste your IELTS writing here to evaluate:", height=250
        )
        uploaded_image = st.file_uploader(
            "📷 Or upload an image of your writing:", type=["png", "jpg", "jpeg"]
        )
        submitted = st.form_submit_button("🚀 Evaluate My Writing")

        if submitted:
            if uploaded_image:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png"
                ) as temp_file:
                    temp_file.write(uploaded_image.read())
                    image_path = temp_file.name
                input_text = ocr(image_path)
                st.subheader("📝 Extracted Text:")
                st.write(input_text)

            if not input_text.strip():
                st.warning("⚠️ Please provide text input or upload an image. ⚠️")
                return

            with st.spinner("🔄 Evaluating..."):

                try:
                    result = ielts_examiner(input_text)
                    show_ielts_result(result)
                except Exception as e:
                    print(f"Error: {str(e)}")
                    st.error("An error occurred during evaluation. Please try again.")


if __name__ == "__main__":
    main()
