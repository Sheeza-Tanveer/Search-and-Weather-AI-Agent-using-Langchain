import os
import certifi
import requests
import streamlit as st

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import tool
from langsmith import Client


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Agentic AI Assistant",
    page_icon=None,
    layout="centered"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")


# ============================================================
# CHECK API KEYS
# ============================================================

missing_keys = []

if not GOOGLE_API_KEY:
    missing_keys.append("GOOGLE_API_KEY")

if not TAVILY_API_KEY:
    missing_keys.append("TAVILY_API_KEY")

if not WEATHERSTACK_API_KEY:
    missing_keys.append("WEATHERSTACK_API_KEY")


# ============================================================
# PAGE TITLE
# ============================================================

st.title("Agentic AI Assistant")

st.write(
    "Ask me questions that require web search or weather information."
)


# ============================================================
# STOP IF API KEYS ARE MISSING
# ============================================================

if missing_keys:

    st.error(
        "The following API keys are missing from your `.env` file:"
    )

    for key in missing_keys:
        st.code(key)

    st.info(
        "Create a `.env` file in the same folder as this app and add your API keys."
    )

    st.stop()


# ============================================================
# WEATHER TOOL
# ============================================================

@tool
def get_weather_data(city: str) -> str:
    """
    Fetch current weather information for a city.
    """

    url = (
        "https://api.weatherstack.com/current"
        f"?access_key={WEATHERSTACK_API_KEY}"
        f"&query={city}"
    )

    try:

        response = requests.get(url, timeout=10)

        data = response.json()

        if "current" not in data:
            return f"Could not fetch weather data for {city}."

        return (
            f"City: {city}\n"
            f"Temperature: {data['current']['temperature']}°C\n"
            f"Weather: {data['current']['weather_descriptions'][0]}\n"
            f"Humidity: {data['current']['humidity']}%"
        )

    except Exception as e:

        return f"Error fetching weather data: {str(e)}"


# ============================================================
# INITIALIZE MODEL
# ============================================================

@st.cache_resource
def initialize_agent():

    search_tool = TavilySearchResults(
        max_results=3
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=GOOGLE_API_KEY
    )

    client = Client()

    prompt = client.pull_prompt(
        "hwchase17/react"
    )

    tools = [
        search_tool,
        get_weather_data
    ]

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )

    return agent_executor


# ============================================================
# INITIALIZE AGENT
# ============================================================

try:

    agent_executor = initialize_agent()

except Exception as e:

    st.error(
        f"Failed to initialize the AI agent:\n\n{str(e)}"
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Settings")

    st.write("### Available Tools")

    st.success("Tavily Web Search")

    st.success("Weatherstack Weather")

    st.success("Gemini AI")

    st.divider()

    st.write("### Example Questions")

    st.write(
        """
        • Find the capital of Pakistan and its weather.

        • What is the weather in Islamabad?

        • Search for the latest AI news.

        • What is the capital of Japan?

        • Find information about LangChain.
        """
    )

    st.divider()

    if st.button(
        "Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# DISPLAY PREVIOUS MESSAGES
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask your AI agent something..."
)


# ============================================================
# PROCESS USER QUERY


if user_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):

        st.markdown(user_input)

    with st.chat_message("assistant"):

        with st.spinner(
            "Agent is thinking..."
        ):

            try:

                response = agent_executor.invoke(
                    {
                        "input": user_input
                    }
                )

                answer = response["output"]

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except Exception as e:

                error_message = (
                    f"Something went wrong:\n\n"
                    f"{str(e)}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message
                    }
                )

