# import pandas as pd # pip install pandas
from google_apis import create_service
import streamlit as st
# import os
import requests
# from dotenv import load_dotenv
# load_dotenv()
# maps_key = os.getenv('GOOGLE_MAPS_API')
maps_key = st.secrets["GOOGLE_MAPS_API"]
print(len(maps_key))

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


# https://developers.google.com/maps/documentation/places/web-service/experimental/places-generative



def text_search_new(query, budget, num_recs):
    # coordinates = get_maps_coordinates()
    # try:
    #     assert coordinates is not None, "coordinates weren't retrieved"
    #     latitude, longitude = coordinates
    # except Exception as e:
    #     print(e)
    temp_lat = 37.7614
    temp_lng = -122.3890
    url = 'https://places.googleapis.com/v1/places:searchText'

    # Define the headers
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': st.secrets["GOOGLE_MAPS_API"],  # Replace 'API_KEY' with your actual Google Places API key
        'X-Goog-FieldMask': 'places.name,places.displayName,places.primaryType,places.rating,' \
            'places.userRatingCount,places.priceLevel,places.generativeSummary.overview'
    }

    # Define the data payload for the POST request
    
    request_body = {
        'textQuery': query,
        'maxResultCount': num_recs,
        'locationBias': {
            'circle': {
                'center': {
                    'latitude': temp_lat,
                    'longitude': temp_lng,
                },
                'radius': 1000
            }
        },
        'rankPreference': 'RELEVANCE',
        'priceLevels': construct_budget(budget),
    }
    response = requests.post(url, headers=headers, json=request_body)
    print(response.json())
    return response.json()['places']


def get_place_details(name):
    response = requests.get(f"https://places.googleapis.com/v1/{name}?fields=*&key={st.secrets['GOOGLE_MAPS_API']}")
    # url = 'https://places.googleapis.com/v1/places:placeDetails'

    # # Define the headers
    # headers = {
    #     'Content-Type': 'application/json',
    #     'X-Goog-Api-Key': st.secrets["GOOGLE_MAPS_API"],  # Replace 'API_KEY' with your actual Google Places API key
    #     'X-Goog-FieldMask': '*'
    # }

    # request_body = {
    #     'name': name,
    # }
    
    # response = requests.post(url, headers=headers, json=request_body)
    # print(response)
    return response.json()

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
    print(coordinates)
    return (coordinates['location']['lat'], coordinates['location']['lng'])
