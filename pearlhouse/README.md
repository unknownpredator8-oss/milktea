# 🧋 PearlHouse — Milk Tea POS System

A full-stack Point of Sale system for milk tea shops with:
- **Frontend**: Beautiful HTML/CSS/JS single-page app
- **Backend**: Python Flask REST API
- **Database**: MySQL (production) or SQLite (development/free hosting)

## 📁 Project Structure
```
pearlhouse/
├── app.py            ← Flask backend (all API routes)
├── schema.sql        ← MySQL schema + seed data
├── requirements.txt  ← Python dependencies
├── Procfile          ← For Railway/Render
├── render.yaml       ← Render one-click config
├── railway.json      ← Railway config
└── static/
    └── index.html    ← Frontend (served by Flask)
```

## 🚀 Free Deployment Options

### Option A: Render.com (Recommended — Free SQLite)
1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` → click **Deploy**
5. Your app is live at `https://pearlhouse-pos.onrender.com`

> **Free tier note**: Render free tier sleeps after 15 min inactivity. First load may be slow.

### Option B: Railway.app (Free $5 credit/month)
1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add a **MySQL** plugin from Railway marketplace (free tier available)
4. Set environment variables:
   ```
   DB_TYPE=mysql
   MYSQL_HOST=${{MySQL.MYSQL_HOST}}
   MYSQL_USER=${{MySQL.MYSQL_USER}}
   MYSQL_PASSWORD=${{MySQL.MYSQL_PASSWORD}}
   MYSQL_DB=${{MySQL.MYSQL_DATABASE}}
   SECRET_KEY=any-random-secret
   ```
5. Run `schema.sql` in Railway's MySQL console
6. Deploy!

### Option C: PythonAnywhere (Free tier)
1. Create free account at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload all files via Files tab
3. Go to **Web** tab → Add new web app → Flask
4. Set source code to your upload folder
5. In **Databases** tab: create MySQL DB, run `schema.sql`
6. Set environment variables in the web app config:
   ```
   DB_TYPE=mysql
   MYSQL_HOST=yourusername.mysql.pythonanywhere-services.com
   MYSQL_USER=yourusername
   MYSQL_PASSWORD=yourpassword
   MYSQL_DB=yourusername$pearlhouse
   ```

## 🖥️ Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run with SQLite (no MySQL needed)
python app.py

# Run with MySQL
DB_TYPE=mysql MYSQL_HOST=localhost MYSQL_USER=root MYSQL_PASSWORD=pass MYSQL_DB=pearlhouse python app.py
```

Visit: http://localhost:5000

## 🔑 Default Login
| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | admin123  |
| Staff | staff    | staff123  |

> ⚠️ Change passwords after first login via Settings → Profile

## 📡 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET/POST | `/api/menu` | List / Add menu items |
| PUT/DELETE | `/api/menu/:id` | Edit / Delete item |
| GET/POST | `/api/ingredients` | Manage ingredients |
| PUT/DELETE | `/api/ingredients/:id` | Edit / Delete ingredient |
| GET/PUT | `/api/menu/:id/ingredients` | Link ingredients to menu item |
| GET/POST | `/api/orders` | List / Create orders |
| PUT | `/api/orders/:id` | Advance order status |
| GET | `/api/transactions` | All transactions |
| GET/POST | `/api/users` | List / Add staff |
| PUT/DELETE | `/api/users/:id` | Edit / Delete user |
| GET | `/api/logs` | User activity logs |
| GET | `/api/stats` | Dashboard statistics |
| GET/POST | `/api/settings` | System settings |

## 🛠️ Tech Stack
- **Frontend**: Vanilla JS + GSAP animations + Chart.js
- **Backend**: Python Flask + Flask-CORS
- **Database**: MySQL (prod) / SQLite (dev)
- **Auth**: Flask sessions (cookie-based)
