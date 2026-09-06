# -*- coding: utf-8 -*-
"""Sparrow 中文汉化一键构建脚本（纯 Python，不需要安装 JDK）。

用法：
  1) 双击运行 / 不带参数：进入交互模式，自动探测已安装的 Sparrow。
  2) 命令行：
       python build.py --src "D:\\Sparrow"
       python build.py --src "D:\\Sparrow" --install
       python build.py --modules "D:\\path\\to\\modules" --out patched.modules

参数：
  --src DIR      Sparrow 安装根目录（内含 runtime/lib/modules）
  --modules FILE 直接指定原版 modules 文件（与 --src 二选一）
  --out FILE     汉化镜像输出路径（默认写到 patch/output/modules.zh）
  --work DIR     临时解包/改写工作目录（默认系统临时目录，结束自动保留以便排查）
  --install      构建成功后直接装回该 Sparrow（会先把原镜像备份为 modules.original.bak）
  --clean        构建前清空工作目录

流程：解包 jimage -> 应用 FXML 字典 -> 应用 Java 字典 -> 就地重建 jimage -> 纯 Python 校验。
跨版本通用：不写死任何 Sparrow 版本号，对任意版本的 modules 都可尝试；
新版本若有未覆盖文案，可用 scan_remaining.py 扫出后往字典里增量补充。
"""
import os
import sys
import gzip
import json
import shutil
import struct
import argparse
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.dirname(HERE)                 # patch/
ZH = os.path.dirname(PATCH)                   # 中文补丁/
sys.path.insert(0, HERE)

import jimage_parse as J          # noqa: E402
import jimage_extract as E        # noqa: E402
import rebuild_jimage as R        # noqa: E402
import apply_fxml_trans as F      # noqa: E402
import apply_java_trans as C      # noqa: E402
import safe_dict as S             # noqa: E402 字典安全形态还原

SPARROW_MOD = "com.sparrowwallet.sparrow"
DICT_DIR = os.path.join(PATCH, "翻译字典")


def log(msg):
    print("[*] " + msg, flush=True)


def ok(msg):
    print("[v] " + msg, flush=True)


def err(msg):
    print("[x] " + msg, flush=True)


def _dump_tmp(name, data):
    """把已还原的字典写到临时明文 json，返回路径（供 apply 模块按路径读取）。"""
    tmp = os.path.join(tempfile.gettempdir(), name)
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False)
    return tmp


# ---------- 字典加载：优先明文 json，其次 .gz；统一经 safe_dict 还原安全形态 ----------
def load_dict_path(filename):
    plain = os.path.join(DICT_DIR, filename)
    if os.path.isfile(plain):
        data = S.load_json_dict(plain)        # 安全形态自动还原；普通形态无副作用
        return _dump_tmp(filename, data)
    gz = plain + ".gz"
    if os.path.isfile(gz):
        data = json.loads(gzip.open(gz, "rb").read().decode("utf-8"))
        data = S.decode_dict(data)
        log("字典 %s 由 .gz 解压得到（%d 条）" % (filename, len(data)))
        return _dump_tmp(filename, data)
    raise FileNotFoundError("找不到翻译字典：%s（或其 .gz）" % filename)


# Java 分批字典（仓库精简形态下用它们自动合并出总字典，合并顺序固定）
# 注：batch5 因单文件较大，拆为 batch5a / batch5b 两个等价分片，合并时依次载入
JAVA_PARTS = ["java_trans.json", "java_trans2.json", "java_trans3.json",
              "java_trans_batch2.json", "java_trans_batch3.json",
              "java_trans_batch4.json", "java_trans_batch5a.json",
              "java_trans_batch5b.json", "java_trans_batch6.json"]

# 外部比较串黑名单：这些是 Bitcoin Core / 节点 / 协议返回的英文原文，程序需要拿
# 常量去和服务器返回做 equals/contains 匹配来判断错误类型，翻译会导致匹配失效，
# 因此即使分批字典里误收，合并时也强制剔除（只保留英文）。
EXTERNAL_NEVER_TRANSLATE = {
    "min relay fee not met",
    "mempool min fee not met",
    "insufficient fee, rejecting replacement",
}


