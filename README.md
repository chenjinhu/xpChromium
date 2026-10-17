# xpChromium

用于 Android 10+、arm64 的 Chromium WebView 定制补丁仓库。这里只记录自己的修改；Chromium 官方源码及其依赖由官方仓库管理。

| 项目 | 当前值 |
| --- | --- |
| Chromium 版本 | `158.0.8109.0` |
| 官方基线 | `51b3c21991199bc9531e7d296056dd9351554c0c` |
| 已编译的自定义源码提交 | `02b7cf0fc73439a0eaaacd262cba3307ce0d02e2` |
| 自定义提交数 | 9 |
| 构建目标 | `system_webview_64_apk` |
| APK 包名 | `com.android.webview` |

`chromium.json` 记录基线、自定义提交、最终源码树及各补丁 SHA-256；`patches/series` 记录应用顺序。每个补丁保留原始提交作者、说明和二进制资源差异。`source_head` 是服务器原始开发分支上的提交；重新执行 `git am` 后提交哈希可能不同，通过源码树摘要验证内容一致。

## 功能和配置

- [系统属性配置、26 个旧补丁的迁移及质量修复](docs/PROPERTY_PATCHES.md)
- [Window、Canvas fillRect 和桌面定制说明](docs/ORIGINAL_PATCH_NOTES.md)
- [构建、回归和签名验证记录](docs/VERIFICATION.md)
- [WebView 编译参数](config/webview-arm64.gn)

系统属性功能由 `chromium.enable=1` 启用。`chromium.config.x_requested_with` 未配置或为 `-` 时使用原生策略，非空合法值强制替换，显式空值删除请求头。此前的 `CanvasFillRectNoise` 独立于此总开关，默认开启。完整行为以配置说明为准。

## 在现有服务器继续开发

开发源码位于 `/home/qiled/chromium-android-latest/src`，分支为 `webview-custom`；该源码仓库的 `origin` 保留为官方 Chromium 上游。本仓库单独克隆到 `/home/qiled/xpChromium`，其 `origin` 指向 GitHub。

先在源码仓库提交修改，再导出补丁到本仓库：

```sh
cd /home/qiled/chromium-android-latest/src
git ours-log
# 编辑、验证后，仅暂存本次涉及的文件
git add <修改的文件>
git commit -m "Describe the custom change"

cd /home/qiled/xpChromium
python3 tools/patches.py export /home/qiled/chromium-android-latest/src
python3 tools/patches.py check
git diff --stat
git add chromium.json patches
git commit -m "Update custom Chromium patches"
git push origin main
```

`export` 要求源码工作区干净、官方基线仍是祖先、补丁提交为线性历史，并检查版本号。它只导出基线之后的提交，不移动源码分支、不同步上游，也不上传完整 Chromium。

当前服务器的增量编译命令：

```sh
CHROMIUM_WEBVIEW_BUILD_ONLY=1 /home/qiled/chromium-android-latest/run-webview-build.sh
```

此命令读取现有源码，不执行默认下载同步。增加新提交后，构建产物的源码标记应同时更新为实际构建的提交。

## 在其他已初始化的 Chromium 工作区应用

先按 Chromium 官方 Android 构建流程准备源码、depot_tools 和依赖，在独立工作区切换到上述精确基线，并完成对应依赖同步。不要直接在已有未提交修改的工作区切换版本。

```sh
git clone https://github.com/chenjinhu/xpChromium.git
cd xpChromium
python3 tools/patches.py check
python3 tools/patches.py apply /path/to/chromium/src
```

`apply` 要求源码 HEAD 恰好为指定基线且工作区干净，使用 `git am` 保留逐个补丁的作者与说明。若失败，会保留现场供检查，可在源码仓库用 `git am --continue` 或 `git am --abort` 处理；工具不会重置源码。成功后核对最终源码树摘要。

然后在 Linux 源码目录执行（`gn`、`autoninja` 需已在 PATH）：

```sh
mkdir -p out/WebView-arm64
cp /path/to/xpChromium/config/webview-arm64.gn out/WebView-arm64/args.gn
gn gen out/WebView-arm64
autoninja -C out/WebView-arm64 -j 16 system_webview_64_apk
```

产物为 `out/WebView-arm64/apks/SystemWebView64.apk`。此仓库不包含 Android SDK、构建依赖、APK、签名私钥或签名压缩包；使用现有 RK14 签名材料另行签名。

补丁包含 Chromium 代码上下文和部分资源；相关代码和资源应遵循原项目各自的许可证与版权声明。
