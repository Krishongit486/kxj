from flask import Flask, request, jsonify
from helpers import extract_text, find_cover_type, find_plan_justification
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/ask", methods=["POST"])
def ask():
    prompt = request.form.get("prompt", "")
    file = request.files.get("file")

    if not file or not file.filename.endswith('.docx'):
        return jsonify({"error": "A valid .docx file must be uploaded."}), 400

    # Save uploaded file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Load and parse the document
    doc = extract_text(filepath)

    # Identify cover type from prompt
    cover_type = find_cover_type(prompt)
    if not cover_type:
        return jsonify({"error": "Cover type not recognized. Must mention 'domestic' or 'international'."}), 400

    # Find plan justification
    result = find_plan_justification(doc, cover_type, prompt)
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(debug=True)

