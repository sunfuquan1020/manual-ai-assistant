package com.manualai.app.data

import com.manualai.app.core.network.CreateDeviceBody
import com.manualai.app.core.network.DeviceDto
import com.manualai.app.core.network.ManualApi
import com.manualai.app.core.network.IdentifyResponseDto
import com.manualai.app.core.network.ManualDto
import com.manualai.app.core.network.ManualFromUrlBody
import com.manualai.app.core.network.ProviderInfoDto
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ManualRepository @Inject constructor(private val api: ManualApi) {

    suspend fun devices(): List<DeviceDto> = api.listDevices()

    suspend fun createDevice(name: String, brand: String?): DeviceDto =
        api.createDevice(CreateDeviceBody(name = name, brand = brand?.ifBlank { null }))

    suspend fun manuals(deviceId: String): List<ManualDto> = api.deviceManuals(deviceId)

    suspend fun providers(): List<ProviderInfoDto> = api.providers()

    suspend fun identify(
        bytes: ByteArray,
        mimeType: String,
        provider: String?,
        model: String?,
    ): IdentifyResponseDto {
        val imagePart = MultipartBody.Part.createFormData(
            "file", "photo.jpg", bytes.toRequestBody(mimeType.toMediaType()),
        )
        val plain = "text/plain".toMediaType()
        return api.identify(
            file = imagePart,
            provider = provider?.toRequestBody(plain),
            model = model?.toRequestBody(plain),
        )
    }

    suspend fun upload(
        bytes: ByteArray,
        filename: String,
        deviceId: String?,
        deviceName: String?,
    ): ManualDto {
        val filePart = MultipartBody.Part.createFormData(
            "file", filename, bytes.toRequestBody("application/pdf".toMediaType()),
        )
        val plain = "text/plain".toMediaType()
        return api.uploadManual(
            file = filePart,
            deviceId = deviceId?.toRequestBody(plain),
            deviceName = deviceName?.ifBlank { null }?.toRequestBody(plain),
        )
    }

    suspend fun fromUrl(url: String, deviceName: String?): ManualDto =
        api.manualFromUrl(
            ManualFromUrlBody(url = url, deviceName = deviceName?.ifBlank { null }),
        )

    suspend fun ingest(manualId: String): ManualDto = api.ingest(manualId)

    suspend fun getManual(manualId: String): ManualDto = api.getManual(manualId)
}
