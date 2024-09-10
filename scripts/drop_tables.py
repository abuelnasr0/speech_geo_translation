import sys
sys.path.insert(0,"/home/mohamed/Mohamed/Vodafone project/projects/app")

from speech_geo_translation.database.database_api import DatabaseAPI


# create the tables.
db_api = DatabaseAPI()
db_api.drop_tables()