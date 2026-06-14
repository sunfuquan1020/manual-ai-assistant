package com.manualai.app.data

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import com.manualai.app.core.BaseUrlProvider
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onEach
import javax.inject.Inject
import javax.inject.Singleton

data class AppSettings(
    val baseUrl: String,
    val provider: String?,
    val model: String?,
)

@Singleton
class SettingsRepository @Inject constructor(
    private val dataStore: DataStore<Preferences>,
    private val baseUrlProvider: BaseUrlProvider,
) {
    private val keyBaseUrl = stringPreferencesKey("base_url")
    private val keyProvider = stringPreferencesKey("provider")
    private val keyModel = stringPreferencesKey("model")

    /** Emits current settings and keeps [BaseUrlProvider] in sync as a side effect. */
    val settings: Flow<AppSettings> = dataStore.data
        .map { prefs ->
            AppSettings(
                baseUrl = prefs[keyBaseUrl] ?: BaseUrlProvider.DEFAULT,
                provider = prefs[keyProvider],
                model = prefs[keyModel],
            )
        }
        .onEach { baseUrlProvider.baseUrl = it.baseUrl }

    /** Read once at startup so the base URL is applied before the first request. */
    suspend fun prime(): AppSettings = settings.first()

    suspend fun update(baseUrl: String, provider: String?, model: String?) {
        dataStore.edit { prefs ->
            prefs[keyBaseUrl] = baseUrl.ifBlank { BaseUrlProvider.DEFAULT }
            if (provider != null) prefs[keyProvider] = provider else prefs.remove(keyProvider)
            if (model != null) prefs[keyModel] = model else prefs.remove(keyModel)
        }
        baseUrlProvider.baseUrl = baseUrl.ifBlank { BaseUrlProvider.DEFAULT }
    }
}
