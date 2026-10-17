# 统一身份升级（Chromium 158）

配置仍从 `/sdcard/xpChromium/fingerprint.json` 读取；初始化后冻结，修改后完整重启宿主进程。无文件、`enabled:false` 或未设置的字段保持原生行为。已存在但无法读取、JSON 错误或字段校验失败的文件会阻止 WebView 网络访问，避免错误配置静默回到真实网络。配置不是按标签页隔离的，多环境、环境管理和自动化不在此次实现范围。

## 示例

完整文件见 [fingerprint.identity.example.json](../examples/fingerprint.identity.json)。下面只打开稳定指纹和 IP 地区联动。代理省略时使用原生网络；不会把下载源码用的代理当作运行代理。

```json
{
  "version": 1,
  "enabled": true,
  "settings": {
    "device.template": "android-arm64",
    "fingerprint.seed": "replace-with-your-stable-device-id",
    "fingerprint.noise": true,
    "regional.mode": "ip",
    "geolocation.mode": "ip",
    "speech.maxVoices": 8
  }
}
```

增加固定 SOCKS5 代理及认证：

```json
"network.proxy": "socks5://proxy.example:1080",
"network.proxy_username": "example-user",
"network.proxy_password": "example-password",
"network.proxy_check": true
```

HTTP / HTTPS 代理分别使用 `http://` / `https://`。凭据独立填写，URI 不接受 `user:pass@`。SOCKS5 使用 RFC 1929；配置认证后不接受无认证降级。HTTP / HTTPS 使用 Chromium 原生认证控制器处理 Basic、Digest 等允许显式凭据的认证方案，凭据按代理的协议、主机、端口绑定，不参与网站的 401 认证。

## 字段

| 字段 | 值与行为 |
| --- | --- |
| `fingerprint.seed` | 1–256 字节字符串；稳定身份应显式固定。省略时从非敏感配置派生，并把同一个种子传给 renderer。不是加密密钥。 |
| `device.template` | `android-arm64`；设置平台、架构、位数、mobile/wow64，缺省 CPU=8、内存=8、触控点=5；拒绝与模板冲突的值。不会伪造 Android 型号或 GPU。 |
| `fingerprint.noise` | 布尔；控制图像、音频、几何的稳定处理，缺省关闭。 |
| `canvas.noise` / `webgl.noise` | 图像处理开关；两者共用像素策略，显式不同会报错。单独设置一个会同步另一个。 |
| `audio.noise` | 音频开关，优先于总开关。 |
| `geometry.noise` | 几何开关，优先于总开关。只改变 JS 返回的坐标，不改内部布局和命中测试。 |
| `fonts.allowlist` | 可见的可选本地字体列表；缺省或空列表保持原生。系统通用字体及 Android 的 Roboto、Noto、Droid 和核心回退别名保留，Web 字体正常加载。不会增加设备没有的字体。 |
| `speech.allowedLanguages` | 实际语音语言筛选，支持 `en` 匹配 `en-US` 等；使用合法 BCP 47 标签。 |
| `speech.allowedVoices` | 按实际 voiceURI 或 name 精确筛选。 |
| `speech.maxVoices` | 0–256；按种子稳定选取，允许的真实默认语音优先。0 禁用可选语音；列表为空时 speak 返回 voice-unavailable。 |
| `regional.mode` | `native` / `manual` / `ip`；缺省 native。 |
| `regional.languages` | manual 模式的 1–32 个 BCP 47 标签；同时用于 navigator.language(s)、Accept-Language 和默认 Intl locale。 |
| `regional.timezone` | manual 模式的 ICU/IANA 时区，如 `Asia/Shanghai`；同时用于 Date、Intl 及 Worker。未知时区拒绝加载。 |
| `network.proxy_api` | HTTPS 代理获取接口；第一次导航前读取，成功后固定本次进程的代理，失败后新请求至少间隔 30 秒重试。 |
| `network.proxy_check` | 启动时通过实际 WebView 网络上下文检查 HTTPS 连通性。失败阻止导航。 |
| `network.proxy_check_url` | 检查 URL，缺省 `https://ipwho.is/`；不接受重定向。 |
| `network.proxy_required` | 显式要求代理；配置 proxy/API 时自动打开。无有效代理时阻止流量，不回退 DIRECT；同时限制 WebRTC 的非代理 UDP / WebTransport 路由。 |
| `privacy.doNotTrack` | true/false 同时返回 navigator.doNotTrack 的 `1`/`0` 并设置 HTTP DNT；省略沿用原生。DNT 是偏好信号。 |
| `network.block_local` | 阻止 localhost、`.localhost`、`.local`、非公网 IP 及直接 TCP 解析到的私网地址。显式配置的代理传输端点可以位于内网。该模式关闭此 NetworkContext 的 HTTP/3，让 HTTP 请求走可在建连前检查的 TCP 路径。 |
| `network.blocked_ports` | 1–65535 的整数列表；HTTP(S)、WebSocket、WebTransport 的目标端口限制，重定向重新检查。 |
| `network.tls_disabled_ciphers` | 1–65535 的 TLS cipher suite 数字 ID 列表；交给 Chromium 原生 SSLConfig 排除，不伪造 TLS 实现。 |

