from collections import ChainMap
import sys
import sh
import os.path
from datetime import datetime

def get_prefix_dicts(root, keys):
    """Given a dict root and a list of keys, return a list of
    "prefix dicts". For example, if keys = ['a', 'b', 'c'], return
    [root,  root['a'], root['a']['b'], root['a']['b']['c'].
    """

    chain = [root]
    current = root
    for i in range(0, len(keys)):
        current = current[keys[i]]
        chain.append(current)
    return chain


def get_recursive_dict(root, keys):
    """Given a dict root and a list of keys, return a dict-like object,
    where lookups are made recursivly from the deepest key and "upwards".

    Example: Say that keys=['a', 'b'] and this function returns chain_map.
    Then, when looking up chain_map['x'], the following will be done:
    - if root['a']['b']['x'] exists return it, otherwise continue
    - if root['a']['x'] exists return it, otherwise continue
    - if root['x'] exists return it, otherwise fail
    """

    return ChainMap({}, *reversed(get_prefix_dicts(root, keys)))


def get_prioritized_recursive_dict(root, primary, secondary):
    """Given a dict root, and two lists of keys: primary and secondary,
    return an dict-like object similarly to get_recursive_dict, but
    which prioritizes values from the path in primary over values from
    the path in secondary.

    The dict can be thought of as a rooted tree. If you follow the sequence
    of keys in primary you get to the node A, and if you follow secondary 
    you get to the node B. Let C be the closest common ancestor to A and B.
    Then the prioritized recursive dict returned by this function will primarily
    search for a key in the path from A to C, secondarily in the path from B 
    to C, and if nothing else is found, in their common prefix from C up to
    the root.
    """

    primary_prefixes = get_prefix_dicts(root, primary)
    secondary_prefixes = get_prefix_dicts(root, secondary)
    
    for i, (prefix1, prefix2) in enumerate(zip(primary_prefixes, secondary_prefixes)):
        if prefix1 != prefix2:
            return ChainMap({}, *reversed(primary_prefixes[:i] + secondary_prefixes[i:]
                + primary_prefixes[i:]))

    if len(primary) > len(secondary):
        return get_recursive_dict(root, primary)
    else:
        return get_recursive_dict(root, secondary)


def main(global_config, source_names):
    if len(source_names) == 0:
        source_names = global_config['backup']['sources'].keys()

    for name in source_names:
        source_config = get_recursive_dict(global_config, ['backup', 'sources', name]) 
        
        if 'remote_list' in source_config:
            remote_list = source_config['remote_list']
        else:
            remote_list = global_config['remotes'].keys()

        for remote in remote_list:
            remote_config = get_prioritized_recursive_dict(global_config,
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
