"""Behavioural tests for the two scripts that can change what the repo publishes.

Run with `python -m unittest discover tests`. Stdlib only, so CI needs nothing
installed to run them.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def live(markdown: str) -> str:
    """Drop every backslash-escaped character, leaving only markup that still acts."""
    return re.sub(r"\\.", "", markdown)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


offerings = load(ROOT / ".github" / "scripts" / "update_offerings.py", "update_offerings")
validate = load(ROOT / "scripts" / "validate_skills.py", "validate_skills")


class ScrapedFieldsAreNeutralised(unittest.TestCase):
    """The Maven profile is third-party input committed without review."""

    def test_title_cannot_close_the_link_it_sits_in(self):
        hostile = "Free Session](https://evil.example/phish) and ["
        escaped = offerings.text(hostile)
        self.assertNotIn("](", live(escaped))
        self.assertIn(r"\]", escaped)

    def test_title_cannot_break_out_of_a_table_cell(self):
        self.assertNotIn("|", live(offerings.text("Risk | Reward")))

    def test_title_cannot_inject_raw_html(self):
        escaped = live(offerings.text("<img src=x onerror=alert(1)>"))
        self.assertNotIn("<", escaped)
        self.assertNotIn(">", escaped)

    def test_title_newlines_collapse(self):
        self.assertEqual(offerings.text("two\n\nlines"), "two lines")

    def test_ordinary_titles_are_left_alone(self):
        title = "Machine Learning for Trading: From Research to Production"
        self.assertEqual(offerings.text(title), title)

    def test_slug_that_would_redirect_the_url_is_refused(self):
        for hostile in ("../../evil", "a/b", "x?next=y", "", None, 7):
            with self.subTest(slug=hostile), self.assertRaises(SystemExit):
                offerings.slug(hostile, "test")

    def test_ordinary_slug_passes_through(self):
        self.assertEqual(offerings.slug("research-to-production", "test"), "research-to-production")

    def test_duration_must_be_a_plausible_number(self):
        self.assertEqual(offerings.minutes(30), 30)
        for junk in ("30", None, True, -1, 0, 10_000):
            with self.subTest(value=junk):
                self.assertIsNone(offerings.minutes(junk))

    def test_a_hostile_title_survives_rendering_without_escaping_the_cell(self):
        lesson = {
            "title": offerings.text("Session](https://evil.example) |"),
            "url": "https://maven.com/p/abc123",
            "start": datetime(2030, 1, 2, 17, 0, tzinfo=UTC),
            "minutes": 30,
        }
        rendered = offerings.render_all([lesson], [])
        row = live(next(line for line in rendered.splitlines() if "maven.com/p/abc123" in line))
        self.assertEqual(row.count("|"), 3)  # leading, separator, trailing
        self.assertEqual(row.count("]("), 1)  # exactly one live link, ours
        self.assertIn("](https://maven.com/p/abc123)", row)


class SplicePreservesEscaping(unittest.TestCase):
    """render() escapes, but splice() is what actually reaches the README."""

    README = "before\n<!-- offerings:t start -->\nold\n<!-- offerings:t end -->\nafter\n"

    def spliced(self, title: str) -> str:
        body = f"| [{offerings.text(title)}](https://maven.com/p/abc123) | 30 min |"
        out = offerings.splice(self.README, "t", body)
        return next(line for line in out.splitlines() if "maven.com/p/abc123" in line)

    def test_a_backslash_in_the_title_does_not_reopen_the_link(self):
        # A literal backslash escapes to \\; a string replacement collapses that
        # back to \, which re-arms the ] the escaping had just neutralised.
        row = live(self.spliced(r"Bootcamp\](https://evil.example) ["))
        self.assertEqual(row.count("]("), 1)
        self.assertIn("](https://maven.com/p/abc123)", row)
        self.assertNotIn("evil.example)", live(row).split("](")[1])

    def test_group_references_are_not_expanded(self):
        row = self.spliced(r"Session \g<0> and \1")
        self.assertIn(r"\g\<0\>", row)
        self.assertNotIn("maven.com/p/abc123 and", row)

    def test_ordinary_title_is_unchanged_by_the_splice(self):
        self.assertIn("| [Deep Dive](https://maven.com/p/abc123) | 30 min |",
                      self.spliced("Deep Dive"))


class BannedFrontmatterFieldsAreRejected(unittest.TestCase):
    def check(self, frontmatter: str) -> list[str]:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        directory = tmp / "category" / "alpha"
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text(
            f"---\n{frontmatter}---\n\n# Alpha\n\n### WRONG\n\n### CORRECT\n\n"
            "## Guardrails\n\n## Checklist\n\n- [ ] done\n"
        )
        errors: list = []
        validate.validate_skill(directory / "SKILL.md", {"alpha"}, errors)
        return [e.message for e in errors]

    BASE = ('name: ml4t-alpha\ndescription: Does a thing. Use when needed.\n'
            'dependencies: []\nmetadata:\n  book_chapters: "7"\n')

    def test_each_banned_field_is_caught(self):
        for banned in ("quantlab_module", "category", "type"):
            with self.subTest(banned=banned):
                messages = self.check(self.BASE + f"{banned}: whatever\n")
                self.assertIn(f"banned frontmatter field: {banned}", messages)

    def test_a_clean_skill_reports_no_banned_field(self):
        self.assertFalse([m for m in self.check(self.BASE) if "banned" in m])


class DependencyGraphIsAcyclic(unittest.TestCase):
    def test_the_repository_graph_has_no_cycle(self):
        skills = sorted(ROOT.glob("*/*/SKILL.md"))
        errors: list = []
        validate.validate_dependency_graph(skills, errors)
        self.assertEqual([e.message for e in errors], [])

    def test_a_cycle_is_reported(self):
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        for name, dep in (("alpha", "beta"), ("beta", "alpha")):
            directory = tmp / "category" / name
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text(
                f"---\nname: ml4t-{name}\ndependencies: [{dep}]\n---\nbody\n"
            )
        errors: list = []
        validate.validate_dependency_graph(sorted(tmp.glob("*/*/SKILL.md")), errors)
        self.assertTrue(any("dependency cycle" in e.message for e in errors))


if __name__ == "__main__":
    unittest.main()
