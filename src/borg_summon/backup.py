import click
import glob
import sys
import sh
import os.path
from datetime import datetime
from collections import ChainMap
from . import borg, util


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

        for remote_name in remote_list:
            if len(remote) > 0 and remote_name not in remote:
                continue

            remote_config = source_config.new_child(config['remotes'][remote_name])

            if create:
                date = str(datetime.now().isoformat())
                archive = remote_config.get('archive_name', 'auto_{datetime}').format(datetime=date)

                print("Backing up the source", source_name, "to the remote", remote_name)
                borg.create(remote_config, remote_name, repo_name, archive)
            else:
                print("Initializing the repo", repo_name, "on the remote", remote_name)
                borg.init(remote_config, remote_name, repo_name)

