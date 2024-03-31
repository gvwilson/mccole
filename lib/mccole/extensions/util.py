"""McCole template utilities."""

import sys


def allowed(kwargs, allowed):
    """Check that dictionary keys are a subset of those allowed."""
    return set(kwargs.keys()).issubset(allowed)


def fail(msg):
    """Fail unilaterally."""
    print(msg, file=sys.stderr)
    raise AssertionError(msg)


def require(cond, msg):
    """Fail if condition untrue."""
    if not cond:
        fail(msg)


