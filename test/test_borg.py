import pytest
from borg_summon import borg

def test_hook_no_command():
    with pytest.raises(borg.InvalidConfigError) as excinfo:
        borg.hook({})
    assert str(excinfo.value) == 'The "command" option is required for hooks.'

def test_borg_invalid_log_level():
    with pytest.raises(borg.InvalidConfigError) as excinfo:
        borg.init({'log_level': 'null', 'location': 'location'}, 'remote', 'repo')
    assert 'not a legal log level' in str(excinfo.value)

def test_borg_no_location():
    with pytest.raises(borg.InvalidConfigError) as excinfo:
        borg.init({}, 'remote', 'repo')
    assert str(excinfo.value).startswith('No location specified for remote')

def test_borg_invalid_encryption():
    with pytest.raises(borg.InvalidConfigError) as excinfo:
        borg.init({'encryption': 'caesar', 'location': 'location'}, 'remote', 'repo')
    assert 'is not a valid encryption mode' in str(excinfo.value)

def test_borg_create_no_paths():
    with pytest.raises(borg.InvalidConfigError) as excinfo:
        borg.create({'location': 'location'}, 'remote', 'repo_name', 'archive_name')
    assert str(excinfo.value).startswith('There are no existing paths to backup')
