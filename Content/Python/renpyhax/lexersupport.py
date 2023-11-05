import renpyhax as renpy

def letterlike(c):
    if c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
        return 1
    else:
        return 0

def match_logical_word(s, pos):
    start = pos
    len_s = len(s)
    c = s[pos]

    if c in " ":
        pos += 1
        while pos < len_s:
            if not s[pos] in " ":
                break
            pos += 1
    elif letterlike(c):
        pos += 1
        while pos < len_s:
            if not letterlike(s[pos]):
                break
            pos += 1
    else:
        pos += 1

    word = s[start:pos]

    if (pos - start) >= 3 and (word[0] in '_') and (word[1] in '_'):
        magic = True
    else:
        magic = False

    return s[start:pos], magic, pos        