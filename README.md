# 文学作品深度阅读助手 AI 后端 MVP

这是一个基于 FastAPI 的 AI 应用后端，用于对用户上传的文学作品或文学片段进行“基于原文”的深度阅读分析。MVP 支持文档上传、文本切分、向量检索、RAG 问答、文学分析接口、阅读笔记生成，以及一个可扩展的轻量 Agent 工作流。

## 已实现功能

- FastAPI 服务启动与 `/health` 健康检查
- `.env` 配置读取，不在代码里硬编码 API Key
- OpenAI-compatible LLM 调用，支持 `base_url / api_key / model_name`
- `/chat` 普通文学问答
- `/chat/stream` SSE 流式输出
- `.txt` / `.md` 文档上传
- 文档解析、chunking、embedding、向量入库
- ChromaDB 向量库，Chroma 不可用时自动 fallback 到本地 JSON 向量检索
- `/rag/query` 检索增强问答，返回引用片段
- 情节梳理、人物分析、主题意象分析、段落细读、双语赏析
- 结构化阅读笔记生成
- SQLite 保存会话、消息、文档、chunk、Agent 运行步骤
- 预留多智能体扩展结构：Reader / Critic / Translator / Verifier

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

查看文档：

```bash
curl http://127.0.0.1:8000/documents
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

运行 Agent：

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"document_id":"替换为文档ID","task":"分析作品中人物命运和主题之间的关系"}'
```

## 运行测试

```bash
pytest
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

## 后续可扩展方向

- 支持 PDF / EPUB 解析
- 增加人物关系抽取与时间线抽取接口
- 引入 LangGraph，实现 Reader / Critic / Translator / Verifier 多智能体协作
- 增加回答 verifier，检查每个结论是否有原文证据
- 增加前端阅读工作台，展示引用、笔记、人物与主题结构
- 增加用户系统与多作品书架

