from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
from config.config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, DB_PARAMS, OLLAMA_EMBEDDING_MODEL, OLLAMA_LLM_MODEL
from src.db import setup_pgvector
from src.file_processor import load_and_process_files
from src.rag import embed_and_store, create_rag_chain

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

# Global variable to store vector store
vector_store = None

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle file uploads and queries."""
    global vector_store
    
    if request.method == 'POST':
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                try:
                    # Setup pgvector
                    setup_pgvector(DB_PARAMS)
                    
                    # Process file based on type
                    kwargs = {
                        'pdf_path': file_path if filename.endswith('.pdf') else None,
                        'csv_path': file_path if filename.endswith('.csv') else None,
                        'txt_path': file_path if filename.endswith('.txt') else None
                    }
                    chunks = load_and_process_files(**kwargs)
                    
                    # Embed and store
                    vector_store = embed_and_store(chunks, DB_PARAMS, OLLAMA_EMBEDDING_MODEL)
                    flash('File uploaded and processed successfully!', 'success')
                except Exception as e:
                    flash(f'Error processing file: {str(e)}', 'error')
                finally:
                    # Clean up uploaded file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                return redirect(url_for('index'))
            else:
                flash('Invalid file type. Only PDF, CSV, and TXT are allowed.', 'error')
        
        # Handle query
        if 'query' in request.form and vector_store:
            query = request.form['query']
            try:
                rag_chain = create_rag_chain(vector_store, OLLAMA_LLM_MODEL)
                response = rag_chain.invoke(query)
                return render_template('index.html', response=response, query=query)
            except Exception as e:
                flash(f'Error processing query: {str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)