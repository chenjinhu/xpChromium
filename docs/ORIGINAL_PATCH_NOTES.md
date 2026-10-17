# Chromium WebView 自定义补丁

- 上游基线：`51b3c21991199bc9531e7d296056dd9351554c0c`，版本 `158.0.8109.0`。
- 本地基线标签：`webview-base-158.0.8109.0`；开发分支：`webview-custom`。
- 输入文件：`Chromium修改.zip`，SHA-256 `13cb9871d4b8e1a62b858870721bd88c130657c2969b4c7c6c10601faeefa510`。
- 输入源码与官方 Chromium `122.0.6261.128` 基本匹配。仅移植自定义差异，保留 158 的接口和上游修复。

## WebView 修改

1. `Window.window`、`Window.document` 从 `LegacyUnforgeable` 改为 `Replaceable`，保留跨域限制与缓存属性。移除 `window` 的只读统计注解，避免新增 setter 引用不存在的统计枚举。
2. 为 `Window.navigator` 补上 `Replaceable`，修复原包直接赋值 Proxy 的示例与只读 IDL 不一致的问题。
3. `fillRect` 为 x、y、width、height 分别生成独立的 `[-1, 1]` 整数偏移。原包缺少随机函数头文件，经用户授权使用 Chromium `base::RandGenerator(81)` 一次均匀采样，拆成四个三进制位 补齐。
4. 保留原始无效参数处理；零宽高不加噪，负尺寸先按上游逻辑归一化，扰动后的宽高下限为 0。
5. `CanvasFillRectNoise` 默认开启，可用 `--disable-blink-features=CanvasFillRectNoise` 恢复上游 Canvas 绘制。此修改影响 HTML Canvas 和 OffscreenCanvas 的共用绘制入口；每次绘制可能得到不同图像。

输入包的 `navigator` 修改只有注释，审查后补齐赋值支持；`screen` 已有 `Replaceable`，无需修改。输入包没有 WebGL 随机化或无限 debugger 处理源码，这两项未实现。

## 桌面 Chrome 修改

另一个提交保留输入包的六个图标资源、缺少 Google API key 的提示文案、关闭该提示栏，以及 `--start-url` 参数日志。原实现只输出日志，不会打开 URL。这些 Chrome 修改不参与 `system_webview_64_apk` 目标。

纯注释、未使用 include、旧版 V8 接口差异和下载提示文案漂移不移植。

## 验证

`python3 webview_custom/test_noise.py` 使用可控随机源，穷举检查生产头文件的全部 81 种输出、各轴分布和每次调用的采样次数。此测试不需要 Android 设备。

`smoke.html` 可在使用此 WebView 的 Android 测试应用中加载，检查对象替换、跨域限制、Canvas 扰动范围、零尺寸和非法参数。正常模式应显示全部 PASS。关闭噪声开关后加载 `smoke.html?noise=off` 检查上游绘制恢复。没有连接 Android 设备时，不将编译或 APK 签名检查视为运行测试通过。

增量编译时使用：

```sh
CHROMIUM_WEBVIEW_BUILD_ONLY=1 /home/qiled/chromium-android-latest/run-webview-build.sh
```

不要在自定义分支直接运行默认同步流程；它会更新上游源码。使用 `git ours-log` 查看自定义提交，`git ours-diff` 查看相对基线的修改。

## Chromium 130 整包功能迁移

系统属性配置与逐项迁移说明见 [PROPERTY_PATCHES.md](PROPERTY_PATCHES.md)。

代码质量修复后的配置实现位于 `third_party/blink/common/webview/property_overrides.cc`，浏览器侧统一处理 UA 元数据。回归命令和行为细节见 PROPERTY_PATCHES.md。
