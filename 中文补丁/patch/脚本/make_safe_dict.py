# -*- coding: utf-8 -*-
"""维护工具：把 翻译字典/ 下所有分批字典转为安全形态并自检。

新增/修改分批字典后运行一次即可：python make_safe_dict.py
它会把每个 JSON 重写为无反斜杠的安全形态（私有区字符），并校验：
  1) 重写后文件不含反斜杠；2) 安全还原后与原字典逐条相等；
  3) 全部分批合并、剔除外部比较串黑名单后，等于最终总字典条数与内容。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import safe_dict as S

DICT = os.path.normpath(os.path.join(HERE, "..", "翻译字典"))
FILES = ["fxml_trans.json", "java_trans.json", "java_trans2.json", "java_trans3.json",
         "java_trans_batch2.json", "java_trans_batch3.json", "java_trans_batch4.json",
         "java_trans_batch5a.json", "java_trans_batch5b.json", "java_trans_batch6.json"]
JAVA_PARTS = [f for f in FILES if f.startswith("java_trans")]
BLACK = {"min relay fee not met", "mempool min fee not met",
         "insufficient fee, rejecting replacement"}

all_ok = True
merged = {}
for f in FILES:
    p = os.path.join(DICT, f)
    orig = json.load(open(p, encoding="utf-8"))
    S.dump_safe_dict(orig, p)                       # 写安全形态
    raw = open(p, encoding="utf-8").read()
    back = S.load_json_dict(p)                      # 再读回并还原
    bs = raw.count(chr(92))
    ok = (back == orig) and bs == 0
    all_ok &= ok
    print("%-26s entries=%4d backslash=%d roundtrip=%s" % (f, len(orig), bs, back == orig))
    if f in JAVA_PARTS:
        merged.update(back)
for k in BLACK:
    merged.pop(k, None)

allp = os.path.join(DICT, "java_trans_all.json")
if os.path.isfile(allp):
    final = json.load(open(allp, encoding="utf-8"))
    print("merged java =", len(merged), " all.json =", len(final),
          " identical =", merged == final)
    all_ok &= (merged == final)
print("ALL SAFE & LOSSLESS:", all_ok)
sys.exit(0 if all_ok else 1)
