import os
import json
import secrets
import logging
from datetime import datetime, timezone, timedelta
from hashlib import md5
from time import time
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import redis
import rq
from app import db, login
from app.search import add_to_index, remove_from_index, query_index


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
        logger.info(f'Searching for {expression} on page {page} with {per_page} items per page.')
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            logger.warning(f'No results found for {expression}.')
            return [], 0
        when = [(ids[i], i) for i in range(len(ids))]
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }
        logger.debug(f'Changes before commit: {session._changes}')

    @classmethod
    def after_commit(cls, session):
        logger.info('Committing changes to the database.')
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
                logger.info(f'Added {obj} to index.')
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
                logger.info(f'Updated {obj} in index.')
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
                logger.info(f'Removed {obj} from index.')
        session._changes = None

    @classmethod
    def reindex(cls):
        logger.info('Reindexing all records in the database.')
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)
            logger.info(f'Reindexed {obj}.')


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        logger.info(f'Paginating query for {endpoint} - Page: {page}, Per Page: {per_page}')
        resources = db.paginate(query, page=page, per_page=per_page, error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page, **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page, **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page, **kwargs) if resources.has_prev else None
            }
        }
        logger.debug(f'Pagination result: {data}')
        return data

# Define the followers table
followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)

class User(PaginatedAPIMixin, UserMixin, db.Model):
    # User fields and relationships
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    last_message_read_time: so.Mapped[Optional[datetime]]
    token: so.Mapped[Optional[str]] = so.mapped_column(sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]

    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    following: so.WriteOnlyMapped['User'] = so.relationship(secondary=followers, primaryjoin=(followers.c.follower_id == id), secondaryjoin=(followers.c.followed_id == id), back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(secondary=followers, primaryjoin=(followers.c.followed_id == id), secondaryjoin=(followers.c.follower_id == id), back_populates='following')
    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(foreign_keys='Message.sender_id', back_populates='author')
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(foreign_keys='Message.recipient_id', back_populates='recipient')
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(back_populates='user')
    tasks: so.WriteOnlyMapped['Task'] = so.relationship(back_populates='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        logger.info(f'Setting password for user: {self.username}')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        logger.info(f'Checking password for user: {self.username}')
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        logger.debug(f'Generating avatar for user: {self.username}')
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        logger.info(f'{self.username} is following {user.username}')
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        logger.info(f'{self.username} is unfollowing {user.username}')
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        logger.debug(f'Checking if {self.username} is following {user.username}')
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        logger.info(f'Counting followers for user: {self.username}')
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        logger.info(f'Counting following for user: {self.username}')
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        logger.debug(f'Fetching following posts for user: {self.username}')
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

    def get_reset_password_token(self, expires_in=600):
        logger.info(f'Generating reset password token for user: {self.username}')
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        logger.info('Verifying reset password token.')
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except Exception as e:
            logger.error(f'Token verification failed: {e

