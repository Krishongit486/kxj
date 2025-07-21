import re
import os
import numpy as np
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(filepath):
    reader = PdfReader(filepath)
    all_text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            all_text += content + "\n"
    return all_text

def find_cover_type(prompt):
    prompt = prompt.lower()
    if "domestic" in prompt:
        return "domestic"
    elif "international" in prompt:
        return "international"
    return None

def extract_section(text, heading):
    pattern = re.compile(rf"{heading}", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    start = match.end()

    next_heading = re.search(r"(table of benefits|exclusions[\s\S]{0,20})", text[start:], re.IGNORECASE)
    end = start + next_heading.start() if next_heading else len(text)

    return text[start:end].strip()

def get_n_gram_match(plan_names, prompt, n=3):
    vectorizer = CountVectorizer(analyzer='char_wb', ngram_range=(n, n))
    all_texts = [prompt] + plan_names
    vectors = vectorizer.fit_transform(all_texts)
    sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    idx = np.argmax(sims)
    return plan_names[idx], sims[idx]

def find_plan_and_justification(text, prompt):
    cover_type = find_cover_type(prompt)
    if not cover_type:
        return None, None, "Cover type not found in prompt."

    table_heading = f"table of benefits for {cover_type} cover"
    exclusion_heading = f"exclusions - {cover_type} cover"

    table_text = extract_section(text, table_heading)
    exclusion_text = extract_section(text, exclusion_heading)

    if not table_text:
        return None, None, f"{cover_type.capitalize()} benefits table not found."
    if not exclusion_text:
        return None, None, f"{cover_type.capitalize()} exclusions section not found."

    # Step 1: Get plan names from the table (first word per line assumed)
    lines = table_text.splitlines()
    plan_names = [line.split()[0] if line.strip() else "" for line in lines if line.strip()]

    # Step 2: Use n-gram similarity to match
    best_plan, score = get_n_gram_match(plan_names, prompt)

    # Step 3: Look for justification line from exclusions
    justification = ""
    for line in exclusion_text.splitlines():
        if best_plan.lower() in line.lower():
            justification = line
            break

    return best_plan, justification or "No justification found.", "Success"
