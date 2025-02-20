import docx2txt
import pypdfium2
import streamlit as st
from redlines import Redlines

from tools.llm_utils import generate_text, json_output


def extract_text_from_pdf(pdf_file):
    text = ""
    pdf = pypdfium2.PdfDocument(pdf_file)
    for i in range(len(pdf)):
        page = pdf[i]
        text += page.get_textpage().get_text_range() + "\n"
    return text


def extract_text_from_docx(docx_file):
    return docx2txt.process(docx_file)


def match_resume_to_job(resume_text, job_description):
    system_prompt = """
Analyze the following resume and job description. Return a JSON dictionary with:
1. match_score (0-100%) based on keyword alignment, experience relevance, and skill overlap.
2. revised_summary: Rewrite the resume's professional summary to better match the job's priorities. If there is no professional summary, write a new one.
3. resume_phrases_to_adjust: List 3 specific sentences/phrases from the resume (quote exactly) with improved versions that better align with the job description.
4. skills_to_add: List up to 5 key skills/terms from the job description missing from the resume.
5. skills_to_remove: List up to 3 resume skills irrelevant to this job.
Format strictly as:
```json
{  
  "match_score": "X%",  
  "revised_summary": "...",  
  "resume_phrases_to_adjust": {  
    "Original Phrase 1": "Improved Version 1",  
    "Original Phrase 2": "Improved Version 2",  
    "Original Phrase 3": "Improved Version 3"  
  },  
  "skills_to_add": ["skill1", "skill2", ...],  
  "skills_to_remove": ["skillA", "skillB", ...]  
}  
```

"""
    user_prompt = f"""
Resume:
{resume_text}
Job Description:
{job_description}
"""
    response = json_output(generate_text(system_prompt, user_prompt))
    return response


# Streamlit UI
st.set_page_config(layout="wide")
st.title("📄Resume Matcher")
st.subheader("Match resumes with job descriptions using AI analysis")

col1, col2 = st.columns(2)

with col1:
    st.header("Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    resume_text = ""

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf"):
            resume_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            resume_text = extract_text_from_docx(uploaded_file)

    # Manual resume input
    # resume_text_manual = st.text_area("Or write your resume manually:", height=300)
    # if resume_text_manual:
    #     resume_text = resume_text_manual

with col2:
    st.header("Job Description")
    job_description = st.text_area("Paste the job description here:", height=400)


if st.button(
    "Match", help="Analyze the resume and job description", use_container_width=True
):
    if resume_text and job_description:
        result = match_resume_to_job(resume_text, job_description)
        if result["match_score"] >= "80%":
            st.success(
                f"Match Score: {result['match_score']} \n    🎉Perfect match! 🎉"
            )
        else:
            st.warning(f"Match Score: {result['match_score']}")

        st.write("### Revised Professional Summary:")
        st.write(result["revised_summary"])
        st.write("### Phrases to Adjust:")
        for original, improved in result["resume_phrases_to_adjust"].items():
            diff = Redlines(original, improved)
            st.markdown(f"- {diff.output_markdown}", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.write("### Skills to Add:")
            for skill in result["skills_to_add"]:
                st.write(f"- :green[{skill}]")
        with col2:
            st.write("### Skills to Remove:")
            for skill in result["skills_to_remove"]:
                st.write(f"- :red[{skill}]")

    else:
        st.warning("Please provide both resume and job description.")
