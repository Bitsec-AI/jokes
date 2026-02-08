# Interesting Techniques

1. **vLLM as OpenAI-compatible API** — The app talks to a self-hosted Qwen3-0.6B model through Basilica's vLLM deployment, but uses the standard `openai` Python SDK to call it. The trick: vLLM exposes an `/v1` endpoint that mimics OpenAI's chat completions API, so `api_key="not-needed"` works fine.

2. **Lazy singleton with cache-busting on failure** — `_get_llm()` caches the OpenAI client in a module-level global `_llm`. If an inference call fails, the handler sets `_llm = None` to force reconnection on the next request. Cheap circuit-breaker pattern without any library.

3. **Find-only deployment lookup (no auto-deploy)** — `_get_llm()` iterates `client.list_deployments()` looking for any `Active` instance. It never calls `deploy_vllm()` itself. Deploying is done externally (CLI or script) before the app starts. This avoids gunicorn workers blocking for minutes during model spin-up and prevents accidental GPU billing from web traffic.

4. **TTL-based Basilica deployments** — Models are deployed with `ttl_seconds=3600` (1 hour). The instance auto-terminates after the TTL expires, so there's no forgotten GPU running up a bill. To keep it alive, you redeploy before expiry. Zero ongoing cost when the app is idle.

5. **Basilica instance reuse awareness** — The app connects to whatever `Active` deployment it finds, keyed by instance name. A lesson learned: `deploy_vllm()` can reuse deleted instance IDs and connect to stale instances running the wrong model. The app sidesteps this by only reading state, never writing it.

6. **`/no_think` in the system prompt** — Qwen3 models have a "thinking mode" that emits `<think>` reasoning tags before answering. Appending `/no_think` to the system prompt disables it, cutting latency and token waste on a 0.6B model that doesn't think well anyway.

7. **Two-pass `<think>` tag stripping** — `_clean_joke()` first removes properly closed `<think>...</think>` blocks, then removes unclosed `<think>...EOF` tails (from max_tokens cutoffs). Order matters: greedy regex on unclosed tags first would eat closed ones.

8. **SequenceMatcher dedup with retry loop** — Generated jokes are compared against all few-shot examples AND the last 50 saved jokes using `difflib.SequenceMatcher` (threshold 0.6). If a joke is too similar, it retries up to 3 times with a fresh random factoid/technique each attempt.

9. **Single few-shot example (not multiple)** — The 0.6B model parrots verbatim when given 3 examples. Reducing to 1 example + explicit "DO NOT copy" instructions was the workaround. The prompt also randomizes which technique and which example get selected each call.

10. **Markdown as a structured data format** — Jokes are persisted as individual `.md` files with a consistent format (`> quote`, `**Style:**`, `**Factoid:**`). Factoids and examples are also parsed from markdown via regex. No database — the filesystem IS the database.

11. **Filename-as-metadata** — Joke filenames encode timestamp + slug: `20260208-143022-tao-holders-bought-the-dip.md`. Sorting by filename gives chronological order. Parsing the filename gives the creation time. No database index needed.

12. **In-memory joke cache with count-based invalidation** — `_get_jokes()` caches parsed joke dicts in `_joke_cache` and only re-parses when the file count changes (`len(files) != _joke_cache_count`). Avoids re-reading hundreds of files on every `/all-jokes` page load.

13. **GitHub Contents API as persistence layer for Fly.io** — Fly.io ephemeral VMs lose local files on redeploy. The app syncs jokes from a GitHub repo on first request (`_sync_from_github`) using threaded downloads, and pushes new jokes back via the Contents API on share. GitHub becomes the durable store.

14. **ThreadPoolExecutor for parallel GitHub downloads** — `_sync_from_github()` fetches the directory listing, diffs against local files, then downloads missing jokes in parallel with 10 workers. Keeps boot-time sync fast.

15. **Pillow OG image generation with `lru_cache`** — `/joke/<id>/image` renders a branded PNG on-the-fly using Pillow (gradient background, orange accent, word-wrapped text). The `@functools.lru_cache(maxsize=256)` decorator memoizes by joke text so repeat requests skip rendering.

16. **Pixel-by-pixel gradient background** — `_render_joke_image` draws a gradient by iterating every Y coordinate and drawing a 1px horizontal line with interpolated RGB values. No gradient fill API in Pillow, so it's hand-rolled.

17. **`render_template_string` with inline HTML** — All HTML templates are stored as Python string constants (`HTML`, `JOKE_PAGE_HTML`, `ALL_JOKES_HTML`) and rendered via Flask's `render_template_string`. Zero template files — the entire app is one `.py` file plus content markdown.

18. **OG meta tags + Twitter Card for social sharing** — The permalink page (`/joke/<id>`) includes full OpenGraph and Twitter Card meta tags pointing to the dynamically-generated image, enabling rich previews when shared on X.

19. **X share intent URL construction** — The "Share on X" button builds a `https://x.com/intent/tweet?text=...&url=...` URL client-side, pre-populating the tweet with joke text + permalink. Best-effort push to GitHub happens first so the permalink resolves.

20. **Gunicorn 300s timeout for slow LLM inference** — Default gunicorn timeout (30s) kills workers before the 0.6B model finishes cold-start inference. The Dockerfile sets `--timeout 300` to accommodate slow first responses.

21. **Fly.io auto-stop/auto-start machines** — `fly.toml` sets `auto_stop_machines = 'stop'` and `min_machines_running = 0`, so the VM shuts down when idle and boots on the next request. Free-tier friendly — only pays for actual usage.

22. **Test isolation by re-declaring functions** — `test_app.py` re-declares `_clean_joke`, `load_factoids`, and `load_examples` instead of importing from `app.py`. This avoids triggering `app.py`'s module-level code (Basilica client init, file loading) during tests. Pragmatic over pure.

23. **Content markdown as few-shot prompt material** — `examples.md` serves double duty: it's human-readable documentation of comedy techniques AND machine-parsed few-shot examples. One source of truth for both the README and the prompt.
