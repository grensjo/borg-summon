from collections import ChainMap

def get_prefix_dicts(root, keys):
    """Given a dict root and a list of keys, return a list of
    "prefix dicts". For example, if keys = ['a', 'b', 'c'], return
    [root,  root['a'], root['a']['b'], root['a']['b']['c'].
    """

    chain = [root]
    current = root
    for i in range(0, len(keys)):
        current = current[keys[i]]
        chain.append(current)
    return chain


def get_recursive_dict(root, keys):
    """Given a dict root and a list of keys, return a dict-like object,
    where lookups are made recursivly from the deepest key and "upwards".

    Example: Say that keys=['a', 'b'] and this function returns chain_map.
    Then, when looking up chain_map['x'], the following will be done:
    - if root['a']['b']['x'] exists return it, otherwise continue
    - if root['a']['x'] exists return it, otherwise continue
    - if root['x'] exists return it, otherwise fail
    """

    return ChainMap({}, *reversed(get_prefix_dicts(root, keys)))


def get_prioritized_recursive_dict(root, primary, secondary):
    """Given a dict root, and two lists of keys: primary and secondary,
    return an dict-like object similarly to get_recursive_dict, but
    which prioritizes values from the path in primary over values from
    the path in secondary.

    The dict can be thought of as a rooted tree. If you follow the sequence
    of keys in primary you get to the node A, and if you follow secondary 
    you get to the node B. Let C be the closest common ancestor to A and B.
    Then the prioritized recursive dict returned by this function will primarily
    search for a key in the path from A to C, secondarily in the path from B 
    to C, and if nothing else is found, in their common prefix from C up to
    the root.
    """

    primary_prefixes = get_prefix_dicts(root, primary)
    secondary_prefixes = get_prefix_dicts(root, secondary)
    
    for i, (prefix1, prefix2) in enumerate(zip(primary_prefixes, secondary_prefixes)):
        if prefix1 != prefix2:
            return ChainMap({}, *reversed(primary_prefixes[:i] + secondary_prefixes[i:]
                + primary_prefixes[i:]))

    if len(primary) > len(secondary):
        return get_recursive_dict(root, primary)
    else:
        return get_recursive_dict(root, secondary)
