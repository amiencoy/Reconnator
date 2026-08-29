# ==================================================================================== #
# This validator enforces Reconnator's explanatory banner on Python and YAML files.   #
# CI exits with a readable file list when a tracked source or config omits the banner. #
# ==================================================================================== #

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


BANNER_PATTERN = re.compile(r"# ={20,} #")
CHECKED_SUFFIXES = {".py", ".yaml", ".yml"}


def tracked_files(repository_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    return sorted(
        repository_root / path
        for path in result.stdout.decode("utf-8").split("\0")
        if path and Path(path).suffix.lower() in CHECKED_SUFFIXES
    )


def has_feature_banner(path: Path) -> bool:
    with path.open(encoding="utf-8") as source:
        first_line = source.readline().rstrip("\r\n")
    return BANNER_PATTERN.fullmatch(first_line) is not None


def missing_banners(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if not has_feature_banner(path)]


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    missing = missing_banners(tracked_files(repository_root))
    if not missing:
        print("All tracked Python and YAML files contain a Reconnator feature banner.")
        return 0

    print("Missing Reconnator feature banner on the first line:", file=sys.stderr)
    for path in missing:
        print(f"  - {path.relative_to(repository_root)}", file=sys.stderr)
    print(
        "Expected a first line matching '# ==================== #'.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
