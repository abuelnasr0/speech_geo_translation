import sys
import geopandas as gpd

sys.path.insert(0, "./")

from speech_geo_translation.database.database_api import DatabaseAPI

SHAPEFILE_PATH = "/home/mohamed/Mohamed/Vodafone_project/all_egypt_map_shpfile/shp_output_names/Shyakha_Village/Shyakha_Village.shp"
locations_gdf = gpd.GeoDataFrame.from_file(SHAPEFILE_PATH)


def truncate_name(x):
    x["name"] = x["name"][:70]
    return x


# Get all Govs
govs = locations_gdf[["GOV_CODE", "GOV_NAME_E"]]
govs = govs.drop_duplicates()
govs = govs.rename(columns={"GOV_CODE": "id", "GOV_NAME_E": "name",})
govs =govs.apply(truncate_name, axis=1)

govs_list =govs.to_dict("records")


# Get all qisms markazes
secs = locations_gdf[["SEC_CODE", "GOV_CODE", "SEC_NAME_E"]]
secs = secs.drop_duplicates()
secs = secs.rename(columns={"SEC_CODE": "id", "GOV_CODE": "governorate_id", "SEC_NAME_E": "name",})
secs =secs.apply(truncate_name, axis=1)

secs_list =secs.to_dict("records")

# get all areas (shayka, village)
areas = locations_gdf[["SSEC_CODE", "SEC_CODE", "GOV_CODE", "SSEC_NAME_", ]]
areas = areas.drop_duplicates()
areas = areas.rename(columns={"SSEC_CODE": "id", "SEC_CODE": "qism_id", "GOV_CODE": "governorate_id", "SSEC_NAME_": "name",})
areas =areas.apply(truncate_name, axis=1)

areas_list =areas.to_dict("records")


# create the tables.
db_api = DatabaseAPI()
db_api.creat_tables()
db_api.initialize_tables(govs_list, secs_list, areas_list)
