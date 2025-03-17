import psycopg, asyncio, os
from dotenv import load_dotenv
from flask import Flask, g, redirect, url_for, render_template
from flask_login import LoginManager, login_required, current_user
from library_manager import dbq


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define user loader
@login_manager.user_loader
def load_user(user_id):
    # Implement user loader function
    return User.get(user_id)

async def init_db():
    return await psycopg.AsyncConnection.connect(DATABASE_URL)

async def close_db(conn):
    await conn.close()

@app.before_request
async def before_req():
    print("initdb")
    g.db = await init_db()

@app.teardown_request
async def teardown(exception):
    print("teardown")
    db = g.get('db', None)
    if db is not None:
        await close_db(db)

@app.route("/")
def home():
    print("load")
    return render_template("home.html")

@app.route("/search")
def search():
    return "<p>Search Library</p>"


@app.route("/logout")
@login_required
def logout():
    # Implement logout functionality
    return redirect(url_for('home'))

@app.route("/review_manager")
@login_required
def review_manager():
    return "<p>Review Manager</p>"

@app.route("/manage_library")
@login_required
def manage_library():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>Manage Library</p>"

@app.route("/manage_reviews")
@login_required
def manage_reviews():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>Manage Reviews</p>"

@app.route("/manage_other")
@login_required
def manage_other():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>Manage Other</p>"

@app.route("/review_statistics")
@login_required
def review_statistics():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    return "<p>Review Statistics</p>"

@app.route("/manage_users")
@login_required
def manage_users():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    return "<p>Manage Users</p>"

@app.route("/login")
def login():
    # Implement login functionality
    return "<p>Login</p>"
