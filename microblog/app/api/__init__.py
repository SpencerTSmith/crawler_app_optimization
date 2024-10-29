import logging
from flask import Blueprint


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)


from app.api import users, errors, tokens

logger.info("API Blueprint 'api' has been created and registered.")

