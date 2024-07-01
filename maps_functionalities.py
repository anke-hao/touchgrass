import pandas as pd # pip install pandas
from google_apis import create_service
import os
import requests
from dotenv import load_dotenv
load_dotenv()
maps_key = os.getenv('GOOGLE_MAPS_API')



def construct_budget(budget):
    price_dict = {'casual': 'PRICE_LEVEL_INEXPENSIVE', 
                  'mid-range': 'PRICE_LEVEL_MODERATE', 
                  'fine dining': ['PRICE_LEVEL_EXPENSIVE', 
                                  'PRICE_LEVEL_VERY_EXPENSIVE']
                }
    return price_dict[budget]


def get_food_type(cuisine):
    if cuisine != "cafe":
        mod_cuisine = cuisine.replace(' ', '_')
        return [f'{mod_cuisine}_restaurant', 'restaurant']
    else:
        return ["cafe"]
    
    
# query is defined as:
# for text_search: the text query that the user inputted
# for nearby_search: pending
# for place_details: the place_id for the specific place that the user is querying

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
        request_body = text_search(query, budget, num_recs, latitude, longitude)
        response = service.places().searchText(
        body = request_body,
        # no spaces in the fields parameter!!!
        fields = 'places.name,places.displayName,places.primaryType,places.rating,' \
            'places.userRatingCount,places.priceLevel,places.generativeSummary.overview'
        ).execute()
        return response['places']
        
    elif places_type == 'nearby_search':
        request_body = 'pending'
    
    elif places_type == 'place_details':
        response = service.places().get(
            name = query,
            fields = '*'
        ).execute()
    return response
        
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
        'priceLevels': construct_budget(budget),
    }
    return request_body


def nearby_search(query, budget, num_recs, latitude, longitude):
    request_body = {
        'includedTypes': get_food_type(query),
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
    

# try maps (seems to be slightly more accurate than geocoder)
def get_maps_coordinates():
    url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={maps_key}'

    coordinates = requests.post(url).json()
    # return a tuple with latitude and longitude
    return (coordinates['location']['lat'], coordinates['location']['lng'])
