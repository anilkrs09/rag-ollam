import logging
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_community.vectorstores.pgvector import PGVector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def embed_and_store(chunks, db_params, embedding_model_name):
    """Embed documents using Ollama and store in PostgreSQL with pgvector."""
    try:
        embedding_model = OllamaEmbeddings(model=embedding_model_name)
        vector_store = PGVector.from_documents(
            documents=chunks,
            embedding=embedding_model,
            collection_name="rag_collection",
            connection_string=f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"
        )
        logging.info("Documents embedded and stored in PostgreSQL")
        return vector_store
    except Exception as e:
        logging.error(f"Error embedding/storing documents: {e}")
        raise

def create_rag_chain(vector_store, llm_model_name):
    """Create RAG chain for querying, including filename in response."""
    llm = ChatOllama(model=llm_model_name)
    
    prompt_template = """Given the following context from documents, answer the question concisely and accurately. If you don't know the answer, say so. List the source filenames used in the answer.

Context:
{context}

Question: {question}

Answer:
{answer}

Source Files:
{sources}
"""
    
    def format_context(documents):
        """Format context and collect filenames."""
        context = ""
        filenames = set()  # Use set to avoid duplicates
        for doc in documents:
            filename = doc.metadata.get("filename", "Unknown")
            filenames.add(filename)
            context += f"[{filename}]:\n{doc.page_content}\n\n"
        return {"context": context, "sources": ", ".join(filenames)}
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question", "answer", "sources"]
    )
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    def combine_context_and_answer(inputs):
        """Generate answer and combine with context and sources."""
        context = inputs["context"]
        question = inputs["question"]
        answer = llm.invoke(f"Context: {context['context']}\nQuestion: {question}\nAnswer:").content
        return {
            "context": context["context"],
            "question": question,
            "answer": answer,
            "sources": context["sources"]
        }
    
    rag_chain = (
        {"context": retriever | format_context, "question": RunnablePassthrough()}
        | RunnableLambda(combine_context_and_answer)
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain