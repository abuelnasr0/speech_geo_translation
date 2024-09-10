import sys
sys.path.insert(0,"./")

from speech_geo_translation.database.database_api import DatabaseAPI


# create the tables.
db_api = DatabaseAPI()
db_api.creat_tables()