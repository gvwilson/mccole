r'''McCole is a simple tool for creating static websites.
'''

from .lint import lint
from .render import render
from .stats import stats

__all__ = [
    'lint',
    'render',
    'stats',
]
