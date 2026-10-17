# 构建验证记录

## 独立 Android Chromium 测试浏览器（2026-10-18）

- 源码提交：`90a39867b3e2a4037133cbdc3aa65277002adb51`；源码树：`ec05e4d1de587a2a68f5bc402acfe27b502284cc`。只追加自定义提交，官方基线保持不变。
- 完整目标 `chrome_public_apk` 于 2026-10-18T03:00:51+08:00 构建完成；构建前后源码工作区干净。
- 复用已有文件解析、代理监视、IP 地区/定位协调器；新增 Chrome 启动、renderer 快照、导航确认、系统及 Profile 网络上下文、WebRTC/WebTransport 和存储权限接入。
- Chromium UA Client Hints 生产入口及 WebView 自动 brands 的 ASan/UBSan 回归通过（品牌生成器与平台边界使用适配器；Android APK 链接实际实现）。
- 44 项原生 HTTP/SOCKS5/认证/传输/请求头测试通过，新增 UA 与 Requested-With 原生替换、删除和默认保留测试；配置/文件、像素/音频、IP 地区解析及 SimpleURLLoader/Mojo 定位测试通过。
- Chrome 适配器、core、net impl、renderer、共享 startup_identity、WebView browser、network service 的 GN 头文件依赖检查通过；13 个文件新增 include 检查无违规；Chrome 适配翻译单元独立编译通过。
- 18 个补丁从官方基线逐个在临时 Git 索引重放，每一步源码树与原始提交完全一致。
- 安装脚本通过 bash 语法检查；示例通过 JSON 解析；检查页通过 JavaScript 语法检查。本地主机 HTTP 实测页面及头回显成功、其他路径返回 404，服务只返回指定诊断头，不返回 Authorization/Cookie。
- APK：`Chromium-158.0.8109.0-arm64-identity-rk14.apk`，513537599 字节；SHA-256：`13131b03d4e3789719a04d01018d02983950c902b23b1a7eb9975d958c5cff58`。
- 包名 `org.chromium.chrome`、版本 158.0.8109.0、minSdk 29、targetSdk 36、arm64 ABI、MANAGE_EXTERNAL_STORAGE/legacy 存储声明、ZIP 完整性、16 KiB ZIP/ELF 对齐、编译功能标记及签名前后 payload CRC/大小一致性均通过验证。
- RK14 v2/v3 签名通过；证书 SHA-256：`cf2ab3818595c4eda08cec72bbe39bc377a30b764a3eebde52536eae01808525`。私钥只在 Mac 临时解包并使用，已清理；服务器只接收签名 APK 与公开验证信息。
- 使用说明见 [CHROMIUM_BROWSER.md](CHROMIUM_BROWSER.md)，默认原生网络的测试配置见 [fingerprint.browser.json](../examples/fingerprint.browser.json)。
- 未执行真机安装或页面/Worker/代理出口验证。设备检查页和 USB 回显入口已经提供；本机 HTTP 测试不替代 Android 运行时验收。已交付的 WebView APK 仍对应后文记录的源码版本。

## 统一身份升级（2026-10-18）

