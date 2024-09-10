from sqlalchemy import create_engine, insert

import os
from dotenv import load_dotenv
from speech_geo_translation.database.models import Complaint, ComplaintType

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWD = os.getenv("DB_PASSWD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DB_URI = "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    DB_USER, DB_PASSWD, DB_HOST, DB_PORT, DB_NAME
)


class DatabaseAPI(object):
    def __new__(cls):
        # Singlton. only one instance will be created.
        if not hasattr(cls, "instance"):
            cls.instance = super(DatabaseAPI, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.engine = create_engine(DB_URI, echo=True)

    def creat_tables(self):
        ComplaintType.metadata.create_all(bind=self.engine)
        Complaint.metadata.create_all(bind=self.engine)

        # Here add any complaint type

    def drop_tables(self):
        Complaint.metadata.drop_all(bind=self.engine)
        ComplaintType.metadata.drop_all(bind=self.engine)

    def add_complaint(self, location):
        # Add complaint to the database
        print(location)
        print("should be added")
        pass
