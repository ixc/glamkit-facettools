import re


def get_verbose_name(class_name):
    """
    Calculate the verbose_name by converting from InitialCaps to "lowercase
    with spaces".
    """
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name
    ).lower().strip()

def sort_by_count(a, b):
    """
    A cmp function that sorts by count (descending), then by name.
    """
    x = -cmp(a.count, b.count)
    if x == 0:
        return cmp(a.name, b.name)
    return x

def is_iterable(obj):
    """Checks if the object is a non-string sequence."""
    return hasattr(obj, '__iter__') and not isinstance(obj, basestring)
