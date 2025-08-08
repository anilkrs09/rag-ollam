import logging
import PyPDF2
import pandas as pd
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_text(text: str) -> str:
    """Remove NUL characters and other problematic characters from text."""
    if not isinstance(text, str):
        text = str(text)
    # Replace NUL characters and other control characters (except \n, \r, \t)
    return ''.join(c for c in text if c == '\n' or c == '\r' or c == '\t' or ord(c) >= 32)

def load_and_process_files(pdf_path=None, csv_path=None, txt_path=None):
    """Load and process PDF, CSV, or TXT files into LangChain documents."""
    documents = []
    
    try:
        if pdf_path:
            logging.info(f"Processing PDF: {pdf_path}")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text() or ""
                    text = sanitize_text(text)
                    if text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={"filename": pdf_path.split('/')[-1], "page": page_num}
                        )
                        documents.append(doc)
        
        elif csv_path:
            logging.info(f"Processing CSV: {csv_path}")
            df = pd.read_csv(csv_path)
            for index, row in df.iterrows():
                text = sanitize_text(" ".join(str(value) for value in row.values))
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={"filename": csv_path.split('/')[-1], "row": index + 1}
                    )
                    documents.append(doc)
        
        elif txt_path:
            logging.info(f"Processing TXT: {txt_path}")
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = sanitize_text(file.read())
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={"filename": txt_path.split('/')[-1]}
                    )
                    documents.append(doc)
        
        logging.info(f"Processed {len(documents)} document chunks")
        return documents
    
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        raise