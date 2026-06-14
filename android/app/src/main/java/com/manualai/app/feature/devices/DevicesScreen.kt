package com.manualai.app.feature.devices

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.manualai.app.core.network.ManualDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DevicesScreen(vm: DevicesViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("我的设备") },
                actions = { TextButton(onClick = vm::refresh) { Text("刷新") } },
            )
        },
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            state.error?.let {
                Text("错误：$it", color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp))
            }
            if (state.loading) {
                CircularProgressIndicator(Modifier.padding(16.dp))
            }
            if (!state.loading && state.devices.isEmpty()) {
                Text("还没有设备。去“上传”页添加一份说明书吧。", Modifier.padding(16.dp))
            }
            LazyColumn(Modifier.fillMaxSize()) {
                items(state.devices, key = { it.id }) { device ->
                    var expanded by remember { mutableStateOf(false) }
                    Card(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp)) {
                        Column(Modifier.padding(12.dp)) {
                            Text(device.name, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
                            device.brand?.let { Text("品牌：$it", style = MaterialTheme.typography.bodySmall) }
                            TextButton(onClick = {
                                expanded = !expanded
                                if (expanded) vm.loadManuals(device.id)
                            }) { Text(if (expanded) "收起说明书" else "查看说明书") }

                            if (expanded) {
                                val manuals = state.manualsByDevice[device.id].orEmpty()
                                if (manuals.isEmpty()) {
                                    Text("（无说明书或加载中）", style = MaterialTheme.typography.bodySmall)
                                }
                                manuals.forEach { manual ->
                                    ManualRow(manual) { vm.ingest(manual.id, device.id) }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ManualRow(manual: ManualDto, onIngest: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Column(Modifier.weight(1f)) {
            Text(manual.filename, style = MaterialTheme.typography.bodyMedium)
            AssistChip(onClick = {}, label = { Text(statusLabel(manual.status)) })
            manual.error?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
        }
        if (manual.status != "processing") {
            Button(onClick = onIngest) {
                Text(if (manual.status == "ready") "重新索引" else "建立知识库")
            }
        }
    }
}

private fun statusLabel(status: String): String = when (status) {
    "pending" -> "待处理"
    "processing" -> "索引中…"
    "ready" -> "已就绪"
    "failed" -> "失败"
    else -> status
}
