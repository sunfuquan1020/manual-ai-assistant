# 说明书 AI 助手 — Android App

Kotlin + Jetpack Compose + Hilt + Retrofit/OkHttp(SSE) + DataStore。
MVP 四个页面：**设备 / 上传 / 问答 / 设置**。

## 构建

需要 Android Studio（Ladybug 或更新）。

```bash
# 在 Android Studio 中：Open → 选择 android/ 目录
# 首次打开会自动下载 Gradle 8.9 并生成 wrapper（gradlew）。
# 然后：Run 'app'，或命令行（生成 wrapper 后）：
./gradlew assembleDebug
```

> 本仓库未包含 `gradlew`/`gradle-wrapper.jar` 二进制。首次在 Android Studio 打开即会生成；
> 或在已装 Gradle 的机器上执行 `gradle wrapper --gradle-version 8.9`。

## 连接后端

- 模拟器访问宿主机后端：Base URL 用 `http://10.0.2.2:8000/`（默认值）。
- 真机：用电脑局域网 IP，如 `http://192.168.1.x:8000/`，并确保后端 `--host 0.0.0.0`。
- 在 **设置** 页可修改 Base URL、选择 AI 供应商（Claude/OpenAI/Ollama）与模型，
  “保存并刷新”会从后端 `GET /providers` 拉取可用供应商。

> Debug 包已开启 `usesCleartextTraffic` 以便本地 http 调试；上线请改 HTTPS。

## 使用流程（MVP）

1. **上传**：选 PDF 说明书（可填设备名），上传后自动建立知识库（索引）。
2. **设备**：查看设备与说明书的索引状态（待处理/索引中/已就绪/失败），可重新索引。
3. **问答**：顶部选设备范围（或全部），输入使用问题，流式得到答案 + 来源页码。
4. **设置**：切换后端地址与 AI 供应商/模型。

## 结构

```
app/src/main/java/com/manualai/app/
  core/            BaseUrlProvider, network/(DTO, ManualApi, HostSelectionInterceptor, ChatSseClient)
  data/            SettingsRepository, ManualRepository, ChatRepository
  di/              AppModule (Hilt)
  feature/
    navigation/    AppNav（底部导航）
    devices/       DevicesScreen + ViewModel
    upload/        UploadScreen + ViewModel
    chat/          ChatScreen + ViewModel（SSE 流式 + 来源）
    settings/      SettingsScreen + ViewModel（供应商/模型/地址）
```
