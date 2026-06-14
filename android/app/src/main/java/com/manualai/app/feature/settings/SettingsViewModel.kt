package com.manualai.app.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.manualai.app.core.BaseUrlProvider
import com.manualai.app.core.network.ProviderInfoDto
import com.manualai.app.data.ManualRepository
import com.manualai.app.data.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val baseUrl: String = BaseUrlProvider.DEFAULT,
    val providers: List<ProviderInfoDto> = emptyList(),
    val selectedProvider: String? = null,
    val selectedModel: String? = null,
    val loading: Boolean = false,
    val error: String? = null,
    val saved: Boolean = false,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settings: SettingsRepository,
    private val manualRepo: ManualRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(SettingsUiState())
    val state: StateFlow<SettingsUiState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            val cfg = settings.settings.first()
            _state.update {
                it.copy(
                    baseUrl = cfg.baseUrl,
                    selectedProvider = cfg.provider,
                    selectedModel = cfg.model,
                )
            }
            fetchProviders()
        }
    }

    fun onBaseUrlChange(value: String) {
        _state.update { it.copy(baseUrl = value, saved = false) }
    }

    fun selectProvider(provider: String) {
        val default = _state.value.providers.firstOrNull { it.provider == provider }?.defaultModel
        _state.update { it.copy(selectedProvider = provider, selectedModel = default, saved = false) }
    }

    fun selectModel(model: String) {
        _state.update { it.copy(selectedModel = model, saved = false) }
    }

    /** Persist settings (also applies the base URL), then re-fetch providers from the backend. */
    fun saveAndRefresh() {
        viewModelScope.launch {
            val s = _state.value
            settings.update(s.baseUrl, s.selectedProvider, s.selectedModel)
            _state.update { it.copy(saved = true) }
            fetchProviders()
        }
    }

    private suspend fun fetchProviders() {
        _state.update { it.copy(loading = true, error = null) }
        runCatching { manualRepo.providers() }
            .onSuccess { list -> _state.update { it.copy(loading = false, providers = list) } }
            .onFailure { e -> _state.update { it.copy(loading = false, error = e.message) } }
    }
}
