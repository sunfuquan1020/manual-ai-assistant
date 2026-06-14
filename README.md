# 说明书 AI 助手（Instructions-AI）

把家里各种电器的电子说明书集中成知识库，用 AI 对话直接回答"怎么用/怎么修"，并给出
说明书原文出处。

- **后端** [`backend/`](backend/README.md)：Python + FastAPI，RAG（PyMuPDF 解析 +
  向量检索 pgvector）+ 多供应商 LLM（Claude / OpenAI / Ollama，可切换）。
- **客户端** [`android/`](android/README.md)：Kotlin + Jetpack Compose，
  上传 / 设备 / 问答 / 设置 四个页面。

## 已实现功能

1. 上传 PDF 说明书 / **扫二维码下载**（`POST /manuals/from-url`）→ 自动建立 RAG 知识库
2. 设备/说明书管理与索引状态
3. AI 对话：检索对应说明书，流式作答 + 来源页码，供应商可在设置页切换
4. **拍照识别设备**：LLM vision 识别品牌/型号并匹配已有设备（`POST /devices/identify`）

四大功能全部落地。后续可扩展：扫描件 PDF 的 OCR、识别后一键跳转对应设备问答等。

## 快速跑通

```bash
# 1) 后端
cd backend
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env            # 填默认供应商密钥（如 ANTHROPIC_API_KEY + VOYAGE_API_KEY）
docker compose up -d && alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --reload

# 2) 客户端
# Android Studio 打开 android/，设置页 Base URL 用 http://10.0.2.2:8000/（模拟器）
```

详见各子目录 README。实现规划见
`~/.claude/plans/app-android-app-ai-1-app-pdf-jiggly-meteor.md`。
