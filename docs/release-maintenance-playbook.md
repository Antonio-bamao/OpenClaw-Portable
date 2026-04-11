# OpenClaw Portable Release Maintenance Playbook

本手册面向发布维护者，覆盖 GitHub Release 资产上传、更新签名私钥备份/恢复，以及 Ed25519 `keyId` 轮换。

## 当前发布链路

发布资产生成后，用户侧更新链路为：

1. 启动器读取 `https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json`
2. `update.json` 指向当前 tag 下的 `OpenClaw-Portable-<version>.zip`
3. 启动器下载并解压 zip
4. 本地导入链路校验 `version.json`
5. 先验 `update-signature.json`
6. 再验 `update-manifest.json`
7. 备份旧版本，替换新版本，失败时回滚

每个 GitHub Release 至少上传两个资产：

- `OpenClaw-Portable-<version>.zip`
- `update.json`

## 发版前检查

1. 确认 `version.json` 的 `version` 就是准备发布的 tag 名，例如 `v2026.04.2`。
2. 确认本地有发布签名私钥：

```powershell
Test-Path .local\update-signing-private-key.txt
```

3. 如果私钥不存在，先从备份恢复。不要重新生成同一个 `keyId` 的私钥。
4. 确认工作区没有把 `.local/` 加入待提交范围；`.local/` 只允许留在本机。

## 生成发布资产

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release-assets.ps1 -Note "本次更新说明"
```

脚本会依次完成：

- 运行 `scripts/build-launcher.ps1`
- 为 `dist\OpenClaw-Portable\update-manifest.json` 生成 `update-signature.json`
- 生成 `dist\release\OpenClaw-Portable-<version>.zip`
- 生成 `dist\release\update.json`

默认私钥路径是：

```text
.local/update-signing-private-key.txt
```

如果要显式指定私钥路径：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release-assets.ps1 -SigningPrivateKeyPath .local\update-signing-private-key.txt -Note "本次更新说明"
```

## 上传 GitHub Release

1. 打开仓库 `Antonio-bamao/OpenClaw-Portable` 的 Releases 页面。
2. 创建新 Release，tag 名必须与 `version.json.version` 一致。
3. Release 标题建议也使用同一个版本号。
4. 上传以下两个文件：
   - `dist\release\OpenClaw-Portable-<version>.zip`
   - `dist\release\update.json`
5. 发布后打开 latest 入口确认 `update.json` 可下载：

```text
https://github.com/Antonio-bamao/OpenClaw-Portable/releases/latest/download/update.json
```

6. 检查 `update.json` 的 `packageUrl` 是否指向同一个 tag 下的 zip 资产。

可选的 `gh` CLI 流程：

```powershell
gh release create v2026.04.2 dist\release\OpenClaw-Portable-v2026.04.2.zip dist\release\update.json --title v2026.04.2 --notes "本次更新说明"
```

## 签名私钥备份

私钥文件是发布者身份根密钥：

```text
.local/update-signing-private-key.txt
```

备份规则：

- 不提交到 Git。
- 不发到聊天工具。
- 不截图、不贴到 issue 或 PR。
- 至少保存在一个加密位置，例如密码管理器安全附件、离线加密 U 盘或受控的机密仓库。
- 备份记录中同时写清：
  - `keyId`，当前为 `portable-ed25519-v1`
  - 对应 public key，当前在 `launcher/services/update_signature.py`
  - 备份日期
  - 适用仓库 `Antonio-bamao/OpenClaw-Portable`

首次生成 keypair 时使用：

```powershell
python .\scripts\generate-update-signing-keypair.py --private-key-path .local\update-signing-private-key.txt
```

生成后把脚本输出的 `publicKey` 写入 `launcher/services/update_signature.py`，并立即备份私钥。

## 在新机器上恢复私钥

1. 从加密备份中取回私钥文本。
2. 在仓库根目录创建 `.local/`。
3. 将私钥保存为：

```text
.local/update-signing-private-key.txt
```

4. 私钥文件内容应是一行 base64 文本，末尾可以有换行。
5. 执行签名相关回归：

```powershell
python -m unittest tests.test_update_signature tests.test_release_assets -v
```

6. 再执行一次发布资产构建，确认脚本能读到私钥并产出 zip 与 `update.json`。

## keyId 轮换流程

只有在私钥疑似泄露、发布机器迁移后需要切换信任根、或计划性密钥更新时才轮换。不要为了普通发版频繁轮换。

### 1. 生成新 keypair

```powershell
python .\scripts\generate-update-signing-keypair.py --private-key-path .local\update-signing-private-key-v2.txt
```

记录输出的 `publicKey`，新 `keyId` 建议使用：

```text
portable-ed25519-v2
```

### 2. 更新运行时信任公钥

编辑 `launcher/services/update_signature.py`：

- 将新公钥加入 `DEFAULT_UPDATE_SIGNING_PUBLIC_KEYS`
- 将 `DEFAULT_UPDATE_SIGNING_KEY_ID` 切换到新 `keyId`
- 将 `DEFAULT_UPDATE_SIGNING_PUBLIC_KEY` 切换到新 public key
- 暂时保留旧 `portable-ed25519-v1` 公钥，确保过渡期内旧签名包仍可验证

过渡期推荐至少覆盖一个公开发版周期。

### 3. 用新私钥签下一版

当前 `scripts/build-release-assets.ps1` 会使用默认 `keyId`。如果已经把 `DEFAULT_UPDATE_SIGNING_KEY_ID` 切到新 key，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-release-assets.ps1 -SigningPrivateKeyPath .local\update-signing-private-key-v2.txt -Note "轮换更新签名 key"
```

如果只想手工验证新 key 的签名链路，可以分三步执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-launcher.ps1
python .\scripts\sign-update-manifest.py --package-root dist\OpenClaw-Portable --private-key-path .local\update-signing-private-key-v2.txt --key-id portable-ed25519-v2
python .\scripts\build-release-assets.py --package-root dist\OpenClaw-Portable --output-dir dist\release --repository Antonio-bamao/OpenClaw-Portable --note "轮换更新签名 key"
```

### 4. 回归验证

```powershell
python -m unittest tests.test_update_signature tests.test_local_update -v
python -m unittest tests.test_update_signature tests.test_release_assets tests.test_update_feed tests.test_online_update tests.test_local_update tests.test_update_manifest tests.test_launcher_controller -v
```

### 5. 移除旧公钥

只有在确认所有仍可能收到在线更新的旧版本都已经升级到信任新 key 的版本后，才能移除旧公钥。否则用户会遇到旧启动器无法验证新包，或新启动器无法识别过渡包的问题。

## 故障处理

私钥丢失：

- 如果旧私钥没有备份，不能继续使用同一个 `keyId`。
- 生成新 keypair，发一个内置新公钥的启动器版本。
- 对外说明旧版本无法通过在线更新跨过这次 key 丢失，需要用户手动下载安装一次新版本。

GitHub Release 上传错包：

- 先删除错误资产或撤回 Release。
- 重新生成 zip 和 `update.json`，不要手改 zip 内部文件。
- 重新上传后，再检查 latest `update.json` 与 `packageUrl`。

签名校验失败：

- 确认 zip 内同时存在 `update-manifest.json` 与 `update-signature.json`。
- 确认签名是在最终打 zip 之前生成的。
- 确认 `update-signature.json.keyId` 在启动器内置信任集合里。
- 确认构建后没有手动改过包内文件或 manifest。
