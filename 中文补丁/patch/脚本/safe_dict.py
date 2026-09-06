# -*- coding: utf-8 -*-
"""翻译字典的“安全形态”编解码工具。

背景
----
Java 界面字面量里常含三类需要在 JSON 中转义的字符：
  * MessageFormat 占位符 U+0001（Sparrow 用它代替 {0}）；
  * 换行 / 制表 / 回车等控制字符；
  * 字符串内的双引号、反斜杠。
普通 JSON 会把它们写成反斜杠转义序列（如 反斜杠+u0001、反斜杠+n、
反斜杠+引号、双反斜杠）。这些反斜杠在“文件 -> 网络推送 -> 再落盘”的过程中
极易被二次转义或误删，曾导致字典条目静默损坏。

本模块把上述字符一对一映射到 Unicode 私有区（U+E0xx，正常中英文文案不会
出现），得到**完全不含反斜杠与控制字符**的“安全形态”字典：人工可读、可被
任意文本通道无损传输；构建加载时再用 :func:`safe_decode` 精确还原为真实字符。

安全形态是无损、可逆、确定的；对不含特殊字符的普通字典执行还原也完全无副作用，
因此 build.py 对所有字典统一走 :func:`load_json_dict` 即可，无需区分形态。
"""
import json

# 真实字符码点 -> 私有区码点
SAFE_MAP = {
    0x01: 0xE001,  # MessageFormat 占位符
    0x09: 0xE009,  # 制表符
    0x0A: 0xE00A,  # 换行
    0x0D: 0xE00D,  # 回车
    0x22: 0xE022,  # 双引号
    0x5C: 0xE05C,  # 反斜杠
}
SAFE_INV = {v: k for k, v in SAFE_MAP.items()}


def safe_encode(text):
    """把字符串中的特殊字符替换为私有区安全字符。"""
    return "".join(chr(SAFE_MAP[ord(c)]) if ord(c) in SAFE_MAP else c for c in text)


def safe_decode(text):
    """把私有区安全字符还原为真实特殊字符（安全形态的逆运算）。"""
    return "".join(chr(SAFE_INV[ord(c)]) if ord(c) in SAFE_INV else c for c in text)


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
