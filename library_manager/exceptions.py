
class ArtistNotFoundError(Exception):
    """Raised when an artist is not found in the database."""
    def __init__(self, artistName: str):
        self.artistName = artistName
        super().__init__(f"Artist '{artistName}' not found.")


class TrackNotFoundError(Exception):
    """Raised when an track is not found in the database."""
    def __init__(self, trackName: str):
        self.trackName = trackName
        super().__init__(f"Track '{trackName}' not found.")

class MediumNotFoundError(Exception):
    """Raised when an medium is not found in the database."""
    def __init__(self, mediumName: str):
        self.mediumName = mediumName
        super().__init__(f"Medium '{mediumName}' not found.")