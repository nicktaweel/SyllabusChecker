from pypdf import PdfReader
from spellchecker import SpellChecker
import re

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def check_spelling(text):
    spell = SpellChecker()

    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]*\b", text)
    checked = set()
    flagged = []

    for word in words:
        w = word.strip()

        if w.lower() in checked:
            continue
        checked.add(w.lower())

        # Filtering
        if (
            len(w) <= 2               # too short
            or w.isupper()            # all caps
            or w[0].isupper()         # proper noun
            or re.search(r"\d", w)    # has numbers
            or re.match(r"^(http|www|edu|com|org|net)", w.lower())  # URLs
            or "-" in w               # compound words
        ):
            continue

        # Spell Check
        if w.lower() not in spell:
            suggestions = spell.candidates(w)
            flagged.append((w, suggestions))

    # Display results
    for word, suggestions in flagged:
        print(f"Misspelled: {word} -> Suggestions: {', '.join(suggestions) if suggestions else 'None'}")

    print(f"\nTotal possible misspelled words: {len(flagged)}")


if __name__ == "__main__":
    pdf_path = ""
    text = extract_text_from_pdf(pdf_path)
    check_spelling(text)



