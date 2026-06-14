package com.manualai.app.feature.identify

import android.graphics.Bitmap
import android.net.Uri
import java.io.ByteArrayOutputStream
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.manualai.app.core.network.IdentificationDto
import com.manualai.app.core.network.IdentifyResponseDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IdentifyScreen(vm: IdentifyViewModel = hiltViewModel()) {
    val context = LocalContext.current
    val state by vm.state.collectAsStateWithLifecycle()

    val galleryPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.GetContent(),
    ) { uri: Uri? ->
        if (uri != null) {
            val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
            if (bytes != null) vm.identify(bytes, mime)
        }
    }
    val cameraPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicturePreview(),
    ) { bitmap: Bitmap? ->
        if (bitmap != null) vm.identify(bitmap.toJpegBytes(), "image/jpeg")
    }

    Scaffold(topBar = { TopAppBar(title = { Text("拍照识别设备") }) }) { padding ->
        Column(
            Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("拍一张设备照片（含品牌/型号铭牌更准），自动识别并匹配你的说明书。", style = MaterialTheme.typography.bodyMedium)
            Button(onClick = { cameraPicker.launch(null) }, modifier = Modifier.fillMaxWidth()) {
                Text("拍照")
            }
            OutlinedButton(onClick = { galleryPicker.launch("image/*") }, modifier = Modifier.fillMaxWidth()) {
                Text("从相册选择")
            }

            when (val s = state) {
                IdentifyState.Idle -> {}
                IdentifyState.Working -> {
                    CircularProgressIndicator()
                    Text("识别中…")
                }
                is IdentifyState.Error -> Text("失败：${s.message}", color = MaterialTheme.colorScheme.error)
                is IdentifyState.Done -> ResultView(s.result)
            }
        }
    }
}

@Composable
private fun ResultView(result: IdentifyResponseDto) {
    IdentificationCard(result.identification)
    Text("匹配到的设备", fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 8.dp))
    if (result.matches.isEmpty()) {
        Text("未匹配到已有设备。可去“上传”页为该设备添加说明书。", style = MaterialTheme.typography.bodySmall)
    } else {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(result.matches) { m ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp)) {
                        Text(m.device.name, fontWeight = FontWeight.Bold)
                        m.device.brand?.let { Text("品牌：$it", style = MaterialTheme.typography.bodySmall) }
                        Text("已就绪说明书：${m.manuals.size} 份", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
private fun IdentificationCard(id: IdentificationDto) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Text("识别结果", fontWeight = FontWeight.Bold)
            Text("品牌：${id.brand ?: "-"}", style = MaterialTheme.typography.bodySmall)
            Text("型号：${id.modelNumber ?: "-"}", style = MaterialTheme.typography.bodySmall)
            Text("类别：${id.category ?: "-"}  类型：${id.deviceType ?: "-"}", style = MaterialTheme.typography.bodySmall)
            if (id.keywords.isNotEmpty()) {
                Text("关键词：${id.keywords.joinToString("、")}", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

private fun Bitmap.toJpegBytes(): ByteArray {
    val stream = ByteArrayOutputStream()
    compress(Bitmap.CompressFormat.JPEG, 90, stream)
    return stream.toByteArray()
}
