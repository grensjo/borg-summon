from unittest.mock import Mock, MagicMock, patch, call, DEFAULT
import sh
import click
import os
import sys
import glob
from click.testing import CliRunner
from borg_summon import command_line, config_parser

from locale import getpreferredencoding
DEFAULT_ENCODING = getpreferredencoding() or "utf-8"

minimal_config = {
    'archive_name': 'archive_name',
    'remotes': {
        'remote_a': {
            'location': 'remote_location_a/'
        },
        'remote_b': {
            'location': 'remote_location_b/'
        },
    },
    'backup': {
        'sources': {
            'source_A': {
                'paths': ['pathA1', 'pathA2']
            },
            'source_B': {
                'paths': ['pathB1', 'pathB2']
            }
        }
    }
}

maximal_config = {
    'archive_name': 'archive_name',
    'remote_list': ['remote_a', 'remote_b'],
    'sudo': True,
    'ssh_command': 'ssh_command',
    'passphrase': 'passphrase1',
    'secret': {
        'remote_b': {
            'source_B': {
                'passphrase': 'passphrase2'
            }
        }
    },
    'log_level': 'info',
    'umask': "0007",
    'remote_borg_path': 'remote_borg_path',
    'encryption': 'repokey',
    'append_only': True,
    'progress': True,
    'stats': True,
    'exclude_file': 'exclude_file',
    'exclude_caches': True,
    'one_file_system': True,
    'compression': 'lz4',
    'remotes': {
        'remote_a': {
            'location': 'remote_location_a/',
        },
        'remote_b': {
            'location': 'remote_location_b/',
        },
    },
    'backup': {
        'sources': {
            'source_A': {
                'paths': ['pathA1', 'pathA2'],
                'pre_create_hook': { 'command': 'pre-create-A.sh', 'sudo': False },
                'post_create_hook': { 'command': 'post-create-A.sh' },
            },
            'source_B': {
                'paths': ['pathB1', 'pathB2'],
                'remote_list': ['remote_b'],
                'sudo_user': 'user_b',
                'pre_create_hook': { 'command': 'pre-create-B.sh', 'args': ['--verbose'] },
                'post_create_hook': { 'command': 'post-create-B.sh', 'sudo_user': 'hook_user' },
            }
        }
    }
}

def mock_default_config(config):
    config_parser.get_from_default = MagicMock(return_value=config)

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
                    print("No match because of missing option", arg)
                    return False
            else:
                if arg[2:eqpos] in options and options[arg[2:eqpos]] == arg[(eqpos+1):]:
                    del options[arg[2:eqpos]]
                else:
                    print("No match because of missing option", arg)
                    return False
        else:
            if args[0] == arg:
                del args[0]
            else:
                print("No match because of missing option", arg)
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
@patch('os.spawnve', return_value=0)
def test_backup_init_minimal(borg_mock):
    # Set up
    mock_default_config(minimal_config)
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
    assert os.spawnve.call_count == 4
    assert result.exit_code == 0



@mock_path
@patch('os.spawnve', return_value=0)
def test_backup_init_maximal(spawnve):
    # Set up
    mock_default_config(maximal_config)
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

    assert os.spawnve.call_count == 3
    assert result.exit_code == 0

@mock_path
@patch('os.spawnve', return_value=0)
def test_backup_create_minimal(borg_mock):
    # Set up
    mock_default_config(minimal_config)
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
    assert os.spawnve.call_count == 4
    assert result.exit_code == 0

@mock_path
@patch('os.spawnve', return_value=0)
def test_backup_create_maximal(borg_mock):
    # TODO verify order of hook executions

    # Set up
    mock_default_config(maximal_config)
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
    assert os.spawnve.call_count == 7
    assert result.exit_code == 0
