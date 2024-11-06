import os
import logging
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import User, Post, Message, Notification, Task

app = create_app()


logging.basicConfig(
    level=logging.DEBUG if os.environ.get('DEBUG') else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() if os.environ.get('LOG_TO_STDOUT') else logging.FileHandler('app.log')
    ]
)


logger = logging.getLogger(__name__)

def log_debug(message):
    logger.debug(message)

def log_info(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)

def log_error(message):
    logger.error(message)

@app.shell_context_processor
def make_shell_context():
    log_info("Creating shell context")
    return {
        'sa': sa,
        'so': so,
        'db': db,
        'User': User,
        'Post': Post,
        'Message': Message,
        'Notification': Notification,
        'Task': Task
    }


if __name__ == "__main__":
    log_info("Application started.")
    log_debug("Debugging mode is on.")
    log_warning("This is a warning message.")
    log_error("This is an error message.")
    

