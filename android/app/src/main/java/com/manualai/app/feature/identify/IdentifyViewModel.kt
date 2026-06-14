package com.manualai.app.feature.identify

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.manualai.app.core.network.IdentifyResponseDto
import com.manualai.app.data.ManualRepository
import com.manualai.app.data.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface IdentifyState {
    data object Idle : IdentifyState
    data object Working : IdentifyState
    data class Done(val result: IdentifyResponseDto) : IdentifyState
    data class Error(val message: String) : IdentifyState
}

@HiltViewModel
class IdentifyViewModel @Inject constructor(
    private val repo: ManualRepository,
    private val settings: SettingsRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<IdentifyState>(IdentifyState.Idle)
    val state: StateFlow<IdentifyState> = _state.asStateFlow()

    fun identify(bytes: ByteArray, mimeType: String) {
        if (_state.value is IdentifyState.Working) return
        _state.value = IdentifyState.Working
        viewModelScope.launch {
            val cfg = settings.settings.first()
            // Use the selected provider; leave model null so the backend picks a
            // vision-capable default for that provider.
            runCatching { repo.identify(bytes, mimeType, cfg.provider, null) }
                .onSuccess { _state.value = IdentifyState.Done(it) }
                .onFailure { _state.value = IdentifyState.Error(it.message ?: "识别失败") }
        }
    }

    fun reset() { _state.value = IdentifyState.Idle }
}
