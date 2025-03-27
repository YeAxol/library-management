import asyncio, psycopg
from library_manager.exceptions import *
from library_manager.classes import User

#################################################
#        Super Cool Search Functions            #
#################################################

async def searchLibrary(conn: psycopg.AsyncConnection, album: str, artist: str, genre: str, track: str, start: int = 0, limit: int = 50):
    async with conn.cursor() as cur:
        query = """
        SELECT DISTINCT album.albumID, album.albumName, album.genre, artist.artistName, track.trackName
        FROM album
        LEFT JOIN album_artist ON album.albumID = album_artist.albumID
        LEFT JOIN artist ON album_artist.artistID = artist.artistID
        LEFT JOIN album_track ON album.albumID = album_track.albumID
        LEFT JOIN track ON album_track.trackID = track.trackID
        WHERE 1=1
        """
        params = []
        if album:
            query += " AND album.albumName ILIKE %s"
            params.append(f"%{album}%")
        if artist:
            query += " AND artist.artistName ILIKE %s"
            params.append(f"%{artist}%")
        if genre:
            query += " AND album.genre ILIKE %s"
            params.append(f"%{genre}%")
        if track:
            query += " AND track.trackName ILIKE %s"
            params.append(f"%{track}%")
        
        query += " ORDER BY album.albumName ASC LIMIT %s OFFSET %s"
        params.extend([limit, start])
        
        await cur.execute(query, params)
        return await cur.fetchall()

async def getAlbum(conn: psycopg.AsyncConnection, album_id: str):
    async with conn.cursor() as cur:
        # Fetch album details
        await cur.execute("""
            SELECT album.albumID, album.albumName, album.albumShort, album.genre, album.picture, album.releaseDate, 
                   string_agg(DISTINCT artist.artistName, ', ') AS artist_names, 
                   string_agg(DISTINCT medium.mediumName, ', ') AS mediums
            FROM album
            LEFT JOIN album_artist ON album.albumID = album_artist.albumID
            LEFT JOIN artist ON album_artist.artistID = artist.artistID
            LEFT JOIN album_medium ON album.albumID = album_medium.albumID
            LEFT JOIN medium ON album_medium.mediumID = medium.mediumID
            WHERE album.albumID = %s
            GROUP BY album.albumID
        """, (album_id,))
        album_data = await cur.fetchone()

        # Fetch track details
        await cur.execute("""
            SELECT track.trackName, string_agg(DISTINCT artist.artistName, ', ') AS track_artists, track.fccClean, track.trackID
            FROM track
            LEFT JOIN album_track ON track.trackID = album_track.trackID
            LEFT JOIN artist_track ON track.trackID = artist_track.trackID
            LEFT JOIN artist ON artist_track.artistID = artist.artistID
            WHERE album_track.albumID = %s
            GROUP BY track.trackID
        """, (album_id,))
        tracks = await cur.fetchall()

        return {
            'album': album_data,
            'tracks': tracks
        }

#################################################
#                  Album Queries                #
#################################################

# async def addEntry(conn: psycopg.AsyncConnection, upc: str, albumname: str, artistname: str, genre: str, shortcode: str, releasedate: str, medium: str, image: str, tracks):
    
    
    
    
    
    
#     async with conn.cursor() as cur:

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
#           Invite Table Queries                #
#################################################

async def getUserInvite(conn:psycopg.AsyncConnection, email:str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM invitedusers WHERE email = %s", (email,))
        return await cur.fetchone() is not None

async def inviteUser(conn:psycopg.AsyncConnection, email:str):
    async with conn.cursor() as cur:
        if await getUserInvite(conn,email) is False:
            await cur.execute("INSERT INTO invitedusers (email) VALUES (%s)",(email,))
            await conn.commit()
            return await getUserInvite(conn,email)
        else:
            raise UserAlreadyInvited(email)

async def removeInvite(conn:psycopg.AsyncConnection, email:str):
    async with conn.cursor() as cur:
        await cur.execute("DELETE FROM invitedusers WHERE email = %s", (email,))
        await conn.commit()
        return await getUserInvite(conn, email)

#################################################
#             User Table Queries                #
#################################################

async def getAllUsers(conn:psycopg.AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute("""SELECT u.firstname, u.lastname, u.email, u.role, u.userid
    FROM users u
    INNER JOIN invitedusers i ON u.email = i.email
""")
        return await cur.fetchall()

#Remove if unused
async def getUser(conn: psycopg.AsyncConnection, user_id: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT userid, firstname, lastname, email, role FROM users WHERE userid = %s", (user_id,))
        user_data = await cur.fetchone()
        uid = user_data[0]
        if user_data:
            return User(str(uid), user_data[1], user_data[2], user_data[3], user_data[4])
        return None

async def getUserUUID(conn:psycopg.AsyncConnection, userEmail: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT userid FROM users WHERE email = %s", (userEmail,))
        UUID = await cur.fetchone()
        return str(UUID[0]) if UUID else None

async def verifyUserUUID(conn:psycopg.AsyncConnection, userID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT userid FROM users WHERE userid = %s", (userID,))
        return await cur.fetchone() # Will return None if no results

async def addUser(conn:psycopg.AsyncConnection, firstName: str, lastName: str, email: str):
    async with conn.cursor() as cur:
        if await getUserUUID(conn,email) is None:
            await cur.execute("INSERT INTO user (firstname, lastname, email) VALUES (%s,%s,%s)", (firstName,lastName,email,))
            await conn.commit()
            return await getUserUUID(conn,email)
        else:
            raise UserAlreadyExistsError(email)

async def deleteUser(conn:psycopg.AsyncConnection, userID: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM users WHERE userid = %s", (userID,))
            await conn.commit()
            return await verifyUserUUID(conn,userID)

#TODO: Might depricate bc of user class?
async def getUserRole(conn:psycopg.AsyncConnection, userID: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("SELECT role FROM users WHERE userid = %s", (userID,))
            role = await cur.fetchone()
            return str(role[0]) if role else None

async def getUserEmail(conn:psycopg.AsyncConnection, userID: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("SELECT email FROM users WHERE userid = %s", (userID,))
            email = await cur.fetchone()
            return str(email[0]) if email else None



async def setUserRole(conn:psycopg.AsyncConnection, userID: str, userRole: str):
    if userRole not in ["member", "staff", "eboard"]:
        raise RoleNotFound(userRole)
    elif await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET role = %s WHERE userID = %s", (userRole, userID))
            await conn.commit()
            return await getUserRole(conn,userID)

async def modifyEmail(conn:psycopg.AsyncConnection, userID: str, newEmail: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET email = %s WHERE userid = %s", (newEmail, userID))
            await conn.commit()
            return await verifyUserUUID(conn,userID) #TODO: return something useful if needed

async def modifyFirstName(conn:psycopg.AsyncConnection, userID: str, newName: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET firstname = %s WHERE userid = %s", (newName, userID))
            await conn.commit()
            return await verifyUserUUID(conn,userID) #TODO: return something useful if needed

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


