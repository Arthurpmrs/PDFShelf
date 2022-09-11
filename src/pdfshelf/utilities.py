def validade_isbn10(isbn: str) -> bool:
    """Checks if a number sequence is a valid ISBN-10. Ref: https://en.wikipedia.org/wiki/ISBN"""
    s = 0
    for i, char in enumerate(isbn):
        s += (10 - i) * int(char)

    if s % 11 == 0:
        is_valid = True
    else:
        is_valid = False
    
    return is_valid

def validate_isbn13(isbn: str) -> bool:
    """Checks if a number sequence is a valid ISBN-13. Ref: https://en.wikipedia.org/wiki/ISBN"""
    s = 0
    for i, char in enumerate(isbn):
        if i % 2 == 0:
            s += 1 * int(char)
        else:
            s += 3 * int(char)
    
    if s % 10 == 0:
        is_valid = True
    else:
        is_valid = False

    return is_valid