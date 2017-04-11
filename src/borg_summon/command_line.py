import click
from . import config_parser, backup, maintain

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

main.add_command(backup.main, name="backup")
main.add_command(maintain.main, name="maintain")
