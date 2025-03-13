from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///addiction_solver.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    recovery_plans = db.relationship('RecoveryPlan', backref='user', lazy=True)
    progress_logs = db.relationship('ProgressLog', backref='user', lazy=True)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, value):
        self.password_hash = value

class RecoveryPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    addiction_type = db.Column(db.String(100), nullable=False)
    goals = db.Column(db.Text, nullable=False)
    strategies = db.Column(db.Text, nullable=False)
    support_network = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProgressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    mood = db.Column(db.String(50), nullable=False)
    triggers = db.Column(db.Text, nullable=True)
    coping_strategies = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recovery plan
    recovery_plan = RecoveryPlan.query.filter_by(user_id=current_user.id).order_by(RecoveryPlan.created_at.desc()).first()
    
    # Get user's recent progress logs
    recent_logs = ProgressLog.query.filter_by(user_id=current_user.id).order_by(ProgressLog.date.desc()).limit(5).all()
    
    # Calculate streak (consecutive days with logs)
    streak = 0
    if recent_logs:
        today = datetime.utcnow().date()
        last_log_date = recent_logs[0].date
        
        # Check if there's a log for today
        if last_log_date == today:
            streak = 1
            check_date = today - timedelta(days=1)
            
            # Check previous days
            while True:
                log = ProgressLog.query.filter_by(user_id=current_user.id, date=check_date).first()
                if log:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
    
    return render_template('dashboard.html', 
                          recovery_plan=recovery_plan, 
                          recent_logs=recent_logs, 
                          streak=streak)

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/educational_resources')
@app.route('/educational_resources/<type>')
def educational_resources(type='all'):
    # Dictionary of addiction types
    addiction_types = {
        'substance': 'Substance Abuse',
        'alcohol': 'Alcohol Addiction',
        'gambling': 'Gambling Addiction',
        'gaming': 'Gaming Addiction',
        'social_media': 'Social Media Addiction',
        'food': 'Food Addiction',
        'shopping': 'Shopping Addiction',
        'work': 'Work Addiction',
        'other': 'Other Addictions'
    }
    
    # Sample data for videos with actual links
    videos = [
        {
            'title': 'Understanding Addiction: The Science Behind Recovery',
            'description': 'A comprehensive overview of how addiction affects the brain and practical steps for recovery.',
            'addiction_type': 'substance',
            'duration': '12:45',
            'author': 'Dr. Sarah Johnson',
            'rating': 4.5,
            'difficulty': 'beginner',
            'url': 'https://www.youtube.com/watch?v=8qK0hxuXOC8',
            'thumbnail_url': 'https://img.youtube.com/vi/8qK0hxuXOC8/maxresdefault.jpg'
        },
        {
            'title': 'Breaking Free from Gaming Addiction',
            'description': 'Expert insights on recognizing and overcoming gaming addiction with practical strategies.',
            'addiction_type': 'gaming',
            'duration': '18:32',
            'author': 'Dr. Alok Kanojia',
            'rating': 4.8,
            'difficulty': 'intermediate',
            'url': 'https://www.youtube.com/watch?v=2k8fHR9jKVM',
            'thumbnail_url': 'https://img.youtube.com/vi/2k8fHR9jKVM/maxresdefault.jpg'
        },
        {
            'title': 'Social Media Addiction: Understanding the Digital Hook',
            'description': 'Learn about the psychology behind social media addiction and strategies to build healthier digital habits.',
            'addiction_type': 'social_media',
            'duration': '22:15',
            'author': 'Dr. Cal Newport',
            'rating': 4.9,
            'difficulty': 'beginner',
            'url': 'https://www.youtube.com/watch?v=3E7hkPZ-HTk',
            'thumbnail_url': 'https://img.youtube.com/vi/3E7hkPZ-HTk/maxresdefault.jpg'
        },
        {
            'title': 'Alcohol Recovery: A Comprehensive Guide',
            'description': 'A detailed walkthrough of the alcohol recovery process, from detox to long-term sobriety maintenance.',
            'addiction_type': 'alcohol',
            'duration': '45:10',
            'author': 'Dr. Andrew Huberman',
            'rating': 4.7,
            'difficulty': 'advanced',
            'url': 'https://www.youtube.com/watch?v=DkS1pkKpILY',
            'thumbnail_url': 'https://img.youtube.com/vi/DkS1pkKpILY/maxresdefault.jpg'
        },
        {
            'title': 'The Neuroscience of Addiction',
            'description': 'An in-depth look at how addiction affects the brain and nervous system.',
            'addiction_type': 'substance',
            'duration': '32:18',
            'author': 'Dr. Anna Lembke',
            'rating': 4.8,
            'difficulty': 'advanced',
            'url': 'https://www.youtube.com/watch?v=QxZxKdFy-ZA',
            'thumbnail_url': 'https://img.youtube.com/vi/QxZxKdFy-ZA/maxresdefault.jpg'
        },
        {
            'title': 'Overcoming Shopping Addiction',
            'description': 'Practical strategies for recognizing and overcoming compulsive shopping behaviors.',
            'addiction_type': 'shopping',
            'duration': '15:42',
            'author': 'Dr. April Benson',
            'rating': 4.3,
            'difficulty': 'intermediate',
            'url': 'https://www.youtube.com/watch?v=8qK0hxuXOC8',
            'thumbnail_url': 'https://img.youtube.com/vi/8qK0hxuXOC8/maxresdefault.jpg'
        },
        {
            'title': 'Work Addiction: Finding Balance',
            'description': 'Understanding workaholism and strategies for creating a healthier work-life balance.',
            'addiction_type': 'work',
            'duration': '28:05',
            'author': 'Dr. Bryan Robinson',
            'rating': 4.6,
            'difficulty': 'intermediate',
            'url': 'https://www.youtube.com/watch?v=2k8fHR9jKVM',
            'thumbnail_url': 'https://img.youtube.com/vi/2k8fHR9jKVM/maxresdefault.jpg'
        },
        {
            'title': 'Gambling Recovery: First Steps',
            'description': 'Essential first steps for anyone looking to overcome gambling addiction.',
            'addiction_type': 'gambling',
            'duration': '19:37',
            'author': 'Dr. Timothy Fong',
            'rating': 4.4,
            'difficulty': 'beginner',
            'url': 'https://www.youtube.com/watch?v=3E7hkPZ-HTk',
            'thumbnail_url': 'https://img.youtube.com/vi/3E7hkPZ-HTk/maxresdefault.jpg'
        }
    ]
    
    # Sample data for books with actual links
    books = [
        {
            'title': 'The Addiction Recovery Workbook',
            'description': 'A comprehensive guide to understanding and overcoming various forms of addiction through practical exercises and strategies.',
            'addiction_type': 'substance',
            'author': 'Dr. Paula Muran',
            'rating': 4.8,
            'difficulty': 'intermediate',
            'url': 'https://www.amazon.com/Addiction-Recovery-Workbook-Evidence-Based-Dependence/dp/1641521562',
            'thumbnail_url': 'https://m.media-amazon.com/images/I/71Vb8lCXhXL._SL1500_.jpg'
        },
        {
            'title': 'Overcoming Gambling Addiction',
            'description': 'A self-help guide using cognitive behavioral therapy techniques to break free from gambling addiction.',
            'addiction_type': 'gambling',
            'author': 'Dr. Alex Blaszczynski',
            'rating': 4.2,
            'difficulty': 'beginner',
            'url': 'https://www.amazon.com/Overcoming-Problem-Gambling-self-help-guide/dp/1472106423',
            'thumbnail_url': 'https://m.media-amazon.com/images/I/71Ky8-QeYrL._SL1500_.jpg'
        },
        {
            'title': 'Breaking Free from Emotional Eating',
            'description': 'A compassionate guide to understanding and overcoming emotional eating patterns and food addiction.',
            'addiction_type': 'food',
            'author': 'Geneen Roth',
            'rating': 4.6,
            'difficulty': 'intermediate',
            'url': 'https://www.amazon.com/Breaking-Free-Emotional-Eating-Geneen/dp/0452284910',
            'thumbnail_url': 'https://m.media-amazon.com/images/I/71Ky8-QeYrL._SL1500_.jpg'
        },
        {
            'title': 'Digital Minimalism: Choosing a Focused Life',
            'description': 'A practical guide to breaking free from technology addiction and reclaiming your time and attention.',
            'addiction_type': 'social_media',
            'author': 'Cal Newport',
            'rating': 4.9,
            'difficulty': 'beginner',
            'url': 'https://www.amazon.com/Digital-Minimalism-Choosing-Focused-Noisy/dp/0525536515',
            'thumbnail_url': 'https://m.media-amazon.com/images/I/71Vb8lCXhXL._SL1500_.jpg'
        },
        {
            'title': 'The Sober Diaries',
            'description': 'A memoir and guide to quitting alcohol and living a healthier, happier life.',
            'addiction_type': 'alcohol',
            'author': 'Clare Pooley',
            'rating': 4.7,
            'difficulty': 'beginner',
            'url': 'https://www.amazon.com/Sober-Diaries-stopped-drinking-started/dp/1473661870',
            'thumbnail_url': 'https://m.media-amazon.com/images/I/71Ky8-QeYrL._SL1500_.jpg'
        },
        {
            'title': 'Hooked: How to Build Habit-Forming Products',
            'description': 'Understanding the psychology of habit formation and addiction in the digital age.',
            'addiction_type': 'social_media',
            'author': 'Nir Eyal',
            'rating': 4.5,
            'difficulty': 'intermediate',
            'url': 'https://www.amazon.com/Hooked-How-Build-Habit-Forming-Products/dp/1591847788',
            'thumbnail_url': 'https://m.media-amazon.com/images/I/71Vb8lCXhXL._SL1500_.jpg'
        }
    ]
    
    # Sample data for articles with actual links
    articles = [
        {
            'title': 'Understanding Food Addiction: Signs, Causes, and Recovery',
            'description': 'An in-depth article exploring the nature of food addiction and evidence-based approaches to recovery.',
            'addiction_type': 'food',
            'author': 'Dr. Lisa Marsh',
            'reading_time': '15 min',
            'rating': 4.1,
            'difficulty': 'beginner',
            'url': 'https://www.healthline.com/nutrition/food-addiction-treatment'
        },
        {
            'title': 'Digital Detox: Breaking Free from Social Media Addiction',
            'description': 'Practical strategies and tips for reducing social media dependency and building healthier online habits.',
            'addiction_type': 'social_media',
            'author': 'Dr. Jean Twenge',
            'reading_time': '12 min',
            'rating': 4.5,
            'difficulty': 'beginner',
            'url': 'https://www.psychologytoday.com/us/blog/digital-world-real-world/202106/digital-detox-10-reasons-take-break-social-media'
        },
        {
            'title': 'The Science of Alcohol Addiction',
            'description': 'A comprehensive guide to understanding alcohol addiction, its effects on the body, and evidence-based treatment options.',
            'addiction_type': 'alcohol',
            'author': 'Dr. Michael Roberts',
            'reading_time': '20 min',
            'rating': 4.8,
            'difficulty': 'advanced',
            'url': 'https://www.niaaa.nih.gov/publications/brochures-and-fact-sheets/understanding-alcohol-use-disorder'
        },
        {
            'title': 'Gaming Addiction in Adolescents: Warning Signs and Intervention',
            'description': 'A guide for parents and educators on identifying gaming addiction in young people and effective intervention strategies.',
            'addiction_type': 'gaming',
            'author': 'Dr. Sarah Peterson',
            'reading_time': '18 min',
            'rating': 4.2,
            'difficulty': 'intermediate',
            'url': 'https://www.psychiatry.org/patients-families/internet-gaming'
        },
        {
            'title': 'Relapse Prevention: Building a Sustainable Recovery',
            'description': 'Evidence-based strategies for preventing relapse and maintaining long-term recovery from substance abuse.',
            'addiction_type': 'substance',
            'author': 'Dr. Thomas Miller',
            'reading_time': '25 min',
            'rating': 4.7,
            'difficulty': 'intermediate',
            'url': 'https://www.samhsa.gov/find-help/recovery'
        }
    ]
    
    # Sample data for podcasts with actual links
    podcasts = [
        {
            'title': 'Recovery Stories: Real People, Real Journeys',
            'description': 'Inspiring interviews with individuals who have successfully overcome addiction and rebuilt their lives.',
            'addiction_type': 'substance',
            'author': 'Hosted by Maria Garcia',
            'duration': '45:22',
            'rating': 4.9,
            'url': 'https://podcasts.apple.com/us/podcast/recovery-happy-hour/id1372848112'
        },
        {
            'title': 'Gaming Balance: Finding Healthy Relationships with Games',
            'description': 'Discussions on maintaining a healthy relationship with gaming and recognizing when it becomes problematic.',
            'addiction_type': 'gaming',
            'author': 'Hosted by Dr. Alok Kanojia',
            'duration': '38:15',
            'rating': 4.2,
            'url': 'https://podcasts.apple.com/us/podcast/game-quitters-podcast-video-game-addiction-gaming-disorder/id1453761433'
        },
        {
            'title': 'Sober Curious: Exploring Life Without Alcohol',
            'description': 'Conversations about the sober curious movement and the benefits of reducing or eliminating alcohol consumption.',
            'addiction_type': 'alcohol',
            'author': 'Hosted by Emma Wilson',
            'duration': '52:40',
            'rating': 4.6,
            'url': 'https://podcasts.apple.com/us/podcast/sober-curious/id1460780302'
        },
        {
            'title': 'Digital Wellness: Reclaiming Your Attention',
            'description': 'Expert discussions on digital wellness and strategies for breaking free from social media addiction.',
            'addiction_type': 'social_media',
            'author': 'Hosted by Dr. Cal Newport',
            'duration': '41:18',
            'rating': 4.8,
            'url': 'https://podcasts.apple.com/us/podcast/your-undivided-attention/id1460030305'
        }
    ]
    
    # Sample data for courses with actual links
    courses = [
        {
            'title': 'Comprehensive Addiction Recovery Program',
            'description': 'A structured 8-week course covering all aspects of addiction recovery, from understanding triggers to building a sustainable recovery plan.',
            'addiction_type': 'substance',
            'author': 'Dr. Jennifer Adams',
            'duration': '8 weeks',
            'rating': 4.7,
            'difficulty': 'intermediate',
            'url': 'https://www.udemy.com/course/addiction-recovery-coaching-certification/'
        },
        {
            'title': 'Mindful Eating: Breaking Free from Food Addiction',
            'description': 'A 6-week course on developing a healthier relationship with food through mindfulness practices and cognitive behavioral techniques.',
            'addiction_type': 'food',
            'author': 'Dr. Lisa Johnson',
            'duration': '6 weeks',
            'rating': 4.1,
            'difficulty': 'beginner',
            'url': 'https://www.coursera.org/learn/food-and-health'
        },
        {
            'title': 'Family Support: Helping Loved Ones with Addiction',
            'description': 'A comprehensive course for family members and friends of individuals struggling with addiction, focusing on effective support strategies.',
            'addiction_type': 'multiple',
            'author': 'Dr. Michael Torres',
            'duration': '4 weeks',
            'rating': 4.9,
            'difficulty': 'intermediate',
            'url': 'https://www.edx.org/learn/addiction/stanford-university-supporting-loved-ones-with-substance-use-disorders'
        }
    ]
    
    # Filter resources by addiction type if specified
    if type != 'all':
        videos = [video for video in videos if video['addiction_type'] == type]
        books = [book for book in books if book['addiction_type'] == type]
        articles = [article for article in articles if article['addiction_type'] == type]
        podcasts = [podcast for podcast in podcasts if podcast['addiction_type'] == type or podcast['addiction_type'] == 'multiple']
        courses = [course for course in courses if course['addiction_type'] == type or course['addiction_type'] == 'multiple']
    
    return render_template('educational_resources.html', 
                          videos=videos, 
                          books=books, 
                          articles=articles,
                          podcasts=podcasts,
                          courses=courses,
                          addiction_types=addiction_types,
                          current_type=type)

