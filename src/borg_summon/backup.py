import click
import glob
import sys
import sh
import os.path
from datetime import datetime
from collections import ChainMap
from . import borg, util
from .report import ActionSuccess, ActionFailure, report_success, report_failure, send_report


@click.command()
@click.option('-s', '--source', multiple=True)
@click.option('-r', '--remote', multiple=True)
@click.option('--create/--init', default=True)
@click.pass_obj
def main(config, source, remote, create):
    if create:
        command_config = ChainMap(util.lookup(config, ['backup', 'create'], {}), config)
    else:
        command_config = ChainMap(util.lookup(config, ['backup', 'init'], {}), config)

    source_list = config['backup']['sources'].keys()

    for source_name in source_list:
        if len(source) > 0 and source_name not in source:
            continue

        source_config = command_config.new_child(config['backup']['sources'][source_name])
        repo_name = source_config.get('repo_name', source_name)
        
        if 'remote_list' in source_config:
            remote_list = source_config['remote_list']
        else:
            remote_list = config['remotes'].keys()

        if len(remote) > 0:
            remote_list = filter(lambda r: r in remote, remote_list)

        if len(remote_list) == 0:
            continue

        if create and 'pre_create_hook' in source_config:
            hook_config = source_config.new_child(source_config['pre_create_hook'])

            print("\n")
            print("Running pre-create-hook for source", source_name)
            try:
                borg.hook(hook_config)
                report_success(ActionSuccess('pre-create-hook', (source_name,)))
            except Exception as e:
                report_failure(ActionFailure('pre-create-hook', (source_name,), e))
                for remote_name in remote_list:
                    report_failure(ActionFailure('create', (source_name, remote_name), 'skipped because of failed pre-create-hook'))
                report_failure(ActionFailure('post-create-hook', (source_name,), 'skipped because of failed pre-create-hook'))
                continue

        for remote_name in remote_list:
            remote_config = source_config.new_child(config['remotes'][remote_name])

            if create:
                date = str(datetime.now().isoformat())
                archive = remote_config.get('archive_name', 'auto_{datetime}').format(datetime=date)

                print("\n")
                print("Backing up the source", source_name, "to the remote", remote_name)
                try:
                    borg.create(remote_config, remote_name, repo_name, archive)
                    report_success(ActionSuccess('create', (source_name, remote_name)))
                except Exception as e:
                    report_failure(ActionFailure('create', (source_name, remote_name), e))
            else:
                print("\n")
                print("Initializing the repo", repo_name, "on the remote", remote_name)
                try:
                    borg.init(remote_config, remote_name, repo_name)
                    report_success(ActionSuccess('init', (source_name, remote_name)))
                except Exception as e:
                    report_failure(ActionFailure('init', (source_name, remote_name), e))


        if create and 'post_create_hook' in source_config:
            hook_config = source_config.new_child(source_config['post_create_hook'])
            print("\n")
            print("Running post-create-hook for source", source_name)
            try:
                borg.hook(hook_config)
                report_success(ActionSuccess('post_create_hook', (source_name,)))
            except Exception as e:
                report_failure(ActionFailure('post-create-hook', (source_name,), e))
