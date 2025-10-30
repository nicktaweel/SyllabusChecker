from pypdf import PdfReader
import os
from sentence_transformers import CrossEncoder
import re
import numpy as np
#for readability: https://pypi.org/project/textstat/
import textstat


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
        for s in re.split(r'(?<=[.!?])\s+|\n+', all_text)                     # adjusted to split on new lines
        if (len(s.split()) > 3 and re.search(r"[A-Za-z]{3,}", s))             # filters out less than 3 word sentences and single standing letters/numbers of 3 characters or less
    ]


    #used as global variable
    score = 0


    #==============================================================================================================================#
#function for rating readability
    #package used is textstat -- basically a package that performs statistics on text
    #source used: https://pypi.org/project/textstat/
    def rate_readability(sentences):

        global score # <---- KEY: MUTATE THE SHARED SCORE HERE

#uses the pre-extracted "sentences" list from the syllabus to calculate various readability metrics and print a simple summary

#combine all sentences back into one text block for scoring
        text = " ".join(sentences)

#using the various functions availiable within the package for rating readability
    # --- Performing Flesch Reading Ease (FRE) --------
    # this measures how easy the syllabus is to read. higher score = easier.
    # measures the sentence and word length of the text. basically tells us how approachable a language is.\
    # this is done using a formula that is briefly covered in the wikipedia article
    # the source tells us that 50-70 is suitable for a college level -- not too easy, but not too difficult
    # we should flag anything from 30-10, lose points, and tell user that it is at a "College Graduate Level" (the source tells us this)
    # anything under 10 should be flagged and lose double points because it is "Professional Level" (again, the source tells us this)
    # please find the source i used for further research here: https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests#Flesch_reading_ease
        fre = textstat.flesch_reading_ease(text)

        # --- Performing Flesch-Kincaid Grade level (FK) ----
        # this presents a score as a U.S. grade level
        # this also uses the same components of FRE (sentence length, syllabes/word) but mapped to a grade scale
        # this is done also using a formula that is briefly covered in the wikipedia article
        # for example: 11.5 means an 11th grader would be able to read the document
        # lets aim for 10 - 13 and review what documents for scores over 14 look like.
        # source for further research: https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests#Flesch%E2%80%93Kincaid_grade_level
        fk = textstat.flesch_kincaid_grade(text)

        # --- Performing the Gunning Fog Formula -----
        # the algorithm works by determining the average sentence length (divides the number of words by the number of sentences)
        # it counts "complex" words consisting of three or more syllables (does not include proper nouns, familiar jargon, or compound words (like -es, -ed, -ing) etc.)
        # it then adds the average sentence length and the percentage of complex words and multiplies the result by 0.4
        # according to the source, we should aim for all sources between 12 (high school senior) and 16 (college senior).
        # scores below 12 should not be flagged and scores over 16 should be flagged
        # additional source used: https://en.wikipedia.org/wiki/Gunning_fog_index
        fog = textstat.gunning_fog(text)


        # now printing readability report
        print("\n------------------Readability Report-------------------")
        print(f"Flesch Reading Ease (FRE): {fre:.2f}")
        print(f"Flesch-Kincaid Grade (FK): {fk:.2f}")
        print(f"Gunning Fog Index (FOG): {fog:.2f}")


        #interpret and explain the scores

        #results from flesch reading ease
        print("\n" + "=" * 50)
        print("Results from flesch-reading-ease:")
        if fre > 70:
            print("Reading Ease: Very Easy to Read")
        elif fre <= 70 and fre > 40:
            print("Reading Ease: Standard (Appropriate College Level)")
        elif fre <= 40 and fre > 10:
            print("Reading Ease: Difficult (College Graduate Level)")
            score -= 5
        else:
            print("Reading Ease: Extremely Difficult (Professional level)")
            score -= 10

        # results from flesch-kincaid
        # source used for grading system: https://readable.com/readability/flesch-reading-ease-flesch-kincaid-grade-level/
        print("\n" + "=" * 50)
        print("Results from flesch-kincaid:")
        if fk < 12:
            print("Grade level is below appropriate level. No penalty issued.")
        elif 12 <= fk <= 16:
            print("College level appropriate.")
        else:
            print("Postgraduate/Professional level. Too complex")
            score -= 10

        # results from gunning fog formula
        print("\n" + "=" * 50)
        print("Results from gunning fog formula:")
        if fog < 12:
            print("Grade level is below appropriate level. No penalty issued.")
        elif 12 <= fk <= 16:
            print("College level appropriate.")
        else:
            print("Postgraduate/Professional level. Too complex")
            score -= 10

 # ==============================================================================================================================#
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
    threshold = 0.05

    # Analyze each section
    print("\n--- Content Analysis Report ---")
    results = {}

    for section, query in required_sections.items():
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

        # Check if found
        results[section] = {
            "found": found,
            "score": best_score,
            "sentence": best_sentence
        }

        status = "Found" if found else "Missing"
        print(f"{section.title()}: {status} (score = {best_score:.2f})")

        if found:
            score += 10

    # NEW SUMMARY BEHAVIOR
    missing = [sec for sec, r in results.items() if not r["found"]]
    found_ok = [sec for sec, r in results.items() if r["found"]]

    if missing:
        print("\nResult: FAIL")
        print("Required sections (missing first): ")
        #missing first labeled with "X"
        for sec in missing:
            print(f"\t X {sec.title()}")
        #then found with a checkmark
        for sec in found_ok:
            print(f"\t ✓ {sec.title()}")
    else:
        print(f"\nOverall Score: {score:.2f}: PASS")

# ======================================================================================================#
#rate readability right after content analysis report
    rate_readability(sentences)
#======================================================================================================#
    # Show example matches for ALL sections (even ones that fail threshold)
    show_examples = input("\nShow example matches for all sections? (y/n): ").strip().lower()
    if show_examples == 'y':
        print("\n--- Example Matches ---")
        for section, result in results.items():
            print(f"\n{section.title()} (score = {result['score']:.2f}):")
            print(f"  {result['sentence']}")

    # Custom query search (idk we can cut)
    print("\n" + "=" * 50)
    answer = input("\nWould you like to search for a phrase? (y/n): ").strip().lower()
    if answer == 'y':
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
