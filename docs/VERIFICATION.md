# 构建验证记录

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
