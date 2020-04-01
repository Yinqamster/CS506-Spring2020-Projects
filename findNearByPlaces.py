# Importing required libraries
import requests 
import json 

import pandas as pd 
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

import time
from uszipcode import SearchEngine

# calculate driving distance between 2 points unit in miles
def calculateDistance(lat1, lng1, lat2, lng2):
    #url = 'http://router.project-osrm.org/route/v1/driving/'
    token = 'pk.eyJ1IjoidGF5bG9yaGF6bGV0dCIsImEiOiJjazgxc2o5Y24wdTU0M2V0bDNwYjZybGQzIn0.xwzXtsyAWHodfu86pkK4QQ'
    url = 'https://api.mapbox.com/directions/v5/mapbox/walking/'
    pos1 = str(lng1) +',' + str(lat1)
    pos2 = str(lng2) +',' + str(lat2)
    locations = pos1 +';'+pos2
    access = locations+'?access_token='+token
    response = requests.get(url+access)
    data = json.loads(response.content)
    if response.status_code == 200:
        print(data['routes'][0]['distance'])
        return data['routes'][0]['distance']*0.000621371 # in miles
    else:
        return 0

def convertZip(zipStr):
    """
    convert '2138.0' to '02138'
    """
    zipCode = ''
    if zipStr is not None:
        if '.' in zipStr:
            zipCode = '0' + zipStr[:4]
    return zipCode

def do_geocode(address, locator, loop=0):
    try:
        time.sleep(1)
        return locator.geocode(address)
    except GeocoderTimedOut:
        if loop >=5:
            return None
        return do_geocode(address, locator, loop+1)
    
    
def findLatitude_Longitude(street, zipCode, state, country, locator, searchEngine):
    city = searchEngine.by_zipcode(zipCode).major_city
    fullAddress= street+', '+ city +', '+ state+', '+ zipCode +', '+country
    print(fullAddress)
    location = do_geocode(fullAddress, locator)
    if not location:
        return [None,None]
    return [location.latitude, location.longitude]

# =============================================================================
# read filtered dataframe csv file
# =============================================================================
df = pd.read_csv('filtered_state_land.csv')
df =  df.loc[:,df.columns]

#clean zipcode
addressZip = df['addr_zip']
addressZip = addressZip.astype(str)
addressZip = addressZip.apply(convertZip)
df['addr_zip'] = addressZip

# get latitude and longitude of each address
# clean address column
address = df['addr_str']
df['addr_str'] = address.astype(str)

locator = Nominatim(user_agent="myGeocoder")
searchEngine= SearchEngine(simple_zipcode=True)

# save [latitude, longitude]
geoLocations = [0 for i in range(df.shape[0])]
for i in range(0, df.shape[0]):
    street = df['addr_str'][i]
    print(street)
    zipCode = df['addr_zip'][i]
    print(zipCode)
    print('Finding ',i,'th location')
    if not zipCode or zipCode == '':
        geoLocations[i] = [None, None]
    else:
        geoLocations[i] = findLatitude_Longitude(street, zipCode, 'MA','United States', locator, searchEngine)

# =============================================================================
# Google Places API Find nearby places
# =============================================================================
#REAL KEY
#api_key='AIzaSyBzJPJge8tfHAsbR4tDlEglR9XF4DJwIBQ'
api_key = 'AIzaSyBat0stmX_TWGWc6gU-Yn__Tr2WJiEBvmo' #You'll need your own API key: https://developers.google.com/places/web-service/get-api-key
business_types = ['transit_station']


