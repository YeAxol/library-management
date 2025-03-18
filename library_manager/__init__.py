from urllib.parse import urlparse
import psycopg, asyncio, os
from dotenv import load_dotenv
from flask import Flask, g, redirect, url_for, render_template, request  # Import request here
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from library_manager import dbq
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


### DB Setup and Teardown to keep connections fresh

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

### Login Logic

def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=os.path.join(os.path.dirname(__file__), 'saml'))
    return auth

def prepare_flask_request(request):
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }

@login_manager.user_loader
def load_user(user_id):
    # Implement user loading logic here
    return asyncio.run(dbq.getUser(g.db, user_id))

@app.route("/login")
def login():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.login())

@app.route("/saml/acs", methods=['POST'])
async def saml_acs():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    if not errors:
        if auth.is_authenticated():
            
            user_data = auth.get_attributes()
            email = user_data.get('email')[0]  # Adjust based on your SAML attributes

            conn = g.db
            #first check if user invited then create user
            #invite deleted user cannot sign in, even if user exists
            #TODO: how to handle alum?
            #use as easy way to deactivate users without removing user entry?
            if not await dbq.getUserInvite(conn, email):
                return redirect(url_for('home'))

            first_name = user_data.get('first_name')[0]  # Adjust based on your SAML attributes
            last_name = user_data.get('last_name')[0]  # Adjust based on your SAML attributes

            user_id = await dbq.getUserUUID(conn, email)
            if not user_id:
                user_id = await dbq.addUser(conn, first_name, last_name, email)
            user = await dbq.getUser(user_id)
            login_user(user)

            return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route("/saml/sls", methods=['GET', 'POST'])
def saml_sls():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_slo()
    return redirect(url_for('home'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

### Routes

@app.route("/")
@app.route("/home")
def home():
    page = int(request.args.get('page', 1))
    title = request.args.get('', '')
    artist = request.args.get('artist', '')
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')

    conn = g.db
    albums, has_next = await dbq.get_albums(conn, title, artist, genre, year, page)

    return render_template("home.html", albums=albums, page=page, has_next=has_next)


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
