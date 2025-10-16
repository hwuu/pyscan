"""Example of buggy Python code for testing."""


def divide_numbers(a, b):
    """Divide two numbers."""
    return a / b  # Bug: No check for division by zero


def get_first_element(lst):
    """Get first element from list."""
    return lst[0]  # Bug: No check for empty list


def process_data(data):
    """Process data dictionary."""
    result = data['value'] * 2  # Bug: No check if 'value' key exists
    return result


def unsafe_file_read(filename):
    """Read file without error handling."""
    f = open(filename, 'r')  # Bug: File not closed, no error handling
    content = f.read()
    return content


def infinite_loop_risk(n):
    """Potentially infinite loop."""
    while n > 0:
        print(n)
        # Bug: n is never decremented, infinite loop!
