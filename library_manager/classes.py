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