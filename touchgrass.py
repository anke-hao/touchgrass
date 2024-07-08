import streamlit_js_eval
import streamlit as st
import folium
from streamlit_folium import st_folium
import maps_functionalities as maps_func
import google.generativeai as genai


genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
initial_coordinates = streamlit_js_eval.get_geolocation()


def load_model():
    """
    Load the generative model.

    Parameters: N/A
    
    Returns:
        model_flash (GenerativeModel): Gemini 1.5 Flash
    """
    config = {
        "temperature": 0.7,
        "max_output_tokens": 2048,
    }
    system_instruction = f"""
        You are a helpful local guide who knows the best food in the area. \n
        You must answer questions about {st.session_state.place_name} as 
        accurately as possible, given the user query {query} and the following 
        JSON of details: \n
        {st.session_state.place_details}
    """
    model_flash = genai.GenerativeModel(
        model_name = "gemini-1.5-flash",
        generation_config=config,
        system_instruction=system_instruction,
        )
    return model_flash


def stream_data(query):
    """
    Preprocesses the response to be streamed

    Parameters:
        query (str): the user query to the chatbot
    
    Returns:
        N/A (yields the response text chunks as they are generated)
    """
    stream = st.session_state.chat.send_message(query, stream=True)
    for part in stream:
        yield part.text
       
        
def get_llm_response(query):
    """
    Streams the LLM response

    Parameters:
        query (str): the user query to the chatbot
    
    Returns:
        response (str): the generated response to the user query
    """
    response = st.write_stream(stream_data(query))
    return response


def get_place(place_id, place_name):
    """
    Stores key information about the specified Place and starts the Q&A session

    Parameters:
        place_id (str): the unique Place ID of the Place
        place_name (str): the human-readable name of the Place
    
    Returns:
        N/A 
    """
    st.session_state.place = place_id
    st.session_state.place_name = place_name
    st.session_state.place_details = maps_func.get_place_details(st.session_state.place)
    st.session_state.messages = []
    restaurant_start_chat()
    

def restaurant_start_chat():
    """
    Preprocesses the response to be streamed, by yielding the response text 
        chunks as they are generated

    Parameters:
        query (str): the user query to the chatbot
    
    Returns:
        N/A 
    """
    st.session_state.model = load_model()
    st.session_state.chat = st.session_state.model.start_chat(
        history=[],
    )
    

def display_choices(recommendations):
    """
    Displays the recommendations of places based on the user 
        specifications, dynamically changing based on the number of 
        recommendations requested. The displayed information includes:
        - Name
        - Rating (and # of ratings)
        - Distance
        - Google Maps URI
        - Generative summary overview

    Parameters:
        recommendations (str): the recommendations that were returned 
    
    Returns:
        N/A 
    """
    cols = st.columns(len(recommendations))
    for i, col in enumerate(cols):
        with col:
            rec = recommendations[i]
            st.write(f"**{rec['displayName']['text']}**")
            st.write(
                f"Rating: {rec['rating']} ({rec['userRatingCount']} reviews)")
            distance = maps_func.get_distance(
                rec['name'], st.session_state.coordinates)
            st.write(f"Distance: {distance}")
            st.write("[Take Me to Google Maps](%s)" % rec['googleMapsUri'])
            if 'generativeSummary' in rec:
                st.write(
                    f"About: {rec['generativeSummary']['overview']['text']}")
            else:
                st.write(
                    "Haven't got a summary for this one. Must be good though!")
            st.button("Learn More", key=rec['name'], on_click=get_place, 
                      args=(rec['name'], rec['displayName']['text']))
    display_map(recommendations)


def display_map(recommendations):
    lat, lng = (st.session_state.coordinates['lat'], st.session_state.coordinates['lng'])
    # lat = st.session_state.coordinates['lat']
    m = folium.Map(location=[lat, lng], zoom_start=12)
    folium.Marker(
            [lat, lng], popup="Your Location", tooltip="Your Location", icon=folium.Icon(color='red')
    ).add_to(m)
    for rec in recommendations:
        rec_coords = maps_func.geocoder(rec['formattedAddress'])
        rec_name = rec['displayName']['text']
        folium.Marker(
            [rec_coords['lat'], rec_coords['lng']], popup=rec_name, tooltip=rec_name, icon=folium.Icon()
        ).add_to(m)

    # call to render Folium map in Streamlit
    return st_folium(m, width='100%')
    
    
