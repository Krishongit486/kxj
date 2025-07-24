import os
import PyPDF2
import google.generativeai as genai

# Setup Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def extract_text_from_pdf(path):
    with open(path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

def query_gemini(document_text, user_prompt):
    query = (
        f"You are a health insurance assistant. Given the following PDF content:\n\n"
        f"{document_text[:25000]}\n\n"  # Truncate for token limits
        f"User wants to know details about a plan based on this prompt: '{user_prompt}'.\n"
        f"Return:\n"
        f"1. Plan matched.\n"
        f"2. Coverage amount info (as per table if any).\n"
        f"3. Justification or nearby paragraph mentioning the plan.\n"
        f"4. Summary in simple terms.\n"
        f"If plan is not confidently found, return a proper message."
    )

    try:
        response = model.generate_content(query)
        return {"summary": response.text, "plan_found": "plan" in response.text.lower()}
    except Exception as e:
        return {
            "plan_found": False,
            "summary": f"Error contacting Gemini: {e}"
        }
