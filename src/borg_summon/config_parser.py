import collections
import os.path
import glob
import logging
import toml

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class CyclicIncludeError(Error):
    """Exception raised when config file (by extension) is included by itself.

    Attributes:
        path -- path to one config file which includes itself
        message -- explanation of the error
    """

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'The config file "%s" includes itself.' % self.path


def merge(target, other):
    """Recursively deep merge dictionary other into dictionary target."""
    for key, value in other.items():
        if key in target:
            if (isinstance(other[key], collections.Mapping) and 
                    isinstance(target[key], collections.MutableMapping)):
                merge(target[key], other[key])
                continue
            elif (isinstance(other[key], collections.Sequence) and
                    isinstance(target[key], collections.Sequence)):
                # Strings are sequences, but we no not want to merge them.
                if not (isinstance(other[key], str) or isinstance(target[key], str)):
                    target[key] += other[key]
                    continue
        target[key] = other[key]


def get_from_default():
    """Get configuration from the default locations, which are:
    - /etc/borg-summon/config.toml
    - ~/.borg-summon/config.toml

    If both of these exist, values defined in ~/.borg-summon.toml override
    values defined in /etc/borg-summon.toml.
    """

    paths = ['/etc/borg-summon/config.toml', '~/.borg-summon/config.toml']
    config = {}
    visited = set()
    
    for path in paths:
        path = os.path.expanduser(path)
        if os.path.isfile(path):
            config = get_from_file(path, config, visited, [])

    return config

def get_from_file(path, config={}, visited=set(), current=[]):
    """Return a new config dict by reading from the given path.

    Keyword arguments:
    config  -- config dict to extend, and values read from file
               will override the ones in config
    visited -- the set of read paths so far in this invocation. Recursive calls
               will use the same instance
    current -- a list of the paths which we are currently processing. Recursive
               calls will use a copy
    """

    config = config.copy()
    current = current.copy()

    if path in current:
        raise CyclicIncludeError(path)
    elif path in visited:
        logging.warning('The file "%s" was included multiple times, but only the first occurrance was used.' % path)
        return config

    with open(os.path.expanduser(path)) as conffile:
        new_config = toml.loads(conffile.read())

    if "include" in new_config:
        includes = new_config["include"]
        del new_config['include']
    else:
        includes = []

    merge(config, new_config)

    visited.add(path)
    current.append(path)

    for include in includes:
        include = os.path.expanduser(include)
        for include_path in glob.glob(include):
            config = get_from_file(include_path, config, visited, current)
    
    return config
