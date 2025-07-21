 from flask import Flask, request, jsonify, render_template
from helpers import analyze_query
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files.get("file")
        prompt = request.form.get("prompt")

        if not file or not prompt:
            return jsonify({"error": "Missing file or prompt."}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        result = analyze_query(filepath, prompt)
        return jsonify(result)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
