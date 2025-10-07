from pypdf import PdfReader
import os

file_path = input("Enter the path to the PDF file: ").strip()

if not os.path.isfile(file_path):
    print("Error: File not found")
elif not file_path.lower().endswith(".pdf"):
    print("Error: Only PDF files are accepted")
else:

    file_name = os.path.basename(file_path).replace(".pdf", "")

    parts = file_name.split("_")

    if len(parts) < 3:
        print("Filename format should follow COURSE_NAME_SEMESTER.pdf")
        course = None
        instructor = None
        semester = None
    elif len(parts) == 4 and parts[1][0].isdigit():
            course = f"{parts[0]}.{parts[1]}"
            instructor = parts[2]
            semester = parts[3]
    else:
        course, instructor, semester = parts[0], parts[1], parts[2]

    print(f"COURSE: {course}, INSTRUCTOR: {instructor}, SEMESTER: {semester}")
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