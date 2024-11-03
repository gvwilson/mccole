"""McCole is a simple tool for creating static websites."""

from .build import build
from .lint import lint
from .stats import stats

__all__ = [
    "build",
    "lint",
    "stats",
]
