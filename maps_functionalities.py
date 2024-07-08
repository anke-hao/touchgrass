import streamlit as st
import requests
import googlemaps


maps_key = st.secrets["GOOGLE_MAPS_API"]
gmaps = googlemaps.Client(key=maps_key)


def construct_budget(budget):
    """
    Based on whether user selected "casual", "mid-range", or "fine dining"
    as their budget choice, return the corresponding request parameter needed
    for the Places API

    Parameters:
        budget (str): user-specified budget
        
    Returns:
        price_dict[budget]: Dictionary value corresponding to 'budget' key
    """
    price_dict = {'casual': 'PRICE_LEVEL_INEXPENSIVE', 
                  'mid-range': 'PRICE_LEVEL_MODERATE', 
                  'fine dining': ['PRICE_LEVEL_EXPENSIVE', 
                                  'PRICE_LEVEL_VERY_EXPENSIVE']
                }
    return price_dict[budget]


def get_distance(place_id, coordinates):
    """
    Given the coordinates of the specified user location and the Place ID of 
    the recommended place, calculate the distance in miles between the two

    Parameters:
        place_id (str): unique Place id
        coordinates (Dict): user-specified coordinates (latitude and longitude)
    
    Returns:
        price_dict[budget]: Dictionary value corresponding to 'budget' key
    """
    processed_place_id = place_id.replace('places/', 'place_id:')
    try:
        lat = coordinates['lat']
        lng = coordinates['lng']
    except Exception as e:
        print(e)
    result = gmaps.distance_matrix((lat, lng), processed_place_id, 
                                    mode = 'driving', units = 'imperial')
    miles = result["rows"][0]["elements"][0]["distance"]["text"]
    return miles


def autocomplete(query):
    """
    Given the user's search query for an address/place, suggest a list of 
        autocompletions

    Parameters:
        query (str): user query
    
    Returns:
        response.json(): JSON with list of autocomplete suggestions of places
    """
    url = 'https://places.googleapis.com/v1/places:autocomplete'

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': maps_key,  
    }
    
    request_body = {
        'input': query,
    }
    response = requests.post(url, headers=headers, json=request_body)
    return response.json()


def geocoder(address):
    """
    Given an address, return the latitude and longitude coordinates
    
    Parameters: 
        address (str): address of a Place

    Returns:
        coords: dictionary with 'lat' and 'lng' as keys
    """
    geocode_result = gmaps.geocode(address)
    coords = geocode_result[0]["geometry"]["location"]
    return coords
    
    
def text_search_new(query, budget, num_recs, coordinates):
    """
    Given the user's search query and their specified budget, number of 
        recommendations to generate, and coordinates (either their own or a
        specified location), search for recommendations nearby

    Parameters: 
        query (str): user query
        budget (str): user-specified budget
        num_recs (int): user-specified number of recommendations to generate
        coordinates (Dict): user-specified coordinates (latitude and longitude)
            
    Returns:
        places: list of places, each with the information specified in the 
        FieldMask of the headers
    """
    try:
        lat = coordinates['lat']
        lng = coordinates['lng']
    except Exception as e:
        print(e)
    url = 'https://places.googleapis.com/v1/places:searchText'

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': st.secrets["GOOGLE_MAPS_API"],  
        'X-Goog-FieldMask': 'places.name,places.displayName,places.rating,' \
                    'places.userRatingCount,places.priceLevel,' \
                    'places.generativeSummary.overview,places.googleMapsUri,' \
                    'places.formattedAddress'
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
    places = response.json()['places']
    return places


def get_place_details(place_id):
    """
    Given the (non-human-readable) name of a Place, get all the information 
        possible from the Places API

    Parameters: 
        place_id (str): unique Place id
        
    Returns:
        response.json(): JSON-formatted information about a Place. 
            Documentation of data fields located here: 
            https://developers.google.com/maps/documentation/places/web-service/data-fields
    """
    response = requests.get(
        f"https://places.googleapis.com/v1/{place_id}?fields=*&key={st.secrets['GOOGLE_MAPS_API']}"
        )
    return response.json()

