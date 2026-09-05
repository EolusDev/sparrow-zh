# Sparrow Wallet 2.5.4 中文汉化便携版

> 基于 [sparrowwallet/sparrow](https://github.com/sparrowwallet/sparrow) **v2.5.4** 的完整中文化版本
>
> **绿色便携 · 任意路径可运行 · 一键还原英文原版 · 翻译字典可扩展**

Sparrow Wallet 是一款专注安全与隐私的开源桌面比特币钱包。原版软件不提供多语言支持，界面文字 100% 硬编码在程序内部。本项目通过改写程序运行时镜像（jimage）实现了**完整中文汉化**，并打包为**便携版（绿色版）**：解压到任何目录、任何电脑，双击 `Sparrow.exe` 即为中文界面，无需安装、无需联网、无需额外运行环境。

---

## 特性

- ✅ **完整汉化**：31 个界面布局文件（FXML）+ 470+ 个 Java 类、约 3500 处界面文字全部中文化
- ✅ **翻译字典 2330 条**：六批人工审定，覆盖主界面、设置、交易、UTXO、多签、硬件钱包导入向导、Payjoin、消息签名、私钥清扫等全部界面
- ✅ **绿色便携**：与安装位置无关，复制/移动/换机均直接可用（已实测带空格路径启动正常）
- ✅ **可回滚**：一键脚本还原原始英文版，原始镜像备份保留
- ✅ **可扩展**：翻译字典为 JSON 结构，按说明追加词条即可增量翻译，脚本幂等可重跑
- ✅ **专业术语保留英文**：Bitcoin / Taproot / Segwit / UTXO / PSBT / BIP39 / BIP32 / Tor / Electrum / Payjoin 等专名不译，避免歧义

---

## 快速开始

### 方式一：便携版（推荐）
1. 下载 Releases 中的 `Sparrow-2.5.4-中文便携版.zip`（本仓库 Release 附件）
2. 解压到任意目录（中文/空格路径均可）
3. 双击 `Sparrow.exe`，即为完整中文界面

### 方式二：本仓库直接使用
仓库内容即为完整程序，克隆/下载后：
```bash
Sparrow.exe                # 直接启动（中文界面）
中文补丁\应用补丁.ps1       # 重新应用汉化（误还原后使用）
中文补丁\还原.ps1           # 一键还原英文原版
```

> 说明：`runtime\lib\modules`（汉化后镜像 89.9MB）与 `中文补丁\backup\modules.original`（原始英文镜像 85.8MB）体积较大，以 Release 附件形式提供，未纳入 git 仓库。若克隆仓库后缺少镜像，请从 Releases 下载后放回对应位置。

---

## 截图

![Sparrow 2.5.4 中文界面](images/screenshot.png)

主界面：菜单「文件 / 视图 / 工具 / 帮助」、欢迎页「新建钱包 / 打开钱包 / 导入钱包 / 拖拽文件以打开」、状态栏连接提示均为中文。

---

## 目录结构

```
Sparrow/
├── Sparrow.exe                  # 主程序（jpackage 启动器）
├── app\                         # 应用配置（Sparrow.cfg 等）
├── runtime\                     # 运行时（lib\modules 为已汉化镜像）
├── 中文补丁\
│   ├── patch\
│   │   ├── modules.patched      # 汉化镜像（89,890,740 字节）
│   │   ├── 翻译字典\*.json       # 全部翻译字典（可扩展）
│   │   └── 脚本\*.py            # 汉化管线脚本（类改写/镜像重建/校验）
│   ├── backup\
│   │   └── modules.original     # 原始英文镜像（回滚基线）
│   ├── 应用补丁.ps1             # 一键应用汉化
│   ├── 还原.ps1                 # 一键还原英文
│   └── 安装说明.md              # 详细使用与增量翻译说明
├── images\screenshot.png        # 汉化效果截图
├── README.md                    # 本文件
├── CHANGELOG.md                 # 汉化修改记录
└── Sparrow汉化使用说明与修改记录.txt  # 完整使用说明 + 汉化事件记录
```

---

## 汉化范围与术语口径

### 已汉化
| 范围 | 说明 |
|---|---|
| FXML 界面布局 | 31 个文件全部中文化（约 2700+ 中文字符） |
| Java 界面字面量 | 470+ 个类、约 3500 处（翻译字典 2330 条） |
| 覆盖模块 | 钱包创建/打开/密码、账户导入导出、多签钱包、交易/UTXO、设置、服务器连接、PayNym、消息签名、私钥清扫、助记词、全部硬件钱包导入向导（Coldcard / Cobo / Keystone / Passport / Jade / SeedSigner / BlueWallet / Specter / BitBox02 等 24 款） |

### 术语口径
- **保留英文**：Bitcoin / Taproot / Segwit / UTXO / PayNym / RBF / CPFP / PSBT / BIP39 / BIP32 / Tor / Electrum / Payjoin / Coldcard / Testnet 等专有名词
- **译为中文**：Address→地址、Balance→余额、Status→状态、Send→发送、Receive→接收、Settings→设置、Sign→签名 等通用词

### 有意保留英文的部分
SQL 语句、日期/数字格式串、颜色/CSS、与外部值比较的错误串（Tor/服务器/协议诊断/硬件卡底层协议错误）、Electrum/Bitcoin Core 服务端日志消息。这些内容不参与界面展示或仅出现在异常日志，保留英文更利于对照上游文档排查，不影响使用。

---

## 校验信息

| 镜像 | 大小 | SHA256 |
|---|---|---|
| 汉化镜像（modules.patched） | 89,890,740 字节 | `95B294A9010C58E962FC20EFE55BF4ACF0DC603E294989BC860AEFDDDA30DBBB` |
| 原始镜像（modules.original） | 85,822,080 字节 | `8142315D03785C2078AABA3339CD92E8139032C50310DAEBC4A160ED472F705A` |

镜像通过 `jimage verify`（exit 0），57359 个资源 perfect-hash 全量校验 0 失配。

---

## 已知限制

1. 硬件卡（Satochip / Keycard / Tapsigner）底层协议错误、Electrum / Bitcoin Core 服务端日志消息、Tor 底层错误保留英文（仅日志/异常场景）
2. 汇率模块需联网获取，网络不可达时日志出现 WARN，属正常现象，不影响功能
3. 汉化通过改写运行时镜像实现，不影响钱包数据与功能逻辑；仍建议使用前备份钱包文件

---

## 如何参与翻译

翻译字典位于 `中文补丁\patch\翻译字典\java_trans_all.json`，结构为：
```json
{ "English original string": "中文译文", ... }
```
新增词条后按序运行（需 JDK 25 的 `jimage` 工具）：
```bash
python 中文补丁\patch\脚本\apply_java_trans.py   # 应用 Java 字面量翻译（幂等）
python 中文补丁\patch\脚本\rebuild_jimage.py     # 重建汉化镜像
中文补丁\应用补丁.ps1                             # 安装新镜像
```
> 注意：与外部值比较的字符串（协议判断、过滤、排序等）不可翻译，以免破坏功能，详见 `中文补丁\安装说明.md`。

---

## 免责声明

- 本项目为 **Sparrow Wallet 的非官方汉化版本**，与 Sparrow Wallet 官方团队无关
- 汉化仅修改界面显示文字，**不改变任何钱包功能、加密逻辑与安全行为**；但仍建议在正式使用前验证、并做好钱包备份
- 使用本项目造成的任何损失，作者不承担责任；请自行评估风险
- 本项目的翻译字典、脚本与镜像为对原项目的衍生修改，遵循原项目许可证条款分发

---

## 许可证

本仓库内容（汉化补丁、翻译字典、脚本、文档）基于 [sparrowwallet/sparrow](https://github.com/sparrowwallet/sparrow) **Apache License 2.0** 许可的衍生修改：

- 原项目：Sparrow Wallet © Sparrow Wallet 开发者，[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- 本仓库在原作品基础上修改了程序界面资源，按 Apache-2.0 条款分发，修改内容见 [CHANGELOG.md](CHANGELOG.md)

完整许可证文本见 [LICENSE](LICENSE)。
