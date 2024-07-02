import os
import datetime
import streamlit_js_eval
import streamlit as st
from st_files_connection import FilesConnection
import vertexai
# import json
import maps_functionalities
# from google.maps import places_v1
# from openai import OpenAI
from vertexai.generative_models import (
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
)
import google.generativeai as genai

from google.oauth2 import service_account
from google.cloud import storage


# url = generate_signed_url_v4(bucket_name, blob_name)
# conn = st.connection('gcs', type=FilesConnection)
# credential_path = r'C:\Users\anke_\AppData\Roaming\gcloud\application_default_credentials.json'
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = st.secrets["application_default_credentials"]


# PROJECT_ID = "celtic-list-427003-c7"  # Your Google Cloud Project ID
PROJECT_ID = "rosy-hangout-424004-f7"  # Your Google Cloud Project ID
LOCATION = "us-central1"  # Your Google Cloud Project Region
# fs = gcsfs.GCSFileSystem(project=PROJECT_ID)
# fs.ls(bucket_name)

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# vertexai.init(project=PROJECT_ID, location=LOCATION)

coordinates = streamlit_js_eval.get_geolocation()
print(coordinates)

# @st.cache_resource
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
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
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
    # st.session_state.place_details = maps_functionalities.places_hub('place_details', st.session_state.place, 0, 0)
    st.session_state.place_details = maps_functionalities.get_place_details(st.session_state.place)
    st.session_state.messages = []
    print(st.session_state.place_name)
    restaurant_start_chat()
    

def restaurant_start_chat():
    st.session_state.model = load_model()
    # print(type(st.session_state.messages))
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
            if 'generativeSummary' in response:
                st.write(f"About: {response['generativeSummary']['overview']['text']}")
            else:
                st.write("Haven't got a summary for this one. Must be good though!")
            st.button("Learn More", key=response['name'], on_click=get_place, args=(response['name'], response['displayName']['text']))


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
with st.form("my-form"):
    query = st.text_input(
        "What kind of food are you in the mood for? \n\n", placeholder="e.g. sushi, tacos, burgers"
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
    submit_button = st.form_submit_button("Find my Food")
    
if submit_button:
    with st.spinner("Generating delicious matches ..."):
        st.session_state.food_options = maps_functionalities.text_search_new(
            query = query,
            budget = budget,
            num_recs = num_recs,
            coordinates = coordinates
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
        