def display_autocomplete_options(search_term):
    """
    Displays the suggestions for autocomplete based on user input

    Parameters:
        search_term: the user query to search for a place
    
    Returns:
        parsed_suggestions (list): a list of suggested places based on the 
        Places API Autocomplete functionality 
        OR
        None if there is no user query inputted
    """
    if search_term:
        suggestions = maps_func.autocomplete(search_term)["suggestions"]
        parsed_suggestions = []
        for suggestion in suggestions:
            display_name = suggestion['placePrediction']['text']['text']
            parsed_suggestions.append(display_name)
        return parsed_suggestions
    else:
        return None


def restaurant_qa(query):
    """
    Displays and handles the Q&A restaurant chatbot experience

    Parameters:
        query (str): the user query to the chatbot
    
    Returns:
        N/A
    """            
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response = get_llm_response(query)
    st.session_state.messages.append({"role": "assistant", "content": response})


# Initializing session state variables if they were not already initialized
if 'food_options' not in st.session_state:
    st.session_state.food_options = False
if 'place' not in st.session_state:
    st.session_state.place = False
    
    
# Rendering the headers of the website            
st.header("touchgrass", divider="rainbow")
st.subheader("Find Food")

# Display form for user input
with st.form("my-form"):
    query = st.text_input( # text input for main user query
        "What kind of food are you in the mood for? \n\n", 
        placeholder="e.g. sushi, tacos, burgers",
    )

    budget = st.radio( # radio button for user budget
        "What's your budget? \n\n",
        [
            "casual",
            "mid-range",
            "fine dining",
        ],
        key="budget",
    )

    num_recs = st.slider( # slider for number of recommendations to generate
        "How many recommendations are you looking for? \n\n",
        1, 5, 3,
        key="num_recs"
    )

    location = st.text_input( # optional text input for user to search 
        label = "Optional: where do you want to search around, " \
                "if not your current location? \n\n",
        placeholder="location to search around",
    )
    
    selections = []
    final_location = None
    if location: # if user filled out a specified location, autocomplete the addr
        selections = display_autocomplete_options(location)
        final_location = st.selectbox(
            label = "Options \n\n",
            placeholder="location to search around",
            options = selections,
        )
        
    submit_button = st.form_submit_button("Find my Food")

# if the user clicked submit without inputting what they wanted to search, 
# throw an error to prompt them to input something and stop execution
if submit_button and not query:
    st.error("Please specify what food you're craving!", icon="🚨")
    st.stop()

# happy path: user inputted their search and clicked submit
if submit_button and query:
    with st.spinner("Generating delicious matches ..."):
        # if a location is specified, use that instead of user's current location
        if final_location: 
            st.session_state.coordinates = maps_func.geocoder(final_location)
        # otherwise, process and use the user's current location
        elif initial_coordinates: 
            st.session_state.coordinates = {
                "lat": initial_coordinates['coords']['latitude'], 
                "lng": initial_coordinates['coords']['longitude']}
        # get food recommendations
        st.session_state.food_options = maps_func.text_search_new(
            query = query,
            budget = budget,
            num_recs = num_recs,
            coordinates = st.session_state.coordinates
        )

# if food recommendations were returned, display them
if st.session_state.food_options:
    st.subheader("Your matches:", divider='gray')
    display_choices(st.session_state.food_options) 
    
# if user clicked "Learn More" and additional information about the place was 
# retrieved, start chat session about the place 
if st.session_state.place:
    st.subheader(f"Chat about {st.session_state.place_name}", divider='gray')
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if st.session_state.messages == []:
        starter_prompt = f"""
        Give the user a friendly introduction to 
        {st.session_state.place_name}.\n
        Make sure to let them know they can ask you about the hours, price 
        range, or any other details.
        """
        with st.chat_message("assistant"):
            st.session_state.messages.append({
                "role": "assistant", "content": get_llm_response(starter_prompt)
                })
        
    # Accept user input
    if query := st.chat_input(
        f"Ask me anything about {st.session_state.place_name}", 
        key='user_chat'):
        restaurant_qa(query)