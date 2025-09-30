# app.py
import json
import os
import sqlite3
from datetime import datetime

from authlib.integrations.flask_client import OAuth
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

# Инициализация Flask
app = Flask(__name__, static_folder='.')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


# Безопасность
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: https://cdnjs.cloudflare.com; "
        "font-src https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# Секретный ключ
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# === База данных ===
DATABASE = 'users.db'


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            picture TEXT,
            files_processed INTEGER DEFAULT 0,
            data_hidden INTEGER DEFAULT 0,
            successful_operations INTEGER DEFAULT 0,
            achievements TEXT,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)
    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Инициализация БД при старте
init_db()


# === Google Auth ===
@app.route('/auth/google')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def auth_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            return "Ошибка: нет данных пользователя", 400

        user_id = user_info['sub']
        name = user_info.get('name', '')
        email = user_info.get('email', '')
        picture = user_info.get('picture', '')

        now = datetime.utcnow().isoformat()

        # Сохраняем/обновляем в БД
        db = get_db_connection()
        db.execute("""
            INSERT INTO users (id, name, email, picture, files_processed, data_hidden, successful_operations, achievements, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                picture=excluded.picture,
                updated_at=excluded.updated_at
        """, (user_id, name, email, picture, '[]', now, now))
        db.commit()
        db.close()

        # Сохраняем в сессии
        session['user_id'] = user_id
        session['user'] = {
            'id': user_id,
            'name': name,
            'email': email,
            'picture': picture
        }

        return redirect('/')
    except Exception as e:
        print(f"Google Auth Error: {e}")
        return "Ошибка авторизации", 500


@app.route('/api/user')
def user_info():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False})

    db = get_db_connection()
    user_row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()

    if not user_row:
        return jsonify({'logged_in': False})

    try:
        achievements = json.loads(user_row['achievements']) if user_row['achievements'] else []
    except:
        achievements = []

    return jsonify({
        'logged_in': True,
        'name': user_row['name'],
        'email': user_row['email'],
        'picture': user_row['picture'],
        'stats': {
            'filesProcessed': user_row['files_processed'],
            'dataHidden': user_row['data_hidden'],
            'successfulOperations': user_row['successful_operations'],
            'achievements': achievements
        }
    })


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('user', None)
    return jsonify({'success': True})


@app.route('/api/save-stats', methods=['POST'])
def save_stats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    files_processed = data.get('filesProcessed', 0)
    data_hidden = data.get('dataHidden', 0)
    successful_operations = data.get('successfulOperations', 0)
    achievements = data.get('achievements', [])

    try:
        achievements_json = json.dumps(achievements)
    except:
        achievements_json = '[]'

    now = datetime.utcnow().isoformat()

    db = get_db_connection()
    db.execute("""
        UPDATE users
        SET files_processed = ?,
            data_hidden = ?,
            successful_operations = ?,
            achievements = ?,
            updated_at = ?
        WHERE id = ?
    """, (files_processed, data_hidden, successful_operations, achievements_json, now, user_id))
    db.commit()
    db.close()

    return jsonify({'success': True})


# === Stego API ===
from stego_backend import process_hide, process_extract, get_file_info


@app.route('/api/hide', methods=['POST'])
def hide():
    data = request.json
    result = process_hide(
        data['container'],
        data['secret'],
        data['method'],
        data.get('password', '')
    )
    return jsonify(result)


@app.route('/api/extract', methods=['POST'])
def extract():
    data = request.json
    result = process_extract(data['stego'], data.get('password', ''))
    return jsonify(result)


@app.route('/api/file-info', methods=['POST'])
def file_info():
    data = request.json
    result = get_file_info(data['file'], data['filename'])
    return jsonify(result)


# === Static files ===
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "404", 404


# === Запуск ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
