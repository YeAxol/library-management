import psycopg
from library_manager.exceptions import *


#################################################
#        Super Cool Search Functions            #
#################################################

async def searchlibrary(conn: psycopg.AsyncConnection, album: str, artist: str, genre: str, track: str, start: int = 0, limit: int = 50):
    async with conn.cursor() as cur:
        query = """
        SELECT DISTINCT album.albumID, album.albumName, album.genre, artist.artistName, album.picture
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



#################################################
#          Album_Artist Table Queries           #
#################################################

async def getAlbumArtists(conn: psycopg.AsyncConnection, albumID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT artist.artistName
            FROM album_artist
            JOIN artist ON album_artist.artistID = artist.artistID
            WHERE album_artist.albumID = %s
        """, (albumID,))
        return await cur.fetchall()

async def addAlbumArtist(conn: psycopg.AsyncConnection, albumID: str, artistID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.artist import verifyArtistUUID
    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyArtistUUID(conn, artistID):
        raise ArtistNotFoundError(artistID)
    async with conn.cursor() as cur:
        await cur.execute("""
            INSERT INTO album_artist (albumID, artistID)
            VALUES (%s, %s)
        """, (albumID, artistID))
        await conn.commit()
        return await getAlbumArtists(conn, albumID)

async def removeAlbumArtist(conn: psycopg.AsyncConnection, albumID: str, artistID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.artist import verifyArtistUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyArtistUUID(conn, artistID):
        raise ArtistNotFoundError(artistID)
    async with conn.cursor() as cur:
        await cur.execute("""
            DELETE FROM album_artist
            WHERE albumID = %s AND artistID = %s
        """, (albumID, artistID))
        await conn.commit()
        return await getAlbumArtists(conn, albumID)

async def modifyAlbumArtist(conn: psycopg.AsyncConnection, albumID: str, oldArtistID: str, newArtistID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.artist import verifyArtistUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyArtistUUID(conn, oldArtistID):
        raise ArtistNotFoundError(oldArtistID)
    if not await verifyArtistUUID(conn, newArtistID):
        raise ArtistNotFoundError(newArtistID)
    async with conn.cursor() as cur:
        await cur.execute("""
            UPDATE album_artist
            SET artistID = %s
            WHERE albumID = %s AND artistID = %s
        """, (newArtistID, albumID, oldArtistID))
        await conn.commit()
        return await getAlbumArtists(conn, albumID)

async def verifyAlbumArtist(conn: psycopg.AsyncConnection, albumID: str, artistID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.artist import verifyArtistUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyArtistUUID(conn, artistID):
        raise ArtistNotFoundError(artistID)
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT 1
            FROM album_artist
            WHERE albumID = %s AND artistID = %s
        """, (albumID, artistID))
        return await cur.fetchone() is not None


#################################################
#          Album_Medium Table Queries           #
#################################################

async def getAlbumMediums(conn: psycopg.AsyncConnection, albumID: str):
    from dbq.album import verifyAlbumUUID
    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT medium.mediumName
            FROM album_medium
            JOIN medium ON album_medium.mediumID = medium.mediumID
            WHERE album_medium.albumID = %s
        """, (albumID,))
        return await cur.fetchall()

async def addAlbumMedium(conn: psycopg.AsyncConnection, albumID: str, mediumID: str, albumUPC: str):
    from dbq.album import verifyAlbumUUID
    from dbq.medium import verifyMediumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyMediumUUID(conn, mediumID):
        raise MediumNotFoundError(mediumID)
    async with conn.cursor() as cur:
        if albumUPC is None:
            await cur.execute("""
                INSERT INTO album_medium (albumID, mediumID)
                VALUES (%s, %s)
            """, (albumID, mediumID))
        else:
            await cur.execute("""
                INSERT INTO album_medium (albumID, mediumID, albumupc)
                VALUES (%s, %s, %s)
            """, (albumID, mediumID, albumUPC))
            await conn.commit()
        return await getAlbumMediums(conn, albumID)

async def removeAlbumMedium(conn: psycopg.AsyncConnection, albumID: str, mediumID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.medium import verifyMediumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyMediumUUID(conn, mediumID):
        raise MediumNotFoundError(mediumID)
    async with conn.cursor() as cur:
        await cur.execute("""
            DELETE FROM album_medium
            WHERE albumID = %s AND mediumID = %s
        """, (albumID, mediumID))
        await conn.commit()
        return await getAlbumMediums(conn, albumID)

async def modifyAlbumMediumUPC(conn: psycopg.AsyncConnection, albumID: str, mediumID: str, newUPC: str):
    from dbq.album import verifyAlbumUUID
    from dbq.medium import verifyMediumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyMediumUUID(conn, mediumID):
        raise MediumNotFoundError(mediumID)
    async with conn.cursor() as cur:
        await cur.execute("""
            UPDATE album_medium
            SET albumupc = %s
            WHERE albumID = %s AND mediumID = %s
        """, (newUPC, albumID, mediumID))
        await conn.commit()
        return await getAlbumMediums(conn, albumID)

async def getAlbumMediumUPC(conn: psycopg.AsyncConnection, albumID: str, mediumID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.medium import verifyMediumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyMediumUUID(conn, mediumID):
        raise MediumNotFoundError(mediumID)
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT albumupc
            FROM album_medium
            WHERE albumID = %s AND mediumID = %s
        """, (albumID, mediumID))
        upc = await cur.fetchone()
        return str(upc[0]) if upc else None

async def verifyAlbumMedium(conn: psycopg.AsyncConnection, albumID: str, mediumID: str):
    from dbq.album import verifyAlbumUUID
    from dbq.medium import verifyMediumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyMediumUUID(conn, mediumID):
        raise MediumNotFoundError(mediumID)
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT 1
            FROM album_medium
            WHERE albumID = %s AND mediumID = %s
        """, (albumID, mediumID))
        return await cur.fetchone() is not None

async def getAlbumNameByUPC(conn: psycopg.AsyncConnection, upc: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT album.albumName
            FROM album
            JOIN album_medium ON album.albumID = album_medium.albumID
            WHERE album_medium.albumupc = %s
        """, (upc,))
        album_name = await cur.fetchone()
        return str(album_name[0]) if album_name else None


#################################################
#          Album_Track Table Queries           #
#################################################

async def getAlbumTracks(conn: psycopg.AsyncConnection, albumID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT track.trackName
            FROM album_track
            JOIN track ON album_track.trackID = track.trackID
            WHERE album_track.albumID = %s
        """, (albumID,))
        return await cur.fetchall()

async def addAlbumTrack(conn: psycopg.AsyncConnection, albumID: str, trackID: str):
    from dbq.track import verifyTrackUUID
    from dbq.album import verifyAlbumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyTrackUUID(conn, trackID):
        raise TrackNotFoundError(trackID)
    async with conn.cursor() as cur:
        await cur.execute("""
            INSERT INTO album_track (albumID, trackID)
            VALUES (%s, %s)
        """, (albumID, trackID))
        await conn.commit()
        return await getAlbumTracks(conn, albumID)

async def removeAlbumTrack(conn: psycopg.AsyncConnection, albumID: str, trackID: str):
    from dbq.track import verifyTrackUUID
    from dbq.album import verifyAlbumUUID

    if not await verifyAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyTrackUUID(conn, trackID):
        raise TrackNotFoundError(trackID)
    async with conn.cursor() as cur:
        await cur.execute("""
            DELETE FROM album_track
            WHERE albumID = %s AND trackID = %s
        """, (albumID, trackID))
        await conn.commit()
        return await getAlbumTracks(conn, albumID)



#################################################
#           Artist Table Queries                #
#################################################

async def getArtistUUID(conn:psycopg.AsyncConnection, artistName: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT artistid FROM artist WHERE artistname = %s", (artistName,))
        UUID = await cur.fetchone()
        return str(UUID[0]) if UUID else None

async def verifyArtistUUID(conn:psycopg.AsyncConnection, artistID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT artistid FROM artist WHERE artistid = %s", (artistID,))
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

async def modifyArtist(conn:psycopg.AsyncConnection, artistID: str, newArtistName: str):
    async with conn.cursor() as cur:
        oldname = await cur.execute("SELECT artistName FROM artist WHERE artistid = %s", (artistID,))
        if oldname is not None:
            await cur.execute("UPDATE artist SET artistname = %s WHERE artistid = %s", (newArtistName, artistID))
        else:
            raise ArtistNotFoundError(artistID)
        await conn.commit()
        return await getArtistUUID(conn, newArtistName)

async def getArtistName(conn:psycopg.AsyncConnection, artistID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT artistName FROM artist WHERE artistid = %s", (artistID,))
        name = await cur.fetchone()
        return str(name[0]) if name else None


#################################################
#          Artist_Track Table Queries           #
#################################################

async def getArtistTracks(conn: psycopg.AsyncConnection, artistID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT track.trackName
            FROM artist_track
            JOIN track ON artist_track.trackID = track.trackID
            WHERE artist_track.artistID = %s
        """, (artistID,))
        return await cur.fetchall()

async def addArtistTrack(conn: psycopg.AsyncConnection, artistID: str, trackID: str):
    from dbq.track import verifyTrackUUID
    from dbq.artist import verifyArtistUUID

    if not await verifyArtistUUID(conn, artistID):
        raise ArtistNotFoundError(artistID)
    if not await verifyTrackUUID(conn, trackID):
        raise TrackNotFoundError(trackID)
    async with conn.cursor() as cur:
        await cur.execute("""
            INSERT INTO artist_track (artistID, trackID)
            VALUES (%s, %s)
        """, (artistID, trackID))
        await conn.commit()
        return await getArtistTracks(conn, artistID)

async def removeArtistTrack(conn: psycopg.AsyncConnection, artistID: str, trackID: str):
    from dbq.track import verifyTrackUUID
    from dbq.artist import verifyArtistUUID

    if not await verifyTrackUUID(conn, artistID):
        raise ArtistNotFoundError(artistID)
    if not await verifyArtistUUID(conn, trackID):
        raise TrackNotFoundError(trackID)
    async with conn.cursor() as cur:
        await cur.execute("""
            DELETE FROM artist_track
            WHERE artistID = %s AND trackID = %s
        """, (artistID, trackID))
        await conn.commit()
        return await getArtistTracks(conn, artistID)

async def getTrackArtists(conn: psycopg.AsyncConnection, trackID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT artist.artistName
            FROM artist_track
            JOIN artist ON artist_track.artistID = artist.artistID
            WHERE artist_track.trackID = %s
        """, (trackID,))
        return await cur.fetchall()


#################################################
#           Medium Table Queries                #
#################################################

async def getAllMediums(conn:psycopg.AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute("SELECT mediumid, mediumname FROM medium")
        mediums = await cur.fetchall()
        mediumslist = []
        for medium in mediums:
            mediumslist += (medium[0]), str(medium[1])
        return mediumslist

async def verifyMediumUUID(conn:psycopg.AsyncConnection, mediumID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT mediumid FROM medium WHERE mediumid = %s", (mediumID,))
        UUID = await cur.fetchone()
        return UUID is not None

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

async def removeMedium(conn:psycopg.AsyncConnection, mediumID: str, mediumModName: str):
    if mediumID is not None:
        if not await getMediumUUID(conn, mediumModName):
            newMedUUID = await addMedium(conn, mediumModName)
        else:
            newMedUUID = await getMediumUUID(conn, mediumModName)
        async with conn.cursor() as cur:
            await cur.execute("UPDATE album_medium SET mediumid = %s WHERE mediumid = %s", (newMedUUID, (str(mediumID[0]))))
            await cur.execute("DELETE FROM medium WHERE mediumid = %s", (str(mediumID[0]),))
            await conn.commit()
            return await verifyMediumUUID(conn, mediumID)
    else:
        return MediumNotFoundError(mediumID)

async def modifyMedium(conn:psycopg.AsyncConnection, mediumID: str, newMediumName: str ):
    async with conn.cursor() as cur:
        if await verifyMediumUUID(conn, mediumID) is not None:
            await cur.execute("UPDATE medium SET mediumname = %s WHERE mediumid = %s", (newMediumName, mediumID))
        else:
            raise MediumNotFoundError(mediumID)


#################################################
#           Review Table Queries                #
#################################################

async def getReviewUUID(conn:psycopg.AsyncConnection, reviewID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT reviewid FROM review WHERE reviewid = %s", (reviewID,))
        UUID = await cur.fetchone()
        return str(UUID[0]) if UUID else None

async def addReview(conn:psycopg.AsyncConnection, reviewText: str, userID: str, hidden: bool = True):
    from dbq.user import verifyUserUUID

    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    async with conn.cursor() as cur:
        if await getReviewUUID(conn, reviewText) is None:
            await cur.execute("INSERT INTO review (review, userID, hidden) VALUES (%s, %s, %s)", (reviewText, userID, hidden))
            await conn.commit()
            return await getReviewUUID(conn, reviewText)
        else:
            return await getReviewUUID(conn, reviewText)

async def removeReview(conn:psycopg.AsyncConnection, reviewID: str):
    async with conn.cursor() as cur:
        UUID = await getReviewUUID(conn, reviewID)
        if UUID is not None:
            await cur.execute("DELETE FROM review WHERE reviewid = %s", (str(UUID[0]),))
            await conn.commit()
            return await getReviewUUID(conn, reviewID)
        else:
            return ReviewNotFoundError(reviewID)

async def modifyReviewHidden(conn:psycopg.AsyncConnection, reviewID: str, hidden: bool):
    async with conn.cursor() as cur:
        UUID = await getReviewUUID(conn, reviewID)
        if UUID is not None:
            await cur.execute("UPDATE review SET hidden = %s WHERE reviewid = %s", (hidden, UUID))
            await conn.commit()
            return await getReviewUUID(conn, reviewID)
        else:
            raise ReviewNotFoundError(reviewID)

async def modifyReviewText(conn:psycopg.AsyncConnection, reviewID: str, newReviewText: str):
    async with conn.cursor() as cur:
        UUID = await getReviewUUID(conn, reviewID)
        if UUID is not None:
            await cur.execute("UPDATE review SET review = %s WHERE reviewid = %s", (newReviewText, UUID))
            await conn.commit()
            await updateReviewDate(conn, reviewID)  # Update the review date after modifying the text
            return await getReviewUUID(conn, newReviewText)
        else:
            raise ReviewNotFoundError(reviewID)

async def updateReviewDate(conn:psycopg.AsyncConnection, reviewID: str):
    async with conn.cursor() as cur:
        UUID = await getReviewUUID(conn, reviewID)
        if UUID is not None:
            await cur.execute("UPDATE review SET reviewDate = NOW() WHERE reviewid = %s", (UUID,))
            await conn.commit()
            return await getReviewUUID(conn, reviewID)
        else:
            raise ReviewNotFoundError(reviewID)

async def getReviewsForAlbum(conn:psycopg.AsyncConnection, albumID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT r.reviewid, r.review, r.hidden, r.reviewDate, u.firstname, u.lastname
            FROM review r
            JOIN users u ON r.userid = u.userid
            JOIN review_album ra ON r.reviewid = ra.reviewid
            WHERE ra.albumid = %s
        """, (albumID,))
        return await cur.fetchall()

async def getReviewGuidelines(conn:psycopg.AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute("SELECT value FROM parameters WHERE key = %s", ('review_guidelines',))
        row = await cur.fetchone()
        return row[0] if row else "No guidelines set."


#################################################
#          Review_Album Table Queries           #
#################################################

async def getAlbumReviews(conn: psycopg.AsyncConnection, albumID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT reviewID
            FROM review_album
            WHERE albumID = %s
        """, (albumID,))
        return await cur.fetchall()

async def verifyAlbumReview(conn: psycopg.AsyncConnection, albumID: str, reviewID: str):
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT 1
            FROM review_album
            WHERE albumID = %s AND reviewID = %s
        """, (albumID, reviewID))
        return await cur.fetchone() is not None

async def addAlbumReview(conn: psycopg.AsyncConnection, albumID: str, reviewID: str):
    from dbq.album import getAlbumUUID

    if not await getAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if verifyAlbumReview(conn, albumID, reviewID):
        raise ReviewAlreadyExistsError(reviewID)
    async with conn.cursor() as cur:
        await cur.execute("""
            INSERT INTO review_album (albumID, reviewID)
            VALUES (%s, %s)
        """, (albumID, reviewID))
        await conn.commit()
        return await getAlbumReviews(conn, albumID)

async def removeAlbumReview(conn: psycopg.AsyncConnection, albumID: str, reviewID: str):
    from dbq.album import getAlbumUUID

    if not await getAlbumUUID(conn, albumID):
        raise AlbumNotFoundError(albumID)
    if not await verifyAlbumReview(conn, albumID, reviewID):
        raise ReviewNotFoundError(reviewID)
    async with conn.cursor() as cur:
        await cur.execute("""
            DELETE FROM review_album
            WHERE albumID = %s AND reviewID = %s
        """, (albumID, reviewID))
        await conn.commit()
        return await getAlbumReviews(conn, albumID)


#################################################
#            Track Table Queries                #
#################################################

async def verifyTrackUUID(conn:psycopg.AsyncConnection, trackID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT trackid FROM track WHERE trackid = %s", (trackID,))
        return await cur.fetchone()  # Will return None if no results

async def getTrackUUID(conn:psycopg.AsyncConnection, trackName: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT trackid FROM track WHERE trackname = %s", (trackName,))
        uuid = await cur.fetchone()
        return str(uuid[0]) if uuid else None

async def addTrack(conn:psycopg.AsyncConnection, trackName: str, artistNames: list, trackDuration: str, fccClean: bool = False):
    from dbq.artist_track import addArtistTrack
    from dbq.artist import getArtistUUID, addArtist

    async with conn.cursor() as cur:
        for artist in artistNames:
            artistUUID = []
            if await getArtistUUID(conn, artist) is None:
                uuid = await addArtist(conn, artist)
            else:
                uuid = await getArtistUUID(conn, artist)
            artistUUID.append(uuid)
        await cur.execute("INSERT INTO track (trackName, fccClean, trackDuration) VALUES (%s, %s, %s) RETURNING trackid", (trackName, fccClean, trackDuration))
        await conn.commit()
        trackUUID = await cur.fetchone()
        for artist in artistUUID:
            await addArtistTrack(conn, artist, str(trackUUID[0]))
        return str(trackUUID[0])

async def removeTrack(conn:psycopg.AsyncConnection, trackUUID: str):
    async with conn.cursor() as cur:
        uuid = await verifyTrackUUID(conn, trackUUID)
        if uuid is not None:
            await cur.execute("DELETE FROM track WHERE trackid = %s", (str(uuid[0]),))
            await conn.commit()
            return await verifyTrackUUID(conn, trackUUID)
        else:
            return TrackNotFoundError(trackUUID)

async def modifyTrack(conn:psycopg.AsyncConnection, trackID: str, newTrackName: str, fccClean: bool = False, trackDuration: str = None):
    async with conn.cursor() as cur:
        oldtrackname = await verifyTrackUUID(conn, trackID)
        if oldtrackname is not None:
            if oldtrackname is None:
                 newTrackName = oldtrackname
            if trackDuration is None:
                await cur.execute("SELECT trackDuration FROM track WHERE trackid = %s", (trackID,))
                trackDuration = await cur.fetchone()
                if trackDuration:
                    trackDuration = trackDuration[0]
            await cur.execute("UPDATE track SET trackname = %s, fccClean = %s, trackDuration = %s WHERE trackid = %s", (newTrackName, fccClean, trackDuration, trackID))
            await conn.commit()
            return await getTrackUUID(conn, newTrackName)
        else:
            raise TrackNotFoundError(trackID)

async def getTrackName(conn:psycopg.AsyncConnection, trackID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT trackName FROM track WHERE trackid = %s", (trackID,))
        name = await cur.fetchone()
        return str(name[0]) if name else None

async def getTrackDuration(conn:psycopg.AsyncConnection, trackID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT trackDuration FROM track WHERE trackid = %s", (trackID,))
        duration = await cur.fetchone()
        return str(duration[0]) if duration else None

async def getTrackFCC(conn:psycopg.AsyncConnection, trackID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT fccClean FROM track WHERE trackid = %s", (trackID,))
        fcc = await cur.fetchone()
        return bool(fcc[0]) if fcc else None

async def verifyTrackName(conn:psycopg.AsyncConnection, trackName: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT trackid FROM track WHERE trackname = %s", (trackName,))
        return await cur.fetchone()  # Will return None if no results

async def getTrackInfo(conn:psycopg.AsyncConnection, trackID: str):
    from dbq.artist_track import getTrackArtists
    async with conn.cursor() as cur:
        await cur.execute("SELECT trackName, fccClean, trackDuration FROM track WHERE trackid = %s", (trackID,))
        track_info = await cur.fetchone()
        if track_info:
            return {
                'trackName': str(track_info[0]),
                'trackArtists': await getTrackArtists(conn, trackID),
                'fccClean': bool(track_info[1]),
                'trackDuration': str(track_info[2])
            }
        return None


#################################################
#               Genre Management                #
#################################################

async def getAllGenres(conn:psycopg.AsyncConnection):
    async with conn.cursor() as cur:
        await cur.execute("SELECT FROM parameter WHERE parametername = 'genre'")
        return await cur.fetchone()  # returns a list of genres

async def updateGenre(conn:psycopg.AsyncConnection, genreName: str):
    async with conn.cursor() as cur:
        await cur.execute("UPDATE parameter SET parametervalue = %s WHERE parametername = 'genre'", (genreName,))
        await conn.commit()
        return await getAllGenres(conn)


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
        uuid = await cur.fetchone()
        return str(uuid[0]) if uuid else None

async def verifyUserUUID(conn:psycopg.AsyncConnection, userID: str):
    async with conn.cursor() as cur:
        await cur.execute("SELECT userid FROM users WHERE userid = %s", (userID,))
        return await cur.fetchone() # Will return None if no results

async def addUser(conn:psycopg.AsyncConnection, firstName: str, lastName: str, email: str):
    async with conn.cursor() as cur:
        if await getUserUUID(conn,email) is None:
            await cur.execute("INSERT INTO users (firstname, lastname, email) VALUES (%s,%s,%s)", (firstName,lastName,email,))
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

#TODO: Might deprecate bc of user class?
async def getUserEmail(conn:psycopg.AsyncConnection, userID: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("SELECT email FROM users WHERE userid = %s", (userID,))
            email = await cur.fetchone()
            return str(email[0]) if email else None

async def getUserRole(conn:psycopg.AsyncConnection, userID: str):
    if await verifyUserUUID(conn, userID) is None:
        raise UserNotFoundError(userID)
    else:
        async with conn.cursor() as cur:
            await cur.execute("SELECT role FROM users WHERE userid = %s", (userID,))
            role = await cur.fetchone()
            return str(role[0]) if role else None

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


