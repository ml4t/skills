#!/usr/bin/env python3
"""Validate ML4T skill repository structure and public-release hygiene."""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_LIBRARIES = {
    "",
    "ml4t-data",
    "ml4t-engineer",
    "ml4t-backtest",
    "ml4t-diagnostic",
    "ml4t-live",
}
FORBIDDEN_TRACKED_PATTERNS = (
    ".agents/",
    ".claude/",
    ".codex/",
    ".workspace/",
    ".idea/",
    ".mcp.json",
    "REVIEW_PROMPT.md",
    "SKILL_AUDIT.md",
    "VALIDATION_REPORT.md",
    "evals/",
    "reviews/",
)
SECRET_PATTERNS = re.compile(
    r"(github_pat|ghp_|sk-[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY)",
    re.IGNORECASE,
)


@dataclass
class Error:
    path: str
    message: str


def fail(errors: list[Error], path: Path | str, message: str) -> None:
    errors.append(Error(str(path), message))


def parse_frontmatter(path: Path, text: str, errors: list[Error]) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        fail(errors, path, "missing YAML frontmatter")
        return {}, text
    try:
        _, raw, body = text.split("---", 2)
    except ValueError:
        fail(errors, path, "malformed YAML frontmatter delimiters")
        return {}, text

    fields: dict[str, str] = {}
    in_metadata = False
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("metadata:"):
            fields["metadata"] = ""
            in_metadata = True
            continue
        if in_metadata and line.startswith("  "):
            key, sep, value = line.strip().partition(":")
            if sep:
                fields[f"metadata.{key}"] = value.strip().strip('"')
            continue
        in_metadata = False
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields, body


def parse_dependencies(value: str) -> list[str]:
    value = value.strip()
    if value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        return ["<parse-error>"]
    return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]


def validate_skill(path: Path, skill_names: set[str], errors: list[Error]) -> None:
    text = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(path, text, errors)
    directory_name = path.parent.name

    if len(text.splitlines()) > 120:
        fail(errors, path, "skill exceeds 120 lines")

    for field in ("name", "description", "dependencies", "metadata"):
        if field not in fields:
            fail(errors, path, f"missing frontmatter field: {field}")

    expected_name = f"ml4t-{directory_name}"
    if fields.get("name") != expected_name:
        fail(errors, path, f"name must be {expected_name!r}")

    description = fields.get("description", "")
    if "Use when" not in description:
        fail(errors, path, "description must include 'Use when' trigger language")

    for banned in ("quantlab_module", "category", "type"):
        if re.search(rf"^{banned}:", text.split("---", 2)[1] if text.startswith("---\n") else ""):
            fail(errors, path, f"banned frontmatter field: {banned}")

    for dependency in parse_dependencies(fields.get("dependencies", "[]")):
        if dependency == "<parse-error>" or dependency not in skill_names:
            fail(errors, path, f"unknown dependency: {dependency}")

    chapters = fields.get("metadata.book_chapters", "")
    if not chapters:
        fail(errors, path, "missing metadata.book_chapters")
    for chapter in [part.strip() for part in chapters.split(",") if part.strip()]:
        if not chapter.isdigit() or not 1 <= int(chapter) <= 27:
            fail(errors, path, f"invalid book chapter: {chapter}")

    library = fields.get("metadata.library", "")
    if library not in ALLOWED_LIBRARIES:
        fail(errors, path, f"unknown metadata.library: {library}")

    if not re.search(r"^### WRONG\s*$", text, flags=re.MULTILINE):
        fail(errors, path, "missing ### WRONG heading")
    if not re.search(r"^### CORRECT\s*$", text, flags=re.MULTILINE):
        fail(errors, path, "missing ### CORRECT heading")
    if "## Guardrails" not in text:
        fail(errors, path, "missing ## Guardrails section")
    if "## Checklist" not in text:
        fail(errors, path, "missing ## Checklist section")

    before_production = text.split("## Production Implementation", 1)[0]
    if re.search(r"^(from|import)\s+ml4t\.", before_production, flags=re.MULTILINE):
        fail(errors, path, "ml4t import appears before Production Implementation")

    blocks = re.findall(r"```python\n(.*?)```", body, flags=re.DOTALL)
    for index, block in enumerate(blocks, start=1):
        try:
            ast.parse(block)
        except SyntaxError as exc:
            fail(errors, path, f"python block {index} syntax error: line {exc.lineno}: {exc.msg}")

    if SECRET_PATTERNS.search(text):
        fail(errors, path, "potential secret-like token found")


