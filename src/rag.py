import logging
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def embed_and_store(chunks, db_params, embedding_model_name):
    """Embed documents using Ollama and store in PostgreSQL with pgvector."""
    try:
        embedding_model = OllamaEmbeddings(model=embedding_model_name)
        vector_store = PGVector(
            collection_name="rag_collection",
            connection_string=f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}",
            embedding_function=embedding_model
        )
        vector_store.add_documents(chunks)
        logging.info("Documents embedded and stored in PostgreSQL")
        return vector_store
    except Exception as e:
        logging.error(f"Error embedding/storing documents: {e}")
        raise

def create_rag_chain(vector_store, llm_model_name):
    """Create RAG chain for querying."""
    llm = ChatOllama(model=llm_model_name)
    
    prompt_template = """Given the following context, answer the question concisely and accurately. If you don't know the answer, say so.

Context: {context}

Question: {question}

Answer: """
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain