from tavily import TavilyClient
from app.config import TAVILY_API_KEY


client=TavilyClient(
    api_key=TAVILY_API_KEY
)
def search(query:str):
   try:

    response=client.search(
        query=query,
        search_depth="basic",
        max_results=5
    )
    results=[]

    for item in response.get("results",[]):
        results.append({
            "title":item.get("title"),
            "url":item.get("url"),
            "content":item.get("content"),
            "score":item.get("score")
        })

    return{
        "succeess":True,
        "query":query,
        "results":results
       }
   except Exception as e:

        return {
            "success":False,
            "error_type":"SEARCH_ERROR",
            "error":str(e)
        }
