"""Single source of truth for the tools shown in navigation and on the home page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    slug: str  # URL path and module name under ai_alchemy.pages
    title: str
    icon: str
    category: str
    description: str
    needs_llm: bool = True


TOOLS: tuple[Tool, ...] = (
    Tool(
        "chat",
        "Chatbot",
        "💬",
        "Conversation",
        "Streaming chat with switchable personas and full history.",
    ),
    Tool(
        "file_qa",
        "File Q&A",
        "📁",
        "Documents",
        "Upload a PDF, DOCX or text file and ask questions grounded in its content.",
    ),
    Tool(
        "youtube",
        "YouTube Summarizer",
        "🎬",
        "Documents",
        "Pull a video transcript, summarise it and chat about what was said.",
    ),
    Tool(
        "resume_matcher",
        "Resume Matcher",
        "📄",
        "Career",
        "Score a resume against a job posting, then draft a cover letter and interview prep.",
    ),
    Tool(
        "ielts",
        "IELTS Writing Examiner",
        "🎓",
        "Writing",
        "Band scores per criterion, feedback and highlighted corrections.",
    ),
    Tool(
        "proofreader",
        "Proofreader",
        "🔍",
        "Writing",
        "Fix grammar and spelling, see a word-level diff and learn why.",
    ),
    Tool(
        "summarizer",
        "Summarizer",
        "🧠",
        "Writing",
        "Condense long text or documents into bullets, a paragraph or a TL;DR.",
    ),
    Tool(
        "repurposer",
        "Content Repurposer",
        "♻️",
        "Writing",
        "Turn one piece of content into posts for LinkedIn, X, Instagram or email.",
    ),
    Tool(
        "translator",
        "Translator",
        "🌐",
        "Language",
        "Translate between 20+ languages with tone control and RTL support.",
    ),
    Tool(
        "image_to_latex",
        "Image to LaTeX",
        "🧮",
        "Vision",
        "Photograph an equation and get compilable LaTeX, rendered live.",
    ),
    Tool(
        "ascii_artist",
        "ASCII Artist",
        "🎨",
        "Images",
        "Convert any picture into ASCII art with tunable detail and contrast.",
        needs_llm=False,
    ),
    Tool(
        "background_remover",
        "Background Remover",
        "🖼️",
        "Images",
        "Cut the background out of a photo locally with an ONNX model.",
        needs_llm=False,
    ),
)

CATEGORY_ORDER = ("Conversation", "Documents", "Career", "Writing", "Language", "Vision", "Images")


def tools_by_category() -> dict[str, list[Tool]]:
    grouped: dict[str, list[Tool]] = {category: [] for category in CATEGORY_ORDER}
    for tool in TOOLS:
        grouped.setdefault(tool.category, []).append(tool)
    return {category: tools for category, tools in grouped.items() if tools}
