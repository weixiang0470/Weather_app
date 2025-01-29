import geocoder
from geopy.geocoders import Nominatim

def get_current_gps_coordinates():
    g = geocoder.ip('me')#this function is used to find the current information using our IP Add
    if g.latlng is not None: #g.latlng tells if the coordiates are found or not
        return g.latlng
    else:
        return None

def get_city():
    coordinates = get_current_gps_coordinates()
    geolocator = Nominatim(user_agent="my_geopy_app")
    if coordinates is not None:
        latitude, longitude = coordinates
        #print(f"Your current GPS coordinates are:")
        # print(f"Latitude: {latitude}")
        # print(f"Longitude: {longitude}")
        location = geolocator.reverse(str(latitude)+","+str(longitude))
        address = location.raw['address']
        city = address.get('city', '')
        # state = address.get('state', '')
        # country = address.get('country', '')
        # code = address.get('country_code')
        # zipcode = address.get('postcode')
        # print(f'City: {city}')
        return city
    else:
        print("Unable to retrieve your GPS coordinates.")
        return None

    