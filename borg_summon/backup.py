import click
import glob
import sys
import sh
import os.path
from datetime import datetime
from collections import ChainMap
from . import borg


@click.command()
@click.argument('sources', nargs=-1)
@click.pass_obj
def main(config, sources):
    command_config = ChainMap(config['backup']['create'], config) #TODO defaults

    if len(sources) == 0:
        sources = config['backup']['sources'].keys()

    for source_name in sources:
        source_config = command_config.new_child(config['backup']['sources'][source_name])
        repo_name = source_config.get('repo_name', source_name)
        
        if 'remote_list' in source_config:
            remote_list = source_config['remote_list']
        else:
            remote_list = config['remotes'].keys()

        for remote in remote_list:
            remote_config = source_config.new_child(config['remotes'][remote])

            date = str(datetime.now().isoformat(timespec='seconds'))
            archive = remote_config['archive_name'].format(datetime=date)

            print("Backing up the source", source_name, "to the remote", remote)
            borg.create(remote_config, remote, repo_name, archive)
