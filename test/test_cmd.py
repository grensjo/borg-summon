from unittest.mock import Mock, MagicMock, patch, call, DEFAULT, mock_open
import toml
import itertools
import sh
import click
import os
import sys
import glob
from click.testing import CliRunner
from borg_summon import command_line, config_parser

from locale import getpreferredencoding
DEFAULT_ENCODING = getpreferredencoding() or "utf-8"


def mock_default_config(config_name):
    with open(os.path.join(os.path.dirname(__file__), 'configs', config_name), 'r') as f:
        m = mock_open(read_data=f.read())
    def generate_open_empty():
        while True:
            yield mock_open(read_data='').return_value
    m.side_effect = itertools.chain([m.return_value], generate_open_empty())
    
    def decorator(func):
        @patch('borg_summon.config_parser.open', m)
        def func_wrapper(*args, **kwargs):
            func(*args, **kwargs)
        return func_wrapper
    return decorator

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

def call_matches(call, args, options, env):
    cname, cargs, ckwargs = call
    options = options.copy()
    args = args.copy()

    cargs = list(cargs)
    cargs[1] = cargs[1].decode(DEFAULT_ENCODING)
    cargs[2] = list(map(lambda a: a.decode(DEFAULT_ENCODING), cargs[2]))
    print("Match?", cargs, args)

    if not cargs[0] == os.P_WAIT:
        return False

    if not cargs[1] == args[0]:
        print("No match because of command name")
        return False

    if not cargs[3] == env:
        print("No match because of environment")
        return False

    for arg in cargs[2]:
        if arg.startswith('--'):
            eqpos = arg.find('=')
            if eqpos == -1:
                if arg[2:] in options and options[arg[2:]] == True:
                    del options[arg[2:]]
                else:
                    print("No match because of missing option A", arg)
                    return False
            else:
                if arg[2:eqpos] in options and options[arg[2:eqpos]] == arg[(eqpos+1):]:
                    del options[arg[2:eqpos]]
                else:
                    print("No match because of missing option B", arg)
                    return False
        else:
            if len(args) > 0 and args[0] == arg:
                del args[0]
            else:
                print("No match because of missing option C", arg)
                return False

    if len(args) == 0 and len(options) == 0:
        return True
    else:
        print("No match because of not empty")
        return False

def any_call_matches(mock, args, options, env):
    for call in mock.mock_calls:
        if call_matches(call, args, options, env):
            return True
    return False


def test_root_command_help():
    runner = CliRunner()
    result = runner.invoke(command_line.main, ['--help'])
    assert result.exit_code == 0

def test_root_backup_help():
    runner = CliRunner()
    result = runner.invoke(command_line.main, ['backup', '--help'])
    assert result.exit_code == 0

def test_root_maintain_help():
    runner = CliRunner()
    result = runner.invoke(command_line.main, ['maintain', '--help'])
    assert result.exit_code == 0


@mock_path
@mock_default_config('minimal.toml')
@patch('os.spawnve', return_value=0)
def test_backup_init_minimal(borg_mock):
    # Set up
    runner = CliRunner()

    # Perform
    result = runner.invoke(command_line.main, ['backup', '--init'], catch_exceptions=False)

    # Assert
    assert any_call_matches(os.spawnve,
            ['/path/borg', 'init', 'remote_location_a/source_A'], {}, {})
    assert any_call_matches(os.spawnve,
            ['/path/borg', 'init', 'remote_location_a/source_B'], {}, {})
    assert any_call_matches(os.spawnve,
            ['/path/borg', 'init', 'remote_location_b/source_A'], {}, {})
    assert any_call_matches(os.spawnve,
            ['/path/borg', 'init', 'remote_location_b/source_B'], {}, {})
    # assert os.spawnve.call_count == 4
    assert result.exit_code == 0



