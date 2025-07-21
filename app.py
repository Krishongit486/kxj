from flask import Flask, request, jsonify, render_template
from helpers import extract_text_from_pdf, find_cover_type, find_plan_info
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        prompt = request.form.get("prompt", "")

        if not file or not prompt:
            return jsonify({"error": "File and prompt are required."}), 400

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        text = extract_text_from_pdf(filepath)
        cover_type = find_cover_type(prompt)

        if not cover_type:
            return jsonify({"error": "Prompt must include either 'domestic' or 'international'."}), 400

        result = find_plan_info(text, prompt, cover_type)
        return jsonify(result)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

