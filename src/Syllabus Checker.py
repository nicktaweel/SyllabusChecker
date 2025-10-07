from pypdf import PdfReader
import os

file_path = input("Enter the path to the PDF file: ").strip()

if not os.path.isfile(file_path):
    print("Error: File not found")
elif not file_path.lower().endswith(".pdf"):
    print("Error: Only PDF files are accepted")
else:
    reader = PdfReader(file_path)

    print(f"Number of pages: {len(reader.pages)}")

    all_text = ""

    for i, page in enumerate(reader.pages, start = 1):
        text = page.extract_text()
        if text:
            all_text += f"\n--- Page {i} ---\n{text}\n"
        else:
            all_text += f"\n--- Page {i} ---\n[No Text Found]\n"

    print("\n---- Extracted Text from Input Syllabus ----\n")
    print(all_text.strip())