def validate_dependency_graph(skills: list[Path], errors: list[Error]) -> None:
    """Reject cycles: an agent resolving `dependencies` transitively must terminate."""
    graph: dict[str, list[str]] = {}
    for path in skills:
        fields, _ = parse_frontmatter(path, path.read_text(encoding="utf-8"), [])
        graph[path.parent.name] = parse_dependencies(fields.get("dependencies", "[]"))

    state: dict[str, int] = {}
    reported: set[tuple[str, ...]] = set()

    def visit(node: str, stack: list[str]) -> None:
        state[node] = 1
        for child in graph.get(node, []):
            if state.get(child, 0) == 1:
                cycle = stack[stack.index(child):] + [child]
                if tuple(sorted(set(cycle))) not in reported:
                    reported.add(tuple(sorted(set(cycle))))
                    fail(errors, node, f"dependency cycle: {' -> '.join(cycle)}")
            elif state.get(child, 0) == 0 and child in graph:
                visit(child, stack + [child])
        state[node] = 2

    for name in sorted(graph):
        if state.get(name, 0) == 0:
            visit(name, [name])


def validate_readme(skill_count: int, errors: list[Error]) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")

    count_match = re.search(r"(\d+)\s+standalone skills", text)
    if not count_match:
        fail(errors, readme, "README must state skill count")
    elif int(count_match.group(1)) != skill_count:
        fail(errors, readme, f"README skill count does not match actual count {skill_count}")

    if "Machine Learning for Algorithmic Trading" not in text:
        fail(errors, readme, "README must reference the book")
    if "Apache-2.0" not in text:
        fail(errors, readme, "README must mention Apache-2.0")

    for _, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            continue
        if not (ROOT / target).exists():
            fail(errors, readme, f"broken relative link: {target}")


def validate_git_tracked_files(errors: list[Error]) -> None:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        return
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    for filename in result.stdout.splitlines():
        for pattern in FORBIDDEN_TRACKED_PATTERNS:
            if filename == pattern.rstrip("/") or filename.startswith(pattern):
                fail(errors, filename, "local/internal artifact must not be tracked")


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def exported_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def discover_ml4t_modules(library_root: Path) -> dict[str, Path]:
    """Map `ml4t.*` module names to source files under `library_root`.

    Two layouts are supported: a directory of `ml4t-*/src` checkouts, which is
    what a local development tree looks like, and a directory that holds the
    installed `ml4t/` namespace package directly, which is what CI gets from
    unpacking the published wheels.
    """
    roots = [(src, src) for src in sorted(library_root.glob("ml4t-*/src"))]
    if not roots and (library_root / "ml4t").is_dir():
        roots = [(library_root, library_root / "ml4t")]

    module_files: dict[str, Path] = {}
    for import_root, tree in roots:
        for path in sorted(tree.rglob("*.py")):
            module_files.setdefault(module_name(import_root, path), path)
    return module_files


def validate_ml4t_imports(skills: list[Path], library_root: Path, errors: list[Error]) -> None:
    module_files = discover_ml4t_modules(library_root)

    if not module_files:
        fail(errors, library_root, "no ml4t package source files found")
        return

    module_exports = {module: exported_names(path) for module, path in module_files.items()}
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        for block in re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL):
            try:
                tree = ast.parse(block)
            except SyntaxError:
                continue  # already reported against this file by validate_skill
            for node in ast.walk(tree):
                is_from_ml4t = isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                    "ml4t"
                )
                if is_from_ml4t:
                    if node.module not in module_files:
                        fail(errors, skill, f"unknown ml4t module: {node.module}")
                        continue
                    for alias in node.names:
                        if alias.name != "*" and alias.name not in module_exports[node.module]:
                            fail(errors, skill, f"unknown export {alias.name} from {node.module}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("ml4t") and alias.name not in module_files:
                            fail(errors, skill, f"unknown ml4t module: {alias.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library-root",
        type=Path,
        default=(
            Path(os.environ["ML4T_LIBRARY_ROOT"]) if "ML4T_LIBRARY_ROOT" in os.environ else None
        ),
        help="Path holding the ml4t library sources: either ml4t-*/src checkouts or an "
        "unpacked ml4t/ package. Enables the Production Implementation API check.",
    )
    args = parser.parse_args()

    errors: list[Error] = []
    skills = sorted(
        path
        for path in ROOT.rglob("SKILL.md")
        if not any(part.startswith(".") for part in path.relative_to(ROOT).parts)
    )
    skill_names = {path.parent.name for path in skills}

    if not skills:
        fail(errors, ROOT, "no SKILL.md files found")
    for path in skills:
        validate_skill(path, skill_names, errors)

    validate_dependency_graph(skills, errors)
    validate_readme(len(skills), errors)
    validate_git_tracked_files(errors)
    if args.library_root is not None:
        validate_ml4t_imports(skills, args.library_root, errors)

    if errors:
        for error in errors:
            print(f"{error.path}: {error.message}", file=sys.stderr)
        print(f"\nFAILED: {len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"OK: validated {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
