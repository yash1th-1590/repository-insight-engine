from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from archaeologist import CodeArchaeologist
import os
import traceback

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

archaeologist = CodeArchaeologist()

@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_repo():
    try:
        data = request.json
        repo_url = data.get('repo')
        
        if not repo_url:
            return jsonify({'error': 'Repository URL required'}), 400
        
        result = archaeologist.analyze_repository(repo_url)
        cleaned = clean_none_values(result)
        return jsonify(cleaned)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def clean_none_values(obj):
    if isinstance(obj, dict):
        return {k: clean_none_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_none_values(item) for item in obj]
    elif obj is None:
        return 'N/A'
    else:
        return obj

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)