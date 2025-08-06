import os, base64, requests
from dotenv import load_dotenv
import discogs_client
from library_manager.classes import AlbumEntry

load_dotenv()
DISCOGS_KEY = os.getenv("DISCOGS_TOKEN")
DISCOGS_SECRET = os.getenv("DISCOGS_SECRET")
HEADERS = {'user-agent': 'WITR-LibraryManager/0.0.1', "Authorization": f"Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}"}
RATELIMIT = 30

d = discogs_client.Client('WITR-LibraryManager/0.0.1',user_token=DISCOGS_KEY)

def search_by_id(release_id: str):
    #This function searches for a release by its ID and returns an AlbumEntry object
    if release_id.startswith("[r"):
        release_id = release_id[2:-1]
    results = d.release(release_id)
    return results_parsed(results)

def search_upc(upc: str):
    #This ugly function goes from the center out first searching the first entry using the UPC before pulling its master release id, then it uses that master release id to pull the master's main_relase id which is used to gain the release that is most likely to have accurate info
    results = d.release((d.master(d.search(barcode = upc).page(1)[0].master.id)).main_release.id)
    return results_parsed(results, upc)


def results_parsed(results, upc = None):
    parsedart = []
    for artist in results.artists:
        parsedart += [artist.name]
    parsedtrack = []
    for track in results.tracklist:
        credit = []
        for artist in parsedart:
            credit += [artist]
        for artist in track.credits:
            credit += [artist.name]
        parsedtrack += [[track.title, credit, track.duration]]
    parseformat = []
    for mformat in results.formats:
        parseformat += [mformat["name"]]
    image = image_url_to_base64(results.images[0]["uri"]) if results.images else None

    if upc:
        barcode = upc
    else:
        barcode_value = getattr(results, "barcode", None)
        barcode = barcode_value[0] if barcode_value and len(barcode_value) > 0 else None

    return AlbumEntry(barcode, results.title, parsedart, results.genres[0], None, results.year, parseformat, image, parsedtrack)


def image_url_to_base64(image_url):
    try:
        response = requests.get(image_url, headers=HEADERS)
        response.raise_for_status()
        image_bytes = response.content
        encoded_string = base64.b64encode(image_bytes).decode('utf-8')
        return encoded_string
    except Exception as e:
        print(f"Error downloading or encoding image: {e}")
        return None