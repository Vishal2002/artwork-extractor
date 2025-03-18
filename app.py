from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import json
import sqlite3
import uuid
from werkzeug.utils import secure_filename
from pdf_extractor import PDFArtworkExtractor
from dataclasses import asdict
from flask_session import Session 
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
 # Add at top

# Configure server-side sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
Session(app)
# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def save_to_db(artworks):
    conn = sqlite3.connect('artworks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artworks (
            id TEXT PRIMARY KEY,
            title TEXT,
            artist TEXT,
            dimensions TEXT,
            material TEXT,
            year TEXT,
            description TEXT,
            page_number INTEGER,
            confidence REAL
        )
    ''')

    for artwork in artworks:
        cursor.execute('''
            INSERT INTO artworks (id, title, artist, dimensions, material, year, description, page_number, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            artwork['id'],
            artwork['title'],
            artwork['artist'],
            artwork['dimensions'],
            artwork['material'],
            artwork['year'],
            artwork['description'],
            artwork['page_number'],
            artwork.get('confidence', 0)  # Provide default if missing
        ))

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.pdf"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract artworks
        extractor = PDFArtworkExtractor()
        artworks = extractor.extract_artworks(filepath)
        
        # Convert to dict for JSON serialization
        
        artwork_dicts = [asdict(artwork) for artwork in artworks]
        
        # Store in session
        session['artworks'] = artwork_dicts
        session['pdf_path'] = filepath
        
        return redirect(url_for('results'))
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/results')
def results():
    if 'artworks' not in session:
        return redirect(url_for('index'))
    
    artworks = session['artworks']
    return render_template('results.html', artworks=artworks)

@app.route('/save', methods=['POST'])
def save_to_database():
    edited_artworks = request.json.get('artworks', [])
    
    # Save to database
    save_to_db(edited_artworks)
    
    # Clear session and delete uploaded PDF
    if 'pdf_path' in session:
        try:
            os.remove(session['pdf_path'])
        except Exception as e:
            print(f"Error removing file: {e}")
    
    session.pop('artworks', None)
    session.pop('pdf_path', None)
    
    return jsonify({'success': True, 'message': 'Data saved successfully'})


if __name__ == '__main__':
    app.run(debug=True)