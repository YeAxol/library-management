import psycopg, asyncio, os
from dotenv import load_dotenv
from flask import Flask, g 

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

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

@app.route("/")
def home():
    return "<p>home</p>"

