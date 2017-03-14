import collections

def lookup(table, keys, default=None):
    current = table
    for key in keys:
        if not isinstance(current, collections.Mapping) or key not in current:
            return default

        current = current[key]
    return current
