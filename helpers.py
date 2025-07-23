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
    start_heading = start_heading.lower()
    start_idx = text.find(start_heading)
    if start_idx == -1:
        return ""
    end_idx = -1
    for end_heading in end_heading_keywords:
        end_heading = end_heading.lower()
        end_idx = text.find(end_heading, start_idx + len(start_heading))
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


def find_plan_info(text, prompt):
    # Step 1: Determine cover type
    cover_type = find_cover_type(prompt)
    if not cover_type:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Prompt doesn't indicate domestic or international clearly.",
            "summary": "Unable to determine cover type from prompt."
        }

    # Step 2: Select proper headings
    if cover_type == "domestic":
        table_heading = "table of benefits for domestic cover"
        in_patient_heading = "in-patient benefits for domestic cover"
    else:
        table_heading = "table of benefits for international cover"
        in_patient_heading = "in-patient benefits for international cover"

    # Step 3: Extract relevant sections
    table_section = extract_section(text, table_heading, ["exclusions", "terms", "section", "waiting period"])
    in_patient_section = extract_section(text, in_patient_heading, ["section", "appendix", "contact", "waiting period"])

    if not table_section or not in_patient_section:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Missing benefits or in-patient section.",
            "summary": "Required sections could not be extracted."
        }

    # Step 4: Parse table and find match
    rows = extract_rows(table_section)
    if not rows or len(rows) < 2:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Could not parse table properly.",
            "summary": "Table format was not recognized."
        }

    headings = rows[0]
    plan_rows = rows[1:]
    plan_candidates = [row[0] for row in plan_rows]
    best_plan, confidence = find_best_match(prompt, plan_candidates)

    if confidence < 0.3:
        return {
            "plan_found": False,
            "amount": "N/A",
            "justification": "Low confidence in plan match.",
            "summary": "Plan could not be confidently matched."
        }

    # Step 5: Extract corresponding amount row
    matched_row = next((row for row in plan_rows if best_plan.lower() in row[0].lower()), None)
    amount_info = dict(zip(headings[1:], matched_row[1:])) if matched_row and len(matched_row) > 1 else {"Amount": "N/A"}

    # Step 6: Extract justification from in-patient section
    justification = ""
    pattern = re.compile(rf"{re.escape(best_plan)}(.*?)(?=\n\S|\Z)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(in_patient_section)
    if match:
        justification = match.group(0).strip()
    else:
        justification = "Justification not found under in-patient benefits section."

    # Step 7: Prepare final response
    summary = (
        f"✅ Plan matched: **{best_plan}** under **{cover_type.upper()}** cover.\n"
        f"💰 Amount Details: {amount_info}\n"
        f"📄 Justification: {justification}"
    )

    return {
        "plan_found": True,
        "plan": best_plan,
        "amount": amount_info,
        "justification": justification,
        "summary": summary
    }
