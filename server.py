# -*- coding: utf-8 -*-
import os
import sys
import json
import sqlite3
import urllib.parse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import random
import string
import csv
import io

DB_FILE = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

ADMIN_PASSWORD = "admin"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            child_name TEXT,
            child_age INTEGER,
            city TEXT,
            parent_name TEXT,
            parent_phone TEXT,
            parent_email TEXT,
            ticket_number TEXT UNIQUE,
            result_profile TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_type TEXT PRIMARY KEY,
            filename TEXT,
            original_name TEXT,
            uploaded_at TEXT
        )
    ''')
    
    defaults = {
        'branch_name': 'Ковельська філія',
        'phone': '+380 (67) 555-43-21',
        'email': 'kovel@itstep.org',
        'address': 'м. Ковель, вул. Незалежності, 1',
        'telegram': '@itstep_kovel'
    }
    for k, v in defaults.items():
        c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (k, v))
    conn.commit()
    conn.close()

init_db()

def get_settings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT key, value FROM settings')
    rows = c.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def update_settings(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for k, v in data.items():
        c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (k, str(v)))
    conn.commit()
    conn.close()

def generate_ticket():
    digits = ''.join(random.choices(string.digits, k=6))
    return f"ITS-{digits}"

class QuizRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message, status=400):
        self._send_json({'error': message}, status=status)

    def _send_file(self, filepath, content_type=None, filename=None):
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return
        if content_type is None:
            content_type, _ = mimetypes.guess_type(filepath)
            content_type = content_type or 'application/octet-stream'
        with open(filepath, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        if filename:
            encoded_fn = urllib.parse.quote(filename)
            self.send_header('Content-Disposition', f'attachment; filename="{encoded_fn}"; filename*=UTF-8\'\'{encoded_fn}')
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == '/api/settings':
            self._send_json(get_settings())
            return

        if path == '/api/admin/leads':
            auth_header = self.headers.get('Authorization', '')
            if auth_header != f'Bearer {ADMIN_PASSWORD}' and query.get('pwd', [''])[0] != ADMIN_PASSWORD:
                self._send_error('Unauthorized', 401)
                return
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT id, created_at, child_name, child_age, city, parent_name, parent_phone, parent_email, ticket_number, result_profile FROM leads ORDER BY id DESC')
            rows = c.fetchall()
            conn.close()
            leads = [{
                'id': r[0],
                'created_at': r[1],
                'child_name': r[2],
                'child_age': r[3],
                'city': r[4],
                'parent_name': r[5],
                'parent_phone': r[6],
                'parent_email': r[7],
                'ticket_number': r[8],
                'result_profile': r[9]
            } for r in rows]
            self._send_json({'leads': leads})
            return

        if path == '/api/admin/leads/export':
            pwd = query.get('pwd', [''])[0]
            if pwd != ADMIN_PASSWORD:
                self.send_error(401, 'Unauthorized')
                return
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT id, created_at, child_name, child_age, city, parent_name, parent_phone, parent_email, ticket_number, result_profile FROM leads ORDER BY id DESC')
            rows = c.fetchall()
            conn.close()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Дата створення', 'Ім\'я дитини', 'Вік дитини', 'Місто', 'Ім\'я батьків', 'Телефон батьків', 'Email батьків', 'Номер квитка', 'IT-Профіль'])
            for r in rows:
                writer.writerow(r)
            
            csv_bytes = ('\ufeff' + output.getvalue()).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="leads_itstep.csv"')
            self.send_header('Content-Length', str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        if path == '/api/files/download':
            file_type = query.get('type', [''])[0]
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT filename, original_name FROM files WHERE file_type = ?', (file_type,))
            row = c.fetchone()
            conn.close()
            if row:
                filepath = os.path.join(UPLOADS_DIR, row[0])
                if os.path.exists(filepath):
                    self._send_file(filepath, filename=row[1])
                    return
            
            if file_type == 'parent_guide':
                filepath = os.path.join(PUBLIC_DIR, 'assets', 'default_guide.pdf')
                if os.path.exists(filepath):
                    self._send_file(filepath, filename='IT_Guide_For_Parents.pdf')
                    return
            self._send_error("Файл ще не завантажено в адмінпанелі", 404)
            return

        if path == '/api/admin/files':
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT file_type, filename, original_name, uploaded_at FROM files')
            rows = c.fetchall()
            conn.close()
            files_dict = {r[0]: {'filename': r[1], 'original_name': r[2], 'uploaded_at': r[3]} for r in rows}
            self._send_json(files_dict)
            return

        req_path = path.lstrip('/')
        if not req_path:
            req_path = 'index.html'
        filepath = os.path.join(PUBLIC_DIR, req_path)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            self._send_file(filepath)
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        if path == '/api/admin/login':
            try:
                data = json.loads(body.decode('utf-8'))
                if data.get('password') == ADMIN_PASSWORD:
                    self._send_json({'success': True, 'token': ADMIN_PASSWORD})
                else:
                    self._send_error('Невірний пароль адміністратора', 401)
            except Exception as e:
                self._send_error(str(e), 400)
            return

        if path == '/api/admin/settings':
            auth_header = self.headers.get('Authorization', '')
            if auth_header != f'Bearer {ADMIN_PASSWORD}':
                self._send_error('Unauthorized', 401)
                return
            try:
                data = json.loads(body.decode('utf-8'))
                update_settings(data)
                self._send_json({'success': True, 'settings': get_settings()})
            except Exception as e:
                self._send_error(str(e), 400)
            return

        if path == '/api/register':
            try:
                data = json.loads(body.decode('utf-8'))
                child_name = data.get('child_name', '').strip()
                child_age = int(data.get('child_age', 0))
                city = data.get('city', '').strip()
                parent_name = data.get('parent_name', '').strip()
                parent_phone = data.get('parent_phone', '').strip()
                parent_email = data.get('parent_email', '').strip()

                if not (child_name and child_age and city and parent_name and parent_phone and parent_email):
                    self._send_error('Будь ласка, заповніть всі поля форми', 400)
                    return

                ticket_number = generate_ticket()
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO leads (created_at, child_name, child_age, city, parent_name, parent_phone, parent_email, ticket_number, result_profile)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (created_at, child_name, child_age, city, parent_name, parent_phone, parent_email, ticket_number, 'Очікує проходження квізу'))
                conn.commit()
                lead_id = c.lastrowid
                conn.close()

                self._send_json({
                    'success': True,
                    'lead_id': lead_id,
                    'ticket_number': ticket_number,
                    'child_name': child_name
                })
            except Exception as e:
                self._send_error(f"Помилка реєстрації: {str(e)}", 400)
            return

        if path == '/api/update-result':
            try:
                data = json.loads(body.decode('utf-8'))
                lead_id = data.get('lead_id')
                result_profile = data.get('result_profile', '').strip()

                if lead_id and result_profile:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute('UPDATE leads SET result_profile = ? WHERE id = ?', (result_profile, lead_id))
                    conn.commit()
                    conn.close()
                self._send_json({'success': True})
            except Exception as e:
                self._send_error(str(e), 400)
            return

        if path == '/api/admin/upload':
            auth_header = self.headers.get('Authorization', '')
            if auth_header != f'Bearer {ADMIN_PASSWORD}':
                self._send_error('Unauthorized', 401)
                return

            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_error('Invalid content type', 400)
                return

            boundary = content_type.split('boundary=')[1].encode()
            parts = body.split(b'--' + boundary)
            
            file_type = None
            file_data = None
            original_filename = "file.pdf"

            for part in parts:
                if b'name="file_type"' in part:
                    file_type = part.split(b'\r\n\r\n')[1].split(b'\r\n')[0].decode('utf-8').strip()
                elif b'name="file"' in part:
                    headers_part = part.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
                    if 'filename="' in headers_part:
                        original_filename = headers_part.split('filename="')[1].split('"')[0]
                    file_data = part.split(b'\r\n\r\n')[1].rstrip(b'\r\n--')

            if file_type and file_data:
                filename = f"{file_type}_{int(datetime.now().timestamp())}.pdf"
                filepath = os.path.join(UPLOADS_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(file_data)

                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                uploaded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute('INSERT OR REPLACE INTO files (file_type, filename, original_name, uploaded_at) VALUES (?, ?, ?, ?)',
                          (file_type, filename, original_filename, uploaded_at))
                conn.commit()
                conn.close()

                self._send_json({'success': True, 'filename': filename, 'original_name': original_filename})
            else:
                self._send_error('Помилка завантаження файла', 400)
            return

handler = QuizRequestHandler
app = QuizRequestHandler

def run(port=8080):
    port = int(os.environ.get('PORT', port))
    server_address = ('', port)
    httpd = HTTPServer(server_address, QuizRequestHandler)
    print(f"Сервер воронки продажів ITSTEP запущено на порту {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
