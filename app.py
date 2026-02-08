#!/usr/bin/env python3
"""
Basilica Joke Generator — deploys a vLLM model and serves jokes on a webpage.

Usage:
    echo 'BASILICA_API_TOKEN=basilica_...' > .env
    python app.py

Or set BASILICA_API_TOKEN as an environment variable.
"""

import base64
import functools
import io
import os
import random
import re
import textwrap
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
import requests as http_requests
from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, render_template_string, request
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from basilica import BasilicaClient

# ---------------------------------------------------------------------------
# Auth: load API token from env or .env file
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Connect to existing deployment, or deploy a new one
# ---------------------------------------------------------------------------
MODEL = "Qwen/Qwen3-4B"

_llm = None


def _get_llm():
    """Lazy-init Basilica connection on first /api/joke request."""
    global _llm
    if _llm is not None:
        return _llm
    client = BasilicaClient()
    deployment = None
    for d in client.list_deployments().deployments:
        if d.state == "Active":
            deployment = client.get(d.instance_name)
            print(f"Reusing existing deployment: {deployment.url}")
            break
    if deployment is None:
        print(f"Deploying {MODEL} … (this may take a few minutes)")
        deployment = client.deploy_vllm(model=MODEL, name="joke-generator", ttl_seconds=3600)
        print(f"Model ready at {deployment.url}")
    _llm = OpenAI(base_url=f"{deployment.url}/v1", api_key="not-needed")
    return _llm

# ---------------------------------------------------------------------------
# Load factoids and example jokes
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent


def load_factoids(path: Path) -> list[str]:
    """Parse factoids.md — extract numbered items (e.g. '1. ...')."""
    items = []
    for line in path.read_text().splitlines():
        m = re.match(r"^\d+\.\s+(.+)", line)
        if m:
            items.append(m.group(1).strip())
    return items


def load_examples(path: Path) -> dict[str, list[str]]:
    """Parse examples.md into {technique_name: [joke, ...]}."""
    sections: dict[str, list[str]] = {}
    current_section = None
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            sections[current_section] = []
        elif current_section and line.startswith("- "):
            sections[current_section].append(line.removeprefix("- ").strip())
    return {k: v for k, v in sections.items() if v}


FACTOIDS = load_factoids(BASE_DIR / "factoids.md")
EXAMPLES = load_examples(BASE_DIR / "examples.md")
TECHNIQUES = list(EXAMPLES.keys())
JOKES_DIR = BASE_DIR / "all-jokes"
JOKES_DIR.mkdir(exist_ok=True)

GITHUB_REPO = "Bitsec-AI/jokes"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
SITE_URL = "https://bittensor-roast.fly.dev"

# Flat set of all example jokes (for deduplication)
ALL_EXAMPLES: set[str] = {joke for jokes in EXAMPLES.values() for joke in jokes}

# Similarity threshold — anything above this vs examples or recent jokes triggers retry
DEDUP_THRESHOLD = 0.6
MAX_RETRIES = 3


def _clean_joke(raw: str) -> str:
    """Strip <think> tags (including unclosed ones) from model output."""
    text = re.sub(r"<think>.*?</think>\s*", "", raw, flags=re.DOTALL)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    return text.strip().strip('"').strip()


def _is_duplicate(joke: str) -> bool:
    """Check if joke is too similar to an example or a recently generated joke."""
    joke_lower = joke.lower()
    # Check against all few-shot examples
    for ex in ALL_EXAMPLES:
        if SequenceMatcher(None, joke_lower, ex.lower()).ratio() > DEDUP_THRESHOLD:
            return True
    # Check against recently saved jokes (last 50)
    recent = _get_jokes()[:50]
    for prev in recent:
        if SequenceMatcher(None, joke_lower, prev["joke"].lower()).ratio() > DEDUP_THRESHOLD:
            return True
    return False

# ---------------------------------------------------------------------------
# In-memory joke index (avoids re-parsing all files on every request)
# ---------------------------------------------------------------------------
_joke_cache: list[dict] = []
_joke_cache_count: int = -1  # force initial load
JOKES_PER_PAGE = 20


