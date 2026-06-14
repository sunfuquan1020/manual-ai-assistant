package com.manualai.app.feature.upload

import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UploadScreen(vm: UploadViewModel = hiltViewModel()) {
    val context = LocalContext.current
    val state by vm.state.collectAsStateWithLifecycle()
    var deviceName by remember { mutableStateOf("") }

    val picker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri: Uri? ->
        if (uri != null) {
            val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            val name = queryDisplayName(context, uri) ?: "manual.pdf"
            if (bytes != null) vm.upload(bytes, name, deviceName)
        }
    }

    Scaffold(topBar = { TopAppBar(title = { Text("上传说明书") }) }) { padding ->
        Column(
            Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("选择一份 PDF 说明书，上传后会自动建立知识库（索引）。", style = MaterialTheme.typography.bodyMedium)
            OutlinedTextField(
                value = deviceName,
                onValueChange = { deviceName = it },
                label = { Text("设备名称（可选，如：客厅空调）") },
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                onClick = { picker.launch(arrayOf("application/pdf")) },
                enabled = state !is UploadState.Working,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("选择 PDF 并上传") }

            when (val s = state) {
                is UploadState.Working -> {
                    CircularProgressIndicator()
                    Text("上传并索引中…")
                }
                is UploadState.Done -> Text(
                    "已上传：${s.manual.filename}（状态：${s.manual.status}）。可到“设备”页查看索引进度。",
                    color = MaterialTheme.colorScheme.primary,
                )
                is UploadState.Error -> Text("失败：${s.message}", color = MaterialTheme.colorScheme.error)
                UploadState.Idle -> {}
            }
        }
    }
}

private fun queryDisplayName(context: android.content.Context, uri: Uri): String? {
    context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
        val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        if (index >= 0 && cursor.moveToFirst()) return cursor.getString(index)
    }
    return null
}
