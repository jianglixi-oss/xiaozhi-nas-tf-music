# 参与开发

欢迎提交问题与 Pull Request。当前支持范围为 Waveshare ESP32-S3-AUDIO-Board，其他板型请先讨论。

1. 创建功能分支，保持变更集中。
2. NAS 修改运行 `python -m unittest discover -s nas-music -p 'test_*.py' -v`。
3. 固件修改按 AGENTS.md 与 MUSIC_SETUP.md 编译对应变体，报告实际硬件、屏幕与测试结果。
4. 不提交 `.env`、token、签名密钥、用户部署记录、构建缓存或音乐文件。
5. 提交 PR 时说明问题、行为变化、测试方式及尚未验证的范围。

新版本使用独立项目版本号（如 v0.1.0）；固件内部基础版本仍为 2.5.2。固件附件需注明板型、屏幕、刷写地址和 SHA-256。
