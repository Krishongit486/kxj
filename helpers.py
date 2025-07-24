import os
import PyPDF2
import google.generativeai as genai

# ✅ Load Gemini API key from terminal environment variable
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY environment variable not set in terminal.")

# 🔧 Configure Gemini with lighter model (chat-bison-001)
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="models/chat-bison-001")  # Lighter alternative to gemini-pro

def extract_text_from_pdf(path):
    """Extracts all text from a PDF file."""
    with open(path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

def query_gemini(document_text, user_prompt):
    """Sends the PDF text and user prompt to Gemini (lightweight model) for intelligent plan extraction."""
    query = (
        "You are a smart health insurance assistant.\n\n"
        "Given the following health insurance policy document:\n"
        "----- START OF DOCUMENT -----\n"
        f"{document_text[:12000]}\n"  # Truncate for lighter model context
        "----- END OF DOCUMENT -----\n\n"
        f"The user wants to know the details about the plan described in their query: '{user_prompt}'.\n\n"
        "Please return the following in your response:\n"
        "1. ✅ Name of the plan matched from the document.\n"
        "2. 💰 Coverage amount or limits from the table (if any).\n"
        "3. 📄 Justification or nearby paragraph mentioning the plan.\n"
        "4. 📝 A short, simple summary.\n"
        "If a plan cannot be confidently matched, say so clearly and explain why."
    )

    try:
        response = model.generate_content(query)
        return {
            "summary": response.text.strip(),
            "plan_found": "plan" in response.text.lower() or "matched" in response.text.lower()
        }
    except Exception as e:
        return {
            "plan_found": False,
            "summary": f"❌ Error contacting Gemini: {e}"
        }
