from flask import Flask, request, render_template, jsonify
from helpers import extract_text_from_pdf, process_policy
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get("file")
    prompt = request.form.get("prompt")

    if not file or not prompt:
        return jsonify({"error": "Missing file or prompt."}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Read and process the PDF
    text = extract_text_from_pdf(filepath)
    result = process_policy(text, prompt)

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
