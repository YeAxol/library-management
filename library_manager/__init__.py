import psycopg, asyncio, os
from dotenv import load_dotenv
from flask import Flask, g 
from library_manager import dbq

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)

async def init_db():
    print("initdb")
    return await psycopg.AsyncConnection.connect(DATABASE_URL)

async def close_db(conn):
    print("closedb")
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

@app.route("/testdb")
async def testdb():
    await dbq.test_db(g.db)
    return "test"

@app.route("/testselect")
async def testselect():
    print(type(g.db))
    print(await dbq.getArtistUUID(g.db,"Test"))
    print(await dbq.getArtistUUID(g.db,"test"))
    print(await dbq.getArtistUUID(g.db,"null"))
    return "lol"
    

@app.route("/")
def home():
    print("load")
    return "<p>home</p>"

