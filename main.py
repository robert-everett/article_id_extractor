import os
import re
import fitz
import sys
from PyQt5.QtWidgets import QApplication, QFileDialog

file_read_errors = []

# paper identifiers
DOI_REGEX   = r'10.\d{4,9}/[-._;()/:A-Z0-9]+'
ARXIV_REGEX = r'arXiv:\d{4}\.\d{5}(v\d+)?'
ISBN_REGEX  = r'ISBN[- ]?(1[03])?:?\s*((97[89])?\d{9}[\dX])'
PHREV_REGEX = r"^(Physical Review|PHYSICAL REVIEW|Phys\. Rev\.) (?: A| B| C| D| E| X)? \d+, \d+$"

def progress_bar(iteration, total, length=40):
    percent = (iteration / total) * 100
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    
    # Print progress bar
    sys.stdout.write(f'\r|{bar}| {percent:.2f}% Complete')
    sys.stdout.flush()

def get_file_name(file_path: str) -> str:
    file_name = os.path.basename(file_path)
    file_name = file_name.removesuffix(".pdf")
    return file_name

def select_extraction_directory(msg: str):
    app = QApplication([])
    result = QFileDialog.getExistingDirectory(None, msg, "", QFileDialog.ShowDirsOnly)
    print(f"\nExtraction Root Directory -> {result}")
    app.quit()
    return result

def open_fitz(f_path: str) -> fitz.Document:
    try:
        document = fitz.open(f_path)
    except fitz.FileDataError:
        file_read_errors.append(f_path)
        return None
    return document

def determine_match(expression: str, search_text: str) -> re.Match[str] | None:
    return re.search(expression, search_text, re.IGNORECASE)

def get_text(document: fitz.Document, page_number: int) -> str:
    return document.load_page(page_number).get_text()

def extract_text_from_file(f_path, num_pages: int = 3) -> str:
    if not os.path.exists(f_path):
        raise FileNotFoundError(f_path)    

    doc = open_fitz(f_path)
    text = ""
    if doc:
        num_pages = min(num_pages, doc.page_count)
        text = text.join(get_text(doc, ii) for ii in range(num_pages))
        doc.close()
    return text

def search_file_for_identifiers(f_path):

    def matches(identifier: str):
        return determine_match(identifier,
                    extract_text_from_file(f_path))
    
    args  = (DOI_REGEX, ARXIV_REGEX, ISBN_REGEX, PHREV_REGEX)
    for match in list(map(matches, args)):
        if match: 
            document_id = match.group(0)
            if document_id:
                return document_id
    return None

def recursive_search_and_extract(buffer: list, root_directory: str):
    print("\nSearching files..")
    files = (os.path.join(root, file)
                 for root, _, files in os.walk(root_directory)
                 for file in files if file.endswith(".pdf"))
    
    for file in files:
        document_id = search_file_for_identifiers(file)
        if document_id:
            buffer.append(
                dict(file=file, identifier=document_id))

def main():
    document_identifiers = []
    
    recursive_search_and_extract(document_identifiers,
        select_extraction_directory("Select an Extraction Directory"))
    
    num_identifiers = len(document_identifiers)
    if num_identifiers > 0:
        for k in range(num_identifiers):
            file_name = get_file_name(document_identifiers[k]['file'])
            ident = document_identifiers[k]['identifier']
            print(f"{ident} -> {file_name}")
    
    print(f"\nFile Identifiers Extracted -> {num_identifiers}\n")
    
    errors = file_read_errors.copy()
    errors = list(set(errors))
    num_read_errors = len(errors)
    if num_read_errors > 0:

        print(f"Error opening {num_read_errors} file(s):")
        for i in range(num_read_errors):
            print(f"\t->{errors[i]}")

if __name__ == "__main__":
    main()
