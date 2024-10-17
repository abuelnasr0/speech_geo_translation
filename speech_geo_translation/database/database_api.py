from sqlalchemy import create_engine, insert
from sqlalchemy import text
import datetime

import os
from dotenv import load_dotenv
from .models import (
    Customer,
    Governorate,
    Qism,
    ServiceArea,
    Complaint,
    GovsQhrCounts,
    QismsQhrCounts,
    AreasQhrCounts,
)
from .models import (
    EVENT_STRING,
    COUNTING_GOVS_FUN_STRING,
    COUNTING_QISMS_FUN_STRING,
    COUNTING_AREAS_FUN_STRING,
)
from .models import STRINGS_LINGTH

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
        self.initialized = False

    def create_tables(self):
        Customer.metadata.create_all(bind=self.engine)
        Governorate.metadata.create_all(bind=self.engine)
        Qism.metadata.create_all(bind=self.engine)
        ServiceArea.metadata.create_all(bind=self.engine)
        Complaint.metadata.create_all(bind=self.engine)
        GovsQhrCounts.metadata.create_all(bind=self.engine)
        QismsQhrCounts.metadata.create_all(bind=self.engine)
        AreasQhrCounts.metadata.create_all(bind=self.engine)

    def set_counting_event(self):
        with self.engine.connect() as connection:
            connection.execute(text(COUNTING_GOVS_FUN_STRING))
            connection.execute(text(COUNTING_QISMS_FUN_STRING))
            connection.execute(text(COUNTING_AREAS_FUN_STRING))

            connection.execute(text(EVENT_STRING))

    def db_startup(self):
        self.create_tables()
        self.set_counting_event()

    def initialize_tables(self, govs=None, qisms=None, service_areas=None):
        # Add Govs, Qisms, ServiceAreas
        if govs == None:
            self.initialized = False
            return

        with self.engine.connect() as connection:
            # Inserting govs
            connection.execute(Governorate.__table__.insert(), govs)
            connection.commit()

            # Inserting qisms, markaz
            connection.execute(Qism.__table__.insert(), qisms)
            connection.commit()

            # Inserting qisms, markaz
            connection.execute(ServiceArea.__table__.insert(), service_areas)
            connection.commit()

        self.initialized = True

    def drop_tables(self):
        Customer.metadata.drop_all(bind=self.engine)
        Governorate.metadata.drop_all(bind=self.engine)
        Qism.metadata.drop_all(bind=self.engine)
        ServiceArea.metadata.drop_all(bind=self.engine)
        Complaint.metadata.drop_all(bind=self.engine)

    def add_complaint(self, longitude, latitude, service_area_id):
        curr_complaint = [
            {
                "longitude": longitude,
                "latitude": latitude,
                "service_area_id": service_area_id,
                "time": datetime.datetime.now(),
            }
        ]
        # Add complaint to the database
        with self.engine.connect() as connection:
            # Inserting govs
            connection.execute(Complaint.__table__.insert(), curr_complaint)
            connection.commit()
