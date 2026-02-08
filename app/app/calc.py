"""
Caculator module
"""


def add(x, y):
    """Return the sum of x and y."""
    return x + y


def subtract(x, y):
    """subtract y from x and return the result."""
    return y - x


def divide(x, y):
    """Divide x by y and return the result. Raises ValueError if y is 0."""
    if y == 0:
        raise ValueError("Cannot divide by zero")
    return x / y
