
from pypdf import PdfReader
import os
from rapidfuzz import fuzz

#for sentence transformers
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


############################################################################
#by rebecca nanayakkara 10/13/2025
#using sentence transformer cross encoder to compare queries to sentences in PDG
#load cross-encoder model from sentence transformers
#this model measures how semantically similar two pieces of text are
#this imported model is small, fast, and accurate model for sentence similarity
#source: https://pypi.org/project/sentence-transformers/
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

#let the user search what query they want
query = input("\nEnter a phrase to search for in the syllabus (e.g., 'attendance policy'): ").strip()
#if user presses enter without typing anything, stop program
if not query:
    raise SystemExit

#split exisiting text into sentences
#s.strip() removes extra spaces
#then for each sentence s, len(s.split()) > 3 ensures that the sentence has at least 4 words (filters out fragments like "David J.")
#re.search(r"[A-Za-z]{3,}", s) checks that there is at least one real word (3+ letters in a row), which avoids numbers and initials
sentences = [
    s.strip()
    for s in re.split(r'(?<=[.!?])\s+', all_text)
    if len(s.split()) > 3 and re.search(r"[A-Za-z]{3,}", s)
    ]

#compare each sentence to query
#model expects pairs : (query,sentence)
#both are lowercased to make case-insensitive
scores = model.predict([(query.lower(), s.lower()) for s in sentences], show_progress_bar=False)

#converts the models raw score (logits) into probabilities between 0 and 1 using the sigmoid function
probs = 1 / (1 + np.exp(-scores))
#combine each sentence with its similarity score in a list of tuples : [(sentence, score), ...]
results = list(zip(sentences, probs))
#sort sentences by similarity score in descending order (highest similarity first)
results.sort(key=lambda x: x[1], reverse=True)

#select the best match (highest score) and take its score
best_sentence, best_score = results[0]

#define a similarity threshold
threshold = 0.35 #adjust strictness; lower = less strict, higher = more strict
## if score is greater than 0.35, we can say that the query has found a match
found = best_score >= threshold
#print top results
print("\n--- Syllabus Checker Report ---")
print(f"Query: {query}")
print(f"Result: {'Found!' if found else 'Missing!'} (score = {best_score:.2f})")

if found:
    print(f"Example match:\n {best_sentence.strip()}")