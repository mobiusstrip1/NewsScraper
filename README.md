# AI/具身智能资讯自动抓取项目

## 1. 安装与初始化

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

复制环境变量模板并填写：

```bash
copy .env.example .env
```

你可以按 key 自动路由不同模型：
- `LLM_PROVIDER=auto`：优先走 OpenAI-compatible（如 Qwen），否则走 Anthropic。
- `LLM_PROVIDER=openai_compatible`：强制走 Qwen/OpenAI 兼容接口。
- `LLM_PROVIDER=anthropic`：强制走 Claude。

## 2. 阶段一：运行全链路

```bash
python src/main.py
```

流程：`fetch -> dedupe -> classify -> digest -> notify`

输出：
- SQLite: `data/news.db`
- 日摘要: `digest/YYYY-MM-DD.md`
- 日志: `logs/run.log`

## 3. Windows 定时任务（每日 08:00）

```bash
schtasks /Create /SC DAILY /TN "AINewsDigest" /TR "cmd /c cd /d E:\SA文档\best_practice\NewsScraper && .venv\Scripts\python src\main.py >> logs\run.log 2>&1" /ST 08:00
```

查看任务：

```bash
schtasks /Query /TN "AINewsDigest" /V /FO LIST
```

## 4. 阶段二：API（FastAPI）

```bash
uvicorn src.api:app --reload
```

接口：
- `GET /digest/today`
- `GET /digest/{date}`
- `GET /digest?category=商业&days=7`

## 5. 阶段三：Web（Streamlit）

```bash
streamlit run web/app.py
```

## 6. iOS 最小查看端

`ios/AI News Digest/` 提供 SwiftUI 最小骨架：
- 今日页（商业/科技切换）
- 详情页（摘要 + 原文链接）
- 历史页（占位，可按日期扩展）

## 7. Bark 推送（手机直接看正文）

1. iPhone 安装 Bark，复制 App 首页显示的 Key。
2. 在 `.env` 填写 `BARK_KEY=你的Key`。
3. 先测连通：
   ```bash
   python src/notify.py
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
   - `copy .env.example .env`
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

