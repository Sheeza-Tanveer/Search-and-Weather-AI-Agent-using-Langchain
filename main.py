import os
import certifi
import requests

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langsmith import Client
from langchain.tools import tool

#load environment variables from .env file

#load environment variables from .env file

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
WEATHERSTACK_API_KEY= os.getenv("WEATHERSTACK_API_KEY")

search_tool = TavilySearchResults(max_results=3)

# custom tool

@tool
def get_weather_data(city: str) -> str:
    """
    Fetch current weather information for a city.
    """

    url = (
        f"https://api.weatherstack.com/current?"
        f"access_key={WEATHERSTACK_API_KEY}&query={city}"
    )

    response = requests.get(url)

    data = response.json()

    if "current" not in data:
        return f"Could not fetch weather data for {city}"

    return (
        f"City: {city}\n"
        f"Temperature: {data['current']['temperature']}°C\n"
        f"Weather: {data['current']['weather_descriptions'][0]}\n"
        f"Humidity: {data['current']['humidity']}%"
    )

#initialize the ChatGroq model with the specified parameters

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

response = llm.invoke("what year is it?")
response



client = Client()

prompt = client.pull_prompt("hwchase17/react")

tools = [search_tool, get_weather_data]

# create agent

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# agent executor

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True # we can see logs 
)



# run agent executor with a query

response = agent_executor.invoke({
    "input": (
        "Find the capital of Pakistan"
        "and then find it's weather."  
    )
})

print("\n=======================")
print("FINAL OUTPUT")
print(response["output"])






