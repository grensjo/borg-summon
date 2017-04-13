from unittest.mock import patch
from borg_summon import report, backup, borg
import logging


@patch('borg_summon.backup.report_failure')
@patch('borg_summon.backup.report_success')
@patch('borg_summon.borg.hook')
@patch('borg_summon.borg.create')
@patch('borg_summon.borg.init')
def test_filter_source_remote_do_nothing(init, create, hook, report_success, report_failure):
    # Setup
    arg_config = {
            'backup': {
                'sources': {
                    's1': {
                        'paths': ['/home'],
                    },
                    's2': {
                        'paths': ['/etc'],
                        'remote_list': [],
                    },
                }
            }
        }
    arg_source = ['s2']
    arg_remote = []
    arg_create = True

    # Perform
    backup.main_inner(arg_config, arg_source, arg_remote, arg_create)

    # Assert
    assert init.call_count == 0
    assert create.call_count == 0
    assert hook.call_count == 0
    assert report_success.call_count == 0
    assert report_failure.call_count == 0


@patch('borg_summon.backup.report_failure')
@patch('borg_summon.backup.report_success')
@patch('borg_summon.borg.hook')
@patch('borg_summon.borg.create')
@patch('borg_summon.borg.init')
def test_filter_remote_call_create_error(init, create, hook, report_success, report_failure):
    # Setup
    arg_config = {
            'backup': {
                'sources': {
                    's1': {
                        'paths': ['/home'],
                    },
                }
            },
            'remotes': {
                'r1': { 'location': 'path1' },
                'r2': { 'location': 'path2' },
            }
        }
    arg_source = []
    arg_remote = ['r2']
    arg_create = True
    create.side_effect = Exception()

    # Perform
    backup.main_inner(arg_config, arg_source, arg_remote, arg_create)

    # Assert
    assert init.call_count == 0
    assert create.call_count == 1
    assert create.call_args[0][1] == 'r2'
    assert create.call_args[0][2] == 's1'
    assert hook.call_count == 0
    assert report_success.call_count == 0
    assert report_failure.call_count == 1
    assert report_failure.call_args[0][0].action == 'create'
    assert report_failure.call_args[0][0].target == ('s1', 'r2')


@patch('borg_summon.backup.report_failure')
@patch('borg_summon.backup.report_success')
@patch('borg_summon.borg.hook')
@patch('borg_summon.borg.create')
@patch('borg_summon.borg.init')
def test_init_error(init, create, hook, report_success, report_failure):
    # Setup
    arg_config = {
            'backup': {
                'sources': {
                    's1': {
                        'paths': ['/home'],
                    },
                }
            },
            'remotes': {
                'r1': { 'location': 'path1' },
            }
        }
    arg_source = []
    arg_remote = []
    arg_create = False
    init.side_effect = Exception()

    # Perform
    backup.main_inner(arg_config, arg_source, arg_remote, arg_create)

    # Assert
    assert init.call_count == 1
    assert init.call_args[0][1] == 'r1'
    assert init.call_args[0][2] == 's1'
    assert create.call_count == 0
    assert hook.call_count == 0
    assert report_success.call_count == 0
    assert report_failure.call_count == 1
    assert report_failure.call_args[0][0].action == 'init'
    assert report_failure.call_args[0][0].target == ('s1', 'r1')


@patch('borg_summon.backup.report_failure')
@patch('borg_summon.backup.report_success')
@patch('borg_summon.borg.hook')
@patch('borg_summon.borg.create')
@patch('borg_summon.borg.init')
def test_pre_create_hook_error(init, create, hook, report_success, report_failure):
    # Setup
    arg_config = {
            'backup': {
                'sources': {
                    's1': {
                        'paths': ['/home'],
                        'pre_create_hook': { 'command': 'true' },
                        'post_create_hook': { 'command': 'true' },
                    },
                    's2': {
                        'paths': ['/home'],
                    },
                }
            },
            'remotes': {
                'r1': { 'location': 'path1' },
            },
        }
    arg_source = []
    arg_remote = []
    arg_create = True
    hook.side_effect = [Exception(), None]

    # Perform
    backup.main_inner(arg_config, arg_source, arg_remote, arg_create)

    # Assert
    assert init.call_count == 0
    assert create.call_count == 1
    assert hook.call_count == 1
    assert report_success.call_count == 1
    assert report_failure.call_count == 3


@patch('borg_summon.backup.report_failure')
@patch('borg_summon.backup.report_success')
@patch('borg_summon.borg.hook')
@patch('borg_summon.borg.create')
@patch('borg_summon.borg.init')
def test_post_create_hook_error(init, create, hook, report_success, report_failure):
    # Setup
    arg_config = {
            'backup': {
                'sources': {
                    's1': {
                        'paths': ['/home'],
                    },
                }
            },
            'remotes': {
                'r1': { 'location': 'path1' },
            },
            'pre_create_hook': { 'command': 'true' },
            'post_create_hook': { 'command': 'true' },
        }
    arg_source = []
    arg_remote = []
    arg_create = True
    hook.side_effect = [None, Exception]

    # Perform
    backup.main_inner(arg_config, arg_source, arg_remote, arg_create)

    # Assert
    assert init.call_count == 0
    assert create.call_count == 1
    assert hook.call_count == 2
    assert report_success.call_count == 2
    assert report_failure.call_count == 1
