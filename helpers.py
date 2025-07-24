import re
import PyPDF2

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

def extract_table_section(text, cover_type):
    text = text.lower()
    if cover_type == "domestic":
        heading = "table of benefits for domestic cover"
    else:
        heading = "part b- coverage- international"

    start_idx = text.find(heading)
    if start_idx == -1:
        return ""
    return text[start_idx:start_idx + 5000]  # grab nearby section, ~5000 chars

def extract_rows(section_text):
    lines = section_text.strip().splitlines()
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in re.split(r'\s{2,}', line) if cell.strip()]
        if cells:
            rows.append(cells)
    return rows

def jaccard_similarity(a, b):
    set_a = set(re.findall(r'\w+', a.lower()))
    set_b = set(re.findall(r'\w+', b.lower()))
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def find_best_match(prompt, candidates):
    best_candidate, best_score = "", 0
    for candidate in candidates:
        score = jaccard_similarity(prompt, candidate)
        if score > best_score:
            best_candidate, best_score = candidate, score
    return best_candidate, best_score

def extract_justification(text, plan_name):
    pattern = re.compile(rf"{re.escape(plan_name)}(.*?)(\n[A-Z][^\n]*\n|$)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else "Justification not found in vicinity of plan name."

def find_plan_info(text, prompt, cover_type):
    table_section = extract_table_section(text, cover_type)
    rows = extract_rows(table_section)

    if len(rows) < 2:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Table could not be parsed properly.",
            "summary": "Check PDF formatting or headings."
        }

    headers = rows[0]
    plan_rows = rows[1:]
    plan_names = [row[0] for row in plan_rows if row]

    best_match, confidence = find_best_match(prompt, plan_names)
    if confidence < 0.3:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Low confidence in matching plan.",
            "summary": f"No reliable match found. Best match was: {best_match} ({confidence:.2f})"
        }

    matched_row = next((row for row in plan_rows if best_match.lower() in row[0].lower()), None)
    amount_info = dict(zip(headers[1:], matched_row[1:])) if matched_row else {}

    justification = extract_justification(text, best_match)

    return {
        "plan_found": True,
        "plan": best_match,
        "amount": amount_info,
        "justification": justification,
        "summary": (
            f"✅ Matched Plan: **{best_match}**\n"
            f"💰 Amount Info: {amount_info}\n"
            f"📄 Justification: {justification[:300]}"
        )
    }
