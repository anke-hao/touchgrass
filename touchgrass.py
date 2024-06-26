import os
import requests
import streamlit as st
import vertexai
import json
import maps_functionalities
from google.maps import places_v1
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
    text_model_pro = GenerativeModel("gemini-1.5-flash")
    multimodal_model_pro = GenerativeModel("gemini-1.5-flash")
    return text_model_pro, multimodal_model_pro


def get_gemini_pro_text_response(
    model: GenerativeModel,
    contents: str,
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
            # st.write(response.text)
            final_response.append(response.text)
        except IndexError:
            # st.write(response)
            final_response.append("")
            continue
    return " ".join(final_response)


def get_gemini_pro_vision_response(
    model, prompt_list, generation_config={}, stream: bool = True
):
    generation_config = {"temperature": 0.1, "max_output_tokens": 2048}
    responses = model.generate_content(
        prompt_list, generation_config=generation_config, stream=stream
    )
    final_response = []
    for response in responses:
        try:
            final_response.append(response.text)
        except IndexError:
            pass
    return "".join(final_response)

#  may or may not use this
def construct_query(cuisine, vibe):
    return f'{vibe} {cuisine}' + ('restaurant' if cuisine != "cafe" else '')
    
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
        
def display_choices(responses):
    for response in responses:
        st.write(f"Place: {response['displayName']['text']}")
        st.write(f"Rating: {response['rating']}")
        st.write(f"Number of Reviews: {response['userRatingCount']}")
        if 'generativeSummary' in response:
            st.write(f"About: {response['generativeSummary']['overview']['text']}")
        else:
            st.write("Haven't got a summary for this one. Must be good though!")
    
st.header("touchgrass", divider="rainbow")
text_model_pro, multimodal_model_pro = load_models()

tab1, tab2, tab3 = st.tabs(
    ["Find Food", "Go Sightseeing", "Find Events"]
)

with tab1:
    # st.write("Using Gemini 1.5 Flash")
    st.subheader("Find Food")

    # This will get replaced with get location
    # location = st.text_input(
    #     "What city are you in? \n\n", key="location", value="sf"
    # )
    query = st.text_input(
        "What kind of food are you in the mood for? \n\n", key="user_query", value="japanese"
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
    # vibe = st.radio(
    #     "What kind of vibe are you looking for? \n\n",
    #     [
    #         "trendy",
    #         "lively",
    #         "romantic",
    #         "casual",
    #     ],
    #     key="vibe",
    #     default=["trendy"],
    # )
    num_recs = st.slider(
        "How many recommendations are you looking for? \n\n",
        1, 5, 3,
        key="num_recs"
    )

    prompt = f"""You are a helpful local guide who knows the best restaurants in the area. \n
    Your goal is to recommend great restaurants based on the requirements of the user. \n
    cuisine: {query} \n
    budget: {budget} \n
    how many recommendations: {num_recs}
    """
    config = {
        "temperature": 0.8,
        "max_output_tokens": 2048,
    }

    generate_t2t = st.button("Find my Food", key="generate_t2t")
    if generate_t2t and prompt:
        # st.write(prompt)
        with st.spinner("Generating delicious matches ..."):
            # first_tab1, first_tab2 = st.tabs(["Matches", "Prompt"])
            # with first_tab1:
                # response = get_gemini_pro_text_response(
                #     text_model_pro,
                #     prompt,
                #     generation_config=config,
                # )
            responses = maps_functionalities.places_hub(
                places_type = 'text_search', 
                query = query,
                budget = budget,
                num_recs = num_recs
            )
            if responses:
                st.write("Your matches:")
                display_choices(responses)
            # with first_tab2:
            #     st.text(prompt)