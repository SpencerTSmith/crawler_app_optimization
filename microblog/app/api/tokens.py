import logging
from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    user = basic_auth.current_user()
    token = user.get_token()
    db.session.commit()
    logger.info(f'Token generated for user: {user.username}')
    return {'token': token}

@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    user = token_auth.current_user()
    user.revoke_token()
    db.session.commit()
    logger.info(f'Token revoked for user: {user.username}')
    return '', 204
