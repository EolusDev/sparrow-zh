# -*- coding: utf-8 -*-
"""Apply Chinese translation dict to .class files inside the extracted sparrow module.
Replaces CONSTANT_Utf8 string literals (not identifiers) with Chinese, rebuilding the
constant pool (handles byte-length changes) and rewriting the class file.
"""
import os, sys, json, struct, io

import pathlib
_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
MODULE = str(_ROOT / "_work" / "extracted" / "com.sparrowwallet.sparrow")
DICT = json.load(open(_HERE.parents[0] / "翻译字典" / "java_trans_all.json", encoding="utf-8"))

TAG_Utf8=1; TAG_Int=3; TAG_Float=4; TAG_Long=5; TAG_Double=6
TAG_Class=7; TAG_String=8; TAG_Fieldref=9; TAG_Methodref=10; TAG_InterfaceMethodref=11
TAG_NameAndType=12; TAG_MethodHandle=15; TAG_MethodType=16; TAG_Dynamic=17; TAG_InvokeDynamic=18
TAG_Module=19; TAG_Package=20

def parse_class(data):
    """Return (cp_entries, cp_index_to_utf8index, rest_bytes_start_offset)"""
    if data[:4] != b'\xca\xfe\xba\xbe':
        raise ValueError("bad magic")
    off = 8  # magic + minor + major
    cp_count = struct.unpack("><H", data[off:off+2])[0]; off += 2
    entries = []  # list of (tag, raw_bytes_of_entry_incl_tag) ; index i corresponds to constant pool slot i+1
    # map from utf8 CONSTANT index (slot) -> text
    # slots: index 0 reserved; long/double occupy 2 slots
    slots = {}   # slot -> (tag, payload)
    i = 1
    while i < cp_count:
        tag = data[off]
        start = off
        off += 1
        if tag == TAG_Utf8:
            ln = struct.unpack("><H", data[off:off+2])[0]; off += 2
            payload = data[off:off+ln]; off += ln
            slots[i] = (tag, payload)
        elif tag in (TAG_Class, TAG_String, TAG_MethodType, TAG_Module, TAG_Package):
            slots[i] = (tag, data[off:off+2]); off += 2
        elif tag in (TAG_Fieldref, TAG_Methodref, TAG_InterfaceMethodref, TAG_NameAndType, TAG_Dynamic, TAG_InvokeDynamic):
            slots[i] = (tag, data[off:off+4]); off += 4
        elif tag in (TAG_Int, TAG_Float):
            slots[i] = (tag, data[off:off+4]); off += 4
        elif tag in (TAG_Long, TAG_Double):
            slots[i] = (tag, data[off:off+8]); off += 8
            slots[i+1] = None  # takes 2 slots
            i += 1
        elif tag == TAG_MethodHandle:
            slots[i] = (tag, data[off:off+3]); off += 3
        else:
            raise ValueError("unknown tag %d at %d" % (tag, start))
        i += 1
    return slots, off

def collect_name_refs(data, slots, pool_start):
    """Return set of utf8 slot indices referenced as identifiers (class/field/method/descriptor)."""
    refs = set()
    def utf8_index_of(slot):
        # slot is a cp index whose content is an index into utf8; need to follow
        return None
    # We need to find, for each slots entry that is Class/NameAndType/etc, the utf8 index it points to.
    # But refs are encoded as indices within the payload. Since we stored payload bytes, and the
    # cp indices are sequential (slot number = cp index), the payload holds u2 indices.
    for slot, ent in slots.items():
        if ent is None: continue
        tag, payload = ent
        if tag == TAG_Class:
            idx = struct.unpack("><H", payload[:2])[0]
            refs.add(idx)
        elif tag == TAG_String:
            idx = struct.unpack("><H", payload[:2])[0]
            refs.add(idx)  # String index is a utf8 index (the literal!) - but that IS a literal; still protect? A CONSTANT_String points to the utf8 content used in a constant. Those are string literals used in code. It's fine to translate.
            refs.discard(idx)  # Actually String constants ARE display literals; do NOT protect.
        elif tag in (TAG_NameAndType, TAG_Fieldref, TAG_Methodref, TAG_InterfaceMethodref):
            ni = struct.unpack("><H", payload[:2])[0]
            if tag == TAG_NameAndType:
                di = struct.unpack("><H", payload[2:4])[0]
                refs.add(ni); refs.add(di)
            else:
                # payload is (class_index, name_and_type_index); the name/desc come via NameAndType
                nt = struct.unpack("><H", payload[2:4])[0]
                if nt in slots and slots[nt] and slots[nt][0] == TAG_NameAndType:
                    refs.add(struct.unpack("><H", slots[nt][1][:2])[0])
                    refs.add(struct.unpack("><H", slots[nt][1][2:4])[0])
        elif tag == TAG_MethodType:
            refs.add(struct.unpack("><H", payload[:2])[0])
        elif tag in (TAG_Module, TAG_Package):
            refs.add(struct.unpack("><H", payload[:2])[0])
    # also field_info/method_info name_index & descriptor_index (parse after pool)
    off = pool_start
    access_flags, this_class, super_class = struct.unpack("><HHH", data[off:off+6]); off += 6
    icount = struct.unpack("><H", data[off:off+2])[0]; off += 2 + 2*icount
    for _ in range(2):  # fields then methods
        n = struct.unpack("><H", data[off:off+2])[0]; off += 2
        for _ in range(n):
            _, ni, di = struct.unpack("><HHH", data[off:off+6]); off += 6
            refs.add(ni); refs.add(di)
            acount = struct.unpack("><H", data[off:off+2])[0]; off += 2
            for _ in range(acount):
                _, alen = struct.unpack("><HI", data[off:off+6]); off += 6
                off += alen
    return refs

def rewrite(data):
    slots, pool_start = parse_class(data)
    refs = collect_name_refs(data, slots, pool_start)
    # build new pool bytes
    out = io.BytesIO()
    changed = 0
    changed_map = {}
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
            if text is not None and slot not in refs and text in DICT:
                new_text = DICT[text]
                new_bytes = new_text.encode("utf-8")
                if new_bytes != payload:
                    changed += 1
                    changed_map.setdefault(text, 0)
                    changed_map[text] += 1
                    payload = new_bytes
            out.write(bytes([TAG_Utf8]))
            out.write(struct.pack("><H", len(payload)))
            out.write(payload)
        else:
            out.write(bytes([tag]))
            out.write(payload)
    new_pool = out.getvalue()
    new_data = data[:8] + struct.pack("><H", len(slots)+1) + new_pool + data[pool_start:]
    # sanity: reparse new_data
    parse_class(new_data)
    return new_data, changed, changed_map

def main():
    total_changed_classes = 0
    total_repls = 0
    changed_classes = []
    for root, dirs, files in os.walk(MODULE):
        for f in files:
            if not f.endswith(".class"): continue
            p = os.path.join(root, f)
            data = open(p, "rb").read()
            try:
                nd, changed, cmap = rewrite(data)
            except Exception as e:
                print("SKIP/ERR %s: %s" % (p, e))
                continue
            if changed:
                open(p, "wb").write(nd)
                total_changed_classes += 1
                total_repls += changed
                changed_classes.append((os.path.relpath(p, MODULE), changed))
    print("changed classes:", total_changed_classes)
    print("total string replacements:", total_repls)
    changed_classes.sort(key=lambda x: -x[1])
    for rel, c in changed_classes[:40]:
        print("  %4d  %s" % (c, rel))

if __name__ == "__main__":
    main()
