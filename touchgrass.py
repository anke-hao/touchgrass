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
            # print(response)
            final_response.append(response.text)
        except IndexError:
            # st.write(response)
            final_response.append("")
            continue
    return " ".join(final_response)



#  may or may not use this
def construct_query(cuisine, vibe):
    return f'{vibe} {cuisine}' + ('restaurant' if cuisine != "cafe" else '')
    

def get_place(place_id, place_name):
    st.session_state.place = place_id
    st.session_state.place_name = place_name
    print(st.session_state.place)

    
def display_choices(responses):
    cols = st.columns(len(responses))
    # buttons = []
    for i, col in enumerate(cols):
        with col:
            response = responses[i]
            st.write(f"**{response['displayName']['text']}**")
            # st.divider()
            st.write(f"Rating: {response['rating']} ({response['userRatingCount']} reviews)")
            # st.write(f"Number of Reviews: {response['userRatingCount']}")
            if 'generativeSummary' in response:
                st.write(f"About: {response['generativeSummary']['overview']['text']}")
            else:
                st.write("Haven't got a summary for this one. Must be good though!")
            # print("HEREEEEEEEEEE")
            # print(response['id'])
            st.button("Learn More", key=response['name'], on_click=get_place, args=(response['name'], response['displayName']['text']))
            # buttons.append(st.button("Learn More", key=response['displayName']['text']))
            # if stateful_button("Learn More", key=response['name']):
            #     get_place(response['name'])

# input: json of restaurant details
def restaurant_qa(query):
    food_details = maps_functionalities.places_hub('place_details', st.session_state.place, 0, 0)
    place_name = food_details['displayName']['text']
    prompt = f"""You are a helpful local guide who knows the best food in the area. \n
    You must answer questions about {place_name} as accurately as possible, given 
    the user query {query} and the following JSON of details: {food_details}
    """
    config = {
        "temperature": 0.8,
        "max_output_tokens": 2048,
    }
    model_flash = load_models()
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": prompt}]
        # st.session_state.messages.append({
        #         "role":"assistant",
        #         "content":f"Ask me anything about {food_details['displayName']['text']}"
        #     }
        # )
        # for message in st.session_state.messages:
        #     if message["role"] != 'system':
        #         with st.chat_message(message["role"]):
        #             st.markdown(message["content"])
    # if query := st.chat_input(f"Ask me anything about ", key='user_chat'):                
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        response = llm_function(
                    model_flash,
                    prompt,
                    generation_config=config,
                )
        # st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    # response = model.generate_content(prompt)
    # # Displaying the Assistant Message
    # with st.chat_message("assistant"):
    #     st.markdown(response.text)

    # # Storing the User Message
    # st.session_state.messages.append(
    #     {
    #         "role":"user",
    #         "content": query
    #     }
    # )

    # # Storing the User Message
    # st.session_state.messages.append(
    #     {
    #         "role":"assistant",
    #         "content": response.text
    #     }
    # )


if 'responses' not in st.session_state:
    st.session_state.responses = False
    
if 'place' not in st.session_state:
    st.session_state.place = False
    
            
st.header("touchgrass", divider="rainbow")
# tab1, tab2 = st.tabs(
#     ["Find Food", "Chat about a Place"]
# )

# with tab1:
    # st.write("Using Gemini 1.5 Flash")
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
    # st.write(prompt)
    with st.spinner("Generating delicious matches ..."):
        # search, chat = st.tabs(["Search", "Chat"])
        # with search:
            # response = get_gemini_pro_text_response(
            #     text_model_pro,
            #     prompt,
            #     generation_config=config,
            # )
        st.session_state.responses = maps_functionalities.places_hub(
            places_type = 'text_search', 
            query = query,
            budget = budget,
            num_recs = num_recs
        )
if st.session_state.responses:
    st.header("Your matches:")
    display_choices(st.session_state.responses) 
    
if st.session_state.place:
    # model = GenerativeModel("gemini-1.5-flash")
    # food_details = maps_functionalities.places_hub('place_details', st.session_state.place, 0, 0)
    # if "messages" not in st.session_state:
    #     st.session_state.messages = [
    #         {
    #             "role":"assistant",
    #             "content":f"Ask me anything about {food_details['displayName']['text']}"
    #         }
    #     ]
    #     for message in st.session_state.messages:
    #         if message["role"] != 'system':
    #             with st.chat_message(message["role"]):
    #                 st.markdown(message["content"])

    # Display chat messages from history on app rerun
    # Accept user input
    if query := st.chat_input(f"Ask me anything about {st.session_state.place_name}", key='user_chat'):
        restaurant_qa(query)
        # st.session_state.messages.append({"role": "user", "content": prompt})
        # with st.chat_message("user"):
        #     st.markdown(prompt)

        # with st.chat_message("assistant"):
        #     response = model.generate_content(prompt)
        #     st.markdown(response.text)
        
        # st.session_state.messages.append({"role": "assistant", "content": response})
        
               
# with tab2:
#     # client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
#     # if "openai_model" not in st.session_state:
#     #     st.session_state["openai_model"] = "gpt-4o"
#     model = GenerativeModel("gemini-1.5-flash")
#     if "messages" not in st.session_state:
#         st.session_state.messages = [
#             {
#                 "role":"assistant",
#                 "content":"Ask me Anything"
#             }
#         ]

#     # Display chat messages from history on app rerun
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])
#     # Accept user input
#     if prompt := st.chat_input("What is up?"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             # stream = client.chat.completions.create(
#             #     model=st.session_state["openai_model"],
#             #     messages=[
#             #         {"role": m["role"], "content": m["content"]}
#             #         for m in st.session_state.messages
#             #     ],
#             #     stream=True,
#             # )
#             # response = st.write_stream(stream)
#             response = model.generate_content(prompt)
#             st.markdown(response.text)
        
#         st.session_state.messages.append({"role": "assistant", "content": response})