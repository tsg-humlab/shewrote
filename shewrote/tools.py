import re


def date_of_x_text_to_int(text):
    if not text:
        return None

    # First try to convert to int immediately
    try:
        int_repr = int(text)
    except ValueError:
        pass
    else:
        return int_repr

    # Strip everything until the first digit...
    text = re.sub(r'^[^\d]*', '', text)
    #  and trailing spaces
    text = re.sub(r'\s*$', '', text)

    # Match options
    if m := re.match(r'^(\d{4})[^\d]*', text):
        return int(m[1])
    if m := re.match(r'.+\-(\d{4})[^\d]*', text):
        return int(m[1])
    if m := re.match(r'^(\d\d)([xX]{2}|\.\.)$', text):
        return int(m[1]) * 100 + 50
    if m := re.match(r'^(\d\d\d)([xX]|\.|\?)$', text):
        return int(m[1]) * 10 + 5
    if m := re.match(r'(\d+)(th|nd)?\s*(century|c\.?)', text, re.IGNORECASE):
        return (int(m[1]) - 1) * 100 + 50
    if m := re.match(r'^(\d*)\s*bce$', text, re.IGNORECASE):
        return 0 - int(m[1])
    if m := re.match(r'(\d+)\-(\d+)', text):
        return int((int(m[1]) + int(m[2])) / 2)
    return None