import logging
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_db(db_params):
    """Connect to the PostgreSQL database on GCP."""
    try:
        conn = psycopg2.connect(**db_params)
        logging.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        raise

def setup_pgvector(db_params):
    """Ensure pgvector extension is enabled."""
    try:
        conn = connect_db(db_params)
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        logging.info("pgvector extension enabled")
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error setting up pgvector: {e}")
        raise