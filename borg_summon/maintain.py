import click

@click.command()
@click.pass_obj
def main(config):
    print(config)
