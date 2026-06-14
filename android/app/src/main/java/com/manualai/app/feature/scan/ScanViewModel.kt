package com.manualai.app.feature.scan

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

sealed interface ScanState {
    data object Scanning : ScanState
    data class Downloading(val url: String) : ScanState
    data class Done(val manual: ManualDto) : ScanState
    data class Error(val message: String) : ScanState
}

@HiltViewModel
class ScanViewModel @Inject constructor(
    private val repo: ManualRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<ScanState>(ScanState.Scanning)
    val state: StateFlow<ScanState> = _state.asStateFlow()

    /** Called when a QR code containing a URL is detected. Ignored if already busy. */
    fun onUrlScanned(url: String, deviceName: String) {
        if (_state.value !is ScanState.Scanning) return
        _state.value = ScanState.Downloading(url)
        viewModelScope.launch {
            runCatching { repo.fromUrl(url, deviceName) }
                .onSuccess { _state.value = ScanState.Done(it) }
                .onFailure { _state.value = ScanState.Error(it.message ?: "下载失败") }
        }
    }

    fun rescan() { _state.value = ScanState.Scanning }
}
