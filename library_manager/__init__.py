from urllib.parse import urlparse
import psycopg, os, json
from dotenv import load_dotenv
from flask import Flask, g, redirect, url_for, render_template, request
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from library_manager import discogs
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from library_manager.classes import User, AlbumEntry
import dbq

#TODO: Handle actual error handling and logging...
#TODO: Implement user error responses
#TODO: Automated database backups


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#########
### TEMP REMOVE BEFORE DEPLOY
#########

#TODO: remove this before deploying
#there absolutely is a cleaner way to do this, flask-login doesn't like async 
@app.route("/test_login_member")
async def test_login_member():
    conn = g.get('db', None)
    user = await dbq.getUser(conn, "d7f427b3-119c-463d-8db9-a9ddbaadfa97 ")
    if user:
        login_user(user)
    return redirect(url_for('home'))

@app.route("/test_login_eboard")
async def test_login_eboard():
    conn = g.get('db', None)
    user = await dbq.getUser(conn, "ecc8a057-a74e-47a4-a99a-06971f2d8407")
    if user:
        login_user(user)
    return redirect(url_for('home'))

@app.route("/test_login_staff")
async def test_login_staff():
    conn = g.get('db', None)
    user = await dbq.getUser(conn, "d1f3e489-c967-4ee0-94ad-8aa090a7a252")
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
    g.db = await init_db()

@app.teardown_request
async def teardown(exception):
    db = g.get('db', None)
    if db is not None:
        await close_db(db)

### Login Logic
## This hasn't been tested yet
def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=os.path.join(os.path.dirname(__file__), 'saml'))
    return auth

def prepare_flask_request(request_details):
    url_data = urlparse(request_details.url)
    return {
        'https': 'on' if request_details.scheme == 'https' else 'off',
        'http_host': request_details.host,
        'server_port': url_data.port,
        'script_name': request_details.path,
        'get_data': request_details.args.copy(),
        'post_data': request_details.form.copy()
    }

@login_manager.user_loader
def load_user(user_id):
#login manager doesn't like async so we have to do this this way
#This works in the context of testing, however it might not work with SAML
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

            if user_data:
                uid = user_data[0]
                # print(uid)
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
## Made these the same because it makes sense to have the search on the home page
@app.route("/")
@app.route("/search")
async def home():
    # Pagination: what order of entries to show, defaults to 0 shows first 50 entries
    # Default could be changed in searchlibrary function
    pagination = int(request.args.get('pagination', 0))
    #Album search parameter, defaults to empty string
    album_search = request.args.get('album', '')
    #Artist search parameter, defaults to empty string
    artist_search = request.args.get('artist', '')
    #Genre search parameter, defaults to empty string
    genre_search = request.args.get('genre', '')
    #Track search parameter, defaults to empty string
    track_search = request.args.get('track', '')

    conn = g.db
    albums = await dbq.searchlibrary(conn, album_search, artist_search, genre_search, track_search, pagination)
    #album returns as a tuple so to decode the image bytes we need to convert it to a list
    albums = list(albums)
    # Decode image bytes to str if they exist
    # albums1 is named albums1 because albums is the name of the album detail route
    for i, album1 in enumerate(albums):
        album1 = list(album1)
        if album1[4] is not None and isinstance(album1[4], bytes):
            album1[4] = album1[4].decode('utf-8')
        albums[i] = album1
    return render_template("home.html", albums=albums, pagination=pagination)

@app.route("/album/<album_uuid>")
#Album details queried by UUID
async def album(album_uuid):
    conn = g.db
    album_entry = await dbq.getAlbum(conn, album_uuid)
    if not album_entry:
        return redirect(url_for('home'))

    # Fetch reviews for the album
    reviews = await dbq.getReviewsForAlbum(conn, album_uuid)

    return render_template("album_detail.html", album=album_entry, reviews=reviews)

### Review Management

