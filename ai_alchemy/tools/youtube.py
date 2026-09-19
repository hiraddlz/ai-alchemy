"""YouTube URL parsing and transcript retrieval."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def extract_video_id(url: str) -> str | None:
    """Return the 11-character video ID from any common YouTube URL form.

    Handles ``watch?v=``, ``youtu.be/``, ``/shorts/``, ``/embed/``, ``/live/``
    and a bare video ID.
    """
    url = url.strip()
    if _VIDEO_ID.match(url):
        return url

    if "://" not in url:
        url = "https://" + url
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() not in _HOSTS:
        return None

    candidates = parse_qs(parsed.query).get("v", [])
    parts = [p for p in parsed.path.split("/") if p]
    if parsed.hostname == "youtu.be" and parts:
        candidates.append(parts[0])
    elif len(parts) >= 2 and parts[0] in {"shorts", "embed", "live", "v"}:
        candidates.append(parts[1])

    for candidate in candidates:
        if _VIDEO_ID.match(candidate):
            return candidate
    return None


def fetch_transcript(video_id: str, languages: tuple[str, ...] = ("en",)) -> str:
    """Download the transcript and join it into one block of text.

    Falls back to any available language (including auto-generated captions)
    when none of ``languages`` exist.
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=list(languages))
    except Exception:
        transcripts = api.list(video_id)
        fetched = next(iter(transcripts)).fetch()
    return " ".join(snippet.text.strip() for snippet in fetched if snippet.text.strip())
