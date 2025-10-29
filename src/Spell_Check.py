from spellchecker import SpellChecker

def spell_check_text(text):

    words = text.split()
    misspelled = False
    misspelled_word_cnt = 0
    spell = SpellChecker()
    misspelled_words = spell.unknown(words)

    for word in misspelled_words:
        print(f"{word} may have been spelled incorrectly, did you mean {spell.correction(word)}?")
        misspelled_word_cnt += 1

    words_spelt_correctly = len(words) - misspelled_word_cnt
    score = words_spelt_correctly / len(words)
    return score



