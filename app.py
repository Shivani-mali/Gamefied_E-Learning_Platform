from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import jsonify
from pymongo import MongoClient
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime
from typing import Any, Dict

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)

# -------------------- DATABASE CONNECTION --------------------
class MockCollection:
    def __init__(self):
        self._data = []

    def find_one(self, query):
        for doc in self._data:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def insert_one(self, doc):
        # store a shallow copy to avoid accidental external mutation
        self._data.append(dict(doc))

    def update_one(self, filter_q, update):
        doc = self.find_one(filter_q)
        if not doc:
            return
        if '$set' in update:
            for k, v in update['$set'].items():
                parts = k.split('.')
                target = doc
                for p in parts[:-1]:
                    if p not in target or not isinstance(target[p], dict):
                        target[p] = {}
                    target = target[p]
                target[parts[-1]] = v
        if '$inc' in update:
            for k, v in update['$inc'].items():
                parts = k.split('.')
                target = doc
                for p in parts[:-1]:
                    target = target.setdefault(p, {})
                target[parts[-1]] = target.get(parts[-1], 0) + v
        if '$push' in update:
            for k, v in update['$push'].items():
                target = doc.setdefault(k, [])
                if isinstance(v, dict) and '$each' in v:
                    target.extend(v['$each'])
                else:
                    target.append(v)


try:
    # Read MongoDB connection string from environment first. If not set,
    # default to a local MongoDB instance for development.
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/?directConnection=true')
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

    # Test the connection
    client.admin.command('ping')
    print("MongoDB connected successfully!")
    # Use the DB specified in the URI's path if present, otherwise fall back to 'logindb'
    try:
        db_name = client.get_default_database().name
    except Exception:
        db_name = 'logindb'
    db = client[db_name]
    users = db['users']
    parents = db['parents']
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    print("Continuing with an in-memory fallback (development mode). Data will not persist across restarts.")
    users = MockCollection()
    parents = MockCollection()

# Static credential for parent
VALID_USERNAME = 'parent123'
VALID_PASSWORD = 'learnfun'

# -------------------- AUTH ROUTES --------------------

