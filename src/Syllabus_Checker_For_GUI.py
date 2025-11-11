from pypdf import PdfReader
import os
from sentence_transformers import CrossEncoder
import re
import numpy as np
import textstat


def check_syllabus(file_path):

    outputs = []

    # Validate file
    if not os.path.isfile(file_path):
        return "Error: The file does not exist."
    elif not file_path.lower().endswith(".pdf"):
        return "Error: Only PDF files are accepted."

    # Parse filename
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
        course = instructor = semester = "Unknown"

    outputs.append(f"COURSE: {course}, INSTRUCTOR: {instructor}, SEMESTER: {semester}")

    # Extract text from PDF
    reader = PdfReader(file_path)
    all_text = ""
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            all_text += text + "\n"
        else:
            all_text += f"\n--- Page {i} ---\n[No Text Found]\n"

    # Load model
    outputs.append("\nLoading sentence transformer model...")
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

    # Split into sentences
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+|\n+', all_text)
        if (len(s.split()) > 3 and re.search(r"[A-Za-z]{3,}", s))
    ]

    # Readability Analysis
    def rate_readability(sentences):
        # calculates readability and then deducts points form score. we can change later just how i decided to implement for now.
        text = " ".join(sentences).strip()
        penalty = 0

        # Calculate metrics
        fre = textstat.flesch_reading_ease(text)
        fk = textstat.flesch_kincaid_grade(text)
        fog = textstat.gunning_fog(text)

        # Display readability report
        outputs.append("\n\nREADABILITY REPORT")
        outputs.append(f"Flesch Reading Ease (FRE): {fre:.2f}")
        outputs.append(f"Flesch-Kincaid Grade (FK): {fk:.2f}")
        outputs.append(f"Gunning Fog Index (FOG): {fog:.2f}")

        # Interpret Flesch Reading Ease
        outputs.append("\n\nFlesch Reading Ease Analysis:")
        if fre > 50:
            outputs.append("  ✓ Very Easy to Read (No penalty)")
            outputs.append("  Suggestion: Sentences are short and word choice is simple. This is good for readability, but if this is an upper-level course you may want to incorporate more precise academic terminology where appropriate.")
        elif 30 < fre <= 50:
            outputs.append("  ✓ Standard - Appropriate College Level (No penalty)")
            outputs.append("  Suggestion: Sentence length and word complexity are appropriate for college students. No changes needed.")
        elif 10 < fre <= 30:
            outputs.append("  ⚠ Difficult - College Graduate Level (Penalty: -5)")
            outputs.append("  Suggestion: The score indicates long sentences or many multi-syllable words. Try shortening sentences or simplifying vocabulary so the text is easier to follow.")
            penalty -= 5
        else:
            outputs.append("  ✗ Extremely Difficult - Professional Level (Penalty: -10)")
            outputs.append("  Suggestion: The text is very dense and uses complex vocabulary. Breaking up long sentences and reducing heavy jargon will improve accessibility.")
            penalty -= 10

        # Interpret Flesch-Kincaid Grade Level
        outputs.append("\n\nFlesch-Kincaid Grade Level Analysis:")
        if fk < 12:
            outputs.append("  ✓ Below college level (No penalty)")
            outputs.append("  Suggestion: The text uses shorter sentences and simpler words. This is clear and easy to follow, but if this is an advanced course you may want to use more discipline-specific language.")
        elif 12 <= fk <= 18:
            outputs.append("  ✓ College level appropriate (No penalty)")
            outputs.append("  Suggestion: Sentence length and word choice match typical college-level writing. No changes needed.")
        else:
            outputs.append("  ✗ Postgraduate/Professional level - Too complex (Penalty: -10)")
            outputs.append("  Suggestion: The grade level suggests very long sentences or many multi-syllable words. Simplifying sentence structure or defining advanced terminology may help.")
            penalty -= 10

        # Interpret Gunning Fog Index
        outputs.append("\n\nGunning Fog Index Analysis:")
        if fog < 12:
            outputs.append("  ✓ Below college level (No penalty)")
            outputs.append("  Suggestion: This syllabus is very easy to read. You could consider adding some more advanced terminology where appropriate, but this is optional.")
        elif 12 <= fog <= 17:
            outputs.append("  ✓ College level appropriate (No penalty)")
            outputs.append("  Suggestion: Great job! The wording and complexity are appropriate for a college-level syllabus.")
        else:
            outputs.append("  ✗ Postgraduate/Professional level - Too complex (Penalty: -10)")
            outputs.append("  Suggestion: The writing is highly complex. Consider shortening long sentences or simplifying vocabulary to make the material easier for students.")
            penalty -= 10

        return penalty

    # Content Analysis
    required_sections = {
        "Contact Information": "email address contact information @psu.edu",
        "Course Materials": "required textbooks course materials readings references",
        "Course Content and Expectations": "course outcomes objective goal expectations",
        "Location and Meeting Times": "location meeting times class schedule room building",
        "Course Goals and Objectives": "course objectives learning objectives goals",
        "Grade Breakdown": "grading policy grade distribution grading scale",
        "Examination Policy": "exams tests quizzes assessment",
        "Academic Integrity Statement": "academic integrity academic honesty plagiarism cheating",
        "Counseling Services": "counseling services mental health student support wellness",
        "Disability Resources": "disability resources impairment adjustment accommodation ADA",
        "Educational Equity Statement": "equity diversity inclusion accessibility accommodations non-discrimination",
        "Campus Closure Policy": "campus closed closure weather emergency snow cancellation"
    }

    # Recommendations for missing sections
    section_recommendations = {
        "Contact Information": "Contact information for all course instructors (including undergraduate or graduate assistants), such as email or phone numbers.",
        "Course Materials": "List all required textbooks, readings, and course materials.",
        "Course Content and Expectations": "A minimum of 80% of the core content and learning objectives approved by Faculty Senate must be included in the most current course proposal.",
        "Location and Meeting Times": "Include the classroom location, building name/number, and meeting days/times for the course.",
        "Course Goals and Objectives": "Course Goals describe the broad knowledge domains and expectations for the course. Course Objectives align with course goals, but are more explicit and represent behaviors,skills, or attitudes that students will learn and demonstrate in the course; objectives are assessed through class activities, assignments, examinations, and/or projects.",
        "Grade Breakdown": "Provide a clear breakdown of how final grades are calculated, and pertain to what letter grade.",
        "Examination Policy": "The course exam policy should include the dates, times and locations of all exams. The syllabus should also note if exams will be administered outside of class time.",
        "Academic Integrity Statement": "Include Penn State's academic integrity policy and consequences for violations like plagiarism.",
        "Counseling Services": "Provide information about campus counseling and psychological services (CAPS) for student mental health support.",
        "Disability Resources": "Information on procedures related to academic adjustments identified by Student Disability Resources.",
        "Educational Equity Statement": "Provide information related to reporting educational bias through the report bias site.",
        "Campus Closure Policy": "Explain procedures for class cancellations due to weather, emergencies, or other campus closures."
    }

    # Calculate readability penalty
    penalty = rate_readability(sentences)

    # Initialize score
    score = 0
    threshold = 0.05

    # Analyze required sections
    outputs.append("\n\nCONTENT ANALYSIS REPORT")
    results = {}

    for section, query in required_sections.items():
        # Compare query to all sentences
        scores = model.predict(
            [(query.lower(), s.lower()) for s in sentences],
            show_progress_bar=False
        )

        # Convert to probabilities
        probs = 1 / (1 + np.exp(-scores))

        # Get top result
        query_results = list(zip(sentences, probs))
        query_results.sort(key=lambda x: x[1], reverse=True)

        best_sentence, best_score = query_results[0]
        found = best_score >= threshold

        results[section] = {
            "found": found,
            "score": best_score,
            "sentence": best_sentence
        }

        status = "✓ Found" if found else "✗ Not Found"
        outputs.append(f"{section:<35} {status:<12}")

        if found:
            score += 10

    # Summary
    missing = [sec for sec, r in results.items() if not r["found"]]
    found_ok = [sec for sec, r in results.items() if r["found"]]
    total_score = score + penalty

    outputs.append("\n\nFINAL SUMMARY")
    outputs.append(f"Content Score: {score} points ({len(found_ok)}/{len(required_sections)} sections found)")
    outputs.append(f"Readability Penalty: {penalty} points")
    outputs.append(f"Total Score: {total_score} points")
    outputs.append("")

    if missing:
        outputs.append("Status: ⚠ INCOMPLETE")
        outputs.append("\nSections Not Found:")
        for sec in missing:
            outputs.append(f"  ✗ {sec}")
        outputs.append("\nSections Found:")
        for sec in found_ok:
            outputs.append(f"  ✓ {sec}")

        # Add recommendations for missing sections
        outputs.append("\n\nRECOMMENDATIONS FOR SECTIONS NOT FOUND")
        for sec in missing:
            outputs.append(f"\n• {sec}:")
            outputs.append(f"  → {section_recommendations[sec]}")
    else:
        outputs.append("Status: ✓ COMPLETE - All required sections found!")

    outputs.append("\nMore information about syllabus requirements can be found at: https://senate.psu.edu/faculty/syllabus-requirements/")

    return "\n".join(outputs)


def get_example_matches(file_path):
    """
    Returns example sentence matches for all required sections.
    This is a separate function so the GUI can call it optionally.
    """
    # [This would contain similar logic to extract and show examples]
    # Keeping it separate for cleaner code organization
    pass
