r'''McCole is a simple tool for creating static websites.
'''

from .lint import lint
from .render import render

__all__ = [
    'lint',
    'render',
]
