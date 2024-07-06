import streamlit_js_eval
import streamlit as st
import maps_functionalities
import google.generativeai as genai


genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
initial_coordinates = streamlit_js_eval.get_geolocation()


def load_model():
    """
    Load the generative models for text and multimodal generation.

    Returns:
        Tuple: A tuple containing the text model and multimodal model.
    """
    config = {
        "temperature": 0.7,
        "max_output_tokens": 2048,
    }
    system_instruction = f"""You are a helpful local guide who knows the best food in the area. \n
    You must answer questions about {st.session_state.place_name} as accurately as possible, given 
    the user query {query} and the following JSON of details: \n
    {st.session_state.place_details}
    """
    print(system_instruction)
    model_flash = genai.GenerativeModel(
        model_name = "gemini-1.5-flash",
        generation_config=config,
        # safety_settings=safety_settings,
        system_instruction=system_instruction,
        )
    return model_flash


def stream_data(query):
    stream = st.session_state.chat.send_message(query, stream=True)
    for part in stream:
        yield part.text
       
        
def get_llm_response(query):
    response = st.write_stream(stream_data(query))
    return response


def get_place(place_id, place_name):
    st.session_state.place = place_id
    st.session_state.place_name = place_name
    st.session_state.place_details = maps_functionalities.get_place_details(st.session_state.place)
    st.session_state.messages = []
    print(st.session_state.place_name)
    restaurant_start_chat()
    

def restaurant_start_chat():
    st.session_state.model = load_model()
    st.session_state.chat = st.session_state.model.start_chat(
        history=[],
    )
    
    print("STARTED CHAT")
    

def display_choices(responses):
    cols = st.columns(len(responses))
    for i, col in enumerate(cols):
        with col:
            response = responses[i]
            st.write(f"**{response['displayName']['text']}**")
            st.write(f"Rating: {response['rating']} ({response['userRatingCount']} reviews)")
            distance = maps_functionalities.get_distance(st.session_state.coordinates, response['name'])
            st.write(f"Distance: {distance}")
            st.write("[Take Me to Google Maps](%s)" % response['googleMapsUri'])
            if 'generativeSummary' in response:
                st.write(f"About: {response['generativeSummary']['overview']['text']}")
            else:
                st.write("Haven't got a summary for this one. Must be good though!")
            st.button("Learn More", key=response['name'], on_click=get_place, args=(response['name'], response['displayName']['text']))


def display_autocomplete_options(search_term):
    if search_term:
        suggestions = maps_functionalities.autocomplete(search_term)["suggestions"]
        parsed_suggestions = []
        for suggestion in suggestions:
            display_name = suggestion['placePrediction']['text']['text']
            parsed_suggestions.append(display_name)
        return parsed_suggestions
    else:
        return None


# input: json of restaurant details
def restaurant_qa(query):            
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response = get_llm_response(query)
    st.session_state.messages.append({"role": "assistant", "content": response})


if 'food_options' not in st.session_state:
    st.session_state.food_options = False
    
if 'place' not in st.session_state:
    st.session_state.place = False
    
            
st.header("touchgrass", divider="rainbow")

st.subheader("Find Food")


# Limitation: Within a form, the only widget that can have a callback function 
# is st.form_submit_button, which means I'm going the error route instead of simply
# disabling the button until the text field is filled out
# Limitation: custom module st_searchbox does not work within a streamlit form

with st.form("my-form"):
    query = st.text_input(
        "What kind of food are you in the mood for? \n\n", 
        placeholder="e.g. sushi, tacos, burgers",
    )

    budget = st.radio(
        "What's your budget? \n\n",
        [
            "casual",
            "mid-range",
            "fine dining",
        ],
        key="budget",
    )

    num_recs = st.slider(
        "How many recommendations are you looking for? \n\n",
        1, 5, 3,
        key="num_recs"
    )
    # Limitation: on_change for selectbox is only when you actually click on an 
    # option and it changes, not if you type in something. Used custom component instead

    location = st.text_input(
        label = "Optional: where do you want to search around, if not your current location? \n\n",
        placeholder="location to search around",
    )
    selections = []
    final_location = None
    if location:
        selections = display_autocomplete_options(location)
        final_location = st.selectbox(
            label = "Options \n\n",
            placeholder="location to search around",
            options = selections,
        )
    submit_button = st.form_submit_button("Find my Food")

        
if submit_button and not query:
    st.error("Please specify what food you're craving!", icon="🚨")
    st.stop()

if submit_button:
    with st.spinner("Generating delicious matches ..."):
        if final_location: # use the specified location instead of user's current location
            st.session_state.coordinates = maps_functionalities.geocoder(final_location)
            print(final_location)
        elif initial_coordinates: # process and use the user's current location
            st.session_state.coordinates = {"lat": initial_coordinates['coords']['latitude'], 
                            "lng": initial_coordinates['coords']['longitude']}
        st.session_state.food_options = maps_functionalities.text_search_new(
            query = query,
            budget = budget,
            num_recs = num_recs,
            coordinates = st.session_state.coordinates
        )
        
if st.session_state.food_options:
    st.subheader("Your matches:", divider='gray')
    display_choices(st.session_state.food_options) 
    
if st.session_state.place:
    st.subheader(f"Chat about {st.session_state.place_name}", divider='gray')
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if st.session_state.messages == []:
        starter_prompt = f"""Give the user a friendly introduction to {st.session_state.place_name}.\n
        Make sure to let them know they can ask you about the hours, price range, or any other details."""
        with st.chat_message("assistant"):
            st.session_state.messages.append({"role": "assistant", "content": get_llm_response(starter_prompt)})
        
    # Accept user input
    if query := st.chat_input(f"Ask me anything about {st.session_state.place_name}", key='user_chat'):
        restaurant_qa(query)
        