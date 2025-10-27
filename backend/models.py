from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from uuid import uuid4

db = SQLAlchemy()
ma = Marshmallow()

def get_uuid():
    return uuid4().hex

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Utilisateur")

# Marshmallow Schema to strucuture the JSON response
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User