"""
Custom tools implementation for RAG using LangChain
"""

from typing import List, Optional, Any
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
import requests
from bs4 import BeautifulSoup
import json

class WebSearchTool(BaseTool):
    """Tool for web search using DuckDuckGo"""
    name: str = "web_search"
    description: str = "Useful for searching current information on the web. Use it when you need recent or updated information."
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        search = DuckDuckGoSearchRun()
        return search.run(query)

class WikipediaTool(BaseTool):
    """Tool for searching Wikipedia"""
    name: str = "wikipedia"
    description: str = "Useful for searching information on Wikipedia. Use it when you need factual or historical information."
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wikipedia.run(query)

class WeatherTool(BaseTool):
    """Tool for getting current weather"""
    name: str = "weather"
    description: str = "Useful for getting current weather information. Requires a specific location."
    
    def _run(self, location: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        # Note: In a real implementation, you should use a weather API like OpenWeatherMap
        # This is a simplified example
        try:
            response = requests.get(f"https://wttr.in/{location}?format=%l:+%c+%t")
            return response.text
        except Exception as e:
            return f"Error getting weather: {str(e)}"

class NewsTool(BaseTool):
    """Tool for getting recent news"""
    name: str = "news"
    description: str = "Useful for getting recent news about a specific topic."
    
    def _run(self, topic: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            search = DuckDuckGoSearchRun()
            results = search.run(f"recent news about {topic}")
            return results
        except Exception as e:
            return f"Error getting news: {str(e)}"

def get_tools() -> List[BaseTool]:
    """Returns a list of all available tools"""
    return [
        WebSearchTool(),
        WikipediaTool(),
        WeatherTool(),
        NewsTool()
    ] 