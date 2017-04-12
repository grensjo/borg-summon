from collections import ChainMap
import logging
import platform
import sys
import traceback
from . import borg

logger = logging.getLogger(__name__)

errors = []

def report_failure(result):
    errors.append(result)
    result.log()
    if isinstance(result.error, Exception):
        traceback.print_exception(None, result.error, result.error.__traceback__, file=sys.stderr)
    print(file=sys.stderr)

def report_success(result):
    result.log()

def send_report(config):
    global errors
    if len(errors) == 0:
        return
    if 'alert_hook' not in config:
        return

    hook_config = ChainMap(config['alert_hook'], config)

    report_header = "borg-summon @ %s - %d errors occurred" % (platform.node(), len(errors))
    report_body = "Here follows a summary of the errors. For more information, check your logs.\n\n%s\n"\
            % "\n".join(map(str, errors))

    borg.hook(hook_config, args_tail=[report_header, report_body])
    errors = []

class ActionSuccess:
    def __init__(self, action, target):
        self.action = action
        self.target = target

    def __str__(self):
        return self.action + "\t" + ",".join(self.target) + "\tsuccess"

    def log(self):
        logging.info(str(self))

class ActionFailure:
    def __init__(self, action, target, error):
        self.action = action
        self.target = target
        self.error = error

    def __str__(self):
        return self.action + "\t" + ",".join(self.target) + "\tfail\t" + repr(self.error) 

    def log(self):
        logging.error(str(self))
