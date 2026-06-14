package com.manualai.app.core.network

import com.manualai.app.core.BaseUrlProvider
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject

/**
 * Rewrites every request's scheme/host/port to the runtime-configurable base URL,
 * so changing the backend address in Settings takes effect without rebuilding
 * Retrofit (whose base URL is otherwise fixed at construction).
 */
class HostSelectionInterceptor @Inject constructor(
    private val baseUrlProvider: BaseUrlProvider,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val base = baseUrlProvider.httpUrl()
        val request = chain.request()
        val newUrl = request.url.newBuilder()
            .scheme(base.scheme)
            .host(base.host)
            .port(base.port)
            .build()
        return chain.proceed(request.newBuilder().url(newUrl).build())
    }
}
