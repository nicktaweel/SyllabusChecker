from pypdf import PdfReader
import os
from sentence_transformers import CrossEncoder
import re
import numpy as np

# Ask the user to input the file path
file_path = input("Enter the path to the PDF file: ").strip()

if not os.path.isfile(file_path):
    print("Error: The file does not exist.")
elif not file_path.lower().endswith(".pdf"):
    print("Error: Only PDF files are accepted.")
else:
    file_name = os.path.basename(file_path).replace(".pdf", "")
    parts = file_name.split("_")

# dumbass course correction code if too many too little underscores i know OCD bullshit
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

# save into variables for now cause i wanna use the instructor variable to find and fully print instructor name, so we get first name
# by using the last name we save here, to solve the Janghoon Yang / Yi Yang problem
    print(f"COURSE: {course}, INSTRUCTOR: {instructor}, SEMESTER: {semester}")

    reader = PdfReader(file_path)
    all_text = ""
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            all_text += text + "\n"
        else:
            all_text += f"\n--- Page {i} ---\n[No Text Found]\n"

    # Load cross-encoder model
    print("\nLoading sentence transformer model...")
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

    # Split text into sentences
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', all_text)
        if len(s.split()) > 3 and re.search(r"[A-Za-z]{3,}", s)
    ]

    # Define required sections with their search queries
    # created a dictionary so this works better, also found that sentence transformers can accept a fuck ton of words and
    # use all of them to develop their search. So we can add to the values in the dictionaries over time to better shape search
    required_sections = {
        "email": "email address contact information @psu.edu office hours",
        "materials": "required textbooks course materials readings references",
        "outcome": "course outcomes objective goal",
        "office hours": "office hours instructor availability meeting times",
        "objective": "course objectives learning objectives goals",
        "grading": "grading policy grade distribution grading scale",
        "exams": "exams tests quizzes",
        "academic integrity": "academic integrity academic honesty plagiarism cheating",
        "counseling": "counseling services mental health student support",
        "equity": "equity diversity inclusion accessibility accommodations"
    }

    # Define similarity threshold
    threshold = 0.35

    # Analyze each section
    print("\n--- Content Analysis Report ---")
    results = {}
    score = 0

    for section, query in required_sections.items():
        # Compare query to all sentences
        scores = model.predict(
            [(query.lower(), s.lower()) for s in sentences],
            show_progress_bar=False
        )

        # Convert to probabilities
        probs = 1 / (1 + np.exp(-scores))

        # Get best match
        best_score = np.max(probs)
        best_idx = np.argmax(probs)
        best_sentence = sentences[best_idx]

        # Check if found
        found = best_score >= threshold
        results[section] = {
            "found": found,
            "score": best_score,
            "sentence": best_sentence
        }

        status = "Found" if found else "Missing"
        print(f"{section.title()}: {status} (score = {best_score:.2f})")

        if found:
            score += 10

    print(f"\nOverall score: {score}")

    # Show example matches for ALL sections (even ones that fail threshold)
    show_examples = input("\nShow example matches for all sections? (y/n): ").strip().lower()
    if show_examples == 'y':
        print("\n--- Example Matches ---")
        for section, result in results.items():
            print(f"\n{section.title()} (score = {result['score']:.2f}):")
            print(f"  {result['sentence']}")

    # Custom query search (idk we can cut)
    print("\n" + "=" * 50)
    query = input("\nEnter a phrase to search for in the syllabus (e.g., 'attendance policy'): ").strip()

    if query:
        # Compare query to all sentences
        scores = model.predict(
            [(query.lower(), s.lower()) for s in sentences],
            show_progress_bar=False
        )

        # Convert to probabilities
        probs = 1 / (1 + np.exp(-scores))

        # Get top results
        query_results = list(zip(sentences, probs))
        query_results.sort(key=lambda x: x[1], reverse=True)

        best_sentence, best_score = query_results[0]
        found = best_score >= threshold

        print("\n--- Custom Query Report ---")
        print(f"Query: {query}")
        print(f"Result: {'Found!' if found else 'Missing!'} (score = {best_score:.2f})")

        if found:
            print(f"Example match:\n  {best_sentence.strip()}")
