from flask import Flask, request, jsonify
import os
from helpers import extract_text_from_pdf, find_cover_type, find_plan_info

app = Flask(__name__)

# Ensure upload folder exists
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return "Insurance Plan Analyzer API is running.", 200


@app.route("/analyze", methods=["POST"])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files['file']
    prompt = request.form.get("prompt", "")

    if not file or file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    if not prompt:
        return jsonify({"error": "Missing prompt."}), 400

    # Save uploaded file
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Extract text and analyze
    try:
        text = extract_text_from_pdf(filepath)
        cover_type = find_cover_type(prompt)

        if not cover_type:
            return jsonify({"error": "Prompt must mention 'domestic' or 'international'."}), 400

        result = find_plan_info(text, prompt, cover_type)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Internal processing error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
