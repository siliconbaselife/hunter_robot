import os
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper

os.environ["GOOGLE_CSE_ID"] = "a5bb86389c8d54e04"
os.environ["GOOGLE_API_KEY"] = "AIzaSyADsE884QVkWz_Y8X1zJMvGl3lVmJ-IbZc"


def google_search(n, query):
    search = GoogleSearchAPIWrapper(k=n)
    tool = Tool(
        name="google_search",
        description="Search Google for recent results.",
        func=search.run,
    )

    results = tool.run(query)

    return results
