# app.py
import os

from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

# Подключаем твой бэкенд
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


# Отдаём главную страницу и JS
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