#Review Form
@app.route("/review_form/<album_uuid>", methods=['GET', 'POST'])
@login_required
async def review_form(album_uuid, edit=False):
    conn = g.db
    if request.method == 'POST':
        review_text = request.form.get('review_text', '')
        if review_text:
            await dbq.addReview(conn, review_text, current_user.id, album_uuid, )
            return redirect(url_for('album_detail', album_uuid=album_uuid))

    album_entry = await dbq.getAlbum(conn, album_uuid)
    if not album_entry:
        return redirect(url_for('home'))

    edit = request.args.get('edit', 'False') == 'True'
    review_guidelines = await dbq.getReviewGuidelines(conn)

    return render_template("review_form.html", album=album_entry, review_guidelines=review_guidelines, edit=edit)

#Albums members reviewed
@app.route("/my_reviews")
@login_required
def my_reviews():
    return "<p>my_reviews</p>"

#Staff and Eboard Reviews
@app.route("/reviews_admin")
@login_required
def reviews_admin():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    return "<p>reviews_admin</p>"

#Eboard Review Statistics
@app.route("/review_statistics")
@login_required
def review_statistics():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    return "<p>Review Statistics</p>"

### Library Management

@app.route("/delete_entry/<album_uuid>", methods=['GET'])
@login_required
#"cdnerd" role cannot delete entries, only staff and eboard can
async def delete_entry(album_uuid):
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    ref = request.referrer or ''
    print("Deleting album with UUID:", album_uuid)
    conn = g.db
    if album_uuid:
        # Delete the album entry from the database
        await dbq.removeAlbum(conn, album_uuid)
        if ref.endswith('/') or ref.endswith('/search'):
            return redirect(url_for('home'))
        return redirect(url_for('manage_library'))

    return {"error": "Invalid album UUID"}, 400

@app.route("/manage_library", methods=['GET', 'POST'])
@login_required
#TODO: review this function, potential bug with uuid collision
#Handled with edit_uuid instead of variable being called album_uuid
#Also with serparate POST and GET requests
async def manage_library():
    if current_user.role not in ['staff', 'eboard', 'cdnerd']:
        return redirect(url_for('home'))

    if request.method == 'GET':
    #GET request with album_uuid to edit an existing album
        edit_uuid = request.args.get('album_uuid', None)
        #initialize album_entry to None and edit to False
        album_entry = None
        edit = False
        # If album_uuid is provided, fetch the album entry for editing
        if edit_uuid:
            edit = True
            conn = g.db
            album_entry = await dbq.getAlbum(conn, edit_uuid)
            # If the album entry is not found, redirect to manage_library
            if not album_entry:
                return redirect(url_for('manage_library'))
        return render_template("manage_library.html", album_entry=album_entry, is_edit=edit)

    # Handle POST request with AlbumEntry data (AJAX JSON)
    if request.method == 'POST':
        album_data = request.get_json()  # Parse JSON data from the request
        if album_data:
            # Dealing with parsing here bc I don't feel like doing this in the already long dbq file
            UPC = album_data.get('upc', None)
            album_uuid = album_data.get('album_uuid', None)
            albumname = album_data.get('album_name', None)
            artists = album_data.get('artist_names', [])
            genre = album_data.get('genre', None)
            shortcode = album_data.get('shortcode', None)
            release_date = album_data.get('release_date', None)
            mediums = album_data.get('mediums', [])
            #Images are stored as base64 encoded strings in the JSON, this makes it easier to store in a database
            #This could easily be changed to store the image as a file instead if there are performance issues
            image = album_data.get('image', None)
            tracks = []
            track_names = album_data.get('track_name', [])
            track_artists = album_data.get('track_artists', [])
            track_durations = album_data.get('track_duration', [])
            track_fcc_clean = album_data.get('track_fcc_clean', [])
            #Edit flag to determine if this is an edit operation or a new album addition
            edit = album_data.get('edit', False)
            for x in range(len(track_names)):
                # Parse artists for this track as a list
                artists_raw = track_artists[x] if x < len(track_artists) else ""
                parsed_artists = [a.strip() for a in artists_raw.split(',') if a.strip()]

                tracks.append([
                    track_names[x] if x < len(track_names) else "",
                    parsed_artists,
                    track_durations[x] if x < len(track_durations) else "",
                    track_fcc_clean[x] if x < len(track_fcc_clean) else False
                ])
            if not edit:
                await dbq.addAlbum(g.db, albumname, shortcode, UPC, genre, release_date, artists, mediums, image, tracks)
            if edit:
                #TODO: handle UPCs better, currently each album can only have one UPC attached to its primary medium
                await dbq.updateAlbum(g.db, album_uuid, albumname, shortcode, genre, release_date, image, tracks, artists, mediums)

            return {"success": True}
        return {"error": "No album data received"}, 400
    return {"error": "Invalid request method"}, 405


