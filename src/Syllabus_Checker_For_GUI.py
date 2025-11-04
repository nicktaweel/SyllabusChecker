from pypdf import PdfReader
import os
from rapidfuzz import fuzz
from sentence_transformers import CrossEncoder
import re
import numpy as np
import textstat


def check_syllabus(file_path, query):
    outputs = []

    if not os.path.isfile(file_path):
        outputs.append("Error: The file does not exist.")
    elif not file_path.lower().endswith(".pdf"):
        outputs.append("Error: Only PDF files are accepted.")
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
            outputs.append("Warning: Unexpected filename format.")
            course = instructor = semester = None

        # save into variables for now cause i wanna use the instructor variable to find and fully print instructor name, so we get first name
        # by using the last name we save here, to solve the Janghoon Yang / Yi Yang problem
        outputs.append(f"COURSE: {course}, INSTRUCTOR: {instructor}, SEMESTER: {semester}")

        reader = PdfReader(file_path)
        all_text = ""
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                all_text += text + "\n"
            else:
                all_text += f"\n--- Page {i} ---\n[No Text Found]\n"

        # Load cross-encoder model
        outputs.append("\nLoading sentence transformer model...")
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

        # Split text into sentences
        sentences = [
            s.strip()
            for s in re.split(r'(?<=[.!?])\s+|\n+', all_text)  # adjusted to split on new lines
            if (len(s.split()) > 3 and re.search(r"[A-Za-z]{3,}", s))
            # filters out less than 3 word sentences and single standing letters/numbers of 3 characters or less
        ]

        # ==============================================================================================================================#

        # function for rating readability
        # package used is textstat -- basically a package that performs statistics on text
        # source used: https://pypi.org/project/textstat/
        def rate_readability(sentences):

            # uses the pre-extracted "sentences" list from the syllabus to calculate various readability metrics and print a simple summary
            # combine all sentences back into one text block for scoring
            text = " ".join(sentences).strip()

            # use penalty (will be added to score, so negative penalty will decrease score)
            penalty = 0

            # using the various functions availiable within the package for rating readability
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
            outputs.append("\n------------------Readability Report-------------------")
            outputs.append(f"Flesch Reading Ease (FRE): {fre:.2f}")
            outputs.append(f"Flesch-Kincaid Grade (FK): {fk:.2f}")
            outputs.append(f"Gunning Fog Index (FOG): {fog:.2f}")

            # interpret and explain the scores

            # results from flesch reading ease
            outputs.append("\n" + "=" * 50)
            outputs.append("Results from flesch-reading-ease:")
            if fre > 70:
                outputs.append("Reading Ease: Very Easy to Read")
            elif fre <= 70 and fre > 40:
                outputs.append("Reading Ease: Standard (Appropriate College Level)")
            elif fre <= 40 and fre > 10:
                outputs.append("Reading Ease: Difficult (College Graduate Level)")
                penalty -= 5
            else:
                outputs.append("Reading Ease: Extremely Difficult (Professional level)")
                penalty -= 10

            # results from flesch-kincaid
            # source used for grading system: https://readable.com/readability/flesch-reading-ease-flesch-kincaid-grade-level/
            outputs.append("\n" + "=" * 50)
            outputs.append("Results from flesch-kincaid:")
            if fk < 12:
                outputs.append("Grade level is below appropriate level. No penalty issued.")
            elif 12 <= fk <= 16:
                outputs.append("College level appropriate.")
            else:
                outputs.append("Postgraduate/Professional level. Too complex")
                penalty -= 10

            # results from gunning fog formula
            outputs.append("\n" + "=" * 50)
            outputs.append("Results from gunning fog formula:")
            if fog < 12:
                outputs.append("Grade level is below appropriate level. No penalty issued.")
            elif 12 <= fog <= 16:
                outputs.append("College level appropriate.")
            else:
                outputs.append("Postgraduate/Professional level. Too complex")
                penalty -= 10

            return penalty #return the penalty score

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

        # set score to 0
        score = 0

        # compue penalty readability score
        penalty = rate_readability(sentences)

        # Define similarity threshold
        threshold = 0.05

        # Analyze each section
        outputs.append("\n--- Content Analysis Report ---")
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
            outputs.append(f"{section.title()}: {status} (score = {best_score:.2f})")

            if found:
                score += 10

        # NEW SUMMARY BEHAVIOR
        missing = [sec for sec, r in results.items() if not r["found"]]
        found_ok = [sec for sec, r in results.items() if r["found"]]

        if missing:
            outputs.append("\nResult: FAIL")
            outputs.append("Required sections (missing first): ")
            # missing first labeled with "X"
            for sec in missing:
                outputs.append(f"\t X {sec.title()}")
            # then found with a checkmark
            for sec in found_ok:
                outputs.append(f"\t ✓ {sec.title()}")
        else:
            total = score + penalty
            outputs.append(f"\nOverall Score: {total:.2f}: PASS")

        # ======================================================================================================#
        # rate readability right after content analysis report
        rate_readability(sentences)
        # ======================================================================================================#
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

    return "\n".join(outputs)
