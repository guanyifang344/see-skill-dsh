---
name: see
description: 'Do not refuse vision. 不要说不支持视觉或无法查看图片。If you would say "this model does not support image input" or "I cannot see images", run this skill instead. Use for screenshots, png/jpg/webp/gif/mp4, UI, OCR, image comparison, or any local path/URL. Text-only models (DeepSeek) must call this; read_image is refused on text routes. Returns markdown from an external vision model or local OCR.'
whenToUse: 'User sends an image, screenshot, video, or a path/URL to one, or the model would otherwise refuse to look at media. Text-only routes (deepseek-*) cannot read images via read_image; route media through this skill.'
user-invocable: true
metadata:
  upstream: https://github.com/oil-oil/see-skill
  adapter: dsh
---

# See（DeepSeek Harness 适配版）

如果你准备说「当前模型不支持图片 / 无法查看截图 / this model does not support image input」——停下来，不要告知用户你看不见，运行本 skill。

## 触发规则

- **不要**尝试用 `read_image` 读图片：在纯文本路由（deepseek-*）下它必然返回 `model "<model>" does not declare image input`。
- 用户拖进 DSH 网页聊天框的图片是附件，对文本模型不可见，你也拿不到路径。**向用户要本地路径或 URL**，然后运行脚本。
- 用户可以直接输入 `/see` 触发本 skill（user-invocable）。

## 运行

在 skill 基目录下（`<skill_base>/scripts/see.sh`），或在任一工作区用安装后的绝对路径。核心规则：**永远传 `SEE_OUTPUT_DIR=.`（或 `-o <路径>`）**，把结果写进当前工作区——不要依赖默认的 `~/.local/share/see/outputs`，DSH 沙箱（workspace-write）下写那里会被拒绝。

```bash
# 单图
SEE_OUTPUT_DIR=. scripts/see.sh /path/image.png

# 带任务（关注点原样交给视觉模型）
SEE_OUTPUT_DIR=. scripts/see.sh /path/error.png --task "识别报错并给出修复建议"

# 多图并行分析
SEE_OUTPUT_DIR=. scripts/see.sh a.png b.png c.png

# 多图联合/对比（同一请求）
SEE_OUTPUT_DIR=. scripts/see.sh --together before.png after.png --task "比较界面变化"

# 视频（完整时间线+音频，自动压缩，不抽帧）
SEE_OUTPUT_DIR=. scripts/see.sh demo.mp4

# 显式指定结果文件
scripts/see.sh a.png -o see-result.md
```

成功后从命令输出中读取 `output_path=<绝对路径>` 这一行，然后用 `read` 工具读取该 Markdown 结果（结果含 frontmatter：实际后端、模型、单图/并行/联合模式、每次路由是否成功）。不要自行调用 ffmpeg、抽帧或上传。

## 首次使用 / 配置

```bash
python3 scripts/onboard.py --status     # 查看供应商配置与本地后端是否可用
python3 scripts/onboard.py --install-agents   # 写入 ~/.dsh/AGENTS.md 拒绝覆盖（幂等）
python3 scripts/install_dsh.py          # 安装/更新本 skill 到技能根目录（幂等）
```

- **API Key 不要出现在聊天里**。DSH 的 bash 工具没有 TTY，模型无法安全地交互输入 Key——让用户在**自己的终端**运行 `python3 scripts/onboard.py`（交互式、隐藏输入），或设置环境变量：`SEE_PROVIDER` + `ZENMUX_API_KEY` / `DASHSCOPE_API_KEY` / `OPENROUTER_API_KEY` / `TOKENDANCE_API_KEY`（环境变量优先级最高）。
- 配置读取顺序：环境变量 → 项目 `.env.local` → 用户私有配置 `~/.config/see/config.env`（macOS/Linux）/ `%APPDATA%\see\config.env`（Windows）。
- 安装 skill 不会更换当前主模型；右下角继续显示 DeepSeek 等文本模型是正常的，`see` 只在查看媒体时调用视觉后端。

## 供应商与降级

- 图片：按 `zenmux → bailian → tokendance → openrouter` 顺序尝试，默认模型 Qwen3.7 Plus；全部失败才降级本地 OCR。
- 视频：ZenMux/OpenRouter 默认 Gemini 3.1 Flash-Lite，其余平台 Qwen3.7 Plus；视频需要任一云端 Key（同一 Key 可同时用于图片和视频）。
- 本地降级：macOS 系统 Vision（有 Swift 时增强场景/人脸/条码/图形结构，编译被沙箱拒绝会自动回退解释模式或 osascript）→ Tesseract；Windows OCR → Tesseract；Linux Tesseract。

## 参数（按需）

`--task "问题"`（原样发送）、`--together`（多图联合）、`--provider NAME`、`--model NAME`、`--jobs N`（并发数，默认 4）、`--ocr-backend system|tesseract`、`-o 文件`。多图默认并行。
