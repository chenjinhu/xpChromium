# Chromium 130 补丁向 158 的迁移

目标为 158.0.8109.0 / Android 10+ / arm64。保留此前 Window/document/navigator Replaceable、Canvas fillRect 噪声及桌面定制。26 个原补丁按功能迁移，不执行旧下载脚本、不回退 Chromium 版本。

## 配置

本版本已取消系统属性读取。使用宿主 App 的 `Fingerprint.configure(json)` 统一入口，调用必须早于 WebView 启动；完整格式和生命周期见 [UNIFIED_CONFIG.md](UNIFIED_CONFIG.md)。以下字段均放在 `settings` 对象内，不带 `chromium.` 前缀。数字 / 布尔值使用 JSON 原生类型。未知字段、类型错误或越界使整份配置失败，旧配置保持不变。

| settings 字段 | 用途及格式 |
| --- | --- |
| config.x_requested_with | 未设置：原生包名策略；非空合法字符串：替换；空字符串：删除 |
| network.proxy | 进程启动代理策略，支持单个 `http://`、`https://` 或 `socks5://` 端点；默认不启用。入口拒绝非法 URI，修改需重启宿主进程，详见 [NETWORK_POLICY.md](NETWORK_POLICY.md) |
| navigator.useragent | 完整 HTTP / JS UA 字符串，最多 4096 字节；拒绝非法控制字符。不再分段 |
| navigator.userAgentMeta.brands / fullVersionList | `[{"brand":"Chromium","version":"158"}]` 数组；完整版本列表单独配置 |
| navigator.userAgentMeta.mobile / wow64 | JSON 布尔值 true/false |
| navigator.userAgentMeta.platform / platformVersion / architecture / model / fullVersion / bitness | UA-CH 字段，要求可序列化的 ASCII；保留高熵提示权限策略与按需发送规则 |
| navigator.productSub / vendor / platform | JS Navigator 字符串，含继承自 NavigatorID 的字段 |
| navigator.cookieEnabled | JSON 布尔值 true/false；仅报告值，不改变 Cookie 权限和存储 |
| navigator.hardwareConcurrency | 整数 1..1024 |
| navigator.deviceMemory | 有限数 0.125..1024（GiB 的报告值） |
| navigator.maxTouchPoints | 整数 0..100 |
| document.clientWidth / clientHeight | 0..100000，仅 viewport 元素的 getter |
| window.innerWidth / innerHeight | 0..100000，兼容原包作为 outer 的回退值 |
| window.outerWidth / outerHeight | 0..100000，新增独立配置，优先于 inner 回退值 |
| window.devicePixelRatio | 有限数 0.01..100；报告值，不改变硬件分辨率 |
| screen.width / height / availWidth / availHeight | 整数 0..100000 |
| screen.colorDepth | 整数 1..128，pixelDepth 跟随 |
| navigator.battery.charging | JSON 布尔值 true/false |
| navigator.battery.chargingTime / dischargingTime | 有限秒数 0..1e15 |
| navigator.battery.level | 有限数 0..1 |
| navigator.bluetooth | false/0 时 getter 返回 null；true 不强制打开原本不可用的 API |
| navigator.connection.type | bluetooth/cellular/ethernet/none/other/unknown/wifi/wimax，按 158 IDL 枚举校验 |
| navigator.connection.effectiveType | slow-2g/2g/3g/4g，按 IDL 校验 |
| navigator.connection.downlinkMax / downlink | 有限数 0..1e9（Mbps） |
| navigator.connection.rtt | 整数 0..2147483647（毫秒） |
| webrtc.public_ip / private_ip | 有效 IPv4；替换 ICE candidate/address/relatedAddress/toJSON 的报告值，保留端口和 raddr/rport 结构；IPv6/mDNS 保持原样，不改变真实网络出口。network.proxy 启用时不做文本改写 |
| webrtc.sdp_redact | 独立开关；true/1 时移除 SDP candidate 行并将 c=IN IP4 置为 0.0.0.0。默认不做；可能影响复制 SDP 建立连接。network.proxy 启用时不做文本改写 |
| audio.randomDouble | 有限配置数，0 关闭；每个声道首次有效 JavaScript 读取统一处理一次，内部播放、卷积与清零不会触发加噪，增量 clamp(seed*0.123, -1e-5, 1e-5)，保留零和非有限样本；两种读取接口共享数据 |
| webgl.unmasked_vendor / unmasked_renderer | 仅修改 WEBGL_debug_renderer_info 解锁后的字符串；保留扩展及 context-lost 检查，不改变真实 GPU |
| canvas.toDataUrl.randomDouble | 有限配置数，0 关闭；通过 seed 位混合选择起点，扫描实际像素寻找不透明的 8-bit RGBA/BGRA 像素，仅找到时复制并翻转一个颜色位后编码。跳过行填充；无候选像素不分配副本。保持原画布及编码格式；不影响 toBlob/getImageData |

