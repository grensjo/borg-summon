import atexit
import click
import logging
from . import config_parser, backup, maintain, report

logger = logging.getLogger('borg_summon')

@click.group()
@click.option('--config', '-c', 'config_path', default=None,
        help='Use the specified config file.',
        type=click.Path())
@click.pass_context
def main(ctx, config_path):
    if config_path is None:
        ctx.obj = config_parser.get_from_default()
    else:
        print(config_path)
        ctx.obj = config_parser.get_from_file(config_path)

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='%(asctime)s\t%(levelname)s\t%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

    if 'log_file' in ctx.obj:
        fh = logging.FileHandler(ctx.obj['log_file'])
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    atexit.register(report.send_report, ctx.obj)

main.add_command(backup.main, name="backup")
main.add_command(maintain.main, name="maintain")
