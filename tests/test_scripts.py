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

    def test_switching_an_install_from_symlinks_to_copies_takes_effect(self):
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        run = __import__("subprocess").run
        run(["bash", str(self.SCRIPT), str(target)], capture_output=True, text=True, check=True)
        result = run(["bash", str(self.SCRIPT), str(target), "--copy"],
                     capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("61 replaced", result.stdout)
        skill = target / "ml4t-data-leakage"
        self.assertFalse(skill.is_symlink())
        self.assertTrue((skill / ".ml4t-installed").is_file())

    def test_a_hand_copied_skill_is_never_deleted(self):
        # Same directory name, same `name:` frontmatter, plus local edits and no
        # installer marker. Only the marker may authorise a delete.
        target = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        mine = target / "ml4t-data-leakage"
        mine.mkdir(parents=True)
        source = (ROOT / "concepts" / "data-leakage" / "SKILL.md").read_text()
        (mine / "SKILL.md").write_text(source + "\n<!-- my notes -->\n")
        for argv in ([], ["--copy"]):
            result = __import__("subprocess").run(
                ["bash", str(self.SCRIPT), str(target), *argv],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("conflict: ml4t-data-leakage", result.stderr)
            self.assertTrue((mine / "SKILL.md").read_text().endswith("<!-- my notes -->\n"))

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

    def test_a_name_only_listed_in_all_is_not_an_export(self):
        # Listing a name in __all__ does not bind it. Trusting the list would
        # let a misspelled or removed library export pass the API check.
        exports = self.exports("""
            __all__ = ["ContractSpec", "Removed"]
            from m.contracts import ContractSpec
        """)
        self.assertIn("ContractSpec", exports)
        self.assertNotIn("Removed", exports)

    def test_a_type_checking_only_import_is_not_a_runtime_export(self):
        exports = self.exports("""
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from m.core import Frame
            else:
                Frame = object
        """)
        self.assertIn("Frame", exports)  # bound by the else branch
        exports = self.exports("""
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from m.core import Frame
        """)
        self.assertNotIn("Frame", exports)


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


class FrontmatterIsParsedAsYaml(unittest.TestCase):
    def fields(self, frontmatter: str):
        errors: list = []
        text = f"---\n{frontmatter}\n---\nbody\n"
        return validate.parse_frontmatter(Path("x/SKILL.md"), text, errors), errors

    def test_a_quoted_banned_key_is_still_the_banned_key(self):
        (fields, _), errors = self.fields('name: ml4t-x\n"category": concepts')
        self.assertEqual([], errors)
        self.assertIn("category", fields)

    def test_a_block_list_of_dependencies_is_accepted(self):
        (fields, _), errors = self.fields("dependencies:\n  - cpcv\n  - purging-embargo")
        self.assertEqual([], errors)
        self.assertEqual(["cpcv", "purging-embargo"], validate.parse_dependencies(
            fields["dependencies"]))

    def test_invalid_yaml_is_reported_rather_than_silently_reshaped(self):
        (_, _), errors = self.fields("name: [unclosed\ndescription: x")
        self.assertTrue(errors)
        self.assertIn("not valid YAML", errors[0].message)

    def test_a_folded_description_keeps_its_trigger_language(self):
        (fields, _), errors = self.fields("description: >\n  Do a thing.\n  Use when asked.")
        self.assertEqual([], errors)
        self.assertIn("Use when", validate.as_text(fields["description"]))

    def test_a_scalar_frontmatter_is_not_a_mapping(self):
        (fields, _), errors = self.fields("just a string")
        self.assertEqual({}, fields)
        self.assertIn("must be a mapping", errors[0].message)


class HiddenPathsAreNotSkills(unittest.TestCase):
    """install.sh globs with the shell, which never sees a dot-prefixed part."""

    def tree(self, *skills: str) -> Path:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        for rel in skills:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text("---\nname: x\n---\n")
        return tmp

    def discovered(self, root: Path) -> tuple[list[str], list[str]]:
        errors: list = []
        found = validate.discover_skills(root, errors)
        return ([p.relative_to(root).as_posix() for p in found],
                [e.message for e in errors])

    def test_a_hidden_category_is_neither_counted_nor_reported(self):
        found, errors = self.discovered(self.tree(
            "concepts/alpha/SKILL.md", ".drafts/beta/SKILL.md"))
        self.assertEqual(["concepts/alpha/SKILL.md"], found)
        self.assertEqual([], errors)

    def test_a_hidden_skill_directory_is_neither_counted_nor_reported(self):
        found, errors = self.discovered(self.tree(
            "concepts/alpha/SKILL.md", "concepts/.beta/SKILL.md"))
        self.assertEqual(["concepts/alpha/SKILL.md"], found)
        self.assertEqual([], errors)

    def test_the_shell_and_python_globs_agree_on_the_real_tree(self):
        errors: list = []
        found = {p.parent.name for p in validate.discover_skills(ROOT, errors)}
        shell = __import__("subprocess").run(
            ["bash", "-c", f'shopt -s nullglob; for s in "{ROOT}"/*/*/SKILL.md; '
             'do basename "$(dirname "$s")"; done'],
            capture_output=True, text=True, check=True)
        self.assertEqual(found, set(shell.stdout.split()))


class ReadmeCatalogListsEverySkill(unittest.TestCase):
    def test_the_real_catalog_links_each_skill_exactly_once(self):
        errors: list = []
        validate.validate_readme(sorted(ROOT.glob("*/*/SKILL.md")), errors)
        self.assertEqual([], [e.message for e in errors])

    def test_a_skill_missing_from_the_catalog_fails(self):
        errors: list = []
        missing = ROOT / "concepts" / "not-in-readme" / "SKILL.md"
        validate.validate_readme([*sorted(ROOT.glob("*/*/SKILL.md")), missing], errors)
        self.assertTrue(any("not-in-readme" in e.message for e in errors),
                        [e.message for e in errors])


class StaleInstallsAreOnlyRemovedOnRequest(unittest.TestCase):
    """A renamed or dropped skill leaves an install behind that no rerun rewrites."""

    SCRIPT = ROOT / "scripts" / "install.sh"

    def target(self) -> Path:
        return Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))

    def install(self, target: Path, *args):
        return __import__("subprocess").run(
            ["bash", str(self.SCRIPT), str(target), *args], capture_output=True, text=True)

    def stale(self, target: Path) -> tuple[list[Path], Path, Path]:
        """One leftover of each kind we own, plus one directory we do not."""
        links = [target / "ml4t-renamed-away", target / "ml4t-whole-category-gone"]
        # Neither target still exists, and the second lost its parent directory
        # too, so `readlink -f` cannot resolve it at all.
        links[0].symlink_to(ROOT / "concepts" / "renamed-away")
        links[1].symlink_to(ROOT / "retired" / "whole-category-gone")
        copied = target / "ml4t-dropped"
        copied.mkdir(parents=True)
        (copied / "SKILL.md").write_text("name: ml4t-dropped\n")
        (copied / ".ml4t-installed").write_text("installed by an older checkout\n")
        theirs = target / "ml4t-someone-elses"
        theirs.mkdir()
        (theirs / "SKILL.md").write_text("name: ml4t-someone-elses\n")
        return links, copied, theirs

    def test_a_plain_rerun_leaves_stale_installs_in_place(self):
        target = self.target()
        links, copied, theirs = self.stale(target)
        result = self.install(target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("pruned", result.stdout)
        for leftover in (*links, copied, theirs):
            self.assertTrue(leftover.exists() or leftover.is_symlink(), leftover)

    def test_prune_removes_our_stale_installs_and_keeps_the_current_ones(self):
        target = self.target()
        links, copied, theirs = self.stale(target)
        result = self.install(target, "--prune")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3 pruned", result.stdout)
        for link in links:
            self.assertFalse(link.is_symlink(), link)
        self.assertFalse(copied.exists())
        self.assertTrue(theirs.exists())  # no marker, no link: not ours to delete
        expected = {f"ml4t-{p.parent.name}" for p in ROOT.glob("*/*/SKILL.md")}
        self.assertEqual({d.name for d in target.iterdir()} - {theirs.name}, expected)

    def test_prune_never_touches_a_directory_outside_our_namespace(self):
        target = self.target()
        other = target / "unrelated-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("name: unrelated-skill\n")
        self.assertEqual(self.install(target, "--prune").returncode, 0)
        self.assertTrue((other / "SKILL.md").is_file())

    def test_uninstall_removes_every_skill_we_installed_and_nothing_else(self):
        target = self.target()
        self.install(target)
        _, _, theirs = self.stale(target)
        result = self.install(target, "--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("removed 64 skills", result.stdout)  # 61 shipped plus 3 stale
        self.assertEqual({d.name for d in target.iterdir()}, {theirs.name})

    def test_uninstall_after_a_copy_install_removes_the_copies_too(self):
        target = self.target()
        self.install(target, "--copy")
        self.assertEqual(self.install(target, "--uninstall").returncode, 0)
        self.assertEqual(list(target.iterdir()), [])

    def test_uninstalling_from_a_directory_we_never_touched_removes_nothing(self):
        target = self.target()
        result = self.install(target, "--uninstall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("removed 0 skills", result.stdout)

    def test_help_lists_every_documented_flag(self):
        result = __import__("subprocess").run(
            ["bash", str(self.SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ("--copy", "--prune", "--uninstall"):
            self.assertIn(flag, result.stdout)


class EveryWorkflowRunningTheValidatorInstallsItsParser(unittest.TestCase):
    """The validator imports PyYAML, which a clean setup-python runner does not have."""

    WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

    def jobs(self, text: str) -> list[str]:
        """Split a workflow into per-job text, so a step is checked against its own job."""
        return re.split(r"\n  (?=\w[\w-]*:\n)", text.split("\njobs:\n", 1)[1])

    def test_the_parser_is_installed_before_the_validator_runs(self):
        checked = 0
        for workflow in self.WORKFLOWS:
            for job in self.jobs(workflow.read_text()):
                if "scripts/validate_skills.py" not in job:
                    continue
                checked += 1
                install = job.find("pip install --quiet pyyaml")
                self.assertNotEqual(-1, install, f"{workflow.name}: no pyyaml install")
                self.assertLess(install, job.find("scripts/validate_skills.py"),
                                f"{workflow.name}: pyyaml is installed too late")
        self.assertGreater(checked, 1)  # both validate.yml and offerings.yml run it

    def test_the_validator_still_needs_the_parser(self):
        source = (ROOT / "scripts" / "validate_skills.py").read_text()
        self.assertIn("import yaml", source)  # if this ever goes, so can the checks above
