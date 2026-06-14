package com.manualai.app.core.network

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface ManualApi {
    @GET("devices")
    suspend fun listDevices(): List<DeviceDto>

    @POST("devices")
    suspend fun createDevice(@retrofit2.http.Body body: CreateDeviceBody): DeviceDto

    @GET("devices/{id}/manuals")
    suspend fun deviceManuals(@Path("id") deviceId: String): List<ManualDto>

    @Multipart
    @POST("devices/identify")
    suspend fun identify(
        @Part file: MultipartBody.Part,
        @Part("provider") provider: RequestBody?,
        @Part("model") model: RequestBody?,
    ): IdentifyResponseDto

    @Multipart
    @POST("manuals/upload")
    suspend fun uploadManual(
        @Part file: MultipartBody.Part,
        @Part("device_id") deviceId: RequestBody?,
        @Part("device_name") deviceName: RequestBody?,
    ): ManualDto

    @POST("manuals/from-url")
    suspend fun manualFromUrl(@retrofit2.http.Body body: ManualFromUrlBody): ManualDto

    @POST("manuals/{id}/ingest")
    suspend fun ingest(@Path("id") manualId: String): ManualDto

    @GET("manuals/{id}")
    suspend fun getManual(@Path("id") manualId: String): ManualDto

    @GET("providers")
    suspend fun providers(): List<ProviderInfoDto>
}
