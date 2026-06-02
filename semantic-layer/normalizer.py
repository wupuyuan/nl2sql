from dictionary import SEMANTIC_DICT


def normalize_value(word: str):
    return SEMANTIC_DICT.get(word, word)
