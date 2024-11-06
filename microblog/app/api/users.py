import logging
import sqlalchemy as sa
from flask import request, url_for, abort
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    logger.info(f'Fetching user with ID: {id}')
    user = db.get_or_404(User, id)
    logger.debug(f'User found: {user.username}')
    return user.to_dict()

@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    logger.info(f'Fetching users: page {page}, per_page {per_page}')
    return User.to_collection_dict(sa.select(User), page, per_page,
                                   'api.get_users')

@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    logger.info(f'Fetching followers for user ID: {id}')
    user = db.get_or_404(User, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(user.followers.select(), page, per_page,
                                   'api.get_followers', id=id)

@bp.route('/users/<int:id>/following', methods=['GET'])
@token_auth.login_required
def get_following(id):
    logger.info(f'Fetching following for user ID: {id}')
    user = db.get_or_404(User, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(user.following.select(), page, per_page,
                                   'api.get_following', id=id)

@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    logger.info('Creating new user.')
    if 'username' not in data or 'email' not in data or 'password' not in data:
        logger.warning('Bad request: Missing username, email, or password fields.')
        return bad_request('must include username, email and password fields')
    if db.session.scalar(sa.select(User).where(
            User.username == data['username'])):
        logger.warning(f'Bad request: Username already taken - {data["username"]}')
        return bad_request('please use a different username')
    if db.session.scalar(sa.select(User).where(
            User.email == data['email'])):
        logger.warning(f'Bad request: Email already in use - {data["email"]}')
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    logger.info(f'User created successfully: {user.username}')
    return user.to_dict(), 201, {'Location': url_for('api.get_user', id=user.id)}

@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    logger.info(f'Updating user with ID: {id}')
    if token_auth.current_user().id != id:
        logger.warning('Authorization error: User tried to update another user\'s profile.')
        abort(403)
    user = db.get_or_404(User, id)
    data = request.get_json()
    if 'username' in data and data['username'] != user.username and \
        db.session.scalar(sa.select(User).where(
            User.username == data['username'])):
        logger.warning(f'Bad request: Username already taken - {data["username"]}')
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
        db.session.scalar(sa.select(User).where(
            User.email == data['email'])):
        logger.warning(f'Bad request: Email already in use - {data["email"]}')
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    logger.info(f'User updated successfully: {user.username}')
    return user.to_dict()

