from textblob import Word

def spell_check_text(text):

    words = text.split()
    misspelled = False

    for w in words:
        word = Word(w)
        suggestions = word.spellcheck()
        correct_word, confidence = suggestions[0]

        if correct_word.lower() != w.lower():
            misspelled = True
            print(f"'{w}' might be misspelled.")
            print(f"Suggested correction: '{correct_word}'")
            print()

