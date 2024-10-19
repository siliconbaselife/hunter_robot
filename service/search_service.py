import os
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.embeddings import OpenAIEmbeddings

from langchain.vectorstores import Chroma

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

    vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db_oai")

    return results
