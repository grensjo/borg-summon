import click
import glob
import sys
import sh
import os.path
from datetime import datetime
from collections import ChainMap
from enum import Enum
from . import borg, util
from .report import ActionSuccess, ActionFailure, report_success, report_failure, send_report

class Action(Enum):
    PRUNE = 'prune'
    CHECK = 'check'

def main_inner(config, repos, remotes, prune_flag, check_flag):
    for action, enabled in ((Action.PRUNE, prune_flag), (Action.CHECK, check_flag)):
        if not enabled:
            continue

        command_config = ChainMap(util.lookup(config, ['maintain', action.value], {}), config)

        repo_list = config['maintain']['repos']

        for repo in repo_list:
            repo_name = repo['repo_name']

            # If a set of repos has been explicitly set, and this is not one of
            # them - skip it
            if len(repos) > 0 and repo_name not in repos:
                continue

            # Get config for this repo
            repo_config = command_config.new_child(repo)
            remote_name = repo_config['remote']

            # If a set of remotes has been explicitly set, and this is not one
            # of them - skip this repo
            if len(remotes) > 0 and remote_name not in remotes:
                continue

            # If this action is disabled for this repo, skip it
            if not repo_config.get('enable_' + action.value, True):
                continue

            # Get config for this remote
            remote_config = repo_config.new_child(config['remotes'][remote_name])

            prefixes = remote_config.get('prefixes', [])
            if len(prefixes) == 0:
                prefixes = [None]

            for prefix in prefixes:
                if action == Action.PRUNE:
                    print("\n")
                    print("Pruning archives the repo", repo_name, "on the remote", remote_name, end="")
                    if prefix is None:
                        print(" with any names")
                    else:
                        print(" with prefix", prefix)

                    try:
                        borg.prune(remote_config, remote_name, repo_name, prefix)
                        report_success(ActionSuccess('prune', (repo_name, remote_name, str(prefix))))
                    except Exception as e:
                        report_failure(ActionFailure('prune', (repo_name, remote_name, str(prefix)), e))
                elif action == Action.CHECK:
                    print("\n")
                    print("Checking archives in the repo", repo_name, "on the remote", remote_name, end="")
                    if prefix is None:
                        print(" with any names")
                    else:
                        print(" with prefix", prefix)

                    try:
                        borg.check(remote_config, remote_name, repo_name, prefix)
                        report_success(ActionSuccess('check', (repo_name, remote_name, str(prefix))))
                    except Exception as e:
                        report_failure(ActionFailure('check', (repo_name, remote_name, str(prefix)), e))

@click.command()
@click.option('-R', '--repo', multiple=True)
@click.option('-r', '--remote', multiple=True)
@click.option('--prune/--no-prune', default=True)
@click.option('--check/--no-check', default=True)
@click.pass_obj
def main(config, repo, remote, prune, check):
    main_inner(config, repo, remote, prune, check)
