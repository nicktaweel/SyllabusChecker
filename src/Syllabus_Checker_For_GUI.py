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

        # Scores
        fre = textstat.flesch_reading_ease(text)
        fk = textstat.flesch_kincaid_grade(text)
        fog = textstat.gunning_fog(text)

        # more forgiving bounds so we do not over-flag syllabi as "difficult"
        # FRE: (easy_threshold, ideal_min, warn_min)
        # FK:  (ideal_min, ideal_max)
        # FOG: (ideal_min, ideal_max)
        LEVEL = {
            0: {"FRE": (65, 40, 25), "FK": (9, 16), "FOG": (8, 16)},
            1: {"FRE": (60, 30, 25), "FK": (10, 18), "FOG": (10, 18)},
            2: {"FRE": (60, 35, 20), "FK": (10, 20), "FOG": (10, 20)},
            3: {"FRE": (50, 30, 10), "FK": (11, 22), "FOG": (10, 22)},
            4: {"FRE": (40, 10, 0),  "FK": (12, 25), "FOG": (10, 25)}
        }

        fre_easy, fre_pref, fre_warn = LEVEL[level]["FRE"]
        fk_min, fk_max = LEVEL[level]["FK"]
        fog_min, fog_max = LEVEL[level]["FOG"]

        # pass/fail logic
        clarity_ok = fre >= fre_pref
        level_ok = fk_min <= fk <= fk_max
        complexity_ok = fog_min <= fog <= fog_max

        passes = sum([clarity_ok, level_ok, complexity_ok])

        # result message + color
        if passes == 3:
            overall = "GREAT! Your syllabus is clear and easy to understand."
            overall_color = "#00FF00"  # Green
        elif passes == 2:
            overall = "GOOD, BUT COULD USE SOME IMPROVEMENT."
            overall_color = "#FFFF00"  # Yellow
        else:
            overall = "NEEDS IMPROVEMENT. Some parts may be difficult for students to understand."
            overall_color = "#FF0000"  # Red

        outputs.append("\n\nREADABILITY REPORT")
        outputs.append(f"OVERALL RESULT: <color={overall_color}>{overall}</color>")

        # clarity and flow will represent flesch reading ease
        outputs.append("\nClarity and Flow:")
        outputs.append("  → Think of this as how smoothly the syllabus reads on a first pass.")

        if fre >= fre_easy:
            # Very easy – clear, but might be a bit simple for higher-level courses
            outputs.append("  ✓ What you did well:")
            outputs.append("    - Sentences are short, clear, and easy to follow.")
            outputs.append("    - Students can quickly understand what you mean.")
            outputs.append("  Suggestions:")
            outputs.append("    - If this is a higher-level course, consider adding a bit more detail or discipline-specific phrasing while keeping sentences clear.")
        elif fre_pref <= fre < fre_easy:
            # Ideal zone → only kudos, no suggestions
            outputs.append("  ✓ What you did well:")
            outputs.append("    - The syllabus flows smoothly for college readers.")
            outputs.append("    - Information is clear without feeling oversimplified or overly dense.")
            outputs.append("  Keep doing what you are doing with sentence length and flow.")
        elif fre_warn <= fre < fre_pref:
            # Slightly challenging, but not terrible
            outputs.append("  ✓ What you did well:")
            outputs.append("    - You provide detailed information that reflects the rigor of the course.")
            outputs.append("  Suggestions:")
            outputs.append("    - Shorten or split up longer sentences so each one focuses on a single idea.")
            outputs.append("    - Remove extra filler words or repeated phrases to make the text feel lighter.")
        else:  # fre < fre_warn, quite hard
            outputs.append("  ✓ What you did well:")
            outputs.append("    - The syllabus appears thorough and covers important information.")
            outputs.append("  Suggestions:")
            outputs.append("    - Break up large blocks of text with headings or bullet points.")
            outputs.append("    - Use shorter, more direct sentences for key expectations.")
            outputs.append("    - Put the most important point at the beginning of the sentence whenever possible.")

        # is it appropriate for course level? --> going to represent flesch kincaid grade
        outputs.append("\nAppropriate for Course Level:")
        outputs.append("  → Think of this as whether the reading feels like it matches a course at this level.")

        if level_ok:
            # Ideal FK range → only kudos
            outputs.append("  ✓ What you did well:")
            outputs.append("    - The reading level fits what we expect for this course level.")
            outputs.append("    - The tone feels professional while still being accessible to students.")
            outputs.append("  Keep this balance of academic language and clarity.")
        elif fk < fk_min:
            # Too simple for the level
            outputs.append("  ✓ What you did well:")
            outputs.append("    - The syllabus is very accessible and friendly to read.")
            outputs.append("  Suggestions:")
            outputs.append("    - Add a bit more academic or discipline-specific language where it helps clarify expectations.")
            outputs.append("    - Provide slightly more detail in key sections, such as major assignments or grading criteria.")
        else:  # fk > fk_max, too advanced
            outputs.append("  ✓ What you did well:")
            outputs.append("    - The writing reflects a serious, academic tone appropriate for higher education.")
            outputs.append("  Suggestions:")
            outputs.append("    - Simplify longer or highly formal sentences, especially in policy-heavy areas.")
            outputs.append("    - Make instructions and deadlines as direct and straightforward as possible.")
            outputs.append("    - Briefly define specialized terms when they first appear.")

        # word choice and complexity will represent gunning fog index
        outputs.append("\nWord Choice and Complexity:")
        outputs.append("  → Think of this as how heavy the wording feels, based on sentence length and bigger words.")

        if fog < fog_min:
            # Very simple wording
            outputs.append("  ✓ What you did well:")
            outputs.append("    - Vocabulary is straightforward and easy to understand.")
            outputs.append("    - Students can quickly grasp what you are saying without getting stuck on the wording.")
            outputs.append("  Suggestions:")
            outputs.append("    - For upper-level or writing-intensive courses, consider adding key discipline-specific terms where appropriate.")
            outputs.append("    - Make sure important concepts are described with enough precision, even while staying clear.")
        elif fog_min <= fog <= fog_max:
            # Ideal zone → only kudos
            outputs.append("  ✓ What you did well:")
            outputs.append("    - Word choice feels balanced: not too simple, but not overly dense.")
            outputs.append("    - Complex ideas are explained in a way that students can process without feeling overwhelmed.")
            outputs.append("  Keep this mix of everyday language and necessary academic terms.")
        else:  # fog > fog_max, too dense
            outputs.append("  ✓ What you did well:")
            outputs.append("    - The syllabus shows strong command of the subject and covers a lot of information.")
            outputs.append("  Suggestions:")
            outputs.append("    - Replace very long or technical words with simpler alternatives when possible.")
            outputs.append("    - Shorten dense sections and avoid packing too many ideas into a single sentence.")
            outputs.append("    - Use bullet points or numbered lists for complex rules or multi-step processes.")


        # if at most 1 test passes, then we add more overall suggestions for user.
        if passes <= 1:
            outputs.append("\nOverall Suggestions:")
            outputs.append("  • Use bullet points for key policies, deadlines, and grading details.")
            outputs.append("  • Add clear section headers so students can quickly find what they need.")
            outputs.append("  • Keep the most important rules short, direct, and easy to scan.")

        return