- 源码提交：`cfc574e8e4f882047107c3fded8ec3e0f5a6f70a`；源码树：`17bac118bfaba9ef6df99c883ea39fd7564d1da5`。
- 固定提交的 Android arm64 完整目标在 2026-10-18T01:40:40+08:00 构建完成；构建前后源码工作区干净。
- 实际 Chromium 配置存储、文件读取及错误文件阻止网络测试通过；新增示例在全新进程导入通过。配置共 77 个字段，renderer 快照不含代理账号、密码和服务 URL。
- 稳定像素算法覆盖重复投影、子区域、行填充、alpha、RGBA/BGRA、WebGL 方向及音频边界；IP 数据解析使用实际 ICU 语言/时区校验。
- 43 项原生 HTTP/SOCKS5/传输/请求头测试通过，包含同步和异步分段认证、拒绝认证降级、Digest 重复失败限制、代理凭据与网站 401 隔离、私网 DNS 结果在创建 TCP 套接字前阻止、显式内网代理端点例外。
- 实际 SimpleURLLoader/TestURLLoaderFactory/Mojo 定位回归通过，包括共享解析器合并请求、缓存、授权、错误、销毁和 override 顺序。
- 既有 5 组主机回归通过，C++ 边界回归启用 ASan/UBSan；包含原来的 9 项质量回归和 81 种 fillRect 偏移。
- 原生测试目标的 GN 依赖检查通过；54 个文件的新增 C++ include 检查无违规；WebView browser、Blink common、network service、net 的 GN 头文件依赖检查通过。
- 16 个补丁从官方基线在临时索引逐个重放，每一步源码树与原始提交一致，最终匹配上述源码树。
- APK ZIP、包名 `com.android.webview`、版本、minSdk 29、targetSdk 36、arm64 ABI、16 KiB ZIP/ELF 对齐、编译后的功能标记及 RK14 v2/v3 签名均已核验；签名前后 ZIP 条目 CRC/大小一致。
- APK：`SystemWebView-158.0.8109.0-arm64-identity-rk14.apk`，329206939 字节；SHA-256：`f6649880cbd564a250a1c92ceda08b5ef7d277a3c50f8670ca903e4cf416c2fc`。
- 证书 SHA-256：`cf2ab3818595c4eda08cec72bbe39bc377a30b764a3eebde52536eae01808525`。只在本机解包并使用 RK14 签名材料，临时私钥已清理；服务器只接收签名 APK 和公开验证信息。
- 使用说明见 [IDENTITY_UPGRADE.md](IDENTITY_UPGRADE.md)，配置见 [fingerprint.identity.json](../examples/fingerprint.identity.json)，设备检查页见 [identity-smoke.html](../tests/identity-smoke.html)。
- 未接入 Android 测试设备。本次不宣称真机安装、首屏/Worker 地区、Canvas/WebGL/PBO、字体/语音播放或真实代理出口抓包已通过；这些路径已完成 Android 编译，并提供可执行的设备检查页。浮点/HDR/部分透明图像等保持原生，代理域名在远端解析的内网限制仍由代理服务保障。
- 多环境隔离、环境管理和自动化按要求不加入。

## 按出口 IP 分配地理位置

- 源码提交：`9f4b898a58ed183a1fabb060a39b4eeac8eefae4`；源码树：`1bdf1045027a1b877478aa05e71445b486282a80`。
- 完整 APK 增量构建通过（576 步，10 分 31 秒），最终按已提交源码打包于 2026-10-17 23:24:46（UTC+8）完成。服务器 build-only 脚本已修正源码标记刷新，artifacts/source-commit.txt 与本提交一致。
- 新增 geolocation.mode / endpoint / accuracy 三项，当前共 53 项配置。默认原生定位；显式 IP 模式在原有定位许可之后，通过该 WebContents 所属 StoragePartition 的网络工厂获取近似经纬度。
- 实际 Chromium SimpleURLLoader / TestURLLoaderFactory 和 Mojo 集成测试通过；下游设备上下文替换为测试对象。覆盖请求合并、override 先于绑定、成功缓存、数字 / 字符串坐标校验、非法 / 超大响应、网络超时、HTTP 错误、失败冷却、权限撤销 / 降级、DevTools override 清除恢复 IP 和销毁。
- 使用真实 Chromium 配置存储 / 文件读取测试及新进程导入通过，新增模式 / HTTPS 端点 / 精度范围拒绝测试通过。
- 既有配置 / 请求头、9 项方法回归、网络身份、自动 brands 的 ASan / UBSan 测试及 81 种 Canvas fillRect 组合通过。
- 10 个变更 C++ 文件的新增 include 依赖检查通过；测试目录已声明依赖。全部 13 个补丁在独立 Git 索引逐个应用后的源码树均与各原提交一致。
- APK ZIP 完整性、包名 / 版本、最低 SDK 29、arm64、16 KiB ZIP / ELF 对齐、编译功能标记及签名前后 ZIP CRC / 大小一致性检查通过。
- 使用用户提供的 RK14 证书在本机签名，私钥未传输，v2 / v3 校验通过。
- APK：`SystemWebView-158.0.8109.0-arm64-ip-geo-rk14.apk`，329141403 字节；SHA-256：`95db227582bb0bf067efcb07205af6bb36b1ba53cf35d9bd39fb1c54cc8e79d0`。
- 证书 SHA-256：`cf2ab3818595c4eda08cec72bbe39bc377a30b764a3eebde52536eae01808525`。
- 尚未进行真机安装、代理出口 / DNS 抓包、宿主定位权限、GPS 行为及页面 getCurrentPosition / watchPosition 验收。测试覆盖队列和网络策略，不替代真实设备验证。
- 本次不自动调整语言、时区，也不实现每 Profile 独立指纹。参考项目公开前端 / 管理和自动化代码，未公开 Chromium 内核修改，不能以界面选项证明全部底层效果。配置见 [UNIFIED_CONFIG.md](UNIFIED_CONFIG.md)。