def get_nearby_places(lat, long, business_type, next_page, radius=805):
    URL = ('https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='
		+lat+','+long+'&radius='+str(radius)+'&key='+ api_key +'&type='
		+business_type+'&pagetoken='+next_page)
    r = requests.get(URL)
    response = r.text
    python_object = json.loads(response)
    print(python_object)
    results = python_object["results"]
    for result in results:
        place_name = result['name']
        place_id = result['place_id']
        geometry = result['geometry']
        location = geometry['location']
        lat_i = location['lat']
        lng_i = location['lng']
        print([business_type, place_name,lat_i,lng_i])
        total_results.append([place_id, business_type, place_name, lat_i, lng_i])
    try:
        next_page_token = python_object["next_page_token"]
        time.sleep(1)
        print('here')
        get_nearby_places(lat, long, business_type, next_page_token, radius=805)
    except KeyError:
		#no next page
        return

#initialize variables to store location proximity information
# numBusStops = [-1 for i in range(len(geoLocations))]
# numSubwayStops = [-1 for i in range(len(geoLocations))]
# numTrainStops = [-1 for i in range(len(geoLocations))]
numTransitStops = [-1 for i in range(len(geoLocations))]

# get number of nearby transit stops within 1/2 mile
for i in range(len(geoLocations)):
    lat = str(geoLocations[i][0])
    long = str(geoLocations[i][1])
    print('Finding ',i,'th stops')
    if lat != 'None' and long != 'None':
        time.sleep(1)
        total_results = []
        get_nearby_places(lat, long, business_types[0],'')
        # get number of nearby bus stops for ith location
        numTransitStops[i] = len(total_results)

# # get number of nearby bus stops within 1/2 mile
# for i in range(len(geoLocations)):
#     lat = str(geoLocations[i][0])
#     long = str(geoLocations[i][1])
#     print('Finding ',i,'th stops')
#     if lat != 'None' and long != 'None':
#         time.sleep(1)
#         total_results = []
#         get_nearby_places(lat, long, business_types[0],'')
#         # get number of nearby bus stops for ith location
#         numBusStops[i] = len(total_results)

# get number of nearby subway stops within 1/2 mile
# for i in range(len(geoLocations)):
#     lat = str(geoLocations[i][0])
#     long = str(geoLocations[i][1])
#     print('Finding ',i,'th stops')
#     if lat != 'None' and long != 'None':
#         time.sleep(1)
#         total_results = []
#         get_nearby_places(lat, long, business_types[1],'')
#         # get number of nearby bus stops for ith location
#         numSubwayStops[i] = len(total_results)
# #
# # # get number of nearby train stops within 1/2 mile
# for i in range(len(geoLocations)):
#     lat = str(geoLocations[i][0])
#     long = str(geoLocations[i][1])
#     print('Finding ',i,'th stops')
#     if lat != 'None' and long != 'None':
#         time.sleep(1)
#         total_results = []
#         get_nearby_places(lat, long, business_types[2],'')
#         # get number of nearby bus stops for ith location
#         numTrainStops[i] = len(total_results)

# =============================================================================
# Google API: find average distance to bus, subway, train stops
# =============================================================================
# calculate average distance to different stations within 1/2 mile
def get_avg_distance(lat, long, business_type, next_page,radius=805):
    URL = ('https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='
		+lat+','+long+'&radius='+str(radius)+'&key='+ api_key +'&type='
		+business_type+'&pagetoken='+next_page)
    r = requests.get(URL)
    response = r.text
    python_object = json.loads(response)
    results = python_object["results"]
    for result in results:
        geometry = result.get('geometry')
        location = geometry.get('location')
        lat_i = float(location.get('lat'))
        lng_i = float(location.get('lng'))
        distance = calculateDistance(float(lat), float(long), lat_i, lng_i)
        if distance >= 0:
            avg_distance.append(distance)
    try:
        next_page_token = python_object["next_page_token"]
        time.sleep(1)
        get_avg_distance(lat, long, business_type, next_page_token, radius=805)
    except KeyError:
		#no next page
        return


#initialize vars to hold transportation proximity information
# avgDistanceBusStops = [-1 for i in range(len(geoLocations))]
# avgDistanceTrainStops = [-1 for i in range(len(geoLocations))]
# avgDistanceSubwayStops = [-1 for i in range(len(geoLocations))]
avgDistanceTransitStops = [-1 for i in range(len(geoLocations))]

