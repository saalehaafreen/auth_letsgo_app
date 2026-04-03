from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    full_name    = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


# ── SIGNUP (called from Rork app) ──────────────────────────
@app.route('/api/auth/signup/', methods=['POST'])
def signup():
    data = request.get_json()

    full_name    = data.get('fullName')
    username     = data.get('username')
    phone_number = data.get('phoneNumber')
    password     = data.get('password')

    if not all([full_name, username, phone_number, password]):
        return jsonify({'message': 'All fields are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409

    new_user = User(
        username=username,
        full_name=full_name,
        phone_number=phone_number,
        password=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'user': {
            'id':          str(new_user.id),
            'username':    new_user.username,
            'fullName':    new_user.full_name,
            'phoneNumber': new_user.phone_number,
        }
    }), 201


# ── LOGIN (called from Rork app) ───────────────────────────
@app.route('/api/auth/login/', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    return jsonify({
        'user': {
            'id':          str(user.id),
            'username':    user.username,
            'fullName':    user.full_name,
            'phoneNumber': user.phone_number,
        }
    }), 200


# ── JSON API for users list (optional) ────────────────────
@app.route('/api/users', methods=['GET'])
def api_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'total': len(users),
        'users': [
            {
                'id':          u.id,
                'username':    u.username,
                'fullName':    u.full_name,
                'phoneNumber': u.phone_number,
                'createdAt':   u.created_at.strftime('%Y-%m-%d %H:%M')
            } for u in users
        ]
    })


# ── WEBPAGE: live list of registered users ─────────────────
@app.route('/users')
def show_users():
    users = User.query.order_by(User.created_at.desc()).all()

    rows = ""
    for user in users:
        initials = ''.join([n[0].upper() for n in user.full_name.split()[:2]])
        joined   = user.created_at.strftime('%d %b %Y, %H:%M')
        rows += f"""
        <tr>
          <td><div class="avatar">{initials}</div></td>
          <td><strong>{user.username}</strong></td>
          <td>{user.full_name}</td>
          <td>{user.phone_number}</td>
          <td><span class="lock">🔒 hidden</span></td>
          <td class="date">{joined}</td>
        </tr>
        """

    if not rows:
        rows = '<tr><td colspan="6" class="empty">No users registered yet. Sign up in the app!</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registered Users</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f0f2f5;
      padding: 30px 20px;
      color: #333;
    }}
    .header {{
      max-width: 960px;
      margin: 0 auto 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .header h1 {{ font-size: 22px; font-weight: 600; }}
    .header p {{ font-size: 13px; color: #888; margin-top: 3px; }}
    .badge {{
      background: #4f46e5;
      color: white;
      padding: 6px 16px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 500;
    }}
    .refresh-note {{
      max-width: 960px;
      margin: 0 auto 12px;
      font-size: 12px;
      color: #aaa;
      text-align: right;
    }}
    .table-wrap {{
      max-width: 960px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    thead {{ background: #4f46e5; color: white; }}
    th {{ padding: 14px 18px; text-align: left; font-size: 13px; font-weight: 500; }}
    td {{ padding: 14px 18px; border-bottom: 1px solid #f0f0f0; font-size: 14px; vertical-align: middle; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #fafaff; }}
    .avatar {{
      width: 36px; height: 36px; border-radius: 50%;
      background: #e0e7ff; color: #4f46e5;
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 600;
    }}
    .lock {{ color: #999; font-size: 12px; }}
    .date {{ color: #aaa; font-size: 12px; }}
    .empty {{
      text-align: center; padding: 50px;
      color: #bbb; font-size: 15px;
    }}
    #last-updated {{
      font-size: 12px;
      color: #aaa;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>📋 Registered Users</h1>
      <p>Users who signed up via the Rork app</p>
    </div>
    <span class="badge">{len(users)} user(s)</span>
  </div>

  <div class="refresh-note">
    Auto-refreshes every 10 seconds &nbsp;|&nbsp;
    <span id="last-updated">Last updated: just now</span>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th></th>
          <th>Username</th>
          <th>Full Name</th>
          <th>Phone Number</th>
          <th>Password</th>
          <th>Joined</th>
        </tr>
      </thead>
      <tbody id="user-tbody">
        {rows}
      </tbody>
    </table>
  </div>

  <script>
    // Auto-refresh the user list every 10 seconds without full page reload
    async function refreshUsers() {{
      try {{
        const res  = await fetch('/api/users');
        const data = await res.json();
        const tbody = document.getElementById('user-tbody');

        if (data.users.length === 0) {{
          tbody.innerHTML = '<tr><td colspan="6" class="empty">No users registered yet. Sign up in the app!</td></tr>';
          return;
        }}

        tbody.innerHTML = data.users.map(u => {{
          const initials = u.fullName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0,2);
          return `
            <tr>
              <td><div class="avatar">${{initials}}</div></td>
              <td><strong>${{u.username}}</strong></td>
              <td>${{u.fullName}}</td>
              <td>${{u.phoneNumber}}</td>
              <td><span class="lock">🔒 hidden</span></td>
              <td class="date">${{u.createdAt}}</td>
            </tr>`;
        }}).join('');

        document.querySelector('.badge').textContent = data.total + ' user(s)';
        document.getElementById('last-updated').textContent =
          'Last updated: ' + new Date().toLocaleTimeString();

      }} catch(e) {{
        console.error('Refresh failed', e);
      }}
    }}

    setInterval(refreshUsers, 10000);
  </script>
</body>
</html>"""
    return html


@app.route('/')
def home():
    return '<meta http-equiv="refresh" content="0; url=/users">'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
