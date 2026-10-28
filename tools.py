import os 
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient
from rich import print
import requests
from bs4 import BeautifulSoup

load_dotenv()   
tavily=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

## --- it is a tool used for search the information/news from website and 
## geting the urls and titles snippets
def search_direct(query: str, n: int = 4):
    res = tavily.search(query=query, max_results=n)
    return res["results"]
def scrape_direct(url: str, limit: int = 4000) -> str:
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:limit]
    except Exception as e:
        return f"could not scrape from {e}"




## langchain tools
@tool
def web_search(query: str)  ->str :
    """search for recent and reliable news on topic . returns titles,URL's, snippets""" 
    results=tavily.search(query=query,max_results=5)
    out=[]
    for r in results['results']:
        out.append(
            f"Title: {r['title']}\n URL: {r['url']}\n Snippet: {r['content'][:300]}\n"
        )
    return "\n-----\n".join(out)


## webscraping tool using beautiful soup 
## getting the information using urls


def scrap_url(url :str) ->str:

    """to get the information from website urls with clean and for deeper reading"""
    try:
        resp=requests.get(url,time_out=10,headers={"User-Agent": "Mozilla/5.0"})
        soup=BeautifulSoup(resp.text,"html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):  ## 
            tag.decompose()  ## removes unwanted tags style nav header footer
        return soup.get_text(separator=" ",strip=True)[:4000]   ## to get text from the tags 
    except Exception as e:
        return f"could not scrape from {e}"





