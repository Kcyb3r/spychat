from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
import requests
import json
import os
from datetime import datetime
import socket
import sys
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
socketio = SocketIO(app, cors_allowed_origins="*")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = '####enter-telegram-bot######'
TELEGRAM_CHAT_ID = '++telegram user id -----!'  # Channel/Group ID where bot will store data
BOT_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def send_to_telegram(message):
    url = f"{BOT_API_URL}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=data)

def get_messages_from_telegram():
    url = f"{BOT_API_URL}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['result']
    return []

def store_room_data(room_code, data):
    message = f"ROOM_DATA|{room_code}|{json.dumps(data)}"
    send_to_telegram(message)

def get_room_data(room_code):
    messages = get_messages_from_telegram()
    for message in reversed(messages):
        if 'text' in message['message']:
            text = message['message']['text']
            if text.startswith(f"ROOM_DATA|{room_code}|"):
                _, _, data_str = text.split('|', 2)
                return json.loads(data_str)
    return None

def generate_unique_code(length=6):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not get_room_data(code):
            return code

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    # Create rooms based on username for private messaging
    room = data['username']  # Use username as room identifier
    emit('message', {
        'message': data['message'],
        'username': data['username'],
        'deviceInfo': data.get('deviceInfo', 'Unknown Device'),
        'sender_id': request.sid,
        'file': data.get('file'),
        'filename': data.get('filename'),
        'filetype': data.get('filetype')
    }, room=room)  # Send only to the room with matching username

@socketio.on('join_room')
def on_join(data):
    username = data['username']
    join_room(username)

@socketio.on('leave_room')
def on_leave(data):
    username = data['username']
    leave_room(username)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    try:
        host = '0.0.0.0'
        port = 5004
        local_ip = get_local_ip()
        logging.info(f"\n🚀 Server running!")
        logging.info(f"💻 Local URL: http://localhost:{port}")
        logging.info(f"🌐 Network URL: http://{local_ip}:{port}")
        
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=False,  # Set to False for production
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
    except Exception as e:
        logging.error(f"Failed to start server: {str(e)}")
        sys.exit(1) 
