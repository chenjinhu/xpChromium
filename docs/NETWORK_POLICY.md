# WebView 网络策略

本阶段为现有系统属性配置增加真正作用于 Chromium 网络栈的代理模式，并统一自定义 UA 的 WebView 入口。默认不设置代理，继续使用原生系统 / AndroidX 网络配置。

## 启用与关闭

在具有系统属性写权限的设备 shell 中，先设置配置，再启动宿主 App：

```sh
# 三种格式任选其一；地址仅为文档示例，必须换成设备可达的代理。
setprop chromium.network.proxy 'http://192.0.2.1:7890'
# setprop chromium.network.proxy 'https://proxy.example:443'
# setprop chromium.network.proxy 'socks5://proxy.example:1080'
setprop chromium.enable 1
```

关闭本次新增的代理模式，保留其他自定义功能：

```sh
setprop chromium.network.proxy -
```

该属性不存在、为空字符串或为 `-` 时不启用代理；`chromium.enable` 不是 `1` 时同样不启用。注意它与 `x_requested_with` 的空字符串语义不同。

代理策略在宿主浏览器进程首次使用时保存快照；包括总开关在内的任何网络配置变更，都必须完整退出并重新启动宿主 App。仅刷新页面或重启 renderer 不足以更换策略。重新创建 NetworkContext / 网络服务时继续使用同一快照，避免部分连接使用新配置、部分使用旧配置。

## 代理模式的行为

- 使用 Chromium 原生 HTTP、HTTPS 或 SOCKS5 代理实现。只接受一个代理端点，不接受 PAC、按协议分流、代理列表、`direct://` 或 URI 中的用户名密码。
- 代理配置应用到 WebView 的 NetworkContext，包括经过该上下文的 HTTP / HTTPS、WebSocket 和预取等请求。真实连接由网络栈执行，不通过修改页面返回的 IP 文本模拟。
- 只有一个代理选项，没有 DIRECT 后备；连接失败不会自动回退直连。
- 去掉 Chromium 对 localhost、回环和链路本地 URL 的隐式代理绕过。此模式不提供域名直连白名单；访问这些 HTTP URL 也会交给所选代理。
- 非空但无效的配置保留为空的 PROXY_LIST，使请求失败；不会把解析错误转换成原生直连。日志会报告错误，不输出配置原文。修正属性后重启 App。
- 配置优先于系统代理、命令行代理及 AndroidX ProxyController。该模式下调用 SetProxyOverride 会返回冲突说明；ClearProxyOverride 不能清除这个启动配置。先将属性设为 `-` 并重启，才能恢复 AndroidX 控制。
- WebRTC 使用原生 `disable_non_proxied_udp` 策略，禁止非代理 UDP 和多网络接口收集；同时移除可能放宽该限制的按 URL 例外。TCP / TURN 连接是否可用取决于代理和服务端，通话可能失败。
- WebTransport 在代理模式下明确拒绝，避免将不支持所选代理的传输当成普通 HTTPS。默认原生模式保留上游行为。
- 停用旧的 `webrtc.public_ip`、`webrtc.private_ip` 和 `webrtc.sdp_redact` 文本改写。ICE / SDP 报告真实路由策略的结果。恢复原生网络模式后，旧配置仍按原有规则生效。

## UA 和请求头

`chromium.navigator.useragent` / `useragent2` / `useragent3` 的同一配置现在也接入 WebView 默认 UA 构造和 WebContents UA 设置，而不只在 URLLoader 最后修改 HTTP 头。它覆盖 App 显式设置的 UA，延续此前自定义属性优先的规则；配置非法时仍回退原生处理。

UA-CH 继续使用已有浏览器侧元数据入口及权限规则。任意 UA 字符串不会自动转换成一套新设备资料；修改 UA 时仍需配套设置 `navigator.userAgentMeta.*`。本阶段没有推测或生成虚构的 GPU、系统版本等信息。

X-Requested-With 仍保留三种语义：未设置 / `-` 使用原生策略，合法非空值替换，显式空值删除；重定向与预取复用现有处理。这个头不会改变网络出口。

## 作用范围和验证边界

当前网络配置是宿主进程级，所有 WebView Profile 共用，不是每个 Profile 独立的代理 API。它不代理宿主自己的 OkHttp、下载器、其他 App 或整个 Android 系统。没有改变 TLS 实现或系统 DNS 设置。

HTTP / SOCKS5 的请求目标解析遵循 Chromium 对相应协议的实现；代理主机域名本身、WebRTC 解析、预解析及设备网络策略仍需抓包检查。本功能不承诺设备级 DNS 隔离，不能代替系统 VPN。

主机回归命令：

```sh
python3 webview_custom/test_network_identity.py
python3 webview_custom/test_properties.py
python3 webview_custom/test_review_regressions.py
python3 webview_custom/test_noise.py
```

新的主机回归编译实际默认 UA 方法、代理策略构造 / WebRTC 偏好方法和配置实现；只在 Bionic、net 解析器和类型边界使用适配器。它验证策略组装，不验证真实代理协议。

`AwNetworkPropertyPolicyTest.*` 使用实际 net 解析、路由、回退和 Mojo 序列化。已加入 `android_webview_unittests`，需设备或模拟器执行；仅编译这些测试不代表设备测试通过。

真机验收至少覆盖：默认无配置、有效代理、代理不可达、非法配置、网络切换及网络服务重建。用受控服务端检查 UA / UA-CH / X-Requested-With、重定向和 WebSocket，抓包检查 WebRTC 非代理 UDP、WebTransport 和 DNS。当前未完成这些真机检查。
