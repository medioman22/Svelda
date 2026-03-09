"""Unit tests for Svelda app helper functions.

Tests cover pure logic that does not require a running Qt application or
network connection: prompt normalisation, tooltip truncation, and the
JSON-based persistence helpers for job history and custom prompts.

Run with:
    conda run -n svelda python -m pytest _python/tests/ -v
or:
    conda run -n svelda python -m unittest discover _python/tests/
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure libs/ is importable before we import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "libs"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app  # noqa: E402


# ---------------------------------------------------------------------------
# _prepare()
# ---------------------------------------------------------------------------

class TestPrepare(unittest.TestCase):
    """Tests for the _prepare() prompt-normalisation function."""

    def test_single_part_returned_as_is(self):
        prompts, codes = app._prepare("KEY", ["single prompt text"])
        self.assertEqual(prompts, ["single prompt text"])
        self.assertEqual(codes, ["KEY"])

    def test_multi_part_joined_with_double_newline(self):
        prompts, codes = app._prepare("K", ["part one", "part two", "part three"])
        self.assertEqual(prompts, ["part one\n\npart two\n\npart three"])
        self.assertEqual(codes, ["K"])

    def test_two_parts_joined(self):
        prompts, codes = app._prepare("X", ["a", "b"])
        self.assertEqual(prompts, ["a\n\nb"])
        self.assertEqual(codes, ["X"])

    def test_empty_list_returned_unchanged(self):
        # Edge case: empty list → returned as-is (len ≤ 1)
        prompts, codes = app._prepare("K", [])
        self.assertEqual(prompts, [])
        self.assertEqual(codes, ["K"])

    def test_key_preserved_verbatim(self):
        _, codes = app._prepare("SOME_COMPOUND_KEY", ["text"])
        self.assertEqual(codes, ["SOME_COMPOUND_KEY"])


# ---------------------------------------------------------------------------
# _get_builtin_text()
# ---------------------------------------------------------------------------

class TestGetBuiltinText(unittest.TestCase):
    """Tests for _get_builtin_text()."""

    def test_known_key_returns_nonempty_string(self):
        text = app._get_builtin_text("NEUTRAL_WHITE")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

    def test_unknown_key_returns_empty_string(self):
        text = app._get_builtin_text("THIS_KEY_DOES_NOT_EXIST_XYZ_123")
        self.assertEqual(text, "")

    def test_all_builtin_keys_return_nonempty_text(self):
        for key in app._BUILTIN_KEYS:
            with self.subTest(key=key):
                text = app._get_builtin_text(key)
                self.assertIsInstance(text, str)
                self.assertGreater(len(text), 0)


# ---------------------------------------------------------------------------
# _prompt_tooltip()
# ---------------------------------------------------------------------------

class TestPromptTooltip(unittest.TestCase):
    """Tests for _prompt_tooltip()."""

    def test_builtin_key_returns_nonempty_string(self):
        tip = app._prompt_tooltip("NEUTRAL_WHITE")
        self.assertIsInstance(tip, str)
        self.assertGreater(len(tip), 0)

    def test_unknown_key_returns_empty_string(self):
        tip = app._prompt_tooltip("NONEXISTENT_KEY_ZZZ_999")
        self.assertEqual(tip, "")

    def test_long_custom_prompt_is_truncated_at_600_chars(self):
        long_text = "x" * 700
        app.CUSTOM_PROMPT_TEXTS["_TEST_LONG_TMP"] = long_text
        try:
            tip = app._prompt_tooltip("_TEST_LONG_TMP")
            # Should be exactly 600 chars + the ellipsis character
            self.assertEqual(len(tip), 601)
            self.assertTrue(tip.endswith("…"))
        finally:
            del app.CUSTOM_PROMPT_TEXTS["_TEST_LONG_TMP"]

    def test_short_custom_prompt_has_no_ellipsis(self):
        short_text = "Short photography prompt"
        app.CUSTOM_PROMPT_TEXTS["_TEST_SHORT_TMP"] = short_text
        try:
            tip = app._prompt_tooltip("_TEST_SHORT_TMP")
            self.assertEqual(tip, short_text)
            self.assertFalse(tip.endswith("…"))
        finally:
            del app.CUSTOM_PROMPT_TEXTS["_TEST_SHORT_TMP"]

    def test_exactly_600_char_prompt_has_no_ellipsis(self):
        exact_text = "y" * 600
        app.CUSTOM_PROMPT_TEXTS["_TEST_EXACT_TMP"] = exact_text
        try:
            tip = app._prompt_tooltip("_TEST_EXACT_TMP")
            self.assertEqual(len(tip), 600)
            self.assertFalse(tip.endswith("…"))
        finally:
            del app.CUSTOM_PROMPT_TEXTS["_TEST_EXACT_TMP"]


# ---------------------------------------------------------------------------
# _load_jobs_history() / _save_jobs_history()
# ---------------------------------------------------------------------------

class TestJobHistory(unittest.TestCase):
    """Tests for the job history persistence helpers."""

    def setUp(self):
        self._tmpdir  = tempfile.TemporaryDirectory()
        self._tmpfile = Path(self._tmpdir.name) / "jobs_history.json"

    def tearDown(self):
        self._tmpdir.cleanup()

    def _patch(self):
        return patch.object(app, "JOBS_HISTORY_FILE", self._tmpfile)

    def test_load_returns_empty_list_when_file_absent(self):
        with self._patch():
            result = app._load_jobs_history()
        self.assertEqual(result, [])

    def test_save_and_reload_roundtrip(self):
        items = [{"config": {"path": "/foo/bar"}, "status": "done", "output_dir": "/out"}]
        with self._patch():
            app._save_jobs_history(items)
            loaded = app._load_jobs_history()
        self.assertEqual(loaded, items)

    def test_save_multiple_and_reload(self):
        items = [{"id": i, "status": "done"} for i in range(5)]
        with self._patch():
            app._save_jobs_history(items)
            loaded = app._load_jobs_history()
        self.assertEqual(len(loaded), 5)
        self.assertEqual(loaded[2]["id"], 2)

    def test_save_trims_to_max_history(self):
        # Create MAX_HISTORY + 10 entries; only the last MAX_HISTORY should survive
        items = [{"id": i} for i in range(app.MAX_HISTORY + 10)]
        with self._patch():
            app._save_jobs_history(items)
            loaded = app._load_jobs_history()
        self.assertEqual(len(loaded), app.MAX_HISTORY)
        # The 10 oldest entries (ids 0–9) should have been trimmed
        self.assertEqual(loaded[0]["id"], 10)
        self.assertEqual(loaded[-1]["id"], app.MAX_HISTORY + 9)

    def test_load_returns_empty_list_on_corrupt_file(self):
        self._tmpfile.write_text("{{{{ not valid json at all")
        with self._patch():
            result = app._load_jobs_history()
        self.assertEqual(result, [])

    def test_save_writes_valid_json(self):
        items = [{"status": "done", "ts": "2025-01-01T00:00:00"}]
        with self._patch():
            app._save_jobs_history(items)
        raw = self._tmpfile.read_text()
        parsed = json.loads(raw)
        self.assertEqual(parsed, items)


# ---------------------------------------------------------------------------
# _load_custom_data() / _save_custom_data()
# ---------------------------------------------------------------------------

class TestCustomData(unittest.TestCase):
    """Tests for the custom-prompt persistence helpers."""

    def setUp(self):
        self._tmpdir  = tempfile.TemporaryDirectory()
        self._tmpfile = Path(self._tmpdir.name) / "custom_prompts.json"

    def tearDown(self):
        self._tmpdir.cleanup()

    def _patch(self):
        return patch.object(app, "CUSTOM_PROMPTS_FILE", self._tmpfile)

    def test_load_returns_default_structure_when_file_absent(self):
        with self._patch():
            data = app._load_custom_data()
        self.assertEqual(data, {"label_overrides": {}, "custom_prompts": {}})

    def test_save_and_reload_roundtrip(self):
        payload = {
            "label_overrides": {"NEUTRAL_WHITE": "My Custom Label"},
            "custom_prompts": {
                "MY_KEY": {"label": "My Prompt", "text": "Do something nice."}
            },
        }
        with self._patch():
            app._save_custom_data(payload)
            loaded = app._load_custom_data()
        self.assertEqual(loaded, payload)

    def test_load_returns_default_on_corrupt_file(self):
        self._tmpfile.write_text("{{invalid json{{")
        with self._patch():
            data = app._load_custom_data()
        self.assertEqual(data, {"label_overrides": {}, "custom_prompts": {}})

    def test_save_writes_valid_json(self):
        payload = {"label_overrides": {}, "custom_prompts": {"K": {"label": "L", "text": "T"}}}
        with self._patch():
            app._save_custom_data(payload)
        raw    = self._tmpfile.read_text()
        parsed = json.loads(raw)
        self.assertEqual(parsed, payload)

    def test_save_pretty_prints_json(self):
        """Saved JSON should be indented for human readability."""
        with self._patch():
            app._save_custom_data({"label_overrides": {}, "custom_prompts": {}})
        raw = self._tmpfile.read_text()
        self.assertIn("\n", raw)  # indented JSON always contains newlines


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------

class TestRegistryIntegrity(unittest.TestCase):
    """Smoke tests ensuring the built-in prompt registry is internally consistent."""

    def test_all_builtin_keys_have_labels(self):
        for key in app._BUILTIN_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, app.PROMPT_LABELS)

    def test_all_builtin_keys_have_prompts(self):
        for key in app._BUILTIN_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, app.ALL_PROMPTS)

    def test_ordered_and_set_are_consistent(self):
        self.assertEqual(set(app._BUILTIN_KEYS_ORDERED), app._BUILTIN_KEYS)

    def test_no_duplicate_keys_in_ordered_list(self):
        self.assertEqual(len(app._BUILTIN_KEYS_ORDERED), len(set(app._BUILTIN_KEYS_ORDERED)))

    def test_max_history_is_positive(self):
        self.assertGreater(app.MAX_HISTORY, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
