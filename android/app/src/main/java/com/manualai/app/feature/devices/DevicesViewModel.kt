package com.manualai.app.feature.devices

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.manualai.app.core.network.DeviceDto
import com.manualai.app.core.network.ManualDto
import com.manualai.app.data.ManualRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DevicesUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val devices: List<DeviceDto> = emptyList(),
    val manualsByDevice: Map<String, List<ManualDto>> = emptyMap(),
)

@HiltViewModel
class DevicesViewModel @Inject constructor(
    private val repo: ManualRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(DevicesUiState())
    val state: StateFlow<DevicesUiState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            runCatching { repo.devices() }
                .onSuccess { devices -> _state.update { it.copy(loading = false, devices = devices) } }
                .onFailure { e -> _state.update { it.copy(loading = false, error = e.message) } }
        }
    }

    fun loadManuals(deviceId: String) {
        viewModelScope.launch {
            runCatching { repo.manuals(deviceId) }
                .onSuccess { manuals ->
                    _state.update { it.copy(manualsByDevice = it.manualsByDevice + (deviceId to manuals)) }
                }
                .onFailure { e -> _state.update { it.copy(error = e.message) } }
        }
    }

    fun ingest(manualId: String, deviceId: String) {
        viewModelScope.launch {
            runCatching { repo.ingest(manualId) }
                .onSuccess { loadManuals(deviceId) }
                .onFailure { e -> _state.update { it.copy(error = e.message) } }
        }
    }
}