@mock_path
@mock_default_config('maximal.toml')
@patch('os.spawnve', return_value=0)
def test_backup_init_maximal(spawnve):
    # Set up
    runner = CliRunner()

    # Perform
    result = runner.invoke(command_line.main, ['backup', '--init'], catch_exceptions=False)

    # Assert
    env = {
        'BORG_RSH': 'ssh_command',
        'BORG_PASSPHRASE': 'passphrase1',
        'BORG_DISPLAY_PASSPHRASE': 'n',
    }
    kwargs = {
        'append-only': True,
        'encryption': 'repokey',
        'info':True,
        'remote-path': 'remote_borg_path',
        'umask': '0007',
    }

    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '/path/borg', 'init',
            'remote_location_a/source_A'], kwargs, env)

    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '/path/borg', 'init',
            'remote_location_b/source_A'], kwargs, env)

    env['BORG_PASSPHRASE'] = 'passphrase2'
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '-u', 'user_b', '/path/borg', 'init',
            'remote_location_b/source_B'], kwargs, env)

    # assert os.spawnve.call_count == 3
    assert result.exit_code == 0

@mock_path
@mock_default_config('minimal.toml')
@patch('os.spawnve', return_value=0)
def test_backup_create_minimal(borg_mock):
    # Set up
    mock_globbing()
    runner = CliRunner()

    # Perform
    result = runner.invoke(command_line.main, ['backup'], catch_exceptions=False)

    # Assert
    assert any_call_matches(os.spawnve, ['/path/borg', 'create',
        'remote_location_a/source_A::archive_name', 'pathA1', 'pathA2'], {}, {})
    assert any_call_matches(os.spawnve, ['/path/borg', 'create',
        'remote_location_a/source_B::archive_name', 'pathB1', 'pathB2'], {}, {})
    assert any_call_matches(os.spawnve, ['/path/borg', 'create',
        'remote_location_b/source_A::archive_name', 'pathA1', 'pathA2'], {}, {})
    assert any_call_matches(os.spawnve, ['/path/borg', 'create',
        'remote_location_b/source_B::archive_name', 'pathB1', 'pathB2'], {}, {})
    # assert os.spawnve.call_count == 4
    assert result.exit_code == 0

@mock_path
@mock_default_config('maximal.toml')
@patch('os.spawnve', return_value=0)
def test_backup_create_maximal(borg_mock):
    # TODO verify order of hook executions

    # Set up
    mock_globbing()
    runner = CliRunner()

    # Perform
    result = runner.invoke(command_line.main, ['backup', '--create'], catch_exceptions=False)

    # Assert
    env = {
        'BORG_RSH': 'ssh_command',
        'BORG_PASSPHRASE': 'passphrase1',
        'BORG_DISPLAY_PASSPHRASE': 'n',
    }
    kwargs = {
        'info': True,
        'remote-path': 'remote_borg_path',
        'umask': '0007',
        'stats': True,
        'progress': True,
        'exclude-from': 'exclude_file',
        'exclude-caches': True,
        'one-file-system': True,
        'compression': 'lz4',
    }


    assert any_call_matches(os.spawnve, ['/path/pre-create-A.sh'], {}, {})
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '/path/borg', 'create',
        'remote_location_a/source_A::archive_name', 'pathA1', 'pathA2'], kwargs, env)
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '/path/borg', 'create',
        'remote_location_b/source_A::archive_name', 'pathA1', 'pathA2'], kwargs, env)
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '/path/post-create-A.sh'], {}, {})

    env['BORG_PASSPHRASE'] = 'passphrase2'
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '-u', 'user_b', '/path/pre-create-B.sh'], {'verbose': True}, {})
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '-u', 'user_b', '/path/borg', 'create',
        'remote_location_b/source_B::archive_name', 'pathB1', 'pathB2'], kwargs, env)
    assert any_call_matches(os.spawnve, ['/path/sudo', '-S', '-u', 'hook_user', '/path/post-create-B.sh'], {}, {})
    # assert os.spawnve.call_count == 7
    assert result.exit_code == 0
