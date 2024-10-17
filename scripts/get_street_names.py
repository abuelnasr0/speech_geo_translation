import gc
import osmnx as ox
import re
from num2words import num2words
import geopandas as gpd
import os
import shutil


GOVS = [
    "Cairo Governorate",
    "Alexandria Governorate",
    "PortSaid Governorate",
    "Suez Governorate",
    "Damietta Governorate",
    "Dakahlia Governorate",
    "Sharqiyah Governorate",
    "Qalyubia",
    "KafrEl-Sheikh Governorate",
    "Gharbiya Governorate",
    "Menoufia Governorate",
    "Beheira Governorate",
    "Ismailia Governorate",
    "Giza Governorate",
    "BeniSuef Governorate",
    "Fayoum Governorate",
    "Minya Governorate",
    "Assiut Governorate",
    "Sohag Governorate",
    "Qena Governorate",
    "Aswan Governorate",
    "Luxor",
    "Red Sea Governorate",
    "New Valley Governorate",
    "Matrouh Governorate",
    "North Sinai Governorate",
    "South Sinai Governorate",
]

egy = gpd.GeoDataFrame.from_file(
    "/content/drive/MyDrive/vodafone/shp_output_names/Shyakha_Village/Shyakha_Village.shp"
)
egy = egy.drop(
    columns=[
        "GOV_CODE",
        "SEC_CODE",
        "SSEC_CODE",
        "SHAPE_Leng",
        "SHAPE_Area",
        "GOV_NAME_E",
        "SEC_NAME_E",
        "SSEC_NAME_",
    ]
)


def remove_list_names(x):
    # Remove Lists only strings
    if isinstance(x["name"], list):
        x["name"] = x["name"][0]
    x["name"] = str(x["name"])

    # Remove punctioation
    x["name"] = re.sub(r"[^\w\s]", "", x["name"])

    # Remove enlgish letters
    x["name"] = re.sub(r"[A-za-z]", "", x["name"])

    return x


def convert_numbers_to_str(x):
    nums = re.findall(r"\d+", x["name"])
    for num in nums:
        x["name"] = x["name"].replace(str(num), num2words(int(num), lang="ar"))

    nums = re.findall(r"\d+", x["SSEC_NAM_1"])
    for num in nums:
        x["SSEC_NAM_1"] = x["SSEC_NAM_1"].replace(
            str(num), num2words(int(num), lang="ar")
        )

    return x


def write_gov_streets(gov, folder):
    place_name = gov + ", Egypt"

    print(f"Collecting {gov}")
    print()

    # Download the street network for the specified place
    graph = ox.graph_from_place(place_name, network_type="all")

    # Get the nodes and edges from the graph
    nodes, edges = ox.graph_to_gdfs(graph)
    edges = edges[edges["name"].isna() != True]
    edges = edges.drop(
        columns=[
            "oneway",
            "lanes",
            "highway",
            "maxspeed",
            "reversed",
            "length",
            "bridge",
            "access",
            "junction",
            "tunnel",
            "service",
            "ref",
            "width",
        ],
        errors="ignore",
    )
    edgesx = edges.apply(remove_list_names, axis=1)

    street_names = gpd.sjoin(egy, edgesx, op="intersects")
    street_names.reset_index(inplace=True)
    street_names = street_names.drop(
        columns=[
            "geometry",
            "index_right0",
            "index_right1",
            "index_right2",
            "osmid",
            "index",
        ],
        errors="ignore",
    )
    street_names = street_names.drop_duplicates()
    street_names = street_names.apply(convert_numbers_to_str, axis=1)

    street_names.to_csv(os.path.join(folder, gov.replace(" ", "_") + ".csv"))

    cache_path = "/content/cache"

    if os.path.exists(cache_path) and os.path.isdir(cache_path):
        shutil.rmtree(cache_path)

    del graph
    del nodes
    del edges
    del edgesx
    del street_names

    gc.collect()


if __name__ == "__main__":
    for gov in GOVS:
        place_name = gov + ", Egypt"

        # Download the street network for the specified place
        graph = ox.graph_from_place(place_name, network_type="all")

        # Get the nodes and edges from the graph
        nodes, edges = ox.graph_to_gdfs(graph)

        del graph
        del nodes
        del edges
        gc.collect()
