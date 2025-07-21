from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from helpers import extract_text_from_pdf, find_plan_and_justification

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files or 'prompt' not in request.form:
        return jsonify({"error": "Missing file or prompt"}), 400

    file = request.files['file']
    prompt = request.form['prompt']

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        text = extract_text_from_pdf(filepath)
        plan, justification, status = find_plan_and_justification(text, prompt)

        if status != "Success":
            return jsonify({"error": status}), 400

        return jsonify({
            "plan_found": plan,
            "justification": justification
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "API is running. Use POST /analyze with a PDF file and prompt."

if __name__ == '__main__':
    app.run(debug=True)
