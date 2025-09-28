# app.py
import os

from authlib.integrations.flask_client import OAuth
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for

app = Flask(__name__, static_folder='.')

# Секретный ключ для подписи cookies (обязательно!)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Настройка OAuth — здесь мы используем переменные окружения, а не жёстко закодированные значения
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),  # ← Берём из переменных окружения
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),  # ← Берём из переменных окружения
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # ← Убраны пробелы!
    client_kwargs={'scope': 'openid email profile'}
)

# Подключаем твой бэкенд
from stego_backend import process_hide, process_extract, \
    get_file_info  # ← Убедись, что файл называется stego_backend_py.py


# === Google Auth Routes ===

@app.route('/auth/google')
def login():
    redirect_uri = url_for('auth_callback', _external=True)  # ← Это важно: _external=True
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def auth_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info:
            session['user'] = {
                'id': user_info['sub'],
                'name': user_info.get('name', ''),
                'email': user_info.get('email', ''),
                'picture': user_info.get('picture', '')
            }
            # Инициализируем статистику, если нет
            if 'stats' not in session:
                session['stats'] = {
                    'filesProcessed': 0,
                    'dataHidden': 0,
                    'successfulOperations': 0,
                    'achievements': []
                }
        return redirect('/')
    except Exception as e:
        print(f"Google Auth Error: {e}")
        return "Ошибка авторизации", 500


@app.route('/api/user')
def user_info():
    user = session.get('user')
    if user:
        return jsonify({
            'logged_in': True,
            'name': user.get('name'),
            'email': user.get('email'),
            'picture': user.get('picture'),
            'stats': session.get('stats', {})
        })
    else:
        return jsonify({'logged_in': False})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    session.pop('stats', None)
    return jsonify({'success': True})


@app.route('/api/save-stats', methods=['POST'])
def save_stats():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.json
    session['stats'] = {
        'filesProcessed': data.get('filesProcessed', 0),
        'dataHidden': data.get('dataHidden', 0),
        'successfulOperations': data.get('successfulOperations', 0),
        'achievements': data.get('achievements', [])
    }
    session.modified = True  # важно!
    return jsonify({'success': True})


# === Stego API ===

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

