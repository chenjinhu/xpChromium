# Android Chromium 测试版

同一份 Chromium 158 定制源码可构建完整 Android 浏览器，无需替换系统 WebView。目标为 `chrome_public_apk`，包名 `org.chromium.chrome`，适用 Android 10+、arm64。浏览器和 WebView 共用指纹配置解析、代理认证、IP 查询和底层 Blink / net 修改。

构建提交 `90a39867b3e2a4037133cbdc3aa65277002adb51`；APK `Chromium-158.0.8109.0-arm64-identity-rk14.apk`（513537599 字节）。SHA-256：`13131b03d4e3789719a04d01018d02983950c902b23b1a7eb9975d958c5cff58`。签名、架构和验证范围见 [VERIFICATION.md](VERIFICATION.md)。

## 安装和检查

连接已开启 USB 调试的设备，在本仓库执行：

```sh
bash tools/install_chromium.sh /path/to/Chromium-158.0.8109.0-arm64-identity-rk14.apk examples/fingerprint.browser.json
```

脚本安装浏览器、授予读取配置所需的存储权限、写入配置和检查页面，然后启动 Chromium。多设备时先设置 `ANDROID_SERIAL`。如果设备上已有同包名但不同证书的 Chromium，Android 会拒绝覆盖安装；请自行决定如何处理已有浏览器数据。

完成 Chromium 首次运行引导后，在地址栏打开：

```text
file:///sdcard/xpChromium/identity-smoke.html?language=zh-CN&timezone=Asia%2FShanghai&noise=1
```

这个示例使用原生网络、固定中文和上海时区，便于离线检查指纹接口。检查页报告 navigator、Date/Intl、Canvas、WebGL、音频、几何和语音接口，并比较 Dedicated Worker 与页面的身份。HTTP 头、代理出口、Service Worker 和真实定位还需进一步验证。

需要同时检查实际 HTTP 头时，在电脑启动本地服务，并通过 USB 转发：

```sh
python3 tools/serve_identity_test.py
# 另一个终端；adb 不在 PATH 时使用 Android SDK 中 adb 的完整路径
adb reverse tcp:8765 tcp:8765
```

浏览器打开 `http://127.0.0.1:8765/?headers=1&language=zh-CN&timezone=Asia%2FShanghai&noise=1`。页面会额外比较线上 User-Agent、Accept-Language，可添加 `dnt=1`、`requestedWith=期望值`。空 `requestedWith=` 检查该头已删除。此服务只监听电脑回环地址，可用 Ctrl+C 关闭；也适合作为设备限制 file URL 访问时的替代入口。此示例要求原生网络且未启用私网阻止；固定代理或私网阻止模式下应将检查页部署到自己的公网 HTTPS 测试服务。

## 配置与权限

浏览器启动时主动读取 `/sdcard/xpChromium/fingerprint.json`，一次解析后冻结；修改文件必须完全停止并重启 `org.chromium.chrome`。文件不存在时保持原生默认值，无法读取或校验失败时阻止网络，并在 logcat 中记录不含配置内容的错误。

Android 11+ 的固定共享存储路径需要“所有文件访问”权限。测试 APK 声明 `MANAGE_EXTERNAL_STORAGE`；安装脚本通过 adb 授权。也可手动进入系统设置的特殊应用权限，为 Chromium 开启所有文件访问权限，再强制停止并重启。Android 10 使用 `READ_EXTERNAL_STORAGE` 和 legacy storage。权限应在首次启动前授予；如果已启动，授权后重新启动进程。

```sh
adb shell appops set org.chromium.chrome MANAGE_EXTERNAL_STORAGE allow
adb shell am force-stop org.chromium.chrome
```

字段说明沿用 [UNIFIED_CONFIG.md](UNIFIED_CONFIG.md)、[NETWORK_POLICY.md](NETWORK_POLICY.md) 和 [IDENTITY_UPGRADE.md](IDENTITY_UPGRADE.md)。浏览器的页面、子资源、Worker、WebSocket 和浏览器自身 NetworkContext 会接入配置的网络策略。设置固定代理时同时禁用 QUIC、限制 WebRTC 的非代理 UDP，并阻止 WebTransport 绕过代理。`config.x_requested_with` 未配置时保持 Chromium 原生行为，空字符串删除该头，非空字符串替换；覆盖在原生网络层应用，不触发页面 CORS 预检。

按出口 IP 联动地区时，将示例中的 manual 地区字段改成 `"regional.mode":"ip"`，删除 `regional.languages`、`regional.timezone`，并按需增加 `"geolocation.mode":"ip"`。首次页面导航会等待网络准备、查询和 renderer 确认。IP 服务失败会按配置阻止导航或返回定位不可用；网站的定位权限仍由 Chromium 的权限界面控制。

下载源码使用的 `192.168.101.182:7890` 不会被自动设置为设备运行代理。需要代理时在配置中显式写 `network.proxy`，支持 HTTP、HTTPS 和 SOCKS5；用户名、密码单独配置。私钥不属于配置内容。

## 构建

服务器沿用已有 Android arm64 Release 构建缓存：

```sh
cd /home/qiled/chromium-android-latest/src
export PATH=/home/qiled/depot_tools-webview:$PATH
export DEPOT_TOOLS_UPDATE=0
gn gen out/WebView-arm64
autoninja -C out/WebView-arm64 chrome_public_apk -j 12
```

输出为 `out/WebView-arm64/apks/ChromePublic.apk`。目录名是已有构建缓存名，实际目标为完整 Chromium 浏览器。此命令不执行源码同步。

APK 使用本机已有 RK14 材料签名；签名私钥保留在 Mac，服务器只接收签名 APK 与公开验证信息。此测试浏览器可独立安装，系统 WebView 不随安装改变。
