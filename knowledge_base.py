from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

class KnowledgeBase:
    def __init__(self, embeddings_model="all-MiniLM-L6-v2", persist_directory="./knowledge_base_db"):
        self.embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True) # Ensure directory exists
        self.initialize_vector_db()
        
    def initialize_vector_db(self):
        # Initial facts - consider loading from a file for larger KBs
        initial_facts = [
            "Narendra Modi is the Prime Minister of India as of 2024.",
            "The position of Prime Minister of India is the head of government in India.",
            "Donald Trump was the 45th President of the United States.",
            "Donald Trump was elected as the 47th President of the United States in 2024.", # Hypothetical for testing
            "The United States has a presidential system of government.",
            "India has a parliamentary system of government.",
            "Joe Biden was the 46th President of the United States.",
            "The capital of India is New Delhi.",
            "The capital of the United States is Washington, D.C.",
        ]
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20) # Increased chunk size
        
        # Check if DB already exists to avoid re-initializing with same data (basic check)
        # A more robust check would involve versioning or checking content hash
        if not os.path.exists(os.path.join(self.persist_directory, "chroma.sqlite3")) or not os.listdir(self.persist_directory):
            docs = text_splitter.create_documents(initial_facts)
            self.vectordb = Chroma.from_documents(
                documents=docs,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.vectordb.persist()
            print("Knowledge base initialized and persisted.")
        else:
            self.vectordb = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("Knowledge base loaded from existing directory.")

    def query_knowledge_base(self, query, k=3):
        if self.vectordb:
            docs = self.vectordb.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        return []
        
    def add_fact(self, fact):
        if self.vectordb:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            docs = text_splitter.create_documents([fact])
            self.vectordb.add_documents(docs)
            self.vectordb.persist() # Persist after adding new facts
            print(f"Fact added to knowledge base: {fact}")