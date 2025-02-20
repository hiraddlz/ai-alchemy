# AI Alchemy

**AI Alchemy** is a free, open-source multi-tool AI application built with Python. It provides a simple, user-friendly interface to access various AI-powered tools such as text and image Generator.

> **Live Demo:** [Access AI Alchemy for Free](https://ai-alchemy.streamlit.app/)

## Features

- **Modular Design:** Each tool is implemented in its own module (file) for easy maintenance and scalability.
- **User-Friendly UI:** Built with Streamlit for a clean and intuitive interface.
- **Free & Open-Source:** Available on GitHub with contributions welcome from the community.
- **Easy Deployment:** Ready to deploy on Streamlit Cloud or any hosting platform that supports Python apps.

## Available Tools
Below is a checklist of the AI-powered tools available in **AI Alchemy**:

- [x] **Summarizer**  
  Condense long articles, reports, or stories into concise summaries.

- [x] **Content Reproducer**  
  Adapt and rework content for platforms like LinkedIn and Twitter, ensuring your message resonates with your audience.

- [x] **IELTS Writing Examiner**  
  Evaluate IELTS writing samples and provide detailed feedback to help improve your writing skills.

- [x] **Proofreader**  
  Detect and correct grammatical, punctuation, and spelling errors in your text.

- [x] **Translator**  
  Translate text between multiple languages using advanced AI models.

- [x] **ASCII Artist**  
  Convert images into creative ASCII art for fun and unique visual representations.

- [x] **File Q&A**  
  Ask questions about the contents of files (e.g., PDFs, text files) and receive detailed, context-aware answers.

- [x] **Resume Matcher**  
  Match resumes with job descriptions using AI.

- [ ] **LaTeX Image Converter** *(Under Development)*  
  Transform LaTeX images code for academic and professional writing.

## Getting Started

### Prerequisites

- Python 3.7 or higher

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/hiraddlz/ai-alchemy.git
   cd ai-alchemy
   ```

2. **Create and activate a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Running the App Locally

1. **Set your OpenAI API key:**

   ```bash
   export OPENAI_API_KEY="your-openai-api-key"  # For Windows: set OPENAI_API_KEY=your-openai-api-key
   ```

2. **Run the Streamlit app:**

   ```bash
   streamlit run app.py
   ```

3. **Open your browser:**  
   The app will typically be accessible at [http://localhost:8501](http://localhost:8501).

<!-- ## Project Structure

```
ai-hub/
├── app.py                  # Main Streamlit application file
├── requirements.txt        # Project dependencies
└── tools/                  # Directory for individual tool modules
    ├── __init__.py         # Package marker for the tools folder
    ├── summarizer.py       # Module for the Story Summarizer tool
    └── generator.py        # Module for the Story Generator tool
``` -->


## Contributing

Contributions are welcome! If you have suggestions, improvements, or new tool ideas, please:

1. Fork the repository.
2. Create your feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature/bug fix"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request.


Feel free to reach out with any suggestions or contributions. I'm happy to collaborate and improve AI Hub further!
