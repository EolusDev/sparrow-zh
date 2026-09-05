# -*- coding: utf-8 -*-
"""把中文翻译字典应用到解包后的 sparrow 模块 .fxml 界面文件。

处理 text/promptText/helpText 属性与 >可见文本节点<；注释块移到文件末尾
以保证替换过程不破坏 XML。既可单独运行，也可被 build.py 以 apply(...) 调用。
"""
import os
import re
import json
import pathlib


def _build_keys(trans):
    return sorted(trans.keys(), key=len, reverse=True)


def apply(base_dir, dict_path):
    """对 base_dir 下全部 .fxml 应用字典，原地改写。返回更新文件数。"""
    with open(dict_path, encoding="utf-8") as fh:
        trans = json.load(fh)
    files_done = 0
    for root, _dirs, fs in os.walk(base_dir):
        for f in fs:
            if not f.endswith(".fxml"):
                continue
            path = os.path.join(root, f)
            with open(path, encoding="utf-8") as fh:
                txt = fh.read()
            orig = txt
            # 1) 摘出注释块，最后再追加回文件尾
            comments = re.findall(r"\u003c!--.*?-->", txt, flags=re.S)
            txt_nc = re.sub(r"\u003c!--.*?-->", "", txt, flags=re.S)
            # 2) 替换 text="X" / promptText="X" / helpText="X"
            for attr in ("text", "promptText", "helpText"):
                def do_attr(m, _attr=attr):
                    val = m.group(1)
                    if val in trans:
                        return _attr + '="' + trans[val] + '"'
                    return m.group(0)
                pat = re.compile(r"\b" + attr + r'="([^"]*)"')
                txt_nc = pat.sub(do_attr, txt_nc)
            # 3) 替换完整可见文本节点 >X<
            def do_content(m):
                inner = m.group(1)
                if inner in trans:
                    return ">" + trans[inner] + "<"
                return m.group(0)
            pat2 = re.compile(r">([^<>]*[A-Za-z][^<>]*)<")
            txt_nc = pat2.sub(do_content, txt_nc)
            if comments:
                txt_nc = txt_nc + "\n" + "\n".join(comments)
            if txt_nc != orig:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(txt_nc)
                files_done += 1
    return files_done


def _defaults():
    here = pathlib.Path(__file__).resolve().parent
    root = here.parents[2]
    base_dir = str(root / "_work" / "extracted" / "com.sparrowwallet.sparrow"
                   / "com" / "sparrowwallet" / "sparrow")
    dict_path = str(here.parents[0] / "翻译字典" / "fxml_trans.json")
    return base_dir, dict_path


if __name__ == "__main__":
    base_dir, dict_path = _defaults()
    n = apply(base_dir, dict_path)
    print("fxml files updated:", n)
