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
from datetime import datetime, timedelta

import warnings

# Suppress FutureWarnings
warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=UserWarning)


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


def get_multiplier_dict(gaussians_list, multiplier_range):
    gaussians = []
    for instance in multiplier_range:
        all_gaussian = 0.0
        magnify = False
        for guassian_params in gaussians_list:

            mean = guassian_params["mean"]
            if instance == mean:
                magnify = True

            std_dev = guassian_params["std_dev"]

            # Calculate Gaussian value and normalize to ensure max is 1
            gaussian_value = np.exp(-((instance - mean) ** 2) / (2 * std_dev**2))
            all_gaussian += gaussian_value

        if magnify:
            all_gaussian *= 1.05
        gaussians.append(all_gaussian)

    gaussians_normalizd = np.array(gaussians) / np.max(np.array(gaussians))

    return gaussians_normalizd


def get_month_gaussian(peak_instances):
    length = len(peak_instances)
    std = 1 / length * 24
    gaussian_list = list()
    for peak_instance in peak_instances:
        gaussian_list.append({"mean": peak_instance, "std_dev": std})

    return gaussian_list


def get_day_gaussian(peak_instances):
    length = len(peak_instances)
    std = 1 / length * 14
    gaussian_list = list()
    for peak_instance in peak_instances:
        gaussian_list.append({"mean": peak_instance, "std_dev": std})

    return gaussian_list


def get_hour_gaussian(peak_instances):
    length = len(peak_instances)
    std = 1 / length * 18
    gaussian_list = list()
    for peak_instance in peak_instances:
        gaussian_list.append({"mean": peak_instance, "std_dev": std})

    return gaussian_list


def get_year_multiplier_dict(start, end, freq, padding=0):
    multiplier_dict = dict()
    for i in range(start, end):
        if (i - (start + padding)) % freq == 0:
            multiplier_dict[i] = np.random.uniform(0.90, 1.0)
        else:
            multiplier_dict[i] = np.random.uniform(0.75, 0.85)

    return multiplier_dict


