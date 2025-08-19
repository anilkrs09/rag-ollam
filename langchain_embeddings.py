flask
langchain
langchain-community
psycopg2-binary
sqlalchemy
pymupdf
pandas
pillow
pytesseract
google-cloud-pubsub
google-cloud-storage


import os

class Config:
    # Postgres + pgvector
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "vectordb")

    CONNECTION_STRING = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    COLLECTION_NAME = "documents"

    # Ollama
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text")

    # GCS + Pub/Sub
    GCS_BUCKET = os.getenv("GCS_BUCKET", "my-bucket")
    PUBSUB_PROJECT_ID = os.getenv("PUBSUB_PROJECT_ID", "my-gcp-project")
    PUBSUB_SUBSCRIPTION = os.getenv("PUBSUB_SUBSCRIPTION", "my-subscription")

    # Flask
    PORT = int(os.getenv("PORT", 8080))



from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
    def __init__(self, connection_string: str, collection_name: str, model_name: str = "nomic-embed-text", 
                 chunk_size: int = 1000, chunk_overlap: int = 100, enable_chunking: bool = True):
        self.extractors: Dict[str, Callable[[bytes], str]] = {}
        self.embeddings = OllamaEmbeddings(model=model_name)
        self.vectorstore = PGVector(
            connection_string=connection_string,
            embedding_function=self.embeddings,
            collection_name=collection_name,
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_chunking = enable_chunking

   # ---------- Register Extractors ----------
    def register_extractor(self, extensions, extractor_fn: Callable[[bytes], str]):
        if isinstance(extensions, str):
            extensions = [extensions]
        for ext in extensions:
            self.extractors[ext.lower()] = extractor_fn

    def get_extractor(self, filename: str) -> Optional[Callable[[bytes], str]]:
        ext = os.path.splitext(filename)[1].lower()
        return self.extractors.get(ext)

    # ---------- Extractors ----------
    @staticmethod
    def pdf_extractor(file_bytes: bytes) -> str:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def txt_extractor(file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8")

    @staticmethod
    def csv_extractor(file_bytes: bytes) -> str:
        df = pd.read_csv(io.BytesIO(file_bytes))
        return df.to_csv(index=False)

    @staticmethod
    def image_extractor(file_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image)

    # ---------- Chunking ----------
    def chunk_text(self, text: str, filename: str):
        if not self.enable_chunking:
            return [Document(page_content=text, metadata={"filename": filename})]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = splitter.split_text(text)
        return [
            Document(page_content=chunk,
                     metadata={"filename": filename, "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]


    def chunk_text(self, text: str, filename: str):
        """Split text into smaller chunks if chunking is enabled."""
        if not self.enable_chunking:
            return [Document(page_content=text, metadata={"filename": filename})]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = splitter.split_text(text)
        return [Document(page_content=chunk, metadata={"filename": filename}) for chunk in chunks]

    def process_file(self, filename: str, file_bytes: bytes):
        try:
            extractor = self.get_extractor(filename)
            if extractor is None:
                raise ValueError(f"No extractor registered for file: {filename}")

            logging.info(f"Extracting text from {filename}")
            text = extractor(file_bytes)
            logging.info(f"Extracted {len(text)} characters")

            # 🔥 Apply chunking
            docs = self.chunk_text(text, filename)

            self.vectorstore.add_documents(docs)
            logging.info(f"Embedded {len(docs)} chunks from {filename} into Postgres")

        except Exception as e:
            logging.error(f"Error processing {filename}: {e}", exc_info=True)
            raise

