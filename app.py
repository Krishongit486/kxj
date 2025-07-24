from flask import Flask, request, render_template
from helpers import extract_text_from_pdf, query_gemini
import os

app = Flask(__name__)
UPLOAD_FOLDER = "./uploads"
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

        full_text = extract_text_from_pdf(filepath)
        result = query_gemini(full_text, prompt)

        return render_template("result.html", result=result, prompt=prompt)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

