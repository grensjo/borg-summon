import pytest
from unittest.mock import patch
from borg_summon import config_parser
from .util import mock_globbing, mock_multiple_opens

def test_merge():
    d1 = {
            'a': 'a',
            'b': {
                'c': 'c',
                'd': [1, 2, 3],
                'e': [1, 2, 3],
            },
            'c': {
                'd': 3,
            },
            'd': 3,
        }
    d2 = {
            'b': {
                'c': 'C',
                'd': [3, 4, 5],
                'e': 0,
            },
            'c': 0,
            'd': 'd',
            'g': 'g',
        }
    res = {
            'a': 'a',
            'b': {
                'c': 'C',
                'd': [1, 2, 3, 3, 4, 5],
                'e': 0,
            },
            'c': 0,
            'd': 'd',
            'g': 'g',
        }

    config_parser.merge(d1, d2)
    assert str(d1) == str(res)


def test_cyclic_include():
    mock_globbing()
    m_open = mock_multiple_opens([
        'include = ["b.toml"]',
        'include = ["c.toml"]',
        'include = ["a.toml"]',
        'include = ["b.toml"]',
        ])
    with patch('borg_summon.config_parser.open', m_open, create=True):
        with pytest.raises(config_parser.CyclicIncludeError) as excinfo:
            config_parser.get_from_file('a.toml')
        assert 'includes itself' in str(excinfo.value)


@patch('logging.warning')
def test_multiple_include(warning):
    mock_globbing()
    m_open = mock_multiple_opens([
        'include = ["b.toml", "c.toml"]',
        'include = ["d.toml"]',
        'log_level = "info"',
        'include = ["d.toml"]',
        'log_level = "info"',
        ])
    with patch('borg_summon.config_parser.open', m_open, create=True):
        config_parser.get_from_file('a.toml')
        assert warning.call_count == 1
        assert 'included multiple times' in str(warning.mock_calls[0])
