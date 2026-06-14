package com.manualai.app.data

import com.manualai.app.core.network.ChatRequestBody
import com.manualai.app.core.network.ChatSseClient
import com.manualai.app.core.network.ChatStreamEvent
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepository @Inject constructor(private val sse: ChatSseClient) {
    fun stream(body: ChatRequestBody): Flow<ChatStreamEvent> = sse.stream(body)
}
