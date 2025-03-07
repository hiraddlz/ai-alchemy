import docx2txt
import pypdfium2
import streamlit as st
from redlines import Redlines
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from tenacity import retry, stop_after_attempt, wait_exponential
from tools.llm_utils import generate_text, json_output, stream_content

# Define schemas for structured output
job_info_schema = [
    ResponseSchema(
        name="company_name", description="The name of the company or 'unknown'"
    ),
    ResponseSchema(name="job_title", description="The job title or 'unknown'"),
    ResponseSchema(name="job_location", description="The job location or 'unknown'"),
]

match_schema = [
    ResponseSchema(name="match_score", description="Match percentage (e.g., '85%')"),
    ResponseSchema(name="revised_summary", description="Revised professional summary"),
    ResponseSchema(
        name="resume_phrases_to_adjust",
        description="Dictionary of original vs improved phrases",
    ),
    ResponseSchema(name="skills_to_add", description="List of skills to add"),
    ResponseSchema(name="skills_to_remove", description="List of skills to remove"),
]

job_info_parser = StructuredOutputParser.from_response_schemas(job_info_schema)
match_parser = StructuredOutputParser.from_response_schemas(match_schema)


# Text extraction functions (unchanged)
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf = pypdfium2.PdfDocument(pdf_file)
    for i in range(len(pdf)):
        page = pdf[i]
        text += page.get_textpage().get_text_range() + "\n"
    return text


def extract_text_from_docx(docx_file):
    return docx2txt.process(docx_file)


# Job info extraction
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def extract_job_info(job_description):
    """Extract structured job info using g4f."""
    prompt_template = ChatPromptTemplate.from_template(
        """
        Extract the following information from the job description:
        1. company_name: The name of the company. Return "unknown" if not found.
        2. job_title: The job title. Return "unknown" if not found.
        3. job_location: The location of the job. Return "unknown" if not found.

        Job Description:
        {job_description}

        {format_instructions}
        """
    )
    prompt = prompt_template.format(
        job_description=job_description,
        format_instructions=job_info_parser.get_format_instructions(),
    )
    response = generate_text(prompt)
    default = {
        "company_name": "unknown",
        "job_title": "unknown",
        "job_location": "unknown",
    }
    return json_output(response, default=default)


# Resume matching
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def match_resume_to_job(resume_text, job_description):
    """Match resume to job description with structured output."""
    prompt_template = ChatPromptTemplate.from_template(
        """
        Analyze the following resume and job description. Provide:
        1. match_score (0-100%) based on keyword alignment, experience, and skills.
        2. revised_summary: Rewrite the resume's summary to match the job.
        3. resume_phrases_to_adjust: 3 phrases from the resume with improved versions.
        4. skills_to_add: Up to 5 skills from the job missing in the resume.
        5. skills_to_remove: Up to 3 irrelevant resume skills.

        Resume:
        {resume_text}
        ---
        Job Description:
        {job_description}

        {format_instructions}
        """
    )
    prompt = prompt_template.format(
        resume_text=resume_text,
        job_description=job_description,
        format_instructions=match_parser.get_format_instructions(),
    )
    response = generate_text(prompt)
    return json_output(response)


# Cover letter generation
def generate_cover_letter(resume_text, job_description):
    prompt_template = ChatPromptTemplate.from_template(
        """
        Generate a cover letter based on the resume and job description.

        Resume:
        {resume_text}
        Job Description:
        {job_description}
        """
    )
    prompt = prompt_template.format(
        resume_text=resume_text, job_description=job_description
    )
    return generate_text(prompt, stream=True)


# Interview questions generation
def generate_interview_questions(resume_text, job_description):
    prompt_template = ChatPromptTemplate.from_template(
        """
        Generate several interview questions and answers based on the resume and job description.

        Resume:
        {resume_text}
        Job Description:
        {job_description}
        """
    )
    prompt = prompt_template.format(
        resume_text=resume_text, job_description=job_description
    )
    return generate_text(prompt, stream=True)


# UI display function (unchanged)
def show_match_result(match_result):
    st.subheader("🔍 Match Analysis 📊")
    if match_result["match_score"] >= "80%":
        st.success(f"🌟 Match Score: {match_result['match_score']} 🎉")
    elif match_result["match_score"] >= "60%":
        st.warning(f"⚠️ Match Score: {match_result['match_score']} 🔄")
    else:
        st.error(f"❌ Match Score: {match_result['match_score']} 💔")

    st.markdown("### ✏️ Revised Professional Summary")
    st.code(f"{match_result['revised_summary']}", language=None, wrap_lines=True)

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


# Streamlit UI
st.set_page_config(layout="wide")
st.title("📄 Resume Matcher 🤖")
st.subheader("🔍 Match resumes with job descriptions using AI 💼")

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""

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

if st.button("Run Selected Options", use_container_width=True):
    if not (run_match or run_cover_letter or run_interview):
        st.warning("Please select at least one option.")
    elif not (st.session_state.resume_text and st.session_state.job_description):
        st.warning("Please provide both resume and job description.")
    else:
        with st.spinner("Preparing job description..."):
            st.session_state.job_info = extract_job_info(
                st.session_state.job_description
            )
        st.write("### 💼 Job Details")
        st.write(f":briefcase: **Job Title:** {st.session_state.job_info['job_title']}")
        st.write(f":office: **Company:** {st.session_state.job_info['company_name']}")
        st.write(
            f":round_pushpin: **Location:** {st.session_state.job_info['job_location']}"
        )

        if run_match:
            with st.spinner("Evaluating resume..."):
                st.session_state.result = match_resume_to_job(
                    st.session_state.resume_text, st.session_state.job_description
                )
            if st.session_state.result:
                show_match_result(st.session_state.result)
            else:
                st.info("Failed to analyze match. Please check inputs and try again.")

            st.download_button(
                label="Applied -> [Download Job Description]",
                data=st.session_state.job_description,
                file_name=f"job_description-{st.session_state.job_info['company_name']}-{st.session_state.job_info['job_title']}-{st.session_state.job_info['job_location']}.txt",
                mime="text/plain",
            )

        if run_cover_letter:
            st.write("#### Generated Cover Letter:")
            with st.spinner("Generating Cover letter..."):
                cover_letter = st.write_stream(
                    stream_content(
                        generate_cover_letter(
                            st.session_state.resume_text,
                            st.session_state.job_description,
                        )
                    )
                )
                if isinstance(cover_letter, str) and cover_letter.startswith("Error:"):
                    st.error(cover_letter)
                else:
                    st.session_state.cover_letter = cover_letter
                    st.download_button(
                        label="Download Cover Letter",
                        data=st.session_state.cover_letter,
                        file_name=f"cover_letter-{st.session_state.job_info['company_name']}-{st.session_state.job_info['job_title']}-{st.session_state.job_info['job_location']}.txt",
                        mime="text/plain",
                    )

        if run_interview:
            st.write("#### Generated Interview Questions:")
            with st.spinner("Generating Interview Questions..."):
                interview_questions = st.write_stream(
                    stream_content(
                        generate_interview_questions(
                            st.session_state.resume_text,
                            st.session_state.job_description,
                        )
                    )
                )
                if isinstance(
                    interview_questions, str
                ) and interview_questions.startswith("Error:"):
                    st.error(interview_questions)
                else:
                    st.session_state.interview_questions = interview_questions
                    st.download_button(
                        label="Download Interview Questions",
                        data=st.session_state.interview_questions,
                        file_name="interview_questions.txt",
                        mime="text/plain",
                    )
