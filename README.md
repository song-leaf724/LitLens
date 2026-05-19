# LitLens 文学作品深度阅读助手

[English](README_EN.md) | 中文

LitLens 是一个面向文学作品深度阅读的 AI 应用。项目基于 FastAPI 构建后端，支持本地前端工作台、文档上传、公共书源导入、PDF/EPUB 解析、体裁感知切分、向量检索、RAG 问答，以及基于 LangGraph 的证据型文学分析 Agent 工作流。系统强调“基于原文回答”，尽量返回可核查的引用片段，避免脱离文本空谈。

## 已实现功能

- FastAPI 服务启动与 `/health` 健康检查
- 静态前端阅读工作台：上传、书源导入、文档管理、RAG 问答、Agent 分析、引用展示
- `.env` 配置读取，不在代码里硬编码 API Key
- OpenAI-compatible LLM 调用，支持 `base_url / api_key / model_name`
- `/chat` 普通文学问答与 `/chat/stream` SSE 流式输出
- `.txt` / `.md` / `.pdf` / `.epub` 文档上传与解析
- 文档删除：同步清理本地文件、SQLite 记录和向量库记录
- Project Gutenberg / Wikisource 公共书源搜索与导入
- 自动体裁识别：英文小说、现代中文、古典诗歌、文言散文、诗歌文本等
- 体裁感知 chunking：现代文本按段落窗口，古诗按整首/句组，文言文按句群
- Embedding 入库与 ChromaDB 向量检索，Chroma 不可用时 fallback 到本地 JSON 向量检索
- `/rag/query` 检索增强问答，返回引用片段、文件名、位置和 chunk 元数据
- 情节梳理、人物分析、主题意象分析、段落细读、双语赏析
- 结构化阅读笔记生成
- SQLite 保存会话、消息、文档、chunk、Agent 运行步骤
- 基于 LangGraph 的证据型 Agent 工作流，支持 `fast` 快速模式和 `deep` 深度模式

## 安装依赖

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置环境变量

复制示例配置：

```bash
cp .env.example .env
```

核心配置：

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=你的 API Key
LLM_MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL_NAME=text-embedding-3-small
EMBEDDING_BATCH_SIZE=16
```

如果暂时没有 API Key，可以不填 `LLM_API_KEY`。系统会使用本地 fallback 逻辑，方便先跑通接口流程；接入真实模型后，回答质量会明显提升。

## 启动项目

```bash
uvicorn app.main:app --reload
```

默认服务地址：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

前端工作台：

```text
http://127.0.0.1:8000/app
```

## 常用接口测试

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

上传文档：

```bash
curl -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@./sample.txt"
```

也可以上传 `.pdf` 或 `.epub`。如果 PDF 是扫描版图片，需要先做 OCR。

查看文档：

```bash
curl http://127.0.0.1:8000/documents
```

删除文档：

```bash
curl -X DELETE http://127.0.0.1:8000/documents/替换为文档ID
```

RAG 问答：

```bash
curl -X POST http://127.0.0.1:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"document_id":"替换为文档ID","query":"这段作品的核心主题是什么？"}'
```

情节梳理：

```bash
curl -X POST http://127.0.0.1:8000/analysis/plot \
  -H "Content-Type: application/json" \
  -d '{"document_id":"替换为文档ID"}'
```

人物分析：

```bash
curl -X POST http://127.0.0.1:8000/analysis/characters \
  -H "Content-Type: application/json" \
  -d '{"document_id":"替换为文档ID","query":"分析主要人物的性格和关系"}'
```

段落细读：

```bash
curl -X POST http://127.0.0.1:8000/analysis/close-reading \
  -H "Content-Type: application/json" \
  -d '{"passage":"这里放入需要细读的文学段落"}'
```

双语赏析：

```bash
curl -X POST http://127.0.0.1:8000/analysis/bilingual \
  -H "Content-Type: application/json" \
  -d '{"passage":"It was the best of times, it was the worst of times."}'
