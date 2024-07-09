import os
import re
import json
from striprtf.striprtf import rtf_to_text
from datetime import datetime
from multiprocessing import Pool, Manager

# Function to extract green background text (footnote references) from the body text.
def extract_green_background_text(text):
    green_background_pattern = r'\\cb12(.+?)\\par'
    matches = re.findall(green_background_pattern, text)
    cleaned_text = re.sub(green_background_pattern, '', text)
    return matches, cleaned_text

# Function to check if a text starts with pinkish text on a blue background.
def starts_with_colored_text(body_text):
    pink_blue_pattern = r'\\cf2\\cb10'
    return bool(re.search(pink_blue_pattern, body_text))

# Function to check if any breadcrumb contains a title that should prevent overlap.
def has_no_overlap_title(breadcrumbs):
    no_overlap_titles = [
        'תניא',
        'קונטרס ומעין',
        'אגרות קודש',
        'אדמו"ר ה"צמח צדק" ותנועת ה"השכלה"',
        'תורת מנחם',
        'מאמרים מלוקטים',
        'היום יום',
        'לקוטי טעמים ומנהגים להגדה של פסח'
    ]
    for title in no_overlap_titles:
        for breadcrumb in breadcrumbs:
            if title in breadcrumb or title.replace(' ', '-') in breadcrumb:
                return True
    return False

# Function to check if the text starts with an opening that should prevent overlap at the beginning.
def starts_with_no_overlap_opening(text):
    no_overlap_openings = [
        'ב"ה',
        'והנה',
        'להבין',
        'וביאור הענין'
    ]
    for opening in no_overlap_openings:
        if text.strip().startswith(opening):
            return True
    return False

# Function to check if the text starts with a large title (size 20 or 18) that should prevent overlap.
def starts_with_large_title(text):
    large_title_pattern = r'\\fs(48|44|40|24|32|22|20|18)'
    return bool(re.search(large_title_pattern, text.split('\n', 1)[0]))

# Function to get the body text after the titles.
def get_body_text(plain_text):
    lines = plain_text.split('\n')
    body_lines = []
    in_body = False
    for line in lines:
        # Assume titles have larger font sizes (e.g., 48, 44, 40, 32, 22)
        if re.search(r'\\fs(48|44|40|32|22|24)', line):
            continue
        # Start collecting body lines after the titles
        if re.search(r'\\fs(20|18|16)', line):
            in_body = True
        if in_body:
            body_lines.append(line)
    return '\n'.join(body_lines)

# Function to check if two documents are duplicates by comparing their content.
def is_duplicate(doc1, doc2):
    return doc1.strip() == doc2.strip()

# Function to process an RTF file and extract relevant data.
def process_rtf_file(args):
    file_path, prev_text, next_text, is_duplicate_doc, is_first_in_book = args
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            rtf_content = file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None, None, None

    try:
        plain_text = rtf_to_text(rtf_content)
    except Exception as e:
        print(f"Error converting RTF to text for file {file_path}: {e}")
        return None, None, None

    result = {
        "Metadata": {
            "source": "Example Source",
            "uploadedDate": datetime.now().strftime("%Y-%m-%d")
        },
        "Breadcrumbs": [],
        "Main titles": [],
        "Second titles": [],
        "More titles": [],
        "Normal Text": [],
        "Reference/Remarks": [],
        "Topics of Extracts Window": [],
        "Numbers of Extracts Window": [],
        "FootnoteReferences": [],
        "Green Background Text": []
    }

    size_pattern = r'\\fs(\d+)'
    breadcrumb_pattern = r'\\cb1\\cf2(.+?)\\par'
    footnote_pattern = r'\\chftn'
    footnote_counter = 1
    breadcrumbs = []

    for line in plain_text.split('\n'):
        # Check for breadcrumbs (yellow background / pinkish text)
        breadcrumb_match = re.search(breadcrumb_pattern, line)
        if breadcrumb_match:
            breadcrumbs = breadcrumb_match.group(1).split('/')
            for i, breadcrumb in enumerate(breadcrumbs):
                result[f"Breadcrumb {i+1}"] = breadcrumb.strip()
            continue

        # Extract green background text (footnote references)
        green_matches, cleaned_line = extract_green_background_text(line)
        if green_matches:
            result["Green Background Text"].extend(green_matches)
            line = cleaned_line

        # Process footnotes
        footnote_match = re.search(footnote_pattern, line)
        if footnote_match:
            footnote_text = re.sub(r'\\[a-z]+\d*', '', line).strip()
            footnote_id = f"F{footnote_counter}"
            result["FootnoteReferences"].append({
                "FootnoteID": footnote_id,
                "FootnoteLevel": 1,
                "FootnoteType": "General",
                "ReferencedTextID": "T1",
                "ReferencedTextSnippet": "Referenced text snippet",
                "FootnoteContent": footnote_text,
                "PositionInDocument": {
                    "Page": 1,
                    "Paragraph": 1
                },
                "ContextualTags": ["footnote"]
            })
            footnote_counter += 1
            continue

        # Process other text based on font size
        size_match = re.search(size_pattern, line)
        if size_match:
            font_size = int(size_match.group(1)) // 2
            clean_text = re.sub(r'\\[a-z]+\d*', '', line).strip()

            if font_size == 48 or font_size == 44 or font_size == 40 or font_size == 24:
                result["Main titles"].append(clean_text)
            elif font_size == 32 or font_size == 22:
                result["Second titles"].append(clean_text)
            elif font_size == 20:
                result["More titles"].append(clean_text)
            elif font_size == 16:
                if "Underline" in line:
                    result["The Searched Words"].append(clean_text)
                else:
                    result["Normal Text"].append(clean_text)
            elif font_size == 18 or font_size == 32:
                result["Emphasis"].append(clean_text)
            elif font_size == 14:
                result["Reference/Remarks"].append(clean_text)
            elif font_size == 10:
                result["Topics of Extracts Window"].append(clean_text)
            elif font_size == 11:
                result["Numbers of Extracts Window"].append(clean_text)

    body_text = get_body_text(plain_text)
    plain_text_with_overlap = plain_text
    if not has_no_overlap_title(breadcrumbs) and not starts_with_no_overlap_opening(body_text) and not starts_with_colored_text(body_text) and not starts_with_large_title(plain_text) and not is_first_in_book:
        plain_text_with_overlap = append_text(plain_text, prev_text, next_text)
    elif not has_no_overlap_title(breadcrumbs):  # Only add overlap at the end
        if starts_with_colored_text(body_text) and len(body_text) < 300:
            pass
        else:
            plain_text_with_overlap += '\n' + next_text if next_text and not is_duplicate_doc else ''

    return result, plain_text_with_overlap[:100], plain_text_with_overlap[-100:], is_duplicate_doc

