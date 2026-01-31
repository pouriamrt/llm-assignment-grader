# Stretchy words - count words that can be extended to match S


def count_stretchy(s, words):
    total = 0
    for w in words:
        if can_extend(s, w):
            total += 1
    return total


def can_extend(s, w):
    i, j = 0, 0
    while i < len(s) and j < len(w):
        if s[i] != w[j]:
            return False
        # count run in s
        run_s = 0
        c = s[i]
        while i < len(s) and s[i] == c:
            run_s += 1
            i += 1
        run_w = 0
        while j < len(w) and w[j] == c:
            run_w += 1
            j += 1
        if run_w != run_s and (run_s < 3 or run_w > run_s):
            return False
    return i == len(s) and j == len(w)


# Example: S = "heeellooo", words = ["hello", "hi", "helo"] -> 1
print(count_stretchy("heeellooo", ["hello", "hi", "helo"]))
