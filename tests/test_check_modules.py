import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_modules  # noqa: E402

LICENSE = "# Licensed under the GNU AGPLv3\n"
CREDIT = f"# {check_modules.KAGE_CREDIT} (https://github.com/gerdaroot/kage-modules)\n"


def module_source(name: str, body: str = "", header: str = "") -> str:
    return (
        f"{header}from .. import loader\n\n\n"
        f"class {name}Mod(loader.Module):\n"
        f'    strings = {{"name": "{name}"}}\n'
        f"{body}"
    )


def command(name: str, decorator: str = "@loader.command()") -> str:
    return f"\n    {decorator}\n    async def {name}(self, message):\n        pass\n"


@pytest.fixture
def repo(tmp_path):
    def build(files: dict[str, str]) -> list[str]:
        for relative, source in files.items():
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        catalog = [relative.removesuffix(".py") for relative in files]
        (tmp_path / "full.txt").write_text("\n".join(catalog) + "\n", encoding="utf-8")
        errors, _ = check_modules.run_checks(tmp_path)
        return errors

    return build


def test_real_repository_is_clean():
    errors, checked = check_modules.run_checks()
    assert errors == []
    assert checked > 0


def test_clean_minimal_repo(repo):
    assert repo({"one.py": module_source("One", command("one"))}) == []


def test_syntax_error_is_reported(repo):
    errors = repo({"broken.py": module_source("Broken", "    def x(:\n")})
    assert any("broken.py: does not compile" in error for error in errors)


def test_undefined_name_is_reported_by_ruff(repo):
    errors = repo({"typo.py": module_source("Typo", command("typo").replace("pass", "utils.answer(message)"))})
    assert any(error.startswith("ruff:") and "utils" in error for error in errors)


def test_catalog_mismatch(repo, tmp_path):
    repo({"a.py": module_source("A")})
    (tmp_path / "full.txt").write_text("a\nghost\n", encoding="utf-8")
    (tmp_path / "b.py").write_text(module_source("B"), encoding="utf-8")
    errors, _ = check_modules.run_checks(tmp_path)
    assert "full.txt: ghost has no ghost.py" in errors
    assert "b.py: not listed in full.txt" in errors


def test_missing_module_class_and_name(repo):
    errors = repo(
        {
            "plain.py": "x = 1\n",
            "nameless.py": "from .. import loader\n\n\nclass NamelessMod(loader.Module):\n    strings = {}\n",
        }
    )
    assert "plain.py: no loader.Module subclass" in errors
    assert "nameless.py: NamelessMod has no strings['name']" in errors


def test_duplicate_module_names_and_commands(repo):
    errors = repo(
        {
            "a.py": module_source("Same", command("dl", '@loader.command(alias="get")')),
            "b.py": module_source("same", command("getcmd", "@staticmethod")),
        }
    )
    assert "module name 'same' used by a.py, b.py" in errors
    assert "command 'get' defined in a.py, b.py" in errors


def test_community_headers(repo):
    errors = repo(
        {
            "community/no_credit.py": module_source("NoCredit", header=LICENSE),
            "community/no_license.py": module_source("NoLicense", header=CREDIT),
            "community/temp_chat.py": module_source("TmpChats", header=LICENSE),
            "community/good.py": module_source("Good", header=LICENSE + CREDIT),
        }
    )
    assert errors == [
        f"community/no_credit.py: missing '{check_modules.KAGE_CREDIT}' line",
        "community/no_license.py: no license header in the first 40 lines",
    ]


@pytest.mark.parametrize(
    ("line", "is_valid"),
    [
        ("# requires: Pillow requests", True),
        ("# requires: yt-dlp[default,curl-cffi]", True),
        ("# requires: speedtest-cli>=2.1", True),
        ("# requires: Pillow, requests", False),
        ("# requires: foo==", False),
        ("# requires:", False),
    ],
)
def test_requires_lines(line, is_valid):
    errors = check_modules.check_requires(Path("m.py"), f"{line}\n")
    assert (errors == []) is is_valid


HENTAI_OK = module_source(
    "Hentai",
    header=(
        'MINOR_TAGS = frozenset({"marin-kitagawa", "rem", "loli"})\n'
        'NSFW_EXCLUDED_TAGS = MINOR_TAGS | {"uniform"}\n'
    ),
    body=(
        "\n    def params(self):\n"
        '        return [("ExcludedTags", t) for t in sorted(NSFW_EXCLUDED_TAGS)]\n'
    ),
)


def test_hentai_guards_pass(repo):
    assert repo({"hentai.py": HENTAI_OK}) == []


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('"rem", ', "", "MINOR_TAGS lost ['rem']"),
        ("MINOR_TAGS | ", "", "NSFW_EXCLUDED_TAGS no longer includes MINOR_TAGS"),
        (
            '[("ExcludedTags", t) for t in sorted(NSFW_EXCLUDED_TAGS)]',
            '[("ExcludedTags", ",".join(NSFW_EXCLUDED_TAGS))]',
            "NSFW request must send one",
        ),
    ],
)
def test_hentai_guards_fail(repo, old, new, message):
    errors = repo({"hentai.py": HENTAI_OK.replace(old, new)})
    assert any(message in error for error in errors)
