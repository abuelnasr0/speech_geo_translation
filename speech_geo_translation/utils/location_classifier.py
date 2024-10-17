import geopandas as gpd
from shapely import Point
import numpy as np

SHAPEFILE_PATH = "/home/mohamed/Mohamed/Vodafone_project/all_egypt_map_shpfile/shp_output_names/Shyakha_Village/Shyakha_Village.shp"


class LocationClassifier:
    def __init__(self, shapefile_path=SHAPEFILE_PATH):
        self.locations_gdf = gpd.GeoDataFrame.from_file(shapefile_path)

    def __call__(self, location):
        loc_point = Point(location[1], location[0])
        location_data = self.locations_gdf[self.locations_gdf.contains(loc_point)]
        if len(location_data) == 0:
            # get nereast place
            location_index = (
                self.locations_gdf.distance(loc_point).sort_values().index[0]
            )
            location_data = self.locations_gdf.loc[location_index]

        gov_ar = location_data["GOV_NAME_A"].values[0]
        sec_ar = location_data["SEC_NAME_A"].values[0]
        ssec_ar = location_data["SSEC_NAM_1"].values[0]
        gov_en = location_data["GOV_NAME_E"].values[0]
        sec_en = location_data["SEC_NAME_E"].values[0]
        ssec_en = location_data["SSEC_NAME_"].values[0]
        gov_id = int(location_data["GOV_CODE"])
        sec_id = int(location_data["SEC_CODE"])
        ssec_id = int(location_data["SSEC_CODE"])

        if not isinstance(gov_ar, str):
            gov_ar = gov_ar.values[0]
        if not isinstance(gov_ar, str):
            sec_ar = sec_ar.values[0]
        if not isinstance(gov_ar, str):
            ssec_ar = ssec_ar.values[0]

        if not isinstance(gov_ar, str):
            gov_en = gov_en.values[0]
        if not isinstance(gov_ar, str):
            sec_en = sec_en.values[0]
        if not isinstance(gov_ar, str):
            ssec_en = ssec_en.values[0]

        return {
            "gov_ar": gov_ar,
            "sec_ar": sec_ar,
            "ssec_ar": ssec_ar,
            "gov_en": gov_en,
            "sec_en": sec_en,
            "ssec_en": ssec_en,
            "gov_id": gov_id,
            "sec_id": sec_id,
            "ssec_id": ssec_id,
        }
