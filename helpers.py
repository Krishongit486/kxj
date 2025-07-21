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


def extract_section(text, start_heading, end_heading_keywords):
    text = text.lower()
    start_idx = text.find(start_heading.lower())
    if start_idx == -1:
        return ""

    end_idx = -1
    for end_heading in end_heading_keywords:
        end_idx = text.find(end_heading.lower(), start_idx + len(start_heading))
        if end_idx != -1:
            break

    if end_idx == -1:
        return text[start_idx + len(start_heading):].strip()
    return text[start_idx + len(start_heading):end_idx].strip()


def extract_rows(section_text):
    lines = section_text.strip().splitlines()
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in re.split(r"\s{2,}", line) if cell.strip()]
        if cells:
            rows.append(cells)
    return rows


# --- NEW: Basic Jaccard similarity without external libraries ---
def jaccard_similarity(a, b):
    set_a = set(re.findall(r'\w+', a.lower()))
    set_b = set(re.findall(r'\w+', b.lower()))
    if not set_a or not set_b:
        return 0.0
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))


def find_best_match(prompt, candidates):
    best_candidate = ""
    best_score = 0
    for candidate in candidates:
        score = jaccard_similarity(prompt, candidate)
        if score > best_score:
            best_candidate = candidate
            best_score = score
    return best_candidate, best_score


def find_plan_info(text, prompt, cover_type):
    if cover_type == "domestic":
        table_headings = [
            "table of benefits for domestic cover",
            "in-patient benefits for domestic cover"
        ]
        exclusion_heading = "exclusions for domestic cover"
    else:
        table_headings = [
            "table of benefits for international cover",
            "in-patient benefits for international cover"
        ]
        exclusion_heading = "exclusions for international cover"

    table_section = ""
    for heading in table_headings:
        table_section = extract_section(
            text,
            heading,
            ["exclusions", "terms and conditions", "section", "waiting period"]
        )
        if table_section:
            break

    if not table_section:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Relevant table or exclusions section not found.",
            "summary": "Unable to locate required sections in document."
        }

    rows = extract_rows(table_section)
    if not rows or len(rows) < 2:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Table format not recognized.",
            "summary": "Unable to extract table rows."
        }

    headings = rows[0]
    plan_candidates = [row[0] for row in rows[1:] if row]
    best_plan, confidence = find_best_match(prompt, plan_candidates)

    if confidence < 0.3:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Plan not found with sufficient confidence.",
            "summary": "Could not confidently match plan."
        }

    matched_row = next((row for row in rows if best_plan.lower() in row[0].lower()), None)
    amount_info = dict(zip(headings[1:], matched_row[1:])) if matched_row and len(matched_row) > 1 else {"Amount": "N/A"}

    exclusion_section = extract_section(
        text,
        exclusion_heading,
        ["section", "appendix", "contact", "waiting period"]
    )

    justification = ""
    for line in exclusion_section.splitlines():
        if best_plan.lower() in line.lower():
            justification = line.strip()
            break

    if not justification:
        justification = "Justification not found."

    summary = (
        f"✅ Plan '{best_plan}' was matched from the {cover_type.upper()} benefits table.\n"
        f"💰 Amount Details: {amount_info}\n"
        f"📄 Justification: {justification}"
    )

    return {
        "plan_found": True,
        "amount": amount_info,
        "justification": justification,
        "summary": summary
    }

