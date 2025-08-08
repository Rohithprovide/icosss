from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # ensure password hash field has length of at least 256
    password_hash = db.Column(db.String(256))


class SearchQuery(db.Model):
    """Model to store search queries for analytics and history."""
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    
    def __repr__(self):
        return f'<SearchQuery {self.query}>'