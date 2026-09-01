"""Behavioural tests for the two scripts that can change what the repo publishes.

Run with `python -m unittest discover tests`. Stdlib only, so CI needs nothing
installed to run them.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import textwrap
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


class InstallerFlattensCategories(unittest.TestCase):
    """install.sh is the executable surface a reader is told to run."""

    SCRIPT = ROOT / "scripts" / "install.sh"

    def run_install(self, *args):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        return target, __import__("subprocess").run(
            ["bash", str(self.SCRIPT), str(target), *args],
            capture_output=True, text=True,
        )

    def test_symlink_install_flattens_every_skill_one_level_deep(self):
        target, result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {f"ml4t-{p.parent.name}" for p in ROOT.glob("*/*/SKILL.md")}
        self.assertEqual({d.name for d in target.iterdir()}, expected)
        for directory in target.iterdir():
            self.assertTrue(directory.is_symlink())
            self.assertTrue((directory / "SKILL.md").is_file())

    def test_copy_install_does_not_depend_on_the_checkout(self):
        target, result = self.run_install("--copy")
        self.assertEqual(result.returncode, 0, result.stderr)
        one = next(target.iterdir())
        self.assertFalse(one.is_symlink())
        self.assertTrue((one / "SKILL.md").is_file())

    def test_rerunning_over_its_own_install_is_a_no_op(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        run = __import__("subprocess").run
        first = run(["bash", str(self.SCRIPT), str(target)], capture_output=True, text=True)
        second = run(["bash", str(self.SCRIPT), str(target)], capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("installed 0 skills", second.stdout)
        self.assertIn("already current", second.stdout)
        self.assertIn("installed 61 skills", first.stdout)

    def test_a_taken_name_fails_the_run_instead_of_reporting_success(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        squatted = target / "ml4t-data-leakage"
        squatted.mkdir(parents=True)
        result = __import__("subprocess").run(
            ["bash", str(self.SCRIPT), str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ml4t-data-leakage", result.stderr)
        self.assertEqual(list(squatted.iterdir()), [])  # the existing directory is untouched

    def test_rerunning_a_copy_install_refreshes_it_instead_of_conflicting(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        run = __import__("subprocess").run
        argv = ["bash", str(self.SCRIPT), str(target), "--copy"]
        run(argv, capture_output=True, text=True, check=True)
        stale = target / "ml4t-data-leakage" / "SKILL.md"
        stale.write_text("name: ml4t-data-leakage\nstale\n")
        second = run(argv, capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotIn("conflict", second.stderr)
        self.assertIn("61 replaced", second.stdout)
        self.assertEqual(
            stale.read_text(),
            (ROOT / "concepts" / "data-leakage" / "SKILL.md").read_text(),
        )
        self.assertEqual([p for p in target.iterdir() if p.name.startswith(".")], [])

    def test_a_symlink_install_replaces_an_earlier_copy_install(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        run = __import__("subprocess").run
        run(["bash", str(self.SCRIPT), str(target), "--copy"],
            capture_output=True, text=True, check=True)
        result = run(["bash", str(self.SCRIPT), str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((target / "ml4t-data-leakage").is_symlink())

    def test_a_foreign_directory_using_our_prefix_is_still_a_conflict(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        squatted = target / "ml4t-data-leakage"
        squatted.mkdir(parents=True)
        (squatted / "SKILL.md").write_text("name: someone-elses-skill\n")
        result = __import__("subprocess").run(
            ["bash", str(self.SCRIPT), str(target), "--copy"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual((squatted / "SKILL.md").read_text(), "name: someone-elses-skill\n")

    def test_an_unknown_option_is_refused(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        result = __import__("subprocess").run(
            ["bash", str(self.SCRIPT), str(target), "--wipe"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown option", result.stderr)


class RepositoryShapeIsEnforced(unittest.TestCase):
    def tree(self, *skills: tuple[str, ...]) -> Path:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        for parts in skills:
            directory = tmp.joinpath(*parts)
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("---\n---\n")
        return tmp

    def discover(self, root: Path):
        errors: list = []
        skills = validate.discover_skills(root, errors)
        return skills, [e.message for e in errors]

    def test_a_skill_nested_too_deep_is_reported(self):
        root = self.tree(("category", "alpha"), ("category", "group", "beta"))
        skills, messages = self.discover(root)
        self.assertEqual([p.parent.name for p in skills], ["alpha"])
        self.assertEqual(messages, ["SKILL.md must live at <category>/<skill>/SKILL.md"])

    def test_duplicate_names_across_categories_are_reported(self):
        root = self.tree(("data", "alpha"), ("features", "alpha"))
        _, messages = self.discover(root)
        self.assertEqual(messages, ["duplicate skill name, also at data/alpha"])

    def test_a_well_shaped_tree_reports_nothing(self):
        root = self.tree(("data", "alpha"), ("features", "beta"))
        skills, messages = self.discover(root)
        self.assertEqual([p.parent.name for p in skills], ["alpha", "beta"])
        self.assertEqual(messages, [])

    def test_hidden_directories_are_ignored(self):
        root = self.tree(("data", "alpha"), (".worktrees", "copy", "alpha"))
        skills, messages = self.discover(root)
        self.assertEqual([p.parent.name for p in skills], ["alpha"])
        self.assertEqual(messages, [])


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


class ExportsAreModuleLevel(unittest.TestCase):
    """A name only counts as an export if `from module import name` would work."""

    def exports(self, source: str) -> set[str]:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        module = tmp / "m.py"
        module.write_text(textwrap.dedent(source))
        return validate.exported_names(module)

    def test_a_method_is_not_an_export(self):
        exports = self.exports("""
            class Broker:
                def submit(self):
                    helper = 1
                    return helper
        """)
        self.assertIn("Broker", exports)
        self.assertNotIn("submit", exports)
        self.assertNotIn("helper", exports)

    def test_a_function_local_import_is_not_an_export(self):
        exports = self.exports("""
            def build():
                from decimal import Decimal
                return Decimal
        """)
        self.assertIn("build", exports)
        self.assertNotIn("Decimal", exports)

    def test_a_conditional_module_level_import_is_an_export(self):
        exports = self.exports("""
            try:
                from m.inner import DataManager
            except ImportError:
                DataManager = None
        """)
        self.assertIn("DataManager", exports)

    def test_all_extended_after_a_literal_assignment_still_exports_both(self):
        exports = self.exports("""
            __all__ = ["ContractSpec"]
            try:
                from m.core import DataManager
                __all__.extend(["DataManager"])
            except ImportError:
                pass
        """)
        self.assertEqual({"ContractSpec", "DataManager"}, exports & {"ContractSpec", "DataManager"})


class QuotedFrontmatterKeysAreNormalized(unittest.TestCase):
    def test_a_quoted_banned_key_is_still_rejected(self):
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        skill = tmp / "concepts" / "widget"
        skill.mkdir(parents=True)
        source = (ROOT / "concepts" / "data-leakage" / "SKILL.md").read_text()
        source = source.replace(
            "name: ml4t-data-leakage", 'name: ml4t-widget\n"category": concepts')
        (skill / "SKILL.md").write_text(source)
        errors: list = []
        validate.validate_skill(skill / "SKILL.md", {"widget"}, errors)
        self.assertTrue(any("banned frontmatter field: category" in e.message for e in errors),
                        [e.message for e in errors])
