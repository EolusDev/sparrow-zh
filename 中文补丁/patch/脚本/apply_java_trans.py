# -*- coding: utf-8 -*-
"""把中文翻译字典应用到解包后的 sparrow 模块 .class 文件。

只替换 CONSTANT_Utf8 里的字符串字面量（绝不动被类名/字段/方法/描述符
引用的常量），并在字节长度变化后重建常量池、重写 class 文件。

既可作为脚本直接运行（使用默认相对路径），也可被 build.py 以
apply(module_dir, dict_path) 形式调用。
"""
import os
import sys
import json
import struct
import io
import pathlib

TAG_Utf8 = 1; TAG_Int = 3; TAG_Float = 4; TAG_Long = 5; TAG_Double = 6
TAG_Class = 7; TAG_String = 8; TAG_Fieldref = 9; TAG_Methodref = 10
TAG_InterfaceMethodref = 11
TAG_NameAndType = 12; TAG_MethodHandle = 15; TAG_MethodType = 16
TAG_Dynamic = 17; TAG_InvokeDynamic = 18
TAG_Module = 19; TAG_Package = 20


def parse_class(data):
    """返回 (slots, 常量池结束偏移)。slots: 常量池槽位 -> (tag, payload)。"""
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("bad magic")
    off = 8
    cp_count = struct.unpack(">H", data[off:off + 2])[0]; off += 2
    slots = {}
    i = 1
    while i < cp_count:
        tag = data[off]
        off += 1
        if tag == TAG_Utf8:
            ln = struct.unpack(">H", data[off:off + 2])[0]; off += 2
            payload = data[off:off + ln]; off += ln
            slots[i] = (tag, payload)
        elif tag in (TAG_Class, TAG_String, TAG_MethodType, TAG_Module, TAG_Package):
            slots[i] = (tag, data[off:off + 2]); off += 2
        elif tag in (TAG_Fieldref, TAG_Methodref, TAG_InterfaceMethodref,
                     TAG_NameAndType, TAG_Dynamic, TAG_InvokeDynamic):
            slots[i] = (tag, data[off:off + 4]); off += 4
        elif tag in (TAG_Int, TAG_Float):
            slots[i] = (tag, data[off:off + 4]); off += 4
        elif tag in (TAG_Long, TAG_Double):
            slots[i] = (tag, data[off:off + 8]); off += 8
            slots[i + 1] = None
            i += 1
        elif tag == TAG_MethodHandle:
            slots[i] = (tag, data[off:off + 3]); off += 3
        else:
            raise ValueError("unknown tag %d at slot %d" % (tag, i))
        i += 1
    return slots, off


def collect_name_refs(data, slots, pool_start):
    """收集被当作标识符引用的 Utf8 槽位（这些绝不能翻译）。"""
    refs = set()
    for slot, ent in slots.items():
        if ent is None:
            continue
        tag, payload = ent
        if tag == TAG_Class:
            refs.add(struct.unpack(">H", payload[:2])[0])
        elif tag == TAG_String:
            # CONSTANT_String 指向的就是显示用字面量，不保护
            pass
        elif tag in (TAG_NameAndType, TAG_Fieldref, TAG_Methodref, TAG_InterfaceMethodref):
            if tag == TAG_NameAndType:
                refs.add(struct.unpack(">H", payload[:2])[0])
                refs.add(struct.unpack(">H", payload[2:4])[0])
            else:
                nt = struct.unpack(">H", payload[2:4])[0]
                if nt in slots and slots[nt] and slots[nt][0] == TAG_NameAndType:
                    refs.add(struct.unpack(">H", slots[nt][1][:2])[0])
                    refs.add(struct.unpack(">H", slots[nt][1][2:4])[0])
        elif tag == TAG_MethodType:
            refs.add(struct.unpack(">H", payload[:2])[0])
        elif tag in (TAG_Module, TAG_Package):
            refs.add(struct.unpack(">H", payload[:2])[0])
    off = pool_start
    icount = struct.unpack(">H", data[off + 6:off + 8])[0]; off += 8 + 2 * icount
    for _ in range(2):  # fields, then methods
        n = struct.unpack(">H", data[off:off + 2])[0]; off += 2
        for _ in range(n):
            ni, di = struct.unpack(">HH", data[off + 2:off + 6]); off += 6
            refs.add(ni); refs.add(di)
            acount = struct.unpack(">H", data[off:off + 2])[0]; off += 2
            for _ in range(acount):
                alen = struct.unpack(">I", data[off + 2:off + 6])[0]; off += 6
                off += alen
    return refs


def rewrite(data, trans):
    slots, pool_start = parse_class(data)
    refs = collect_name_refs(data, slots, pool_start)
    out = io.BytesIO()
    changed = 0
    for slot in sorted(slots):
        ent = slots[slot]
        if ent is None:
            continue
        tag, payload = ent
        if tag == TAG_Utf8:
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None and slot not in refs and text in trans:
                new_bytes = trans[text].encode("utf-8")
                if new_bytes != payload:
                    changed += 1
                    payload = new_bytes
            out.write(bytes([TAG_Utf8]))
            out.write(struct.pack(">H", len(payload)))
            out.write(payload)
        else:
            out.write(bytes([tag]))
            out.write(payload)
    new_data = data[:8] + struct.pack(">H", len(slots) + 1) + out.getvalue() + data[pool_start:]
    parse_class(new_data)  # 自检：重建后必须仍可解析
    return new_data, changed


def apply(module_dir, dict_path, verbose=False):
    """对 module_dir 下全部 .class 应用字典，原地改写。返回(改动类数, 替换处数)。"""
    with open(dict_path, encoding="utf-8") as fh:
        trans = json.load(fh)
    changed_classes = 0
    replacements = 0
    for root, _dirs, files in os.walk(module_dir):
        for f in files:
            if not f.endswith(".class"):
                continue
            p = os.path.join(root, f)
            data = open(p, "rb").read()
            try:
                nd, changed = rewrite(data, trans)
            except Exception as e:
                print("SKIP/ERR %s: %s" % (p, e))
                continue
            if changed:
                open(p, "wb").write(nd)
                changed_classes += 1
                replacements += changed
                if verbose:
                    print("  %4d  %s" % (changed, os.path.relpath(p, module_dir)))
    return changed_classes, replacements


def _defaults():
    here = pathlib.Path(__file__).resolve().parent
    root = here.parents[2]
    module_dir = str(root / "_work" / "extracted" / "com.sparrowwallet.sparrow")
    dict_path = str(here.parents[0] / "翻译字典" / "java_trans_all.json")
    return module_dir, dict_path


if __name__ == "__main__":
    module_dir, dict_path = _defaults()
    cc, rp = apply(module_dir, dict_path, verbose=False)
    print("changed classes:", cc)
    print("total string replacements:", rp)
