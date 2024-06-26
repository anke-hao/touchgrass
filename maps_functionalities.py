import pandas as pd # pip install pandas
from google_apis import create_service
import geocoder
import touchgrass
import os
import requests
from dotenv import load_dotenv
load_dotenv()
maps_key = os.getenv('GOOGLE_MAPS_API')


def places_hub(places_type, query, budget, num_recs):
    client_secret_file = 'secrets\client_secret_desktop.json'
    API_NAME = 'places'
    API_VERSION = 'v1'
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
    service = create_service(client_secret_file, API_NAME, API_VERSION, SCOPES)
    
    coordinates = get_maps_coordinates()
    try:
        assert coordinates is not None, "coordinates weren't retrieved"
        latitude, longitude = coordinates
    except Exception as e:
        print(e)
    
    if places_type == 'text_search':
        request_body = text_search(query, budget, num_recs, latitude, longitude )
        response = service.places().searchText(
        body = request_body,
        # no spaces in the fields parameter!!!
        fields = 'places.displayName,places.primaryType,places.rating,' \
            'places.userRatingCount,places.priceLevel,places.generativeSummary.overview'
        ).execute()
        
    elif places_type == 'nearby_search':
        request_body = 'pending'
        
    return response['places']
        
# https://developers.google.com/maps/documentation/places/web-service/experimental/places-generative

def text_search(query, budget, num_recs, latitude, longitude):
    request_body = {
        'textQuery': query,
        'maxResultCount': num_recs,
        'locationBias': {
            'circle': {
                'center': {
                    'latitude': latitude,
                    'longitude': longitude,
                },
                'radius': 1000
            }
        },
        'rankPreference': 'RELEVANCE',
        'priceLevels': touchgrass.construct_budget(budget),
    }
    return request_body


def nearby_search(query, budget, num_recs, latitude, longitude):
    request_body = {
        'includedTypes': touchgrass.get_food_type(query),
        'maxResultCount': num_recs,
        'locationRestriction': {
            'circle': {
                'center': {
                    'latitude': latitude,
                    'longitude': longitude,
                },
                'radius': 1000
            }
        },
        'rankPreference': 'POPULARITY',
    }
    return request_body
    

# try geocoder
def get_geocoder_coordinates():
    g = geocoder.ip('me')#this function is used to find the current information using our IP Add
    if g.latlng is not None: #g.latlng tells if the coordinates are found or not
        return g.latlng
    else:
        return None

# try maps (seems to be slightly more accurate)
def get_maps_coordinates():
    url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={maps_key}'

    coordinates = requests.post(url).json()
    # return a tuple with latitude and longitude
    return (coordinates['location']['lat'], coordinates['location']['lng'])



# df = pd.json_normalize(places_list)
# df.to_csv('places_results.csv', index=False)