import logging
import os
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_and_process_files(pdf_path=None, csv_path=None, txt_path=None):
    """Load and chunk PDF, CSV, and text files, adding filename to metadata."""
    documents = []
    
    if pdf_path and os.path.exists(pdf_path):
        try:
            pdf_loader = PyPDFLoader(pdf_path)
            pdf_docs = pdf_loader.load()
            filename = os.path.basename(pdf_path)
            for doc in pdf_docs:
                doc.metadata["filename"] = filename
            documents.extend(pdf_docs)
            logging.info(f"Loaded PDF: {pdf_path}")
        except Exception as e:
            logging.error(f"Error loading PDF: {e}")
            raise
    
    if csv_path and os.path.exists(csv_path):
        try:
            csv_loader = CSVLoader(file_path=csv_path, encoding='utf-8')
            csv_docs = csv_loader.load()
            filename = os.path.basename(csv_path)
            for doc in csv_docs:
                doc.metadata["filename"] = filename
            documents.extend(csv_docs)
            logging.info(f"Loaded CSV: {csv_path}")
        except Exception as e:
            logging.error(f"Error loading CSV: {e}")
            raise
    
    if txt_path and os.path.exists(txt_path):
        try:
            txt_loader = TextLoader(file_path=txt_path, encoding='utf-8')
            txt_docs = txt_loader.load()
            filename = os.path.basename(txt_path)
            for doc in txt_docs:
                doc.metadata["filename"] = filename
            documents.extend(txt_docs)
            logging.info(f"Loaded Text: {txt_path}")
        except Exception as e:
            logging.error(f"Error loading Text: {e}")
            raise
    
    if not documents:
        logging.error("No documents loaded")
        raise ValueError("No valid files provided")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    logging.info(f"Created {len(chunks)} document chunks")
    return chunks