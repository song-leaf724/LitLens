# 文学作品深度阅读助手 AI 后端 MVP

[English](README_EN.md) | 中文

这是一个基于 FastAPI 的 AI 应用后端，用于对用户上传的文学作品或文学片段进行“基于原文”的深度阅读分析。MVP 支持文档上传、文本切分、向量检索、RAG 问答、文学分析接口、阅读笔记生成，以及一个基于 LangGraph 的证据型文学分析 Agent 工作流。

## 已实现功能

- FastAPI 服务启动与 `/health` 健康检查
- `.env` 配置读取，不在代码里硬编码 API Key
- OpenAI-compatible LLM 调用，支持 `base_url / api_key / model_name`
- `/chat` 普通文学问答
- `/chat/stream` SSE 流式输出
- `.txt` / `.md` / `.pdf` / `.epub` 文档上传与解析
- 文档解析、chunking、embedding、向量入库
- ChromaDB 向量库，Chroma 不可用时自动 fallback 到本地 JSON 向量检索
- `/rag/query` 检索增强问答，返回引用片段
- 情节梳理、人物分析、主题意象分析、段落细读、双语赏析
- 结构化阅读笔记生成
- SQLite 保存会话、消息、文档、chunk、Agent 运行步骤
- 基于 LangGraph 的证据型 Agent 工作流，支持快速模式和深度模式

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

本次版本扩展了 `documents` 和 `chunks` 数据表字段。当前 MVP 还没有引入 Alembic 迁移系统，如果你本地已有旧版本测试数据，启动前建议清空旧数据库和向量库后重新上传或导入文本：

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
  services/
  schemas/
  core/
  rag/
  agent/
  tools/
  db/
  prompts/
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

- 支持 PDF / EPUB 解析
- 增加人物关系抽取与时间线抽取接口
- 引入 LangGraph，实现 Reader / Critic / Translator / Verifier 多智能体协作
- 增加回答 verifier，检查每个结论是否有原文证据
- 增加前端阅读工作台，展示引用、笔记、人物与主题结构
- 增加用户系统与多作品书架