@app.route("/library_parameters", methods=['GET', 'POST'])
@login_required
#TODO: Implement this function to manage library parameters like valid genres and mediums
#TODO: Implement genre verification
def library_parameters():
    if current_user.role not in ['staff', 'eboard']:
        return redirect(url_for('home'))
    conn = g.db

    if request.method == 'GET':
        mediums = dbq.getAllMediums(conn)
        genres = dbq.getAllGenres(conn)
        review_guidelines = dbq.getReviewGuidelines(conn)
        return render_template("library_parameters.html")

    # TODO: Finish implementing this function to handle POST requests    # elif request.method == 'POST':
    #     # Handle POST request to update library parameters
    #     action = request.form.get('action', None)
    #     if action == 'add_medium':
    #         medium_name = request.form.get('medium_name', None)
    #         if medium_name:
    #             await dbq.addMedium(conn, medium_name)
    #             return {"success": True}
    #     elif action == 'add_genre':
    #         genre_name = request.form.get('genre_name', None)
    #         if genre_name:
    #             await dbq.addGenre(conn, genre_name)
    #             return {"success": True}
    #     elif action == 'update_review_guidelines':
    #         guidelines = request.form.get('review_guidelines', None)
    #         if guidelines:
    #             await dbq.updateReviewGuidelines(conn, guidelines)
    #             return {"success": True}
    #     return {"error": "Invalid action"}, 400

    return {"error": "Invalid request method"}, 405

@app.route("/fetch_upc", methods=["POST"])
@login_required
# Fetch album details from Discogs using UPC
def fetch_upc():
    if current_user.role not in ['staff', 'eboard', 'cdnerd']:
        return redirect(url_for('home'))
    upc = request.form.get('upc', None)
    if upc:
        album_entry = discogs.search_upc(upc)
        if album_entry:
            return render_template("partials/album_form.html", album_entry=album_entry)
    return {"error": "Invalid UPC"}, 400

@app.route("/fetch_discogs", methods=["POST"])
@login_required
# Fetch album details from Discogs using Discogs ID
def fetch_discogs():
    if current_user.role not in ['staff', 'eboard', 'cdnerd']:
        return redirect(url_for('home'))
    discogs_id = request.form.get('discogs_id', None)
    if discogs_id:
        album_entry = discogs.search_by_id(discogs_id)
        if album_entry:
            return render_template("partials/album_form.html", album_entry=album_entry)
    return {"error": "Invalid Discogs ID"}, 400


### User Management
@app.route("/manage_users")
@login_required
# Endpoint to manage active users, only accessible by eboard members
# Users who are deactivated will not appear on this list
async def manage_users():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    conn = g.db
    users = await dbq.getAllUsers(conn)
    return render_template("user_manager.html", users=users)

@app.route("/update_users", methods=['POST'])
@login_required
# Endpoint to handle user updates, invites, and role changes
# WARNING: Users cannot be deleted to retain review history
async def update_users():
    if current_user.role != 'eboard':
        return redirect(url_for('home'))
    conn = g.db
    # Check if the request contains an invite email
    if request.form.get("invite_email"):
        email = request.form.get("invite_email")
        await dbq.inviteUser(conn, email)
    # Check if the request contains a user id to deactivate
    elif request.form.get("deactivate"):
        uid = request.form.get("deactivate")
        email = await dbq.getUserEmail(conn, uid)
        await dbq.removeInvite(conn, email)
    # Check if the request contains a user to change roles
    elif request.form.get("changed_roles"):
        changed_roles = request.form.get("changed_roles")
        changed_roles_dict = json.loads(changed_roles)
        for uid, new_role in changed_roles_dict.items():
            await dbq.setUserRole(conn, uid, new_role)
    return redirect(url_for("manage_users"))