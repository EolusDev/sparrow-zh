# Sparrow Wallet 中文汉化版

> 基于 [sparrowwallet/sparrow](https://github.com/sparrowwallet/sparrow) **v2.5.4** 的完整中文化项目
>
> **完整中文化 · 绿色便携 · 任意路径可运行 · 纯 Python 一键构建 · 字典可扩展 · 可回滚**

Sparrow Wallet 是一款专注安全与隐私的开源桌面比特币钱包。原版软件不提供多语言支持，界面文字 100% 硬编码在程序内部。本项目通过改写程序运行时镜像（jimage）实现**完整中文汉化**，并提供一条**不依赖 JDK、只用 Python 标准库**的可复现构建管线：既能直接下载现成的便携中文版，也能在任意版本的原版 Sparrow 上一键重新生成汉化镜像。

---

## 三种使用方式（按需选择）

### 方式一：直接下载中文便携版（最省事，普通用户）
1. 到 **Releases** 下载 `Sparrow-2.5.4-中文便携版.zip`
2. 解压到任意目录（中文、空格路径均可）
3. 双击 `Sparrow.exe` 即为完整中文界面，免安装、免联网、免运行环境

### 方式二：双击一键汉化（想给本机已装的 Sparrow 打补丁）
1. 安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 **Add Python to PATH**）
2. 双击 `中文补丁\一键汉化.bat`
3. 按提示把 Sparrow 安装文件夹拖进窗口（或直接回车自动探测），选择是否装回
4. 完成后启动 Sparrow 即为中文版；会自动在镜像旁保留 `modules.original.bak` 用于还原

### 方式三：命令行一键构建（进阶 / 跨版本 / 开发者）
```bash
# 对某个原版 Sparrow 构建汉化镜像并直接装回
python 中文补丁/patch/脚本/build.py --src "D:\Sparrow" --install

# 或指定原版 modules，只产出汉化镜像（不改动安装）
python 中文补丁/patch/脚本/build.py --modules "路径\modules" --out modules.zh

# 参数：--work 工作目录  --clean 清空重建  --install-to 装回到另一个 Sparrow 目录
```
`build.py` 会自动完成：**解包 jimage → 应用 FXML 字典 → 应用 Java 字典 → 就地重建镜像 → 完美哈希与中文统计校验**，全程纯 Python 标准库，**不需要安装 JDK**。

---

## Sparrow 升级到新版本后怎么办（重要）

本项目的工具链与版本号无关，新版出来后无需逆向重做：

1. 安装新版原版 Sparrow，拿到它的 `runtime\lib\modules`
2. 运行 `build.py` 对新镜像重新构建。绝大部分界面文字沿用现有 2359 条字典（由分批字典自动合并）
3. 用 `scan_remaining.py` 扫描新版里尚未覆盖的英文字面量：
   ```bash
   python 中文补丁/patch/脚本/scan_remaining.py
   ```
4. 把新增可见文案补进 `翻译字典\` 下对应的分批字典（或本地合并出的 java_trans_all.json；FXML 文案补 fxml_trans.json），重跑 `build.py` 即可
5. 与外部值比较的字符串（协议判断、过滤排序、SQL、日志）**不可翻译**，判别口径见 `中文补丁\安装说明.md`

---

## 特性

- **完整汉化**：31 个界面布局文件（FXML）+ 439 个 Java 类、2444 处界面文字中文化，成品镜像共 477 个资源含中文、20481 个中文字符
- **翻译字典 2359 条**：人工分批审定（仓库以 9 个分批字典存放，构建时自动合并），覆盖主界面、设置、交易、UTXO、多签、24 款硬件钱包导入向导、Payjoin、消息签名、私钥清扫、助记词等全部界面
- **纯 Python 工具链**：自行实现 jimage 解包 / 常量池改写 / 镜像重建 / 校验，只用标准库，别人克隆后无需 JDK 即可复现
- **绿色便携**：与安装位置无关，复制 / 移动 / 换机 / 带空格路径均直接可用（已实测）
- **可回滚**：保留原始镜像，一键还原英文原版
- **确定性可复现**：同一原始镜像 + 同一字典，构建产物字节一致（已用 SHA256 交叉验证）
- **专业术语保留英文**：Bitcoin / Taproot / Segwit / UTXO / PSBT / BIP39 / BIP32 / Tor / Electrum / Payjoin 等专名不译，避免歧义

---

## 界面效果

菜单「文件 / 视图 / 工具 / 帮助」、欢迎页「新建钱包 / 打开钱包 / 导入钱包 / 拖拽文件以打开」、底部状态栏「未连接（点击右侧开关进行连接）」均为中文，设置、交易、UTXO、多签与硬件钱包导入向导等全部对话框同样完成中文化（运行截图见 Release 资产）。

---

## 目录结构

```
sparrow-zh/
├── 中文补丁/
│   ├── 一键汉化.bat            # 双击入口（自动找 Python、进入交互）
│   ├── 应用补丁.ps1 / 还原.ps1  # PowerShell 装回 / 还原脚本
│   ├── 安装说明.md             # 详细原理、增量翻译与“不可翻译”判别口径
│   └── patch/
│       ├── 翻译字典/            # fxml_trans.json + 9 个 java_trans 分批字典（构建时自动合并）
│       └── 脚本/
│           ├── build.py            # ★ 一键编排：解包→翻译→重建→校验→(装回)
│           ├── jimage_extract.py   # 纯 Python jimage 解包（替代 JDK jimage extract）
│           ├── jimage_parse.py     # jimage 格式解析 / 完美哈希
│           ├── apply_fxml_trans.py # FXML 界面翻译
│           ├── apply_java_trans.py # Java class 常量池字面量翻译（不动标识符）
│           ├── rebuild_jimage.py   # 就地重建 jimage（保持哈希表/字符串表不变）
│           └── scan_remaining.py   # 扫描残留英文字面量，辅助增量翻译
├── README.md / CHANGELOG.md / LICENSE / .gitignore
└── Sparrow汉化使用说明与修改记录.txt
```

> `runtime\lib\modules`（成品汉化镜像，约 89.9MB）、原始镜像与中文便携版 zip 体积较大，**不纳入 git**，通过 **Releases** 分发。

---

## 汉化范围与术语口径

### 已汉化
| 范围 | 实测 |
|---|---|
| FXML 界面布局 | 31 个文件，27 个被改写，约 2700+ 中文字符 |
| Java 界面字面量 | 439 个类、2444 处替换（最终字典 2359 条） |
| 成品镜像 | 477 个资源含中文，共 20481 个中文字符；57359 个资源完美哈希 0 失配 |
| 覆盖功能 | 钱包创建/打开/密码、账户导入导出、多签、交易/UTXO、设置、服务器连接、PayNym、消息签名、私钥清扫、助记词、24 款硬件钱包导入向导 |

### 术语口径
- **保留英文**：Bitcoin / Taproot / Segwit / UTXO / PayNym / RBF / CPFP / PSBT / BIP39 / BIP32 / Tor / Electrum / Payjoin / Coldcard / Testnet 等专有名词
- **译为中文**：Address→地址、Balance→余额、Status→状态、Send→发送、Receive→接收、Settings→设置、Sign→签名 等通用词

### 有意保留英文
SQL 语句、日期/数字格式串、颜色/CSS、与外部值比较的错误串（Tor/服务器/协议诊断/硬件卡底层协议错误）、Electrum/Bitcoin Core 服务端日志。这些不参与界面展示或仅出现在异常日志，保留英文更利于对照上游排查。

---

## 技术原理（简述）

Sparrow 由 jpackage 打包，字节码与资源都在 `runtime\lib\modules` 这个 jimage 容器里。构建管线：

1. **解包**：`jimage_extract.py` 按 jimage 格式（小端、完美哈希、location 属性编码、0xCAFEFAFA + zlib 压缩块）纯 Python 解出 sparrow 模块
2. **FXML**：替换 `text/promptText/helpText` 属性与可见文本节点（注释块移到文件尾）
3. **Java class**：只替换常量池中**未被类名/字段/方法/描述符引用**的 `CONSTANT_Utf8` 字面量，并在字节长度变化后重建常量池，绝不改动标识符与字节码逻辑
4. **重建**：redirect 哈希表与字符串表保持字节不变，只重建 locations/offsets/data，改动资源以 raw 写入，保证 JVM 完美哈希查找依旧成立
5. **校验**：重新解析镜像，全量检查完美哈希失配数（须为 0）并统计中文资源

> 注：曾尝试用 `jlink` 整体重链接，因 JDK 工具链小版本与运行时不兼容导致启动失败（与翻译无关），已弃用；最终采用上述“就地改写 jimage”方案并通过实际启动验证。

---

## 已知限制

1. 硬件卡底层协议错误、Electrum / Bitcoin Core 服务端日志、Tor 底层错误保留英文（仅日志/异常场景）
2. 汇率模块需联网，离线时日志出现 WARN 属正常，不影响功能
3. 汉化只改界面显示文字，不改钱包数据与任何加密/签名逻辑；正式使用前仍请备份钱包

---

## 免责声明

- 本项目为 **Sparrow Wallet 的非官方汉化版本**，与官方团队无关
- 汉化仅修改界面文字，**不改变任何钱包功能、加密逻辑与安全行为**
- 请自行评估风险并做好钱包备份；因使用本项目产生的损失作者不承担责任
- 翻译字典、脚本与镜像为原项目的衍生修改，遵循原许可证条款分发

## 许可证

衍生自 [sparrowwallet/sparrow](https://github.com/sparrowwallet/sparrow)（**Apache License 2.0**），完整文本见 [LICENSE](LICENSE)，修改内容见 [CHANGELOG.md](CHANGELOG.md)。
