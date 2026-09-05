# 更新记录（CHANGELOG）

本项目为 Sparrow Wallet 2.5.4 的完整中文化衍生版。以下按时间顺序记录汉化与修改的完整经过。

## v2.5.4-zh.1 — 2026-09-05（当前版本）

### 汉化实现
- **解包**：使用 JDK 25 `jimage` 将运行时镜像 `runtime\lib\modules` 解包（124 个模块，sparrow 模块 1154+ 个类与 31 个 FXML）
- **FXML 中文化**：31 个界面布局文件全部翻译，注释块移至文件尾保证工具链解析安全
- **Java 字面量翻译（六批字典，853 → 2330 条）**：
  - 第一批 base（853 条）：主界面、对话框、设置、交易等高频词
  - 第二批 batch2（+660 条）：首轮扫描残留补翻
  - 第三批 batch3（+317 条）：带拼接控制符的复合字面量
  - 第四批 batch4（+287 条）：复合串前后缀差异漏网项
  - 第五批 batch5（+282 条）：全部硬件导入向导长文本、设置页说明、Payjoin 错误、钱包校验警告
  - 第六批 batch6（+23 条）：状态栏/广播日志可见串
- **残留统计**：1716 → 896 → 695 → 670（最终 670 条均为有意保留项：SQL/协议日志/专名）

### 镜像重建（关键路线）
- **路线 A（证伪）**：jlink 重建产出镜像虽通过 `jimage verify` 与中文复检，但启动失败（`BootstrapMethodError → LambdaConversionException`）。A/B 对照实验证明与翻译无关，为 JDK 25.0.4.1 工具链与运行时 25.0.2 模块重链接不兼容，整条路线放弃
- **路线 B（采用）**：逆向 jimage 格式（7×u4 头、perfect-hash 查找表、location 属性编码、数据段布局），实现就地改写重建——redirect 表与字符串表字节不变，只重建 locations/offsets 与数据段；修改资源以未压缩原字节写入，未修改资源原样复制
- **验证**：`jimage verify` exit 0；57359 个资源 perfect-hash 全量校验 0 失配；启动稳定；界面截图确认全中文

### 便携化
- 排查并消除全部路径依赖（镜像内部、Sparrow.cfg、runtime\release、.jpackage.xml 均无绝对路径）
- `应用补丁.ps1` / `还原.ps1` 由硬编码路径改为**相对路径**（自动定位脚本上一级为程序根目录）
- 实测：复制/解压到带空格的陌生路径（如 `C:\Users\Public\便携测试 Sparrow`）直接启动，中文界面完整生效
- 打包 `Sparrow-2.5.4-中文便携版.zip`（261MB，SHA256 `2FBD766BC39301B7BEC6921AEDB453A9E6328CC6D4BDD3024EF8D60F52A1BA09`）

### 目录体积治理
- 程序目录由 2.0 GB 清理至 0.79 GB（删除重复 JDK 副本、JDK 压缩包、源码包、诊断解包、临时镜像/截图/中间清单等约 1.2 GB）
- 当前根目录 1.06 GB（含便携版 zip 261MB；删除后 0.79 GB）

### 交付物
- 汉化镜像 `中文补丁\patch\modules.patched`（SHA256 `95B294A9…`，89,890,740 字节）
- 原始镜像备份 `中文补丁\backup\modules.original`（SHA256 `8142315D…`，回滚基线）
- 一键应用/还原脚本、翻译字典（10 个 JSON）、汉化管线脚本
- `README.md`、`CHANGELOG.md`、`Sparrow汉化使用说明与修改记录.txt`、`安装说明.md`

---

## 上游

- 原项目：Sparrow Wallet 2.5.4（[sparrowwallet/sparrow](https://github.com/sparrowwallet/sparrow)），Apache License 2.0
- 本版本未修改任何钱包功能逻辑，仅替换界面显示资源
