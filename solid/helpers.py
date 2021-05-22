import keyword
PYTHON_ONLY_RESERVED_WORDS = keyword.kwlist

def _subbed_keyword(keyword: str) -> str:
    """
    Append an underscore to any python reserved word.
    Prepend an underscore to any OpenSCAD identifier starting with a digit.
    No-op for all other strings, e.g. 'or' => 'or_', 'other' => 'other'
    """
    new_key = keyword

    if keyword in PYTHON_ONLY_RESERVED_WORDS:
        new_key = keyword + "_"

    if keyword[0].isdigit():
        new_key = "_" + keyword

    if new_key != keyword:
        print(f"\nFound OpenSCAD code that's not compatible with Python. \n"
              f"Imported OpenSCAD code using `{keyword}` \n"
              f"can be accessed with `{new_key}` in SolidPython\n")
    return new_key

def _unsubbed_keyword(subbed_keyword: str) -> str:
    """
    Remove trailing underscore for already-subbed python reserved words.
    Remove prepending underscore if remaining identifier starts with a digit.
    No-op for all other strings: e.g. 'or_' => 'or', 'other_' => 'other_'
    """
    if subbed_keyword.endswith("_") and subbed_keyword[:-1] in PYTHON_ONLY_RESERVED_WORDS:
        return subbed_keyword[:-1]

    if subbed_keyword.startswith("_") and subbed_keyword[1].isdigit():
        return subbed_keyword[1:]

    return subbed_keyword

