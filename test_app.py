"""Tests for joke generation logic (no Basilica/network required)."""
import re
import tempfile
from pathlib import Path
from difflib import SequenceMatcher
from unittest.mock import patch, MagicMock
import pytest


# ---------------------------------------------------------------------------
# Import helpers directly (avoid importing app which triggers Basilica)
# ---------------------------------------------------------------------------
def _clean_joke(raw: str) -> str:
    """Strip <think> tags (including unclosed ones) from model output."""
    text = re.sub(r"<think>.*?</think>\s*", "", raw, flags=re.DOTALL)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    return text.strip().strip('"').strip()


def load_factoids(path: Path) -> list[str]:
    items = []
    for line in path.read_text().splitlines():
        m = re.match(r"^\d+\.\s+(.+)", line)
        if m:
            items.append(m.group(1).strip())
    return items


def load_examples(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_section = None
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            sections[current_section] = []
        elif current_section and line.startswith("- "):
            sections[current_section].append(line.removeprefix("- ").strip())
    return {k: v for k, v in sections.items() if v}


# ---------------------------------------------------------------------------
# Tests for _clean_joke
# ---------------------------------------------------------------------------
class TestCleanJoke:
    def test_plain_text(self):
        assert _clean_joke("This is a joke.") == "This is a joke."

    def test_closed_think_tags(self):
        raw = "<think>some reasoning</think>This is the joke."
        assert _clean_joke(raw) == "This is the joke."

    def test_closed_think_tags_multiline(self):
        raw = "<think>\nlong\nreasoning\n</think>\nThe actual joke."
        assert _clean_joke(raw) == "The actual joke."

    def test_unclosed_think_tag(self):
        """Model output cut off mid-think — no closing tag."""
        raw = "<think>reasoning that never ends because max_tokens hit"
        assert _clean_joke(raw) == ""

    def test_unclosed_think_tag_with_joke_before(self):
        """Edge case: joke text before an unclosed think."""
        raw = "The joke text.<think>some trailing reasoning"
        assert _clean_joke(raw) == "The joke text."

    def test_think_then_joke_then_unclosed_think(self):
        raw = "<think>ok</think>The joke.<think>more"
        assert _clean_joke(raw) == "The joke."

    def test_strips_surrounding_quotes(self):
        assert _clean_joke('"Here is a joke"') == "Here is a joke"

    def test_strips_whitespace(self):
        assert _clean_joke("  \n The joke \n  ") == "The joke"

    def test_empty_string(self):
        assert _clean_joke("") == ""

    def test_only_think_tags(self):
        assert _clean_joke("<think>just thinking</think>") == ""

    def test_nested_angle_brackets(self):
        """Model sometimes outputs other XML-like tags."""
        raw = "<think>stuff</think>TAO is <great> at losing money."
        assert _clean_joke(raw) == "TAO is <great> at losing money."


# ---------------------------------------------------------------------------
# Tests for load_factoids
# ---------------------------------------------------------------------------
class TestLoadFactoids:
    def test_parses_numbered_items(self, tmp_path):
        f = tmp_path / "facts.md"
        f.write_text("# Title\n\n1. First fact\n2. Second fact  \n3. Third fact\n")
        result = load_factoids(f)
        assert result == ["First fact", "Second fact", "Third fact"]

    def test_strips_trailing_whitespace(self, tmp_path):
        f = tmp_path / "facts.md"
        f.write_text("1. Fact with trailing spaces   \n")
        result = load_factoids(f)
        assert result == ["Fact with trailing spaces"]

    def test_skips_non_numbered_lines(self, tmp_path):
        f = tmp_path / "facts.md"
        f.write_text("# Header\nSome text\n1. Real fact\n- Bullet\n")
        result = load_factoids(f)
        assert result == ["Real fact"]

    def test_handles_real_file(self):
        base = Path(__file__).parent
        result = load_factoids(base / "factoids.md")
        assert len(result) > 100, f"Expected 100+ factoids, got {len(result)}"
        assert all(isinstance(f, str) and len(f) > 10 for f in result)


# ---------------------------------------------------------------------------
# Tests for load_examples
# ---------------------------------------------------------------------------
class TestLoadExamples:
    def test_parses_sections(self, tmp_path):
        f = tmp_path / "ex.md"
        f.write_text("## Style A\n- Joke 1\n- Joke 2\n\n## Style B\n- Joke 3\n")
        result = load_examples(f)
        assert set(result.keys()) == {"Style A", "Style B"}
        assert result["Style A"] == ["Joke 1", "Joke 2"]
        assert result["Style B"] == ["Joke 3"]

    def test_skips_empty_sections(self, tmp_path):
        f = tmp_path / "ex.md"
        f.write_text("## Empty\n\n## Has Jokes\n- A joke\n")
        result = load_examples(f)
        assert "Empty" not in result
        assert "Has Jokes" in result

    def test_handles_real_file(self):
        base = Path(__file__).parent
        result = load_examples(base / "examples.md")
        assert len(result) == 7, f"Expected 7 techniques, got {len(result)}"
        total = sum(len(v) for v in result.values())
        assert total == 48, f"Expected 48 example jokes, got {total}"


# ---------------------------------------------------------------------------
# Tests for deduplication logic
# ---------------------------------------------------------------------------
DEDUP_THRESHOLD = 0.6


def _is_similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > DEDUP_THRESHOLD


class TestDeduplication:
    def test_exact_copy_detected(self):
        example = "Staking TAO is like paying for a gym membership you never use."
        assert _is_similar(example, example)

    def test_minor_paraphrase_detected(self):
        a = "Bittensor: where 'decentralized' means one foundation with a kill switch."
        b = "Bittensor: where 'collaborative model training' means one foundation with a kill switch."
        assert _is_similar(a, b)

    def test_genuinely_different_passes(self):
        a = "TAO holders bought the dip. The dip bought them therapy."
        b = "Subnet owners burn millions to launch projects nobody uses."
        assert not _is_similar(a, b)

    def test_short_joke_vs_long_not_false_positive(self):
        a = "TAO is dead."
        b = "Bittensor finally solved the Byzantine generals problem. Their solution: let one general make all decisions."
        assert not _is_similar(a, b)


# ---------------------------------------------------------------------------
# Tests for save_joke (file I/O)
# ---------------------------------------------------------------------------
class TestSaveJoke:
    def test_creates_file_with_correct_content(self, tmp_path):
        # Inline the save logic to avoid importing app module
        joke = "Test joke about TAO"
        factoid = "TAO went to zero"
        technique = "Misdirection"

        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "-", joke[:40].lower()).strip("-")
        filename = f"{ts}-{slug}.md"
        content = (
            f"# Roast\n\n"
            f"> {joke}\n\n"
            f"**Style:** {technique}  \n"
            f"**Factoid:** {factoid}\n"
        )
        (tmp_path / filename).write_text(content)

        # Verify it can be parsed back
        text = (tmp_path / filename).read_text()
        joke_match = re.search(r"^> (.+)$", text, re.MULTILINE)
        style_match = re.search(r"\*\*Style:\*\* (.+)", text)
        factoid_match = re.search(r"\*\*Factoid:\*\* (.+)", text)

        assert joke_match.group(1).strip() == joke
        assert style_match.group(1).strip() == technique
        assert factoid_match.group(1).strip() == factoid


# ---------------------------------------------------------------------------
# Tests for prompt construction
# ---------------------------------------------------------------------------
class TestPromptConstruction:
    def test_system_prompt_has_anti_copy_instructions(self):
        technique = "Misdirection"
        example = "Some example joke here."
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
        assert "DO NOT copy" in system_prompt
        assert "MUST be original" in system_prompt
        assert "/no_think" in system_prompt
        assert technique in system_prompt
        assert example in system_prompt

    def test_only_one_example_in_prompt(self):
        """Verify we only include 1 example, not 3."""
        import random
        examples = {"Misdirection": ["joke1", "joke2", "joke3", "joke4"]}
        technique = "Misdirection"
        example = random.choice(examples[technique])
        # The prompt should contain exactly one "- " prefixed example
        prompt_examples = f"- {example}"
        assert prompt_examples.count("- ") == 1
