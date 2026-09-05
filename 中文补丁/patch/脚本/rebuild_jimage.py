# -*- coding: utf-8 -*-
"""Rebuild a jimage with replaced sparrow module resources (raw, uncompressed).

Strategy:
  - Parse original image fully (header/redirect/offsets/locations/strings/data).
  - Build the ordered list of ALL data-bearing entries by original data offset.
  - For sparrow module resources whose content changed, replace blob with the
    content bytes from the extracted tree (stored raw: compressed=0).
  - All other entries keep their original blob bytes verbatim.
  - Rebuild data section, locations region (with updated offset/compressed/
    uncompressed), offsets table; keep redirect + strings byte-identical.
"""
import struct, os, sys
import jimage_parse as J

MULT = 0x01000193

def serialize_attrs(attrs):
    out = bytearray()
    for kind in range(1, 9):
        v = attrs.get(kind, 0)
        if v == 0:
            continue
        n = (v.bit_length() + 7) // 8  # number of bytes needed
        n -= 1
        out.append((kind << 3) | n)
        for i in range(n, -1, -1):
            out.append((v >> (i << 3)) & 0xFF)
    out.append(0)  # END
    return bytes(out)

def rebuild(src_image, dest_path, tree_root, sparrow_mod="com.sparrowwallet.sparrow"):
    img = J.JImage(src_image)
    d = img.data
    ds = img.data_start

    # 1) collect all entries with data (offset attr present or implicit 0)
    #    entry: (orig_offset, li, attrs, full_name)
    entries = []
    for li in range(img.table_length):
        loff = img.offsets[li]
        if loff == 0:
            continue
        attrs = img.get_attributes(loff)
        # implicit offset 0 allowed (e.g. first resource)
        if 5 not in attrs and 6 not in attrs and 7 not in attrs:
            # pure name/dir entry with no data - still needs locations entry
            entries.append((0, li, attrs, None))
            continue
        off = attrs.get(5, 0)
        comp = attrs.get(6, 0)
        uncomp = attrs.get(7, 0)
        blob_size = comp if comp else uncomp
        mod, nm = img.resolve(attrs)
        name = "/" + mod + "/" + nm if mod and nm else (nm or mod or "/")
        entries.append((off, li, attrs, name))

    # sort by original data offset; entries without data offset go first (0)
    entries.sort(key=lambda e: e[0])

    # 2) build new data section + per-li new attrs
    entries_meta = {}
    new_data = bytearray()
    changed = []
    kept = 0
    for off, li, attrs, name in entries:
        comp = attrs.get(6, 0)
        uncomp = attrs.get(7, 0)
        blob_size = comp if comp else uncomp
        orig_blob = d[ds + off: ds + off + blob_size] if blob_size else b""
        new_attrs = dict(attrs)
        replace = False
        new_blob = orig_blob
        if name and name.startswith("/" + sparrow_mod + "/"):
            rel = name[len("/" + sparrow_mod + "/"):]
            fpath = os.path.join(tree_root, sparrow_mod, rel.replace("/", os.sep))
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    cand = f.read()
                if cand != orig_blob:
                    new_blob = cand
                    replace = True
                    new_attrs[6] = 0
                    new_attrs[7] = len(cand)
                    changed.append(name)
        if not replace:
            kept += 1
        new_attrs[5] = len(new_data)
        new_data += new_blob
        entries_meta[li] = new_attrs

    # 3) rebuild locations region + offsets table
    new_locations = bytearray()
    new_offsets = [0] * img.table_length
    for li in range(img.table_length):
        if li in entries_meta:
            new_offsets[li] = len(new_locations)
            new_locations += serialize_attrs(entries_meta[li])

    # 4) header
    locations_size = len(new_locations)
    # redirect + strings unchanged (bytes)
    redirect_bytes = d[img.redirect_start: img.offsets_start]
    strings_bytes = d[img.strings_start: img.strings_start + img.strings_size]

    hdr = bytearray()
    hdr += struct.pack("<I", 0xCAFEDADA)
    hdr += struct.pack("<I", (img.major << 16) | img.minor)
    hdr += struct.pack("<I", img.flags)
    hdr += struct.pack("<I", img.resource_count)
    hdr += struct.pack("<I", img.table_length)
    hdr += struct.pack("<I", locations_size)
    hdr += struct.pack("<I", img.strings_size)

    out = bytes(hdr) + redirect_bytes + struct.pack("<%di" % img.table_length, *new_offsets) + bytes(new_locations) + strings_bytes + bytes(new_data)

    with open(dest_path, "wb") as f:
        f.write(out)

    print("entries total:", len(entries))
    print("changed resources:", len(changed))
    print("kept unchanged:", kept)
    print("old locations_size:", img.locations_size, "new:", locations_size)
    print("old data size:", len(d) - ds, "new data size:", len(new_data))
    print("old file:", len(d), "new file:", len(out))
    return changed

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    src = os.path.join(root, "中文补丁", "backup", "modules.original")
    dst = os.path.join(root, "_work", "modules.patched")
    tree = os.path.join(root, "_work", "extracted")
    rebuild(src, dst, tree)
