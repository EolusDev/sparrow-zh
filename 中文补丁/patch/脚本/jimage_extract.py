# -*- coding: utf-8 -*-
"""纯 Python 的 jimage 解包器，用于替代 JDK 自带的 `jimage extract`。

jimage 内被压缩的资源布局（小端）：
  [0:4]   magic = 0xCAFEFAFA
  [4:8]   zlib 压缩载荷长度 clen
  [8:12]  保留(0)
  [12:16] 解压后长度 uncomp
  [16:20] 保留(0)
  [20:24] 压缩级别相关字段
  [24:28] 0xFFFFFFFF
  [28]    0x01
  [29 : 29+clen] 标准 zlib 流（0x78 0x9C 头，wbits=15）
未压缩资源（compressed=0）则直接是原始字节。

只依赖标准库 + 同目录 jimage_parse.py。
"""
import os
import struct
import zlib

import jimage_parse as J

ZIP_MAGIC = 0xCAFEFAFA
ZSTREAM_OFFSET = 29


def read_resource(img, attrs):
    """根据 location 属性，从镜像数据段读出某资源的原始（解压后）字节。"""
    comp = attrs.get(6, 0)
    uncomp = attrs.get(7, 0)
    off = attrs.get(5, 0)
    if comp:
        blob = img.data[img.data_start + off: img.data_start + off + comp]
        magic = struct.unpack_from("<I", blob, 0)[0]
        if magic != ZIP_MAGIC:
            raise ValueError("bad zip magic %08x" % magic)
        clen = struct.unpack_from("<I", blob, 4)[0]
        dec = zlib.decompress(blob[ZSTREAM_OFFSET: ZSTREAM_OFFSET + clen], 15)
        if len(dec) != uncomp:
            # 兜底：长度字段不一致时直接解压到流末尾
            dec = zlib.decompress(blob[ZSTREAM_OFFSET:], 15)
        return dec
    return img.data[img.data_start + off: img.data_start + off + uncomp]


def iter_entries(img, module=None):
    """遍历镜像中所有带数据的资源，产出 (module, name, attrs)。"""
    for li in range(img.table_length):
        off = img.offsets[li]
        if off == 0:
            continue
        attrs = img.get_attributes(off)
        if 5 not in attrs and 6 not in attrs and 7 not in attrs:
            continue  # 纯名字/目录条目，无数据
        mod, nm = img.resolve(attrs)
        if module is not None and mod != module:
            continue
        if not nm:
            continue
        yield mod, nm, attrs


def extract(src_image, out_root, module=None, verbose=False):
    """把 src_image 解包到 out_root/<module>/<name...>。返回写出文件数。"""
    img = J.JImage(src_image)
    count = 0
    for mod, nm, attrs in iter_entries(img, module):
        data = read_resource(img, attrs)
        fp = os.path.join(out_root, mod, *nm.split("/"))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "wb") as fh:
            fh.write(data)
        count += 1
        if verbose and count % 2000 == 0:
            print("  extracted", count)
    return count


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    src = os.path.join(root, "中文补丁", "backup", "modules.original")
    out = os.path.join(root, "_work", "extracted")
    mod = "com.sparrowwallet.sparrow"
    n = extract(src, out, module=mod, verbose=True)
    print("extracted files:", n)
