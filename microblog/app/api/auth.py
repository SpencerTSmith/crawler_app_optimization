import logging
import sqlalchemy as sa
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app import db
from app.models import User
from app.api.errors import error_response


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username, password):
    logger.info(f'Verifying password for user: {username}')
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user and user.check_password(password):
        logger.info(f'Password verification successful for user: {username}')
        return user
    logger.warning(f'Password verification failed for user: {username}')
    return None

@basic_auth.error_handler
def basic_auth_error(status):
    logger.error(f'Basic authentication error occurred with status: {status}')
    return error_response(status)

@token_auth.verify_token
def verify_token(token):
    logger.info(f'Verifying token: {token}')
    if token:
        user = User.check_token(token)
        if user:
            logger.info(f'Token verification successful for user: {user.username}')
            return user
    logger.warning(f'Token verification failed or token is missing: {token}')
    return None

@token_auth.error_handler
def token_auth_error(status):
    logger.error(f'Token authentication error occurred with status: {status}')
    return error_response(status)

