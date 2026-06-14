package com.manualai.app.feature.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Devices
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.manualai.app.data.SettingsRepository
import com.manualai.app.feature.chat.ChatScreen
import com.manualai.app.feature.devices.DevicesScreen
import com.manualai.app.feature.identify.IdentifyScreen
import com.manualai.app.feature.scan.ScanScreen
import com.manualai.app.feature.settings.SettingsScreen
import com.manualai.app.feature.upload.UploadScreen
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RootViewModel @Inject constructor(settings: SettingsRepository) : ViewModel() {
    init {
        // Apply the persisted base URL before any request is made.
        viewModelScope.launch { runCatching { settings.prime() } }
    }
}

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("devices", "设备", Icons.Filled.Devices),
    Tab("upload", "上传", Icons.Filled.UploadFile),
    Tab("chat", "问答", Icons.Filled.Chat),
    Tab("settings", "设置", Icons.Filled.Settings),
)

@Composable
fun AppNav() {
    hiltViewModel<RootViewModel>() // trigger settings priming
    val navController = rememberNavController()

    Scaffold(
        bottomBar = {
            NavigationBar {
                val backStack by navController.currentBackStackEntryAsState()
                val current = backStack?.destination
                tabs.forEach { tab ->
                    val selected = current?.hierarchy?.any { it.route == tab.route } == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            navController.navigate(tab.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = "devices",
            modifier = Modifier.padding(padding),
        ) {
            composable("devices") { DevicesScreen() }
            composable("upload") {
                UploadScreen(
                    onScanClick = { navController.navigate("scan") },
                    onIdentifyClick = { navController.navigate("identify") },
                )
            }
            composable("scan") { ScanScreen(onClose = { navController.popBackStack() }) }
            composable("identify") { IdentifyScreen() }
            composable("chat") { ChatScreen() }
            composable("settings") { SettingsScreen() }
        }
    }
}
