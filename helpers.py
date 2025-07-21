import fitz  # PyMuPDF
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text


def get_ngrams(text, n=2):
    tokens = re.findall(r'\w+', text.lower())
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


def extract_table_sections(text, cover_type):
    benefits_heading = f"table of benefits for {cover_type} cover"
    exclusions_heading = f"exclusions - {cover_type} cover"

    benefits_match = re.search(benefits_heading, text, re.I)
    exclusions_match = re.search(exclusions_heading, text, re.I)

    if not benefits_match or not exclusions_match:
        return None, None

    benefits_start = benefits_match.end()
    exclusions_start = exclusions_match.start()

    benefits_text = text[benefits_start:exclusions_start]
    exclusions_text = text[exclusions_match.end():]

    return benefits_text.strip(), exclusions_text.strip()


def match_plan_name(benefits_text, prompt):
    prompt_ngrams = get_ngrams(prompt, 2)
    lines = benefits_text.split('\n')
    best_match = ""
    best_score = 0
    best_amount = "N/A"

    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        plan_candidate = ' '.join(parts[:2]).lower()
        amount_candidate = ' '.join(parts[2:])

        for ngram in prompt_ngrams:
            score = cosine_similarity(
                [[hash(ngram)]],
                [[hash(plan_candidate)]]
            )[0][0] if ngram and plan_candidate else 0

            if score > best_score:
                best_score = score
                best_match = plan_candidate
                best_amount = amount_candidate

    return best_match, best_amount


def extract_justification(exclusions_text, plan_name):
    lines = exclusions_text.split('\n')
    for line in lines:
        if plan_name.lower() in line.lower():
            return line.strip()
    return "No specific justification found for this plan."


def process_policy(text, prompt):
    # Step 1: Determine cover type
    cover_type = "domestic" if "domestic" in prompt.lower() else "international" if "international" in prompt.lower() else None
    if not cover_type:
        return {
            "plan_found": False,
            "justification": "Cover type not specified (must contain 'domestic' or 'international')",
            "amount": "N/A",
            "summary": "We could not process your request due to lack of cover type."
        }

    # Step 2: Extract table and exclusion text
    benefits_text, exclusions_text = extract_table_sections(text, cover_type)
    if not benefits_text or not exclusions_text:
        return {
            "plan_found": False,
            "justification": "Relevant table or exclusions section not found.",
            "amount": "N/A",
            "summary": "Unable to locate required sections in document."
        }

    # Step 3: Match plan and amount
    plan_name, amount = match_plan_name(benefits_text, prompt)
    plan_found = plan_name != ""

    # Step 4: Extract justification
    justification = extract_justification(exclusions_text, plan_name) if plan_found else "Plan not found."

    # Step 5: Generate human-like summary
    if plan_found:
        summary = f"The plan '{plan_name}' under {cover_type.title()} cover was found. The amount covered is {amount}. Justification from exclusions: {justification}"
    else:
        summary = "We could not match your query to any plan in the document."

    return {
        "plan_found": plan_found,
        "plan_name": plan_name,
        "amount": amount,
        "justification": justification,
        "summary": summary
    }
