# AI/具身智能资讯自动抓取项目

## 1. 安装与初始化

### macOS

```bash
chmod +x scripts/*.sh
./scripts/setup_venv.sh
source .venv/bin/activate
cp .env.example .env
```

### Windows

**PowerShell / CMD：**

```bat
scripts\setup_venv.bat
.venv\Scripts\activate.bat
copy .env.example .env
```

**Git Bash（MINGW64）：**

```bash
chmod +x scripts/*.sh
./scripts/setup_venv.sh
source .venv/Scripts/activate
```

注意：不要执行 `bash scripts/setup_venv.bat`（`.bat` 只能给 CMD 用）。

你可以按 key 自动路由不同模型：
- `LLM_PROVIDER=auto`：优先走 OpenAI-compatible（如 Qwen），否则走 Anthropic。
- `LLM_PROVIDER=openai_compatible`：强制走 Qwen/OpenAI 兼容接口。
- `LLM_PROVIDER=anthropic`：强制走 Claude。

## 2. 阶段一：运行全链路

### macOS / Windows（通用）

```bash
python src/main.py
```

或使用跨平台脚本（自动切到项目根目录）：

```bash
# macOS
./scripts/run_daily.sh

# Windows
scripts\run_daily.bat
```

流程：`fetch -> dedupe -> classify -> digest -> notify`

输出：
- SQLite: `data/news.db`
- 日摘要: `digest/YYYY-MM-DD.md`
- 日志: `logs/run.log`

## 3. 定时任务（每日 08:00）

### macOS（launchd）

```bash
chmod +x scripts/install_schedule_mac.sh
./scripts/install_schedule_mac.sh
```

查看状态：

```bash
launchctl print gui/$(id -u)/com.newsscraper.daily
```

卸载：

```bash
launchctl bootout gui/$(id -u)/com.newsscraper.daily
rm ~/Library/LaunchAgents/com.newsscraper.daily.plist
```

说明：Mac 若到点处于睡眠，任务会在唤醒后补跑（与 cron 不同）。

### Windows（任务计划程序）

```bat
scripts\install_schedule_win.bat
```

查看任务：

```bat
schtasks /Query /TN "AINewsDigest" /V /FO LIST
```

删除任务：

```bat
schtasks /Delete /TN "AINewsDigest" /F
```

## 4. 阶段二：API（FastAPI，端口 7800）

```bash
# macOS
./scripts/start_api.sh

# Windows
scripts\start_api.bat
```

接口：
- `GET /digest/today`
- `GET /digest/{date}`
- `GET /digest?category=商业&days=7`

## 5. 阶段三：Web（Streamlit，端口 8502）

```bash
# macOS
./scripts/start_web.sh

# Windows
scripts\start_web.bat
```

## 6. iOS 最小查看端

`ios/AI News Digest/` 提供 SwiftUI 最小骨架：
- 今日页（商业/科技切换）
- 详情页（摘要 + 原文链接）
- 历史页（占位，可按日期扩展）

## 7. Bark 推送（手机直接看正文）

1. iPhone 安装 Bark，打开 App **首页**复制 **Key**（不是 Settings 里的 Device Token）。
2. 在 `.env` 填写 `BARK_KEY=你的Key`。
3. 先测连通（会打印 Bark 真实返回）：
   ```bash
   python src/notify.py --verbose
   ```
4. 跑主流程后会推送**完整摘要正文**（不是仅“已生成X条”）：
   ```bash
   python src/main.py
   ```

推送说明：
- 使用 Bark POST 接口发送正文，并开启 `isArchive=1`，可在 Bark App 历史里回看。
- 正文过长会自动拆成多条（标题会显示 `1/3`、`2/3`）。
- 推送内容与 `digest/YYYY-MM-DD.md` 一致。

## 8. 验收建议

- 连续 3 天观察 `logs/run.log` 是否每日稳定执行。
- 每日确认 Bark 是否收到“今日AI资讯（商业X·科技Y）”及正文内容。
- 抽查 `data/news.db` 中 10 条分类结果质量。

## 9. `.env` 实例填写（Qwen）

```env
LLM_PROVIDER=openai_compatible

ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-5

OPENAI_API_KEY=sk-your-qwen-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus

BARK_KEY=your-bark-key
```

如果你要切换成 Claude，只需改：

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-claude-key
```

## 10. 一次完整演练清单（本地）

1. **准备环境变量**
   - macOS: `cp .env.example .env`
   - Windows: `copy .env.example .env`
   - 填好 `OPENAI_API_KEY`（Qwen）和 `BARK_KEY`
2. **跑一次全链路**
   - `python src/main.py`
   - 预期：`logs/run.log` 出现 `Fetched=... New=... Digest=...`
3. **检查数据和摘要**
   - 查看 `digest/YYYY-MM-DD.md` 是否有“商业/科技”分组
   - 检查 `data/news.db` 已新增文章
4. **验证推送**
   - 手机 Bark 收到完整摘要正文（可点开查看，历史可回看）
5. **启动 API（7800）**
   - `python -m uvicorn src.api:app --host 127.0.0.1 --port 7800`
   - 浏览器打开 `http://127.0.0.1:7800/docs`
6. **启动 Web（可选）**
   - `python -m streamlit run web/app.py --server.port 8502`
   - 浏览器打开 `http://127.0.0.1:8502`
7. **接口抽查**
   - `GET /digest/today`
   - `GET /digest/2026-07-09`
   - `GET /digest?category=科技&days=7`

## 11. Git 忽略说明

`.gitignore` 已忽略：
- `.env`（密钥）
- `.venv/`（虚拟环境）
- `logs/`、`*.log`（运行日志）
- `data/*.db`、`digest/`（本地运行产物）
