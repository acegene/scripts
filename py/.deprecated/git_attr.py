from collections import OrderedDict


def is_alpha(char: str) -> bool:
    assert len(char) == 1
    # fmt: off
    low = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    upper = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    # fmt: on
    if char in low or char in upper:
        return True
    return False


lines: OrderedDict = OrderedDict()
with open(".gitattributes", "r", encoding="utf-8") as f:
    for line in f.readlines():
        if len(line) == 0:
            print("ERROR")
            continue
        if line[0] == "#":
            lines[line.strip("\n")] = None
            # lines.add(line.strip("\n"))
            # print(f"{line}", end="")
            continue
        line_split = line.split()
        line_split_insensitive = line_split
        line_split_first_word = ""
        for i, char in enumerate(line_split[0]):
            if is_alpha(char):
                char_upper = char.upper()
                char_lower = char.lower()
                line_split_first_word += "[" + char_lower + char_upper + "]"
            else:
                line_split_first_word += char
        line_split_insensitive[0] = line_split_first_word
        line_key = " ".join(line_split_insensitive)
        lines[line_key] = None

        # lines.add(" ".join(line_split_insensitive))
for l in lines.keys():
    print(l)
# print("\n".join(lines))
