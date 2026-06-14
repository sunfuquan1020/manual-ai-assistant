package com.manualai.app.feature.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.manualai.app.core.network.ChatMessageDto
import com.manualai.app.core.network.ChatRequestBody
import com.manualai.app.core.network.ChatStreamEvent
import com.manualai.app.core.network.DeviceDto
import com.manualai.app.core.network.SourceDto
import com.manualai.app.data.ChatRepository
import com.manualai.app.data.ManualRepository
import com.manualai.app.data.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class UiMessage(val role: String, val text: String)

data class ChatUiState(
    val devices: List<DeviceDto> = emptyList(),
    val selectedDeviceId: String? = null,
    val messages: List<UiMessage> = emptyList(),
    val sources: List<SourceDto> = emptyList(),
    val streaming: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepo: ChatRepository,
    private val manualRepo: ManualRepository,
    private val settings: SettingsRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(ChatUiState())
    val state: StateFlow<ChatUiState> = _state.asStateFlow()
    private var streamJob: Job? = null

    init {
        viewModelScope.launch {
            runCatching { manualRepo.devices() }
                .onSuccess { devices -> _state.update { it.copy(devices = devices) } }
        }
    }

    fun selectDevice(deviceId: String?) {
        _state.update { it.copy(selectedDeviceId = deviceId) }
    }

    fun send(text: String) {
        if (text.isBlank() || _state.value.streaming) return

        _state.update {
            it.copy(
                messages = it.messages + UiMessage("user", text) + UiMessage("assistant", ""),
                sources = emptyList(),
                streaming = true,
                error = null,
            )
        }

        val current = _state.value
        val history = current.messages
            .dropLast(1) // exclude the empty assistant placeholder
            .map { ChatMessageDto(role = it.role, content = it.text) }

        streamJob?.cancel()
        streamJob = viewModelScope.launch {
            val cfg = settings.settings.first()
            val body = ChatRequestBody(
                deviceId = current.selectedDeviceId,
                messages = history,
                provider = cfg.provider,
                model = cfg.model,
            )
            runCatching {
                chatRepo.stream(body).collect { event -> handle(event) }
            }.onFailure { e ->
                _state.update { it.copy(streaming = false, error = e.message) }
            }
        }
    }

    private fun handle(event: ChatStreamEvent) {
        when (event) {
            is ChatStreamEvent.Sources -> _state.update { it.copy(sources = event.sources) }
            is ChatStreamEvent.Delta -> appendToAssistant(event.text)
            ChatStreamEvent.Done -> _state.update { it.copy(streaming = false) }
            is ChatStreamEvent.Error ->
                _state.update { it.copy(streaming = false, error = event.message) }
        }
    }

    private fun appendToAssistant(delta: String) {
        _state.update { st ->
            val msgs = st.messages.toMutableList()
            val idx = msgs.indexOfLast { it.role == "assistant" }
            if (idx >= 0) msgs[idx] = msgs[idx].copy(text = msgs[idx].text + delta)
            st.copy(messages = msgs)
        }
    }
}
