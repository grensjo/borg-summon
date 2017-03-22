import click
from click.testing import CliRunner 
from borg_summon import command_line

def test_root_command_help():
    runner = CliRunner()
    result = runner.invoke(command_line.main, ['--help'])
    assert result.exit_code == 0

def test_root_backup_help():
    runner = CliRunner()
    result = runner.invoke(command_line.main, ['backup', '--help'])
    assert result.exit_code == 0

def test_root_maintain_help():
    runner = CliRunner()
    result = runner.invoke(command_line.main, ['maintain', '--help'])
    assert result.exit_code == 0
