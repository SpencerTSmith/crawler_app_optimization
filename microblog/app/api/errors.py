import logging
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import HTTPException
from app.api import bp


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

def error_response(status_code, message=None):
    logger.error(f'Error response generated: {status_code} - {message}')
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    return payload, status_code

def bad_request(message):
    logger.warning(f'Bad request: {message}')
    return error_response(400, message)

@bp.errorhandler(HTTPException)
def handle_exception(e):
    logger.error(f'HTTP Exception occurred: {e.code} - {e.description}')
    return error_response(e.code)

