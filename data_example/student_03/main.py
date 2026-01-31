"""Stretchy words counter."""


def rle(s):
    if not s:
        return []
    out = []
    ch, n = s[0], 1
    for i in range(1, len(s)):
        if s[i] == ch:
            n += 1
        else:
            out.append((ch, n))
            ch, n = s[i], 1
    out.append((ch, n))
    return out


def stretchy(S, words):
    s_rle = rle(S)
    count = 0
    for w in words:
        w_rle = rle(w)
        if len(s_rle) != len(w_rle):
            continue
        ok = True
        for k in range(len(s_rle)):
            c1, n1 = s_rle[k]
            c2, n2 = w_rle[k]
            if c1 != c2:
                ok = False
                break
            if n1 != n2 and (n1 < 3 or n2 > n1):
                ok = False
                break
        if ok:
            count += 1
    return count


if __name__ == "__main__":
    print(stretchy("heeellooo", ["hello", "hi", "helo"]))  # 1
