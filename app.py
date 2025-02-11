from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
import os
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///addiction_solver.db'
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

google_bp = make_google_blueprint(scope=['profile', 'email'])
app.register_blueprint(google_bp, url_prefix='/login')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    recovery_plans = db.relationship('RecoveryPlan', backref='user', lazy=True)
    progress_logs = db.relationship('ProgressLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

class RecoveryPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    addiction_type = db.Column(db.String(100), nullable=False)
    goals = db.Column(db.Text, nullable=False)
    strategies = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProgressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    mood = db.Column(db.Integer, nullable=False)
    cravings = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email.', 'error')
            return redirect(url_for('register'))
        
        # Create new user with hashed password
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    recovery_plan = RecoveryPlan.query.filter_by(user_id=current_user.id).first()
    progress_logs = ProgressLog.query.filter_by(user_id=current_user.id).order_by(ProgressLog.date.desc()).limit(7).all()
    return render_template('dashboard.html', recovery_plan=recovery_plan, progress_logs=progress_logs)

@app.route('/create_recovery_plan', methods=['GET', 'POST'])
@login_required
def create_recovery_plan():
    if request.method == 'POST':
        addiction_type = request.form['addiction_type']
        goals = request.form['goals']
        strategies = request.form['strategies']
        
        recovery_plan = RecoveryPlan(user_id=current_user.id, addiction_type=addiction_type, goals=goals, strategies=strategies)
        db.session.add(recovery_plan)
        db.session.commit()
        
        flash('Recovery plan created successfully.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_recovery_plan.html')

@app.route('/log_progress', methods=['GET', 'POST'])
@login_required
def log_progress():
    if request.method == 'POST':
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        mood = int(request.form['mood'])
        cravings = int(request.form['cravings'])
        notes = request.form['notes']
        
        progress_log = ProgressLog(user_id=current_user.id, date=date, mood=mood, cravings=cravings, notes=notes)
        db.session.add(progress_log)
        db.session.commit()
        
        flash('Progress logged successfully.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('log_progress.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

google_bp.storage = SQLAlchemyStorage(OAuth, db.session, user=current_user)

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with Google.", category="error")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", category="error")
        return False

    google_info = resp.json()
    google_user_id = google_info["id"]

    try:
        oauth = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=google_user_id).one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=google_user_id, token=token)

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in with Google.", category="success")
    else:
        user = User(username=google_info["email"].split("@")[0], email=google_info["email"])
        oauth.user = user
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash("Successfully signed in with Google.", category="success")

    return False

@app.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    return redirect(url_for('dashboard'))

def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

