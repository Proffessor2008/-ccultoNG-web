# app.py (обновлённая версия с PostgreSQL)
import json
import os
from datetime import datetime
import base64

from authlib.integrations.flask_client import OAuth
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, abort
from werkzeug.middleware.proxy_fix import ProxyFix

# Инициализация Flask
app = Flask(__name__, static_folder='.')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


# Безопасность (остаётся без изменений)
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://www.googletagmanager.com https://accounts.google.com 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com https://cdn.tailwindcss.com; "
        "img-src 'self' data: https: blob: https://cdnjs.cloudflare.com https://lh3.googleusercontent.com https://api.producthunt.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
        "connect-src 'self' https://www.google-analytics.com https://accounts.google.com; "
        "frame-src https://accounts.google.com https://docs.google.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self' https://accounts.google.com; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests;"
    )
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response


# Секретный ключ
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# OAuth (без изменений)
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# === Подключение к PostgreSQL ===
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL не задан в переменных окружения!")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            picture TEXT,
            files_processed INTEGER DEFAULT 0,
            data_hidden INTEGER DEFAULT 0,
            successful_operations INTEGER DEFAULT 0,
            achievements TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


# Инициализация БД при старте
init_db()


# === Google Auth и API (почти без изменений) ===

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
        now = datetime.utcnow()

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO users (id, name, email, picture, files_processed, data_hidden, successful_operations, achievements, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 0, 0, 0, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                picture = EXCLUDED.picture,
                updated_at = EXCLUDED.updated_at
        """, (user_id, name, email, picture, '[]', now, now))
        db.commit()
        cur.close()
        db.close()

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
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_row = cur.fetchone()
    cur.close()
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
    now = datetime.utcnow()

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        UPDATE users
        SET files_processed = %s,
            data_hidden = %s,
            successful_operations = %s,
            achievements = %s,
            updated_at = %s
        WHERE id = %s
    """, (files_processed, data_hidden, successful_operations, achievements_json, now, user_id))
    db.commit()
    cur.close()
    db.close()
    return jsonify({'success': True})


# === Stego API (без изменений) ===
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
    if os.path.isfile(filename):
        return send_from_directory('.', filename)
    abort(404)


@app.errorhandler(404)
def not_found(e):
    return send_from_directory('.', '404.html'), 404


if __name__ == '__main__':
    # Получаем порт из переменной окружения или используем 8000 по умолчанию
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
