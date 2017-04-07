import click
import sys
import glob
from click.testing import CliRunner 
from borg_summon import command_line, config_parser
from unittest.mock import Mock, MagicMock, patch, call
import sh

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
            'sudo_user': 'user_b',
        },
    },
    'backup': {
        'sources': {
            'source_A': {
                'paths': ['pathA1', 'pathA2'],
            },
            'source_B': {
                'paths': ['pathB1', 'pathB2'],
                'remote_list': ['remote_b'],
            }
        }
    }
}

def mock_default_config(config):
    config_parser.get_from_default = MagicMock(return_value=config)

def mock_globbing():
    glob.glob = Mock(side_effect = lambda x: [x])

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

@patch('sh.borg', create=True)
def test_backup_init_minimal(borg_mock):
    # Set up
    mock_default_config(minimal_config)
    runner = CliRunner()

    # Perform
    result = runner.invoke(command_line.main, ['backup', '--init'], catch_exceptions=False)

    # Assert
    sh.borg.init.assert_has_calls([
            call('remote_location_a/source_A', _fg=True, _env={}),
            call('remote_location_a/source_B', _fg=True, _env={}),
            call('remote_location_b/source_A', _fg=True, _env={}),
            call('remote_location_b/source_B', _fg=True, _env={}),
        ], any_order=True)
    assert sh.borg.init.call_count == 4
    assert result.exit_code == 0

@patch('sh.borg', create=True)
def test_backup_init_maximal(borg_mock):
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
    sh.borg.init.assert_any_call('remote_location_a/source_A', _fg=True, _env=env, **kwargs)
    sh.borg.init.assert_any_call('remote_location_b/source_A', _fg=True, _env=env, **kwargs)
    env['BORG_PASSPHRASE'] = 'passphrase2'
    sh.borg.init.assert_any_call('remote_location_b/source_B', _fg=True, _env=env, **kwargs)
    assert sh.borg.init.call_count == 3
    assert result.exit_code == 0

@patch('sh.borg', create=True)
def test_backup_create_minimal(borg_mock):
    # Set up
    mock_default_config(minimal_config)
    mock_globbing()
    runner = CliRunner()
    
    # Perform
    result = runner.invoke(command_line.main, ['backup'], catch_exceptions=False)

    # Assert
    sh.borg.create.assert_has_calls([
            call('remote_location_a/source_A::archive_name', 'pathA1', 'pathA2', _fg=True, _env={}),
            call('remote_location_a/source_B::archive_name', 'pathB1', 'pathB2', _fg=True, _env={}),
            call('remote_location_b/source_A::archive_name', 'pathA1', 'pathA2', _fg=True, _env={}),
            call('remote_location_b/source_B::archive_name', 'pathB1', 'pathB2', _fg=True, _env={}),
        ], any_order=True)
    assert sh.borg.create.call_count == 4
    assert result.exit_code == 0

@patch('sh.borg', create=True)
def test_backup_create_maximal(borg_mock):
    # TODO: test sudo

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
    sh.borg.create.assert_any_call('remote_location_a/source_A::archive_name',
            'pathA1', 'pathA2', _fg=True, _env=env, **kwargs)
    sh.borg.create.assert_any_call('remote_location_b/source_A::archive_name',
            'pathA1', 'pathA2', _fg=True, _env=env, **kwargs)
    env['BORG_PASSPHRASE'] = 'passphrase2'
    sh.borg.create.assert_any_call('remote_location_b/source_B::archive_name',
            'pathB1', 'pathB2', _fg=True, _env=env, **kwargs)
    assert sh.borg.create.call_count == 3
    assert result.exit_code == 0