# get avg dist from nearby transit stops within 1/2 miles
for i in range(len(geoLocations)):
    lat = str(geoLocations[i][0])
    long = str(geoLocations[i][1])
    print('Finding',i,'th stops')
    if lat != 'None' and long != 'None':
        time.sleep(1)
        avg_distance = []
        get_avg_distance(lat, long, business_types[0],'')
        # get avg distance of xxx stops for ith location
        if len(avg_distance) > 0:
            avgDistanceTransitStops[i] = sum(avg_distance)/len(avg_distance)
        else:
            avgDistanceTransitStops[i] = 0
    else:
        avgDistanceTransitStops[i] = -1
        print(i,'th Location info not available!')

# # get avg dist from nearby bus stops within 1/2 miles
# for i in range(len(geoLocations)):
#     lat = str(geoLocations[i][0])
#     long = str(geoLocations[i][1])
#     print('Finding',i,'th stops')
#     if lat != 'None' and long != 'None':
#         time.sleep(1)
#         avg_distance = []
#         get_avg_distance(lat, long, business_types[0],'')
#         # get avg distance of xxx stops for ith location
#         if len(avg_distance) > 0:
#             avgDistanceBusStops[i] = sum(avg_distance)/len(avg_distance)
#         else:
#             avgDistanceBusStops[i] = 0
#     else:
#         avgDistanceBusStops[i] = -1
#         print(i,'th Location info not available!')

# # get avg dist from nearby subway stops within 1/2 miles
# for i in range(len(geoLocations)):
#     lat = str(geoLocations[i][0])
#     long = str(geoLocations[i][1])
#     print('Finding',i,'th stops')
#     if lat != 'None' and long != 'None':
#         time.sleep(1)
#         avg_distance = []
#         get_avg_distance(lat, long, business_types[1],'')
#         # get avg distance of xxx stops for ith location
#         if len(avg_disance) > 0:
#             avgDistanceSubwayStops[i] = sum(avg_distance)/len(avg_distance)
#         else:
#             avgDistanceSubwayStops[i] = 0
#     else:
#         avgDistanceSubwayStops[i] = -1
#         print(i,'th Location info not available!')
#
# ##get avg dist from nearby train stops within 1/2 miles
# for i in range(len(geoLocations)):
#     lat = str(geoLocations[i][0])
#     long = str(geoLocations[i][1])
#     if lat != 'None' and long != 'None':
#         time.sleep(1)
#         avgDistance = get_avg_distance(lat, long, business_types[2],'')
#         # get avg distance of xxx stops for ith location
#         if len(avg_distance) > 0:
#             avgDistanceTrainStops[i] = sum(avg_distance)/len(avg_distance)
#         else:
#             avgDistanceTrainStops[i] = 0
#     else:
#         avgDistanceTrainStops[i] = -1
#         print(i,'th Location info not available!')
        
# =============================================================================
# Append coordinate locations on the final dataframe
# =============================================================================
df['latitude'] = [x[0] for x in geoLocations]
df['longitude'] = [x[1] for x in geoLocations]

# =============================================================================
# Append avg distance to stations within 1/2 mile on the final dataframe
# =============================================================================
# df['avgDistanceBusStops'] = avgDistanceBusStops
# df['avgDistanceSubwayStops'] = avgDistanceSubwayStops
# df['avgDistanceTrainStops'] = avgDistanceTrainStops
df['avgDistanceTransitStops'] = avgDistanceTransitStops

# df['numBusStops'] = numBusStops
# df['numSubwayStops'] = numSubwayStops
# df['numTrainStops'] = numTrainStops
df['numTransitStops'] = numTransitStops


# save final result as csv
df.to_csv('transport_proximity.csv',index=False)
