from urllib.parse import urlparse
import psycopg, asyncio, os, requests, json
from dotenv import load_dotenv
from flask import Flask, g, redirect, url_for, render_template, request, session  # Import request here
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin
from library_manager import dbq
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from library_manager.classes import User

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
DISCOGS_API_KEY = os.getenv("DISCOGS_API_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#########
### TEMP REMOVE BEFORE DEPLOY
#########

#there absolutely is a cleaner way to do this, flask-login doesn't like async 
@app.route("/test_login_member")
async def test_login_member():
    conn = g.get('db', None)
    user = await dbq.getUser(conn, "9835f995-0b30-424f-bb85-bea1c3975ff0")
    if user:
        login_user(user)
    return redirect(url_for('home'))

@app.route("/test_login_eboard")
async def test_login_eboard():
    conn = g.get('db', None)
    user = await dbq.getUser(conn, "065b1e2b-5570-4c7e-a097-c4caddde88df")
    if user:
        login_user(user)
    return redirect(url_for('home'))

@app.route("/test_login_staff")
async def test_login_staff():
    conn = g.get('db', None)
    user = await dbq.getUser(conn, "5be598a3-e422-472d-b5c4-53165f717b5f")
    if user:
        login_user(user)
    return redirect(url_for('home'))



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
    with psycopg.Connection.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT userid, firstname, lastname, email, role
                FROM users
                WHERE userid = %s
                """,
                (user_id,),
            )
            user_data = cur.fetchone()
            print("loaduser")
            
            if user_data:
                uid = user_data[0]
                print(uid)
                return User(
                    str(uid),
                    user_data[1],
                    user_data[2],
                    user_data[3],
                    user_data[4],
                )
    return None


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
### Home Page / Search Library

@app.route("/")
@app.route("/search")
async def home():
    entry = int(request.args.get('entry', 0))
    album = request.args.get('album', '')
    artist = request.args.get('artist', '')
    genre = request.args.get('genre', '')
    track = request.args.get('track', '')

    conn = g.db
    albums = await dbq.searchLibrary(conn, album, artist, genre, track, entry)

    return render_template("home.html", albums=albums, entry=entry)

### Review Management

@app.route("/review_manager")
@login_required
def review_manager():
    return "<p>Review Manager</p>"

@app.route("/manage_reviews")
@login_required
def manage_reviews():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>Manage Reviews</p>"

@app.route("/review_statistics")
@login_required
def review_statistics():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    return "<p>Review Statistics</p>"

### Library Management

@app.route("/add_entry")
@login_required
def add_entry():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>Add Entry</p>"

@app.route("/manage_library", methods=['GET', 'POST'])
@login_required
async def manage_library():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))

    album_uuid = request.args.get('album_uuid', None)
    album_data = None

    if album_uuid:
        conn = g.db
        album_data = await dbq.getAlbum(conn, album_uuid)
        if not album_data:
            return redirect(url_for('manage_library'))

    return render_template("manage_entries.html", album_data=album_data)


@app.route("/manage_other")
@login_required
def manage_other():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>Manage Other</p>"

def fetch_album_by_upc(upc):
    """
    Queries the Discogs API for album information based on the provided UPC.
    Returns a dictionary with album data or None if no results were found.
    """
    if not upc or not DISCOGS_API_KEY:
        return None

    api_url = f"https://api.discogs.com/database/search?upc={upc}&token={DISCOGS_API_KEY}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        if "results" in data and data["results"]:
            return data["results"][0]  # Return the first result
    return None

@app.route("/fetch_upc", methods=["POST"])
def fetch_upc():
    upc = request.form.get("upc")
    album_data = fetch_album_by_upc(upc)
    if album_data:
        # Process album_data as needed
        pass
    return redirect(url_for("home"))


### User Management

@app.route("/manage_users")
@login_required
async def manage_users():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    conn = g.db
    users = await dbq.getAllUsers(conn)
    return render_template("user_manager.html", users=users)

@app.route("/update_users", methods=['POST'])
@login_required
async def update_users():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    conn = g.db
    if request.form.get("invite_email"):
        email = request.form.get("invite_email")
        await dbq.inviteUser(conn,email)
    elif request.form.get("deactivate"):
        uid = request.form.get("deactivate")
        email = await dbq.getUserEmail(conn,uid)
        await dbq.removeInvite(conn,email)
    elif request.form.get("changed_roles"):
        changed_roles = request.form.get("changed_roles")
        changed_roles_dict = json.loads(changed_roles)
        for uid, new_role in changed_roles_dict.items():
            await dbq.setUserRole(conn, uid, new_role)
    return redirect(url_for("manage_users"))