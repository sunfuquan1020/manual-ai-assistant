package com.manualai.app.feature.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.manualai.app.core.network.ProviderInfoDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(vm: SettingsViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    Scaffold(topBar = { TopAppBar(title = { Text("设置") }) }) { padding ->
        Column(
            Modifier.padding(padding).fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text("后端地址", fontWeight = FontWeight.Bold)
            OutlinedTextField(
                value = state.baseUrl,
                onValueChange = vm::onBaseUrlChange,
                label = { Text("Base URL（模拟器用 http://10.0.2.2:8000/）") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )

            Text("AI 供应商", fontWeight = FontWeight.Bold)
            if (state.loading) CircularProgressIndicator()
            state.error?.let { Text("无法获取供应商列表：$it", color = MaterialTheme.colorScheme.error) }

            ProviderDropdown(state.providers, state.selectedProvider, vm::selectProvider)

            val models = state.providers.firstOrNull { it.provider == state.selectedProvider }?.models.orEmpty()
            if (models.isNotEmpty()) {
                Text("模型", fontWeight = FontWeight.Bold)
                ModelDropdown(models, state.selectedModel, vm::selectModel)
            }

            Button(onClick = vm::saveAndRefresh, modifier = Modifier.fillMaxWidth()) {
                Text("保存并刷新")
            }
            if (state.saved) Text("已保存。", color = MaterialTheme.colorScheme.primary)
        }
    }
}

@Composable
private fun ProviderDropdown(
    providers: List<ProviderInfoDto>,
    selected: String?,
    onSelect: (String) -> Unit,
) {
    var open by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth()) {
        OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) {
            Text(selected ?: "（默认）")
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            providers.forEach { p ->
                val label = p.provider + if (p.available) "" else "（未配置）"
                DropdownMenuItem(
                    text = { Text(label) },
                    enabled = p.available,
                    onClick = { onSelect(p.provider); open = false },
                )
            }
        }
    }
}

@Composable
private fun ModelDropdown(models: List<String>, selected: String?, onSelect: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth()) {
        OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) {
            Text(selected ?: models.first())
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            models.forEach { m ->
                DropdownMenuItem(text = { Text(m) }, onClick = { onSelect(m); open = false })
            }
        }
    }
}
