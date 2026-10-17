# xpChromium

用于 Android 10+、arm64 的 Chromium WebView 定制补丁仓库。这里只记录自己的修改；Chromium 官方源码及其依赖由官方仓库管理。

| 项目 | 当前值 |
| --- | --- |
| Chromium 版本 | `158.0.8109.0` |
| 官方基线 | `51b3c21991199bc9531e7d296056dd9351554c0c` |
| 自定义源码提交 | `bf95d218bcae6441438511bea18b89c4aa2ad4a2` |
| 自定义提交数 | 11 |
| 构建目标 | `system_webview_64_apk` |
| APK 包名 | `com.android.webview` |

`chromium.json` 记录基线、自定义提交、最终源码树及各补丁 SHA-256；`patches/series` 记录应用顺序。每个补丁保留原始提交作者、说明和二进制资源差异。`source_head` 是服务器原始开发分支上的提交；重新执行 `git am` 后提交哈希可能不同，通过源码树摘要验证内容一致。

## 功能和配置

- [系统属性配置、26 个旧补丁的迁移及质量修复](docs/PROPERTY_PATCHES.md)
- [真实代理、WebRTC 路由和网络身份配置](docs/NETWORK_POLICY.md)
- [统一指纹配置 API、字段类型和生命周期](docs/UNIFIED_CONFIG.md)
- [Window、Canvas fillRect 和桌面定制说明](docs/ORIGINAL_PATCH_NOTES.md)
- [构建、回归和签名验证记录](docs/VERIFICATION.md)
- [WebView 编译参数](config/webview-arm64.gn)

本版本使用宿主 App 的 JSON 统一入口，已经取消 `chromium.*` 系统属性读取。将 [Fingerprint.java](sdk/Fingerprint.java) 集成到宿主 App，在 WebView 启动前调用 `Fingerprint.configure(json)`；完整接入说明见 [UNIFIED_CONFIG.md](docs/UNIFIED_CONFIG.md)，最小示例见 [examples/fingerprint.json](examples/fingerprint.json)。默认关闭迁移的字段覆盖、代理和 Canvas 扰动。统一配置被冻结后需重启宿主进程才能改变；当前仍是进程级作用范围。

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
