from dotenv import load_dotenv
import os
import redis

load_dotenv()

class ApplicationConfig:
    SECRET_KEY = open("/run/secrets/SECRET_KEY").read().strip() if os.path.exists("/run/secrets/SECRET_KEY") else os.environ["SECRET_KEY"]
    
    # Database config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get("FLASK_ENV", "production") == "development"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    
    # Server side ession config
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USER_SIGNER = True
    SESSION_REDIS = redis.from_url("redis://redis:6379")
    