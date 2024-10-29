import json
import sys
import time
import sqlalchemy as sa
import logging
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import User, Post, Task
from app.email import send_email


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

app = create_app()
app.app_context().push()

def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = db.session.get(Task, job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()
        logger.info(f'Task progress updated to {progress}% for job ID {job.get_id()}.')

def export_posts(user_id):
    try:
        user = db.session.get(User, user_id)
        logger.info(f'Starting export of posts for user: {user.username} (User ID: {user_id})')
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = db.session.scalar(sa.select(sa.func.count()).select_from(
            user.posts.select().subquery()))
        logger.info(f'Total posts to export: {total_posts}')

        for post in db.session.scalars(user.posts.select().order_by(
                Post.timestamp.asc())):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)  # Simulating a long-running process
            i += 1
            _set_task_progress(100 * i // total_posts)

        logger.info(f'Exporting {len(data)} posts to email.')
        send_email(
            '[Microblog] Your blog posts',
            sender=app.config['ADMINS'][0], recipients=[user.email],
            text_body=render_template('email/export_posts.txt', user=user),
            html_body=render_template('email/export_posts.html', user=user),
            attachments=[('posts.json', 'application/json',
                          json.dumps({'posts': data}, indent=4))],
            sync=True)
        logger.info('Email sent successfully with exported posts.')

    except Exception as e:
        _set_task_progress(100)
        logger.error('Unhandled exception occurred during post export', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)
        logger.info('Export posts task completed.')


