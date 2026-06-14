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
| POST | `/manuals/from-url` | 按 URL 下载 PDF（扫码流程）并自动索引 |
| POST | `/manuals/{id}/ingest` | 解析→分块→向量化 |
| GET  | `/manuals/{id}` | 查说明书状态 |
| POST | `/devices` / GET `/devices` | 设备管理 |
| GET  | `/devices/{id}/manuals` | 某设备的说明书 |
| POST | `/devices/identify` | 上传设备照片，LLM vision 识别品牌/型号并匹配设备（multipart：`file` + 可选 `provider`/`model`） |
| GET  | `/providers` | 可用供应商与模型列表 |
| POST | `/chat` | RAG 对话，SSE 流式 |

## 测试

```bash
pytest                 # 全部（默认含录制式 provider 测试，离线）
pytest -m recorded     # 仅 LLM provider 录制回放测试（claude/openai/ollama，离线）
pytest -m pgvector     # 需要运行中的 Postgres + pgvector
```

录制式测试用 `tests/cassettes/` 下的录制响应 + httpx MockTransport 回放，
跑通各 provider 的真实 SDK 解析逻辑，无需密钥与网络。重新录制只需用真实响应覆盖对应
cassette 文件（保持线格式不变）。
