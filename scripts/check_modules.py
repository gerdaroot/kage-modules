"""Static checks for the Kage module repository. Exits non-zero and lists every problem found."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement

ROOT = Path(__file__).resolve().parent.parent
KAGE_CREDIT = "Modified for Kage by gerdaroot"
# CC-BY-NC-ND (no derivatives): shipped byte-for-byte, so it can't carry the credit line
UNMODIFIED_COMMUNITY_FILES = {"temp_chat.py"}
LICENSE_HEADER = re.compile(r"licen[cs]ed? under|GNU|\bA?GPL|Creative Commons|MIT License", re.I)
HEADER_LINES = 40
# Same pattern Kage's loader uses; a line that doesn't match is silently ignored on install
KAGE_REQUIRES = re.compile(
    r"^\s*# ?requires:(?: ?)((?:{url} )*(?:{url}))\s*$".format(
        url=r"[-[\]_.~:/?#@!$&'()*+,;%<=>a-zA-Z0-9]+"
    )
)
REQUIRES_LINE = re.compile(r"^\s*#\s*requires:", re.I)
HENTAI_REQUIRED_MINOR_TAGS = {"marin-kitagawa", "rem"}


@dataclass
class ModuleInfo:
    path: Path
    name: str | None = None
    commands: set[str] = field(default_factory=set)


def module_files(root: Path = ROOT) -> list[Path]:
    return sorted([*root.glob("*.py"), *(root / "community").glob("*.py")])


def rel(path: Path) -> str:
    return f"community/{path.name}" if path.parent.name == "community" else path.name


def check_compiles(path: Path) -> list[str]:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except (SyntaxError, ValueError) as error:
        return [f"{rel(path)}: does not compile: {error}"]
    return []


def check_ruff(paths: list[Path], root: Path) -> list[str]:
    command = [sys.executable, "-m", "ruff", "check", "--no-cache", "--select", "F,E9"]
    try:
        result = subprocess.run(
            [*command, "--output-format", "concise", *map(str, paths)],
            capture_output=True,
            text=True,
            cwd=root,
        )
    except FileNotFoundError:
        return ["ruff: cannot run the Python interpreter"]
    if "No module named ruff" in result.stderr:
        return ["ruff is not installed: pip install ruff"]
    if result.returncode == 0:
        return []
    return [f"ruff: {line}" for line in result.stdout.splitlines() if ": " in line]


def read_catalog(catalog: Path) -> list[str]:
    lines = (line.strip() for line in catalog.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def check_catalog(entries: list[str], files: list[Path]) -> list[str]:
    listed = set(entries)
    on_disk = {rel(path).removesuffix(".py") for path in files}
    errors = [f"full.txt: duplicate entry {entry}" for entry in sorted(listed) if entries.count(entry) > 1]
    errors += [f"full.txt: {entry} has no {entry}.py" for entry in sorted(listed - on_disk)]
    errors += [f"{entry}.py: not listed in full.txt" for entry in sorted(on_disk - listed)]
    return errors


def is_loader_attr(node: ast.expr, attr: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == attr
        and isinstance(node.value, ast.Name)
        and node.value.id == "loader"
    )


def module_classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and any(is_loader_attr(base, "Module") for base in node.bases)
    ]


def strings_name(cls: ast.ClassDef) -> str | None:
    for node in cls.body:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "strings" for target in node.targets):
            continue
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            if isinstance(key, ast.Constant) and key.value == "name" and isinstance(value, ast.Constant):
                return value.value
    return None


def command_decorator(method: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.expr | None:
    for decorator in method.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if is_loader_attr(target, "command"):
            return decorator
    return None


def decorator_aliases(decorator: ast.expr) -> set[str]:
    if not isinstance(decorator, ast.Call):
        return set()
    aliases = set()
    for keyword in decorator.keywords:
        if keyword.arg not in {"alias", "aliases"}:
            continue
        values = keyword.value.elts if isinstance(keyword.value, (ast.List, ast.Tuple)) else [keyword.value]
        aliases |= {v.value.lower() for v in values if isinstance(v, ast.Constant) and isinstance(v.value, str)}
    return aliases


def class_commands(cls: ast.ClassDef) -> set[str]:
    """Mirrors kage.types.get_commands: `@loader.command` methods and legacy `*cmd` methods."""
    commands = set()
    for method in cls.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorator = command_decorator(method)
        if decorator is None and not method.name.endswith("cmd"):
            continue
        name = method.name.rsplit("cmd", 1)[0] if method.name.endswith("cmd") else method.name
        commands.add(name.lower())
        commands |= decorator_aliases(decorator) if decorator is not None else set()
    return commands


def inspect_module(path: Path, tree: ast.Module) -> tuple[ModuleInfo, list[str]]:
    info = ModuleInfo(path)
    classes = module_classes(tree)
    if not classes:
        return info, [f"{rel(path)}: no loader.Module subclass"]
    errors = []
    for cls in classes:
        name = strings_name(cls)
        if name is None:
            errors.append(f"{rel(path)}: {cls.name} has no strings['name']")
        info.name = info.name or name
        info.commands |= class_commands(cls)
    return info, errors


def check_duplicates(modules: list[ModuleInfo]) -> list[str]:
    names, commands = defaultdict(list), defaultdict(list)
    for module in modules:
        if module.name:
            names[module.name.casefold()].append(rel(module.path))
        for command in module.commands:
            commands[command].append(rel(module.path))
    errors = [f"module name {n!r} used by {', '.join(p)}" for n, p in sorted(names.items()) if len(p) > 1]
    errors += [f"command {c!r} defined in {', '.join(p)}" for c, p in sorted(commands.items()) if len(p) > 1]
    return errors


def check_community_header(path: Path, source: str) -> list[str]:
    errors = []
    if path.name not in UNMODIFIED_COMMUNITY_FILES and KAGE_CREDIT not in source:
        errors.append(f"{rel(path)}: missing '{KAGE_CREDIT}' line")
    header = [line for line in source.splitlines()[:HEADER_LINES] if line.lstrip().startswith("#")]
    if not any(LICENSE_HEADER.search(line) for line in header):
        errors.append(f"{rel(path)}: no license header in the first {HEADER_LINES} lines")
    return errors


def invalid_requirements(line: str) -> list[str]:
    match = KAGE_REQUIRES.match(line)
    if not match:
        return [line.strip()]
    bad = []
    for token in match[1].split():
        try:
            Requirement(token)
        except InvalidRequirement:
            bad.append(token)
    return bad


def check_requires(path: Path, source: str) -> list[str]:
    return [
        f"{rel(path)}:{number}: invalid pip requirement {token!r}"
        for number, line in enumerate(source.splitlines(), 1)
        if REQUIRES_LINE.match(line)
        for token in invalid_requirements(line)
    ]


def assigned_value(tree: ast.Module, name: str) -> ast.expr | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    return None


def names_in(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def strings_in(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def excluded_tags_iterables(tree: ast.Module) -> list[ast.expr]:
    """The <iter> of every `("ExcludedTags", tag) for tag in <iter>` comprehension."""
    iterables = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ListComp, ast.GeneratorExp)):
            continue
        element = node.elt
        if (
            isinstance(element, ast.Tuple)
            and element.elts
            and isinstance(element.elts[0], ast.Constant)
            and element.elts[0].value == "ExcludedTags"
        ):
            iterables += [generator.iter for generator in node.generators]
    return iterables


def check_hentai(path: Path, tree: ast.Module) -> list[str]:
    errors = []
    missing = HENTAI_REQUIRED_MINOR_TAGS - strings_in(assigned_value(tree, "MINOR_TAGS"))
    if missing:
        errors.append(f"{rel(path)}: MINOR_TAGS lost {sorted(missing)}")
    if "MINOR_TAGS" not in names_in(assigned_value(tree, "NSFW_EXCLUDED_TAGS")):
        errors.append(f"{rel(path)}: NSFW_EXCLUDED_TAGS no longer includes MINOR_TAGS")
    # waifu.im rejects comma lists, so each excluded tag must be its own query parameter
    if not any("NSFW_EXCLUDED_TAGS" in names_in(it) for it in excluded_tags_iterables(tree)):
        errors.append(f"{rel(path)}: NSFW request must send one ('ExcludedTags', tag) per NSFW_EXCLUDED_TAGS entry")
    return errors


def run_checks(root: Path = ROOT) -> tuple[list[str], int]:
    files = module_files(root)
    errors = [error for path in files for error in check_compiles(path)]
    errors += check_ruff(files, root)
    errors += check_catalog(read_catalog(root / "full.txt"), files)
    modules = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, str(path))
        except SyntaxError:
            continue
        info, module_errors = inspect_module(path, tree)
        modules.append(info)
        errors += module_errors + check_requires(path, source)
        if path.parent.name == "community":
            errors += check_community_header(path, source)
        if rel(path) == "hentai.py":
            errors += check_hentai(path, tree)
    errors += check_duplicates(modules)
    return errors, len(files)


def main() -> int:
    errors, checked = run_checks()
    for error in errors:
        print(f"error: {error}")
    print(f"{checked} modules checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