def process_batch(file_paths, results, footnotes):
    prev_texts = [None] * len(file_paths)
    next_texts = [None] * len(file_paths)
    is_duplicate_docs = [False] * len(file_paths)
    is_first_in_book_flags = [False] * len(file_paths)

    for i in range(len(file_paths)):
        if i > 0:
            prev_texts[i] = file_paths[i-1][1]
        if i < len(file_paths) - 1:
            next_texts[i] = file_paths[i+1][2]

    args = [(file_paths[i][0], prev_texts[i], next_texts[i], is_duplicate_docs[i], is_first_in_book_flags[i]) for i in range(len(file_paths))]
    
    with Pool() as pool:
        outputs = pool.map(process_rtf_file, args)
    
    for i, output in enumerate(outputs):
        if output:
            result, prev_overlap, next_overlap, is_duplicate_doc = output
            results.append(result)
            if prev_overlap:
                file_paths[i][1] = prev_overlap
            if next_overlap:
                file_paths[i][2] = next_overlap
            if i < len(file_paths) - 1:
                if is_duplicate(result, results[-1]):
                    is_duplicate_docs[i] = True
                    is_duplicate_docs[i+1] = True
                if is_duplicate_docs[i] and not is_duplicate_docs[i-1]:
                    is_first_in_book_flags[i] = True

def process_directory(directory_path):
    all_results = {"Documents": []}
    all_footnotes = {"Footnotes": []}
    files = sorted([f for f in os.listdir(directory_path) if f.endswith(".rtf")])
    
    manager = Manager()
    results = manager.list()
    footnotes = manager.list()

    file_paths = [(os.path.join(directory_path, f), None, None) for f in files]
    
    for i in range(0, len(file_paths), BATCH_SIZE):
        batch = file_paths[i:i + BATCH_SIZE]
        process_batch(batch, results, footnotes)
    
    for result in results:
        all_results["Documents"].append(result)
    
    for footnote in footnotes:
        all_footnotes["Footnotes"].append(footnote)

    # Save main document JSON
    output_path_docs = os.path.join(directory_path, 'documents_output.json')
    try:
        with open(output_path_docs, 'w', encoding='utf-8') as json_file:
            json.dump(all_results, json_file, indent=2)
    except Exception as e:
        print(f"Error writing documents JSON output: {e}")

    # Save footnotes JSON
    output_path_footnotes = os.path.join(directory_path, 'footnotes_output.json')
    try:
        with open(output_path_footnotes, 'w', encoding='utf-8') as json_file:
            json.dump(all_footnotes, json_file, indent=2)
    except Exception as e:
        print(f"Error writing footnotes JSON output: {e}")

# Usage
process_directory('/path/to/your/rtf/files')
