from flask import Flask, request, jsonify
from helpers import extract_text_from_pdf, find_cover_type, find_plan_info

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("file")
    prompt = request.form.get("prompt", "")

    if not file or not prompt:
        return jsonify({"error": "File and prompt required."}), 400

    filepath = f"./uploads/{file.filename}"
    file.save(filepath)

    full_text = extract_text_from_pdf(filepath)
    cover_type = find_cover_type(prompt)

    if not cover_type:
        return jsonify({"error": "Mention 'domestic' or 'international' in your prompt."}), 400

    result = find_plan_info(full_text, prompt, cover_type)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

