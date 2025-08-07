import os

# Flask configuration
SECRET_KEY = 'ollama-key'  # Replace with a secure key
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'txt'}

# Database configuration for GCP PostgreSQL
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

# Ollama configuration
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_LLM_MODEL = "llama3.2"

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
