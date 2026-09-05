# -*- coding: utf-8 -*-
import os, re, json

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_work", "extracted", "com.sparrowwallet.sparrow", "com", "sparrowwallet", "sparrow")
dpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "翻译字典", "fxml_trans.json")
with open(dpath, encoding="utf-8") as fh:
    TRANS = json.load(fh)

# sort keys by length desc so longer strings match first (avoid partial overlap in content nodes)
keys = sorted(TRANS.keys(), key=len, reverse=True)

def repl_in_attr(m):
    val = m.group(2)
    return m.group(1) + val + m.group(3)

total_repl = 0
files_done = 0
for root, dirs, fs in os.walk(base):
    for f in fs:
        if not f.endswith(".fxml"):
            continue
        path = os.path.join(root, f)
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
        orig = txt
        # 1) strip comment blocks (save them, re-append at end)
        comments = re.findall(r'<!--.*?-->', txt, flags=re.S)
        txt_nc = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
        # 2) replace text="X", promptText="X", helpText="X"
        for attr in ("text", "promptText", "helpText"):
            def do_attr(m, _attr=attr):
                val = m.group(1)
                if val in TRANS:
                    return _attr + '="' + TRANS[val] + '"'
                return m.group(0)
            pat = re.compile(r'\b' + attr + r'="([^"]*)"')
            txt_nc = pat.sub(do_attr, txt_nc)
        # 3) replace visible content >X< (exact full text nodes only)
        def do_content(m):
            inner = m.group(1)
            if inner in TRANS:
                return '>' + TRANS[inner] + '<'
            return m.group(0)
        pat2 = re.compile(r'>([^<>]*[A-Za-z][^<>]*)<')
        txt_nc = pat2.sub(do_content, txt_nc)
        # re-append comments at end (keeps file valid, comments not functional)
        if comments:
            txt_nc = txt_nc + "\n" + "\n".join(comments)
        if txt_nc != orig:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(txt_nc)
            files_done += 1
            print("updated:", os.path.relpath(path, base))

print("files updated:", files_done)
