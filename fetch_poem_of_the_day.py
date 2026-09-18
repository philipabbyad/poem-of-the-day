#!/usr/bin/env python3
"""Downloads the Poetry Foundation "Poem of the Day" as a plain text file. See README.md."""

import html
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

FEED_URL = "https://www.poetryfoundation.org/rss/poemoftheday"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}encoded"

# Where poems get saved. Change this if you want a different folder.
OUTPUT_DIR = Path.home() / "poems" / "poem-of-the-day"

# Retry knobs for the catch-up run that fires right after a scheduled wake,
# when the network may not have reconnected yet.
FETCH_RETRIES = 5
FETCH_RETRY_DELAY_SECONDS = 15


def fetch_feed(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "poem-of-day-script/1.0"})
    last_error: Exception | None = None
    for attempt in range(1, FETCH_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except (urllib.error.URLError, OSError) as exc:
            last_error = exc
            if attempt < FETCH_RETRIES:
                time.sleep(FETCH_RETRY_DELAY_SECONDS)
    raise last_error


def html_to_text(raw_html: str) -> str:
    """Turn the feed's HTML poem body into readable plain text."""
    # Line breaks first, so we don't lose them when tags are stripped.
    # (the feed often follows a <br> with a literal newline - collapse both to one)
    text = re.sub(r"<br\s*/?>\s*\n?", "\n", raw_html)
    text = re.sub(r"</p>", "\n\n", text)
    # Decode entities before matching "Editor's Note" - the apostrophe may arrive
    # as a numeric/named entity (e.g. &#8217;) rather than a literal character.
    text = html.unescape(text)
    # Drop everything from the Editor's Note heading onward - just the poem.
    text = re.split(r"<h3>Editor.s Note</h3>", text)[0]
    # Strip remaining tags and collapse extra blank lines.
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def split_title_author(raw_title: str) -> tuple[str, str]:
    """Split a feed title like "Poem Name by Author" into (title, author).

    Splits on the *last* " by " so poem titles that themselves contain
    "by" (e.g. "Stopping by Woods on a Snowy Evening") aren't cut short.
    Returns (raw_title, "") when no " by " is present at all.
    """
    if " by " in raw_title:
        title, author = raw_title.rsplit(" by ", 1)
        return title.strip(), author.strip()
    return raw_title.strip(), ""


def get_latest_item(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)
    item = root.find("./channel/item")  # first item = most recent
    if item is None:
        raise RuntimeError("No <item> found in feed")

    raw_title = (item.findtext("title") or "Untitled").strip()
    title, author = split_title_author(raw_title)
    link = item.findtext("link") or ""
    pub_date = item.findtext("pubDate") or ""
    content_el = item.find(CONTENT_NS)
    raw_html = content_el.text if content_el is not None else ""

    return {
        "raw_title": raw_title,  # unchanged combined string, used only for the filename slug
        "title": title,
        "author": author,
        "link": link.strip(),
        "pub_date": pub_date.strip(),
        "poem": html_to_text(raw_html or ""),
    }


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return slug[:60] or "poem"


def save_poem(item: dict, out_dir: Path) -> tuple[Path, bool]:
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{slugify(item['raw_title'])}.txt"
    path = out_dir / filename

    if path.exists():
        return path, False  # already downloaded today, don't overwrite

    title_block = f"{item['title']}\nby {item['author']}" if item["author"] else item["title"]
    body = f"{item['pub_date']}\n{item['link']}\n\n{title_block}\n\n{item['poem']}\n"
    path.write_text(body, encoding="utf-8")
    return path, True


def main() -> int:
    try:
        xml_bytes = fetch_feed(FEED_URL)
        item = get_latest_item(xml_bytes)
        path, wrote = save_poem(item, OUTPUT_DIR)
        print(f"Saved: {path}" if wrote else f"Already saved today: {path}")
        return 0
    except Exception as exc:
        print(f"Failed to fetch/save poem: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
