# import pandas as pd # pip install pandas
from google_apis import create_service
import streamlit as st

# import os
import requests
import googlemaps
maps_key = st.secrets["GOOGLE_MAPS_API"]
gmaps = googlemaps.Client(key=maps_key)

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


def get_distance(coordinates, place_id):
    processed_place_id = place_id.replace('places/', 'place_id:')
    try:
        lat = coordinates['lat']
        lng = coordinates['lng']
    except Exception as e:
        print(e)
    result = gmaps.distance_matrix((lat, lng), processed_place_id, mode = 'driving', units = 'imperial')
    miles = result["rows"][0]["elements"][0]["distance"]["text"]
    return miles


# https://developers.google.com/maps/documentation/places/web-service/experimental/places-generative

def autocomplete(query):
    # response = requests.get(f"https://places.googleapis.com/v1/{query}?fields=*&key={st.secrets['GOOGLE_MAPS_API']}")
    url = 'https://places.googleapis.com/v1/places:autocomplete'

    # Define the headers
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': maps_key,  # Replace 'API_KEY' with your actual Google Places API key
    }
    
    request_body = {
        'input': query,
    }
    response = requests.post(url, headers=headers, json=request_body)
    return response.json()

def geocoder(address):
    geocode_result = gmaps.geocode(address)
    return geocode_result[0]["geometry"]["location"]
    
    
def text_search_new(query, budget, num_recs, coordinates):
    try:
        lat = coordinates['lat']
        lng = coordinates['lng']
        print(lat)
    except Exception as e:
        print(e)
    url = 'https://places.googleapis.com/v1/places:searchText'

    # Define the headers
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': st.secrets["GOOGLE_MAPS_API"],  # Replace 'API_KEY' with your actual Google Places API key
        'X-Goog-FieldMask': 'places.name,places.displayName,places.primaryType,places.rating,' \
            'places.userRatingCount,places.priceLevel,places.generativeSummary.overview,' \
            'places.googleMapsUri'
    }
    
    request_body = {
        'textQuery': query,
        'maxResultCount': num_recs,
        'locationBias': {
            'circle': {
                'center': {
                    'latitude': lat,
                    'longitude': lng,
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
