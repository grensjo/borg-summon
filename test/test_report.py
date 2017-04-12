from unittest.mock import patch
from borg_summon import borg, report

@patch('borg_summon.borg.hook')
def test_send_report_empty(hook):
    report.errors = []

    # Successful actions should not be reported.
    report.report_success(report.ActionSuccess("foo", "bar"))
    report.send_report({ 'alert_hook': { 'command': '/bin/true' } })

    # The hook should not have been called, since there were no
    # errors to report.
    assert hook.call_count == 0

@patch('borg_summon.borg.hook')
def test_send_report_no_hook(hook):
    report.errors = []

    report.report_failure(report.ActionFailure("foo", "bar", "error"))
    report.send_report({})
    
    # The hook method should not have been called, since there was
    # no hook command in the config.
    assert hook.call_count == 0

@patch('borg_summon.borg.hook')
def test_send_report_success(hook):
    report.errors = []

    report.report_failure(report.ActionFailure("foo", "bar", "error"))
    report.report_failure(report.ActionFailure("foo", "bar", Exception()))
    report.send_report({ 'alert_hook': { 'command': '/bin/true' } })
    
    assert hook.call_count == 1
    args, kwargs = hook.call_args
    assert args[0]['command'] == '/bin/true'
    assert len(kwargs) == 1
