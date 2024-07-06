# Introduction: 
I wanted to learn how to build a prototype of something that leveraged generative AI as well as gave me some exposure on how to work with external data sources, including how to call APIs and leverage API data.

This was my first time working with this “stack” (Streamlit, Vertex AI/Gemini API, and Google Maps/Places). I chose Streamlit for its perceived ease of displaying prototypes as webapps using a pythonic approach, Google Maps/Places due to my app’s functionality (the API also allows for $200 worth of API calls for free every month, which definitely doesn’t hurt), and Vertex AI/Gemini API for the intro offer I got of $300 in free credits to use in my first three months.

# Takeaways:
I ended up learning a lot more than expected about Streamlit and about various hurdles to implementing Vertex AI. I learned less than expected about prompt engineering/implementing generative AI chat, but I think that goes more to show how easy it is to prototype generative AI functionality using a foundational model, compared to learning everything else that is needed to build out the app. I’ve heard of two key challenges in building genAI apps; one is productionizing them, and the second is prioritizing usability of their interfaces.

# Features:
### Search for restaurants nearby based on user criteria/information:
- Location [Type: N/A or free text field]
  - Option 1: the user’s own location, which is automatically collected with permission
  - Option 2: an inputted address 
- What type of food they are looking for [Type: free text field]
- Price range [Type: radio button]
- Number of recommendations to generate [Type: slider]
  
### View restaurant(s) information:
- Name
- Rating
- Number of ratings
   Distance
- Google Maps URI
- About (generative summary)
  
### Chat about a specific restaurant by clicking “Learn More”:
- Can ask about information that is not displayed in the basic information above, such as hours open
- Can ask about more niche information, such as whether a place is good for kids/dogs
- Chat responses generated with Gemini 1.5 Flash
- Can switch chat context anytime by clicking on a different restaurant’s “Learn More”
  
# Future improvements:
Incorporating function calling for enhanced accuracy
Adding a maps widget for improved visualization of locations
Adding functionality for displaying locations along a route

# Lessons Learned and Challenges:
## OAuth 2.0
Initially, I used VertexAI instead of the Gemini API to call Gemini 1.5 Flash, since the former was touted as more production ready and I wanted to learn how to get that type of workflow setup within the VertexAI environment instead of directly calling the API. 

The first hurdle was figuring out how to set up OAuth 2.0—I first tried to do it with GitHub Codespaces as my IDE (because I wanted to use my new iPad to code) but as I was just starting out and learning the ropes, I was bumping up against confusing errors and limited documentation for this particular combination of Codespaces + VertexAI, and it was easier to configure just with my local environment (I may be able to figure it out now with what I’ve learned in the last week and a half, but for other reasons I’m no longer using Vertex AI and wouldn’t run up against this problem with my current codebase anyway).

The second OAuth issue that threw me for a loop a week into building: I was adding a new feature and debugging when I suddenly started getting a RefreshError 'invalid_grant: Token has been expired or revoked.' I thought for a second that somehow I got blacklisted by Vertex AI, but then started getting suspicious about how this was almost exactly a week since I got started and set up my project. Going down a rabbit hole, I found the following reason for the error: If a Google Cloud Platform project has an OAuth consent screen configured for an external user type and a publishing status of "Testing" is issued a refresh token, it expires in 7 days. Obviously I didn’t want to move my prototype to production, so to mitigate this at least temporarily, I deleted the token_places_v1.json under /token_files to re-authenticate myself for another week (reached this conclusion by extrapolating from this StackOverflow post and it worked). This was obviously a temporary solution, and one that started making me realize that if I wanted to just build a prototype and leave it be, maybe Vertex AI wouldn’t be the best match for this stack.

The third hump was after I deployed to Streamlit Community Cloud, where I was simply not able to authenticate myself with OAuth 2.0 over Streamlit Cloud. The process for local environment setup for OAuth 2.0 involved running a CLI (command line interface) command to get a JSON file for my Application Default Credentials. I would then get the path to this file (which is now stored in my local directory) and store it in an environment variable GOOGLE_APPLICATION_CREDENTIALS. However, this is a secret file that I would not want to commit to Github, and I was aware that I could try and leverage Streamlit Secrets for deployment on Streamlit—but the issue there was how to set my environment variable, since I could set my Streamlit secret as the value of my credentials, but I would actually need a path to somewhere accessible by Streamlit. I tried the following:
- Uploading my application_default_credentials.json to a Google Cloud Storage Bucket and trying to get either an authorized or signed url to it to pass as a “path”
  - This involved creating a GCP service account in order to authorize myself to the bucket
- Figuring out a way to use anything but an environment variable to authorize myself
  - This is a bit more fuzzy to me. I’ve found nothing in terms of documentation specifically for the Vertex AI use case with Streamlit, and looked through the troubleshooting guide to find out if there was a use case/environment I could extrapolate to me using Streamlit, but wasn’t able to pick up on anything. I have seen ways for the end user to authenticate themselves—but I’m the only one who needs to authenticate so they can bill me 😂

In the end, I decided to go for the more direct Gemini API route and switched out my Vertex AI implementation (sayonara vertexai.init(project=PROJECT_ID, location=LOCATION), hello genai.configure(api_key=st.secrets["GOOGLE_API_KEY"]))—I have to say, while I still want to figure out Vertex AI, the Gemini API is much more straightforward compared to everything I did with Vertex previously.

## Streamlit
Streamlit is great for starting out and getting an interactive interface without needing to build everything out with HTML/CSS/Javascript or a  (I did build my own website from scratch but I am not particularly a fan of frontend development, and a pythonic approach sounded amazing to me). While exploring what Streamlit could do, I learned a lot about how to use Streamlit’s callbacks (e.g. calling a function to start a chat when a button is clicked) and session state to store and persist state between reruns (which includes anytime a user interacts with a page).

