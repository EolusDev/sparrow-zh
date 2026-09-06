# -*- coding: utf-8 -*-
"""翻译字典的“安全形态”编解码工具（可见 ASCII 标记版）。

背景
----
Java 界面字面量里常含三类需要在 JSON 中转义的特殊字符：
  * MessageFormat 占位符 U+0001（Sparrow 用它代替 {0}）；
  * 换行 / 制表 / 回车等控制字符；
  * 字符串内的双引号、反斜杠。
普通 JSON 会把它们写成反斜杠转义；而无论反斜杠转义还是不可见的私有区字符，
在“文件 -> 文本通道推送 -> 再落盘”时都容易被二次转义、误删或肉眼漏过，
曾导致字典条目静默损坏。

本模块把每个特殊字符一对一替换为**可见的纯 ASCII 标记**（形如 @@X@@，正常
中英文界面文案绝不会出现），得到不含反斜杠、不含控制字符、且每个特殊位置都
肉眼可见、可被 grep 统计的“安全形态”字典；构建加载时再用 safe_decode 精确还原。

标记表（定长 5 字符，互不为子串）：
  U+0001 占位符 -> @@A@@      换行 LF -> @@N@@      制表 TAB -> @@T@@
  回车 CR -> @@R@@            双引号  -> @@Q@@      反斜杠  -> @@B@@

安全形态无损、可逆、确定；对不含特殊字符的普通字典做还原也完全无副作用，
因此 build.py 对所有字典统一走 load_json_dict 即可，无需区分形态。
"""
import json

# 真实字符码点 -> 可见 ASCII 标记
TOKEN = {
    0x01: "@@A@@",  # MessageFormat 占位符
    0x0A: "@@N@@",  # 换行 LF
    0x09: "@@T@@",  # 制表 TAB
    0x0D: "@@R@@",  # 回车 CR
    0x22: "@@Q@@",  # 双引号
    0x5C: "@@B@@",  # 反斜杠
}
# 标记 -> 真实字符码点
TOKEN_INV = {tok: cp for cp, tok in TOKEN.items()}


def safe_encode(text):
    """把字符串中的特殊字符替换为可见标记。"""
    return "".join(TOKEN[ord(c)] if ord(c) in TOKEN else c for c in text)


def safe_decode(text):
    """把可见标记还原为真实特殊字符（安全形态的逆运算）。"""
    for tok, cp in TOKEN_INV.items():
        if tok in text:
            text = text.replace(tok, chr(cp))
    return text


def encode_dict(d):
    """对整个 {英文: 中文} 字典做安全编码。"""
    return {safe_encode(k): safe_encode(v) for k, v in d.items()}


def decode_dict(d):
    """对整个字典做安全还原。"""
    return {safe_decode(k): safe_decode(v) for k, v in d.items()}


def load_json_dict(path, encoding="utf-8"):
    """读取一个 JSON 字典文件并做安全还原，返回可直接用于改写的 {str: str}。"""
    with open(path, encoding=encoding) as fh:
        data = json.load(fh)
    return decode_dict(data)


def dump_safe_dict(d, path, encoding="utf-8"):
    """把字典以安全形态（无反斜杠、UTF-8 明文、键排序）写入 JSON 文件。"""
    safe = encode_dict(d)
    with open(path, "w", encoding=encoding, newline="\n") as fh:
        json.dump(safe, fh, ensure_ascii=False, indent=0, sort_keys=True)