```

生成阅读笔记：

```bash
curl -X POST http://127.0.0.1:8000/notes/generate \
  -H "Content-Type: application/json" \
  -d '{"document_id":"替换为文档ID","focus":"人物关系和主题意象"}'
```

运行证据型 Agent 工作流：

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"document_id":"替换为文档ID","task":"分析作品中人物命运和主题之间的关系","top_k":5,"mode":"deep"}'
```

`mode` 可选：

- `fast`：快速模式，只执行“检索原文 -> 快速回答”，延迟更低。
- `deep`：深度模式，执行“计划 -> 检索 -> Reader -> Critic -> Verifier -> 汇总”，适合展示多智能体编排。

`/agent/run` 内部使用 LangGraph 编排，响应中的 `steps` 会返回每一步的执行轨迹。

## 运行测试

```bash
pytest
```

## 升级注意

当前项目还没有引入 Alembic 迁移系统。如果你本地已有旧版本测试数据，遇到表结构、向量维度或历史数据不兼容问题时，可以清空旧数据库和向量库后重新上传或导入文本：

```bash
rm -rf data/app.db data/chroma data/uploads
mkdir -p data/chroma data/uploads
```

## 项目结构

```text
app/
  main.py
  api/
    router.py
    routes/
  agent/
  book_sources/
  core/
  db/
  prompts/
  rag/
  schemas/
  services/
  tools/
frontend/
  index.html
  styles.css
  app.js
tests/
```



## 公共书源导入与体裁感知 RAG

本项目现在支持从合法公开书源搜索并导入文学文本，导入后会复用现有文档入库链路：保存文本、自动识别体裁、选择 chunk 策略、embedding、写入向量库和 SQLite。

当前支持书源：

- `gutenberg`：Project Gutenberg 公版英文文学，搜索使用 Gutendex，下载优先选择 plain text。
- `wikisource`：中文 Wikisource / 维基文库公开文本，使用 MediaWiki API 获取页面纯文本。

搜索作品：

```bash
curl "http://127.0.0.1:8000/book-sources/search?source=gutenberg&q=pride%20and%20prejudice"
```

导入作品：

```bash
curl -X POST http://127.0.0.1:8000/book-sources/import \
  -H "Content-Type: application/json" \
  -d '{"source":"gutenberg","source_id":"1342"}'
```

导入成功后返回 `document.id`，继续用于 `/rag/query`、`/chat`、`/analysis/*`。

上传文件和书源导入都会自动识别文本体裁：

- `english_fiction`
- `modern_chinese`
- `classical_poetry`
- `classical_prose`
- `poetry_or_lyrics`
- `unknown`

不同体裁会选择不同 chunk 策略：现代文本使用通用段落窗口切分；古诗词生成整首和句组 chunk；文言文按自然段和句群切分。`/rag/query` 返回的 `citations` 会包含 `document_type`、`chunk_type`、`section_title`，便于解释引用来源。

注意：项目不接入盗版电子书站点或 DRM 内容，只支持用户自行上传合法文本或导入公开合法书源。

## 后续可扩展方向

- 本地书库扫描与批量导入：扫描用户授权目录，筛选 `.txt/.md/.pdf/.epub` 后批量入库
- OCR 支持：处理扫描版 PDF 或图片文本，可接入 PaddleOCR、Tesseract 或云 OCR
- 更强的引用核查：对最终回答做 claim-level evidence checking，标记每个结论对应的原文依据
- 上下文压缩与阅读记忆：对长篇作品生成章节摘要、人物记忆和主题记忆，降低长上下文成本
- 人物关系图与时间线：抽取人物、事件、章节位置，形成可视化阅读地图
- 多作品书架与用户系统：支持多用户、收藏、阅读进度、笔记管理
- 后台任务队列：大文件解析、批量 embedding、书源导入可迁移到 Redis + Celery/RQ
- 向量库升级：数据量变大后可评估 Milvus、Qdrant 或 PostgreSQL + pgvector
- 桌面应用形态：用 Electron/Tauri 包装前端，实现更自然的本地文件扫描和离线书库管理
- 部署工程化：补充生产环境 Docker Compose、日志轮转、监控和 CI/CD

