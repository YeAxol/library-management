from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, first_name, last_name, email, role):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    
class AlbumEntry():
    def __init__(self, upc, album_name, artists_name, genre, shortcode, release_date, mediums, image, tracks, album_id=None):
        self.upc = upc
        self.album_name = album_name
        self.artist_name = artists_name
        self.genre = genre
        self.shortcode = shortcode
        self.release_date = release_date
        self.mediums = mediums
        self.image = image
        self.tracks = tracks
        self.album_id = album_id
    
    def get_upc(self):
        return self.upc

    def get_album_name(self):
        return self.album_name

    def get_artist_name(self):
        return self.artist_name

    def get_genre(self):
        return self.genre

    def get_shortcode(self):
        return self.shortcode

    def get_release_date(self):
        return self.release_date

    def get_mediums(self):
        return self.mediums

    def get_image(self):
        return self.image

    def get_tracks(self):
        return self.tracks

    def get_album_id(self):
        return self.album_id