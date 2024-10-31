import logging
from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlsplit
from flask_login import login_user, logout_user, current_user
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} already authenticated, redirecting to index.')
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            logger.warning('Invalid login attempt for username: %s', form.username.data)
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        
        logger.info(f'User {user.username} logged in successfully.')
        return redirect(next_page)
    
    return render_template('auth/login.html', title=_('Sign In'), form=form)

@bp.route('/logout')
def logout():
    logger.info(f'User {current_user.username} logged out.')
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} already authenticated, redirecting to index.')
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        logger.info(f'User {user.username} registered successfully.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title=_('Register'), form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} already authenticated, redirecting to index.')
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
            logger.info(f'Password reset email sent to {user.email}.')
        
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title=_('Reset Password'), form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} already authenticated, redirecting to index.')
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        logger.warning(f'Invalid password reset token provided: {token}.')
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        logger.info(f'Password reset for user: {user.username}.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)