def generate_random_complaints(
    complaints_count,
    complaints_count_period,
    start_year,
    end_year,
    year_seasonality_freq,
    peak_hours,
    peak_days,
    peak_months,
    areas_gdf,
    areas_weights,
):
    month_multiplier = get_multiplier_dict(
        get_month_gaussian(peak_months), [i + 1 for i in range(12)]
    )
    day_multiplier = get_multiplier_dict(
        get_day_gaussian(peak_days), [i + 1 for i in range(7)]
    )
    hour_multiplier = get_multiplier_dict(
        get_hour_gaussian(peak_hours), [i for i in range(24)]
    )

    start_date = datetime(start_year, 1, 1)
    end_date = datetime(2010, 12, 31, 23, 59)

    # Time delta of 15 minutes
    qhr_time_delta = timedelta(minutes=complaints_count_period)

    # Initialize current date to start date
    current_date = start_date
    complaints = []
    while current_date <= end_date:
        print(current_date.strftime("%Y-%m-%d %H:%M"))
        curr_complaints_count = int(
            complaints_count
            * month_multiplier_dict[current_date.month]
            * day_multiplier_dict[current_date.weekday() + 1]
            * hour_multiplier_dict[current_date.hour]
        )
        for i in range(len(areas_gdf)):
            area_complaints_count = int(curr_complaints_count * areas_weights[i])
            multi_point = areas_gdf.iloc[[i]].sample_points(size=area_complaints_count)
            for v in range(area_complaints_count):
                complaints.append(
                    {
                        "longitude": multi_point.get_coordinates().iloc[v].x,
                        "latitude": multi_point.get_coordinates().iloc[v].y,
                        "time": current_date
                        + timedelta(
                            minutes=np.random.randint(0, 15),
                            seconds=np.random.randint(0, 60),
                        ),
                        "service_area_id": int(areas_gdf.iloc[i]["SSEC_CODE"]),
                    }
                )

        current_date += qhr_time_delta
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
        "--complaints_count",
        default=15,
        type=int,
        help=("Number of comlpaints to generate every `complaints_count_period`"),
    )

    parser.add_argument(
        "--complaints_count_period",
        default=12,
        type=int,
        help=("the period that the `complaint_counts` should be in"),
    )

    parser.add_argument(
        "--start_year",
        default=2008,
        type=int,
        help=("the year to start generating time series data from."),
    )

    parser.add_argument(
        "--end_year",
        default=2024,
        type=int,
        help=("the year to end generating time series data at."),
    )

    parser.add_argument(
        "--year_seasonality_freq",
        default=3,
        type=int,
        help=(
            "The year's frequency where the complaints increase at. for example every 3 years."
        ),
    )

    parser.add_argument(
        "--peak_hours",
        default=[9, 13, 14],
        action="append",
        help="The peak hours in the day",
    )

    parser.add_argument(
        "--peak_days",
        default=[3, 4],
        action="append",
        help="The peak days in the week",
    )

    parser.add_argument(
        "--peak_months",
        default=[9, 10, 2, 3],
        action="append",
        help="The peak months in the year",
    )

    parser.add_argument(
        "--only_counts",
        default=True,
        type=bool,
        help="Return counts with out longitude and latitude",
    )

    # Read arguments
    args = parser.parse_args()
    save_csv = args.save_csv
    save_mysql = args.save_mysql
    complaints_count = args.complaints_count
    complaints_count_period = args.complaints_count_period
    start_year = args.start_year
    end_year = args.end_year
    year_seasonality_freq = args.year_seasonality_freq
    peak_hours = args.peak_hours
    peak_days = args.peak_days
    peak_months = args.peak_months
    only_counts = args.only_counts

    # Get cities with know populations
    known_pop_eg_cities = get_known_eg_cities_df()

    # Get the train knn model for estimation
    knn_model = get_trained_knn_model(known_pop_eg_cities)

    # Get the centroid (location) of each polygon (area. e.g. (city, Village)),
    # To estimite their population.
    areas_gdf = gpd.GeoDataFrame.from_file(SHAPEFILE)
    unknown_pop_eg_areas = get_unknown_eg_areas_locations(areas_gdf)

    # Predict unkown areas population
    estimated_popualtion = np.array(
        estimate_population(knn_model, unknown_pop_eg_areas), dtype=float
    )
    estimated_popualtion = estimated_popualtion / np.max(estimated_popualtion)
    x = np.exp(estimated_popualtion - np.max(estimated_popualtion)) / np.sum(
        np.exp(estimated_popualtion - np.max(estimated_popualtion)), axis=0
    )

    areas_weights = x / np.max(x)

    print("Started random complaints generation.")

    year_multiplier_dict = get_year_multiplier_dict(
        start_year, end_year, year_seasonality_freq
    )

    initial_complaints = generate_random_complaints(
        complaints_count=complaints_count * year_multiplier_dict[start_year],
        complaints_count_period=complaints_count_period,
        start_year=start_year,
        end_year=end_year,
        year_seasonality_freq=year_seasonality_freq,
        peak_hours=peak_hours,
        peak_days=peak_days,
        peak_months=peak_months,
        areas_gdf=areas_gdf,
        areas_weights=areas_weights,
        only_counts=only_counts,
    )
    print(initial_complaints)
    print(len(initial_complaints))
    print(len(areas_gdf))

    # complaints_df = pd.DataFrame.from_records(complaints)

    # print("Finished random complaints generation.")

    # print("Started finding service area id.")

    # # Convert the DataFrame to a GeoDataFrame
    # geometry = [
    #     Point(xy) for xy in zip(complaints_df["longitude"], complaints_df["latitude"])
    # ]
    # complaints_points = gpd.GeoDataFrame(complaints_df, geometry=geometry)

    # gdf_joined = gpd.sjoin(complaints_points, area_gdf, how="left", op="within")
    # gdf_joined = gdf_joined[gdf_joined["index_right"].isna() != True]
    # print(gdf_joined.columns)
    # gdf_joined = gdf_joined.drop(
    #     columns=[
    #         "geometry",
    #         "SSEC_NAM_1",
    #         "SSEC_NAME_",
    #         "SEC_NAME_A",
    #         "SEC_NAME_E",
    #         "GOV_NAME_A",
    #         "GOV_NAME_E",
    #         "SHAPE_Area",
    #         "SHAPE_Leng",
    #         "index_right",
    #     ]
    # )
    # gdf_joined.GOV_CODE = gdf_joined.GOV_CODE.astype(int)
    # gdf_joined.SEC_CODE = gdf_joined.SEC_CODE.astype(int)
    # gdf_joined.SSEC_CODE = gdf_joined.SSEC_CODE.astype(int)
    # gdf_joined.reset_index(drop=True, inplace=True)
    # gdf_joined.rename(
    #     columns={
    #         "GOV_CODE": "governorate_id",
    #         "SEC_CODE": "qism_id",
    #         "SSEC_CODE": "service_area_id",
    #     },
    #     inplace=True,
    # )

    # print("Finished finding service area id.")

    # if save_csv:
    #     print("Started saving csv.")
    #     gdf_joined.to_csv("complaints.csv")
    #     print("Finished saving csv.")


if __name__ == "__main__":
    main()
