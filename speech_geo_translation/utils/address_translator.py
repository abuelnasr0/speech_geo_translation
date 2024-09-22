import googlemaps

API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"


class AddressTranslator:
    def __init__(self, api_key: str = API_KEY):
        # Initialize the Google Maps client with the API key
        self.gmaps_client = googlemaps.Client(key=api_key)

    def __call__(self, address: str) -> dict[str, float]:

        # Geocoding an address
        geocode_result = self.gmaps_client.geocode(address)

        if geocode_result:
            # Extract latitude and longitude
            location = geocode_result[0]["geometry"]["location"]
            latitude = location["lat"]
            longitude = location["lng"]

        return {
            "longitude": longitude,
            "latitude": latitude,
        }
