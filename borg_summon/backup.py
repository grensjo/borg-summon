import click
import glob
import sys
import sh
import os.path
from datetime import datetime
from . import util


@click.command()
@click.argument('sources', nargs=-1)
@click.pass_obj
def main(global_config, sources):
    if len(sources) == 0:
        sources = global_config['backup']['sources'].keys()

    for name in sources:
        source_config = util.get_recursive_dict(global_config, ['backup', 'sources', name]) 
        
        if 'remote_list' in source_config:
            remote_list = source_config['remote_list']
        else:
            remote_list = global_config['remotes'].keys()

        for remote in remote_list:
            remote_config = util.get_prioritized_recursive_dict(global_config,
                    ['backup', 'sources', name], ['remotes', remote])

            # TODO: hooks
            cmd = ['create']


            if 'log_level' in remote_config:
                level = remote_config['log_level']
                if level in ('critical', 'error', 'warning', 'info', 'verbose'):
                    cmd.append('--' + level)
                else:
                    raise Exception # TODO

            if 'umask' in remote_config:
                cmd.append('--umask')
                cmd.append(remote_config['umask'])

            if 'remote_borg_path' in remote_config:
                cmd.append('--remote-path')
                cmd.append(remote_config['remote_borg_path'])

            if remote_config.get('stats', False):
                cmd.append('--stats')

            if remote_config.get('progress', False):
                cmd.append('--progress')

            if 'exclude_file' in remote_config:
                cmd.append('--exclude-from')
                cmd.append(remote_config['exclude_file'])

            if remote_config.get('exclude_caches', False):
                cmd.append('--exclude-caches')

            if remote_config.get('one_file_system', False):
                cmd.append('--one-file-system')

            if 'compression' in remote_config:
                cmd.append('--compression')
                cmd.append(remote_config['compression'])

            date = str(datetime.now().isoformat(timespec='seconds'))
            repo = remote_config['where'] + name
            archive = repo + "::" + remote_config['archive_name'].format(datetime=date)

            cmd.append(archive)
            cmd.extend(remote_config['paths'])

            cmd = list(map(os.path.expanduser, cmd))
            
            env = {}
            if 'passphrase' in remote_config:
                env['BORG_PASSPHRASE'] = remote_config['passphrase']

            print("Backing up", name, "to", remote)
            if remote_config.get('sudo', False):
                with sh.contrib.sudo:
                    sh.borg(*cmd, _fg=True, _env=env)
            else:
                sh.borg(*cmd, _fg=True, _env=env)
