package com.manualai.app.core.network

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class DeviceDto(
    val id: String,
    val name: String,
    val brand: String? = null,
    @Json(name = "model_number") val modelNumber: String? = null,
    val category: String? = null,
    @Json(name = "created_at") val createdAt: String,
)

@JsonClass(generateAdapter = true)
data class CreateDeviceBody(
    val name: String,
    val brand: String? = null,
    @Json(name = "model_number") val modelNumber: String? = null,
    val category: String? = null,
)

@JsonClass(generateAdapter = true)
data class ManualFromUrlBody(
    val url: String,
    @Json(name = "device_id") val deviceId: String? = null,
    @Json(name = "device_name") val deviceName: String? = null,
)

@JsonClass(generateAdapter = true)
data class ManualDto(
    val id: String,
    @Json(name = "device_id") val deviceId: String? = null,
    val filename: String,
    @Json(name = "content_type") val contentType: String,
    @Json(name = "size_bytes") val sizeBytes: Long,
    val status: String,
    @Json(name = "embedding_model") val embeddingModel: String? = null,
    @Json(name = "page_count") val pageCount: Int? = null,
    val error: String? = null,
    @Json(name = "created_at") val createdAt: String,
)

@JsonClass(generateAdapter = true)
data class IdentificationDto(
    val brand: String? = null,
    @Json(name = "model_number") val modelNumber: String? = null,
    val category: String? = null,
    @Json(name = "device_type") val deviceType: String? = null,
    val keywords: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class DeviceMatchDto(
    val device: DeviceDto,
    val manuals: List<ManualDto>,
)

@JsonClass(generateAdapter = true)
data class IdentifyResponseDto(
    val identification: IdentificationDto,
    val matches: List<DeviceMatchDto>,
)

@JsonClass(generateAdapter = true)
data class ProviderInfoDto(
    val provider: String,
    val available: Boolean,
    @Json(name = "default_model") val defaultModel: String,
    val models: List<String>,
)

@JsonClass(generateAdapter = true)
data class ChatMessageDto(val role: String, val content: String)

@JsonClass(generateAdapter = true)
data class ChatRequestBody(
    @Json(name = "device_id") val deviceId: String? = null,
    @Json(name = "manual_id") val manualId: String? = null,
    val messages: List<ChatMessageDto>,
    val provider: String? = null,
    val model: String? = null,
)

@JsonClass(generateAdapter = true)
data class SourceDto(
    @Json(name = "chunk_id") val chunkId: String,
    @Json(name = "manual_id") val manualId: String,
    val page: Int,
    val snippet: String,
)

/** A single SSE frame from /chat. Exactly one of the optional fields is set per type. */
@JsonClass(generateAdapter = true)
data class SseFrame(
    val type: String,
    val text: String? = null,
    val message: String? = null,
    val sources: List<SourceDto>? = null,
)
