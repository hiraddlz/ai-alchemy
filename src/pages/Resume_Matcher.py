import docx2txt
import pypdfium2
import streamlit as st
from redlines import Redlines

from tools.llm_utils import generate_text, json_output, stream_content


def extract_text_from_pdf(pdf_file):
    text = ""
    pdf = pypdfium2.PdfDocument(pdf_file)
    for i in range(len(pdf)):
        page = pdf[i]
        text += page.get_textpage().get_text_range() + "\n"
    return text


def extract_text_from_docx(docx_file):
    return docx2txt.process(docx_file)


def extract_job_info(job_description, max_attempts=3):
    """Extract company name, job title, and location from the job description."""
    system_prompt = """
Extract the following information from the job description. Return a JSON dictionary with:
1. company_name: The name of the company. Return "unknown" if not found.
2. job_title: The job title. Return "unknown" if not found.
3. job_location: The location of the job. Return "unknown" if not found.
Format strictly as:
```json
{
    "company_name": "XYZ",
    "job_title": "Job Title",
    "job_location": "City, State"
}
```
"""
    user_prompt = f"""
Job Description:\n
{job_description}
"""

    # Initialize default response in case all attempts fail
    default_response = {
        "company_name": "unknown",
        "job_title": "unknown",
        "job_location": "unknown",
    }

    # Try up to 3 times to get a valid JSON response
    for attempt in range(max_attempts):
        try:
            response = json_output(generate_text(system_prompt, user_prompt))

            # Ensure all required fields exist, replace with "unknown" if missing or empty
            validated_response = default_response.copy()
            for key in default_response:
                if (
                    key in response
                    and response[key]
                    and response[key].strip().lower() != "unknown"
                ):
                    validated_response[key] = response[key]

            return validated_response

        except Exception as e:
            # If this is the last attempt, return the default response
            if attempt == max_attempts - 1:
                return default_response
            # Otherwise, continue to the next attempt

    # This should never be reached, but included for completeness
    return default_response


