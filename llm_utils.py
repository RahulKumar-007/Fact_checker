import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.tools import Tool

# Load environment variables when this module is imported
# Ensures API keys are available for functions in this module
# load_dotenv() # It's better to call load_dotenv() in entry point scripts (app.py, main_cli.py)

def init_llm():
    """Initializes and returns the Gemini LLM."""
    # Ensure .env is loaded by the calling script (app.py or main_cli.py)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Did you create a .env file and load it?")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    return llm

def init_search_tool():
    """Initializes and returns the DuckDuckGo search tool."""
    search = DuckDuckGoSearchAPIWrapper()
    search_tool = Tool(
        name="Web Search",
        description="Useful for searching the web for current information",
        func=search.run
    )
    return search_tool