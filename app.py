from flask import Flask, request, render_template, jsonify
import os
from helpers import extract_text_from_pdf, find_cover_type, find_plan_info

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        prompt = request.form.get("prompt", "")
        if not file or not prompt:
            return render_template("index.html", error="Please upload a file and enter a prompt.")

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        text = extract_text_from_pdf(filepath)
        cover_type = find_cover_type(prompt)

        if not cover_type:
            return render_template("index.html", error="Prompt must mention either 'domestic' or 'international'.")

        result = find_plan_info(text, prompt, cover_type)
        return render_template("result.html", result=result)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

