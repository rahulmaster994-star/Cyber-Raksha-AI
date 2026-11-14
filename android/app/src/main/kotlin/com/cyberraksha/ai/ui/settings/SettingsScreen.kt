package com.cyberraksha.ai.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.ui.theme.*
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    prefs: AppPreferences,
    onBack: () -> Unit,
    onLogout: () -> Unit = {},
    onNavigateToOnboarding: () -> Unit = {},
    viewModel: SettingsViewModel = remember { SettingsViewModel(prefs) }
) {
    val state by viewModel.uiState.collectAsState()
    var severityMenuExpanded by remember { mutableStateOf(false) }
    var showDeleteDialog by remember { mutableStateOf(false) }

    val coroutineScope = rememberCoroutineScope()
    val userName by prefs.userName.collectAsState(initial = null)
    val userEmail by prefs.userEmail.collectAsState(initial = null)
    val userMobile by prefs.userMobile.collectAsState(initial = null)
    val isMobileVerified by prefs.isMobileVerified.collectAsState(initial = false)
    val userToken by prefs.userToken.collectAsState(initial = null)
    val whatsappEnabled by prefs.whatsappProtectionEnabled.collectAsState(initial = true)
    val telegramEnabled by prefs.telegramProtectionEnabled.collectAsState(initial = true)
    val callBlockingEnabled by prefs.callBlockingEnabled.collectAsState(initial = true)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings", fontWeight = FontWeight.Bold, color = TextPrimary) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = TextPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DarkSurface)
            )
        },
        containerColor = DarkBackground
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Status Message (if any)
            state.statusMessage?.let { msg ->
                val color = if (state.isSuccess) SeverityLow else SeverityCritical
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(color.copy(alpha = 0.15f), RoundedCornerShape(8.dp))
                        .padding(12.dp)
                ) {
                    Icon(
                        imageVector = if (state.isSuccess) Icons.Default.CheckCircle else Icons.Default.Warning,
                        contentDescription = null,
                        tint = color,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(text = msg, style = MaterialTheme.typography.bodyMedium, color = color)
                }
            }

            // Backend Connectivity Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Text(
                        text = "Backend Node Configuration",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedTextField(
                        value = state.backendUrl,
                        onValueChange = viewModel::onBackendUrlChanged,
                        label = { Text("Backend URL") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = CyberCyan,
                            unfocusedBorderColor = DarkOutline
                        )
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = { viewModel.saveBackendUrl() },
                        enabled = !state.isTesting,
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCyan),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (state.isTesting) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                color = DarkBackground,
                                strokeWidth = 2.dp
                            )
                        } else {
                            Text("Test & Save Connectivity", color = DarkBackground, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            // Notifications Configuration Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Text(
                        text = "Notification Settings",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Push Alerts", fontWeight = FontWeight.Medium, color = TextPrimary)
                            Text("Deliver instant security notifications", style = MaterialTheme.typography.labelSmall, color = TextSecondary)
                        }
                        Switch(
                            checked = state.notificationsEnabled,
                            onCheckedChange = viewModel::onNotificationsToggled,
                            colors = SwitchDefaults.colors(checkedThumbColor = CyberCyan)
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Minimum Severity Filter
                    ExposedDropdownMenuBox(
                        expanded = severityMenuExpanded,
                        onExpandedChange = { severityMenuExpanded = !severityMenuExpanded }
                    ) {
                        OutlinedTextField(
                            value = "Min Severity: ${state.minSeverity}",
                            onValueChange = {},
                            readOnly = true,
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = severityMenuExpanded) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .menuAnchor(MenuAnchorType.PrimaryNotEditable),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = CyberCyan,
                                unfocusedBorderColor = DarkOutline
                            )
                        )
                        ExposedDropdownMenu(
                            expanded = severityMenuExpanded,
                            onDismissRequest = { severityMenuExpanded = false }
                        ) {
                            listOf("LOW", "MEDIUM", "HIGH", "CRITICAL").forEach { sev ->
                                DropdownMenuItem(
                                    text = { Text(sev) },
                                    onClick = {
                                        viewModel.onMinSeverityChanged(sev)
                                        severityMenuExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }
            }

            // Device Identification Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Text(
                        text = "Device Registration",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    InfoRow("Device Name", state.deviceName)
                    InfoRow("Device UUID", if (state.deviceId.isNotEmpty()) state.deviceId else "Not assigned")
                    InfoRow("App Version", state.appVersion)

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedButton(
                        onClick = { viewModel.reregisterDevice() },
                        enabled = !state.isTesting,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Re-register Device with Backend", color = CyberCyan)
                    }
                }
            }

            // Autonomous Defense Vectors & Permissions Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Text(
                        text = "Protection Vectors & Permissions",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    // WhatsApp Protection Toggle
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("WhatsApp Message Shield", fontWeight = FontWeight.Medium, color = TextPrimary)
                            Text("Inspect incoming previews for fraud & phishing", style = MaterialTheme.typography.labelSmall, color = TextSecondary)
                        }
                        Switch(
                            checked = whatsappEnabled,
                            onCheckedChange = { coroutineScope.launch { prefs.setWhatsappProtectionEnabled(it) } },
                            colors = SwitchDefaults.colors(checkedThumbColor = CyberCyan)
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Telegram Protection Toggle
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("Telegram Message Shield", fontWeight = FontWeight.Medium, color = TextPrimary)
                            Text("Inspect incoming previews for crypto & job scams", style = MaterialTheme.typography.labelSmall, color = TextSecondary)
                        }
                        Switch(
                            checked = telegramEnabled,
                            onCheckedChange = { coroutineScope.launch { prefs.setTelegramProtectionEnabled(it) } },
                            colors = SwitchDefaults.colors(checkedThumbColor = CyberCyan)
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Call Blocking Toggle
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("Auto-block Critical Extortion Calls", fontWeight = FontWeight.Medium, color = TextPrimary)
                            Text(if (callBlockingEnabled) "Rejects digital arrest callers before ring" else "Permits ring; displays warning banner", style = MaterialTheme.typography.labelSmall, color = TextSecondary)
                        }
                        Switch(
                            checked = callBlockingEnabled,
                            onCheckedChange = { coroutineScope.launch { prefs.setCallBlockingEnabled(it) } },
                            colors = SwitchDefaults.colors(checkedThumbColor = CyberCyan)
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Button(
                        onClick = onNavigateToOnboarding,
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCyan, contentColor = Color.Black),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.Security, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Open Permission & Battery Dashboard", fontWeight = FontWeight.Bold)
                    }
                }
            }

            // Citizen Account & Data Governance Card (DPDP Act Compliance)
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Text(
                        text = "Citizen Account & Data Governance",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    InfoRow("Account Name", userName ?: "Citizen")
                    InfoRow("Email", userEmail ?: "Not configured")
                    InfoRow("Mobile (+91)", userMobile ?: "Not linked")
                    InfoRow("Mobile Status", if (isMobileVerified) "Verified (Protected)" else "Pending OTP Verification")

                    Spacer(modifier = Modifier.height(16.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedButton(
                            onClick = {
                                coroutineScope.launch {
                                    prefs.clearUserSession()
                                    onLogout()
                                }
                            },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Sign Out", color = TextPrimary)
                        }

                        Button(
                            onClick = { showDeleteDialog = true },
                            colors = ButtonDefaults.buttonColors(containerColor = SeverityCritical.copy(alpha = 0.2f), contentColor = SeverityCritical),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Delete Account")
                        }
                    }
                }
            }
        }
    }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("Delete Account & Data", color = SeverityCritical) },
            text = {
                Text(
                    "Are you sure you want to permanently delete your Cyber Raksha account and all associated threat records? This action cannot be undone.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        showDeleteDialog = false
                        coroutineScope.launch {
                            try {
                                val api = com.cyberraksha.ai.data.remote.NetworkModule.getApiService(state.backendUrl)
                                userToken?.let { api.deleteAccount("Bearer $it") }
                            } catch (_: Exception) {}
                            prefs.clearUserSession()
                            onLogout()
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = SeverityCritical, contentColor = androidx.compose.ui.graphics.Color.White)
                ) {
                    Text("Delete Permanently")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text("Cancel", color = TextSecondary)
                }
            }
        )
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, style = MaterialTheme.typography.bodyMedium, color = TextSecondary)
        Text(text = value, style = MaterialTheme.typography.bodyMedium, color = TextPrimary, fontWeight = FontWeight.Medium)
    }
}

