from dotenv import load_dotenv
import os
import redis

load_dotenv()

class ApplicationConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    
    # Database config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    # Store the sqlite DB inside the project's instance folder so it's easy to manage
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pythonwebapp.db'
    
    # Server side ession config
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USER_SIGNER = True
    SESSION_REDIS = redis.from_url("redis://redis:6379")
    