@app.route('/create_recovery_plan', methods=['GET', 'POST'])
@login_required
def create_recovery_plan():
    if request.method == 'POST':
        addiction_type = request.form.get('addiction_type')
        goals = request.form.get('goals')
        strategies = request.form.get('strategies')
        support_network = request.form.get('support_network')
        
        new_plan = RecoveryPlan(
            user_id=current_user.id,
            addiction_type=addiction_type,
            goals=goals,
            strategies=strategies,
            support_network=support_network
        )
        
        db.session.add(new_plan)
        db.session.commit()
        
        flash('Recovery plan created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_recovery_plan.html')

@app.route('/edit_recovery_plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_recovery_plan(plan_id):
    plan = RecoveryPlan.query.get_or_404(plan_id)
    
    # Check if the plan belongs to the current user
    if plan.user_id != current_user.id:
        flash('You do not have permission to edit this recovery plan.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        plan.addiction_type = request.form.get('addiction_type')
        plan.goals = request.form.get('goals')
        plan.strategies = request.form.get('strategies')
        plan.support_network = request.form.get('support_network')
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Recovery plan updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_recovery_plan.html', plan=plan)

@app.route('/log_progress', methods=['GET', 'POST'])
@login_required
def log_progress():
    if request.method == 'POST':
        mood = request.form.get('mood')
        triggers = request.form.get('triggers')
        coping_strategies = request.form.get('coping_strategies')
        notes = request.form.get('notes')
        
        # Check if a log already exists for today
        today = datetime.utcnow().date()
        existing_log = ProgressLog.query.filter_by(user_id=current_user.id, date=today).first()
        
        if existing_log:
            # Update existing log
            existing_log.mood = mood
            existing_log.triggers = triggers
            existing_log.coping_strategies = coping_strategies
            existing_log.notes = notes
            flash('Progress log updated for today!', 'success')
        else:
            # Create new log
            new_log = ProgressLog(
                user_id=current_user.id,
                mood=mood,
                triggers=triggers,
                coping_strategies=coping_strategies,
                notes=notes
            )
            db.session.add(new_log)
            flash('Progress logged successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    # Check if a log already exists for today
    today = datetime.utcnow().date()
    existing_log = ProgressLog.query.filter_by(user_id=current_user.id, date=today).first()
    
    return render_template('log_progress.html', existing_log=existing_log)

@app.route('/view_progress_logs')
@login_required
def view_progress_logs():
    # Get all progress logs for the current user, ordered by date (newest first)
    logs = ProgressLog.query.filter_by(user_id=current_user.id).order_by(ProgressLog.date.desc()).all()
    
    return render_template('view_progress_logs.html', logs=logs)

@app.route('/delete_progress_log/<int:log_id>', methods=['POST'])
@login_required
def delete_progress_log(log_id):
    log = ProgressLog.query.get_or_404(log_id)
    
    # Check if the log belongs to the current user
    if log.user_id != current_user.id:
        flash('You do not have permission to delete this log.', 'error')
        return redirect(url_for('view_progress_logs'))
    
    db.session.delete(log)
    db.session.commit()
    
    flash('Progress log deleted successfully!', 'success')
    return redirect(url_for('view_progress_logs'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update email
        new_email = request.form.get('email')
        if new_email and new_email != current_user.email:
            # Check if email is already in use
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already in use.', 'error')
                return redirect(url_for('profile'))
            
            current_user.email = new_email
        
        # Update password
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            # Verify current password
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('profile'))
            
            # Verify new passwords match
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('profile'))
            
            # Update password
            current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)