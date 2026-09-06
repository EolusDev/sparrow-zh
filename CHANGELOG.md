# 更新记录（CHANGELOG）

本项目为 Sparrow Wallet 2.5.4 的完整中文化衍生版。以下按时间顺序记录汉化与修改的完整经过。

## v2.5.4-zh.1 — 2026-09-05（当前版本）

### 汉化实现
- **解包**：解析运行时镜像 `runtime\lib\modules`（jimage 容器，124 个模块；sparrow 模块 1380 个资源，含 31 个 FXML）
- **FXML 中文化**：31 个界面布局文件中 27 个被改写，注释块移至文件尾保证 XML 合法
- **Java 字面量翻译（六批字典，853 → 2330 条）**：
  - 第一批 base（853 条）：主界面、对话框、设置、交易等高频词
  - 第二批 batch2（+660 条）：首轮扫描残留补翻
  - 第三批 batch3（+317 条）：带拼接控制符的复合字面量
  - 第四批 batch4（+287 条）：复合串前后缀差异漏网项
  - 第五批 batch5（+282 条）：全部硬件导入向导长文本、设置页说明、Payjoin 错误、钱包校验警告
  - 第六批 batch6（+23 条）：状态栏/广播日志可见串
- **最终实测**：最终字典 2359 条（8 个分批字典合并 2362 条、剔除 3 个节点外部比较串）；439 个 Java 类、2444 处字面量替换；成品镜像 477 个资源含中文、共 20481 个中文字符；残留英文均为有意保留项（SQL/协议日志/专名/外部错误原文）

### 纯 Python 一键构建工具链（关键升级）
- 为让后续版本可快速重新汉化、且不依赖特定 JDK，整条管线改造为**只用 Python 标准库**：
  - `jimage_extract.py`：解析 0xCAFEFAFA + zlib 压缩块，纯 Python 解包（1380 个压缩资源 0 失败），替代 JDK 的 `jimage extract`
  - `apply_fxml_trans.py` / `apply_java_trans.py`：重构为可被导入的函数，并修复常量池字段解析中一处 `struct.unpack` 缓冲区长度 bug
  - `build.py`：一键编排「解包→FXML→Java→重建→校验→(可选)装回」，支持自动探测与 `--src/--modules/--out/--work/--install/--install-to/--clean` 参数；无参数进入交互模式
  - `一键汉化.bat`：双击入口，自动查找 Python
- **字典自动合并**：仓库只放可读的分批明文字典，`build.py` 找不到总字典时按固定顺序自动合并；并内置“外部比较串黑名单”，强制保留 `min relay fee not met` 等节点错误原文，避免破坏错误匹配
- **确定性可复现**：同一原始镜像 + 同一字典，命令行与双击入口、以及“总字典 / 分批合并”两条路径的产物 SHA256 完全一致（实测均为 `88A3EE9C…`）

### 镜像重建（关键路线）
- **路线 A（证伪）**：jlink 整体重链接虽通过 `jimage verify` 与中文复检，但启动失败（`BootstrapMethodError → LambdaConversionException`）。A/B 对照证明与翻译无关，为 JDK 25.0.4.1 工具链与运行时 25.0.2 模块重链接不兼容，整条路线放弃
- **路线 B（采用）**：逆向 jimage 格式（7×u4 头、perfect-hash 查找表、location 属性编码、数据段布局），实现就地改写重建——redirect 表与字符串表字节不变，只重建 locations/offsets 与数据段；改动资源以未压缩原字节写入，未改资源原样复制
- **验证**：57359 个资源 perfect-hash 全量校验 0 失配；实际启动稳定；界面截图确认菜单、欢迎页、状态栏全中文

### 便携化
- 排查并消除全部路径依赖（镜像内部、Sparrow.cfg、runtime\release、.jpackage.xml 均无绝对路径）
- `应用补丁.ps1` / `还原.ps1` 与全部构建脚本均使用相对路径，按脚本自身位置推导程序根，任意目录/盘符/中文或空格路径解压即用（已实测）
- 打包 `Sparrow-2.5.4-中文便携版.zip`（261,735,813 字节，SHA256 `47269CBBA5B8BE40D68077AF9EC2729DEF09021DB9F03F2E03073E48BE39EF99`）

### 目录体积治理
- 程序目录一度约 2.0 GB；删除重复解包副本、jlink 失败产物、重复 JDK、源码包、临时镜像/截图/中间清单等过程文件
- 最终根目录约 540 MB（含便携版 zip 约 249 MiB、中文补丁约 168 MB、运行中的 runtime 约 122 MB）；构建工具链不再需要 JDK

### 交付物
- 汉化镜像 `中文补丁\patch\modules.patched`（89,890,769 字节，SHA256 `88A3EE9C6BC1523DF3B07FC995E55B89A92D52E1C117D6BD82F9C4F930EA3808`）
- 原始镜像备份 `中文补丁\backup\modules.original`（85,822,080 字节，SHA256 `8142315D03785C2078AABA3339CD92E8139032C50310DAEBC4A160ED472F705A`，回滚基线）
- 一键构建/应用/还原脚本、翻译字典（FXML + Java 八批明文字典，构建时自动合并为 2359 条并剔除外部比较串黑名单）
- `README.md`、`CHANGELOG.md`、`Sparrow汉化使用说明与修改记录.txt`、`中文补丁\安装说明.md`

---

## 上游

- 原项目：Sparrow Wallet 2.5.4（[sparrowwallet/sparrow](https://github.com/sparrowwallet/sparrow)），Apache License 2.0
- 本版本未修改任何钱包功能逻辑，仅替换界面显示资源
