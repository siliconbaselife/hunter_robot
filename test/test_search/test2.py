import os
from langchain.chat_models.openai import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import ConversationSummaryBufferMemory
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.retrievers.web_research import WebResearchRetriever
from langchain.chains import RetrievalQAWithSourcesChain
from cryptography.fernet import Fernet

cipher = Fernet("Rthp08pOy1BzlI_PFXKXEXmqmxGv0k_DUsmFGjr6NZs=")

secret_token = "gAAAAABlWsO9M5MHWyTjwMrJTxqj1yfzfuvJXNAxVFCZT4AoyklbVX3_EpmIVv59HhTjg4bYIZugs2sXBHDDpfvuJaThWXZr_lRomw5YYMNVdq9atyo7gcQUs8u8iDbsO3qOVDBKH_BXkGoiFJWXdAJSnJqT3xCKcg=="
OPENAI_API_KEY = cipher.decrypt(secret_token).decode()
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

os.environ["GOOGLE_CSE_ID"] = "a5bb86389c8d54e04"
os.environ["GOOGLE_API_KEY"] = "AIzaSyADsE884QVkWz_Y8X1zJMvGl3lVmJ-IbZc"


class QuestionAnsweringSystem:
    def __init__(self):
        # Set up environment variables for API keys

        # Initialize components
        self.chat_model = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True,
                                     openai_api_key=os.environ['OPENAI_API_KEY'])
        self.vector_store = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db_oai")
        self.conversation_memory = ConversationSummaryBufferMemory(llm=self.chat_model, input_key='question',
                                                                   output_key='answer', return_messages=True)
        self.google_search = GoogleSearchAPIWrapper()
        self.web_research_retriever = WebResearchRetriever.from_llm(vectorstore=self.vector_store, llm=self.chat_model,
                                                                    search=self.google_search, allow_dangerous_requests=True)
        self.qa_chain = RetrievalQAWithSourcesChain.from_chain_type(self.chat_model,
                                                                    retriever=self.web_research_retriever)

    def answer_question(self, user_input_question):
        # Query the QA chain with the user input question
        result = self.qa_chain({"question": user_input_question})

        # Return the answer and sources
        return result["answer"], result["sources"]

    def get_docs(self, query="华为在印尼对标公司"):
        docs = self.web_research_retriever.get_relevant_documents(query)
        print(docs)


# Example usage:
qa_system = QuestionAnsweringSystem()
# user_input_question = input("Ask a question: ")
# answer, sources = qa_system.answer_question(user_input_question)
# print("Answer:", answer)
# print("Sources:", sources)
qa_system.get_docs()
