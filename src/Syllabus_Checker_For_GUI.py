from pypdf import PdfReader
import os
from rapidfuzz import fuzz
from sentence_transformers import CrossEncoder
import re
import numpy as np

def check_syllabus(file_path, query):
    outputs = []

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
        outputs.append("Warning: Unexpected filename format.")
        course = instructor = semester = None

    outputs.append(f"Course: {course}")
    outputs.append(f"Instructor: {instructor}")
    outputs.append(f"Semester: {semester}\n")

    reader = PdfReader(file_path)
    all_text = ""
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            all_text += text + "\n"
        else:
            all_text += f"\n--- Page {i} ---\n[No Text Found]\n"

    required_sections = ["email", "materials", "outcome", "office hours", "objective", "grading", "exams", "academic integrity", "counseling", "equity"]

    clean_text = all_text.lower()
    results = {}
    outputs.append("--- Content Analysis Report ---")

    score = 0
    for section in required_sections:
        found = fuzz.partial_ratio(section, clean_text) >= 70
        results[section] = found
        status = "Found" if found else "Missing"
        outputs.append(f"{section.title()} : {status}")
        if found:
            score += 10

    outputs.append(f"\nOverall score: {score}\n")

    #Query Search with SentenceTransformer
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

    if not query:
        return "\n".join(outputs) + "\nNo query entered."

    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', all_text)
        if len(s.split()) > 3 and re.search(r"[A-Za-z]{3,}", s)
    ]

    scores = model.predict([(query.lower(), s.lower()) for s in sentences], show_progress_bar=False)
    probs = 1 / (1 + np.exp(-scores))
    results = list(zip(sentences, probs))
    results.sort(key=lambda x: x[1], reverse=True)

    best_sentence, best_score = results[0]
    threshold = 0.35
    found = best_score >= threshold

    outputs.append("\n--- Syllabus Checker Report ---")
    outputs.append(f"Query: {query}")
    outputs.append(f"Result: {'Found!' if found else 'Missing!'} (score = {best_score:.2f})")

    if found:
        outputs.append(f"\nExample match:\n{best_sentence.strip()}")

    return "\n".join(outputs)
