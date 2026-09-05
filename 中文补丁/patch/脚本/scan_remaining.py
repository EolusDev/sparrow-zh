# -*- coding: utf-8 -*-
import re, os
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_work", "extracted", "com.sparrowwallet.sparrow")
seen = {}
for dirpath, dirs, files in os.walk(root):
    for fn in files:
        if not fn.endswith(".class"):
            continue
        p = os.path.join(dirpath, fn)
        data = open(p, "rb").read()
        s = data.decode("utf-8", "ignore")
        pat = re.compile(r"[A-Za-z][A-Za-z0-9 .\-_()'\"!?,]{5,}")
        for m in pat.finditer(s):
            t = m.group().strip()
            if re.search(r"[A-Za-z]{2,}[A-Z]{2,}", t):
                continue  # CamelCase idents
            if re.search(r"\b(com\.|org\.|java\.|javafx\.|class |public |static |void |return |import |package |interface |extends |implements |throw new|this\.|new [A-Z])", t):
                continue
            words = t.split()
            if len(words) < 2:
                continue
            if not re.search(r"[a-z]{2,}", t):
                continue
            seen[t] = seen.get(t, 0) + 1
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_work", "remaining_english.txt"), "w", encoding="utf-8") as f:
    for k in sorted(seen, key=lambda x: -seen[x]):
        f.write("%d\t%s\n" % (seen[k], k))
print("total distinct:", len(seen))
