from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CR_DIR = ROOT / "docs" / "internal" / "cr"
TITLE_PREFIX = "# Change Request: "


def find_cr_file(cr_number: str, cr_dir: Path | None = None) -> Path:
    cr_dir = CR_DIR if cr_dir is None else cr_dir
    matches = sorted(cr_dir.glob(f"{cr_number}-*.md"))
    if not matches:
        raise SystemExit(f"No CR file found for CR-{cr_number} in {cr_dir}")
    if len(matches) != 1:
        names = ", ".join(path.name for path in matches)
        raise SystemExit(f"Expected exactly one CR file for CR-{cr_number}, found {len(matches)}: {names}")
    return matches[0]


def extract_cr_title(cr_path: Path) -> str:
    for line in cr_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(TITLE_PREFIX):
            title = line[len(TITLE_PREFIX):].strip()
            if not title:
                raise SystemExit(f"CR title line is empty in {cr_path}")
            return title
    raise SystemExit(f"Missing '{TITLE_PREFIX}' line in {cr_path}")


def build_commit_message(cr_number: str, title: str) -> str:
    return f"Implement CR-{cr_number}: {title}"


def confirm_commit() -> bool:
    response = input("Do you want to continue and commit? n (default) or Y: ").strip().lower()
    return response == "y"


def run_commit(cr_number: str, commit_message: str, cwd: Path = ROOT, yes: bool = False) -> int:
    print("---- CR SUBMITTER ---")
    print(
        f"- Ensure all and only files related to CR-{cr_number} are staged then run the following command (use 'git add -A' to add all)"
    )
    print(f'git commit -m "{commit_message}"')
    if not yes and not confirm_commit():
        print("exit witout commit")
        return 0
    completed = subprocess.run(["git", "commit", "-m", commit_message], cwd=str(cwd))
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Commit staged changes for a CR using the CR title")
    parser.add_argument("-y", "--yes", action="store_true", help="Run without interactive confirmation")
    parser.add_argument("cr_number", help="Three-digit CR number, for example 024")
    args = parser.parse_args(argv)

    if len(args.cr_number) != 3 or not args.cr_number.isdigit():
        print("CR number must be exactly three digits, for example 024", file=sys.stderr)
        return 2

    cr_path = find_cr_file(args.cr_number)
    title = extract_cr_title(cr_path)
    commit_message = build_commit_message(args.cr_number, title)
    return run_commit(args.cr_number, commit_message, yes=args.yes)


if __name__ == "__main__":
    raise SystemExit(main())