
class ArtistNotFoundError(Exception):
    """Raised when an artist is not found in the database."""
    def __init__(self, artistName: str):
        self.artistName = artistName
        super().__init__(f"Artist '{artistName}' not found.")

class AlbumNotFoundError(Exception):
    """Raised when an album is not found in the database."""
    def __init__(self, albumName: str):
        self.albumName = albumName
        super().__init__(f"Album '{albumName}' not found.")

class AlbumAlreadyExistsError(Exception):
    """Raised when an album already exists in the database."""
    def __init__(self, albumName: str):
        self.albumName = albumName
        super().__init__(f"Album '{albumName}' already exists in the database.")

class ReviewNotFoundError(Exception):
    """Raised when a review is not found in the database."""
    def __init__(self, reviewId: str):
        self.reviewId = reviewId
        super().__init__(f"Review with ID '{reviewId}' not found.")

class ReviewAlreadyExistsError(Exception):
    """Raised when a review already exists in the database."""
    def __init__(self, reviewId: str):
        self.reviewId = reviewId
        super().__init__(f"Review with ID '{reviewId}' already exists in the database.")

class TrackNotFoundError(Exception):
    """Raised when a track is not found in the database."""
    def __init__(self, trackName: str):
        self.trackName = trackName
        super().__init__(f"Track '{trackName}' not found.")

class MediumNotFoundError(Exception):
    """Raised when a medium is not found in the database."""
    def __init__(self, mediumName: str):
        self.mediumName = mediumName
        super().__init__(f"Medium '{mediumName}' not found.")

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database."""
    def __init__(self, userName: str):
        self.userName = userName
        super().__init__(f"User '{userName}' not found.")

class UserAlreadyExistsError(Exception):
    """Raised when a user already exists with the email in the database"""
    def __init__(self, userEmail: str):
        self.userEmail = userEmail
        super().__init__(f"User with the email '{userEmail}' is already registered.")

class UserAlreadyInvited(Exception):
    """Raised when a user already exists with the email in the database"""
    def __init__(self, userEmail: str):
        self.userEmail = userEmail
        super().__init__(f"User with the email '{userEmail}' is already invited.")

class RoleNotFound(Exception):
    """Raised when a user is assigned an invalid role"""
    def __init__(self, userRole: str):
        self.userRole = userRole
        super().__init__(f"Role '{userRole}' not found.")

