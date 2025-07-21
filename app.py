from flask import Flask, request, render_template, jsonify
from helpers import extract_text_from_pdf, analyze_query
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files or 'prompt' not in request.form:
        return jsonify({"error": "Missing file or prompt"}), 400

    file = request.files['file']
    prompt = request.form['prompt']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        text = extract_text_from_pdf(filepath)
        result = analyze_query(text, prompt)

        return render_template('result.html', result=result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
