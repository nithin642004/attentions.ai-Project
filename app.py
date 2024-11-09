import streamlit as st
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from neo4j import GraphDatabase

# --- Neo4j Setup ---
class MemoryAgent:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def store_preferences(self, user_id, preferences):
        with self.driver.session() as session:
            session.run("MERGE (u:User {id: $user_id}) SET u.preferences = $preferences", 
                        user_id=user_id, preferences=preferences)

    def get_preferences(self, user_id):
        with self.driver.session() as session:
            result = session.run("MATCH (u:User {id: $user_id}) RETURN u.preferences AS preferences", 
                                 user_id=user_id)
            return result.single()["preferences"] if result.single() else None

# --- FastAPI Backend ---
app = FastAPI()

class UserRequest(BaseModel):
    name: str
    city: str
    budget: int
    interests: list

@app.post("/generate-itinerary/")
async def generate_itinerary(request: UserRequest):
    # Placeholder for calling an LLM or itinerary generation logic
    response = f"Generated itinerary for {request.city} with interests {request.interests}"
    return {"itinerary": response}

# --- Streamlit Frontend ---
# Initialize Memory Agent
memory_agent = MemoryAgent("bolt://localhost:7687", "neo4j", "password")

def main():
    st.title("One-Day Tour Planning Assistant")

    # User login and authentication
    if 'user_id' not in st.session_state:
        user_name = st.text_input("Enter your name to log in:")
        if user_name:
            st.session_state['user_id'] = user_name.lower()
            st.write(f"Welcome, {user_name}!")
    else:
        st.write(f"Logged in as: {st.session_state['user_id']}")

    # Chat-style interaction
    st.subheader("Plan Your Itinerary")
    city = st.text_input("Which city are you visiting?")
    budget = st.number_input("Enter your budget ($)", min_value=0)
    interests = st.multiselect("Choose your interests", ["Culture", "Adventure", "Food", "Shopping"])

    # Display previous preferences if available
    if st.button("Retrieve Previous Preferences"):
        previous_prefs = memory_agent.get_preferences(st.session_state['user_id'])
        if previous_prefs:
            st.write(f"Your saved preferences: {previous_prefs}")
        else:
            st.write("No previous preferences found.")

    # Submit and store user preferences
    if st.button("Submit Preferences"):
        user_data = {
            'name': st.session_state['user_id'], 'city': city, 'budget': budget, 'interests': interests
        }
        memory_agent.store_preferences(st.session_state['user_id'], user_data)
        st.write("Preferences saved!")

        # Generate itinerary (placeholder for actual LLM API call)
        st.write("Generating itinerary...")
        itinerary = f"Generated itinerary for {city} with budget {budget} and interests {interests}"
        st.write(itinerary)

    # Display chat history for the user
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    user_message = st.text_input("Type your message:")
    if st.button("Send") and user_message:
        st.session_state['chat_history'].append(f"User: {user_message}")
        response_message = f"System: Generating response for '{user_message}'..."  # Placeholder for response
        st.session_state['chat_history'].append(response_message)

    for chat in st.session_state['chat_history']:
        st.write(chat)

    # Close Neo4j connection on app closure
    if st.button("Close App"):
        memory_agent.close()
        st.write("Memory agent connection closed.")

if __name__ == "__main__":
    main()

# --- Weather Functionality ---
def get_weather(city):
    api_key = 'your_api_key'  # Replace with your API key
    url = f"http://api.weatherapi.com/v1/forecast.json?q={city}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch weather information.")
        return None

# Display weather information
if 'city' in st.session_state:
    weather_info = get_weather(st.session_state['city'])
    if weather_info:
        forecast = weather_info['forecast']['forecastday'][0]['day']
        st.write(f"Weather for {st.session_state['city']}: {forecast['condition']['text']}, "
                 f"Temperature: {forecast['avgtemp_c']}°C")
