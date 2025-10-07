"""Command line utility for anonymising sensitive tokens in log files.

This module exposes a small CLI that scans a source directory for files,
applies a collection of regular-expression based rules, and writes sanitized
copies of the files to an output directory.  The implementation focuses on
testability, readability and observability to make future changes easier.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Iterator, List, Pattern


LOGGER = logging.getLogger(__name__)


def configure_logging(verbosity: int) -> None:
    """Configure a basic logging setup for the CLI."""

    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


@dataclass(frozen=True)
class SanitizerRule:
    """A compiled sanitization rule backed by a regular expression."""

    description: str
    pattern: Pattern[str]

    def scrub(self, value: str, placeholder: str, maintain_length: bool) -> str:
        """Apply the rule to the provided value and return the sanitized text."""

        def _replacement(match: re.Match[str]) -> str:
            matched_text = match.group(0)
            if not maintain_length:
                return placeholder

            if len(placeholder) == 1:
                return placeholder * len(matched_text)

            # When the placeholder is more than one character we tile it so the
            # replacement roughly maintains the input length while remaining
            # easy to recognise.
            repetitions, remainder = divmod(len(matched_text), len(placeholder))
            return (placeholder * repetitions) + placeholder[:remainder]

        return self.pattern.sub(_replacement, value)


@dataclass(frozen=True)
class SanitizerConfig:
    """Configuration required to anonymise log files."""

    source_dir: Path
    output_dir: Path
    rules_file: Path
    ignore_file: Path | None
    placeholder: str = "*"
    maintain_length: bool = True


class LogSanitizer:
    """Encapsulates the logic for anonymising files based on regex rules."""

    def __init__(self, config: SanitizerConfig) -> None:
        self.config = config
        self.rules = self._load_rules(config.rules_file)
        self.ignore_patterns = (
            self._load_ignore_patterns(config.ignore_file)
            if config.ignore_file is not None
            else []
        )

    @staticmethod
    def _load_rules(rules_path: Path) -> List[SanitizerRule]:
        if not rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_path}")

        rules: List[SanitizerRule] = []
        for idx, line in enumerate(rules_path.read_text().splitlines(), start=1):
            rule_text = line.strip()
            if not rule_text or rule_text.startswith("#"):
                continue

            try:
                pattern = re.compile(rule_text)
            except re.error as exc:  # pragma: no cover - defensive branch
                raise ValueError(
                    f"Invalid regex on line {idx} of {rules_path}: {exc}"
                ) from exc

            rules.append(SanitizerRule(description=rule_text, pattern=pattern))

        if not rules:
            raise ValueError(f"No sanitization rules found in {rules_path}")

        LOGGER.info("Loaded %d sanitization rules", len(rules))
        return rules

    @staticmethod
    def _load_ignore_patterns(ignore_path: Path | None) -> List[str]:
        if ignore_path is None or not ignore_path.exists():
            return []

        patterns: List[str] = []
        for line in ignore_path.read_text().splitlines():
            token = line.strip()
            if not token or token.startswith("#"):
                continue
            patterns.append(token)

        LOGGER.info("Loaded %d ignore patterns", len(patterns))
        return patterns

    def source_files(self) -> Iterator[Path]:
        """Yield files from the source directory that are not ignored."""

        for path in sorted(self.config.source_dir.rglob("*")):
            if not path.is_file():
                continue

            if self._is_ignored(path):
                LOGGER.debug("Ignoring file %s", path)
                continue

            yield path

    def _is_ignored(self, path: Path) -> bool:
        if not self.ignore_patterns:
            return False

        from fnmatch import fnmatch

        relative = path.relative_to(self.config.source_dir)
        for pattern in self.ignore_patterns:
            if fnmatch(str(relative), pattern) or fnmatch(path.name, pattern):
                return True
        return False

    def sanitise(self) -> None:
        """Sanitize every file in the source directory."""

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        for source_path in self.source_files():
            destination = self.config.output_dir / source_path.relative_to(
                self.config.source_dir
            )
            destination.parent.mkdir(parents=True, exist_ok=True)

            LOGGER.info("Processing %s", source_path)
            content = source_path.read_text(encoding="utf-8", errors="ignore")
            sanitized_content = self._sanitise_file(content)
            destination.write_text(sanitized_content, encoding="utf-8")

    def _sanitise_file(self, content: str) -> str:
        result = content
        for rule in self.rules:
            original = result
            result = rule.scrub(
                result,
                placeholder=self.config.placeholder,
                maintain_length=self.config.maintain_length,
            )
            if original != result:
                LOGGER.debug("Applied rule: %s", rule.description)
        return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("source"),
        help="Directory containing files to sanitise",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results"),
        help="Directory to write anonymised files to",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("main.rule"),
        help="Path to the rules file",
    )
    parser.add_argument(
        "--ignore",
        type=Path,
        default=Path("ignore.list"),
        help="File containing glob patterns for files to ignore",
    )
    parser.add_argument(
        "--placeholder",
        default="*",
        help="Replacement token for detected matches",
    )
    parser.add_argument(
        "--strip-length",
        action="store_true",
        help="Do not maintain the original match length when replacing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -vv for debug)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    configure_logging(args.verbose)

    ignore_file = args.ignore if args.ignore.exists() else None
    config = SanitizerConfig(
        source_dir=args.source,
        output_dir=args.output,
        rules_file=args.rules,
        ignore_file=ignore_file,
        placeholder=args.placeholder,
        maintain_length=not args.strip_length,
    )

    sanitizer = LogSanitizer(config)
    sanitizer.sanitise()


if __name__ == "__main__":
    main()
