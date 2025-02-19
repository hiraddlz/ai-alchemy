import streamlit as st
from tools.llm_utils import generate_text, json_output


def IELTS_Examiner():
    st.title("📝 IELTS Writing Examiner")

    # Memory input
    with st.form("ielts_examiner_form"):
        input_text = st.text_area("Add text to evaluate:")
        if st.form_submit_button("Evaluate"):
            system_prompt = "You know everything about scoring IELTS essays. You assess the given essay of the given question and provide feedback and specify mistakes and suggest corrections.\
            I will give you my question and my essay to answer that question.\
            Your output must be a JSON following this structure: {'band': the band score, 'feedback': your feedback (maximum 100 words), 'mistakes':[{'mistake': the whole sentence,'correction': a correction for that sentence]}"

            try:
                evaluation = generate_text(system_prompt, input_text)
                result = json_output(evaluation)
                st.write(f"### Score: {result['band']} / 9")
                st.write(f"### Feedback:")
                st.write(f"{result['feedback']}")
                st.write("### Mistakes:")
                for i, mistake in enumerate(result["mistakes"]):
                    st.write(f"- **Mistake {i+1}:** {mistake['mistake']}")
                    st.write(f"- **Correction {i+1}:** {mistake['correction']}")
            except Exception as e:
                print(f"Error: {str(e)}")
                st.write(f"Try again.")
            evaluation = generate_text(system_prompt, input_text)




IELTS_Examiner()