## 启动自动读取文件与 brands 自动生成

- 源码提交：`ac5ae14b50b7a5e8c281b56664d4eef416ec528a`。
- 最终源码树：`9c7cb346b427311df3ca79047f55520e07aaba18`。
- 完整 APK 构建完成：2026-10-17 22:32:26（UTC+8）。
- 宿主进程初始化 WebView 时读取 `/sdcard/xpChromium/fingerprint.json` 并冻结快照；旧公开 Java 配置 API / SDK 已移除，生产代码无系统属性读取。
- 未填写 brands / fullVersionList / fullVersion 时，默认与 AndroidX 元数据路径按合法 UA Chrome 四段版本或真实内核版本自动生成；显式配置仍优先，保留低熵规则。
- 实际 Chromium 文件读取 / 配置存储集成测试通过，覆盖缺失、正常、空文件、超大文件、目录、FIFO、权限拒绝、非法 JSON，以及失败原子保留、并发快照、冻结和新进程导入。
- 自动 brands 测试使用实际 UA 解析与元数据策略方法，上游品牌生成和类型边界使用适配器；ASan / UBSan 通过。原生品牌生成 API 在最终 APK 中编译 / 链接通过。
- 既有配置 / 请求头、9 项方法回归、网络策略及 81 种 fillRect 组合检查通过；10 个变更 C++ 文件依赖检查通过。
- 直接解析最终构建 APK DEX，确认旧公开 FingerprintConfig 类和 AwFingerprintConfig.configure 方法不再存在。
- 全部 12 个补丁在独立临时 Git 索引逐个应用，每一步的源码树均与原始提交一致，最终与已编译版本一致。
- 使用用户提供的 RK14 证书在本机签名，私钥未传输；v2 / v3、包名、最低 SDK 29、arm64、16 KiB ZIP / ELF 对齐、ZIP 完整性和签名前后 CRC / 大小一致性校验通过。
- APK：`SystemWebView-158.0.8109.0-arm64-file-config-rk14.apk`，329075867 字节。
- SHA-256：`7cc7fbc56f49222ccd6eb36c8996da7197b6eabb907cbf01bdc92e9ba4fb7718`。
- 证书 SHA-256：`cf2ab3818595c4eda08cec72bbe39bc377a30b764a3eebde52536eae01808525`。
- 尚未完成真机安装、Android 存储权限、宿主启动读取、页面 / Worker 和代理抓包验证。文件读取使用宿主 App UID 的权限；Android 11+ 的分区存储可能阻止该路径访问，provider 签名不赋予宿主权限。
- 修改配置后需完整重启宿主 App。详见 [UNIFIED_CONFIG.md](UNIFIED_CONFIG.md)。

## 统一 JSON 配置入口

- 源码提交：`bf95d218bcae6441438511bea18b89c4aa2ad4a2`。
- 最终源码树：`66226f12a833d09aec36bdd285fa72d5fe951626`。
- 完整 APK 构建完成：2026-10-17 21:55:15（UTC+8）。
- 生产配置实现无 Android 系统属性读取，统一入口覆盖现有 50 项配置，取消旧 UA 分段；Canvas fillRect 噪声改为显式开启。
- 实际 Chromium 配置存储集成测试通过：格式 / 类型 / 范围 / 未知键、brands、代理 URI、失败保留旧配置、整份替换、4 线程并发快照、启动冻结；新进程导入同一序列化 JSON 通过。
- 既有配置 / 请求头、9 项方法回归、网络身份 / 策略组装、81 种 fillRect 组合通过；getter / 方法测试启用 ASan / UBSan，配置存储边界使用内存适配器，实际存储由独立集成测试覆盖。
- 12 个变更 C++ 文件依赖检查通过。Java/JNI、浏览器启动冻结、renderer 初始化和全部调用点完成 APK 编译 / 链接。
- 直接解析 APK DEX 方法表，确认反射入口 `com.android.webview.chromium.FingerprintConfig.configure` 保留原名；宿主 SDK 封装使用公开 Android SDK 编译通过。
- 全部 11 个补丁逐个还原后的源码树与原始提交一致。
- APK ZIP 完整性、包名、最低 SDK 29、arm64、16 KiB 对齐及 RK14 v2 / v3 签名校验通过；签名前后 ZIP CRC 和大小一致，签名临时材料已清理。
- APK：`SystemWebView-158.0.8109.0-arm64-unified-rk14.apk`，329075867 字节。
- SHA-256：`b8c21a39baaca59df76d98f0218f4be7b30b7d8e66daa18caa1f3b322ca0878f`。
- 未完成真机宿主 API 调用、页面 / Worker 端到端及代理抓包测试。本节对应旧版宿主 Java API，后续版本已改为启动文件读取；旧 setprop 不再生效。

