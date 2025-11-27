from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os
from datetime import datetime
from typing import Any, Dict

app = Flask(__name__, static_folder='static', template_folder='templates')

# -------------------- SECRET KEY --------------------
# Read from Railway → Variables
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# -------------------- MONGO DB CONNECTION --------------------
class MockCollection:
    def __init__(self):
        self._data = []

    def find_one(self, query):
        for doc in self._data:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def insert_one(self, doc):
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
                    target = target.setdefault(p, {})
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

# -------------------- CONNECT TO REAL MONGO DB --------------------
try:
    MONGO_URI = os.environ.get("MONGO_URI")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    # Test MongoDB connection
    client.admin.command('ping')
    print("MongoDB Atlas connected successfully!")

    db = client['logindb']
    users = db['users']
    parents = db['parents']

except Exception as e:
    print("MongoDB connection failed:", e)
    print("Using fallback in-memory DB for development.")
    users = MockCollection()
    parents = MockCollection()

# -------------------- AUTH --------------------
@app.route('/')
def login():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def do_login():
    email = request.form['email']
    password = request.form['password']

    user = users.find_one({'email': email})
    if user and check_password_hash(user['password'], password):

        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        users.update_one({'email': email}, {
            '$set': {'last_activity': current_date},
            '$inc': {'login_count': 1}
        })

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
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        if users.find_one({'email': email}):
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))

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
            'time_spent': 0,
            'completed_works': [],
            'last_activity': 'Never',
            'achievements': [],
            'feedback': [],
            'login_count': 0
        }
        users.insert_one(user_doc)

        parent_email = f"parent_{email}"
        parent_doc = {
            'email': parent_email,
            'password': hashed_password,
            'child_email': email,
            'child_name': name
        }
        parents.insert_one(parent_doc)

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# -------------------- MAIN PAGES --------------------
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/pre-primary')
def pre_primary():
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

@app.route('/primary')
def primary():
    return redirect(url_for('primary_section'))

@app.route('/primary_section')
def primary_section():
    return render_template('primary_section.html')

@app.route('/history')
def history():
    return render_template('history.html')

# -------------------- HISTORY DATA --------------------
@app.route('/history/data')
def history_data():
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
    unlocked = 0

    if session.get('child_logged_in'):
        user = users.find_one({'email': session['child_email']})
        unlocked = user.get('history_progress', 0) if user else 0

    return jsonify({'playlist': playlist, 'unlocked': unlocked})

@app.route('/history/submit_quiz', methods=['POST'])
def history_submit_quiz():
    if not request.is_json:
        return jsonify({'error': 'JSON required'}), 400

    data = request.get_json()
    video_index = int(data.get('video_index', -1))
    score = int(data.get('score', 0))

    PASS_SCORE = 60

    child_email = session.get('child_email')
    user = users.find_one({'email': child_email})

    unlocked = user.get('history_progress', 0) if user else 0

    if score >= PASS_SCORE:
        if video_index >= unlocked:
            new_unlocked = video_index + 1
            users.update_one({'email': child_email}, {'$set': {'history_progress': new_unlocked}})
            unlocked = new_unlocked

        users.update_one({'email': child_email}, {
            '$inc': {'progress.History': 5},
            '$push': {'completed_works': f'History video {video_index} quiz'}
        })

        return jsonify({'success': True, 'unlocked': unlocked})

    return jsonify({'success': False}), 200

# -------------------- OTHER SUBJECTS --------------------
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

# -------------------- PARENT AREA --------------------
@app.route('/parent_login', methods=['GET', 'POST'])
def parent_login():
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
            return render_template('parent_login.html', error='Invalid email or password.')

    return render_template('parent_login.html')

@app.route('/parent_dashboard')
def parent_dashboard():
    if not session.get('parent_logged_in'):
        return redirect(url_for('parent_login'))

    child_email = session.get('child_email')
    child = users.find_one({'email': child_email})

    if child:
        return render_template('parent_dashboard.html', **child)

    return "Child data not found"

@app.route('/parent_logout')
def parent_logout():
    session.clear()
    return redirect(url_for('parent_login'))

# -------------------- LOGOUT --------------------
@app.route('/logout')
def logout():
    if session.get('child_logged_in'):
        logout_time = datetime.now()
        login_time = datetime.strptime(session['login_time'], '%Y-%m-%d %H:%M:%S')
        minutes = int((logout_time - login_time).total_seconds() / 60)

        users.update_one({'email': session['child_email']}, {
            '$inc': {'time_spent': minutes}
        })

    session.clear()
    return redirect(url_for('login'))

# -------------------- RUN FLASK --------------------
if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
