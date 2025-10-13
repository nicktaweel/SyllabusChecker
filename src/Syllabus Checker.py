from pypdf import PdfReader
import os
from rapidfuzz import fuzz

# Ask the user to input the file path
file_path = input("Enter the path to the PDF file: ").strip()

if not os.path.isfile(file_path):
    print("Error: The file does not exist.")
elif not file_path.lower().endswith(".pdf"):
    print("Error: Only PDF files are accepted.")
else:
    file_name = os.path.basename(file_path).replace(".pdf", "")
    parts = file_name.split("_")

    if len(parts) >= 4 and parts[1][0].isdigit():
        course = f"{parts[0]}.{parts[1]}"
        instructor = parts[2]
        semester = parts[3]
    elif len(parts) >= 3:
        course = parts[0]
        instructor = parts[1]
        semester = parts[2]
    else:
        print("Warning: Unexpected filename format.")
        course = instructor = semester = None

    print(f"COURSE: {course}, INSTRUCTOR: {instructor}, SEMESTER: {semester}")

    reader = PdfReader(file_path)
    all_text = ""
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            all_text += text + "\n"
        else:
            all_text += f"\n--- Page {i} ---\n[No Text Found]\n"

    # --- Analyze Text ---
    required_sections = [
        "email",
        "materials",
        "outcome",
        "office hours",
        "objective",
        "grading",
        "exams",
        "academic integrity",
        "counseling",
        "equity"
    ]

    clean_text = all_text.lower()

    results = {}

    for section in required_sections:
        score = fuzz.partial_ratio(section, clean_text)
        results[section] = score >= 70

    print("\n--- Content Analysis Report ---")
    score = 0
    for section, found in results.items():
        status = "Found" if found else "Missing"
        print(f"{section.title()} : {status}")
        if found:
            score += 10

    print(f"\nOverall score: {score}")
