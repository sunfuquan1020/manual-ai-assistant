package com.manualai.app.feature.upload

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.manualai.app.core.network.ManualDto
import com.manualai.app.data.ManualRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface UploadState {
    data object Idle : UploadState
    data object Working : UploadState
    data class Done(val manual: ManualDto) : UploadState
    data class Error(val message: String) : UploadState
}

@HiltViewModel
class UploadViewModel @Inject constructor(
    private val repo: ManualRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<UploadState>(UploadState.Idle)
    val state: StateFlow<UploadState> = _state.asStateFlow()

    /** Upload the PDF, then immediately kick off ingestion to build the knowledge base. */
    fun upload(bytes: ByteArray, filename: String, deviceName: String) {
        viewModelScope.launch {
            _state.value = UploadState.Working
            runCatching {
                val manual = repo.upload(bytes, filename, deviceId = null, deviceName = deviceName)
                repo.ingest(manual.id)
            }
                .onSuccess { _state.value = UploadState.Done(it) }
                .onFailure { _state.value = UploadState.Error(it.message ?: "上传失败") }
        }
    }

    fun reset() { _state.value = UploadState.Idle }
}
