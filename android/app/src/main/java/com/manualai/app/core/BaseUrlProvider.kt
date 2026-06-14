package com.manualai.app.core

import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Holds the backend base URL. Default targets the host machine from the Android
 * emulator (10.0.2.2). The settings screen can change it at runtime; the value is
 * also persisted via [com.manualai.app.data.SettingsRepository].
 */
@Singleton
class BaseUrlProvider @Inject constructor() {
    @Volatile
    var baseUrl: String = DEFAULT

    fun httpUrl(): HttpUrl = baseUrl.toHttpUrl()

    companion object {
        const val DEFAULT = "http://10.0.2.2:8000/"
    }
}
