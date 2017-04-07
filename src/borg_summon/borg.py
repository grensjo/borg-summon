import sh
import glob
import os.path
from contextlib import ExitStack
from . import util

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InvalidConfigError(Error):
    """Exception raised when there is a critical configuration error.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def get_common_args_and_env(config, remote, repo_name):
    args = {}
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
            args[level] = True
        else:
            raise ValueError('"%s" is not a legal log level. Expected "critical",\
                    "error", "warning", "info", "debug" or "verbose".')

    if 'umask' in config:
        args['umask'] = config['umask']

    if 'remote_borg_path' in config:
        args['remote-path'] = config['remote_borg_path']

    if 'location' not in config:
        raise InvalidConfigError('No location specified for remote "%s".' % remote)
        
    return args, env

def execution_context(config):
    """Return a suitable context manager for calling borg. If the sudo setting is
    true, it will be the sudo context manager from the sh package. If the sudo_user
    setting is also set, that user will be passed to sudo using the --user option.

    If the sudo setting is not set to true, a dummy context manager which does not
    do anything will be returned.

    Arguments:
        config -- a dictionary-like configuration object which will be used to
                  select which context manager will be returned
    """
    if config.get('sudo', False):
        user = config.get('sudo_user', None)
        if user is not None:
            return sh.contrib.sudo(user=user, _with=True)
        else:
            return sh.contrib.sudo
    else:
        # If the sudo setting is not true, return a dummy context manager.
        return ExitStack()

def init(config, remote, repo_name):
    """Call borg to initialize a repository. Any relevant options specified in the
    config object will be passed to borg.

    Arguments:
        config -- a dictionary-like object with the needed configuration for the
                 source and remote involved
        remote -- the name of the remote
        repo_name -- the name of the repository to initialize
    """
    args, env = get_common_args_and_env(config, remote, repo_name)
    
    if 'encryption' in config:
        encryption = config['encryption']
        if encryption in ('none', 'keyfile', 'repokey'):
            args['encryption'] = encryption
        else:
            raise ValueError('"%s" is not a valid encryption mode. Expected "none",\
                    "keyfile" or "repokey".')

    if config.get('append_only', False):
        args['append-only'] = True

    location = config['location']
    repo_path = os.path.expanduser(location + repo_name)

    with execution_context(config):
        sh.borg.init(repo_path, _fg=True, _env=env, **args)

def create(config, remote, repo_name, archive):
    """Call borg to create an archive (perform a backup). Any relevant options specified
    in the config object will be passed to borg.

    Arguments:
        config -- a dictionary-like object with the needed configuration for the
                  source and remote involved
        remote -- the name of the remote to backup to
        repo_name -- the name of the repository to initialize
        archive -- the name of the archive to create (this needs to be unique within
                   the repository
    """
    args = []
    kwargs, env = get_common_args_and_env(config, remote, repo_name)

    if config.get('stats', False):
        kwargs['stats'] = True

    if config.get('progress', False):
        kwargs['progress'] = True

    if 'exclude_file' in config:
        kwargs['exclude-from'] = os.path.expanduser(config['exclude_file'])

    if config.get('exclude_caches', False):
        kwargs['exclude-caches'] = True

    if config.get('one_file_system', False):
        kwargs['one-file-system'] = True

    if 'compression' in config:
        kwargs['compression'] = config['compression']

    location = config['location']
    args.append(os.path.expanduser(location + repo_name) + "::" + archive)

    # Add all paths to cmd, with ~ expanded and shell-like globbing (using * wildcards)
    for path in config['paths']:
        args.extend(glob.glob(os.path.expanduser(path)))

    with execution_context(config):
        sh.borg.create(*args, _fg=True, _env=env, **kwargs)



def check(config):
    raise NotImplementedError

def prune(config):
    raise NotImplementedError

def extract(config):
    raise NotImplementedError
