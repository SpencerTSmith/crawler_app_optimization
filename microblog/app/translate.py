import logging
import requests
from flask import current_app
from flask_babel import _


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

def translate(text, source_language, dest_language):
    logger.info(f'Translating text from {source_language} to {dest_language}.')
    
    if 'MS_TRANSLATOR_KEY' not in current_app.config or \
            not current_app.config['MS_TRANSLATOR_KEY']:
        logger.warning('Translation service is not configured. Returning error message.')
        return _('Error: the translation service is not configured.')

    auth = {
        'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': 'westus'
    }

    logger.debug(f'Sending request to translation service with text: {text}')
    try:
        r = requests.post(
            'https://api.cognitive.microsofttranslator.com'
            '/translate?api-version=3.0&from={}&to={}'.format(
                source_language, dest_language), headers=auth, json=[
                {'Text': text}])

        if r.status_code != 200:
            logger.error(f'Translation service failed with status code: {r.status_code}.')
            return _('Error: the translation service failed.')

        translated_text = r.json()[0]['translations'][0]['text']
        logger.info('Translation successful.')
        return translated_text

    except Exception as e:
        logger.error(f'An error occurred during translation: {e}', exc_info=True)
        return _('Error: the translation service failed.')
