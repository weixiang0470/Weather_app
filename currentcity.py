import geocoder
from geopy.geocoders import Nominatim

# Get current coordinates by ip address
def get_current_gps_coordinates():

    g = geocoder.ip('me')#this function is used to find the current information using our IP Add
    if g.latlng is not None: #g.latlng tells if the coordinates are found or not
        return g.latlng
    else:
        return None

# Get city name by current ip address
def get_city():
    coordinates = get_current_gps_coordinates()
    print(f'{coordinates=}')
    geolocator = Nominatim(user_agent="my_geopy_app")
    print(f'{geolocator=}')
    if coordinates is not None:
        latitude, longitude = coordinates
        location = geolocator.reverse(str(latitude)+","+str(longitude))
        # print(f'{location=}')
        address = location.raw['address']
        # print(f'{address}')
        city = address.get('city', '')
        if not city: city = address.get('state', '')
        if not city: city = address.get('country', '')
        # state = address.get('state', '')
        # country = address.get('country', '')
        # code = address.get('country_code')
        # zipcode = address.get('postcode')
        # print(f'City: {city}')
        return city
    else:
        print("Unable to retrieve your GPS coordinates.")
        return None

    