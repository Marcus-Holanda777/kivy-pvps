import pyrebase
from models.config import config

firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()
