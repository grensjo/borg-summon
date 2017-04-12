import glob
import itertools
import os
from unittest.mock import Mock, patch, mock_open

def mock_globbing():
    glob.glob = Mock(side_effect = lambda x: [x])

def mock_path(func, path='/path'):
    isok = lambda *args: True
    orig_environ = os.environ.copy()
    def env_get(key, default=None):
        if key == 'PATH':
            return path
        else:
            return orig_environ.get(key, default)

    @patch('os.environ.get', side_effect=env_get)
    @patch('os.path.exists', side_effect=isok)
    @patch('os.access', side_effect=isok)
    @patch('os.path.isfile', side_effect=isok)
    def func_wrapper(isfile, access, exists, get, *args, **kwargs):
        func(*args, **kwargs)

    return func_wrapper

def mock_multiple_opens(it):
    def generate_open():
        for e in it:
            yield mock_open(read_data=e).return_value
    return Mock(side_effect = generate_open())
