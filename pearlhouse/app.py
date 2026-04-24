"""
PearlHouse Milk Tea POS — Flask Backend
Supports MySQL (production) and SQLite (fallback/dev)
"""

import os, json, datetime
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'pearlhouse-secret-2024')
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000',
     'https://*.render.com', 'https://*.railway.app', 'https://*.pythonanywhere.com'])

# ─── DATABASE SETUP ────────────────────────────────────────────────────────────
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # 'mysql' or 'sqlite'

def get_db():
    if DB_TYPE == 'mysql':
        import pymysql
        return pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DB', 'pearlhouse'),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            charset='utf8mb4'
        )
    else:
        import sqlite3
        db_path = os.environ.get('SQLITE_PATH', 'pearlhouse.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

def query(sql, params=(), one=False, commit=False):
    """Universal query helper for both MySQL and SQLite."""
    conn = get_db()
    try:
        if DB_TYPE == 'mysql':
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if commit or sql.strip().upper().startswith(('INSERT','UPDATE','DELETE','CREATE','DROP','ALTER')):
                    conn.commit()
                if sql.strip().upper().startswith('INSERT') and not one:
                    return cur.lastrowid
                rows = cur.fetchall()
                return (dict(rows[0]) if rows else None) if one else [dict(r) for r in rows]
        else:
            # SQLite: adapt %s → ?
            sql_lite = sql.replace('%s', '?')
            cur = conn.execute(sql_lite, params)
            if commit or sql_lite.strip().upper().startswith(('INSERT','UPDATE','DELETE')):
                conn.commit()
            if sql_lite.strip().upper().startswith('INSERT') and not one:
                return cur.lastrowid
            rows = cur.fetchall()
            return (dict(rows[0]) if rows else None) if one else [dict(r) for r in rows]
    finally:
        conn.close()

def init_db():
    """Initialize SQLite database with schema (MySQL uses schema.sql separately)."""
    if DB_TYPE == 'sqlite':
        schema = """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL,
          display_name TEXT,
          role TEXT DEFAULT 'staff',
          image TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS menu_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          price REAL NOT NULL,
          category TEXT DEFAULT 'Milk Tea',
          emoji TEXT DEFAULT '🧋',
          stock INTEGER DEFAULT 0,
          available INTEGER DEFAULT 1,
          image TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS ingredients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          emoji TEXT DEFAULT '🧉',
          unit TEXT DEFAULT 'pcs',
          stock REAL DEFAULT 0,
          threshold REAL DEFAULT 0,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS item_ingredients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          menu_item_id INTEGER NOT NULL,
          ingredient_id INTEGER NOT NULL,
          qty REAL NOT NULL DEFAULT 0,
          UNIQUE(menu_item_id, ingredient_id)
        );
        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_num INTEGER NOT NULL,
          total REAL NOT NULL,
          payment TEXT DEFAULT 'cash',
          status TEXT DEFAULT 'preparing',
          staff TEXT,
          created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS order_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_id INTEGER NOT NULL,
          menu_item_id INTEGER,
          name TEXT NOT NULL,
          price REAL NOT NULL,
          qty INTEGER NOT NULL DEFAULT 1,
          emoji TEXT DEFAULT '🧋'
        );
        CREATE TABLE IF NOT EXISTS user_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT,
          role TEXT,
          action TEXT DEFAULT 'login',
          timestamp TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS settings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          key_name TEXT UNIQUE NOT NULL,
          value_text TEXT
        );
        """
        conn = get_db()
        for stmt in schema.strip().split(';'):
            s = stmt.strip()
            if s:
                conn.execute(s)
        conn.commit()

        # Seed data if empty
        cur = conn.execute("SELECT COUNT(*) as c FROM users")
        if cur.fetchone()['c'] == 0:
            seed_sqlite(conn)
        conn.close()

def seed_sqlite(conn):
    conn.execute("INSERT OR IGNORE INTO users(username,password,display_name,role) VALUES(?,?,?,?)",
                 ('admin','admin123','Administrator','admin'))
    conn.execute("INSERT OR IGNORE INTO users(username,password,display_name,role) VALUES(?,?,?,?)",
                 ('staff','staff123','Staff User','staff'))
    menu = [
        (1,'Classic Pearl Milk Tea',85,'Milk Tea','🧋',50,1),
        (2,'Taro Milk Tea',95,'Milk Tea','💜',45,1),
        (3,'Brown Sugar Boba',100,'Milk Tea','🤎',40,1),
        (4,'Matcha Latte',110,'Milk Tea','🍵',35,1),
        (5,'Mango Fruit Tea',85,'Fruit Tea','🥭',50,1),
        (6,'Strawberry Tea',90,'Fruit Tea','🍓',48,1),
        (7,'Lychee Tea',88,'Fruit Tea','🍈',42,1),
        (8,'Passion Fruit Tea',92,'Fruit Tea','🍊',38,1),
        (9,'Mango Slush',95,'Slush','🧊',30,1),
        (10,'Strawberry Slush',95,'Slush','🌸',30,1),
    ]
    for m in menu:
        conn.execute("INSERT OR IGNORE INTO menu_items(id,name,price,category,emoji,stock,available) VALUES(?,?,?,?,?,?,?)", m)
    ings = [
        (101,'Tapioca Pearls','⚫','kg',5,1),(102,'Fresh Milk','🥛','L',12,3),
        (103,'Black Tea','🍃','kg',2,0.5),(104,'Taro Powder','💜','kg',3,0.5),
        (105,'Brown Sugar Syrup','🍯','bottles',8,2),(106,'Matcha Powder','🍵','kg',1.5,0.3),
        (107,'Mango Puree','🥭','kg',4,1),(108,'Strawberry Puree','🍓','kg',3,1),
        (109,'Lychee Syrup','🍈','bottles',5,2),(110,'Passion Fruit Syrup','🍊','bottles',4,2),
        (111,'Sugar Syrup','🍬','L',6,1),(112,'Cups & Lids','🥤','pcs',500,100),
    ]
    for i in ings:
        conn.execute("INSERT OR IGNORE INTO ingredients(id,name,emoji,unit,stock,threshold) VALUES(?,?,?,?,?,?)", i)
    links = [
        (1,101,.05),(1,102,.3),(1,103,.01),(1,111,.02),(1,112,1),
        (2,101,.05),(2,102,.3),(2,104,.02),(2,111,.02),(2,112,1),
        (3,101,.05),(3,102,.3),(3,105,.05),(3,112,1),
        (4,102,.3),(4,106,.015),(4,111,.02),(4,112,1),
        (5,107,.1),(5,103,.01),(5,111,.02),(5,112,1),
        (6,108,.1),(6,103,.01),(6,111,.02),(6,112,1),
        (7,109,.05),(7,103,.01),(7,111,.02),(7,112,1),
        (8,110,.05),(8,103,.01),(8,111,.02),(8,112,1),
        (9,107,.12),(9,111,.02),(9,112,1),
        (10,108,.12),(10,111,.02),(10,112,1),
    ]
    for l in links:
        conn.execute("INSERT OR IGNORE INTO item_ingredients(menu_item_id,ingredient_id,qty) VALUES(?,?,?)", l)
    conn.commit()

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def next_order_num():
    row = query("SELECT MAX(order_num) as mx FROM orders", one=True)
    return (row['mx'] or 1000) + 1 if row else 1001

def fmt_row(row):
    """Convert Row/dict to plain dict with None-safe values."""
    if row is None:
        return None
    d = dict(row)
    # Booleans
    for k in ('available',):
        if k in d:
            d[k] = bool(d[k])
    return d

# ─── HEALTH ────────────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'db': DB_TYPE})

# ─── STATIC / SPA ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ─── AUTH ──────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = query("SELECT * FROM users WHERE username=%s AND password=%s", (username, password), one=True)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    session['user_id'] = user['id']
    session['role'] = user['role']
    # Log
    query("INSERT INTO user_logs(username,role,action) VALUES(%s,%s,%s)",
          (username, user['role'], 'login'), commit=True)
    user.pop('password', None)
    return jsonify({'user': fmt_row(user)})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/me')
@require_login
def me():
    user = query("SELECT * FROM users WHERE id=%s", (session['user_id'],), one=True)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.pop('password', None)
    return jsonify({'user': fmt_row(user)})

# ─── MENU ──────────────────────────────────────────────────────────────────────
@app.route('/api/menu', methods=['GET'])
@require_login
def get_menu():
    items = query("SELECT * FROM menu_items ORDER BY category, name")
    return jsonify({'items': [fmt_row(i) for i in items]})

@app.route('/api/menu', methods=['POST'])
@require_admin
def add_menu():
    d = request.json or {}
    lid = query(
        "INSERT INTO menu_items(name,price,category,emoji,stock,available,image) VALUES(%s,%s,%s,%s,%s,%s,%s)",
        (d.get('name'), d.get('price', 0), d.get('category', 'Milk Tea'),
         d.get('emoji', '🧋'), d.get('stock', 0), 1, d.get('image')), commit=True)
    item = query("SELECT * FROM menu_items WHERE id=%s", (lid,), one=True)
    return jsonify({'item': fmt_row(item)}), 201

@app.route('/api/menu/<int:item_id>', methods=['PUT'])
@require_admin
def update_menu(item_id):
    d = request.json or {}
    fields = []
    vals = []
    for k in ('name', 'price', 'category', 'emoji', 'stock', 'available', 'image'):
        if k in d:
            fields.append(f"{k}=%s")
            vals.append(d[k])
    if fields:
        vals.append(item_id)
        query(f"UPDATE menu_items SET {','.join(fields)} WHERE id=%s", vals, commit=True)
    item = query("SELECT * FROM menu_items WHERE id=%s", (item_id,), one=True)
    return jsonify({'item': fmt_row(item)})

@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
@require_admin
def delete_menu(item_id):
    query("DELETE FROM menu_items WHERE id=%s", (item_id,), commit=True)
    return jsonify({'ok': True})

# ─── INGREDIENTS ───────────────────────────────────────────────────────────────
@app.route('/api/ingredients', methods=['GET'])
@require_login
def get_ingredients():
    ings = query("SELECT * FROM ingredients ORDER BY name")
    return jsonify({'ingredients': [fmt_row(i) for i in ings]})

@app.route('/api/ingredients', methods=['POST'])
@require_admin
def add_ingredient():
    d = request.json or {}
    lid = query(
        "INSERT INTO ingredients(name,emoji,unit,stock,threshold) VALUES(%s,%s,%s,%s,%s)",
        (d.get('name'), d.get('emoji', '🧉'), d.get('unit', 'pcs'),
         d.get('stock', 0), d.get('threshold', 0)), commit=True)
    ing = query("SELECT * FROM ingredients WHERE id=%s", (lid,), one=True)
    return jsonify({'ingredient': fmt_row(ing)}), 201

@app.route('/api/ingredients/<int:ing_id>', methods=['PUT'])
@require_admin
def update_ingredient(ing_id):
    d = request.json or {}
    fields, vals = [], []
    for k in ('name', 'emoji', 'unit', 'stock', 'threshold'):
        if k in d:
            fields.append(f"{k}=%s")
            vals.append(d[k])
    if fields:
        vals.append(ing_id)
        query(f"UPDATE ingredients SET {','.join(fields)} WHERE id=%s", vals, commit=True)
    ing = query("SELECT * FROM ingredients WHERE id=%s", (ing_id,), one=True)
    return jsonify({'ingredient': fmt_row(ing)})

@app.route('/api/ingredients/<int:ing_id>', methods=['DELETE'])
@require_admin
def delete_ingredient(ing_id):
    query("DELETE FROM ingredients WHERE id=%s", (ing_id,), commit=True)
    return jsonify({'ok': True})

# ─── ITEM INGREDIENTS (links) ──────────────────────────────────────────────────
@app.route('/api/menu/<int:item_id>/ingredients', methods=['GET'])
@require_login
def get_item_ingredients(item_id):
    links = query(
        "SELECT ii.*, i.name, i.emoji, i.unit FROM item_ingredients ii "
        "JOIN ingredients i ON ii.ingredient_id=i.id WHERE ii.menu_item_id=%s", (item_id,))
    return jsonify({'links': [fmt_row(l) for l in links]})

@app.route('/api/menu/<int:item_id>/ingredients', methods=['PUT'])
@require_admin
def save_item_ingredients(item_id):
    d = request.json or {}
    links = d.get('links', [])
    query("DELETE FROM item_ingredients WHERE menu_item_id=%s", (item_id,), commit=True)
    for lnk in links:
        query("INSERT INTO item_ingredients(menu_item_id,ingredient_id,qty) VALUES(%s,%s,%s)",
              (item_id, lnk['ingId'], lnk['qty']), commit=True)
    return jsonify({'ok': True})

# ─── ORDERS ────────────────────────────────────────────────────────────────────
@app.route('/api/orders', methods=['GET'])
@require_login
def get_orders():
    orders = query("SELECT * FROM orders ORDER BY created_at DESC LIMIT 200")
    result = []
    for o in orders:
        o = fmt_row(o)
        items = query("SELECT * FROM order_items WHERE order_id=%s", (o['id'],))
        o['items'] = [fmt_row(i) for i in items]
        result.append(o)
    return jsonify({'orders': result})

@app.route('/api/orders', methods=['POST'])
@require_login
def create_order():
    d = request.json or {}
    items = d.get('items', [])
    total = d.get('total', 0)
    payment = d.get('payment', 'cash')
    staff = d.get('staff') or session.get('username', 'staff')
    onum = next_order_num()

    oid = query(
        "INSERT INTO orders(order_num,total,payment,status,staff) VALUES(%s,%s,%s,%s,%s)",
        (onum, total, payment, 'preparing', staff), commit=True)

    for it in items:
        query("INSERT INTO order_items(order_id,menu_item_id,name,price,qty,emoji) VALUES(%s,%s,%s,%s,%s,%s)",
              (oid, it.get('id'), it.get('name'), it.get('price', 0), it.get('qty', 1), it.get('emoji', '🧋')), commit=True)
        # Deduct menu item stock
        query("UPDATE menu_items SET stock=MAX(0,stock-%s) WHERE id=%s",
              (it.get('qty', 1), it.get('id')), commit=True)
        # Deduct ingredient stock
        ing_links = query("SELECT * FROM item_ingredients WHERE menu_item_id=%s", (it.get('id'),))
        for lnk in ing_links:
            query("UPDATE ingredients SET stock=MAX(0,stock-%s) WHERE id=%s",
                  (float(lnk['qty']) * it.get('qty', 1), lnk['ingredient_id']), commit=True)

    order = query("SELECT * FROM orders WHERE id=%s", (oid,), one=True)
    order = fmt_row(order)
    order_items_rows = query("SELECT * FROM order_items WHERE order_id=%s", (oid,))
    order['items'] = [fmt_row(r) for r in order_items_rows]
    return jsonify({'order': order}), 201

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
@require_login
def update_order(order_id):
    d = request.json or {}
    status = d.get('status', 'preparing')
    query("UPDATE orders SET status=%s WHERE id=%s", (status, order_id), commit=True)
    order = query("SELECT * FROM orders WHERE id=%s", (order_id,), one=True)
    order = fmt_row(order)
    order_items_rows = query("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    order['items'] = [fmt_row(r) for r in order_items_rows]
    return jsonify({'order': order})

# ─── TRANSACTIONS ──────────────────────────────────────────────────────────────
@app.route('/api/transactions', methods=['GET'])
@require_login
def get_transactions():
    orders = query("SELECT * FROM orders ORDER BY created_at DESC LIMIT 500")
    result = []
    for o in orders:
        o = fmt_row(o)
        items = query("SELECT * FROM order_items WHERE order_id=%s", (o['id'],))
        o['items'] = [fmt_row(i) for i in items]
        result.append(o)
    return jsonify({'transactions': result})

# ─── USERS ─────────────────────────────────────────────────────────────────────
@app.route('/api/users', methods=['GET'])
@require_admin
def get_users():
    users = query("SELECT id,username,display_name,role,image,created_at FROM users ORDER BY role,username")
    return jsonify({'users': [fmt_row(u) for u in users]})

@app.route('/api/users', methods=['POST'])
@require_admin
def add_user():
    d = request.json or {}
    username = d.get('username', '').strip()
    password = d.get('password', '')
    display_name = d.get('display_name', username)
    role = d.get('role', 'staff')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    existing = query("SELECT id FROM users WHERE username=%s", (username,), one=True)
    if existing:
        return jsonify({'error': 'Username already exists'}), 409
    lid = query("INSERT INTO users(username,password,display_name,role) VALUES(%s,%s,%s,%s)",
                (username, password, display_name, role), commit=True)
    user = query("SELECT id,username,display_name,role,image FROM users WHERE id=%s", (lid,), one=True)
    return jsonify({'user': fmt_row(user)}), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_login
def update_user(user_id):
    # Users can only edit themselves; admins can edit anyone
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    d = request.json or {}
    fields, vals = [], []
    for k in ('display_name', 'image'):
        if k in d:
            fields.append(f"{k}=%s")
            vals.append(d[k])
    if 'password' in d and d['password']:
        fields.append("password=%s")
        vals.append(d['password'])
    if fields:
        vals.append(user_id)
        query(f"UPDATE users SET {','.join(fields)} WHERE id=%s", vals, commit=True)
    user = query("SELECT id,username,display_name,role,image FROM users WHERE id=%s", (user_id,), one=True)
    return jsonify({'user': fmt_row(user)})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete yourself'}), 400
    query("DELETE FROM users WHERE id=%s", (user_id,), commit=True)
    return jsonify({'ok': True})

# ─── LOGS ──────────────────────────────────────────────────────────────────────
@app.route('/api/logs', methods=['GET'])
@require_admin
def get_logs():
    logs = query("SELECT * FROM user_logs ORDER BY timestamp DESC LIMIT 500")
    return jsonify({'logs': [fmt_row(l) for l in logs]})

@app.route('/api/logs', methods=['POST'])
@require_login
def add_log():
    d = request.json or {}
    query("INSERT INTO user_logs(username,role,action) VALUES(%s,%s,%s)",
          (d.get('username'), d.get('role'), d.get('action', 'action')), commit=True)
    return jsonify({'ok': True})

# ─── SETTINGS ──────────────────────────────────────────────────────────────────
@app.route('/api/settings', methods=['GET'])
@require_login
def get_settings():
    rows = query("SELECT key_name, value_text FROM settings")
    return jsonify({r['key_name']: r['value_text'] for r in rows})

@app.route('/api/settings', methods=['POST'])
@require_admin
def save_settings():
    d = request.json or {}
    for k, v in d.items():
        existing = query("SELECT id FROM settings WHERE key_name=%s", (k,), one=True)
        if existing:
            query("UPDATE settings SET value_text=%s WHERE key_name=%s", (str(v), k), commit=True)
        else:
            query("INSERT INTO settings(key_name,value_text) VALUES(%s,%s)", (k, str(v)), commit=True)
    return jsonify({'ok': True})

# ─── DASHBOARD STATS ───────────────────────────────────────────────────────────
@app.route('/api/stats')
@require_login
def get_stats():
    period = request.args.get('period', 'today')
    if period == 'today':
        if DB_TYPE == 'mysql':
            date_filter = "DATE(created_at) = CURDATE()"
        else:
            date_filter = "DATE(created_at) = DATE('now')"
    elif period == 'week':
        if DB_TYPE == 'mysql':
            date_filter = "YEARWEEK(created_at) = YEARWEEK(NOW())"
        else:
            date_filter = "created_at >= DATE('now', '-7 days')"
    else:
        if DB_TYPE == 'mysql':
            date_filter = "YEAR(created_at)=YEAR(NOW()) AND MONTH(created_at)=MONTH(NOW())"
        else:
            date_filter = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"

    row = query(f"SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as rev FROM orders WHERE {date_filter}", one=True)
    menu_count = query("SELECT COUNT(*) as cnt FROM menu_items", one=True)
    low_stock = query("SELECT COUNT(*) as cnt FROM ingredients WHERE stock <= threshold", one=True)
    return jsonify({
        'orders': row['cnt'] if row else 0,
        'revenue': float(row['rev']) if row else 0,
        'menu_items': menu_count['cnt'] if menu_count else 0,
        'low_stock': low_stock['cnt'] if low_stock else 0,
    })

# ─── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"🧋 PearlHouse POS starting on port {port} | DB: {DB_TYPE}")
    app.run(host='0.0.0.0', port=port, debug=debug)
