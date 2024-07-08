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
- Incorporating function calling for enhanced accuracy
- Adding a maps widget for improved visualization of locations
- Adding functionality for displaying locations along a route

# Lessons Learned and Challenges:
Linked [here](https://docs.google.com/document/d/1trnOI8a_BXjLVzR5KyACOk1MHnrXKgk9a5vRRSIWOwE/edit?usp=sharing).

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
