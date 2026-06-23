from geopy.geocoders import Nominatim

geolocator = Nominatim(
    user_agent="traffic_management_system"
)

def get_coordinates(location_name):

    try:

        location = geolocator.geocode(
            f"{location_name}, Bangalore, India"
        )

        if location:

            return (
                location.latitude,
                location.longitude
            )

    except Exception as e:

        print(e)

    return None