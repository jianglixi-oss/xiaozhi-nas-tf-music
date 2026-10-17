# 小智 NAS 音乐 MCP

与专用 Waveshare 音乐固件配套，继续使用 xiaozhi.me 官方服务器。
目前按文件名搜索 MP3，不调用飞牛音乐私有 API，也不修改曲库。

1. 解压后把此目录放到飞牛 NAS 的 Docker 项目目录。
2. 将 `.env.example` 复制为 `.env`。
3. 登录 https://xiaozhi.me，选择设备对应的智能体，进入“配置角色”，找到“MCP 接入点”，复制完整 `wss://...` 地址到 `MCP_ENDPOINT`；不同界面版本入口位置可能不同。不要公开含 token 的地址。
4. `NAS_MUSIC_DIR` 填实际音乐目录，`MUSIC_BASE_URL` 填 NAS 内网地址，例如 `http://192.168.1.10:8765`。
5. 使用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成 `MUSIC_SIGNING_KEY`。
6. 执行 `docker compose up -d --build`。

挂载的音乐目录只读，默认 Compose 构建的容器 UID=10001 需要读取权限。
NAS 与设备需互通，允许设备访问 TCP 8765；不要把该端口直接开放到公网。
`MUSIC_BASE_URL` 使用 NAS 地址，不能使用 Docker 容器内部地址。

角色提示：

```text
播放 NAS 歌曲时先调用 nas_music_search，再用选中结果的 device_arguments
调用设备 self.music.play_url。找不到时说明曲库未找到，不要假装播放。
停止使用 self.music.stop，查询结果使用 self.music.status。
```

歌曲新增后调用 `nas_music_refresh`；目前不支持 FLAC、飞牛音乐歌单及收藏。
设备固件必须提供 `self.music.play_url`，官方原版 v2.5.2 单独配此服务无法播放。

桥接程序 `mcp_pipe.py` 来自 https://github.com/78/mcp-calculator 。

## 飞牛容器界面部署（不构建镜像）

也可使用与真机测试相同的 Python 启动方式：上传本目录源码及 `.env` 到一个应用目录，并创建 `deps` 子目录。

- 镜像：`python:3.12-slim`
- 启动命令：`python /app/bootstrap.py`
- 环境：`PYTHONPATH=/deps`、`PYTHONUNBUFFERED=1`
- 挂载：应用目录 → `/app`（只读）、音乐目录 → `/music`（只读）、`deps` → `/deps`（读写）
- 端口：宿主 `8765` → 容器 `8765/TCP`
- 自动重启，建议内存上限 512 MiB。

首次启动会下载依赖（默认清华 PyPI 镜像，可通过 `PIP_INDEX_URL` 覆盖）；之后复用 `/deps`。
此方式使用镜像默认用户，与 Compose 的 UID=10001 不同。不要挂载 Docker socket 或开启特权模式。

## 测试记录

2026-10-17：已在飞牛 NAS 部署，用户确认 Waveshare 板上 NAS 语音点歌播放通过。
自动测试覆盖曲库搜索、签名、过期与 MCP stdio 握手及 HTTP 下载；未自动测试真实官方云端。
