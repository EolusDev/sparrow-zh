# -*- coding: utf-8 -*-
"""维护工具：把 翻译字典/ 下所有分批字典统一转为“可见标记安全形态”并自检。

它兼容两种现状输入：普通 JSON，或上一版“私有区字符”安全形态（自动还原成普通
字典后再重编码），因此可重复运行、幂等。新增/修改分批字典后运行：
    python make_safe_dict.py
校验：1) 重写后文件不含反斜杠/控制字符；2) 安全还原后与原字典逐条相等；
3) 全部分批合并、剔除外部比较串黑名单后等于最终总字典；4) 标记无原文冲突。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import safe_dict as S

# 旧版“私有区字符”形态的逆映射（用于把历史中间态还原为普通字典）
PRIV_INV = {0xE001: 0x01, 0xE009: 0x09, 0xE00A: 0x0A, 0xE00D: 0x0D,
            0xE022: 0x22, 0xE05C: 0x5C}


def from_private(d):
    def dec(s):
        return "".join(chr(PRIV_INV[ord(c)]) if ord(c) in PRIV_INV else c for c in s)
    return {dec(k): dec(v) for k, v in d.items()}


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
    raw0 = json.load(open(p, encoding="utf-8"))
    orig = from_private(raw0)                       # 若是私有区形态则还原，否则不变
    clash = [k for k in orig if "@@" in k] + [v for v in orig.values() if "@@" in v]
    S.dump_safe_dict(orig, p)                       # 写可见标记安全形态
    raw = open(p, encoding="utf-8").read()
    back = S.load_json_dict(p)                      # 再读回并还原
    bs = raw.count(chr(92))
    ctrl = sum(1 for ch in raw if ord(ch) < 0x20 and ch not in "\n\r\t")
    ok = (back == orig) and bs == 0 and ctrl == 0 and not clash
    all_ok &= ok
    print("%-26s entries=%4d backslash=%d ctrl=%d clash=%d roundtrip=%s"
          % (f, len(orig), bs, ctrl, len(clash), back == orig))
    if f in JAVA_PARTS:
        merged.update(back)
for k in BLACK:
    merged.pop(k, None)

allp = os.path.join(DICT, "java_trans_all.json")
if os.path.isfile(allp):
    final = json.load(open(allp, encoding="utf-8"))
    final = from_private(final)
    print("merged java =", len(merged), " all.json =", len(final),
          " identical =", merged == final)
    all_ok &= (merged == final)
print("ALL SAFE & LOSSLESS:", all_ok)
sys.exit(0 if all_ok else 1)
