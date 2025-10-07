import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import (
    LogSanitizer,
    SanitizerConfig,
    SanitizerRule,
    configure_logging,
    main,
    parse_args,
)


def _write_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path

def test_sanitizer_rule_scrub_maintains_length():
    rule = SanitizerRule(description=r"\\d+", pattern=re.compile(r"\d+"))
    value = "Order 12345 shipped"

    # Maintain length should return same number of characters as matched
    maintained = rule.scrub(value, placeholder="*", maintain_length=True)
    assert maintained == "Order ***** shipped"

    # Without maintaining length the placeholder should be inserted literally
    stripped = rule.scrub(value, placeholder="REDACTED", maintain_length=False)
    assert stripped == "Order REDACTED shipped"


def test_load_rules_and_ignore(tmp_path: Path):
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()

    rules_file = _write_file(
        tmp_path / "rules.txt",
        """
        # comment line
        \\d+
        [A-Z]{2,}
        """.strip(),
    )
    ignore_file = _write_file(tmp_path / "ignore.list", "secrets.log\n")

    _write_file(source_dir / "log.txt", "ID 12345 NAME BOB")
    _write_file(source_dir / "secrets.log", "Should never be processed")

    sanitizer = LogSanitizer(
        SanitizerConfig(
            source_dir=source_dir,
            output_dir=output_dir,
            rules_file=rules_file,
            ignore_file=ignore_file,
            placeholder="X",
            maintain_length=True,
        )
    )

    sanitizer.sanitise()

    # Ignored file should not be copied
    assert not (output_dir / "secrets.log").exists()

    result = (output_dir / "log.txt").read_text(encoding="utf-8")
    assert result == "XX XXXXX XXXX XXX"


def test_load_rules_requires_entries(tmp_path: Path):
    rules_file = _write_file(tmp_path / "rules.txt", "# only comments")

    with pytest.raises(ValueError):
        LogSanitizer._load_rules(rules_file)


def test_parse_args_defaults():
    args = parse_args([])
    assert args.source == Path("source")
    assert args.output == Path("results")
    assert args.rules == Path("main.rule")
    assert args.ignore == Path("ignore.list")
    assert args.placeholder == "*"
    assert args.strip_length is False
    assert args.verbose == 0


def test_main_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    source = tmp_path / "src"
    output = tmp_path / "dst"
    rules = _write_file(tmp_path / "rules.txt", "email@example.com")
    ignore = _write_file(tmp_path / "ignore.list", "ignored.txt")

    source.mkdir()
    _write_file(source / "file.txt", "Contact email@example.com for details")
    _write_file(source / "ignored.txt", "Should not appear")

    argv = [
        "--source",
        str(source),
        "--output",
        str(output),
        "--rules",
        str(rules),
        "--ignore",
        str(ignore),
        "--placeholder",
        "[redacted]",
        "--strip-length",
    ]

    configure_logging(verbosity=0)
    main(argv)

    out = (output / "file.txt").read_text(encoding="utf-8")
    assert out == "Contact [redacted] for details"
    assert not (output / "ignored.txt").exists()

