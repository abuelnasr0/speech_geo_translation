import argparse
import geopandas as gpd
import geonamescache
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
import numpy as np
from numpy.random import choice
import random
import datetime
from shapely import Point


SHAPEFILE = "/home/mohamed/Mohamed/Vodafone_project/all_egypt_map_shpfile/shp_output_names/Shyakha_Village/Shyakha_Village.shp"


def get_unknown_eg_areas_locations(area_gdf):
    # Read The area geodataframe

    centroids = area_gdf.centroid

    unkown_areas_locations = np.array([[cent.x, cent.y] for cent in centroids])

    return unkown_areas_locations


def get_known_eg_cities_df():
    gc = geonamescache.GeonamesCache()
    cities = gc.get_cities()
    cities_df = pd.DataFrame.from_dict(cities)
    cities_df = cities_df.transpose()
    cities_df = cities_df.drop(columns=["alternatenames", "admin1code"])
    cities_df = cities_df[cities_df["countrycode"] == "EG"]

    return cities_df


def get_trained_knn_model(known_pop_cities_df):
    x_train = np.vstack(
        [
            known_pop_cities_df["latitude"].values,
            known_pop_cities_df["longitude"].values,
        ]
    ).T
    y_train = known_pop_cities_df["population"].values
    knn_model = KNeighborsRegressor(weights="distance")
    knn_model.fit(x_train, y_train)

    return knn_model


def estimate_population(knn_model, unknown_pop_eg_areas):
    return knn_model.predict(unknown_pop_eg_areas)


def generate_random_complaints(
    areas_locations,
    areas_weights,
    days=30,
    num_complaints_aday=1000,
    start_date=datetime.datetime.now(),
):
    """Random complaints every day in Egypt cities"""

    hours_weights = np.array(
        [i + 1 for i in range(14)] + [i + 4 for i in range(10, 0, -1)]
    )
    hours_probability = hours_weights / np.sum(hours_weights)

    def get_random_time_delta():
        """Generates randome hours in a day.
        Gives moreweight for peak hours.
        """

        return datetime.timedelta(
            hours=int(choice([i for i in range(2, 26)], 1, p=hours_probability)),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

    def get_random_long(lang):
        scale = random.randint(0, 1)
        if scale:
            return lang + random.gauss(0.001, 0.0005)
        else:
            return lang + random.gauss(0.005, 0.0009)

    def get_random_lat(lat):
        scale = random.randint(0, 1)
        if scale:
            return lat + random.gauss(0.001, 0.0005)
        else:
            return lat + random.gauss(0.005, 0.0009)

    def get_random_complaint(date, city_id):
        long = get_random_long(float(areas_locations[city_id, 1]))
        lat = get_random_lat(float(areas_locations[city_id, 0]))
        time = date + get_random_time_delta()
        return {
            "longitude": long,
            "latitude": lat,
            "time": time,
        }

    complaints = []
    for i in range(0, days):
        curr_date = start_date + datetime.timedelta(days=i)
        cities_ids = choice(
            [j for j in range(len(areas_weights))],
            int(random.gauss(num_complaints_aday, 250)),
            p=areas_weights / np.sum(areas_weights),
        )
        for city_id in cities_ids:
            complaints.append(get_random_complaint(curr_date, city_id))

    return complaints


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--save_csv",
        default=True,
        type=bool,
        help=("Save complaints as csv."),
    )
    parser.add_argument(
        "--save_mysql",
        default=False,
        type=bool,
        help=("Save complaints into the database."),
    )

    parser.add_argument(
        "--days",
        default=365 * 3,
        type=int,
        help=("Number of days to generate complaints for."),
    )

    parser.add_argument(
        "--complaints_aday",
        default=10000,
        type=int,
        help=("Number of comlpaints to generate every day"),
    )

    # Read arguments
    args = parser.parse_args()
    save_csv = args.save_csv
    save_mysql = args.save_mysql
    days = args.days
    complaints_aday = args.complaints_aday

    # Get cities with know populations
    known_pop_eg_cities = get_known_eg_cities_df()

    # Get the train knn model for estimation
    knn_model = get_trained_knn_model(known_pop_eg_cities)

    # Get the centroid (location) of each polygon (area. e.g. (city, Village)),
    # To estimite their population.
    area_gdf = gpd.GeoDataFrame.from_file(SHAPEFILE)
    unknown_pop_eg_areas = get_unknown_eg_areas_locations(area_gdf)

    # Predict unkown areas population
    estimated_popualtion = estimate_population(knn_model, unknown_pop_eg_areas)

    print("Started random complaints generation.")

    # Important variables
    complaints = generate_random_complaints(
        unknown_pop_eg_areas,
        estimated_popualtion,
        days=days,
        num_complaints_aday=complaints_aday,
    )
    complaints_df = pd.DataFrame.from_records(complaints)

    print("Finished random complaints generation.")

    print("Started finding service area id.")

    # Convert the DataFrame to a GeoDataFrame
    geometry = [
        Point(xy) for xy in zip(complaints_df["longitude"], complaints_df["latitude"])
    ]
    complaints_points = gpd.GeoDataFrame(complaints_df, geometry=geometry)

    gdf_joined = gpd.sjoin(complaints_points, area_gdf, how="left", op="within")
    gdf_joined = gdf_joined[gdf_joined["index_right"].isna() != True]
    print(gdf_joined.columns)
    gdf_joined = gdf_joined.drop(
        columns=[
            "geometry",
            "SSEC_NAM_1",
            "SSEC_NAME_",
            "SEC_NAME_A",
            "SEC_NAME_E",
            "GOV_NAME_A",
            "GOV_NAME_E",
            "SHAPE_Area",
            "SHAPE_Leng",
            "index_right",
        ]
    )
    gdf_joined.GOV_CODE = gdf_joined.GOV_CODE.astype(int)
    gdf_joined.SEC_CODE = gdf_joined.SEC_CODE.astype(int)
    gdf_joined.SSEC_CODE = gdf_joined.SSEC_CODE.astype(int)
    gdf_joined.reset_index(drop=True, inplace=True)
    gdf_joined.rename(
        columns={
            "GOV_CODE": "governorate_id",
            "SEC_CODE": "qism_id",
            "SSEC_CODE": "service_area_id",
        },
        inplace=True,
    )

    print("Finished finding service area id.")

    if save_csv:
        print("Started saving csv.")
        gdf_joined.to_csv("complaints.csv")
        print("Finished saving csv.")


if __name__ == "__main__":
    main()
