#!/usr/bin/env python3
"""
Basilica Joke Generator — deploys a vLLM model and serves jokes on a webpage.

Usage:
    echo 'BASILICA_API_TOKEN=basilica_...' > .env
    python app.py

Or set BASILICA_API_TOKEN as an environment variable.
"""

import base64
import io
import os
import random
import re
import textwrap
from datetime import datetime, timezone
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
MODEL = "Qwen/Qwen3-0.6B"

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
    <p class="subtitle">Built by <a href="https://x.com/bitsecai" style="color:#6c3ce0;text-decoration:none;">BitSec</a> &middot; Qwen3-0.6B Inference by <a href="https://x.com/basilic_ai" style="color:#6c3ce0;text-decoration:none;">Basilica</a></p>
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
      const text = currentJokeText + '\n\nvia @bitsecai x @basilic_ai';
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
    # 1. Pick a random factoid as the topic
    factoid = random.choice(FACTOIDS)

    # 2. Pick a random comedy technique and sample few-shot examples
    technique = random.choice(TECHNIQUES)
    examples = random.sample(EXAMPLES[technique], min(3, len(EXAMPLES[technique])))
    examples_block = "\n".join(f"- {ex}" for ex in examples)

    system_prompt = (
        f"You write short roast jokes about the Bittensor (TAO) crypto ecosystem.\n\n"
        f"Your comedy style: {technique}\n\n"
        f"Examples of this style:\n{examples_block}\n\n"
        f"Write ONE new joke in the same style. Just the joke, nothing else.\n\n"
        f"/no_think"
    )

    user_prompt = f"Write a roast joke using this fact: {factoid}"

    response = _get_llm().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        top_p=0.8,
        max_tokens=150,
    )
    joke = re.sub(r"<think>.*?</think>\s*", "", response.choices[0].message.content, flags=re.DOTALL).strip()
    joke_id = save_joke(joke, factoid, technique)
    return jsonify(joke=joke, id=joke_id)


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
  <meta property="og:title" content="Bittensor Roast Machine">
  <meta property="og:description" content="{{ joke }}">
  <meta property="og:image" content="{{ site_url }}/joke/{{ joke_id }}/image">
  <meta property="og:url" content="{{ site_url }}/joke/{{ joke_id }}">
  <meta name="twitter:card" content="summary_large_image">
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
    .footer { margin-top: 24px; color: #555; font-size: 0.75rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Bittensor Roast Machine</h1>
    <p class="subtitle">Built by <a href="https://x.com/bitsecai" style="color:#6c3ce0;text-decoration:none;">BitSec</a> &middot; Qwen3-0.6B Inference by <a href="https://x.com/basilic_ai" style="color:#6c3ce0;text-decoration:none;">Basilica</a></p>
    <div class="joke-text">{{ joke }}</div>
    <div class="joke-meta">
      <span>{{ style }}</span>
      <span>{{ time }}</span>
    </div>
    <a class="btn" href="/">Get roasted</a>
    <p class="footer">
      <a href="/all-jokes" style="color:#6c3ce0;text-decoration:none;">View all roasts</a>
      &middot; <a href="https://github.com/Bitsec-AI/jokes" style="color:#6c3ce0;text-decoration:none;">GitHub</a>
      &middot; TAO bless
    </p>
  </div>
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

@app.route("/joke/<joke_id>/image")
def joke_image(joke_id: str):
    data = _load_joke(joke_id)
    if not data:
        abort(404)

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#0f0f1a")
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.load_default(size=48)
    font_body = ImageFont.load_default(size=36)
    font_footer = ImageFont.load_default(size=24)

    # Title
    title = "Bittensor Roast Machine"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((W - bbox[2]) / 2, 40), title, fill="#e0e0e0", font=font_title)

    # Joke text — word-wrapped
    joke_text = data["joke"]
    wrapped = textwrap.fill(joke_text, width=45)
    bbox = draw.textbbox((0, 0), wrapped, font=font_body)
    text_h = bbox[3] - bbox[1]
    y_start = (H - text_h) / 2
    draw.text((80, y_start), wrapped, fill="white", font=font_body)

    # Footer
    footer = "@bitsecai x @basilic_ai"
    bbox = draw.textbbox((0, 0), footer, font=font_footer)
    draw.text(((W - bbox[2]) / 2, H - 60), footer, fill="#555555", font=font_footer)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")


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
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n  Open http://localhost:{port} in your browser\n")
    app.run(host="0.0.0.0", port=port)
