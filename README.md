# logAnon

`logAnon` is a small command line utility that anonymises sensitive tokens in
log files.  It scans a source directory, applies a list of regular expression
rules, and writes sanitised copies of the files to an output directory.

## Features

- Configurable source and output directories.
- Regex-driven replacement rules loaded from an external file.
- Optional ignore list that accepts glob patterns (e.g. `*.gz` or
  `**/debug.log`).
- Ability to either maintain the original character length of matches or to
  replace them with a fixed placeholder.
- Verbose logging to observe which files and rules are used during execution.

## Getting started

1. Create a Python virtual environment (optional but recommended) and install
   the project if you plan to package it.  The script itself has no external
   dependencies.
2. Populate the `source/` directory with the log files you want to anonymise.
3. Copy `main.example` to `main.rule` and edit it so that it contains one regular
   expression per line. Lines starting with `#` are treated as comments.
4. Update `ignore.list` with any file patterns that should be skipped.  The file
   accepts glob-style patterns and comments.
5. Run the script:

   ```bash
   python main.py --source source --output results --rules main.rule \
       --ignore ignore.list
   ```

   Use `-v` or `-vv` for additional logging.

## Command line options

```
usage: python main.py [-h] [--source SOURCE] [--output OUTPUT] [--rules RULES]
                      [--ignore IGNORE] [--placeholder PLACEHOLDER]
                      [--strip-length] [-v]
```

- `--source`: Directory containing files to sanitise (defaults to `source`).
- `--output`: Directory to write anonymised files to (defaults to `results`).
- `--rules`: Path to the rules file (defaults to `main.rule`).
- `--ignore`: Path to the ignore list containing glob patterns (defaults to
  `ignore.list`).
- `--placeholder`: Replacement token used when a rule matches (defaults to `*`).
- `--strip-length`: When supplied the replacement token is used once instead of
  matching the length of the detected text.
- `-v` / `-vv`: Increase logging verbosity.

## Development

- The codebase targets Python 3.11+ and prefers standard library tooling.
- The `main.py` module is structured to be testable; the `LogSanitizer`
  component can be imported and used directly from other Python code.
- Automated coverage lives under `tests/` and can be executed with `pytest`.
- Future improvements might include:
  - Packaging the CLI with an entry point for easier installation.
  - A streaming mode for processing very large files without loading them fully
    into memory.

## License

The original repository did not specify a license.  Add one if distribution is
required.