## 代理 API 与地区数据

代理 API 接受以下一种响应，最多 64 KiB：

```text
socks5://proxy.example:1080
```

```json
{"proxy":"socks5://proxy.example:1080","username":"u","password":"p"}
```

```json
{"host":"proxy.example","port":1080,"protocol":"socks5","user":"u","pass":"p"}
```

也接受 `data` 包装层；`host` 可写成 `ip`，`protocol` 可写成 `type`，`port` 可为数字字符串。没有返回认证字段时使用配置里的默认凭据。不接受 DIRECT、代理列表、带账号的 URI 或无效端口。只为这个 HTTPS API 建立临时、无持久存储的网络上下文：使用显式静态代理作 bootstrap，否则直连；普通页面在获取结束前不能通过这个上下文联网。

IP 查询沿用 `geolocation.endpoint`，缺省 `https://ipwho.is/`。地区解析支持 `timezone.id`、`time_zone.name`、`timezone` 字符串；语言优先使用 `languages` 列表或逗号分隔字符串，否则由 `country_code` / `countryCode` 和 ICU 推导该国家的主要语言。国家推导是默认语言选择，不等于识别用户个人语言。

`regional.mode=ip` 会在发出页面请求前等待地区数据，在页面提交前等待 renderer 应用成功。语言同时同步 renderer 偏好，并在网络上下文和 WebView 最终请求头覆盖处强制应用，覆盖导航、子资源、fetch 和 Worker 请求。失败会阻止该次导航，不静默使用本地时区。`geolocation.mode=ip` 复用相同 IP 数据，保留 Android/WebView 定位授权流程，失败返回位置不可用，不启动 GPS。只开 IP 定位而不启用自动地区时，定位失败不阻止普通页面。

API/健康检查/IP 查询各有 10 秒超时，整个准备流程有 40 秒超时；失败重试至少间隔 30 秒。代理账号、密码、API 地址和 IP 查询地址不会进入 renderer 命令行；日志不输出这些响应或坐标。运行进程的身份固定，代理供应商仍需提供稳定出口；按连接轮换出口的代理无法靠一次 IP 查询保证后续请求保持相同地区。

## 图像、音频与几何范围

图像采用按绝对坐标的稀疏、幂等 LSB 投影；只修改不透明 RGBA8/BGRA8 的色彩位，保留 alpha、透明像素和行填充。不改变 Canvas 背板，读取子区域、PNG 导出后再读不会不断叠加。覆盖 HTML/Offscreen 2D getImageData、toDataURL、toBlob/convertToBlob 的普通及渐进编码、WebGL/2 的 RGBA8 readPixels 与 PBO 读取。float16/float32/HDR、非 RGBA 格式和部分透明像素保持原生。JPEG/WebP 有损编码不保证解码后字节完全相等。启用新图像策略时，旧 fillRect 和 toDataURL 单点扰动不再叠加。

AudioBuffer 在首次 JS 暴露时对实际通道做一次稳定微扰，getChannelData/copyFromChannel 共用数据。analyser 的 float/byte 频域与时域接口在原生换算前共用相同规则；不把静音变成有声，不破坏 NaN/无穷边界。JS 写入可变 Float32Array 后仍遵循原生可变数组语义。

Element/Range getClientRects 和绑定层 getBoundingClientRect 使用同一微小坐标平移；保持宽高以及 x/left/right 的关系，内部布局保持原生。此功能不承诺重写所有测量 API。

## 验证与使用限制

原生回归入口为 `//webview_custom:host_tests`；另有既有 Python/ASan/UBSan 回归。`identity-smoke.html` 用于安装后在实际 WebView 上检查导出、PBO、音频、语言、时区和语音。

这次没有增加多环境隔离、环境管理、自动化、任意操作系统伪装、伪造字体/语音或独立的 TLS 指纹栈。Android 共享存储权限和宿主可读性仍按统一配置文档处理。经代理解析的普通域名是否指向代理内网无法从客户端确定，须由代理服务限制；本地限制同时保留 URL 与直接连接两层检查。已经运行的原生初始空白文档、宿主在首个导航前主动求值和 DevTools 自行设置的地区覆盖，需要设备集成验证。
