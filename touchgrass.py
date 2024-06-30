import os
import requests
import streamlit as st
import vertexai
import json
import maps_functionalities
from google.maps import places_v1
from openai import OpenAI
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

credential_path = r'C:\Users\anke_\AppData\Roaming\gcloud\application_default_credentials.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

# PROJECT_ID = "celtic-list-427003-c7"  # Your Google Cloud Project ID
PROJECT_ID = "rosy-hangout-424004-f7"  # Your Google Cloud Project ID
LOCATION = "us-central1"  # Your Google Cloud Project Region
vertexai.init(project=PROJECT_ID, location=LOCATION)


@st.cache_resource
def load_models():
    """
    Load the generative models for text and multimodal generation.

    Returns:
        Tuple: A tuple containing the text model and multimodal model.
    """
    model_flash = GenerativeModel("gemini-1.5-flash")
    return model_flash


# # Process and store Query and Response
def llm_function(model: GenerativeModel,
    prompt: str,
    generation_config: GenerationConfig,
    stream: bool = True,
):
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    
    responses = model.generate_content(
    prompt,
    generation_config=generation_config,
    safety_settings=safety_settings,
    stream=stream,
    )

    final_response = []
    for response in responses:
        try:
            st.markdown(response.text)
            final_response.append(response.text)
        except IndexError:
            final_response.append("")
            continue
    return " ".join(final_response)



#  may or may not use this
def construct_query(cuisine, vibe):
    return f'{vibe} {cuisine}' + ('restaurant' if cuisine != "cafe" else '')
    

def get_place(place_id, place_name):
    st.session_state.place = place_id
    st.session_state.place_name = place_name
    st.session_state.place_details = maps_functionalities.places_hub('place_details', st.session_state.place, 0, 0)
    if 'messages' in st.session_state:
        del st.session_state['messages']
    print(st.session_state.place)
    print(st.session_state)

    
def display_choices(responses):
    cols = st.columns(len(responses))
    for i, col in enumerate(cols):
        with col:
            response = responses[i]
            st.write(f"**{response['displayName']['text']}**")
            st.write(f"Rating: {response['rating']} ({response['userRatingCount']} reviews)")
            if 'generativeSummary' in response:
                st.write(f"About: {response['generativeSummary']['overview']['text']}")
            else:
                st.write("Haven't got a summary for this one. Must be good though!")
            st.button("Learn More", key=response['name'], on_click=get_place, args=(response['name'], response['displayName']['text']))


# input: json of restaurant details
def restaurant_qa(query):
    # food_details = maps_functionalities.places_hub('place_details', st.session_state.place, 0, 0)
    prompt = f"""You are a helpful local guide who knows the best food in the area. \n
    You must answer questions about {st.session_state.place_name} as accurately as possible, given 
    the user query {query} and the following JSON of details: {st.session_state.place_details}
    """
    config = {
        "temperature": 0.8,
        "max_output_tokens": 2048,
    }
    model_flash = load_models()
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": prompt}]
            
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response = llm_function(
                    model_flash,
                    prompt,
                    generation_config=config,
                )
    
    st.session_state.messages.append({"role": "assistant", "content": response})


if 'food_options' not in st.session_state:
    st.session_state.food_options = False
    
if 'place' not in st.session_state:
    st.session_state.place = False
    
            
st.header("touchgrass", divider="rainbow")

st.subheader("Find Food")

query = st.text_input(
    "What kind of food are you in the mood for? \n\n", value="japanese"
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



generate_t2t = st.button("Find my Food", key="generate_t2t")
if generate_t2t:
    with st.spinner("Generating delicious matches ..."):
        st.session_state.food_options = maps_functionalities.places_hub(
            places_type = 'text_search', 
            query = query,
            budget = budget,
            num_recs = num_recs
        )
if st.session_state.food_options:
    st.header("Your matches:")
    display_choices(st.session_state.food_options) 
    
if st.session_state.place:
    # Accept user input
    if query := st.chat_input(f"Ask me anything about {st.session_state.place_name}", key='user_chat'):
        restaurant_qa(query)
        