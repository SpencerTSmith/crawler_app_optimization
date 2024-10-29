import logging
from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger('email')

def send_async_email(app, msg):
    with app.app_context():
        logger.info(f'Sending email: {msg.subject} to {msg.recipients}')
        mail.send(msg)
        logger.info(f'Email sent: {msg.subject} to {msg.recipients}')


def send_email(subject, sender, recipients, text_body, html_body,
               attachments=None, sync=False):
    logger.info(f'Preparing to send email: {subject} to {recipients}')
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            logger.info(f'Attaching file: {attachment[0]}')
            msg.attach(*attachment)

    if sync:
        logger.info('Sending email synchronously.')
        mail.send(msg)
        logger.info(f'Email sent: {subject} to {recipients}')
    else:
        logger.info('Sending email asynchronously in a separate thread.')
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()