def load_java_dict():
    """Java 字典解析：优先总字典 all.json，其次 all.json.gz；
    都没有时从分批字典（安全形态）按固定顺序自动合并并还原。所有路径都经过
    safe_dict 还原；分批里多出的少量键在源码中匹配不到，apply 阶段不会替换。"""
    plain = os.path.join(DICT_DIR, "java_trans_all.json")
    if os.path.isfile(plain):
        return _dump_tmp("java_trans_all.json", S.load_json_dict(plain))
    gz = plain + ".gz"
    if os.path.isfile(gz):
        data = json.loads(gzip.open(gz, "rb").read().decode("utf-8"))
        data = S.decode_dict(data)
        log("Java 总字典由 .gz 解压得到（%d 条）" % len(data))
        return _dump_tmp("java_trans_all.json", data)
    merged = {}
    used = []
    for name in JAVA_PARTS:
        fp = os.path.join(DICT_DIR, name)
        if os.path.isfile(fp):
            merged.update(S.load_json_dict(fp))   # 安全形态自动还原
            used.append(name)
    if not merged:
        raise FileNotFoundError("找不到 Java 翻译字典（java_trans_all.json/.gz 或分批字典）")
    dropped = [k for k in EXTERNAL_NEVER_TRANSLATE if k in merged]
    for k in dropped:
        merged.pop(k)
    if dropped:
        log("已跳过 %d 个外部比较串（保留英文以维持错误匹配）" % len(dropped))
    log("未找到总字典，已由 %d 个分批字典自动合并（%d 条）" % (len(used), len(merged)))
    return _dump_tmp("java_trans_all.merged.json", merged)


# ---------- 定位原版 modules ----------
def resolve_modules(src=None, modules=None):
    if modules:
        if not os.path.isfile(modules):
            raise FileNotFoundError(modules)
        return os.path.abspath(modules)
    candidates = []
    if src:
        candidates.append(os.path.join(src, "runtime", "lib", "modules"))
    # 常见安装位置自动探测
    for base in (os.environ.get("ProgramFiles", ""),
                 os.environ.get("ProgramFiles(x86)", ""),
                 os.path.expanduser("~\\AppData\\Local")):
        if base:
            candidates.append(os.path.join(base, "Sparrow", "runtime", "lib", "modules"))
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    return None


# ---------- 纯 Python 校验：完美哈希可解析 + 中文统计 ----------
def verify_image(path, tree_root):
    img = J.JImage(path)
    # 1) 对每个 redirect 链做一次解析，确保完美哈希表自洽、offsets 有效
    bad = 0
    for li in range(img.table_length):
        off = img.offsets[li]
        if off == 0:
            continue
        try:
            img.get_attributes(off)
        except Exception:
            bad += 1
    # 2) 统计 sparrow 模块内含中文的资源与字符数（与工作树对照）
    zh_res = 0
    zh_chars = 0
    for mod, nm, attrs in E.iter_entries(img, SPARROW_MOD):
        blob = E.read_resource(img, attrs)
        txt = blob.decode("utf-8", "ignore")  # class 是二进制，忽略非法字节后仍可统计其中中文
        c = sum(1 for ch in txt if "一" <= ch <= "鿿")
        if c:
            zh_res += 1
            zh_chars += c
    return bad, zh_res, zh_chars, img.resource_count


def count_tree_zh(tree_root):
    base = os.path.join(tree_root, SPARROW_MOD)
    res = 0
    chars = 0
    for root, _d, fs in os.walk(base):
        for f in fs:
            txt = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
            c = sum(1 for ch in txt if "一" <= ch <= "鿿")
            if c:
                res += 1
                chars += c
    return res, chars


