# 统一指纹配置入口（version 1）

本版本取消 Android `chromium.*` 系统属性读取。宿主 App 在 WebView 启动前调用一次 JSON 配置入口，浏览器、renderer、Worker 和网络侧使用同一份配置。旧 `setprop` 命令不再生效，APK 签名不影响配置能力。

## 宿主 App 接入

把 [android/Fingerprint.java](../sdk/Fingerprint.java) 复制到宿主项目，在主线程、创建第一个 WebView 之前调用：

```java
import com.xpchromium.Fingerprint;

// 可在 Application.onCreate 中执行，必须早于任何 WebView、预热、预取、
// CookieManager、ServiceWorkerController 等可能启动 WebView 的调用。
Fingerprint.configure(json);
WebView webView = new WebView(context);
```

封装通过公开 API `WebView.getWebViewClassLoader()` 获取当前 provider，调用 `com.android.webview.chromium.FingerprintConfig.configure(String)`。不依赖隐藏 Android API、root、系统属性、共享文件或网页 JS 注入。只在安装本版本 xpChromium provider 时可用；宿主自身仍应遵循 WebView 的数据目录等初始化要求。

provider 方法返回空字符串表示成功，非空字符串表示拒绝原因；封装将拒绝转换为异常。调用过晚、安装了其他 provider 或配置有误时，应处理错误，不应忽略后继续当作已配置成功。宿主代码需由你集成，本仓库没有自动改写你的浏览器 App。

## JSON 格式

```json
{
  "version": 1,
  "enabled": true,
  "settings": {
    "navigator.useragent": "Mozilla/5.0 (Linux; Android 10; K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/158.0.0.0 Mobile Safari/537.36",
    "navigator.hardwareConcurrency": 8,
    "navigator.deviceMemory": 8,
    "navigator.maxTouchPoints": 5,
    "navigator.userAgentMeta.mobile": true,
    "navigator.userAgentMeta.platform": "Android",
    "navigator.userAgentMeta.brands": [
      {"brand": "Chromium", "version": "158"},
      {"brand": "Android WebView", "version": "158"}
    ],
    "config.x_requested_with": "",
    "canvas.fillRectNoise": false
  }
}
```

这是调用示例，不是自动生成的完整设备身份。UA 和 UA-CH 的关联值仍由调用方配套提供。

三个顶层字段均为必填，不能增加其他顶层字段。`settings` 使用不带 `chromium.` 前缀的字段名，清单见 [PROPERTY_PATCHES.md](PROPERTY_PATCHES.md)。字段名区分大小写。数字和布尔值使用 JSON 原生类型，不要写成字符串。

- `navigator.useragent` 是一个完整字符串，不再使用 `useragent2` / `useragent3` 分段；最多 4096 字节。
- brands / fullVersionList 使用 `[{"brand":"...","version":"..."}]` 数组，不再使用 `&` 拼接字符串。
- `config.x_requested_with` 缺省为原生策略，`""` 删除，非空合法字符串替换。
- `network.proxy` 缺省为原生网络；设置时必须是单个合法 `http://`、`https://` 或 `socks5://` URI。用户名密码认证尚未实现。
- `canvas.fillRectNoise` 默认关闭；只有 `enabled:true` 且该项为 `true` 时开启旧 fillRect 噪声。上游运行时功能开关仍可进一步禁用。
- 单项字符串最多 4096 字节，完整 JSON 最多 32768 字节。UA-CH 结构化字符串限制为可序列化 ASCII；数值沿用原实现范围。

## SOCKS5 和恢复默认

启用代理的最小配置：

```json
{"version":1,"enabled":true,"settings":{"network.proxy":"socks5://192.0.2.1:1080"}}
```

示例地址必须替换为设备可达的代理。代理模式仍会禁止非代理 UDP、拒绝 WebTransport，并停用旧 ICE/SDP 文本改写。详见 [NETWORK_POLICY.md](NETWORK_POLICY.md)。无效代理 URI 在配置入口被拒绝，当前已接受的整份配置保持不变。

启动前恢复配置默认值：

```json
{"version":1,"enabled":false,"settings":{}}
```

未调用入口时也使用这个默认配置。它关闭迁移的字段覆盖、代理和 Canvas 扰动；既有 Window/document/navigator 的 IDL 定制仍保留，不代表整个 APK 回到官方未修改版。

## 生命周期和一致性

配置按宿主进程管理，当前不能给同一进程的多个 WebView Profile 分别设置。不同宿主进程必须分别配置。

入口会先完成整份校验，再原子替换快照；失败不改变已接受的配置。启动前再次成功调用是整份替换，不是字段合并。省略字段使用原生行为，删除旧字段时不要依赖上次调用的内容。

浏览器进入启动阶段时冻结配置；读取网络策略也会冻结。之后的修改明确失败，需完整重启宿主进程再设置。提前读取默认 UA 不冻结配置；但已经缓存 UA 的宿主代码需要在配置后重新读取。

renderer 启动参数携带已验证 JSON 的 Base64 编码，启动时先安装快照，再创建页面；同一 renderer 的 Worker 共享不可变快照。新 renderer / renderer 重建复用相同配置。单进程模式直接共享浏览器快照。Base64 只用于传输编码，请勿把密码或令牌放进指纹配置。

网页没有这个入口，也没有通过 `addJavascriptInterface` 暴露任何配置能力。配置只在本次宿主进程中生效，不自动写文件保存。

## 验证

`webview_custom:fingerprint_config_test` 编译实际配置生产实现，使用 Chromium JSON、URL 与锁，覆盖默认值、类型和范围、非法字段、brands、代理格式、失败不改配置、整份替换、并发快照读取、冻结和新进程导入。

```sh
gn gen out/Fingerprint-host --root-target=//webview_custom:fingerprint_config_test \
  --args='is_debug=false is_component_build=false symbol_level=0 use_remoteexec=false target_os="linux" target_cpu="x64"'
autoninja -C out/Fingerprint-host -j 16 fingerprint_config_test
out/Fingerprint-host/fingerprint_config_test
```

既有 `test_properties.py`、`test_review_regressions.py`、`test_network_identity.py` 验证生产 getter / 方法体，配置存储边界使用内存适配器；不再把它们当作 Bionic 属性服务测试。APK 构建验证 Java/JNI 注册、原生类型和链接。真实宿主调用、renderer/Worker 页面结果及设备网络仍需真机端到端测试。

`smoke.html` 默认按 fillRect 噪声关闭检查；在统一配置显式启用该项时，加载 `smoke.html?noise=on` 检查噪声模式。