配置入口拒绝数值类型错误、越界及非有限值，整份失败不改变旧配置。各项仅改变暴露的值或文中所述数据；不绕过 API 可用性、权限、安全上下文或宿主设置。

新增 `canvas.fillRectNoise` 布尔项；默认关闭，仅在统一配置 enabled=true 且该项=true 时开启原 fillRect 噪声。

## 原补丁处理

- 0001：迁至 components/embedder_support 的新 UA 入口，并保留 renderer/worker 覆盖。
- 0002、0014：统一 UA-CH 数据源，分别处理 major/full brands，保留高熵权限控制。
- 0003、0005：合并为 WebView 请求头策略，覆盖已有值、删除值、重定向及预取；不修改全局 net::HttpRequestHeaders。
- 0004、0020：只有 include/空行，无行为，不移植无效修改。
- 0006..0013、0015..0018、0024：迁移对应 getter，补齐验证，适配新枚举接口。
- 0019、0021：修复条件分支覆盖与无条件写死 IP，使用结构化 token 替换，SDP 脱敏单独启用。
- 0022、0023：修复未初始化标志、声道处理范围、重复加噪及复制前后不一致；限制噪声幅度。
- 0025：改为像素副本编码，避免破坏 PNG/JPEG/WebP 编码数据。
- 0026：旧功能已移除，158 的原生自动 X-Requested-With 注入由新策略协调，不重新引入旧 flag。

## 验证

`python3 webview_custom/test_properties.py` 编译生产 getter、实际请求头策略函数和配置存储边界适配器，覆盖属性解析、请求头操作、UA、brands、ICE/SDP、音频与像素索引，并启用 AddressSanitizer/UndefinedBehaviorSanitizer。

`python3 webview_custom/test_review_regressions.py` 执行实际生产方法体的 9 个回归用例；仅模拟配置存储、容器和编码器边界，不模拟方法实现。测试不验证 PNG 编码器本身或 V8 行为；APK 构建检查实际 Android 类型、编译和链接。现有 `test_noise.py` 验证 81 种 fillRect 偏移。

实际 JSON 存储测试见 UNIFIED_CONFIG.md；主机测试不能代替 RK14 的宿主调用、真实网络和页面测试。

## 代码质量修复

- WebView 专用配置实现移到 Blink common，移除 base 中的产品策略和大段内联代码；Bionic 头文件保留在实现文件。
- 每次操作捕获同一份不可变配置快照；UA-CH 在浏览器侧创建元数据时处理，renderer setter 和公共序列化保持原生行为。
- AndroidX 自定义 UA 元数据与默认元数据使用同一校验；非法 ASCII 值回退原值。
- 内部音频访问不触发噪声；JavaScript 两种读取接口仍共享一次处理后的数据，Zero 重置处理状态。
- ICE 仅处理 candidate 前缀和规范 IPv4，保留原有空白、端口及扩展；不修改不符合结构的输入。
- Canvas 遍历真实像素以避免遗漏其他行，不读写 padding，不为全透明图创建副本。
