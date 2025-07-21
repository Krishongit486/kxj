import re
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

def extract_text_from_pdf(filepath):
    doc = fitz.open(filepath)
    return "\n".join([page.get_text() for page in doc])

def get_ngrams(text, n=1):
    vectorizer = CountVectorizer(ngram_range=(n, n), stop_words='english').fit([text])
    return vectorizer.get_feature_names_out()

def semantic_search(clauses, query):
    query_emb = model.encode(query, convert_to_tensor=True)
    best_score = -1
    best_match = None

    for clause in clauses:
        if not clause.strip():
            continue
        clause_emb = model.encode(clause, convert_to_tensor=True)
        score = util.cos_sim(query_emb, clause_emb).item()
        if score > best_score:
            best_score = score
            best_match = clause
    return best_match

def analyze_query(text, query):
    # Extract region
    region = 'domestic' if 'domestic' in query.lower() else 'international' if 'international' in query.lower() else None
    if not region:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Could not determine whether domestic or international.",
            "summary": "Your query must mention either 'domestic' or 'international'."
        }

    # Find relevant sections
    benefit_section = extract_section(text, f"table of benefits for {region} cover")
    exclusion_section = extract_section(text, f"exclusions")

    if not benefit_section:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Relevant table or exclusions section not found.",
            "summary": "Unable to locate required sections in document."
        }

    lines = benefit_section.split("\n")
    plan_match = semantic_search(lines, query)

    if not plan_match:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Plan not found in benefits section.",
            "summary": "We couldn't find any matching plan for your query."
        }

    # Extract amount (basic pattern)
    amount_match = re.search(r'(₹|\$|INR|USD)?\s?\d{1,3}(?:,\d{3})*(?:\.\d+)?', plan_match)
    amount = amount_match.group() if amount_match else "N/A"

    # Get plan name for exclusion search
    plan_name = " ".join(plan_match.split()[:4])  # first few words
    justification = semantic_search(exclusion_section.split("\n"), plan_name) if exclusion_section else "N/A"

    return {
        "plan_found": True,
        "amount": amount,
        "justification": justification,
        "summary": f"✅ Plan identified as '{plan_name.strip()}'. Estimated coverage amount: {amount}. Justification: {justification or 'N/A'}"
    }

def extract_section(text, heading):
    lines = text.split("\n")
    capture = False
    section_lines = []

    for line in lines:
        if heading.lower() in line.lower():
            capture = True
            continue
        elif capture and re.match(r'^[A-Z][a-z]+', line):  # next heading
            break
        if capture:
            section_lines.append(line)

    return "\n".join(section_lines)