################################################################################################



    # Required sections (now lists of keywords instead of one long sentence)
    required_sections = {
        "Contact Information": ["instructor contact", "email"],
        "Course Materials": ["textbook", "course materials", "required texts"],
        "Course Content and Expectations": ["course content", "course expectations", "learning outcomes", "course summary"],
        "Location and Meeting Times": ["meeting times", "class meeting", "classroom location", "class time"],
        "Course Goals and Objectives": ["course goals", "course objectives", "learning objectives"],
        "Grade Breakdown": ["grade breakdown", "grading scale", "final grade percentage", "grade determination", "final grade"],
        "Examination Policy": ["examination policy", "exam policy", "makeup exam", "no makeups", "exams", "quizzes"],
        "Attendance Policy": ["attendance policy", "attendance is required", "attendance will be taken", "attend"],
        "Academic Integrity Statement": ["academic integrity", "plagiarism", "academic honesty"],
        "Counseling Services": ["counseling and psychological services"],
        "Disability Resources": ["student disability resources", "disabilities", "accommodations"],
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

    rate_readability(sentences, course_level)

    # 5. KUDOS (LAST BLOCK)
    if found_ok:
        outputs.append("\n\nKUDOS FOR SECTIONS FOUND")
        for sec in found_ok:
            outputs.append(f"\n• {sec}:")
            outputs.append(f"  ✓ {section_kudos[sec]}")

    return "\n".join(outputs)
