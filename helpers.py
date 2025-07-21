import docx2txt
import re

def extract_text(path):
    try:
        doc = docx.Document(path)
        return doc
    except Exception as e:
        raise ValueError(f"Error reading document: {e}")

def find_cover_type(prompt):
    prompt = prompt.lower()
    if "domestic" in prompt:
        return "domestic"
    elif "international" in prompt:
        return "international"
    else:
        return None

def find_plan_justification(doc, cover_type, prompt):
    if cover_type == "domestic":
        table_heading = "table of benefits for domestic cover"
        exclusion_heading = "exclusions - domestic cover"
    else:
        table_heading = "table of benefits for international cover"
        exclusion_heading = "exclusions - international cover"

    matched_table = None
    table_found = False
    for i, para in enumerate(doc.paragraphs):
        if table_heading in para.text.strip().lower():
            table_found = True
            matched_table = get_nearest_table(doc, i)
            break

    if not table_found or matched_table is None:
        return f"{cover_type.capitalize()} Table Of Benefits section not found."

    table_data = extract_table_data(matched_table)

    # Match plan name in leftmost column
    plan_name = prompt.lower()
    matched_row = None
    for row in table_data:
        if len(row) > 0 and row[0].strip().lower() in plan_name:
            matched_row = row
            matched_plan_name = row[0].strip()
            break

    if not matched_row:
        return "Plan not found in the selected table."

    # Get exclusions section text
    exclusion_text = ""
    in_exclusion = False
    for para in doc.paragraphs:
        txt = para.text.strip().lower()
        if exclusion_heading in txt:
            in_exclusion = True
            continue
        if in_exclusion and ("table of benefits" in txt or "cover" in txt):
            break
        if in_exclusion:
            exclusion_text += para.text + "\n"

    # Match plan name in exclusions
    justification = ""
    for line in exclusion_text.splitlines():
        if matched_plan_name.lower() in line.lower():
            justification = line
            break

    return justification if justification else "Justification not found in exclusions."

def get_nearest_table(doc, para_index, threshold=5):
    """
    Finds the table within 'threshold' paragraphs from the given index.
    """
    para_text = doc.paragraphs[para_index].text.strip()
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if para_text in cell.text:
                    return table
    # fallback: just return first table after heading para
    for i in range(para_index, min(len(doc.paragraphs), para_index + threshold)):
        if i < len(doc.tables):
            return doc.tables[i]
    return None

def extract_table_data(table):
    data = []
    for row in table.rows:
        data.append([cell.text.strip() for cell in row.cells])
    return data
