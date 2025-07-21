import re
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(path):
    with open(path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

def find_cover_type(prompt):
    prompt = prompt.lower()
    if "domestic" in prompt:
        return "domestic"
    elif "international" in prompt:
        return "international"
    return None

def extract_section(text, start_heading, end_heading):
    pattern = re.compile(
        f"{re.escape(start_heading)}(.*?){re.escape(end_heading)}",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""

def find_best_match(prompt, candidates):
    vectorizer = TfidfVectorizer().fit_transform([prompt] + candidates)
    vectors = vectorizer.toarray()
    cosine = cosine_similarity([vectors[0]], vectors[1:])
    best_index = cosine[0].argmax()
    return candidates[best_index], cosine[0][best_index]

def extract_rows(section_text):
    lines = section_text.strip().splitlines()
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in re.split(r"\s{2,}", line) if cell.strip()]
        if cells:
            rows.append(cells)
    return rows

def find_plan_info(text, prompt, cover_type):
    # Updated headings based on actual document
    table_start = "Table of Benefits - Domestic Cover" if cover_type == "domestic" else "Table of Benefits - International Cover"
    table_end = "Exclusions for Domestic Cover" if cover_type == "domestic" else "Exclusions for International Cover"
    table_section = extract_section(text, table_start, table_end)

    if not table_section:
        return {"plan_found": False, "amount": "N/A", "justification": "Relevant table or exclusions section not found.", "summary": "Unable to locate required sections in document."}

    rows = extract_rows(table_section)
    if not rows:
        return {"plan_found": False, "amount": "N/A", "justification": "Table format not recognized.", "summary": "Unable to extract table rows."}

    headings = rows[0]
    plan_candidates = [row[0] for row in rows[1:] if row]
    best_plan, confidence = find_best_match(prompt, plan_candidates)

    if confidence < 0.3:
        return {"plan_found": False, "amount": "N/A", "justification": "Plan not found with sufficient confidence.", "summary": "Could not confidently match plan."}

    matched_row = next((row for row in rows if row[0] == best_plan), None)
    amount_info = dict(zip(headings[1:], matched_row[1:])) if matched_row and len(matched_row) > 1 else {"Amount": "N/A"}

    # Exclusion
    exclusion_heading = "Exclusions for Domestic Cover" if cover_type == "domestic" else "Exclusions for International Cover"
    exclusion_section = extract_section(text, exclusion_heading, "Section")

    justification = ""
    for para in exclusion_section.splitlines():
        if best_plan.lower() in para.lower():
            justification = para
            break
    if not justification:
        justification = "Justification not found."

    # Human summary
    summary = f"✅ Plan '{best_plan}' was matched from the {cover_type} table.\n💰 Amount Details: {amount_info}\n📄 Justification: {justification}"

    return {
        "plan_found": True,
        "amount": amount_info,
        "justification": justification,
        "summary": summary
    }
