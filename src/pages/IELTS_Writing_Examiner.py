import streamlit as st
from tools.llm_utils import generate_text, json_output
from tools.image_utils import ocr


def IELTS_Examiner():
    st.title("📝 IELTS Writing Examiner")

    with st.form("ielts_examiner_form"):
        input_text = st.text_area("Add your IELTS writing here to evaluate:")
        uploaded_image = st.file_uploader(
            "Or upload an image of your writing:", type=["png", "jpg", "jpeg"]
        )

        if st.form_submit_button("Evaluate"):
            if uploaded_image:
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png"
                ) as temp_file:
                    temp_file.write(
                        uploaded_image.read()
                    )  # Write the file to the temporary directory
                    image_path = temp_file.name  # Get file path
                input_text = ocr(image_path)  # Extract text from image
                st.write("### Extracted Text:")
                st.write(input_text)

            if not input_text.strip():
                st.write("Please provide text input or upload an image.")
                return

            system_prompt = "You know everything about scoring IELTS essays. You assess the given essay of the given question and provide feedback and specify mistakes and suggest corrections.\
            I will give you my question and my essay to answer that question.\
            Your output must be a JSON following this structure: {'band': the band score, 'feedback': your feedback (maximum 100 words), 'mistakes':[{'mistake': the whole sentence,'correction': a correction for that sentence]}"

            try:
                evaluation = generate_text(system_prompt, input_text)
                result = json_output(evaluation)
                st.success(f"### Score: {result['band']} / 9")
                st.write(f"### Feedback:")
                st.write(f"{result['feedback']}")
                st.write("### Mistakes:")
                for i, mistake in enumerate(result["mistakes"]):
                    st.write(f"---")
                    st.write(f"**Mistake {i+1}:** {mistake['mistake']}")
                    st.write(f"**Correction {i+1}:** {mistake['correction']}")
            except Exception as e:
                print(f"Error: {str(e)}")
                st.write(f"Try again.")
            evaluation = generate_text(system_prompt, input_text)


IELTS_Examiner()