def _parse_joke_file(f: Path) -> dict:
    text = f.read_text()
    joke_match = re.search(r"^> (.+)$", text, re.MULTILINE)
    style_match = re.search(r"\*\*Style:\*\* (.+)", text)
    ts_match = re.match(r"(\d{8})-(\d{6})", f.name)
    time_str = ""
    if ts_match:
        d, t = ts_match.groups()
        time_str = f"{d[:4]}-{d[4:6]}-{d[6:]} {t[:2]}:{t[2:4]} UTC"
    return {
        "id": f.stem,
        "joke": joke_match.group(1).strip() if joke_match else "(parse error)",
        "style": style_match.group(1).strip() if style_match else "",
        "time": time_str,
    }


def _get_jokes() -> list[dict]:
    global _joke_cache, _joke_cache_count
    files = sorted(JOKES_DIR.glob("*.md"), reverse=True)
    if len(files) != _joke_cache_count:
        _joke_cache = [_parse_joke_file(f) for f in files]
        _joke_cache_count = len(files)
    return _joke_cache


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Basilica Joke Generator</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #0f0f1a;
      color: #e0e0e0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #1a1a2e;
      border: 1px solid #2a2a4a;
      border-radius: 16px;
      padding: 48px;
      max-width: 600px;
      width: 90%;
      text-align: center;
    }
    h1 { font-size: 2rem; margin-bottom: 8px; }
    .subtitle { color: #888; margin-bottom: 32px; font-size: 0.9rem; }
    #joke {
      background: #12121f;
      border: 1px solid #2a2a4a;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      min-height: 80px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
      line-height: 1.6;
      white-space: pre-wrap;
    }
    #joke.empty { color: #555; font-style: italic; }
    button {
      background: linear-gradient(135deg, #6c3ce0, #4a7cf7);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 14px 32px;
      font-size: 1rem;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    button:hover { opacity: 0.85; }
    button:disabled { opacity: 0.5; cursor: wait; }
    .footer { margin-top: 24px; color: #555; font-size: 0.75rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Bittensor Roast Machine</h1>
    <p class="subtitle">Built by <a href="https://x.com/bitsecai" style="color:#6c3ce0;text-decoration:none;">bitsecai</a> &middot; Powered by <a href="https://x.com/basilic_ai" style="color:#6c3ce0;text-decoration:none;">Basilica</a> + Qwen/Qwen3-4B</p>
    <div id="joke" class="empty">Click the button to get roasted, subnet owner.</div>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <button id="btn" onclick="getJoke()">Roast a subnet owner</button>
      <button id="share-btn" onclick="shareJoke()" style="display:none;background:linear-gradient(135deg,#1da1f2,#0d8ecf);">Share on X</button>
    </div>
    <p class="footer">
      <a href="/all-jokes" style="color:#6c3ce0;text-decoration:none;">View all roasts</a>
      &middot; <a href="https://github.com/Bitsec-AI/jokes" style="color:#6c3ce0;text-decoration:none;">GitHub</a>
      &middot; TAO bless
    </p>
  </div>
  <script>
    let currentJokeId = null;
    let currentJokeText = null;

    async function getJoke() {
      const btn = document.getElementById('btn');
      const box = document.getElementById('joke');
      const shareBtn = document.getElementById('share-btn');
      btn.disabled = true;
      btn.textContent = 'Thinking…';
      shareBtn.style.display = 'none';
      box.className = 'empty';
      box.textContent = '...';
      try {
        const res = await fetch('/api/joke');
        const data = await res.json();
        box.className = '';
        box.textContent = data.joke;
        currentJokeId = data.id;
        currentJokeText = data.joke;
        shareBtn.style.display = 'inline-block';
      } catch (err) {
        box.className = '';
        box.textContent = 'Oops, something went wrong. Try again!';
      }
      btn.disabled = false;
      btn.textContent = 'Tell me another joke';
    }

    async function shareJoke() {
      if (!currentJokeId) return;
      const shareBtn = document.getElementById('share-btn');
      shareBtn.disabled = true;
      shareBtn.textContent = 'Saving…';
      try {
        await fetch('/api/share/' + currentJokeId, {method: 'POST'});
      } catch (e) { /* best effort */ }
      const permalink = '{{ site_url }}/joke/' + currentJokeId;
      const text = currentJokeText + String.fromCharCode(10,10) + 'via @bitsecai x @basilic_ai';
      const intentUrl = 'https://x.com/intent/tweet?text=' + encodeURIComponent(text) + '&url=' + encodeURIComponent(permalink);
      window.open(intentUrl, '_blank');
      shareBtn.disabled = false;
      shareBtn.textContent = 'Share on X';
    }
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML, model=MODEL, site_url=SITE_URL)


def save_joke(joke: str, factoid: str, technique: str) -> str:
    """Save a generated joke as a markdown file in all-jokes/. Returns the filename stem (joke ID)."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", joke[:40].lower()).strip("-")
    filename = f"{ts}-{slug}.md"
    content = (
        f"# Roast\n\n"
        f"> {joke}\n\n"
        f"**Style:** {technique}  \n"
        f"**Factoid:** {factoid}\n"
    )
    (JOKES_DIR / filename).write_text(content)
    return Path(filename).stem


@app.route("/api/joke")
def api_joke():
    for attempt in range(MAX_RETRIES):
        # 1. Pick a random factoid as the topic
        factoid = random.choice(FACTOIDS)

        # 2. Pick a random comedy technique and ONE example
        technique = random.choice(TECHNIQUES)
        example = random.choice(EXAMPLES[technique])

        system_prompt = (
            f"You write short, original roast jokes about the Bittensor (TAO) crypto ecosystem.\n\n"
            f"Your comedy style: {technique}\n\n"
            f"Here is one example of the style (DO NOT copy or paraphrase this — write something completely new):\n"
            f"- {example}\n\n"
            f"Rules:\n"
            f"- Write ONE new joke. Just the joke text, nothing else.\n"
            f"- Your joke MUST be original. Do NOT reuse phrases or structure from the example.\n"
            f"- Use the factoid below as inspiration, but transform it into humor — don't just restate it.\n\n"
            f"/no_think"
        )

        user_prompt = f"Write a roast joke using this fact: {factoid}"

        response = _get_llm().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            top_p=0.95,
            max_tokens=150,
        )
        joke = _clean_joke(response.choices[0].message.content)

        if not joke or len(joke) < 20:
            continue  # too short / empty — retry
        if not _is_duplicate(joke):
            break  # original enough — use it
    # else: use the last attempt even if it's a dupe (better than nothing)

    joke_id = save_joke(joke, factoid, technique)
    resp = jsonify(joke=joke, id=joke_id)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------------------
# Joke loading helper (local filesystem + GitHub API fallback)
# ---------------------------------------------------------------------------

def _load_joke(joke_id: str) -> dict | None:
    """Find a joke by ID. Checks local files first, falls back to GitHub API."""
    # Local: glob for files starting with the ID
    matches = list(JOKES_DIR.glob(f"{joke_id}*.md"))
    if matches:
        return _parse_joke_file(matches[0])

    # Fallback: fetch from GitHub API
    if not GITHUB_TOKEN:
        return None
    # Try exact filename (ID + .md)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/all-jokes/{joke_id}.md"
    resp = http_requests.get(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }, timeout=10)
    if resp.status_code != 200:
        return None
    content = base64.b64decode(resp.json()["content"]).decode()
    joke_match = re.search(r"^> (.+)$", content, re.MULTILINE)
    style_match = re.search(r"\*\*Style:\*\* (.+)", content)
    ts_match = re.match(r"(\d{8})-(\d{6})", joke_id)
    time_str = ""
    if ts_match:
        d, t = ts_match.groups()
        time_str = f"{d[:4]}-{d[4:6]}-{d[6:]} {t[:2]}:{t[2:4]} UTC"
    return {
        "joke": joke_match.group(1).strip() if joke_match else "(parse error)",
        "style": style_match.group(1).strip() if style_match else "",
        "time": time_str,
    }


# ---------------------------------------------------------------------------
# Share endpoint: commit joke file to GitHub
# ---------------------------------------------------------------------------

@app.route("/api/share/<joke_id>", methods=["POST"])
def api_share(joke_id: str):
    if not GITHUB_TOKEN:
        return jsonify(ok=False, error="GITHUB_TOKEN not configured"), 500

    # Find the local file
    matches = list(JOKES_DIR.glob(f"{joke_id}*.md"))
    if not matches:
        return jsonify(ok=False, error="Joke not found"), 404

    filepath = matches[0]
    content_b64 = base64.b64encode(filepath.read_bytes()).decode()

    # PUT to GitHub Contents API
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/all-jokes/{filepath.name}"
    resp = http_requests.put(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }, json={
        "message": f"Add joke {filepath.name}",
        "content": content_b64,
    }, timeout=15)

    if resp.status_code in (200, 201):
        return jsonify(ok=True, url=f"{SITE_URL}/joke/{joke_id}")
    if resp.status_code == 422:
        # Already exists — that's fine
        return jsonify(ok=True, url=f"{SITE_URL}/joke/{joke_id}")
    return jsonify(ok=False, error=f"GitHub API error {resp.status_code}"), 502


# ---------------------------------------------------------------------------
# Permalink page with OG meta tags
# ---------------------------------------------------------------------------

JOKE_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bittensor Roast</title>
  <meta property="og:type" content="website">
  <meta property="og:title" content="Bittensor Roast Machine">
  <meta property="og:description" content="{{ joke }}">
  <meta property="og:image" content="{{ site_url }}/joke/{{ joke_id }}/image">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:url" content="{{ site_url }}/joke/{{ joke_id }}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@bitsecai">
  <meta name="twitter:title" content="Bittensor Roast Machine">
  <meta name="twitter:description" content="{{ joke }}">
  <meta name="twitter:image" content="{{ site_url }}/joke/{{ joke_id }}/image">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #0f0f1a;
      color: #e0e0e0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #1a1a2e;
      border: 1px solid #2a2a4a;
      border-radius: 16px;
      padding: 48px;
      max-width: 600px;
      width: 90%;
      text-align: center;
    }
    h1 { font-size: 2rem; margin-bottom: 8px; }
    .subtitle { color: #888; margin-bottom: 32px; font-size: 0.9rem; }
    .joke-text {
      background: #12121f;
      border: 1px solid #2a2a4a;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 16px;
      font-size: 1.1rem;
      line-height: 1.6;
    }
    .joke-meta { color: #555; font-size: 0.75rem; margin-bottom: 24px; }
    .joke-meta span { margin-right: 16px; }
    a.btn {
      display: inline-block;
      background: linear-gradient(135deg, #6c3ce0, #4a7cf7);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 14px 32px;
      font-size: 1rem;
      cursor: pointer;
      text-decoration: none;
      transition: opacity 0.2s;
    }
    a.btn:hover { opacity: 0.85; }
    .btn-share {
      display: inline-block;
      background: linear-gradient(135deg, #1da1f2, #0d8ecf);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 14px 32px;
      font-size: 1rem;
      cursor: pointer;
      text-decoration: none;
      transition: opacity 0.2s;
    }
    .btn-share:hover { opacity: 0.85; color: white; }
    .footer { margin-top: 24px; color: #555; font-size: 0.75rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Bittensor Roast Machine</h1>
    <p class="subtitle">Built by <a href="https://x.com/bitsecai" style="color:#6c3ce0;text-decoration:none;">bitsecai</a> &middot; Powered by <a href="https://x.com/basilic_ai" style="color:#6c3ce0;text-decoration:none;">Basilica</a> + Qwen/Qwen3-4B</p>
    <div class="joke-text">{{ joke }}</div>
    <div class="joke-meta">
      <span>{{ style }}</span>
      <span>{{ time }}</span>
    </div>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a class="btn" href="/">Get roasted</a>
      <a class="btn-share" id="share-btn" href="#" onclick="sharePage(event)">Share on X</a>
    </div>
    <p class="footer">
      <a href="/all-jokes" style="color:#6c3ce0;text-decoration:none;">View all roasts</a>
      &middot; <a href="https://github.com/Bitsec-AI/jokes" style="color:#6c3ce0;text-decoration:none;">GitHub</a>
      &middot; TAO bless
    </p>
  </div>
  <script>
    function sharePage(e) {
      e.preventDefault();
      var jokeText = document.querySelector('.joke-text').textContent;
      var permalink = '{{ site_url }}/joke/{{ joke_id }}';
      var text = jokeText + String.fromCharCode(10,10) + 'via @bitsecai x @basilic_ai';
      window.open('https://x.com/intent/tweet?text=' + encodeURIComponent(text) + '&url=' + encodeURIComponent(permalink), '_blank');
    }
  </script>
</body>
</html>
"""


@app.route("/joke/<joke_id>")
def joke_permalink(joke_id: str):
    data = _load_joke(joke_id)
    if not data:
        abort(404)
    return render_template_string(
        JOKE_PAGE_HTML,
        joke=data["joke"],
        style=data["style"],
        time=data["time"],
        joke_id=joke_id,
        site_url=SITE_URL,
    )


# ---------------------------------------------------------------------------
# OG image generation (Pillow)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=256)
def _render_joke_image(joke_text: str) -> bytes:
    """Render a joke as a branded PNG. Cached in memory (up to 256 images)."""
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#0f0f1a")
    draw = ImageDraw.Draw(img)

    # Subtle gradient: deep black to slightly warm black
    for y in range(H):
        frac = y / H
        r = int(10 + frac * 15)
        g = int(10 + frac * 8)
        b = int(10 + frac * 5)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Orange accent line at top
    draw.rectangle([(0, 0), (W, 4)], fill="#f57c20")

    font_title = ImageFont.load_default(size=42)
    font_body = ImageFont.load_default(size=34)
    font_quote = ImageFont.load_default(size=120)
    font_footer = ImageFont.load_default(size=22)

    # Big decorative quote mark in orange
    draw.text((60, 80), "\u201c", fill="#f57c2060", font=font_quote)

    # Title in orange
    title = "Bittensor Roast Machine"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((W - bbox[2]) / 2, 36), title, fill="#f57c20", font=font_title)

    # Joke text — white, word-wrapped and vertically centered
    wrapped = textwrap.fill(joke_text, width=42)
    bbox = draw.textbbox((0, 0), wrapped, font=font_body)
    text_h = bbox[3] - bbox[1]
    y_start = max(140, (H - text_h) / 2 - 10)
    draw.text((120, y_start), wrapped, fill="white", font=font_body)

    # Divider line above footer
    draw.line([(100, H - 80), (W - 100, H - 80)], fill="#333333", width=1)

    # Footer
    footer = "@bitsecai  x  @basilic_ai"
    bbox = draw.textbbox((0, 0), footer, font=font_footer)
    draw.text(((W - bbox[2]) / 2, H - 55), footer, fill="#999999", font=font_footer)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@app.route("/joke/<joke_id>/image")
def joke_image(joke_id: str):
    data = _load_joke(joke_id)
    if not data:
        abort(404)
    png = _render_joke_image(data["joke"])
    return Response(png, mimetype="image/png", headers={"Cache-Control": "public, max-age=86400"})


ALL_JOKES_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>All Roasts</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #0f0f1a;
      color: #e0e0e0;
      min-height: 100vh;
      padding: 48px 24px;
    }
    .container { max-width: 700px; margin: 0 auto; }
    h1 { font-size: 2rem; margin-bottom: 8px; text-align: center; }
    .subtitle { color: #888; margin-bottom: 32px; font-size: 0.9rem; text-align: center; }
    .joke-card {
      background: #1a1a2e;
      border: 1px solid #2a2a4a;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 16px;
    }
    .joke-text { font-size: 1.05rem; line-height: 1.6; margin-bottom: 12px; }
    .joke-meta { color: #555; font-size: 0.75rem; }
    .joke-meta span { margin-right: 16px; }
    a { color: #6c3ce0; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .back { text-align: center; margin-bottom: 24px; }
    .empty-state { text-align: center; color: #555; padding: 48px; font-style: italic; }
    .filters { text-align: center; margin-bottom: 24px; line-height: 2; }
    .filter-label { color: #888; margin-right: 8px; font-size: 0.85rem; }
    .filters a {
      display: inline-block; padding: 4px 12px; margin: 2px 4px;
      border-radius: 6px; font-size: 0.8rem; border: 1px solid #2a2a4a;
      color: #aaa; transition: all 0.15s;
    }
    .filters a:hover { border-color: #6c3ce0; color: #e0e0e0; text-decoration: none; }
    .filters a.active { background: #6c3ce0; border-color: #6c3ce0; color: white; }
    .pagination {
      display: flex; justify-content: center; align-items: center;
      gap: 24px; margin-top: 24px; padding: 16px 0;
    }
    .pagination a {
      padding: 8px 16px; border: 1px solid #2a2a4a;
      border-radius: 8px; font-size: 0.85rem; transition: border-color 0.15s;
    }
    .pagination a:hover { border-color: #6c3ce0; text-decoration: none; }
    .pagination .disabled { color: #333; padding: 8px 16px; font-size: 0.85rem; }
    .page-info { color: #888; font-size: 0.85rem; }
    .share-link { color: #1da1f2 !important; margin-left: 8px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>All Roasts</h1>
    <p class="subtitle">
      {% if style_filter %}
        {{ count }} {{ style_filter }} roast{{ 's' if count != 1 else '' }}
        (of {{ total_all }} total)
      {% else %}
        {{ count }} roast{{ 's' if count != 1 else '' }} generated
      {% endif %}
    </p>
    <p class="back"><a href="/">&larr; Back to roast machine</a></p>
    <div class="filters">
      <span class="filter-label">Filter:</span>
      <a href="/all-jokes" class="{{ 'active' if not style_filter else '' }}">All</a>
      {% for tech in techniques %}
        <a href="/all-jokes?style={{ tech }}"
           class="{{ 'active' if style_filter == tech else '' }}">{{ tech }}</a>
      {% endfor %}
    </div>
    {% if jokes %}
      {% for j in jokes %}
      <div class="joke-card">
        <div class="joke-text">{{ j.joke }}</div>
        <div class="joke-meta">
          <span>{{ j.style }}</span>
          <span>{{ j.time }}</span>
          <a href="#" class="share-link" onclick="shareFromList('{{ j.id }}', this, event)">Share on X</a>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty-state">No roasts yet. Go generate some!</div>
    {% endif %}
    {% if total_pages > 1 %}
    <div class="pagination">
      {% if page > 1 %}
        <a href="/all-jokes?page={{ page - 1 }}{{ '&style=' + style_filter if style_filter else '' }}">&larr; Newer</a>
      {% else %}
        <span class="disabled">&larr; Newer</span>
      {% endif %}
      <span class="page-info">Page {{ page }} of {{ total_pages }}</span>
      {% if page < total_pages %}
        <a href="/all-jokes?page={{ page + 1 }}{{ '&style=' + style_filter if style_filter else '' }}">Older &rarr;</a>
      {% else %}
        <span class="disabled">Older &rarr;</span>
      {% endif %}
    </div>
    {% endif %}
  </div>
  <script>
    async function shareFromList(jokeId, el, e) {
      e.preventDefault();
      const card = el.closest('.joke-card');
      const jokeText = card.querySelector('.joke-text').textContent;
      el.textContent = 'Saving…';
      try {
        await fetch('/api/share/' + jokeId, {method: 'POST'});
      } catch (err) { /* best effort */ }
      const permalink = '{{ site_url }}/joke/' + jokeId;
      const text = jokeText + String.fromCharCode(10,10) + 'via @bitsecai x @basilic_ai';
      window.open('https://x.com/intent/tweet?text=' + encodeURIComponent(text) + '&url=' + encodeURIComponent(permalink), '_blank');
      el.textContent = 'Share on X';
    }
  </script>
</body>
</html>
"""


@app.route("/all-jokes")
def all_jokes():
    all_items = _get_jokes()

    # --- Filtering ---
    style_filter = request.args.get("style", "").strip()
    if style_filter and style_filter in TECHNIQUES:
        filtered = [j for j in all_items if j["style"] == style_filter]
    else:
        style_filter = ""
        filtered = all_items

    total = len(filtered)

    # --- Pagination ---
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    total_pages = max(1, (total + JOKES_PER_PAGE - 1) // JOKES_PER_PAGE)
    page = min(page, total_pages)

    start = (page - 1) * JOKES_PER_PAGE
    page_jokes = filtered[start : start + JOKES_PER_PAGE]

    return render_template_string(
        ALL_JOKES_HTML,
        jokes=page_jokes,
        count=total,
        total_all=len(all_items),
        page=page,
        total_pages=total_pages,
        style_filter=style_filter,
        techniques=TECHNIQUES,
        site_url=SITE_URL,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n  Open http://localhost:{port} in your browser\n")
    app.run(host="0.0.0.0", port=port)
