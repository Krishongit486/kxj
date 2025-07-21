import re
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
from difflib import get_close_matches

model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)
    return text

def ngram_similarity(a, b):
    a, b = a.lower(), b.lower()
    n = 3
    a_ngrams = {a[i:i+n] for i in range(len(a)-n+1)}
    b_ngrams = {b[i:i+n] for i in range(len(b)-n+1)}
    if not a_ngrams or not b_ngrams:
        return 0
    return len(a_ngrams & b_ngrams) / len(a_ngrams | b_ngrams)

def find_cover_type(prompt):
    prompt = prompt.lower()
    if "international" in prompt or "abroad" in prompt or "foreign" in prompt:
        return "international"
    elif "domestic" in prompt or "india" in prompt or "within country" in prompt:
        return "domestic"
    return None

def extract_tables(text, cover_type):
    # Simple heuristic split by section name
    if cover_type == "domestic":
        benefit_match = re.search(r'table of benefits\s*-\s*domestic.*?(exclusions\s*-\s*domestic|table of benefits\s*-\s*international)', text, re.I | re.S)
        exclusion_match = re.search(r'exclusions\s*-\s*domestic.*?(table of benefits\s*-\s*international|exclusions\s*-\s*international|$)', text, re.I | re.S)
    else:
        benefit_match = re.search(r'table of benefits\s*-\s*international.*?(exclusions\s*-\s*international|$)', text, re.I | re.S)
        exclusion_match = re.search(r'exclusions\s*-\s*international.*?$', text, re.I | re.S)

    benefit_text = benefit_match.group(0) if benefit_match else ""
    exclusion_text = exclusion_match.group(0) if exclusion_match else ""
    return benefit_text.strip(), exclusion_text.strip()

def find_best_plan_match(benefit_text, prompt):
    rows = [line for line in benefit_text.split('\n') if line.strip()]
    plan_candidates = []
    for row in rows:
        columns = [col.strip() for col in row.split("  ") if col.strip()]
        if len(columns) > 1:
            plan_candidates.append(columns)

    best_row = None
    best_score = 0
    prompt = prompt.lower()

    for row in plan_candidates:
        plan = row[0].lower()
        sim = ngram_similarity(plan, prompt)
        if sim > best_score:
            best_score = sim
            best_row = row

    return best_row, best_score

def find_justification(exclusion_text, plan_name):
    lines = exclusion_text.split('\n')
    best_line = ""
    best_score = 0
    for line in lines:
        sim = ngram_similarity(line, plan_name)
        if sim > best_score:
            best_score = sim
            best_line = line
    return best_line.strip()

def analyze_query(file_path, prompt):
    text = extract_text_from_pdf(file_path)
    cover_type = find_cover_type(prompt)

    if not cover_type:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Could not determine cover type.",
            "summary": "Please specify if it's domestic or international."
        }

    benefit_text, exclusion_text = extract_tables(text, cover_type)

    if not benefit_text:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Relevant table or exclusions section not found.",
            "summary": "Unable to locate required sections in document."
        }

    best_row, score = find_best_plan_match(benefit_text, prompt)

    if not best_row or score < 0.3:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Plan not found in table.",
            "summary": f"No matching plan found for the query under {cover_type} cover."
        }

    justification = find_justification(exclusion_text, best_row[0])
    amount_data = ", ".join(best_row[1:]) if len(best_row) > 1 else "N/A"

    return {
        "plan_found": True,
        "amount": amount_data,
        "justification": justification or "No justification found in exclusions.",
        "summary": f"The plan '{best_row[0]}' under {cover_type} cover includes the following: {amount_data}. Justification: {justification or 'Not available.'}"
    }
