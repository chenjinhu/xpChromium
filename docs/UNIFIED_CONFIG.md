# 启动文件指纹配置（version 1）

WebView 在宿主进程初始化时自动读取固定路径：

```text
/sdcard/xpChromium/fingerprint.json
```

宿主 App 无需调用配置方法，也无需集成 Java SDK。旧 `Fingerprint.configure(json)` 入口和系统属性输入均已移除。本版本通过这一个文件加载配置，浏览器、renderer、Worker 和网络侧共用同一份已校验快照。

## 文件示例

```json
{
  "version": 1,
  "enabled": true,
  "settings": {
    "navigator.useragent": "Mozilla/5.0 (Linux; Android 10; K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/158.0.8109.0 Mobile Safari/537.36",
    "navigator.hardwareConcurrency": 8,
    "navigator.deviceMemory": 8,
    "navigator.maxTouchPoints": 5,
    "navigator.userAgentMeta.mobile": true,
    "navigator.userAgentMeta.platform": "Android",
    "config.x_requested_with": "",
    "canvas.fillRectNoise": false
  }
}
```

保存为 UTF-8 JSON。完整示例见 [fingerprint.example.json](../examples/fingerprint.json)。三个顶层字段均为必填，不能增加其他顶层字段。`settings` 字段不带 `chromium.` 前缀，大小写敏感。数字 / 布尔值使用 JSON 原生类型，不能写成字符串。完整字段清单和范围见 [PROPERTY_PATCHES.md](PROPERTY_PATCHES.md)。

## brands 自动生成

`navigator.userAgentMeta.brands`、`fullVersionList` 和 `fullVersion` 均可省略。启用定制时，默认和 AndroidX 自定义元数据路径均使用 Chromium 原生 `GenerateBrandVersionList`，保留 GREASE 和品牌排序规则。

- 自定义 `navigator.useragent` 包含合法四段 `Chrome/版本` 时，自动跟随该版本。例如 `Chrome/157.0.8000.2` 生成主版本 `157` 和完整版本 `157.0.8000.2`。
- 未配置 UA 或无法从 UA 解析合法四段版本时，使用实际内核版本，本次为 `158.0.8109.0`。
- 自动生成 Chromium / Android WebView 品牌；不会把任意 UA 字符串推断成其他浏览器产品。
- 显式传入 brands / fullVersionList / fullVersion 仍优先，调用方应确保这些手工值互相一致。
- 低熵路径只生成主版本品牌，不补发高熵字段；原有 Client Hints 权限和按需发送规则保留。

如果要手工覆盖，brands / fullVersionList 使用 `[{"brand":"...","version":"..."}]` 数组。

## SOCKS5 和恢复默认

代理配置可以直接写入文件：

```json
{"version":1,"enabled":true,"settings":{"network.proxy":"socks5://192.0.2.1:1080"}}
```

把示例地址换成设备可达的代理；也支持单个 `http://` / `https://` 端点，尚不支持用户名密码认证。省略 network.proxy 时使用原生网络。代理模式会限制非代理 UDP、拒绝 WebTransport 并停用旧 ICE/SDP 文本改写，详见 [NETWORK_POLICY.md](NETWORK_POLICY.md)。

恢复默认配置，可以删除文件，或保存：

```json
{"version":1,"enabled":false,"settings":{}}
```

这会关闭字段覆盖、定制代理和 Canvas 扰动；早期 Window/document/navigator 的 IDL 定制仍保留。

## 加载时机和失败处理

- 宿主浏览器进程加载 WebView 原生库并完成 JNI 初始化后立即读取一次，再冻结配置；早于后续浏览器启动和网络上下文创建。renderer 不访问外部存储，只接收浏览器传递的快照。
- 文件必须是普通文件，大小为 1..32768 字节。按一个文件描述符读取，限制最大读入大小；目录、FIFO、空文件和超大文件被拒绝。单项字符串最多 4096 字节。
- 文件不存在：保留默认配置，记录 INFO；不会创建目录或示例文件。
- 无读取权限、读取失败、内容非法、字段未知或数值越界：整份拒绝，保持默认配置并记录 ERROR，不输出配置内容。若文件里的代理配置有误，整份文件不会生效。
- 配置在进程中保持不变。修改或创建文件后，必须完整退出并重启宿主 App；只刷新页面或重启 renderer 不会重新读取。
- 建议用临时文件写完后原子替换正式文件，避免启动正好读到写入中的内容。
- 当前作用范围为宿主进程。不同宿主进程读取同一路径，并各自保存启动时快照；尚不能为同一进程的多个 WebView Profile 指定独立文件。

## Android 存储权限

WebView 内核运行在宿主 App 的 UID 下，读取此路径使用宿主的权限。Android 10 的外部存储规则以及 Android 11+ 的分区存储限制可能阻止读取共享目录内的 JSON；普通媒体读取权限通常不能授予任意 JSON 文件访问。

对于 Android 11+，通常需要宿主具备适用的“所有文件访问权限”或目标 ROM 已授予相应目录访问能力；目标 Android 版本、targetSdk 和 ROM 策略需在设备上确认。给 WebView provider APK 加权限或使用 RK14 签名，不能自动赋予宿主此权限。程序不会绕过权限检查，也不会自动弹窗申请。文件读取权限应在首次初始化 WebView 前准备好。

可在 logcat 中检索 `Loaded fingerprint configuration`、`No fingerprint configuration file` 或 `Fingerprint file was not applied` 判断加载结果。日志显示加载成功也不等于全部页面和网络行为已经验证。

## 验证

实际 Chromium 配置 / 文件集成测试：

```sh
gn gen out/Fingerprint-host --root-target=//webview_custom:fingerprint_config_test \
  --args='is_debug=false is_component_build=false symbol_level=0 use_remoteexec=false target_os="linux" target_cpu="x64"'
autoninja -C out/Fingerprint-host -j 16 fingerprint_config_test
out/Fingerprint-host/fingerprint_config_test
```

覆盖文件缺失、正常读取、空文件、大小上限、目录、FIFO、权限拒绝、非法 JSON，以及配置原子拒绝、并发快照、冻结和新进程导入。`test_auto_brands.py` 执行实际 UA 版本解析和元数据策略方法，类型与上游品牌生成函数边界使用适配器；原生品牌函数与 Java/JNI 自动入口由 APK 编译 / 链接检查。

既有配置 / 请求头、9 项方法回归、网络身份和 81 种 Canvas 组合测试继续保留。宿主实际启动读取、Android 存储权限、页面 / Worker 结果及代理出口仍需真机验证。`smoke.html` 默认按 fillRect 噪声关闭检查；显式开启时加载 `smoke.html?noise=on`。
