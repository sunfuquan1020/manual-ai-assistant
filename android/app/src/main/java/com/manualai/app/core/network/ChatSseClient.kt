package com.manualai.app.core.network

import com.manualai.app.core.BaseUrlProvider
import com.squareup.moshi.Moshi
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

sealed interface ChatStreamEvent {
    data class Sources(val sources: List<SourceDto>) : ChatStreamEvent
    data class Delta(val text: String) : ChatStreamEvent
    data object Done : ChatStreamEvent
    data class Error(val message: String) : ChatStreamEvent
}

@Singleton
class ChatSseClient @Inject constructor(
    baseClient: OkHttpClient,
    private val baseUrlProvider: BaseUrlProvider,
    moshi: Moshi,
) {
    // SSE needs no read timeout — the connection stays open while streaming.
    private val sseClient: OkHttpClient =
        baseClient.newBuilder().readTimeout(0, TimeUnit.MILLISECONDS).build()
    private val frameAdapter = moshi.adapter(SseFrame::class.java)
    private val bodyAdapter = moshi.adapter(ChatRequestBody::class.java)

    fun stream(body: ChatRequestBody): Flow<ChatStreamEvent> = callbackFlow {
        val url = baseUrlProvider.httpUrl().newBuilder().addPathSegment("chat").build()
        val request = Request.Builder()
            .url(url)
            .header("Accept", "text/event-stream")
            .post(bodyAdapter.toJson(body).toRequestBody("application/json".toMediaType()))
            .build()

        val listener = object : EventSourceListener() {
            override fun onEvent(
                eventSource: EventSource,
                id: String?,
                type: String?,
                data: String,
            ) {
                val frame = runCatching { frameAdapter.fromJson(data) }.getOrNull() ?: return
                when (frame.type) {
                    "sources" -> trySend(ChatStreamEvent.Sources(frame.sources ?: emptyList()))
                    "delta" -> frame.text?.let { trySend(ChatStreamEvent.Delta(it)) }
                    "done" -> { trySend(ChatStreamEvent.Done); close() }
                    "error" -> {
                        trySend(ChatStreamEvent.Error(frame.message ?: "error"))
                        close()
                    }
                }
            }

            override fun onClosed(eventSource: EventSource) {
                close()
            }

            override fun onFailure(
                eventSource: EventSource,
                t: Throwable?,
                response: okhttp3.Response?,
            ) {
                trySend(ChatStreamEvent.Error(t?.message ?: "network error"))
                close()
            }
        }

        val source = EventSources.createFactory(sseClient).newEventSource(request, listener)
        awaitClose { source.cancel() }
    }
}
