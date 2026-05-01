"""Install files needed for building sites."""

import importlib.resources
from pathlib import Path
import sys


_REQUIRED_FILES = {
    Path("README.md"): "",
    Path("LICENSE.md"): "# License\n",
    Path("CODE_OF_CONDUCT.md"): "# Code of Conduct\n",
    Path("glossary/index.md"): "# Glossary\n",
    Path("bibliography/index.md"): "# Bibliography\n",
}


def create(options):
    """Main driver."""
    src = importlib.resources.files(__name__.split(".")[0]) / "data"
    available = {
        filename: options.dst / filename.relative_to(src)
        for filename in src.glob("**/*")
        if filename.is_file()
    }
    if options.only:
        available = {
            filename: path
            for filename, path in available.items()
            if filename.relative_to(src) in options.only
        }

    exists = {str(dst) for dst in available.values() if dst.exists()}
    if exists and (not options.force):
        print(
            f"not overwriting {', '.join(sorted(exists))} (use --force)",
            file=sys.stderr,
        )
        sys.exit(1)

    options.dst.mkdir(parents=True, exist_ok=True)
    for src, dst in available.items():
        if options.verbose > 0:
            print(f"… {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    for rel, content in _REQUIRED_FILES.items():
        dst = options.dst / rel
        if not dst.exists():
            if options.verbose > 0:
                print(f"… {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
