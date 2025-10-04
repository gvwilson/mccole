"""Install files needed for building sites."""

import importlib.resources
import sys


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
