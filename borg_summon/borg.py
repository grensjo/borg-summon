import sh
import glob
import os.path
from . import util

def get_common_args_and_env(config, remote, repo_name):
    args = []
    env = {}

    if 'ssh_command' in config:
        env['BORG_RSH'] = config['ssh_command']

    passphrase = util.lookup(config, ['secret', remote, repo_name, 'passphrase'],
            default=config.get('passphrase'))
    if passphrase is not None:
        env['BORG_PASSPHRASE'] = passphrase
        env['BORG_DISPLAY_PASSPHRASE'] = "n"

    if 'log_level' in config:
        level = config['log_level']
        if level in ('critical', 'error', 'warning', 'info', 'debug', 'verbose'):
            args.append('--' + level)
        else:
            raise ValueError('"%s" is not a legal log level. Expected "critical",\
                    "error", "warning", "info", "debug" or "verbose".')

    if 'umask' in config:
        args.append('--umask')
        args.append(config['umask'])

    if 'remote_borg_path' in config:
        args.append('--remote-path')
        args.append(config['remote_borg_path'])

    return args, env

def init(config, remote, repo_name):
    args, env = get_common_args_and_env(config, remote, repo_name)
    
    if 'encryption' in config:
        encryption = config['encryption']
        if level in ('none', 'keyfile', 'repokey'):
            args.append('--encryption')
            args.append(level)
        else:
            raise ValueError('"%s" is not a valid encryption mode. Expected "none",\
                    "keyfile" or "repokey".')

    if config.get('append_only', False):
        args.append('--append-only')

    where = config['where']
    args.append(os.path.expanduser(where + repo_name))

    if config.get('sudo', False):
        with sh.contrib.sudo:
            sh.borg.init(*args, _fg=True, _env=env)
    else:
        sh.borg.init(*args, _fg=True, _env=env)

def create(config, remote, repo_name, archive):
    args, env = get_common_args_and_env(config, remote, repo_name)

    if config.get('stats', False):
        args.append('--stats')

    if config.get('progress', False):
        args.append('--progress')

    if 'exclude_file' in config:
        args.append('--exclude-from')
        args.append(os.path.expanduser(config['exclude_file']))

    if config.get('exclude_caches', False):
        args.append('--exclude-caches')

    if config.get('one_file_system', False):
        args.append('--one-file-system')

    if 'compression' in config:
        args.append('--compression')
        args.append(config['compression'])
    
    where = config['where']
    args.append(os.path.expanduser(where + repo_name) + "::" + archive)

    # Add all paths to cmd, with ~ expanded and shell-like globbing (using * wildcards)
    for path in config['paths']:
        args.extend(glob.glob(os.path.expanduser(path)))

    if config.get('sudo', False):
        with sh.contrib.sudo:
            sh.borg.create(*args, _fg=True, _env=env)
    else:
        sh.borg.create(*args, _fg=True, _env=env)



def check(config):
    pass

def prune(config):
    pass

def extract(config):
    pass