def main():
    ap = argparse.ArgumentParser(description="Sparrow 中文汉化一键构建")
    ap.add_argument("--src", help="Sparrow 安装根目录")
    ap.add_argument("--modules", help="直接指定原版 modules 文件")
    ap.add_argument("--out", help="汉化镜像输出路径")
    ap.add_argument("--work", help="工作目录")
    ap.add_argument("--install", action="store_true",
                    help="构建后装回源镜像所在的 Sparrow（就地替换）")
    ap.add_argument("--install-to", dest="install_to",
                    help="装回到指定 Sparrow 安装根目录（其 runtime/lib/modules），与源镜像分离")
    ap.add_argument("--clean", action="store_true", help="构建前清空工作目录")
    args = ap.parse_args()

    # 无参数 -> 交互模式，方便双击使用
    if len(sys.argv) == 1:
        log("未提供参数，进入交互模式。直接回车将自动探测已安装的 Sparrow。")
        typed = input("请把 Sparrow 安装文件夹拖到这里（或回车自动探测）: ").strip().strip('"')
        if typed:
            args.src = typed
        args.install = (input("构建完成后是否直接装回该 Sparrow？(y/N): ").strip().lower() == "y")

    src_modules = resolve_modules(args.src, args.modules)
    if not src_modules:
        err("未找到原版 runtime/lib/modules，请用 --src 指定 Sparrow 安装目录。")
        return 2
    log("原版镜像：%s（%d 字节）" % (src_modules, os.path.getsize(src_modules)))

    work = args.work or os.path.join(PATCH, "build_work")
    tree = os.path.join(work, "extracted")
    if args.clean and os.path.isdir(tree):
        shutil.rmtree(tree)
    os.makedirs(tree, exist_ok=True)

    # 1) 解包（纯 Python）
    log("解包 sparrow 模块 …")
    n = E.extract(src_modules, tree, module=SPARROW_MOD)
    ok("解包 %d 个资源到 %s" % (n, tree))

    # 2) FXML
    fxml_dict = load_dict_path("fxml_trans.json")
    fxml_base = os.path.join(tree, SPARROW_MOD, "com", "sparrowwallet", "sparrow")
    nf = F.apply(fxml_base, fxml_dict)
    ok("FXML 界面文件更新 %d 个" % nf)

    # 3) Java class
    java_dict = load_java_dict()
    cc, rp = C.apply(os.path.join(tree, SPARROW_MOD), java_dict)
    ok("Java 类改写 %d 个，字符串替换 %d 处" % (cc, rp))

    # 4) 重建镜像
    out = args.out or os.path.join(PATCH, "output", "modules.zh")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    log("就地重建 jimage …")
    changed = R.rebuild(src_modules, out, tree)
    ok("重建完成，替换资源 %d 个 -> %s（%d 字节）"
       % (len(changed), out, os.path.getsize(out)))

    # 5) 校验
    bad, zh_res, zh_chars, rc = verify_image(out, tree)
    tree_res, tree_chars = count_tree_zh(tree)
    ok("镜像资源总数 %d，完美哈希失配 %d" % (rc, bad))
    ok("镜像内含中文资源 %d 个 / 中文字符 %d；工作树 %d 个 / %d"
       % (zh_res, zh_chars, tree_res, tree_chars))
    if bad:
        err("完美哈希存在失配，镜像不可用，请检查后重试。")
        return 3

    # 6) 可选装回
    target = None
    if args.install_to:
        target = os.path.join(args.install_to, "runtime", "lib", "modules")
    elif args.install:
        target = src_modules  # 就地替换读出来的那个 modules
    if target:
        if not os.path.isfile(target):
            err("装回目标不存在：%s" % target)
            return 4
        bak = target + ".original.bak"
        if not os.path.isfile(bak):
            shutil.copy2(target, bak)  # 仅第一次保留真正的原版，之后不再覆盖
            ok("已备份原版 -> %s" % bak)
        shutil.copy2(out, target)
        ok("已装回汉化镜像：%s" % target)
        log("现在启动 Sparrow 即为中文版；还原时把 modules.original.bak 改名回 modules 即可。")
    else:
        log("未装回。需要时把输出文件复制到某 Sparrow 的 runtime/lib/modules（先备份原文件）。")

    ok("全部完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