def match_resume_to_job(resume_text, job_description, max_attempts=3):
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
  "skills_to_remove": ["skillA", "skillB", ...],
}  
```

"""
    user_prompt = f"""
Resume:
{resume_text}
---
Job Description:
{job_description}
"""
    for attempt in range(max_attempts):
        try:
            return json_output(generate_text(system_prompt, user_prompt))
        except Exception as e:
            # If this is the last attempt, return None
            if attempt == max_attempts - 1:
                return None


def show_match_result(match_result):
    st.subheader("🔍 Match Analysis 📊")

    if match_result["match_score"] >= "80%":
        st.success(f"🌟 Match Score: {match_result['match_score']} 🎉")
    elif match_result["match_score"] >= "60%":
        st.warning(f"⚠️ Match Score: {match_result['match_score']} 🔄")
    else:
        st.error(f"❌ Match Score: {match_result['match_score']} 💔")

    st.markdown("### ✏️ Revised Professional Summary")
    st.write(f"📝 {match_result['revised_summary']}")

    st.markdown("### 🔄 Phrases to Improve")
    for orig, improved in match_result["resume_phrases_to_adjust"].items():
        diff = Redlines(orig, improved)
        st.markdown(diff.output_markdown, unsafe_allow_html=True)

    cols = st.columns(2)
    with cols[0]:
        st.markdown("### 🌱 Skills to Add")
        for skill in match_result["skills_to_add"]:
            st.markdown(f"- ✅ :green[{skill}]")
    with cols[1]:
        st.markdown("### 🗑️ Skills to Remove")
        for skill in match_result["skills_to_remove"]:
            st.markdown(f"- ❌ :red[{skill}]")


def generate_cover_letter(resume_text, job_description):
    system_prompt = """Generate a cover letter based on the resume and job description. Return the cover letter as a string."""
    user_prompt = f"""Generate a cover letter.\n
Resume:\n
{resume_text}
Job Description:\n
{job_description}"""
    return generate_text(system_prompt, user_prompt, stream=True)


def generate_interview_questions(resume_text, job_description):
    system_prompt = """Generate several interview questions and answers based on the resume and job description. Return the questions and answers as a string."""
    user_prompt = f"""Generate several interview questions and answers.\n
Resume:\n
{resume_text}
Job Description:\n
{job_description}"""
    return generate_text(system_prompt, user_prompt, stream=True)


# Initialize session state variables if they don't exist
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""


# Streamlit UI
st.set_page_config(layout="wide")
st.title("📄 Resume Matcher 🤖")
st.subheader("🔍 Match resumes with job descriptions using AI 💼")

# Initialize session state
if "generated" not in st.session_state:
    st.session_state.generated = {
        "cover_letter": False,
        "interview_questions": False,
        "match": False,
    }

# File upload and job description input
col1, col2 = st.columns(2)
with col1:
    st.header("Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf"):
            st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            st.session_state.resume_text = extract_text_from_docx(uploaded_file)

with col2:
    st.header("Job Description")
    job_desc_input = st.text_area("Paste the job description here:", height=400)
    st.session_state.job_description = job_desc_input

# Generation controls
st.subheader("🚀 Generation Options")
col1, col2, col3 = st.columns(3)
with col1:
    run_match = st.checkbox(
        "🔍 Analyze Match", help="Analyze the resume and job description", value=True
    )
with col2:
    run_cover_letter = st.checkbox(
        "✉️ Generate Cover Letter",
        help="Create a tailored cover letter based on the resume and job description",
    )
with col3:
    run_interview = st.checkbox(
        "🎤 Interview Prep", help="Generate potential interview questions and answers"
    )

# Add a button to run the selected functions
if st.button("Run Selected Options", use_container_width=True):
    if not (run_match or run_cover_letter or run_interview):
        st.warning("Please select at least one option.")
    elif not (st.session_state.resume_text and st.session_state.job_description):
        st.warning("Please provide both resume and job description.")
    else:
        # Run the match function if selected
        with st.spinner("Preparing job description..."):
            st.session_state.job_info = extract_job_info(
                st.session_state.job_description
            )
        # Write the job info results
        st.write("### 💼 Job Details")
        st.write(f":briefcase: **Job Title:** {st.session_state.job_info['job_title']}")
        st.write(f":office: **Company:** {st.session_state.job_info['company_name']}")
        st.write(
            f":round_pushpin: **Location:** {st.session_state.job_info['job_location']}"
        )

        if run_match:
            try:
                with st.spinner("Evaluating resume..."):
                    st.session_state.result = match_resume_to_job(
                        st.session_state.resume_text, st.session_state.job_description
                    )
                show_match_result(st.session_state.result)
            except Exception as e:
                print(f"An error occurred: {e}")
                st.info(
                    "Please try again and make sure the resume and job description are in the correct format."
                )

            st.download_button(
                label="Applied -> [Download Job Description]",
                data=st.session_state.job_description,
                file_name=f"job_description-{st.session_state.job_info['company_name']}-{st.session_state.job_info['job_title']}-{st.session_state.job_info['job_location']}.txt",
                mime="text/plain",
            )

        # Run the cover letter function if selected
        if run_cover_letter:
            try:
                st.write("#### Generated Cover Letter:")
                with st.spinner("Generating Cover letter..."):
                    st.session_state.cover_letter = st.write_stream(
                        stream_content(
                            generate_cover_letter(
                                st.session_state.resume_text,
                                st.session_state.job_description,
                            )
                        )
                    )
            except Exception as e:
                print(f"An error occurred: {e}")
                st.info(
                    "Please try again and make sure the resume and job description are in the correct format."
                )

            st.download_button(
                label="Download Cover Letter",
                data=st.session_state.cover_letter,
                file_name=f"cover_letter-{st.session_state.job_info['company_name']}-{st.session_state.job_info['job_title']}-{st.session_state.job_info['job_location']}.txt",
                mime="text/plain",
            )

        # Run the interview questions function if selected
        if run_interview:
            st.write("#### Generated Interview Questions:")
            interview_questions = st.write_stream(
                stream_content(
                    generate_interview_questions(
                        st.session_state.resume_text, st.session_state.job_description
                    )
                )
            )
            st.download_button(
                label="Download Interview Questions",
                data=interview_questions,
                file_name="interview_questions.txt",
                mime="text/plain",
            )
