"""Sample code for testing AST parser."""


def simple_function(x, y):
    """A simple function."""
    return x + y


def function_with_calls(a, b):
    """Function that calls other functions."""
    result = simple_function(a, b)
    return result * 2


def function_with_external_call():
    """Function that calls external library."""
    import os
    return os.path.exists("/tmp")


class Calculator:
    """Calculator class."""

    def add(self, x, y):
        """Add two numbers."""
        return x + y

    def multiply(self, x, y):
        """Multiply using add."""
        total = 0
        for _ in range(y):
            total = self.add(total, x)
        return total


async def async_function():
    """Async function."""
    return await some_async_call()


def recursive_function(n):
    """Recursive function."""
    if n <= 0:
        return 1
    return n * recursive_function(n - 1)
