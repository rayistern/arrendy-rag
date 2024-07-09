import json
from docx import Document

def rgb_to_hex(rgb):
    if rgb is None:
        return None
    return f"{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def docx_to_json(file_path):
    doc = Document(file_path)
    # Initialize objects for specific colors
    object_1_text = []
    object_2_text = []

    for para in doc.paragraphs:
        for run in para.runs:
            hex_color = rgb_to_hex(run.font.color.rgb) if run.font.color.rgb else "000000"  # Default to black if no color set
            if hex_color == "000000":
                object_1_text.append(run.text)
            elif hex_color == "800000":
                object_2_text.append(run.text)

    # Combine text into JSON structure
    data = {
        "Object1": ' '.join(object_1_text),
        "Object2": ' '.join(object_2_text)
    }

    with open('output.json', 'w', encoding='utf-8') as json_file:  # Set encoding to utf-8
        json.dump(data, json_file, indent=4, ensure_ascii=False)

# Path to your DOCX file
docx_to_json('C:/Scripts/arrendy-rag/arrendy-rag/TestDocs/1101-1.docx')
