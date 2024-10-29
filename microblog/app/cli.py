import os
import logging
from flask import Blueprint
import click


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger('cli')

bp = Blueprint('cli', __name__, cli_group=None)


@bp.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    logger.info(f'Initializing language: {lang}')
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        logger.error('Extract command failed.')
        raise RuntimeError('extract command failed')
    logger.info('Extract command succeeded.')

    if os.system(f'pybabel init -i messages.pot -d app/translations -l {lang}'):
        logger.error('Init command failed.')
        raise RuntimeError('init command failed')
    logger.info(f'Init command succeeded for language: {lang}.')

    os.remove('messages.pot')
    logger.info('Removed messages.pot file.')


@translate.command()
def update():
    """Update all languages."""
    logger.info('Updating all languages.')
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        logger.error('Extract command failed.')
        raise RuntimeError('extract command failed')
    logger.info('Extract command succeeded.')

    if os.system('pybabel update -i messages.pot -d app/translations'):
        logger.error('Update command failed.')
        raise RuntimeError('update command failed')
    logger.info('Update command succeeded.')

    os.remove('messages.pot')
    logger.info('Removed messages.pot file.')


@translate.command()
def compile():
    """Compile all languages."""
    logger.info('Compiling all languages.')
    if os.system('pybabel compile -d app/translations'):
        logger.error('Compile command failed.')
        raise RuntimeError('compile command failed')
    logger.info('Compile command succeeded.')

