
import googlemaps
class AddressTranslator:
    def __init__(
        self,
    ):
        pass

    def __call__(self, api_key: str, address: str) -> dict[str, float]:

        # Initialize the Google Maps client with the API key
        gmaps = googlemaps.Client(key=api_key)
        
        # Geocoding an address
        geocode_result = gmaps.geocode(address)
        
        if geocode_result:
            # Extract latitude and longitude
            location = geocode_result[0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
        else:
            latitude = None
            longitude = None


        return {
            "longitude": longitude,
            "latitude": latitude,
        }