## 网络策略升级

- 源码提交：`1598a163cff1c3ed23c6406f8bcdded6cd4c06ea`。
- 最终源码树：`8944b1caec621d4e13dcb3ad50775bbdb19f5953`。
- 完整 APK 构建完成：2026-10-17 16:38:16（UTC+8）。
- 4 组主机回归通过，包括网络身份 / 策略组装、既有配置和请求头、9 项质量修复回归及 81 种 Canvas 偏移；C++ 主机测试启用 ASan / UBSan。
- 9 个变更 C++ 文件的依赖检查通过；生产网络对象和 5 个原生网络策略测试用例通过 Android 编译。原生用例尚未在设备执行。
- 10 个补丁逐个还原后的源码树均与各原始提交一致。
- APK ZIP 完整性、包名、最低 SDK 29、arm64、16 KiB 对齐及 RK14 v2 / v3 签名校验通过；签名前后 ZIP 条目的 CRC 和大小一致。
- APK：`SystemWebView-158.0.8109.0-arm64-network-rk14.apk`，329075867 字节。
- SHA-256：`4b3670cf68c1dea8abc626b6d0e9db4a42cb9e823ef5c5b5c8ec9740d94dd70f`。
- 临时签名材料已清理，APK 和私钥不入库。
- 当前未完成真机安装、代理出口、DNS / WebRTC 抓包及页面端到端测试。网络策略的作用范围见 [NETWORK_POLICY.md](NETWORK_POLICY.md)。

## 首次导入版本的验证

记录对应源码提交 `02b7cf0fc73439a0eaaacd262cba3307ce0d02e2`，最终源码树 `2b8375977d6175cc2f70f00a4db68a737b9330a1`。这是本次导入的构建记录，不代表以后每次提交都已完成这些验证。

- 版本：Chromium `158.0.8109.0`，Android 10+ / arm64。
- 服务器：Ubuntu 22.04，16 核、31 GiB RAM。
- 完整 APK 编译于 2026-10-17 14:46:29（UTC+8）完成，目标 `system_webview_64_apk`。
- 配置解析和请求头等主机测试通过，启用 ASan / UBSan。
- 9 项质量修复回归通过：规范 IPv4、ICE 空白保留、无效 candidate 前缀、UA 元数据非法 ASCII、主开关读取次数、音频内部读取、音频清零复用、Canvas 其他行像素、全透明 Canvas 免复制。
- Canvas fillRect 全部 81 种偏移组合检查通过。
- 29 个变更 C++ 文件的依赖检查通过。
- APK 的 ZIP 完整性、包名、arm64 ABI、最低 SDK 29、16 KiB 对齐及签名检查通过。
- 使用用户提供的 RK14 证书签名，v2 / v3 签名校验通过。

已交付的签名 APK：`SystemWebView-158.0.8109.0-arm64-reviewed-rk14.apk`。

```text
SHA-256: 329dfa33611af100be31b04914b776825307a89df04a21993ea196176130ceda
Bytes:   329075867
Certificate SHA-256:
cf2ab3818595c4eda08cec72bbe39bc377a30b764a3eebde52536eae01808525
```

从应用补丁后的源码根目录运行已有主机回归：

```sh
python3 webview_custom/test_noise.py
python3 webview_custom/test_properties.py
python3 webview_custom/test_review_regressions.py
```

这些测试需要主机 C++ 编译器；测试边界使用轻量适配器，实际 Android 类型及链接由 APK 编译检查。尚未进行 RK14 真机安装、属性权限、页面和真实网络验证。

## 补丁仓库导入验证

- 在独立临时 Git 索引中从官方基线逐个应用 9 个补丁，每一步的源码树均与原始提交一致，最后与已编译版本一致；没有改动正在使用的源码工作区。
- 补丁管理工具通过临时仓库集成检查：导出与校验、包含二进制资源的顺序应用、最终源码树一致性、错误基线拒绝、脏工作区拒绝、补丁损坏拒绝。
