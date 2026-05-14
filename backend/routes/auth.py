import os
import random
import smtplib
from email.mime.text import MIMEText
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

def send_otp_email(to_email, otp, context_type="Authentication"):
    sender_email = os.environ.get('MAIL_USERNAME')
    sender_password = os.environ.get('MAIL_PASSWORD')
    
    if not sender_email or not sender_password or sender_email == "your_email@gmail.com":
        print(">> SMTP credentials missing in .env! Skipping real email dispatch.")
        return False
        
    try:
        msg = MIMEText(f"Your NeoVault {context_type} OTP is: {otp}\n\nDo not share this with anyone. If you did not request this, please secure your account immediately.")
        msg['Subject'] = f"NeoVault {context_type} Token: {otp}"
        msg['From'] = f"NeoVault Security Node <{sender_email}>"
        msg['To'] = to_email
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f">> SMTP Dispatch Error: {e}")
        return False

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Save auth context to session securely
            session['pending_user_id'] = user.id
            session['login_otp'] = otp
            
            # Fire SMTP Dispatch
            email_sent = send_otp_email(user.email, otp, "Login")
            
            # Automatically print OTP to console/flash for development environment
            print(f"=============================")
            print(f"NEOVAULT SECURE OTP: {otp}")
            print(f"=============================")
            
            if email_sent:
                flash(f'An OTP has been dispatched to {user.email}.', 'info')
            else:
                flash(f'[DEV MODE] No SMTP configured. Your OTP is: {otp}', 'info')
            
            return redirect(url_for('auth.otp_verify'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'error')
    return render_template('login.html')

@auth_bp.route('/otp-verify', methods=['GET', 'POST'])
def otp_verify():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    pending_user_id = session.get('pending_user_id')
    stored_otp = session.get('login_otp')
    
    if not pending_user_id or not stored_otp:
        flash('Authentication session expired. Please sign in again.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if user_otp == stored_otp:
            # OTP matched, log the user in
            user = db.session.get(User, pending_user_id)
            if user:
                login_user(user)
                # Clear session
                session.pop('pending_user_id', None)
                session.pop('login_otp', None)
                return redirect(url_for('core.index'))
        else:
            flash('Invalid or expired OTP token. Access Denied.', 'error')
            
    return render_template('otp.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.signup'))
            
        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Generate 6-digit OTP for initial registration access
        otp = str(random.randint(100000, 999999))
        
        # Save auth context to session securely
        session['pending_user_id'] = new_user.id
        session['login_otp'] = otp
        
        email_sent = send_otp_email(new_user.email, otp, "Registration")
        
        print(f"=============================")
        print(f"NEOVAULT REGISTRATION OTP: {otp}")
        print(f"=============================")
        
        if email_sent:
            flash(f'A verification OTP was sent to {new_user.email}.', 'info')
        else:
            flash(f'[DEV MODE] No SMTP configured. Your OTP is: {otp}', 'info')
        
        return redirect(url_for('auth.otp_verify'))
    return render_template('signup.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            otp = str(random.randint(100000, 999999))
            session['reset_email'] = email
            session['reset_otp'] = otp
            
            email_sent = send_otp_email(user.email, otp, "Password Recovery")
            
            print(f"=============================")
            print(f"NEOVAULT PASSWORD RESET OTP: {otp}")
            print(f"=============================")
            
            if email_sent:
                flash(f'A recovery OTP has been sent to {user.email}.', 'info')
            else:
                flash(f'[DEV MODE] No SMTP configured. Your OTP is: {otp}', 'info')
            
            return redirect(url_for('auth.reset_otp'))
        else:
            # Prevent email enumeration by giving a generic success message
            flash('If an account exists for that email, an OTP has been sent.', 'info')
            
    return render_template('forgot.html')

@auth_bp.route('/reset-otp', methods=['GET', 'POST'])
def reset_otp():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    reset_email = session.get('reset_email')
    stored_otp = session.get('reset_otp')
    
    if not reset_email or not stored_otp:
        flash('Password reset session expired. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if user_otp == stored_otp:
            session['allow_password_reset'] = True
            return redirect(url_for('auth.new_password'))
        else:
            flash('Invalid or expired OTP token. Access Denied.', 'error')
            
    return render_template('reset_otp.html')

@auth_bp.route('/new-password', methods=['GET', 'POST'])
def new_password():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    if not session.get('allow_password_reset') or not session.get('reset_email'):
        flash('Unauthorized access. Please complete the OTP verification first.', 'error')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.new_password'))
            
        user = User.query.filter_by(email=session.get('reset_email')).first()
        if user:
            user.password = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.commit()
            
            # Clear all reset session variables
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            session.pop('allow_password_reset', None)
            
            flash('Master Security PIN successfully updated. You may now sign in.', 'info')
            return redirect(url_for('auth.login'))
            
    return render_template('new_password.html')

@auth_bp.route('/oauth/<provider>')
def oauth_stub(provider):
    flash(f"{provider.capitalize()} Enterprise OAuth is not configured! You must inject Google/GitHub CLIENT_ID and CLIENT_SECRET into the .env core to unlock social login APIs.", 'error')
    return redirect(url_for('auth.login'))
