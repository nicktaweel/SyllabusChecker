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
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

#split into sentences
    raw_chunks = re.split(r'(?<=[.!?])\s+|\n+', all_text)
    sentences = [
        s.strip()
        for s in raw_chunks
        if (len(s.split()) >= 2 and re.search(r"[A-Za-z]{3,}", s))
    ]

    # derive course_level from the existing parse
    # normalize course numbers so that "83" becomes "083" etc.

    def normalize_course_num(num):
        # Pad course numbers to 3 digits
        digits = re.findall(r"\d+", num)
        if not digits:
            return None
        return digits[0].zfill(3)

    # Case A: CMPSC_303_* ->  parts[1] contains number
    if len(parts) >= 4 and parts[1] and parts[1][0].isdigit():
        raw_num = parts[1]  # e.g., "303", "83", "201E"
        course_num = normalize_course_num(raw_num)

    # Case B: ENG.202 or ENGL.83S
    elif course != "Unknown":
        m = re.search(r'^[A-Za-z]{2,}\.(\d+)', course)
        if not m:
            raise ValueError(
                f"Filename pattern present but level missing in course token '{course}'. "
                "Expected like 'ENG.202' or 'CMPSC.303'."
            )
        course_num = normalize_course_num(m.group(1))

    else:
        raise ValueError(
            f"ERROR: The entered PDF '{file_name}'. is either not a syllabus or is not in the correct file format. Please review PDF and re-upload."
        )

    if course_num is None:
        raise ValueError(
            f"Could not extract numeric course digits from '{file_name}'.")

    # Determine course level from normalized number
    # 083 - first digit = 0 - treat as 1 (100-level)
    level_char = int(course_num[0])

    # convert to an integer, and if its not part of the level dict, throw error
    course_level = int(level_char)
    if course_level not in (0, 1, 2, 3, 4):
        raise ValueError(
            f"Unsupported course level '{course_level}' in '{file_name}'. "
            "Expected 0–4 (e.g., BIO_004, ENG.101, CMPSC_203, ENGL.302, CMPSC_463)."
        )

    # Readability Analysis
    def rate_readability(sentences, level):
        # calculates readability and then deducts points form score. we can change later just how i decided to implement for now.
        text = " ".join(sentences).strip()
        penalty = 0

        # Calculate metrics
        fre = textstat.flesch_reading_ease(text)
        fk = textstat.flesch_kincaid_grade(text)
        fog = textstat.gunning_fog(text)

        # dictionary to hold the different range values for readability based on course level
        LEVEL = {
            # fre uses tuple, first value is the value we set as the "easy" threshold
            # second is our perfect spot
            # anything lower than third is issued a penalty
            # FK_MIN is our threshold for easy flesch kincaid
            # FK_MAX is our limit for flesch kincaid
            # FOG_MIN is our threshold for easy gunning fog
            # FOG_MAX is our limit for gunning fog
            0: {"FRE": (60, 30, 25), "FK": (12, 16), "FOG": (10, 16)},
            1: {"FRE": (60, 30, 25), "FK": (12, 16), "FOG": (10,16)}, # for like eng 101
            2: {"FRE": (60, 30, 20), "FK": (12, 18), "FOG": (12,18)},
            3: {"FRE": (50, 30, 10), "FK": (12, 20), "FOG": (12,20)},
            4: {"FRE": (40, 10, 0), "FK": (12, 25), "FOG": (12, 25)}
        }

        fre_easy, fre_pref, fre_warn = LEVEL[level]["FRE"]
        fk_min, fk_max = LEVEL[level]["FK"]
        fog_min, fog_max = LEVEL[level]["FOG"]

        # Interpret Flesch Reading Ease (FRE)
        outputs.append("\n\nFlesch Reading Ease (FRE):")
        outputs.append("  → This test measures how easy your syllabus is to read. "
                       "Higher scores mean simpler, more approachable language.")

        if fre >= fre_easy:
            outputs.append("  ✓ Very easy to read (No penalty)")
            outputs.append("  What you did well:")
            outputs.append("    - Sentences are concise and easy to follow.")
            outputs.append("    - The writing tone feels friendly and direct without unnecessary jargon.")
            outputs.append("    - Sections are likely short and well-spaced, making the syllabus comfortable to skim.")
            outputs.append("  What you could improve on:")
            outputs.append("    - For upper-level courses, consider incorporating more discipline-specific vocabulary where appropriate.")
            outputs.append("    - Keep the structure clear but add slightly more technical depth if the content allows.")
        elif fre_pref <= fre < fre_easy:
            outputs.append("  ✓ Comfortable for college readers (No penalty)")
            outputs.append("  What you did well:")
            outputs.append("    - The tone and structure are balanced for most college students.")
            outputs.append("    - Important information like grading or due dates is likely placed in accessible sections.")
            outputs.append("    - The syllabus reads naturally, without being too casual or too formal.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Keep paragraphs short and focused on one idea at a time.")
            outputs.append("    - Use consistent headers and bullets to help students locate policies or deadlines faster.")
        elif fre_warn < fre < fre_pref:
            outputs.append("  ⚠ Slightly challenging (Penalty: -5)")
            outputs.append("  What you did well:")
            outputs.append("    - The writing maintains an academic tone suited for the subject matter.")
            outputs.append("    - Most sentences appear complete and grammatically correct.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Shorten long sentences or divide them into two for clarity.")
            outputs.append("    - Replace complex or abstract phrasing with direct, action-oriented language.")
            outputs.append("    - Add bullet lists or subheadings for key sections like assignments or grading.")
            penalty -= 5
        else:  # fre <= fre_warn
            outputs.append("  ✗ Hard to read (Penalty: -10)")
            outputs.append("  What you did well:")
            outputs.append("    - The syllabus likely conveys all required information thoroughly.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Simplify the sentence structure and remove filler words.")
            outputs.append("    - Break long paragraphs into shorter ones with clear headings.")
            outputs.append("    - Avoid heavy academic wording that could confuse students.")
            outputs.append("    - Use bullets or numbered lists to improve readability and organization.")
            penalty -= 10

        # Interpret Flesch-Kincaid Grade Level (FK)
        outputs.append("\n\nFlesch–Kincaid Grade Level (FK):")
        outputs.append("  → This test converts your text’s difficulty into a U.S. school grade level. "
                       "A higher number means a more advanced reading level.")

        if fk < fk_min:
            outputs.append("  ✓ Easy to follow (No penalty)")
            outputs.append("  What you did well:")
            outputs.append("    - The syllabus is written in plain, accessible language suitable for a wide range of students.")
            outputs.append("    - Instructions and expectations are straightforward and easy to understand.")
        elif fk_min <= fk <= fk_max:
            outputs.append("  ✓ Matches course expectations (No penalty)")
            outputs.append("  What you did well:")
            outputs.append("    - The tone balances professionalism with accessibility.")
            outputs.append("    - Sentences likely contain enough detail to clarify expectations without overcomplicating them.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Keep directions action-oriented (e.g., “Submit by Friday” instead of “Submissions should be made by Friday”).")
            outputs.append("    - Limit multi-clause sentences and maintain consistent tense throughout.")
        else:  # fk > fk_max
            outputs.append("  ✗ Too advanced for most students (Penalty: -10)")
            outputs.append("  What you did well:")
            outputs.append("    - The writing demonstrates a strong academic tone and attention to detail.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Simplify clause-heavy sentences and use direct verbs instead of nominalized phrases (e.g., “evaluation of” → “evaluate”).")
            outputs.append("    - Reduce technical jargon or define it briefly where necessary.")
            outputs.append("    - Reorder long sentences so the action appears near the beginning.")
            penalty -= 10

        # Interpret Gunning Fog Index (FOG)
        outputs.append("\n\nGunning Fog Index (FOG):")
        outputs.append("  → This test estimates how many years of education a reader needs to understand the text. "
                       "Higher scores mean denser or more complex language.")

        if fog < fog_min:
            outputs.append("  ✓ Very easy to understand (No penalty)")
            outputs.append("  What you did well:")
            outputs.append("    - The syllabus is straightforward and free of unnecessary complexity.")
            outputs.append("    - Students can likely locate and understand essential information with minimal effort.")
            outputs.append("  What you could improve on:")
            outputs.append("    - If this is an upper-level course, introduce concise technical terms to align with subject expectations.")
            outputs.append("    - Ensure any added detail still maintains clarity and directness.")
        elif fog_min <= fog <= fog_max:
            outputs.append("  ✓ On target for your course (No penalty)")
            outputs.append("  What you did well:")
            outputs.append("    - The syllabus is appropriately detailed without being overly wordy.")
            outputs.append("    - Complex information is likely presented in clear, digestible segments.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Continue balancing academic vocabulary with plain explanations.")
            outputs.append("    - Use bullet lists, tables, or spacing to visually separate dense information.")
        else:  # fog > fog_max
            outputs.append("  ✗ Too complex or dense (Penalty: -10)")
            outputs.append("  What you did well:")
            outputs.append("    - The writing conveys expertise and comprehensive coverage of the course.")
            outputs.append("  What you could improve on:")
            outputs.append("    - Shorten long sentences and avoid excessive multi-syllabic words.")
            outputs.append("    - Simplify nested clauses and use punctuation strategically to improve pacing.")
            outputs.append("    - Rework dense paragraphs into shorter, clearly labeled sections so students can skim key information.")
            penalty -= 10

        return penalty

    # Required sections (now lists of keywords instead of one long sentence)
    required_sections = {
        "Contact Information": ["instructor contact", "email"],
        "Course Materials": ["textbook", "course materials", "required texts"],
        "Course Content and Expectations": ["course content", "course expectations", "learning outcomes", "course summary"],
        "Location and Meeting Times": ["meeting times", "class meeting", "classroom location", "class time"],
        "Course Goals and Objectives": ["course goals", "course objectives", "learning objectives"],
        "Grade Breakdown": ["grade breakdown", "grading scale", "final grade percentage", "grade determination", "final grade"],
        "Examination Policy": ["examination policy", "exam policy", "makeup exam", "no makeups"],
        "Attendance Policy": ["attendance policy", "attendance is required", "attendance will be taken"],
        "Academic Integrity Statement": ["academic integrity", "plagiarism", "academic honesty"],
        "Counseling Services": ["counseling and psychological services"],
        "Disability Resources": ["student disability resources"],
        "Educational Equity Statement": ["educational equity", "diversity and inclusion", "report bias"],
        "Campus Closure Policy": ["campus closure", "class cancellation"]
    }

    # Recommendations for missing sections
    section_recommendations = {
        "Contact Information": "Contact information for all course instructors (including undergraduate or graduate assistants), such as email or phone numbers.",
        "Course Materials": "List all required textbooks, readings, and course materials.",
        "Course Content and Expectations": "The content of this course, and the expectations of what a student should know / be able to do at its conclusion should be featured in detail.",
        "Location and Meeting Times": "Include the classroom location, building name/number, and meeting days/times for the course.",
        "Course Goals and Objectives": "Course Goals describe the broad knowledge domains and expectations for the course. Course Objectives align with course goals, but are more explicit and represent behaviors,skills, or attitudes that students will learn and demonstrate in the course; objectives are assessed through class activities, assignments, examinations, and/or projects.",
        "Grade Breakdown": "Provide a clear breakdown of how final grades are calculated, and pertain to what letter grade.",
        "Examination Policy": "The course exam policy should include the dates, times and locations of all exams. The syllabus should also note if exams will be administered outside of class time.",
        "Attendance Policy": "Clearly state your attendance expectations, including how absences affect grades, whether excused absences are allowed, and the procedure for notifying you of absences.",
        "Academic Integrity Statement": "Include Penn State's academic integrity policy and consequences for violations like plagiarism.",
        "Counseling Services": "Provide information about campus counseling and psychological services (CAPS) for student mental health support.",
        "Disability Resources": "Information on procedures related to academic adjustments identified by Student Disability Resources.",
        "Educational Equity Statement": "Provide information related to reporting educational bias through the report bias site.",
        "Campus Closure Policy": "Explain procedures for class cancellations due to weather, emergencies, or other campus closures."
    }

    # Kudos messages for found sections
    section_kudos = {
        "Contact Information": "Great! Students will be able to easily reach you with questions or concerns.",
        "Course Materials": "Excellent! Students know exactly what materials they need to purchase or access.",
        "Course Content and Expectations": "Well done! Students have a clear understanding of what the course covers and what's expected of them.",
        "Location and Meeting Times": "Perfect! Students know where and when to show up for class.",
        "Course Goals and Objectives": "Fantastic! Clear learning objectives help students understand what they'll achieve in this course.",
        "Grade Breakdown": "Excellent! Students can see exactly how their performance will be evaluated.",
        "Examination Policy": "Great job! Students know what to expect regarding exams and assessments.",
        "Attendance Policy": "Well done! Students understand your expectations regarding attendance and absences.",
        "Academic Integrity Statement": "Excellent! This sets clear expectations about academic honesty and ethical behavior.",
        "Counseling Services": "Thank you for including this! Students now know where to find mental health support.",
        "Disability Resources": "Great! Students with disabilities know how to request accommodations.",
        "Educational Equity Statement": "Wonderful! This promotes an inclusive and welcoming learning environment.",
        "Campus Closure Policy": "Good thinking! Students know what to do if campus closes unexpectedly."
    }


    # 1. CONTENT ANALYSIS (FIRST BLOCK)
    outputs.append("\n\nCONTENT ANALYSIS REPORT")

    score = 0
    threshold = 0.4
    results = {}


    # fix to find keywords and to always add or sub if found, not found
    for section, keywords in required_sections.items():


        best_score = 0
        best_sentence = ""
        found = False

        for kw in keywords:
            scores = model.predict([(kw.lower(), s.lower()) for s in sentences], show_progress_bar=False)
            probs = 1 / (1 + np.exp(-scores))

            # find best match for this keyword
            sentence, prob = sorted(zip(sentences, probs), key=lambda x: x[1], reverse=True)[0]

            if prob > best_score:
                best_score = prob
                best_sentence = sentence

        found = best_score >= threshold  # use section-specific threshold

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
    total_score = score

    # 3. FINAL SUMMARY (SECOND BLOCK)
    if total_score >= 120:
        grade = "EXCELLENT"
        grade_color = "#00FF00"  # Green
    elif total_score >= 100:
        grade = "GREAT"
        grade_color = "#00FF00"  # Green
    elif total_score >= 80:
        grade = "GOOD"
        grade_color = "#00FF00"  # Green
    elif total_score >= 60:
        grade = "ADEQUATE"
        grade_color = "#00FF00"  # Green
    else:
        grade = "INCOMPLETE"
        grade_color = "#FF0000"  # Red

    outputs.append("\n\nFINAL SUMMARY")
    outputs.append(f"GRADE: <color={grade_color}>{grade}</color>")
    outputs.append("")

    if missing:
        outputs.append("\nSections Not Found:")
        for sec in missing:
            outputs.append(f"  ✗ {sec}")
        outputs.append("\nSections Found:")
        for sec in found_ok:
            outputs.append(f"  ✓ {sec}")

    # 4. RECOMMENDATIONS (THIRD BLOCK)
    if missing:
        outputs.append("\n\nRECOMMENDATIONS FOR SECTIONS NOT FOUND")
        for sec in missing:
            outputs.append(f"\n• {sec}:")
            outputs.append(f"  → {section_recommendations[sec]}")

    # 2. READABILITY REPORT (FOURTH BLOCK — PRINTED HERE)

    penalty = rate_readability(sentences, course_level)

    # 5. KUDOS (LAST BLOCK)
    if found_ok:
        outputs.append("\n\nKUDOS FOR SECTIONS FOUND")
        for sec in found_ok:
            outputs.append(f"\n• {sec}:")
            outputs.append(f"  ✓ {section_kudos[sec]}")

    return "\n".join(outputs)
