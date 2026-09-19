<div align="center">

<img src="assets/logo.svg" alt="AI Alchemy" width="260">

**Twelve AI-powered tools in one Streamlit app. Works out of the box on free models - or bring any LLM provider.**

[![CI](https://github.com/hiraddlz/ai-alchemy/actions/workflows/ci.yml/badge.svg)](https://github.com/hiraddlz/ai-alchemy/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B)](https://streamlit.io)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[**Live demo**](https://ai-alchemy.streamlit.app/) · [Tools](#tools) · [Quick start](#quick-start) · [Architecture](#architecture) · [Development](#development)

<img src="docs/screenshots/home.png" alt="AI Alchemy home page" width="900">

</div>

## What it is

AI Alchemy is a single, self-hostable web app that packages everyday LLM workflows - proofreading,
summarising, document Q&A, resume tailoring, IELTS grading, translation, equation OCR - behind a
clean UI. It **works with no API key** - out of the box it routes to free public models
(DeepSeek, GLM, Qwen, Nemotron, ...) - and it is **provider-agnostic**: switch a dropdown to run the
same tools on OpenAI, Google Gemini, Groq, DeepSeek, Hugging Face, OpenRouter, a local Ollama server
or any OpenAI-compatible endpoint. Keys live only in your browser session.

Highlights:

- **Free by default.** A keyless backend (via [g4f](https://github.com/xtekky/gpt4free)) with a
  curated fallback chain of endpoints that work right now, incl. a vision model. Best-effort by
  nature - so every screen also lets you drop in your own key for guaranteed quality.

- **Structured outputs, not just chat.** Grading and matching tools request JSON, validate it, and
  render it as metrics, badges, tables and word-level diffs.
- **Vision where it helps.** Equation-to-LaTeX and handwriting OCR use the model's vision input
  instead of shipping a 2 GB `torch` + `pix2tex` stack.
- **Streaming everywhere.** Long outputs render token by token.
- **Tested.** Pure helpers are unit-tested; every page is exercised end-to-end with Streamlit's
  `AppTest` against a fake OpenAI-compatible server (no network, no keys).
- **Shared-key mode.** Prefer a reliable provider for visitors? Deploy with one free-tier key and
  the app locks the model and enforces per-session, per-minute and prompt-size caps so nobody can
  drain it.
- **Deployable in one command** - Streamlit Cloud, Docker, or `streamlit run app.py`.

## Tools

| Tool | What it does |
| --- | --- |
| 💬 **Chatbot** | Streaming chat with switchable personas and full history |
| 📁 **File Q&A** | Upload PDF / DOCX / TXT / MD and ask grounded questions; suggested prompts |
| 🎬 **YouTube Summarizer** | Transcript → TL;DR + key points + quotes, then chat about the video |
| 📄 **Resume Matcher** | 0-100 fit score, strengths, gaps, keyword coverage, rewritten summary, phrase-level diffs, cover letter and interview prep |
| 🎓 **IELTS Writing Examiner** | Band per criterion, next-band advice, corrections with diffs, vocabulary upgrades; accepts a photo of handwriting |
| 🔍 **Proofreader** | Fix / tighten / formalise, word-level diff, and an explanation of each change |
| 🧠 **Summarizer** | Bullets, paragraph, TL;DR or executive brief; text or document input; output language |
| ♻️ **Content Repurposer** | One source → LinkedIn post, X thread, Instagram caption, newsletter, blog intro |
| 🌐 **Translator** | 20+ languages, register control, right-to-left rendering for Persian/Arabic/Urdu/Hebrew |
| 🧮 **Image to LaTeX** | Photograph an equation, get compilable LaTeX rendered live |
| 🎨 **ASCII Artist** | Image → ASCII with tunable width, charset, brightness and contrast (no key needed) |
| 🖼️ **Background Remover** | Local U²-Net background removal via `rembg` (no key needed) |

<div align="center">
<img src="docs/screenshots/ielts_result.png" alt="IELTS examiner result" width="900">
<br><sup>IELTS Writing Examiner: structured JSON from the model rendered as per-criterion scores and highlighted corrections.</sup>
</div>

## Quick start

```bash
git clone https://github.com/hiraddlz/ai-alchemy.git
cd ai-alchemy
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[images]"        # drop [images] to skip the background remover
streamlit run app.py
```

Open http://localhost:8501 - that's it. With nothing configured the app starts on the
**Free (no key needed)** provider. Pick a tool and go.

### Model providers

| Provider | Key | Notes |
| --- | --- | --- |
| **Free (no key needed)** - default | none | Public endpoints via g4f: DeepSeek V4 Flash, GLM 5.2, Qwen 3.8, Nemotron 3 Ultra, Ling (vision), or *Auto*. Best-effort speed/availability; falls back across endpoints automatically. |
| Google Gemini | free tier | 1500 req/day, 1M tokens/min, vision - recommended as a shared host key |
| Groq | free tier | very fast; ~6k tokens/min |
| OpenRouter | free tier | `:free` models |
| OpenAI, DeepSeek, Hugging Face | paid / token | full model catalogues |
| Ollama | none | anything you run locally |
| Custom | as needed | any OpenAI-compatible URL (vLLM, LM Studio, ...) |

Change provider in **⚙️ Model settings** in the sidebar; keys never leave the browser session.

### Shared-key mode (optional, for a public deployment)

If you would rather your visitors use a specific provider than the public endpoints, put **one
free-tier key** in `.streamlit/secrets.toml` (locally) or in your Streamlit Cloud app's *Secrets*
box, based on [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example):

```toml
LLM_PROVIDER = "gemini"          # free tier: 1500 req/day, 1M tokens/min, vision
LLM_API_KEY  = "AIza..."         # https://aistudio.google.com/apikey
LLM_MODEL    = "gemini-2.0-flash"
```

The app then runs on that key for everyone, with guards:

| Guard | Default | Purpose |
| --- | --- | --- |
| `DEMO_SESSION_LIMIT` | 25 calls | one visitor cannot drain the daily quota |
| `DEMO_RPM` | 12 / min | stays under the provider's rate limit across all visitors |
| `DEMO_MAX_WORDS` | 15,000 | keeps huge documents off the shared key |
| model lock | - | the host key only ever runs `LLM_MODEL` |

Anyone can still paste their own key in the sidebar to lift the caps or switch provider.

All settings, as secrets or environment variables:

| Variable | Meaning | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | `free`, `openai`, `gemini`, `groq`, `openrouter`, `deepseek`, `huggingface`, `ollama`, `custom` | `free` (or `openai` if `g4f` is not installed) |
| `LLM_API_KEY` | API key (`OPENAI_API_KEY` is also honoured for OpenAI) | - |
| `LLM_MODEL` | Model name | provider default |
| `LLM_BASE_URL` | Endpoint URL, only needed for `custom` | provider preset |
| `DEMO_SESSION_LIMIT` / `DEMO_RPM` / `DEMO_MAX_WORDS` | Shared-mode caps | 25 / 12 / 15000 |

### Docker

```bash
docker build -t ai-alchemy .
docker run -p 8501:8501 -e LLM_PROVIDER=groq -e LLM_API_KEY=gsk_... ai-alchemy
```

### Streamlit Community Cloud

Point a new app at `app.py` and deploy - no secrets needed for the free provider. To run visitors
on a shared key instead, paste the contents of `secrets.toml.example` (with your key) into the app's
*Secrets* box. `requirements.txt` is kept in sync with `pyproject.toml` for this.

## Architecture

```
app.py                     entry point: page config, st.navigation, sidebar settings
ai_alchemy/
├── config.py              provider presets + settings resolution (visitor key > host key)
├── llm.py                 LLMClient: chat / stream / JSON / vision, same API for every backend
├── free_backend.py        keyless backend: OpenAI-client look-alike over g4f with provider fallback
├── quota.py               shared-mode guards: session budget, sliding-window RPM, prompt size
├── registry.py            single list of tools that drives navigation and the home page
├── ui.py                  shared widgets: settings sidebar, require_client(), streaming helpers
├── tools/                 pure, framework-free helpers (unit tested)
│   ├── ascii_art.py       image → ASCII
│   ├── documents.py       PDF / DOCX / TXT extraction, truncation
│   ├── youtube.py         URL parsing (watch, youtu.be, shorts, embed, live) + transcripts
│   └── diff.py            word-level redline diffs
└── pages/                 one module per tool, each exposing render()
tests/
├── conftest.py            FakeOpenAIServer: canned JSON + SSE streaming replies
├── test_tools.py          unit tests for helpers
├── test_llm.py            settings resolution, JSON parsing, client error mapping
├── test_quota.py          rate limiter and prompt sizing
└── test_pages.py          AppTest end-to-end runs of every page
```

Design notes:

- **One client, many providers.** `LLMClient` wraps the official `openai` SDK with a `base_url`;
  the free provider swaps in a `FreeBackend` that exposes the same `chat.completions.create`
  surface. Provider quirks (JSON mode, key requirements) live in a preset table, not in the tools.
- **Free mode is honest about itself.** Public endpoints come and go, so the backend tries a short
  curated chain (KiloCode → HuggingSpace → Cohere), primes streams before committing to a provider,
  and turns total failure into a one-line message with a way out (pick another model / add a key).
- **Structured output is defensive.** `complete_json()` asks for JSON mode where supported, strips
  code fences, trims prose, repairs trailing commas and retries once before surfacing an error.
- **Shared mode is opt-in by deployment.** A key in secrets makes the app free for visitors; the
  guards in `quota.py` are a `before_request` hook on the client, so tools never know about them.
- **Errors are user-facing.** SDK exceptions are mapped to plain-language messages ("rejected the
  API key", "model not found", "rate limit") and rendered inline instead of crashing the page.
- **Pages are thin.** Prompts and layout live in the page; anything testable without Streamlit lives
  in `ai_alchemy/tools`.

## Development

```bash
pip install -e ".[dev,images]"
pre-commit install          # ruff lint + format on commit
pytest                      # ~80 tests, no network required
ruff check . && ruff format --check .
```

CI runs lint, the test matrix (3.10 / 3.12 / 3.13) and a Docker build on every push and PR.

### Adding a tool

1. Create `ai_alchemy/pages/<slug>.py` with a `render()` function. Use `require_client()` for the
   model and `stream_to_ui()` / `complete_json()` for output.
2. Add a `Tool(...)` entry to `ai_alchemy/registry.py` - navigation and the home page update
   automatically.
3. Put any non-UI logic in `ai_alchemy/tools/` and add a test.

## License

[MIT](LICENSE) © Hirad Dolatzadeh