However, I ran up against some limitations of what I could do in terms of customizability and functionality as I got deeper into development. I had to do at least one semi-strange workaround to make sure everything would still work properly, while trying to minimize the hit to usability as much as possible. I want to point out some specific items of note, both for Streamlit on its own and the Streamlit-Gemini API-Google Maps combos.

### Streamlit-only

#### Text input 
The main issue I had with the text_input field was that it always displays a “Press Enter to Apply” (or “Press Enter to Submit Form” if it’s located with a form) when you start typing in the textbox. I put all my user input fields in a form to make it less confusing to the user, but I would still prefer them to always use the Submit button I provide instead of pressing Enter, since the text_input is all the way at the top of the form and should not be the form field that triggers an entire form submission.

#### Limited Callback Functionality in Forms:
I wanted to implement a callback function for a text_input widget that would disable the form’s Submit button until the text input field is filled out, but within a form, the only widget that can have a callback function is the st.form_submit_button widget itself. This means I ended up displaying an error if the user decided to click the Submit button without filling out the text field, which in my opinion is a messier option than simply disabling the button until all fields are completed.

In a similar vein, the custom module st_searchbox mentioned below simply did not work within a forms widget, since it contained a callback function.

#### Dynamic Search/Autocomplete Display:
One of my features involves a dynamic search autocomplete for address suggestions, similar to how Google autocompletes addresses inputted into its own search field. However, Streamlit doesn't have its own searchable text field. The st.text_input autocomplete parameter is related to autocompleting passwords, and st.selectbox does not have a parameter that accepts a callback to generate results when the user is typing something in. st.selectbox does have an on_change parameter, but that’s for when the user actually clicks on a choice—and the address choices for my use case need to be dynamically generated based on user inputs and change every time there’s a new character entered/deleted.

I tried using st_searchbox, a custom Streamlit component, but it had erratic behavior as follows:
- I search for an address and select the address option I want
- I start the chat (and the page then scrolled down, which I assume refreshed the page components)
- The search field looks like it clears and the option to clear it disappears, but the actual address that I had previously selected is still stored in the session
- As Streamlit seems to automatically refresh the page whenever it needs to scroll down, and I haven’t found any documentation on how I can detect this, I am unable to fully control when the stored variable is cleared on the backend.

<p align="center">
  <img src="https://github.com/anke-hao/touchgrass/blob/main/streamlit_st_searchbox_bug.gif"/>
</p>

This search field is optional, which means the user could potentially want to actually clear it but would have no way of doing so if the ‘x’ option to clear it disappears from the frontend.

Eventually, I made a workaround with a combination of a st.text_input widget and a st.selectbox widget, where I first type in anything in the text input field and then pick from a list of generated selections from the selectbox. This decision was also made when evaluating the benefits of still keeping everything in form versus a bunch of separated widgets (as mentioned above, st_searchbox does not work in a form).

### Streamlit and Gemini API

#### Chat streaming
I ended up using a combination of the LLM chat app tutorial in Streamlit Docs and Gemini API documentation (overview and in-depth versions). The Streamlit docs use OpenAI 's API, and the main difference that I needed to take into account was a difference in how the streaming was handled. There was no preprocessing needed for using OpenAI().chat.completions.create with stream=True, but I needed to build out a basic preprocessing function for Gemini’s streaming and figure out how to hook that up with Streamlit’s st.write_stream(). 

### Streamlit and Google Maps (Geolocation) API

A final challenge came as I deployed to Streamlit Community Cloud and it seemed like my maps functionality was not working at all. I eventually pinpointed it as the geolocation functionality, and found out (which does seem obvious in hindsight) that you can’t accurately get user IP addresses from Streamlit-hosted websites; instead, it is the IP address of whichever machine that particular instance is running on, which is neither accurate nor stable. I used a custom module that directly uses JS to geolocate the user after asking for permission in the browser.

### Places API
While the original Places API had more documentation and examples, the documentation for how to implement the new Places API with python was very sparse.

The sample code in the Python client library provided in the documentation had bugs in them, e.g. calling variables directly that were actually nested attributes. Their code snippets were also prefaced by comments like “This snippet has been automatically generated and should be regarded as a code template only,” which was confusing to me—were they generated by Gemini? I ended up working out how to use POST and GET requests directly instead. 


## V1 

### Demo:
https://youtu.be/PpdN8AWONwA

### Features:
- Basic Streamlit front-end
- Gemini results generation

### Lessons learned:
- Streamlit generally easy to work with
- Google authentication does not have established best practices with Github Codespaces, and still involved some setup on local

## V2

### Demo:
https://youtu.be/Rflkb8SAG3c

### Features:
- Geolocation
- Places (new) API functionality
  - text search
  - place details
- chatbot functionality with Gemini 1.5 Flash

### Lessons learned:
- Google Places (new) documentation of the Python client library is poor and has bugs, ended up using a combination of a Youtube tutorial's code + get requests
- Once you get more in the weeds with Streamlit, you run up against limitations in customizability (e.g. carousel, button behavior)
- If your Google Cloud Platform project has an OAuth consent screen configured for an external user type and a publishing status of "Testing" is issued a refresh token, it expires in 7 days and you will get a RefreshError 'invalid_grant: Token has been expired or revoked.' To mitigate this at least temporarily, delete the token_places_v1.json under /token_files to reauthenticate yourself for another week.
  - Reference: https://stackoverflow.com/questions/71994891/access-google-api-using-python-refresh-error-invalid-grant-appears-suddenly-a
