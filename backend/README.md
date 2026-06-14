# 说明书 AI 助手 — 后端 (FastAPI)

RAG 知识库 + 多供应商 LLM（Claude / OpenAI / Ollama）对话后端。所有 LLM/embedding
密钥只在后端，Android App 只传供应商与模型名。

## 快速开始

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 填入至少“默认供应商”的密钥

docker compose up -d          # 启动 Postgres + pgvector
alembic upgrade head          # 建表（含 CREATE EXTENSION vector）

uvicorn app.main:app --reload
```

打开 http://localhost:8000/docs 查看接口。

## 配置（.env）

- `DEFAULT_LLM_PROVIDER` = `claude` | `openai` | `ollama`（对话默认供应商，可被请求覆盖）
- `DEFAULT_EMBEDDING_PROVIDER` = `voyage` | `openai` | `ollama`（全局；切换需重新 ingest）
- 各供应商密钥：`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `VOYAGE_API_KEY` / `OLLAMA_BASE_URL`

启动时只校验**默认**供应商所需密钥；其它供应商在请求时按需校验。

## 接口（MVP）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/manuals/upload` | 上传 PDF 说明书（multipart：`file` + 可选 `device_id`/`device_name`） |
| POST | `/manuals/{id}/ingest` | 解析→分块→向量化（Stage 2） |
| GET  | `/manuals/{id}` | 查说明书状态 |
| POST | `/devices` / GET `/devices` | 设备管理 |
| GET  | `/devices/{id}/manuals` | 某设备的说明书 |
| GET  | `/providers` | 可用供应商与模型列表（Stage 3） |
| POST | `/chat` | RAG 对话，SSE 流式（Stage 3） |

## 测试

```bash
pytest                 # 上传等不依赖 pgvector 的测试（SQLite）
pytest -m pgvector     # 需要运行中的 Postgres + pgvector
```