@app.route('/')
def login():
    """Login Page"""
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def do_login():
    """Handle Login Form Submission"""
    email = request.form['email']
    password = request.form['password']

    user = users.find_one({'email': email})

    if user and check_password_hash(user['password'], password):
        # Update child's last activity and login count
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update last activity
        users.update_one({'email': email}, {
            '$set': {'last_activity': current_date},
            '$inc': {'login_count': 1}
        })

        # Store child session data
        session['child_logged_in'] = True
        session['child_email'] = email
        session['child_name'] = user.get('name', 'Student')
        session['login_time'] = current_date

        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup Page for New Users"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # Check for existing email
        if users.find_one({'email': email}):
            flash('Email already registered! Try login.', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password)
        user_doc = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': hashed_password,
            'progress': {
                'Reading': 0,
                'Mathematics': 0,
                'Science': 0,
                'Problem Solving': 0
            },
            'grades': {
                'Reading': 'N/A',
                'Mathematics': 'N/A',
                'Science': 'N/A',
                'Problem Solving': 'N/A'
            },
            'time_spent': 0,  # in minutes
            'completed_works': [],
            'last_activity': 'Never',
            'achievements': [],
            'feedback': [],
            'login_count': 0
        }
        users.insert_one(user_doc)

        # Create parent account
        parent_email = f"parent_{email}"
        parent_doc = {
            'email': parent_email,
            'password': hashed_password,  # Same password for simplicity
            'child_email': email,
            'child_name': name
        }
        parents.insert_one(parent_doc)

        flash('Account created successfully! Parent account also created with email: ' + parent_email, 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


# -------------------- MAIN SELECTION PAGE --------------------

@app.route('/home')
def home():
    """After login: Choose between Primary & Pre-Primary"""
    return render_template('home.html')


# -------------------- PRE-PRIMARY SECTION --------------------

@app.route('/pre-primary')
def pre_primary():
    """Pre-Primary Main Section"""
    return render_template('pre_primary_section.html')


@app.route('/strokes')
def strokes():
    return render_template('strokes.html')


@app.route('/alphabets')
def alphabets():
    return render_template('alphabets.html')


@app.route('/colors')
def colors():
    return render_template('colors.html')


@app.route('/animals')
def animals():
    return render_template('animals.html')


@app.route('/vegetables')
def vegetables():
    return render_template('vegetables.html')


@app.route('/fruits')
def fruits():
    return render_template('fruits.html')


@app.route('/numbers')
def numbers():
    return render_template('numbers.html')


# -------------------- PRIMARY SECTION --------------------

@app.route('/primary')
def primary():
    """Redirect to Primary Section"""
    return redirect(url_for('primary_section'))


@app.route('/primary_section')
def primary_section():
    """Primary Main Section — History, Math, Science, GK, Grammar, Quizzes"""
    return render_template('primary_section.html')


@app.route('/history')
def history():
    return render_template('history.html')


# -------------------- HISTORY PLAYLIST / PROGRESS API --------------------
@app.route('/history/data')
def history_data():
    """Return the list of videos (IDs) and the unlocked index for the current child.
    For simplicity the playlist is defined here as an ordered array of YouTube video IDs.
    In production you could populate this from YouTube API or a DB.
    """
    # Example: Video IDs from the playlist the user provided. Replace with real IDs if you want.
    # Use the ordered list of video IDs provided by the user (Shivaji Maharaj series)
    playlist = [
        "o4IsZBynx88",
        "DxaUKNG-Tks",
        "hvSl9EJ0m_8",
        "qzWxZGx3F8A",
        "1wH3OCFhPNE",
        "WcTtlB_3V08",
        "hEp-vWeF904",
        "c9H5ka7sesQ",
        "MKqtCib-QNg"
    ]
    playlist_id = None

    unlocked = 0
    # If a child is logged in, try to read saved progress
    if session.get('child_logged_in'):
        child_email = session.get('child_email')
        user = users.find_one({'email': child_email})
        if user:
            unlocked = user.get('history_progress', 0)
    else:
        # Use session-stored progress for anonymous users
        unlocked = session.get('history_progress', 0)

    return jsonify({'playlist': playlist, 'playlist_id': playlist_id, 'unlocked': unlocked})


@app.route('/history/submit_quiz', methods=['POST'])
def history_submit_quiz():
    """Accept quiz results for a video index. If the user passes, unlock the next video.
    Expected JSON: { 'video_index': int, 'score': int }
    """
    if not request.is_json:
        return jsonify({'error': 'JSON required'}), 400
    data = request.get_json()
    video_index = int(data.get('video_index', -1))
    score = int(data.get('score', 0))

    # Basic validation
    if video_index < 0:
        return jsonify({'error': 'Invalid video index'}), 400

    PASS_SCORE = 60
    unlocked = 0
    child_email = None
    if session.get('child_logged_in'):
        child_email = session.get('child_email')
        user = users.find_one({'email': child_email})
        unlocked = user.get('history_progress', 0) if user else 0
    else:
        unlocked = session.get('history_progress', 0)

    if score >= PASS_SCORE:
        # If the user completed the currently-locked video, unlock next one
        if video_index >= unlocked:
            new_unlocked = video_index + 1
            # Persist
            if session.get('child_logged_in'):
                users.update_one({'email': child_email}, {'$set': {'history_progress': new_unlocked}})
            else:
                session['history_progress'] = new_unlocked
            unlocked = new_unlocked

        # Also increment general progress for History subject
        if session.get('child_logged_in'):
            users.update_one({'email': child_email}, {
                '$inc': {'progress.History': 5},
                '$push': {'completed_works': f'History video {video_index} quiz'}
            })

        return jsonify({'success': True, 'unlocked': unlocked})
    else:
        return jsonify({'success': False, 'message': 'Please try the quiz again to unlock the next video.'}), 200


@app.route('/math')
def math():
    return render_template('math.html')


@app.route('/science')
def science():
    return render_template('science.html')


@app.route('/gk')
def gk():
    return render_template('gk.html')


@app.route('/grammar')
def grammar():
    return render_template('grammar.html')


@app.route('/quiz')
def quiz():
    return render_template('quiz.html')


# -------------------- PARENT ROUTES --------------------

@app.route('/parent_login', methods=['GET', 'POST'])
def parent_login():
    # If already logged in, go to dashboard
    if session.get('parent_logged_in'):
        return redirect(url_for('parent_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        parent = parents.find_one({'email': email})
        if parent and check_password_hash(parent['password'], password):
            session['parent_logged_in'] = True
            session['parent_email'] = email
            session['child_email'] = parent['child_email']
            session['child_name'] = parent['child_name']
            return redirect(url_for('parent_dashboard'))
        else:
            # inline error message
            return render_template('parent_login.html', error='Invalid email or password.', email=email)

    return render_template('parent_login.html')


@app.route('/parent_dashboard')
def parent_dashboard():
    if not session.get('parent_logged_in'):
        return redirect(url_for('parent_login'))

    child_email = session.get('child_email')
    child = users.find_one({'email': child_email})
    if child:
        progress = child.get('progress', {
            'Reading': 0,
            'Mathematics': 0,
            'Science': 0,
            'Problem Solving': 0
        })
        grades = child.get('grades', {
            'Reading': 'N/A',
            'Mathematics': 'N/A',
            'Science': 'N/A',
            'Problem Solving': 'N/A'
        })
        child_name = child.get('name', 'Child')
        time_spent = child.get('time_spent', 0)
        completed_works = child.get('completed_works', [])
        last_activity = child.get('last_activity', 'N/A')
        achievements = child.get('achievements', [])
        feedback = child.get('feedback', [])
        preprimary_progress = child.get('preprimary_progress', {})
    else:
        progress = {
            'Reading': 0,
            'Mathematics': 0,
            'Science': 0,
            'Problem Solving': 0
        }
        grades = {
            'Reading': 'N/A',
            'Mathematics': 'N/A',
            'Science': 'N/A',
            'Problem Solving': 'N/A'
        }
        child_name = 'Child'
        time_spent = 0
        completed_works = []
        last_activity = 'N/A'
        achievements = []
        feedback = []
        preprimary_progress = {}

    return render_template(
        'parent_dashboard.html',
        progress=progress,
        grades=grades,
        child_name=child_name,
        time_spent=time_spent,
        completed_works=completed_works,
        last_activity=last_activity,
        achievements=achievements,
        feedback=feedback,
        preprimary_progress=preprimary_progress,
    )


@app.route('/parent_logout')
def parent_logout():
    session.pop('parent_logged_in', None)
    session.pop('parent_email', None)
    session.pop('child_email', None)
    session.pop('child_name', None)
    return redirect(url_for('parent_login'))


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if not session.get('parent_logged_in'):
        return redirect(url_for('parent_login'))

    feedback_text = request.form.get('feedback', '').strip()
    if feedback_text:
        child_email = session.get('child_email')
        feedback_entry = {
            'date': '2025-11-04',  # In real app, use datetime
            'message': feedback_text,
            'parent_email': session.get('parent_email')
        }
        users.update_one({'email': child_email}, {'$push': {'feedback': feedback_entry}})
        flash('Feedback submitted successfully!', 'success')
    else:
        flash('Please enter feedback.', 'error')

    return redirect(url_for('parent_dashboard'))


@app.route('/logout')
def logout():
    """Handle child logout and update time spent"""
    if session.get('child_logged_in'):
        logout_time = datetime.now()

        # Calculate time spent
        if session.get('login_time'):
            login_time = datetime.strptime(session['login_time'], '%Y-%m-%d %H:%M:%S')
            time_spent_minutes = int((logout_time - login_time).total_seconds() / 60)

            # Update time spent in database
            child_email = session.get('child_email')
            users.update_one({'email': child_email}, {
                '$inc': {'time_spent': time_spent_minutes}
            })

    # Clear child session
    session.pop('child_logged_in', None)
    session.pop('child_email', None)
    session.pop('child_name', None)
    session.pop('login_time', None)

    return redirect(url_for('login'))


@app.route('/update_progress', methods=['POST'])
def update_progress():
    """Update child progress when they complete activities"""
    if not session.get('child_logged_in'):
        return {'error': 'Not logged in'}, 401

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    subject = data.get('subject')
    progress_increase = int(data.get('progress_increase', 5))  # Default 5% increase
    activity_name = data.get('activity_name')

    if not subject or not activity_name:
        return {'error': 'Missing subject or activity name'}, 400

    child_email = session.get('child_email')

    # Update progress
    users.update_one({'email': child_email}, {
        '$inc': {f'progress.{subject}': progress_increase},
        '$push': {'completed_works': activity_name},
        '$set': {'last_activity': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    })

    # Cap progress at 100%
    user = users.find_one({'email': child_email})
    current_progress = 0
    if user:
        progress_data = user.get('progress', {})
        current_progress = progress_data.get(subject, 0) if progress_data else 0
        if current_progress > 100:
            users.update_one({'email': child_email}, {
                '$set': {f'progress.{subject}': 100}
            })
            current_progress = 100

    # Check for achievements
    check_achievements(child_email)

    if request.is_json:
        return {'success': True, 'new_progress': min(current_progress + progress_increase, 100)}
    else:
        flash('Progress updated successfully!', 'success')
        return redirect(url_for('quiz'))


@app.route('/preprimary/progress/update', methods=['POST'])
def preprimary_progress_update():
    """Per-section progress updates for Pre-Primary pages.
    Expected JSON: {
      section: 'colors'|'animals'|'fruits'|'vegetables'|'numbers'|'strokes',
      video_watched?: bool,
      inc_games?: int,           # increment for games played
      quiz_score?: int           # 0..4
    }
    """
    if not session.get('child_logged_in'):
        return jsonify({'error': 'Not logged in'}), 401
    if not request.is_json:
        return jsonify({'error': 'JSON required'}), 400

    payload: Dict[str, Any] = request.get_json() or {}
    section = str(payload.get('section', '')).strip().lower()
    if section not in {'colors', 'animals', 'fruits', 'vegetables', 'numbers', 'strokes'}:
        return jsonify({'error': 'Invalid section'}), 400

    video_watched = payload.get('video_watched', None)
    inc_games = int(payload.get('inc_games', 0) or 0)
    quiz_score = payload.get('quiz_score', None)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    child_email = session.get('child_email')

    set_fields: Dict[str, Any] = {f'preprimary_progress.{section}.last_updated': now}
    if isinstance(video_watched, bool) and video_watched:
        set_fields[f'preprimary_progress.{section}.video_watched'] = True
    if isinstance(quiz_score, int):
        # clamp quiz score to 0..4
        qs = max(0, min(4, quiz_score))
        set_fields[f'preprimary_progress.{section}.quiz_score'] = qs

    inc_fields: Dict[str, int] = {}
    if inc_games:
        inc_fields[f'preprimary_progress.{section}.games_played'] = inc_games

    update_doc: Dict[str, Any] = {'$set': set_fields}
    if inc_fields:
        update_doc['$inc'] = inc_fields

    users.update_one({'email': child_email}, update_doc)

    # Also keep high-level activity list
    activity_summary = None
    if inc_games:
        activity_summary = f'Pre-Primary {section.title()}: played {inc_games} game(s)'
    if isinstance(quiz_score, int):
        activity_summary = f'Pre-Primary {section.title()}: quiz {quiz_score}/4'
    if activity_summary:
        users.update_one({'email': child_email}, {
            '$push': {'completed_works': activity_summary},
            '$set': {'last_activity': now}
        })

    # Return current section doc (best-effort)
    user = users.find_one({'email': child_email}) or {}
    section_doc = (user.get('preprimary_progress', {}) or {}).get(section, {})
    return jsonify({'success': True, 'section': section, 'data': section_doc})


def check_achievements(child_email):
    """Check and award achievements based on progress"""
    user = users.find_one({'email': child_email})
    if not user:
        return

    achievements = user.get('achievements', [])
    progress = user.get('progress', {})
    completed_works = user.get('completed_works', [])
    login_count = user.get('login_count', 0)

    new_achievements = []

    # Achievement: First Steps (5 logins)
    if login_count >= 5 and 'First Steps' not in achievements:
        new_achievements.append('First Steps')

    # Achievement: Learning Explorer (10 completed activities)
    if len(completed_works) >= 10 and 'Learning Explorer' not in achievements:
        new_achievements.append('Learning Explorer')

    # Achievement: Subject Master (80%+ in any subject)
    for subject, pct in progress.items():
        if pct >= 80 and f'{subject} Master' not in achievements:
            new_achievements.append(f'{subject} Master')

    # Achievement: Perfect Score (100% in any subject)
    for subject, pct in progress.items():
        if pct >= 100 and f'{subject} Champion' not in achievements:
            new_achievements.append(f'{subject} Champion')

    # Achievement: Dedicated Learner (50+ hours)
    time_spent = user.get('time_spent', 0)
    if time_spent >= 3000 and 'Dedicated Learner' not in achievements:  # 50 hours in minutes
        new_achievements.append('Dedicated Learner')

    if new_achievements:
        users.update_one({'email': child_email}, {
            '$push': {'achievements': {'$each': new_achievements}}
        })


# -------------------- MAIN ENTRY POINT --------------------
if __name__ == '__main__':
    print("Starting Flask app...")
    # Disable the reloader to avoid Windows socket/reloader issues in some environments
    app.run(debug=True, port=5000, use_reloader=False)
