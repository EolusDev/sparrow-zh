# -*- coding: utf-8 -*-
"""Parse a jlink jimage file (little-endian, PerfectHash lookup)."""
import struct

def unmasked_hash(s, seed):
    MULT = 0x01000193
    seed &= 0xFFFFFFFF
    for ch in s:
        uch = ord(ch)
        if uch & ~0x7F:
            buffer = []
            mask = (~0x3F) & 0xFFFFFFFF
            n = 0
            while True:
                buffer.append(0x80 | (uch & 0x3F))
                uch >>= 6
                mask >>= 1
                if (uch & mask) == 0:
                    break
                n += 1
            buffer.append(((mask << 1) & 0xFF) | uch)
            for b in reversed(buffer):
                seed = ((seed * MULT) ^ (b & 0xFF)) & 0xFFFFFFFF
        elif uch == 0:
            seed = ((seed * MULT) ^ 0xC0) & 0xFFFFFFFF
            seed = ((seed * MULT) ^ 0x80) & 0xFFFFFFFF
        else:
            seed = ((seed * MULT) ^ uch) & 0xFFFFFFFF
    return seed

def jimage_hash(s, seed=None):
    if seed is None:
        seed = 0x01000193
    return unmasked_hash(s, seed) & 0x7FFFFFFF

def java_hash(s, seed=None):
    h = 0 if seed is None else seed
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return h

def signed32(v):
    if v >= 0x80000000:
        v -= 0x100000000
    return v

class JImage:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        self.magic, = struct.unpack_from("<I", d, 0)
        assert self.magic == 0xCAFEDADA, hex(self.magic)
        version = struct.unpack_from("<I", d, 4)[0]
        self.major = version >> 16
        self.minor = version & 0xFFFF
        self.flags = struct.unpack_from("<I", d, 8)[0]
        self.resource_count = struct.unpack_from("<I", d, 12)[0]
        self.table_length = struct.unpack_from("<I", d, 16)[0]
        self.locations_size = struct.unpack_from("<I", d, 20)[0]
        self.strings_size = struct.unpack_from("<I", d, 24)[0]
        self.header_size = 28
        self.redirect_start = self.header_size
        self.offsets_start = self.redirect_start + self.table_length * 4
        self.locations_start = self.offsets_start + self.table_length * 4
        self.strings_start = self.locations_start + self.locations_size
        self.data_start = self.strings_start + self.strings_size
        self.redirect = struct.unpack_from("<%di" % self.table_length, d, self.redirect_start)
        self.offsets = struct.unpack_from("<%di" % self.table_length, d, self.offsets_start)
        # precompute string table boundaries (relative offsets -> text)
        self._str_map = {}
        pos = self.strings_start
        end = self.strings_start + self.strings_size
        while pos < end:
            nxt = d.index(b"\x00", pos)
            self._str_map[pos - self.strings_start] = d[pos:nxt].decode("utf-8", "replace")
            pos = nxt + 1

    def string_at(self, offset):
        return self._str_map.get(offset, "")

    def get_location_index(self, name):
        count = self.table_length
        h = jimage_hash(name)
        index = self.redirect[h % count]
        if index < 0:
            return -index - 1
        elif index > 0:
            h2 = jimage_hash(name, index)
            return h2 % count
        else:
            return -1

    def get_attributes(self, off):
        """Decompress location attributes at byte offset into locations region."""
        attrs = {}
        o = self.locations_start + off
        limit = self.locations_start + self.locations_size
        while o < limit:
            b = self.data[o]; o += 1
            if b <= 0x7:
                break
            kind = b >> 3
            length = (b & 0x7) + 1
            val = 0
            for j in range(length):
                val = (val << 8) | self.data[o]; o += 1
            attrs[kind] = val
        return attrs

    def location(self, name):
        li = self.get_location_index(name)
        if li < 0:
            return None
        if li >= len(self.offsets):
            return None
        off = self.offsets[li]
        if off <= 0:
            return None
        return self.get_attributes(off)

    def resolve(self, attrs):
        mod = self.string_at(attrs.get(1, 0))
        parent = self.string_at(attrs.get(2, 0))
        base = self.string_at(attrs.get(3, 0))
        ext = self.string_at(attrs.get(4, 0))
        name = base
        if parent:
            name = parent + "/" + name
        if ext:
            name = name + "." + ext
        return mod, name

    def find(self, name):
        attrs = self.location(name)
        if attrs is None:
            return None
        mod, nm = self.resolve(attrs)
        full = "/" + mod + "/" + nm if mod and nm else (nm or mod or "")
        if full != name:
            return None
        return attrs

if __name__ == "__main__":
    import sys
    img = JImage(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "runtime", "lib", "modules"))
    print("major", img.major, "minor", img.minor, "res_count", img.resource_count,
          "table", img.table_length, "loc_size", img.locations_size, "str_size", img.strings_size)
    print("data_start", img.data_start, "file", len(img.data))
    for probe in ["java.base/module-info.class",
                  "java.base/java/lang/Object.class",
                  "com.sparrowwallet.sparrow/module-info.class",
                  "com.sparrowwallet.sparrow/com/sparrowwallet/sparrow/AppController.class",
                  "com/sparrowwallet.sparrow/com/sparrowwallet/sparrow/control/MainWindow.fxml"]:
        attrs = img.find(probe)
        if attrs:
            mod, nm = img.resolve(attrs)
            print("FOUND", probe, "| mod", mod, "name", nm, "| off", attrs.get(5), "comp", attrs.get(6), "uncomp", attrs.get(7))
        else:
            print("NOT FOUND", probe)
