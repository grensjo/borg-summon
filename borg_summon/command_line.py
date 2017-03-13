import click
from . import config_parser, maintain
from . import backup as backup2

@click.group()
@click.option('--config', '-c', 'config_path', default=None, help='Use the specified config file.',
        type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def main(ctx, config_path):
    if config_path is None:
        ctx.obj = config_parser.get_from_default()
    else:
        print(config_path)
        ctx.obj = config_parser.get_from_file(config_path)

@main.command()
@click.argument('sources', nargs=-1)
@click.pass_obj
def backup(config, sources):
    backup2.main(config, sources)


@main.command()
@click.pass_obj
def maintain(config):
    print(config)
