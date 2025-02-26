import asyncio, psycopg
from library_manager.exceptions import *

async def test_db(conn: psycopg.AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO artist (artistName) VALUES (%s)", ("Test",))
        
        await cur.execute("SELECT * FROM artist")
        print(await cur.fetchone())
        await conn.commit()

#################################################
#           Artist Table Queries                #
#################################################

async def getArtistUUID(conn: psycopg.AsyncConnection, artistName: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT artistid FROM artist WHERE artistname = %s", (artistName,))
        UUID = await cur.fetchone()
        return str(UUID[0]) if UUID else None

async def addArtist(conn:psycopg.AsyncConnection, artistName: str):
    async with conn.cursor() as cur:
        if await getArtistUUID(conn, artistName) is None:
            await cur.execute("INSERT INTO artist (artistName) VALUES (%s)", (artistName,))
            await conn.commit()
            return await getArtistUUID(conn, artistName)
        else:
            return await getArtistUUID(conn, artistName)

async def removeArtist(conn:psycopg.AsyncConnection, artistName: str):
    async with conn.cursor() as cur:
        UUID = await getArtistUUID(conn, artistName)
        if UUID is not None:
            await cur.execute("DELETE FROM artist WHERE artistid = %s", (str(UUID[0]),))
            await conn.commit()
            return await getArtistUUID(conn, artistName)
        else:
            return ArtistNotFoundError(artistName)
        
async def modifyArtist(conn:psycopg.AsyncConnection, artistID: str, newArtistName: str ):
    async with conn.cursor() as cur:
        oldname = await cur.execute("SELECT artistName FROM artist WHERE artistid = %s", (artistID,)) 
        if oldname is not None:
            await cur.execute("UPDATE artist SET artistname = %s WHERE artistid = %s", (newArtistName, artistID))
        else:
            raise ArtistNotFoundError(artistID)
        

#################################################
#            Track Table Queries                #
#################################################

#################################################
#           Medium Table Queries                #
#################################################

async def getMediumUUID(conn:psycopg.AsyncConnection, mediumName: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT mediumid FROM medium WHERE mediumname = %s", (mediumName,))
        UUID = await cur.fetchone()
        return str(UUID[0]) if UUID else None

async def addMedium(conn:psycopg.AsyncConnection, mediumName: str):
    async with conn.cursor() as cur:
        if await getMediumUUID(conn, mediumName) is None:
            await cur.execute("INSERT INTO medium (mediumName) VALUES (%s)", (mediumName,))
            await conn.commit()
            return await getMediumUUID(conn, mediumName)
        else:
            return await getMediumUUID(conn, mediumName)
        
async def removeMedium(conn:psycopg.AsyncConnection, mediumName: str):
    async with conn.cursor() as cur:
        UUID = await getMediumUUID(conn, mediumName)
        if UUID is not None:
            await cur.execute("DELETE FROM medium WHERE mediumid = %s", (str(UUID[0]),))
            await conn.commit()
            return await getMediumUUID(conn, mediumName)
        else:
            return MediumNotFoundError(mediumName)

async def modifyMedium(conn:psycopg.AsyncConnection, mediumID: str, newMediumName: str ):
    async with conn.cursor() as cur:
        oldname = await cur.execute("SELECT mediumName FROM medium WHERE mediumid = %s", (mediumID,)) 
        if oldname is not None:
            await cur.execute("UPDATE medium SET mediumname = %s WHERE mediumid = %s", (newMediumName, mediumID))
        else:
            raise MediumNotFoundError(mediumID)
        

#################################################
#           Album Table Queries                #
#################################################

#################################################
#           Review Table Queries                #
#################################################

#################################################
#             User Table Queries                #
#################################################

#################################################
#          Review_Album Table Queries           #
#################################################

#################################################
#          Album_Medium Table Queries           #
#################################################

#################################################
#          Album_Artist Table Queries           #
#################################################

#################################################
#          Album_Track Table Queries           #
#################################################

#################################################
#          Artist_Track Table Queries           #
#################################################


